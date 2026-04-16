# Calibration Strategy: Compass App MVP

## Hard-Iron Offset (Calibration Type)
Компенсация постоянного магнитного поля устройства.

## User Procedure (По-русски)
1.  Держать телефон горизонтально.
2.  Медленно вращать телефон по траектории "восьмерки" (figure-eight), охватывая все ориентации (X, Y, Z).
3.  Продолжать 15–30 секунд.
4.  Нажать кнопку "Save Calibration" в браузере.

## Algorithm (Min-Max)
- Собираем выборку `(mx, my, mz)`.
- Вычисляем `bias_x = (max(xs) + min(xs)) / 2.0` и т.д.
- `corrected_mag = raw_mag - bias`.

## Web UI Calibration Flow
1.  **Start**: `POST /calibrate` -> AppController переходит в `calibration_loop`.
2.  **Display**: SSE отправляет `event="calibration_start"`, UI показывает "CALIBRATING...".
3.  **End**: `POST /calibrate/save` (или тайм-аут) -> вычисление bias, сохранение в `calibration.json`, SSE `event="calibration_done"`.

## Storage
`calibration.json`:
```json
{
  "bias_x": 12.5,
  "bias_y": -3.2,
  "bias_z": 8.1,
  "timestamp_iso": "...",
  "sample_count": 342
}
```
