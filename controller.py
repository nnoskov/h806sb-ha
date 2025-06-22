import asyncio
import socket
import logging
from typing import Optional

_LOGGER = logging.getLogger(__name__)

class LedController:
    """Управление LED устройством через UDP с поддержкой Home Assistant."""
    
    def __init__(self, host: str, port: int = 4626):
        self._host = host
        self._port = port
        self._command_counter = 0
        self._udp_socket = None
        self._serial_number = bytearray([0]*4)
        
        # Базовый пакет (как в вашем оригинальном коде)
        self._base_packet = bytearray([
            0xFB, 0xC1, 0x00, 0x50, 0x00, 0x01,
            0x00, 0xAE, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00
        ])
        _LOGGER.debug("Init of Led Controller completed!")

    async def async_initialize(self):
        """Инициализация сокета (вызывается при старте)."""
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.setblocking(False)
        _LOGGER.debug("UDP socket initialized for %s:%s", self._host, self._port)

    async def async_send_packet(self, brightness: int, speed: int, is_on: bool):
        """Отправка пакета на устройство."""
        if not self._udp_socket:
            await self.async_initialize()
            
        packet = bytearray(self._base_packet)
        packet[2] = (self._command_counter + 1) % 256
        packet[3] = max(1, min(100, speed))  # speed 1-100
        packet[4] = max(0, min(31, brightness))  # brightness 0-31
        packet[5] = 1 if is_on else 0
        packet[13:16] = self._serial_number
        
        try:
            await asyncio.get_event_loop().sock_sendto(
                self._udp_socket,
                packet,
                (self._host, self._port)
            )
            self._command_counter += 1
            _LOGGER.debug("Sent to %s:%s - %s", self._host, self._port, packet.hex())
            return True
        except Exception as err:
            _LOGGER.error("Error sending UDP packet: %s", err)
            return False
    
    async def async_check_availability(self, timeout: float = 2.0) -> bool:
        """Проверка доступности устройства с ожиданием ответа."""
        if not self._udp_socket:
            await self.async_initialize()
        
        # Создаем сокет для получения ответа
        loop = asyncio.get_event_loop()
        try:
            # Отправляем проверочный пакет (пример заголовка 0xAB 0x01)
            check_packet = bytearray([0xAB, 0x01, 0x00, 0x02]) + bytes(4) + self._serial_number
            _LOGGER.debug(f"Sending alive check packet: {check_packet.hex()}")
            self._udp_socket.sendto(check_packet, (self._host, self._port))
            
            # Ожидаем ответ с таймаутом
            data, _ = await asyncio.wait_for(
                loop.sock_recv(self._udp_socket, 12),
                timeout=timeout
            )
            _LOGGER.debug(f"Recived data: {data.hex()}")
            # Проверяем заголовок ответа (пример: должен начинаться с 0xFB 0xO1)
            return len(data) >= 2 and data[0] == 0xAB and data[1] == 0x01
        except (asyncio.TimeoutError, socket.error):
            return False


    async def async_close(self):
        """Очистка ресурсов."""
        if self._udp_socket:
            self._udp_socket.close()
            
    def set_serial_number(self, serial_number: str):
        """Setting the serial number with zero filling and reverse..
        
        Example:
            "0с3951" (3 bytes) -> filling to 4 bytes - "00 0с 39 51" -> revers to "51 39 0с 00"
        """
        try:
            # Converting hex-string to bytes
            serial_as_bytes = bytes.fromhex(serial_number)
            _LOGGER.debug(f"Original serial: {serial_as_bytes.hex(' ')}")
            
            # Filling by zero on left 
            if len(serial_as_bytes) < 4:
                padding = bytes(4 - len(serial_as_bytes))
                serial_as_bytes = padding + serial_as_bytes
                _LOGGER.debug(f"Padded serial: {serial_as_bytes.hex(' ')}")

            # Revesr of bytes (little-endian)
            reversed_serial = bytearray(reversed(serial_as_bytes))
            _LOGGER.debug(f"Final serial: {bytes(reversed_serial).hex(' ')}")
            self._serial_number[:] = reversed_serial
            
            _LOGGER.info(f"Serial number set: {self._serial_number.hex()}")
            
        except ValueError as ve:
            _LOGGER.error(f"Invalid serial number format: {ve}")
            raise
        except Exception as e:
            _LOGGER.error(f"Error setting serial: {e}")
            raise