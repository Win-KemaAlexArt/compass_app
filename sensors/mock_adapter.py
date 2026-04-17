import math
import time
import logging
from sensors.base_adapter import BaseSensorAdapter

log = logging.getLogger(__name__)

class MockAdapter(BaseSensorAdapter):
    """
    Эмулятор датчиков. Генерирует детерминированные значения на основе синусоид
    для тестирования Core Logic без доступа к реальному железу.
    """

    def __init__(self, freq_hz: float = 1.0):
        self.freq_hz = freq_hz
        self._start_time = None

    def start(self) -> None:
        log.info("MockAdapter started with freq=%s Hz", self.freq_hz)
        self._start_time = time.time()

    def read(self) -> dict | None:
        if self._start_time is None:
            log.warning("MockAdapter read() called before start()")
            return None

        t = time.time() - self._start_time
        
        # Имитируем медленное вращение: 1 оборот за 10 секунд (0.1 Гц)
        rotation_freq = 0.1 
        omega = 2 * math.pi * rotation_freq
        
        # Акселерометр: почти статичен (устройство лежит ровно)
        ax, ay, az = 0.0, 0.0, 9.81
        
        # Магнетометр: вращается в плоскости XY
        mx = math.sin(omega * t) * 30.0
        my = math.cos(omega * t) * 30.0
        mz = 15.0
        
        return {
            "ax": ax, "ay": ay, "az": az,
            "mx": mx, "my": my, "mz": mz
        }

    def stop(self) -> None:
        log.info("MockAdapter stopped")
        self._start_time = None
