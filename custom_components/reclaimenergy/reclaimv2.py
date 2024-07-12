"""Reclaim Energy V2 Heat Pump Hot Water System Controller."""

import asyncio
import json
import logging
import ssl
from typing import Any

import aiomqtt
import boto3
import botocore

AWS_REGION_NAME = ""
AWS_IDENTITY_POOL = ""
AWS_HOSTNAME = ""
AWS_PORT = 8883

_LOGGER = logging.getLogger(__name__)


def validate_unique_id(id: str) -> bool:
    """Validate the Reclaim unit unique ID."""

    # id is a 17 characters long integer
    if not id.isnumeric() or len(id) != 17:
        return False

    # convert to hex string
    hexstr = f"{int(id):#016x}"[2:]

    # build the lookup table used by the checksum
    lut = []
    key = 47
    for x in range(256):
        i = x
        for _y in range(8):
            j = i & 128
            i <<= 1
            if j != 0:
                i ^= key
        lut.append(i & 255)

    # calculate the checksum
    cksum = 0
    for x in range(len(hexstr) - 2):
        cksum = lut[(cksum ^ ord(hexstr[x])) & 255]

    return int(hexstr[-2:], 16) == cksum


def obtain_aws_keys() -> tuple:
    """Authenticate to AWS and obtain iot certs for mqtt."""

    try:
        cognito = boto3.client("cognito-identity", region_name=AWS_REGION_NAME)

        # obtain identity from pool
        identity = cognito.get_id(IdentityPoolId=AWS_IDENTITY_POOL)["IdentityId"]

        # obtain api creds
        creds = cognito.get_credentials_for_identity(IdentityId=identity)["Credentials"]

        # get certs for aws-iot core mqtt
        iot = boto3.client(
            "iot",
            region_name=AWS_REGION_NAME,
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretKey"],
            aws_session_token=creds["SessionToken"],
        )
        keys = iot.create_keys_and_certificate(setAsActive=True)

        # attach to pswpolicy
        iot.attach_policy(policyName="pswpolicy", target=keys["certificateArn"])

        cert = keys["certificatePem"]
        key = keys["keyPair"]["PrivateKey"]
    except botocore.exceptions.ClientError:
        return None
    else:
        return (identity, cert, key)


def ushort(x: int):
    """Convert python int to it's unsigned short value."""
    return x - 65536 if x & 0x8000 else x


class ReclaimState:
    """Represents the current system state."""

    modes = [
        "Mode 1: 24H",
        "Mode 2: Off-Peak 1",
        "Mode 3: Off-Peak 2",
        "Mode 4: PV Connectivity",
        "Mode 5: User Timers",
        "Mode 6: User Timers & Temperature",
        "Mode 7: PV Default Timer",
        "Mode 8: Holiday Mode",
    ]

    days = ["Sun", "Mon", "Tue", "Wed", "Thurs", "Fri", "Sat"]

    modbus_map = {
        "mode": (
            40964,
            lambda x: ReclaimState.modes[x - 2],
            lambda x: ReclaimState.modes.index(x) + 2,
        ),
        "pump": (200, None, None),
        "case": (50, lambda x: ushort(int(x / 2)), None),
        "water": (79, lambda x: ushort(int(x / 2)), None),
        "outlet": (213, ushort, None),
        "inlet": (214, ushort, None),
        "discharge": (215, ushort, None),
        "suction": (216, ushort, None),
        "evaporator": (217, ushort, None),
        "ambient": (218, ushort, None),
        "compspeed": (219, None, None),
        "waterspeed": (220, None, None),
        "fanspeed": (221, None, None),
        "power": (225, None, None),
        "current": (226, lambda x: x / 1000, None),
        "hours": (222, None, None),
        "starts": (223, None, None),
        "boost": (40990, bool, int),
        "mode5_timer1_start": (40971, lambda x: int(x / 256), lambda x: x * 256),
        "mode5_timer1_duration": (40972, lambda x: int(x / 256), lambda x: x * 256),
        "mode5_timer2_start": (40973, lambda x: int(x / 256), lambda x: x * 256),
        "mode5_timer2_duration": (40974, lambda x: int(x / 256), lambda x: x * 256),
        "mode5_timer2_on_temp": (40975, lambda x: x / 2, lambda x: x * 2),
        "mode6_timer1_start": (40976, lambda x: int(x / 256), lambda x: x * 256),
        "mode6_timer1_duration": (40977, lambda x: int(x / 256), lambda x: x * 256),
        "mode6_timer2_start": (40991, lambda x: int(x / 256), lambda x: x * 256),
        "mode6_timer2_duration": (40992, lambda x: int(x / 256), lambda x: x * 256),
        "mode6_timer2_on_temp": (40978, lambda x: x / 2, lambda x: x * 2),
        "mode6_timer2_off_temp": (40979, lambda x: x / 2, lambda x: x * 2),
        "mode7_start": (40980, lambda x: int(x / 256), lambda x: x * 256),
        "mode7_duration": (40981, lambda x: int(x / 256), lambda x: x * 256),
        "mode8_day": (
            41000,
            lambda x: ReclaimState.days[x - 1],
            lambda x: ReclaimState.days.index(x + 1),
        ),
        "mode8_start": (41001, lambda x: int(x / 256), lambda x: x * 256),
    }

    def __init__(self, data: dict) -> None:
        """Initialise with modbus data."""
        self.data = data

    def __getattr__(self, name: str):
        """Return a processed attribute."""
        try:
            mb = self.modbus_map[name]
            if mb[1]:
                return mb[1](self.data[mb[0]])

            return self.data[mb[0]]
        except (IndexError, KeyError) as e:
            raise AttributeError from e


