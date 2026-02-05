"""Number platform for openHAB."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .entity import OpenHABEntity


# Items that contain these keywords are controllable setpoints
SETPOINT_KEYWORDS = [
    "manual_temperature",
    "at_home_temperature",
    "away_temperature",
    "vacation_temperature",
    "frost_protection_temperature",
    "setpoint",
    "target",
]


def is_controllable_number(item) -> bool:
    """Check if an item is a controllable number (not read-only)."""
    name_lower = item.name.lower()
    # Check if it's a temperature item that's likely a setpoint
    if item.type_.startswith("Number"):
        for keyword in SETPOINT_KEYWORDS:
            if keyword in name_lower:
                return True
    return False


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for item in coordinator.data.values():
        if is_controllable_number(item):
            LOGGER.debug("Adding number entity: %s", item.name)
            entities.append(OpenHABNumber(hass, coordinator, item))

    LOGGER.info("Setting up %d number entities", len(entities))
    async_add_entities(entities)


class OpenHABNumber(OpenHABEntity, NumberEntity):
    """openHAB Number class for controlling values."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 5.0
    _attr_native_max_value = 35.0
    _attr_native_step = 0.5

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
