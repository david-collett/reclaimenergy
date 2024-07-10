"""Sensors for Heat Pump Power and Temperatures."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ReclaimV2Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        [
            WaterTempSensor(coordinator=entry.runtime_data),
            AmbientTempSensor(coordinator=entry.runtime_data),
            PowerSensor(coordinator=entry.runtime_data),
        ]
    )


class WaterTempSensor(ReclaimV2Entity, SensorEntity):
    """Represents the current water temperature at the bottom sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "water_temperature"

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            self._attr_native_value = self.coordinator.data.water
            self.async_write_ha_state()
        except AttributeError:
            _LOGGER.warning("Bad data!")


class AmbientTempSensor(ReclaimV2Entity, SensorEntity):
    """Represents the current water temperature at the bottom sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "ambient_temperature"

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            self._attr_native_value = self.coordinator.data.ambient
            self.async_write_ha_state()
        except AttributeError:
            _LOGGER.warning("Bad data!")


class PowerSensor(ReclaimV2Entity, SensorEntity):
    """Represents the current power usage of the heat pump."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_translation_key = "power"

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            self._attr_native_value = self.coordinator.data.power
            self.async_write_ha_state()
        except AttributeError:
            _LOGGER.warning("Bad data!")
