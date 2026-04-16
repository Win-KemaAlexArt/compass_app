import math
import numpy as np
from dataclasses import dataclass

@dataclass
class RawSensorFrame:
    ax: float; ay: float; az: float  # акселерометр (m/s²)
    mx: float; my: float; mz: float  # магнетометр (µT)

@dataclass  
class OrientationState:
    heading_deg: float       # 0–360, магнитный азимут
    pitch_deg: float         # угол тангажа
    roll_deg: float          # угол крена
    tilt_deg: float          # общий наклон от горизонта
    confidence_state: str    # "GOOD" / "WARNING" / "POOR"
    is_gimbal_lock: bool      # True если tilt_deg > 75°

def compute_orientation(frame: RawSensorFrame, confidence: str = "GOOD") -> OrientationState:
    """
    Вычисляет ориентацию на основе данных акселерометра и магнетометра.
    Применяет компенсацию наклона (tilt-compensation).
    """
    ax, ay, az = frame.ax, frame.ay, frame.az
    mx, my, mz = frame.mx, frame.my, frame.mz
    
    # Проверка на работоспособность акселерометра
    accel_vec = np.array([ax, ay, az])
    accel_norm = np.linalg.norm(accel_vec)
    
    if accel_norm < 0.1:
        return OrientationState(
            heading_deg=0.0, pitch_deg=0.0, roll_deg=0.0, 
            tilt_deg=0.0, confidence_state="POOR", is_gimbal_lock=False
        )

    # Шаг 1 — Roll и Pitch из акселерометра
    # roll: угол вокруг оси Y
    roll = math.atan2(ay, az)
    # pitch: угол вокруг оси X
    pitch = math.atan2(-ax, math.sqrt(ay**2 + az**2))

    # Шаг 2 — Tilt-Compensation магнетометра
    # Используем формулы из Task-3.md
    cos_p, sin_p = math.cos(pitch), math.sin(pitch)
    cos_r, sin_r = math.cos(roll), math.sin(roll)
    
    mx2 = mx * cos_p + mz * sin_p
    my2 = mx * sin_r * sin_p + my * cos_r - mz * sin_r * cos_p
    
    # Шаг 3 — Азимут
    heading_rad = math.atan2(-my2, mx2)
    heading_deg = math.degrees(heading_rad) % 360.0

    # Шаг 4 — Gimbal Lock проверка
    # Общий наклон от горизонтали (угол между вектором гравитации и осью Z)
    # az / norm([ax,ay,az]) это cos угла отклонения от вертикали
    tilt_rad = math.acos(max(-1.0, min(1.0, az / accel_norm)))
    tilt_deg = math.degrees(tilt_rad)
    is_gimbal_lock = tilt_deg > 75.0

    return OrientationState(
        heading_deg=heading_deg,
        pitch_deg=math.degrees(pitch),
        roll_deg=math.degrees(roll),
        tilt_deg=tilt_deg,
        confidence_state=confidence,
        is_gimbal_lock=is_gimbal_lock
    )
