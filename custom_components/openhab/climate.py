"""Climate platform for openHAB."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER, NAME
from .utils import sanitize_entity_id, strip_ip


# Map openHAB modes to HA HVAC modes
OPENHAB_TO_HVAC_MODE = {
    "MANUAL": HVACMode.HEAT,
    "SCHEDULE": HVACMode.AUTO,
    "AWAY": HVACMode.AUTO,
    "VACATION": HVACMode.AUTO,
    "FROST_PROTECTION": HVACMode.AUTO,
    "AT_HOME": HVACMode.HEAT,
    "OFF": HVACMode.OFF,
}

HVAC_MODE_TO_OPENHAB = {
    HVACMode.HEAT: "MANUAL",
    HVACMode.AUTO: "SCHEDULE",
    HVACMode.OFF: "OFF",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    # Find groups that are thermostats (have mode + temperature items)
    for group_name, group_info in coordinator.groups.items():
        # Find items belonging to this group
        group_items = {
            name: coordinator.data.get(name)
            for name, parent in coordinator.item_to_group.items()
            if parent == group_name and coordinator.data.get(name)
        }
        
        if not group_items:
            continue
        
        # Check if this group has thermostat items
        mode_item = None
        current_temp_item = None
        target_temp_item = None
        raw_mode_item = None
        
        for item_name, item in group_items.items():
            if not item or not item.type_:
                continue
                
            name_lower = item_name.lower()
            raw_item = coordinator.raw_items.get(item_name, {})
            state_desc = raw_item.get("stateDescription", {})
            
            # Find Mode item (String with commandOptions, not read-only)
            if item.type_ == "String" and "_mode" in name_lower:
                cmd_opts = raw_item.get("commandDescription", {}).get("commandOptions", [])
                if cmd_opts and not state_desc.get("readOnly", False):
                    mode_item = item
                    raw_mode_item = raw_item
            
            # Find current temperature (read-only Number:Temperature)
            if item.type_.startswith("Number") and state_desc.get("readOnly", False):
                if "room_temperature" in name_lower or "floor_temperature" in name_lower:
                    if current_temp_item is None or "room" in name_lower:
                        current_temp_item = item
            
            # Find target/setpoint temperature (writable Number:Temperature)
            if item.type_.startswith("Number") and not state_desc.get("readOnly", True):
                if "manual_temperature" in name_lower or "at_home_temperature" in name_lower:
                    if target_temp_item is None or "manual" in name_lower:
                        target_temp_item = item
        
        # Create climate entity if we have the required items
        if mode_item and current_temp_item and target_temp_item:
            LOGGER.info("Creating climate entity for group: %s", group_name)
            entities.append(OpenHABClimate(
                hass, coordinator, group_info, 
                mode_item, raw_mode_item,
                current_temp_item, target_temp_item
            ))

    LOGGER.info("Setting up %d climate entities", len(entities))
    async_add_entities(entities)


class OpenHABClimate(ClimateEntity):
    """openHAB Climate class."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE |
        ClimateEntityFeature.TURN_OFF |
        ClimateEntityFeature.TURN_ON
    )
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    _attr_min_temp = 5.0
    _attr_max_temp = 35.0
    _attr_target_temperature_step = 0.5
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self, 
        hass: HomeAssistant, 
        coordinator, 
        group_info: dict,
        mode_item,
        raw_mode_item: dict,
        current_temp_item,
        target_temp_item,
    ) -> None:
        """Initialize the climate entity."""
        self.hass = hass
        self.coordinator = coordinator
        self._group_info = group_info
        self._mode_item = mode_item
        self._raw_mode_item = raw_mode_item
        self._current_temp_item = current_temp_item
        self._target_temp_item = target_temp_item
        
        self._base_url = coordinator.api._base_url
        self._host = strip_ip(self._base_url)
        
        group_name = group_info.get("name", "")
        sanitized_host = sanitize_entity_id(self._host)
        sanitized_name = sanitize_entity_id(group_name)
        self._attr_unique_id = f"{DOMAIN}_{sanitized_host}_{sanitized_name}_climate"
        
        # Get min/max from target temp item
        raw_target = coordinator.raw_items.get(target_temp_item.name, {})
        state_desc = raw_target.get("stateDescription", {})
        if state_desc.get("minimum") is not None:
            self._attr_min_temp = float(state_desc.get("minimum"))
        if state_desc.get("maximum") is not None:
            self._attr_max_temp = float(state_desc.get("maximum"))
        if state_desc.get("step") is not None:
            self._attr_target_temperature_step = float(state_desc.get("step"))
        
        # Build preset modes from openHAB command options
        self._preset_modes = []
        self._preset_map = {}  # label -> command
        cmd_opts = raw_mode_item.get("commandDescription", {}).get("commandOptions", [])
        for opt in cmd_opts:
            cmd = opt.get("command", "")
            label = opt.get("label", cmd)
            self._preset_modes.append(label)
            self._preset_map[label] = cmd
        
        if self._preset_modes:
            self._attr_supported_features |= ClimateEntityFeature.PRESET_MODE
            self._attr_preset_modes = self._preset_modes

    @property
    def name(self) -> str:
        """Return the name."""
        return self._group_info.get("label", self._group_info.get("name", "Thermostat"))

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        group_name = self._group_info.get("name", "")
        group_label = self._group_info.get("label", group_name)
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._host}_{group_name}")},
            name=group_label,
            model="Thermostat",
            manufacturer="openHAB",
            via_device=(DOMAIN, self._host),
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.is_online

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        item = self.coordinator.data.get(self._current_temp_item.name)
        if item and item._state is not None:
            if isinstance(item._state, (int, float)):
                return float(item._state)
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        item = self.coordinator.data.get(self._target_temp_item.name)
        if item and item._state is not None:
            if isinstance(item._state, (int, float)):
                return float(item._state)
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        item = self.coordinator.data.get(self._mode_item.name)
        if item and item._state:
            mode_str = str(item._state).upper()
            return OPENHAB_TO_HVAC_MODE.get(mode_str, HVACMode.AUTO)
        return HVACMode.AUTO

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        item = self.coordinator.data.get(self._mode_item.name)
        if item and item._state:
            # Find label for current state
            for label, cmd in self._preset_map.items():
                if cmd == item._state:
                    return label
            return item._state
        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            temp = kwargs[ATTR_TEMPERATURE]
            LOGGER.debug("Setting %s to %s", self._target_temp_item.name, temp)
            await self.hass.async_add_executor_job(
                self.coordinator.api.openhab.req_post,
                f"/items/{self._target_temp_item.name}",
                str(temp),
            )
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        openhab_mode = HVAC_MODE_TO_OPENHAB.get(hvac_mode)
        if openhab_mode:
            LOGGER.debug("Setting %s to %s", self._mode_item.name, openhab_mode)
            await self.hass.async_add_executor_job(
                self.coordinator.api.openhab.req_post,
                f"/items/{self._mode_item.name}",
                openhab_mode,
            )
            await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        command = self._preset_map.get(preset_mode, preset_mode)
        LOGGER.debug("Setting %s to %s (command: %s)", self._mode_item.name, preset_mode, command)
        await self.hass.async_add_executor_job(
            self.coordinator.api.openhab.req_post,
            f"/items/{self._mode_item.name}",
            command,
        )
        await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()
