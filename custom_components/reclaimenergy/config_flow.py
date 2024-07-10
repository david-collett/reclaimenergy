"""Config flow for Reclaim Energy integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    AWS_IOT_ROOT_CERT,
    CACERT_FILENAME,
    CERT_FILENAME,
    CONF_CACERT_PATH,
    CONF_CERT_PATH,
    CONF_KEY_PATH,
    DOMAIN,
    KEY_FILENAME,
    NAME,
)
from .reclaimv2 import obtain_aws_keys, validate_unique_id

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_UNIQUE_ID): str,
    }
)


def obtain_and_save_aws_keys(cacertpath: str, certpath: str, keypath: str) -> bool:
    """Obtain AWS Credentials."""

    result = obtain_aws_keys()
    if not result:
        return False

    with open(cacertpath, "w", encoding="utf8") as f:
        f.write(AWS_IOT_ROOT_CERT)

    with open(certpath, "w", encoding="utf8") as f:
        f.write(result[1])

    with open(keypath, "w", encoding="utf8") as f:
        f.write(result[2])

    return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    if not validate_unique_id(data[CONF_UNIQUE_ID]):
        raise InvalidIdentifier

    # obtain AWS keys
    cacertpath = hass.config.path(CACERT_FILENAME)
    certpath = hass.config.path(CERT_FILENAME)
    keypath = hass.config.path(KEY_FILENAME)
    if not await hass.async_add_executor_job(
        obtain_and_save_aws_keys, cacertpath, certpath, keypath
    ):
        raise InvalidAuth
    # Return info that you want to store in the config entry.
    return {
        CONF_UNIQUE_ID: data[CONF_UNIQUE_ID],
        CONF_CACERT_PATH: cacertpath,
        CONF_CERT_PATH: certpath,
        CONF_KEY_PATH: keypath,
    }


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Reclaim Energy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidIdentifier:
                errors["base"] = "invalid_id"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=NAME, data=info)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate unable to authenticate."""


class InvalidIdentifier(HomeAssistantError):
    """Error to indicate user has entered an invalid ID."""
