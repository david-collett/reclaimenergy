"""Binary sensor for Heat Pump State."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    async_add_entities([HeatPumpSensor(coordinator=entry.runtime_data)])


class HeatPumpSensor(ReclaimV2Entity, BinarySensorEntity):
    """Represents the current state of the heat pump."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_translation_key = "heatpump_state"
    _attr_icon = "mdi:heat-pump"

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            self._attr_is_on = self.coordinator.data.pump
            self.async_write_ha_state()
        except AttributeError:
            _LOGGER.warning("Bad data!")
