"""Sensors for Heat Pump Power and Temperatures."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
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
            OutletTempSensor(coordinator=entry.runtime_data),
            InletTempSensor(coordinator=entry.runtime_data),
            DischargeTempSensor(coordinator=entry.runtime_data),
            SuctionTempSensor(coordinator=entry.runtime_data),
            EvaporatorTempSensor(coordinator=entry.runtime_data),
            AmbientTempSensor(coordinator=entry.runtime_data),
            CaseTempSensor(coordinator=entry.runtime_data),
            PowerSensor(coordinator=entry.runtime_data),
            CurrentSensor(coordinator=entry.runtime_data),
            CompressorHours(coordinator=entry.runtime_data),
            CompressorStarts(coordinator=entry.runtime_data),
            FanSpeed(coordinator=entry.runtime_data),
            CompressorSpeed(coordinator=entry.runtime_data),
            WaterPumpSpeed(coordinator=entry.runtime_data),
        ]
    )


class ReclaimV2SensorBase(ReclaimV2Entity, SensorEntity):
    """Base class for reclaim sensors."""

    @callback
    def _handle_coordinator_update(self) -> None:
        if hasattr(self.coordinator.data, self._attr_translation_key):
            self._attr_native_value = getattr(
                self.coordinator.data, self._attr_translation_key
            )
            self.async_write_ha_state()


class ReclaimV2SensorTemp(ReclaimV2SensorBase):
    """Base class of temperature sensors."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS


class WaterTempSensor(ReclaimV2SensorTemp):
    """Represents the current water temperature at the bottom sensor."""

    _attr_translation_key = "water"


class OutletTempSensor(ReclaimV2SensorTemp):
    """Represents the current water temperature at the outlet."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "outlet"


class InletTempSensor(ReclaimV2SensorTemp):
    """Represents the current water temperature at the inlet."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "inlet"


class DischargeTempSensor(ReclaimV2SensorTemp):
    """Represents the discharge temperature."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "discharge"


class SuctionTempSensor(ReclaimV2SensorTemp):
    """Represents the current suction temperature."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "suction"


class EvaporatorTempSensor(ReclaimV2SensorTemp):
    """Represents the current evaporator temperature."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "evaporator"


class AmbientTempSensor(ReclaimV2SensorTemp):
    """Represents the ambient temperature at the heat pump unit."""

    _attr_translation_key = "ambient"


class CaseTempSensor(ReclaimV2SensorTemp):
    """Represents the case temperature at the heat pump unit."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "case"


class PowerSensor(ReclaimV2SensorBase):
    """Represents the current power usage of the heat pump."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_translation_key = "power"


class CurrentSensor(ReclaimV2SensorBase):
    """Represents the current power usage of the heat pump."""

    _attr_entity_registry_enabled_default = False
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_translation_key = "current"


class CompressorHours(ReclaimV2SensorBase):
    """Represents the operating hours of the heat pump."""

    _attr_entity_registry_enabled_default = False
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_translation_key = "hours"


class CompressorStarts(ReclaimV2SensorBase):
    """Represents the number of cycles of the heat pump."""

    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_translation_key = "starts"


class WaterPumpSpeed(ReclaimV2SensorBase):
    """Represents water pump speed."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "waterspeed"


class CompressorSpeed(ReclaimV2SensorBase):
    """Represents compressor speed."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "compspeed"


class FanSpeed(ReclaimV2SensorBase):
    """Represents fan speed."""

    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "fanspeed"
