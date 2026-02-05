"""Sensor platform for openHAB."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, ITEMS_MAP, LOGGER, SENSOR
from .device_classes_map import SENSOR_DEVICE_CLASS_MAP
from .entity import OpenHABEntity


# Keywords that indicate controllable setpoints (handled by number platform)
SETPOINT_KEYWORDS = [
    "manual_temperature",
    "at_home_temperature", 
    "away_temperature",
    "vacation_temperature",
    "frost_protection_temperature",
    "setpoint",
    "target",
]


def is_read_only_sensor(item) -> bool:
    """Check if item should be a read-only sensor (not a controllable number)."""
    name_lower = item.name.lower()
    # Exclude items that are controllable setpoints
    for keyword in SETPOINT_KEYWORDS:
        if keyword in name_lower:
            return False
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if not coordinator.data:
        LOGGER.warning("No data in coordinator, cannot set up sensors")
        return

    sensors = []
    for item in coordinator.data.values():
        LOGGER.debug("Checking item: %s, type_: %s", item.name, item.type_)
        if item.type_ in ITEMS_MAP[SENSOR] and is_read_only_sensor(item):
            LOGGER.debug("Adding sensor: %s", item.name)
            sensors.append(OpenHABSensor(hass, coordinator, item))

    LOGGER.info("Setting up %d sensors from %d items", len(sensors), len(coordinator.data))
    async_add_entities(sensors)


class OpenHABSensor(OpenHABEntity, SensorEntity):
    """openHAB Sensor class."""

    _attr_device_class_map = SENSOR_DEVICE_CLASS_MAP

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        return self.item._state
