import json
import os
import logging
from datetime import datetime

log = logging.getLogger(__name__)

class CalibrationManager:
    """
    Управление калибровкой магнетометра (Hard-Iron Offset).
    Накапливает выборки и вычисляет смещение по осям.
    """
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self._samples = []
        self._bias = {"bias_x": 0.0, "bias_y": 0.0, "bias_z": 0.0}
        self.is_loaded = False

    def reset(self):
        """Очищает накопленные выборки."""
        self._samples = []
        log.info("Calibration samples reset")

    def add_sample(self, mx: float, my: float, mz: float):
        """Добавляет точку данных для калибровки."""
        self._samples.append((mx, my, mz))

    def compute(self) -> dict:
        """
        Вычисляет bias по алгоритму Min-Max.
        Требует минимум 20 выборок.
        """
        if len(self._samples) < 20:
            raise ValueError("Insufficient samples. Need at least 20.")
        
        xs = [s[0] for s in self._samples]
        ys = [s[1] for s in self._samples]
        zs = [s[2] for s in self._samples]
        
        bias = {
            "bias_x": (max(xs) + min(xs)) / 2.0,
            "bias_y": (max(ys) + min(ys)) / 2.0,
            "bias_z": (max(zs) + min(zs)) / 2.0,
            "sample_count": len(self._samples),
            "timestamp_iso": datetime.now().isoformat()  # Using now() for simplicity as datetime.UTC might not be available in older Python
        }
        self._bias = {k: bias[k] for k in ["bias_x", "bias_y", "bias_z"]}
        return bias

    def save(self):
        """Вычисляет и сохраняет калибровку в файл."""
        try:
            data = self.compute()
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            log.info("Calibration saved to %s", self.storage_path)
            self.is_loaded = True
        except Exception as e:
            log.error("Failed to save calibration: %s", e)
            raise

    def load(self) -> dict | None:
        """Загружает калибровку из файла."""
        if not os.path.exists(self.storage_path):
            log.warning("Calibration file %s not found", self.storage_path)
            return None
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            self._bias = {
                "bias_x": data.get("bias_x", 0.0),
                "bias_y": data.get("bias_y", 0.0),
                "bias_z": data.get("bias_z", 0.0)
            }
            self.is_loaded = True
            log.info("Calibration loaded from %s", self.storage_path)
            return data
        except Exception as e:
            log.error("Failed to load calibration: %s", e)
            return None

    def apply(self, mx: float, my: float, mz: float) -> tuple[float, float, float]:
        """Применяет текущий bias к сырым данным магнетометра."""
        if not self.is_loaded:
            # log.warning only once to avoid spamming 10Hz stream
            pass 
        
        return (
            mx - self._bias["bias_x"],
            my - self._bias["bias_y"],
            mz - self._bias["bias_z"]
        )
