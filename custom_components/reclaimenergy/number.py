"""Timer settings for Heat Pump."""

import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
    async_add_entities(
        [
            Mode5Timer1Duration(coordinator=entry.runtime_data),
            Mode5Timer2Duration(coordinator=entry.runtime_data),
            Mode5Timer2OnTemp(coordinator=entry.runtime_data),
            Mode6Timer1Duration(coordinator=entry.runtime_data),
            Mode6Timer2Duration(coordinator=entry.runtime_data),
            Mode6Timer2OnTemp(coordinator=entry.runtime_data),
            Mode6Timer2OffTemp(coordinator=entry.runtime_data),
            Mode7Duration(coordinator=entry.runtime_data),
        ]
    )


class ReclaimV2DurationBase(ReclaimV2Entity, NumberEntity):
    """Represents the timer parameters of the heat pump."""

    _attr_entity_registry_enabled_default = False
    _attr_native_max_value = 12
    _attr_native_min_value = 3
    _attr_native_step = 1
    _attr_native_value = 0

    @callback
    def _handle_coordinator_update(self) -> None:
        if hasattr(self.coordinator.data, self._attr_translation_key):
            self._attr_native_value = getattr(
                self.coordinator.data, self._attr_translation_key
            )
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set timer duration."""
        await self.coordinator.api.set_value(self._attr_translation_key, int(value))


class Mode5Timer1Duration(ReclaimV2DurationBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode5_timer1_duration"


class Mode5Timer2Duration(ReclaimV2DurationBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode5_timer2_duration"
    _attr_native_min_value = 0


class Mode5Timer2OnTemp(ReclaimV2DurationBase):
    """Represents the timer parameters of the heat pump."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "mode5_timer2_on_temp"
    _attr_native_max_value = 45
    _attr_native_min_value = 25
    _attr_native_step = 0.5


class Mode6Timer1Duration(ReclaimV2DurationBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode6_timer1_duration"


class Mode6Timer2Duration(ReclaimV2DurationBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode6_timer2_duration"
    _attr_native_min_value = 0


class Mode6Timer2OnTemp(ReclaimV2DurationBase):
    """Represents the timer parameters of the heat pump."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "mode6_timer2_on_temp"
    _attr_native_max_value = 45
    _attr_native_min_value = 25
    _attr_native_step = 0.5


class Mode6Timer2OffTemp(ReclaimV2DurationBase):
    """Represents the timer parameters of the heat pump."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "mode6_timer2_off_temp"
    _attr_native_max_value = 60
    _attr_native_min_value = 55
    _attr_native_step = 0.5


class Mode7Duration(ReclaimV2DurationBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode7_duration"
