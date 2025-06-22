from __future__ import annotations

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the H806SB light platform."""
    # Здесь должна быть логика инициализации вашего устройства
    # Например:
    host = entry.data["host"]
    async_add_entities([H806SBLight(host)])

class H806SBLight(LightEntity):
    """Representation of an H806SB Light."""

    def __init__(self, host: str) -> None:
        """Initialize the light."""
        self._host = host
        self._attr_name = "H806SB Light"
        self._attr_unique_id = f"h806sb_{host}"
        self._attr_color_mode = ColorMode.RGB
        self._attr_supported_color_modes = {ColorMode.RGB}
        self._attr_is_on = False
        self._attr_brightness = 255
        self._attr_rgb_color = (255, 255, 255)

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        # Реализация включения света
        self._attr_is_on = True
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_RGB_COLOR in kwargs:
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        # Реализация выключения света
        self._attr_is_on = False
        self.async_write_ha_state()