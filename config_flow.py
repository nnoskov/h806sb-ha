from homeassistant import config_entries, exceptions
from homeassistant.core import callback

import voluptuous as vol
import logging

from .discovery import H806SBDiscovery
from .controller import LedController
from .const import DOMAIN, CONFIG_VERSION

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register(DOMAIN)
class H806SBFlowHandler(config_entries.ConfigFlow):
    """Config flow for H806SB."""

    VERSION = CONFIG_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_option_flow(config_entry):
        """H806SB option callback."""
        _LOGGER.debug(f"GetOptionFlow:{config_entry}")
        return H806SBOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        device = await self.async_discover_devices()
        if not device:
            return self.async_abort(reason="no_devices_found")

        controller = LedController(host=device["ip"])
        controller.set_serial_number(device["serial"])

        try:
            if not await controller.async_check_availability():
                return self.async_abort(reason="device_unavailable")
            await self.async_set_unique_id(device["serial"])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"H806SB ({device['name']})",
                data={"host": device["ip"],
                      "serial_number": device["serial"],
                      "name": device["name"]
                },
            )
        finally:
            await controller.async_close()

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

class H806SBOptionsFlowHandler(config_entries.OptionsFlow):
    """Option flow for OpenRGB component."""
    
    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()