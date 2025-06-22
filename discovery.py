import asyncio
import socket
from typing import Optional, Tuple

class H806SBDiscovery:
    DEVICE_PORT = 4626
    LISTEN_PORT = 4882
    DISCOVERY_PACKET = bytes([0xAB, 0x01])
    RESPONSE_HEADER = bytes([0xAB, 0x02])

    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.bind(("0.0.0.0", self.LISTEN_PORT))
        self._sock.settimeout(5.0)  # Таймаут ожидания ответа

    async def discover_device(self, timeout: int = 5) -> Optional[Tuple[str, bytes, str]]:
        """Поиск устройства в сети."""
        try:
            # Отправляем broadcast-запрос
            self._sock.sendto(self.DISCOVERY_PACKET, ("<broadcast>", self.DEVICE_PORT))
            await asyncio.sleep(0.05)
            self._sock.sendto(self.DISCOVERY_PACKET, ("<broadcast>", self.DEVICE_PORT))

            # Ждём ответ
            data, addr = await asyncio.get_event_loop().sock_recvfrom(self._sock, 1024)
            
            if data.startswith(self.RESPONSE_HEADER):
                # Извлекаем имя устройства
                name_data = data[2:]
                name = name_data.split(b'\x00')[0].decode("ascii")
                
                # Парсим серийный номер (формат HCX_XXXXXX)
                if "_" in name:
                    _, hex_part = name.split("_", 1)
                    serial_number = bytes.fromhex(hex_part)
                    return (addr[0], serial_number, name)
        except (socket.timeout, ValueError, IndexError):
            pass
        return None

    def close(self):
        self._sock.close()