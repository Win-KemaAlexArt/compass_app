import argparse
import logging
import os
import time
import signal
import sys
import json
import math
import threading

from sensors.mock_adapter import MockAdapter
from sensors.termux_adapter import TermuxAdapter
from core.orientation import compute_orientation, RawSensorFrame
from core.filters import CircularEMAFilter, EMAFilter
from core.calibration import CalibrationManager
from core.quality import evaluate_confidence
from ui import web_server
from ui.cli_view import render as cli_render

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("compass.main")

DIRECTIONS = [
    (0,   "N"),  (22.5, "NNE"), (45,  "NE"),  (67.5,  "ENE"),
    (90,  "E"),  (112.5,"ESE"), (135, "SE"),  (157.5, "SSE"),
    (180, "S"),  (202.5,"SSW"), (225, "SW"),  (247.5, "WSW"),
    (270, "W"),  (292.5,"WNW"), (315, "NW"),  (337.5, "NNW"),
]

def heading_to_cardinal(deg: float) -> str:
    deg = deg % 360
    for threshold, label in reversed(DIRECTIONS):
        if deg >= threshold - 11.25:
            return label
    return "N"

class AppController:
    def __init__(self, args):
        self.args = args
        storage_path = os.path.join(os.path.dirname(__file__), "calibration.json")
        self._cal = CalibrationManager(storage_path)
        
        # Инициализация фильтров
        self._heading_filter = CircularEMAFilter(alpha=0.15)
        self._pitch_filter = EMAFilter(alpha=0.3)
        self._roll_filter = EMAFilter(alpha=0.3)
        
        self._last_state = None
        self._running = False

    def _create_adapter(self):
        if self.args.mock:
            log.info("Using MockAdapter")
            return MockAdapter(freq_hz=10.0)
        else:
            log.info("Using TermuxAdapter")
            return TermuxAdapter("accelerometer,magnetic")

    def _process_frame(self, raw_dict: dict) -> dict | None:
        required_keys = {"ax", "ay", "az", "mx", "my", "mz"}
        if not required_keys.issubset(raw_dict.keys()):
            # log.debug("Incomplete sensor frame: %s", raw_dict.keys())
            return None
            
        # Применяем калибровку
        mx_raw, my_raw, mz_raw = raw_dict["mx"], raw_dict["my"], raw_dict["mz"]
        mx, my, mz = self._cal.apply(mx_raw, my_raw, mz_raw)
        
        frame = RawSensorFrame(
            ax=raw_dict["ax"], ay=raw_dict["ay"], az=raw_dict["az"],
            mx=mx, my=my, mz=mz
        )
        
        # Вычисляем ориентацию
        state = compute_orientation(frame)
        
        # Оцениваем качество
        confidence_str = evaluate_confidence(frame, state.tilt_deg)
        
        # Фильтруем значения
        heading = self._heading_filter.update(state.heading_deg)
        pitch = self._pitch_filter.update(state.pitch_deg)
        roll = self._roll_filter.update(state.roll_deg)
        
        mag_magnitude = math.sqrt(mx**2 + my**2 + mz**2)
        
        # Формируем SSE payload
        payload = {
            "heading": round(heading, 1),
            "azimuth": round(state.heading_deg, 1),
            "cardinal": heading_to_cardinal(heading),
            "confidence": 100.0 if confidence_str == "GOOD" else (50.0 if confidence_str == "WARNING" else 10.0),
            "conf_state": confidence_str,
            "pitch": round(pitch, 1),
            "roll": round(roll, 1),
            "mag_mag": round(mag_magnitude, 2),
            "ts": int(time.time_ns()),
            "is_gimbal_lock": state.is_gimbal_lock
        }
        
        self._last_state = payload
        return payload

    def run(self):
        self._cal.load()
        
        if not self.args.no_ui:
            web_server.start_server()
            time.sleep(0.5) # Даем Flask подняться
            
        adapter = self._create_adapter()
        adapter.start()
        
        self._running = True
        log.info("Compass App started (Mode: %s, Mock: %s)", self.args.mode, self.args.mock)
        
        try:
            while self._running:
                raw = adapter.read()
                
                if raw is None:
                    time.sleep(0.01)
                    continue
                
                payload = self._process_frame(raw)
                
                if payload is None:
                    continue
                
                # Диспетчеризация
                if not self.args.no_ui:
                    web_server.push_state(payload)
                
                if self.args.mode in ("cli", "both") or self.args.no_ui:
                    cli_render(payload)
                
                # Ограничение частоты цикла (max 20 Hz)
                time.sleep(0.05)
                
                # Проверка триггера калибровки
                if web_server.get_calibration_trigger().is_set():
                    self._run_calibration(adapter)
                    
        finally:
            log.info("Stopping compass...")
            adapter.stop()

    def _run_calibration(self, adapter):
        web_server.get_calibration_trigger().clear()
        
        # Анонсируем начало калибровки
        web_server.push_state({"event": "calibration_start"})
        self._cal.reset()
        
        log.info("CALIBRATION STARTED. Rotate device in figure-eight for 20 seconds.")
        
        start_time = time.time()
        # Собираем данные в течение 20 секунд (или пока не нажмут Save)
        while time.time() - start_time < 20:
            raw = adapter.read()
            if raw and "mx" in raw:
                self._cal.add_sample(raw["mx"], raw["my"], raw["mz"])
            
            # Если в процессе нажали Save раньше времени (опционально)
            if web_server.get_calibration_save_trigger().is_set():
                break
            time.sleep(0.01)
            
        log.info("Calibration collection finished. Waiting for Save trigger...")
        
        # Ждем нажатия Save в браузере (timeout 60s)
        if web_server.get_calibration_save_trigger().wait(timeout=60):
            try:
                self._cal.save()
                log.info("Calibration COMPLETED and SAVED.")
            except Exception as e:
                log.error("Calibration FAILED to save: %s", e)
            finally:
                web_server.get_calibration_save_trigger().clear()
        else:
            log.warning("Calibration TIMEOUT: No save trigger received.")
            
        # Анонсируем завершение
        web_server.push_state({"event": "calibration_done"})

def main():
    parser = argparse.ArgumentParser(description="Python Compass App (Android/Termux)")
    parser.add_argument("--mock", action="store_true", help="Use mock sensor data")
    parser.add_argument("--no-ui", action="store_true", help="Disable Web UI and Flask")
    parser.add_argument("--mode", choices=["web", "cli", "both"], default="web", help="Display mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    controller = AppController(args)

    def _shutdown(sig, frame):
        log.info("Interrupted. Shutting down...")
        controller._running = False
        # sys.exit(0) is handled by the main loop termination

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    controller.run()

if __name__ == "__main__":
    main()
