import math

def evaluate_confidence(frame, tilt_deg: float) -> str:
    """
    Оценивает качество сигнала на основе данных датчиков и текущего наклона.
    Возвращает "GOOD", "WARNING" или "POOR".
    """
    ax, ay, az = frame.ax, frame.ay, frame.az
    mx, my, mz = frame.mx, frame.my, frame.mz
    
    # 1. Магнитное поле (норма)
    mag_norm = math.sqrt(mx**2 + my**2 + mz**2)
    mag_state = "GOOD"
    if mag_norm < 15 or mag_norm > 120:
        mag_state = "POOR"
    elif mag_norm < 25 or mag_norm > 65:
        mag_state = "WARNING"
        
    # 2. Gimbal Lock (наклон)
    tilt_state = "GOOD"
    if tilt_deg > 75:
        tilt_state = "POOR"
    elif tilt_deg > 60:
        tilt_state = "WARNING"
        
    # 3. Gravity norm (стабильность акселерометра)
    accel_norm = math.sqrt(ax**2 + ay**2 + az**2)
    grav_diff = abs(accel_norm - 9.81)
    accel_state = "GOOD"
    if grav_diff > 3.0:
        accel_state = "POOR"
    elif grav_diff > 1.5:
        accel_state = "WARNING"
        
    # Приоритет худшего состояния
    states = [mag_state, tilt_state, accel_state]
    if "POOR" in states:
        return "POOR"
    if "WARNING" in states:
        return "WARNING"
    return "GOOD"
