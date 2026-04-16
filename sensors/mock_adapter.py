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
        # Угловая частота
        omega = 2 * math.pi * self.freq_hz
        
        # Акселерометр: имитация легкого покачивания вокруг гравитации
        ax = math.sin(omega * t) * 0.5
        ay = math.cos(omega * t) * 0.5
        az = 9.81
        
        # Магнетометр: имитация вращения вокруг оси Z
        # Добавляем фазовый сдвиг pi/4
        phase = math.pi / 4
        mx = math.sin(omega * t + phase) * 30.0
        my = math.cos(omega * t + phase) * 30.0
        mz = 15.0
        
        return {
            "ax": ax, "ay": ay, "az": az,
            "mx": mx, "my": my, "mz": mz
        }

    def stop(self) -> None:
        log.info("MockAdapter stopped")
        self._start_time = None
