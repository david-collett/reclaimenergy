"""Timer settings for Heat Pump."""

from datetime import time
import logging

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ReclaimV2Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the time platform."""
    async_add_entities(
        [
            Mode5Timer1Start(coordinator=entry.runtime_data),
            Mode5Timer2Start(coordinator=entry.runtime_data),
            Mode6Timer1Start(coordinator=entry.runtime_data),
            Mode6Timer2Start(coordinator=entry.runtime_data),
            Mode7Start(coordinator=entry.runtime_data),
            Mode8Start(coordinator=entry.runtime_data),
        ]
    )


class ReclaimV2TimerBase(ReclaimV2Entity, TimeEntity):
    """Represents the timer parameters of the heat pump."""

    _attr_entity_registry_enabled_default = False
    _attr_native_value = time(hour=0)

    @callback
    def _handle_coordinator_update(self) -> None:
        if hasattr(self.coordinator.data, self._attr_translation_key):
            self._attr_native_value = time(
                hour=getattr(self.coordinator.data, self._attr_translation_key)
            )
            self.async_write_ha_state()

    async def async_set_value(self, value: time) -> None:
        """Set timer start."""
        if value.minute != 0 or value.second != 0:
            raise ServiceValidationError("Only whole hours are permitted")
        await self.coordinator.api.set_value(self._attr_translation_key, value.hour)


class Mode5Timer1Start(ReclaimV2TimerBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode5_timer1_start"


class Mode5Timer2Start(ReclaimV2TimerBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode5_timer2_start"


class Mode6Timer1Start(ReclaimV2TimerBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode6_timer1_start"


class Mode6Timer2Start(ReclaimV2TimerBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode6_timer2_start"


class Mode7Start(ReclaimV2TimerBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode7_start"


class Mode8Start(ReclaimV2TimerBase):
    """Represents the timer parameters of the heat pump."""

    _attr_translation_key = "mode8_start"
