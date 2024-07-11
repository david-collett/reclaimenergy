"""Config flow for Reclaim Energy integration."""

from __future__ import annotations

import contextlib
import logging
import os
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
    """Validate the provided user data and test authentication."""

    # test that the provided ID is valid
    if not validate_unique_id(data[CONF_UNIQUE_ID]):
        raise InvalidIdentifier

    # obtain AWS keys
    basepath = hass.config.path(DOMAIN)
    with contextlib.suppress(FileExistsError):
        os.mkdir(hass.config.path(DOMAIN))

    cacertpath = os.path.join(basepath, CACERT_FILENAME)
    certpath = os.path.join(basepath, CERT_FILENAME)
    keypath = os.path.join(basepath, KEY_FILENAME)
    if not await hass.async_add_executor_job(
        obtain_and_save_aws_keys, cacertpath, certpath, keypath
    ):
        raise InvalidAuth

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


class InvalidAuth(HomeAssistantError):
    """Error to indicate unable to authenticate."""


class InvalidIdentifier(HomeAssistantError):
    """Error to indicate user has entered an invalid ID."""
