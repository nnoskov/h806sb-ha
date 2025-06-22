"""The H806SB Led Controller integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .discovery import H806SBDiscovery

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[Platform] = [Platform.LIGHT]

async def async_setup(hass: HomeAssistant, config: dict):
    """Setting integration by configuration.yaml."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setting up from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    """Settings integration by UI."""
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True

async def async_discover_devices():
    """Discover devices of H806SB in network."""
    discovery = H806SBDiscovery()
    try:
        device = await discovery.discover_device()
        if device:
            ip, serial, name = device
            _LOGGER.debug(f"Device found: {name} (IP: {ip})")
            return {"ip": ip, "serial": serial.hex(), "name": name}
    finally:
        discovery.close()