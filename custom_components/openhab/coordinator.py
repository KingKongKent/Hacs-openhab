"""Data update coordinator for integration openHAB."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiClientException, OpenHABApiClient
from .const import DATA_COORDINATOR_UPDATE_INTERVAL, DOMAIN, LOGGER


class OpenHABDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, api: OpenHABApiClient) -> None:
        """Initialize."""
        self.api = api
        self.platforms: list[str] = []
        self.version: str = ""
        self.is_online = False
        self.groups: dict[str, dict] = {}  # Group name -> group info
        self.item_to_group: dict[str, str] = {}  # Item name -> parent group name
        self.raw_items: dict[str, dict] = {}  # Item name -> raw item dict

        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=DATA_COORDINATOR_UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            if self.version is None or len(self.version) == 0:
                self.version = await self.api.async_get_version()
                LOGGER.info("Connected to openHAB version: %s", self.version)

            items = await self.api.async_get_items()
            self.is_online = bool(items)
            
            # Fetch raw items and groups for device hierarchy
            await self._fetch_raw_items_and_groups()
            
            if items:
                LOGGER.info("Fetched %d items from openHAB", len(items))
                for item_name, item in items.items():
                    LOGGER.debug("Item: %s, Type: %s", item_name, item.type_)
            else:
                LOGGER.warning("No items fetched from openHAB. Make sure you have Items (not just Things) configured in openHAB.")
            
            return items

        except ApiClientException as exception:
            raise UpdateFailed(exception) from exception

    async def _fetch_raw_items_and_groups(self) -> None:
        """Fetch raw items and groups for device hierarchy."""
        try:
            raw_items_list = await self.api.async_get_items_raw()
            
            self.raw_items = {}
            self.groups = {}
            self.item_to_group = {}
            
            for raw_item in raw_items_list:
                item_name = raw_item.get("name", "")
                self.raw_items[item_name] = raw_item
                
                if raw_item.get("type") == "Group":
                    self.groups[item_name] = {
                        "name": item_name,
                        "label": raw_item.get("label", item_name),
                        "tags": raw_item.get("tags", []),
                        "category": raw_item.get("category", ""),
                    }
                
                # Map items to their parent groups
                group_names = raw_item.get("groupNames", [])
                if group_names:
                    self.item_to_group[item_name] = group_names[0]
            
            LOGGER.info("Fetched %d raw items, %d groups, %d item-to-group mappings", 
                       len(self.raw_items), len(self.groups), len(self.item_to_group))
        except Exception as e:
            LOGGER.warning("Could not fetch raw items: %s", e)
