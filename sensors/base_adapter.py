import logging
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)

class BaseSensorAdapter(ABC):
    """
    Абстрактный базовый класс для адаптеров датчиков.
    Обеспечивает единый интерфейс для получения данных от реальных
    или эмулируемых сенсоров Android.
    """

    @abstractmethod
    def start(self) -> None:
        """
        Инициализирует и запускает поток данных от датчика.
        """
        pass

    @abstractmethod
    def read(self) -> dict | None:
        """
        Читает одно обновление данных от датчика.
        Возвращает словарь с сырыми значениями или None в случае ошибки.
        Пример: {"ax": 0.0, "ay": 0.0, "az": 9.81, "mx": 10.0, "my": -5.0, "mz": 2.0}
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Останавливает поток данных и освобождает ресурсы.
        """
        pass
