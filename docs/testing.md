# Testing Strategy: Compass App MVP

## Unit Tests
- `orientation.py`: Проверка азимута при известных векторах (N, E, S, W, Tilted).
- `filters.py`: Проверка EMA circular wrap-around (359° -> 1°).
- `quality.py`: Проверка scoring (interference, stability, tilt).
- `web_server.py`: Проверка SSE payload формата (JSON).

## Integration Tests
- `Termux Sensor -> orientation -> SSE -> browser`.
- `Calibration Flow`: POST /calibrate -> loop -> POST /save -> JSON file.
- `Graceful Shutdown`: SIGINT -> sensor cleanup -> Flask stop.
- `Browser Reconnect`: EventSource auto-retry.

## Manual Test Scenarios
1.  **Horizontal North**: Телефон на плоскости, нос на север.
2.  **Tilt Test (45°)**: Азимут стабилен при наклоне.
3.  **Metal Interference**: Металл рядом -> POOR confidence.
4.  **Gimbal Lock (80°)**: Предупреждение TILT! в браузере.
5.  **Browser Resume**: Закрыть/открыть вкладку -> данные возобновляются.

## Runtime Validation (Termux)
```bash
# Тест датчиков
termux-sensor -l
termux-sensor -s "accelerometer,magnetic" -n 1

# Тест Web сервера
python main.py --mock --mode web
curl http://localhost:8080/stream
```
