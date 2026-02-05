"""Sample API Client."""
from __future__ import annotations

from typing import Any

import requests
from requests.auth import AuthBase
from openhab import OpenHAB

from .const import CONF_AUTH_TYPE_BASIC, CONF_AUTH_TYPE_TOKEN, LOGGER


class OpenHABTokenAuth(AuthBase):
    """Custom auth class for openHAB API token authentication (requests library)."""

    def __init__(self, token: str) -> None:
        """Initialize with the API token."""
        self.token = token

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        """Add the X-OPENHAB-TOKEN header to the request."""
        r.headers["X-OPENHAB-TOKEN"] = self.token
        return r


class ApiClientException(Exception):
    """Api Client Exception."""


class OpenHABApiClient:
    """API Client"""

    # pylint: disable=R0913
    def __init__(
        self,
        hass,
        base_url: str,
        auth_type: str,
        auth_token: str | None,
        username: str | None,
        password: str | None,
    ) -> None:
        """openHAB API Client."""
        self.hass = hass
        self._base_url = base_url
        self._rest_url = f"{base_url}/rest"
        self._username = username
        self._password = password
        self._auth_token = auth_token
        self._auth_type = auth_type

        LOGGER.info("Initializing OpenHAB client with URL: %s, auth_type: %s", self._rest_url, auth_type)

        if auth_type == CONF_AUTH_TYPE_TOKEN and auth_token:
            # Use custom auth class for token authentication
            LOGGER.info("Creating OpenHAB client with token auth")
            self.openhab = OpenHAB(self._rest_url, http_auth=OpenHABTokenAuth(auth_token))
        elif auth_type == CONF_AUTH_TYPE_BASIC and username:
            LOGGER.info("Creating OpenHAB client with basic auth")
            self.openhab = OpenHAB(self._rest_url, username, password)
        else:
            LOGGER.info("Creating OpenHAB client without auth")
            self.openhab = OpenHAB(self._rest_url)

    async def async_get_version(self) -> str:
        """Get all items from the API."""
        info = await self.hass.async_add_executor_job(self.openhab.req_get, "/")
        runtime_info = info["runtimeInfo"]
        return f"{runtime_info['version']} {runtime_info['buildString']}"

    async def async_get_items(self) -> dict[str, Any]:
        """Get all items from the API."""
        return await self.hass.async_add_executor_job(self.openhab.fetch_all_items)

    async def async_get_item(self, item_name: str) -> dict[str, Any]:
        """Get item from the API."""
        return await self.hass.async_add_executor_job(self.openhab.get_item, item_name)

    async def async_send_command(self, item_name: str, command: str) -> None:
        """Set Item state"""
        item = await self.hass.async_add_executor_job(self.async_get_item, item_name)
        await item.command(command)

    async def async_update_item(self, item_name: str, command: str) -> None:
        """Set Item state"""
        item = await self.hass.async_add_executor_job(self.async_get_item, item_name)
        await item.update(command)
