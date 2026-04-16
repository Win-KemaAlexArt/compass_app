# Sensor Integration: Compass App MVP

## Discovery Method (Termux)
- Выполнить: `termux-sensor -l`.
- Найти по подстрокам `"accelerometer"` и `"magnetic"` в JSON выводе.

## Payload Schema (Termux)
```json
{
  "Sensor Name": {
    "values": [x, y, z]
  }
}
```

## Command Usage
- **Continuous**: `termux-sensor -s "accelerometer,magnetic" -d 100`.
- **Single-shot**: `termux-sensor -s "accelerometer,magnetic" -n 1`.
- **Cleanup**: `termux-sensor -c`.

## Coordinate System (Android Portrait)
- `X`: вправо (right edge).
- `Y`: вверх (top edge).
- `Z`: из экрана (perpendicular).
- Accelerometer: м/с².
- Magnetometer: мкТл (µT).

## Constraints
- **Zero Hardcode**: Не использовать полные имена датчиков.
- **Latency**: Флаг `-d 100` для стабильного 10Hz потока.
- **Battery**: `termux-wake-lock` для предотвращения сна.
