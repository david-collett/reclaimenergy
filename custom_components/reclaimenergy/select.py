"""Mode selector for Heat Pump."""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ReclaimV2Entity
from .reclaimv2 import ReclaimState

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        [
            ModeSelect(coordinator=entry.runtime_data),
            DaySelect(coordinator=entry.runtime_data),
        ]
    )


class ModeSelect(ReclaimV2Entity, SelectEntity):
    """Represents the operating mode of the heat pump."""

    _attr_translation_key = "operating_mode"
    _attr_options = ReclaimState.modes
    _attr_current_option = _attr_options[0]

    @callback
    def _handle_coordinator_update(self) -> None:
        if hasattr(self.coordinator.data, "mode"):
            self._attr_current_option = self.coordinator.data.mode
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Set operating mode."""
        await self.coordinator.api.set_value("mode", option)


class DaySelect(ReclaimV2Entity, SelectEntity):
    """Represents the holiday mode day."""

    _attr_translation_key = "mode8_day"
    _attr_options = ReclaimState.days
    _attr_current_option = _attr_options[0]

    @callback
    def _handle_coordinator_update(self) -> None:
        if hasattr(self.coordinator.data, "mode8_day"):
            self._attr_current_option = self.coordinator.data.mode8_day
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Set operating mode."""
        await self.coordinator.api.set_value("mode8_day", option)
