"""Number platform for openHAB."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .entity import OpenHABEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    LOGGER.info("Number platform: coordinator.data has %d items, raw_items has %d items", 
                len(coordinator.data) if coordinator.data else 0, 
                len(coordinator.raw_items) if coordinator.raw_items else 0)
    
    for item in coordinator.data.values():
        # Skip items with no type
        if not item.type_:
            continue
            
        # Only Number items that are NOT read-only
        if item.type_.startswith("Number"):
            raw_item = coordinator.raw_items.get(item.name, {})
            state_desc = raw_item.get("stateDescription", {})
            is_read_only = state_desc.get("readOnly", True)
            has_min = state_desc.get("minimum") is not None
            has_max = state_desc.get("maximum") is not None
            
            LOGGER.debug("Number check: %s - type=%s, readOnly=%s, hasMin=%s, hasMax=%s", 
                        item.name, item.type_, is_read_only, has_min, has_max)
            
            # Skip read-only items (like current temperature readings)
            if is_read_only:
                continue
            
            # Must have min/max defined (indicates it's a setpoint)
            if has_min and has_max:
                LOGGER.info("Adding number entity: %s (min=%s, max=%s, step=%s)", 
                           item.name, 
                           state_desc.get("minimum"),
                           state_desc.get("maximum"),
                           state_desc.get("step", 0.5))
                entities.append(OpenHABNumber(hass, coordinator, item, raw_item))

    LOGGER.info("Setting up %d number entities", len(entities))
    async_add_entities(entities)


class OpenHABNumber(OpenHABEntity, NumberEntity):
    """openHAB Number class for controlling values."""

    _attr_device_class = None
    _attr_mode = NumberMode.BOX

    def __init__(self, hass, coordinator, item, raw_item):
        """Initialize the number entity."""
        super().__init__(hass, coordinator, item)
        self._attr_device_class_map = {}
        self._raw_item = raw_item
        
        # Get min/max/step from stateDescription
        state_desc = raw_item.get("stateDescription", {})
        self._attr_native_min_value = float(state_desc.get("minimum", 5))
        self._attr_native_max_value = float(state_desc.get("maximum", 35))
        self._attr_native_step = float(state_desc.get("step", 0.5))

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.item._state is None:
            return None
        if isinstance(self.item._state, (int, float)):
            return float(self.item._state)
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if self.item.unit_of_measure:
            uom = str(self.item.unit_of_measure)
            if "°C" in uom or "celsius" in uom.lower():
                return UnitOfTemperature.CELSIUS
            if "°F" in uom or "fahrenheit" in uom.lower():
                return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        LOGGER.debug("Setting %s to %s", self.item.name, value)
        await self.hass.async_add_executor_job(
            self.coordinator.api.openhab.req_post,
            f"/items/{self.item.name}",
            str(value),
        )
        await self.coordinator.async_request_refresh()
