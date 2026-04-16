import subprocess
import json
import logging
from sensors.base_adapter import BaseSensorAdapter

log = logging.getLogger(__name__)

class TermuxAdapter(BaseSensorAdapter):
    """
    Адаптер для датчиков Termux. Использует утилиту termux-sensor 
    через subprocess для получения данных в реальном времени.
    Поддерживает чтение одного или нескольких датчиков одновременно.
    """

    def __init__(self, sensor_name: str, delay_ms: int = 100):
        self.sensor_name = sensor_name
        self.delay_ms = delay_ms
        self._process = None

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
        """
        Читает одну строку из stdout процесса и парсит JSON.
        Возвращает комбинированный словарь данных для всех запрошенных датчиков.
        """
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
            result = {}
            
            # termux-sensor выводит объект, где ключи - имена датчиков
            for sensor_full_name, sensor_data in data.items():
                if not isinstance(sensor_data, dict) or "values" not in sensor_data:
                    continue
                
                vals = sensor_data["values"]
                if len(vals) < 3:
                    continue
                
                name_low = sensor_full_name.lower()
                if "accel" in name_low:
                    result.update({"ax": vals[0], "ay": vals[1], "az": vals[2]})
                elif "magnet" in name_low:
                    result.update({"mx": vals[0], "my": vals[1], "mz": vals[2]})
                else:
                    # Если датчик неизвестен, сохраняем как есть
                    result[sensor_full_name] = vals

            if not result:
                log.warning("No valid sensor data found in JSON: %s", line)
                return None
                
            return result

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