class MessageListener:
    """Message Listener."""

    def on_message(self, state: ReclaimState) -> None:
        """Process device state updates."""


class ReclaimV2:
    """ReclaimV2 HPHWS Controller."""

    def __init__(self, unique_id: int, cacert: str, certificate: str, key: str) -> None:
        """Initialize."""
        self.unique_id = unique_id
        self.cacert = cacert
        self.certificate = certificate
        self.key = key

        self._client = None
        self._connected = False
        self._listener_task = None

        hexid = f"{self.unique_id:#016x}"[2:-2]
        self.subscribe_topic = f"dontek{hexid}/status/psw"
        self.command_topic = f"dontek{hexid}/cmd/psw"

    def connect(self, listener: MessageListener) -> None:
        """Connect to MQTT server and subscribe for updates."""
        self._listener_task = asyncio.create_task(self._listen(listener))

    async def _listen(self, listener: MessageListener):
        aws_tls_params = aiomqtt.TLSParameters(
            ca_certs=self.cacert,
            certfile=self.certificate,
            keyfile=self.key,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None,
        )
        self._connected = True
        while self._connected:
            try:
                async with aiomqtt.Client(
                    hostname=AWS_HOSTNAME, port=AWS_PORT, tls_params=aws_tls_params
                ) as self._client:
                    _LOGGER.debug("Connected, subscribing to %s", self.subscribe_topic)
                    await self._client.subscribe(self.subscribe_topic)

                    # request initial update
                    await self.request_update()

                    # process messages
                    async for message in self._client.messages:
                        self._process_message(message, listener)

            except aiomqtt.MqttError as mqtt_err:
                _LOGGER.warning("Waiting for retry, error: %s", mqtt_err)
                self._client = None
            except Exception as e:  # noqa: BLE001
                _LOGGER.error("Exception in MQTT loop: %s", e)
            finally:
                await asyncio.sleep(5)

    async def disconnect(self) -> None:
        """Disconnect from MQTT Server."""
        if self._listener_task is None:
            return
        self._connected = False
        self._listener_task.cancel()
        self._listener_task = None
        self._client = None

    def _process_message(self, message, listener: MessageListener):
        try:
            payload = json.loads(message.payload)
            if payload["messageId"] == "read" and payload["modbusReg"] == 1:
                # full modbus packet with all values
                raw = payload["modbusVal"]
                data = {raw[i]: raw[i + 1] for i in range(0, len(raw), 2)}
                _LOGGER.debug("Received modbus data: %s", data)
                state = ReclaimState(data)
                listener.on_message(state)
            elif payload["messageId"] == "write":
                # ack of a command, process so the entities are updated
                values = payload["modbusVal"]
                if len(values) == 1:
                    state = ReclaimState({payload["modbusReg"]: values[0]})
                    _LOGGER.debug("Received modbus data: %s", payload)
                    listener.on_message(state)
            else:
                _LOGGER.warning("Unknown payload: %s", payload)
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            _LOGGER.error("Error processing payload(%s): %s", e, message.payload)

    async def request_update(self) -> None:
        """Send MQTT update request to controller."""
        if not self._connected:
            _LOGGER.warning("Not connected")
            return

        if self._client:
            try:
                await self._client.publish(
                    self.command_topic,
                    json.dumps({"messageId": "read", "modbusReg": 1, "modbusVal": [1]}),
                    qos=1,
                )
            except aiomqtt.exceptions.MqttError as e:
                _LOGGER.error("Error publishing update request: %s", e)

    async def set_value(self, name: str, value: Any) -> None:
        """Send MQTT message to turn on boost mode."""
        if not self._connected:
            _LOGGER.warning("Not connected")
            return

        entry = ReclaimState.modbus_map[name]
        if not entry[2]:
            _LOGGER.warning("This value is readonly and cannot be set")
            return

        if self._client:
            try:
                value = entry[2](value)
                await self._client.publish(
                    self.command_topic,
                    json.dumps(
                        {
                            "messageId": "write",
                            "modbusReg": entry[0],
                            "modbusVal": [value],
                        }
                    ),
                    qos=1,
                )
            except aiomqtt.exceptions.MqttError as e:
                _LOGGER.error("Error publishing value request: %s", e)


async def main():
    """Test harness."""

    class LogMessageListener(MessageListener):
        def on_message(self, state: ReclaimState) -> None:
            _LOGGER.info(state)

    reclaimv2 = ReclaimV2(
        12345, "AmazonRootCA1.pem", "reclaim_cert.pem", "reclaim_key.pem"
    )
    await reclaimv2.connect(LogMessageListener())

    while True:
        _LOGGER.debug("Requesting update")
        await reclaimv2.request_update()
        await asyncio.sleep(10)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
