"""ReclaimV2 Components."""

from homeassistant.const import CONF_UNIQUE_ID
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ReclaimV2Coordinator


class ReclaimV2Entity(CoordinatorEntity[ReclaimV2Coordinator]):
    """Implementation of the base ReclaimV2 Entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ReclaimV2Coordinator) -> None:
        """Initialize the ReclaimV2 Entity."""

        super().__init__(coordinator=coordinator)
        self._attr_unique_id = (
            f"{coordinator.api.unique_id}_{self._attr_translation_key}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.data[CONF_UNIQUE_ID])},
            manufacturer="Reclaim Energy",
            model="Reclaim V2",
        )
