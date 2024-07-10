"""Switch for Heat Pump Boost mode."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ReclaimV2Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities([BoostSwitch(coordinator=entry.runtime_data)])


class BoostSwitch(ReclaimV2Entity, SwitchEntity):
    """Represents the boost state of the heat pump."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_translation_key = "boost_switch"
    _attr_icon = "mdi:rocket"

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            self._attr_is_on = self.coordinator.data.boost
            self.async_write_ha_state()
        except AttributeError:
            _LOGGER.warning("Bad data!")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on Boost Mode."""
        await self.coordinator.api.set_boost(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off Boost Mode."""
        await self.coordinator.api.set_boost(False)
