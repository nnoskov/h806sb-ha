from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
import logging

from .discovery import H806SBDiscovery
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class H806SBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for H806SB."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        device = await self.async_discover_devices()
        if not device:
            return self.async_abort(reason="no_devices_found")

        await self.async_set_unique_id(device["serial"])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"H806SB ({device['name']})",
            data={"host": device["ip"]},
        )

    async def async_discover_devices(self):
        """Discover devices."""
        discovery = H806SBDiscovery()
        try:
            device = await discovery.discover_device()
            if device:
                ip, serial, name = device
                _LOGGER.debug(f"Device found: {name} (IP: {ip})")
                return {"ip": ip, "serial": serial.hex(), "name": name}
            return None
        finally:
            discovery.close()