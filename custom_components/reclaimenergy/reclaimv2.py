"""Reclaim Energy V2 Heat Pump Hot Water System Controller."""

import asyncio
from collections import namedtuple
import json
import logging
import ssl

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
    hexstr = f"{int(id):#014x}"[2:]

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


ReclaimState = namedtuple(
    "ReclaimState", ["pump", "water", "ambient", "power", "boost"]
)


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

        hexid = f"{self.unique_id:#014x}"[2:-2]
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
                raw = payload["modbusVal"]
                data = {raw[i]: raw[i + 1] for i in range(0, len(raw), 2)}
                _LOGGER.debug("Received modbus data: %s", data)
                state = ReclaimState(
                    data[200], data[79] / 2, data[223] / 2, data[225], data[40990]
                )
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

    async def set_boost(self, boost: bool) -> None:
        """Send MQTT update request to controller."""
        if not self._connected:
            _LOGGER.warning("Not connected")
            return

        if self._client:
            try:
                await self._client.publish(
                    self.command_topic,
                    json.dumps(
                        {
                            "messageId": "write",
                            "modbusReg": 40990,
                            "modbusVal": [1 if boost else 0],
                        }
                    ),
                    qos=1,
                )
            except aiomqtt.exceptions.MqttError as e:
                _LOGGER.error("Error publishing boost request: %s", e)


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
