from __future__ import annotations

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .controller import LedController
from .const import DOMAIN
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Настройка платформы света."""
    config = entry.data
    
    # Создаем контроллер и устанавливаем серийный номер
    controller = LedController(host=config["host"])
    if "serial_number" in config:
        controller.set_serial_number(config["serial_number"])
    
    # Создаем координатор для проверки состояния устройства
    coordinator = H806SBCoordinator(hass, controller)
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([H806SBLight(coordinator, controller, config)])

class H806SBCoordinator(DataUpdateCoordinator):
    """Координатор для проверки состояния устройства."""
    
    def __init__(self, hass: HomeAssistant, controller: LedController):
        super().__init__(
            hass,
            _LOGGER,
            name="H806SB Device Status",
            update_interval=timedelta(seconds=30)
        )
        self.controller = controller
    
    async def _async_update_data(self) -> dict[str, Any]:
        """Проверка доступности устройства."""
        try:
            available = await self.controller.async_check_availability()
            return {"available": available}
        except Exception as err:
            _LOGGER.error("Error checking device status: %s", err)
            raise UpdateFailed(f"Error communicating with device: {err}")

class H806SBLight(CoordinatorEntity, LightEntity):
    """Реализация управления H806SB светом."""
    
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        controller: LedController,
        config: dict
    ) -> None:
        """Инициализация."""
        super().__init__(coordinator)
        self._controller = controller
        self._config = config
        self._attr_name = config.get("name", "H806SB Light")
        self._attr_unique_id = f"h806sb_{config['host']}"
        self._attr_is_on = False
        self._attr_brightness = 255
        self._attr_rgb_color = (255, 255, 255)
        self._default_speed = 80

    async def async_added_to_hass(self) -> None:
        """При добавлении в HA."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Обработка обновлений от координатора."""
        self._attr_available = self.coordinator.data.get("available", False)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Включение света с параметрами."""
        if not self._attr_available:
            raise HomeAssistantError("Device is not available")
        
        brightness = kwargs.get(ATTR_BRIGHTNESS, self._attr_brightness)
        device_brightness = int((brightness / 255) * 31)
        
        if ATTR_RGB_COLOR in kwargs:
            self._attr_rgb_color = kwargs[ATTR_RGB_COLOR]
            # Здесь можно добавить обработку RGB
        
        try:
            success = await self._controller.async_send_packet(
                brightness=device_brightness,
                speed=self._default_speed,
                is_on=True
            )
            if not success:
                raise HomeAssistantError("Failed to send command to device")
                
            self._attr_is_on = True
            self._attr_brightness = brightness
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error turning on light: %s", err)
            raise HomeAssistantError(f"Error turning on light: {err}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Выключение света."""
        if not self._attr_available:
            raise HomeAssistantError("Device is not available")
            
        try:
            success = await self._controller.async_send_packet(
                brightness=0,
                speed=0,
                is_on=False
            )
            if not success:
                raise HomeAssistantError("Failed to send command to device")
                
            self._attr_is_on = False
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error turning off light: %s", err)
            raise HomeAssistantError(f"Error turning off light: {err}")

    async def async_will_remove_from_hass(self) -> None:
        """Очистка при удалении интеграции."""
        await super().async_will_remove_from_hass()
        await self._controller.async_close()