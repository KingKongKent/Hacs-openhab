"""Sensor platform for openHAB."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, ITEMS_MAP, LOGGER, SENSOR
from .device_classes_map import SENSOR_DEVICE_CLASS_MAP
from .entity import OpenHABEntity


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
        # Skip items with no type
        if not item.type_:
            continue
            
        if item.type_ not in ITEMS_MAP[SENSOR]:
            continue
            
        raw_item = coordinator.raw_items.get(item.name, {})
        state_desc = raw_item.get("stateDescription", {})
        cmd_desc = raw_item.get("commandDescription", {})
        
        # For Number items: only include if readOnly=True OR no min/max defined
        if item.type_.startswith("Number"):
            is_read_only = state_desc.get("readOnly", True)
            has_range = state_desc.get("minimum") is not None and state_desc.get("maximum") is not None
            
            if is_read_only or not has_range:
                LOGGER.debug("Adding sensor: %s (readOnly=%s, hasRange=%s)", item.name, is_read_only, has_range)
                sensors.append(OpenHABSensor(hass, coordinator, item))
            continue
        
        # For String items: only include if readOnly=True OR no commandOptions
        if item.type_ == "String":
            is_read_only = state_desc.get("readOnly", True)
            has_options = bool(cmd_desc.get("commandOptions", []))
            
            if is_read_only or not has_options:
                LOGGER.debug("Adding string sensor: %s (readOnly=%s, hasOptions=%s)", item.name, is_read_only, has_options)
                sensors.append(OpenHABSensor(hass, coordinator, item))
            continue
        
        # Other types: add as sensor
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
