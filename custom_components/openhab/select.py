"""Select platform for openHAB."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .entity import OpenHABEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for item in coordinator.data.values():
        # Check if item has command options (selectable values)
        if hasattr(item, 'commandDescription') or item.type_ == "String":
            # Get the raw item data to check for command options
            try:
                raw_item = await hass.async_add_executor_job(
                    coordinator.api.openhab.get_item_raw, item.name
                )
                if raw_item.get("commandDescription", {}).get("commandOptions"):
                    LOGGER.debug("Adding select entity: %s", item.name)
                    entities.append(OpenHABSelect(hass, coordinator, item, raw_item))
            except Exception as e:
                LOGGER.debug("Could not get command options for %s: %s", item.name, e)

    LOGGER.info("Setting up %d select entities", len(entities))
    async_add_entities(entities)


class OpenHABSelect(OpenHABEntity, SelectEntity):
    """openHAB Select class for controlling options."""

    def __init__(self, hass, coordinator, item, raw_item):
        """Initialize the select entity."""
        super().__init__(hass, coordinator, item)
        self._raw_item = raw_item
        self._options_map = {}  # command -> label
        self._labels_map = {}   # label -> command
        
        # Parse command options
        cmd_opts = raw_item.get("commandDescription", {}).get("commandOptions", [])
        for opt in cmd_opts:
            cmd = opt.get("command", "")
            label = opt.get("label", cmd)
            self._options_map[cmd] = label
            self._labels_map[label] = cmd

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        state = self.item._state
        if state is None:
            return None
        # Return the label if available, otherwise the raw state
        return self._options_map.get(state, state)

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        return list(self._options_map.values())

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Convert label back to command
        command = self._labels_map.get(option, option)
        LOGGER.debug("Setting %s to %s (command: %s)", self.item.name, option, command)
        await self.hass.async_add_executor_job(
            self.coordinator.api.openhab.req_post,
            f"/items/{self.item.name}",
            command,
        )
        await self.coordinator.async_request_refresh()
