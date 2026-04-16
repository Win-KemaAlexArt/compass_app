import subprocess
import json
import logging
from sensors.base_adapter import BaseSensorAdapter

log = logging.getLogger(__name__)

class TermuxAdapter(BaseSensorAdapter):
    """
    Адаптер для датчиков Termux. Использует утилиту termux-sensor 
    через subprocess для получения данных в реальном времени.
    """

    def __init__(self, sensor_name: str, delay_ms: int = 100):
        self.sensor_name = sensor_name
        self.delay_ms = delay_ms
        self._process = None
        self._is_accel = "accel" in sensor_name.lower()
        self._is_mag = "magnet" in sensor_name.lower() or "magnetic" in sensor_name.lower()

    def start(self) -> None:
        """Запускает termux-sensor в режиме непрерывного потока."""
        cmd = ["termux-sensor", "-s", self.sensor_name, "-d", str(self.delay_ms)]
        log.info("Starting sensor: %s", " ".join(cmd))
        
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
        except FileNotFoundError:
            log.error("termux-sensor not found. Is termux-api installed?")
            raise

    def read(self) -> dict | None:
        """Читает одну строку из stdout процесса и парсит JSON."""
        if not self._process:
            log.warning("TermuxAdapter.read() called but process is not running")
            return None

        line = self._process.stdout.readline()
        if not line:
            return None

        line = line.strip()
        if not line:
            return None

        try:
            data = json.loads(line)
            # termux-sensor -s name может выводить данные как {"SensorName": {"values": [...]}}
            # или иногда просто {"values": [...]} в зависимости от версии/флагов.
            # Мы ищем первый объект с ключом 'values'.
            
            values = None
            if "values" in data:
                values = data["values"]
            else:
                # Ищем во вложенных объектах (по имени датчика)
                for sensor_data in data.values():
                    if isinstance(sensor_data, dict) and "values" in sensor_data:
                        values = sensor_data["values"]
                        break
            
            if values is None or len(values) < 3:
                log.warning("Malformed sensor data: %s", line)
                return None

            x, y, z = values[0], values[1], values[2]
            
            if self._is_accel:
                return {"ax": x, "ay": y, "az": z}
            elif self._is_mag:
                return {"mx": x, "my": y, "mz": z}
            else:
                return {"x": x, "y": y, "z": z}

        except json.JSONDecodeError:
            log.warning("Failed to decode sensor JSON: %s", line)
            return None
        except Exception as e:
            log.error("Unexpected error in TermuxAdapter.read: %s", e)
            return None

    def stop(self) -> None:
        """Останавливает процесс termux-sensor."""
        if self._process:
            log.info("Stopping sensor process for %s", self.sensor_name)
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                log.warning("Process for %s did not terminate, killing...", self.sensor_name)
                self._process.kill()
            self._process = None
