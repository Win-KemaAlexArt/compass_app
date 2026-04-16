import math

class EMAFilter:
    """
    Экспоненциальное скользящее среднее (Exponential Moving Average).
    Используется для сглаживания линейных величин.
    """
    def __init__(self, alpha: float = 0.2):
        if not (0 < alpha <= 1.0):
            raise ValueError("Alpha must be in range (0, 1.0]")
        self.alpha = alpha
        self._value = None

    def update(self, new_value: float) -> float:
        if self._value is None:
            self._value = new_value
        else:
            self._value = self._value + self.alpha * (new_value - self._value)
        return self._value

class CircularEMAFilter(EMAFilter):
    """
    EMA фильтр для круговых величин (градусы 0-360).
    Учитывает переход через 0/360 с использованием кратчайшего пути.
    """
    def update(self, new_value: float) -> float:
        if self._value is None:
            self._value = new_value % 360
        else:
            # Кратчайшее расстояние между углами
            delta = ((new_value - self._value) + 180) % 360 - 180
            self._value = (self._value + self.alpha * delta) % 360
        return self._value
