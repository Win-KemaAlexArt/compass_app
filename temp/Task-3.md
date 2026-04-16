```
# ЗАДАЧА: Phase 3 — Core Logic (Полная реализация)

## Контекст
Прочитай последовательно: `GEMINI.md` → `docs/progress.md` → `.agent/tasks/BACKLOG.md` → `docs/spec.md` (§3.2, §5–§11, §14) → `docs/calibration.md` → `docs/testing.md` → `docs/architecture.md`.

Phase 2 завершена. Адаптеры работают. Переходим к вычислительному ядру.

---

## Архитектурное решение перед стартом (зафикисруй как Decision-017)

`TermuxAdapter` в Phase 2 реализован под одиночный датчик (один процесс = один датчик).
Но `spec.md §3.2` требует запускать `termux-sensor -s "accelerometer,magnetic" -d 100` — один процесс, один JSON-объект содержит **оба** датчика сразу.

Зафиксируй `Decision-017` в `docs/decisions.md`:
- **Decision**: Для `AppController` использовать один `TermuxAdapter("accelerometer,magnetic")`, который читает комбинированный JSON и распаковывает оба датчика в одном `read()`.
- **Reason**: `spec.md §3.2` явно описывает этот паттерн. Два отдельных адаптера = два процесса = рассинхронизация временных меток, удвоенное потребление ресурсов.
- **Impact**: `TermuxAdapter.read()` должен возвращать dict с 6 ключами (`ax,ay,az,mx,my,mz`) из обоих датчиков. Логика определения ключей по `_is_accel`/`_is_mag` заменяется поиском ключей по substring.

После записи Decision-017 обнови `sensors/termux_adapter.py`: метод `read()` должен итерировать по всем ключам верхнего уровня JSON, определять тип каждого датчика по substring ("accel" → ax/ay/az, "magnet" → mx/my/mz) и возвращать **единый словарь** с 6 ключами. Если один из датчиков отсутствует в текущем JSON — вернуть `None` и логировать WARNING.

Добавь тест `test_termux_read_combined_json` в `tests/test_sensors.py`: мок readline() возвращает JSON с двумя датчиками `{"LSM6DSM Accelerometer": {"values": [1,2,3]}, "MMC5603NJ Magnetometer": {"values": [4,5,6]}}`. Проверь, что `read()` возвращает dict с ключами `ax=1, ay=2, az=3, mx=4, my=5, mz=6`.

---

## Задача 1: `core/orientation.py` — Tilt-Compensated Azimuth

Создай `core/orientation.py`. Используй только `math` и `numpy` (уже установлен через `pkg`).

### Датаклассы (используй `dataclasses.dataclass`):

```python
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
```

### Функция `compute_orientation(frame: RawSensorFrame) -> OrientationState`:

**Шаг 1 — Roll и Pitch из акселерометра:**
```
roll  = atan2(ay, az)
pitch = atan2(-ax, sqrt(ay² + az²))
```

**Шаг 2 — Tilt-Compensation магнетометра (поворот в горизонтальную плоскость):**
```
mx2 = mx*cos(pitch) + mz*sin(pitch)
my2 = mx*sin(roll)*sin(pitch) + my*cos(roll) - mz*sin(roll)*cos(pitch)
```

**Шаг 3 — Азимут:**
```
heading_rad = atan2(-my2, mx2)
heading_deg = degrees(heading_rad) % 360
```

**Шаг 4 — Gimbal Lock проверка:**
```
tilt_deg = degrees(acos(clamp(az / norm([ax,ay,az]), -1.0, 1.0)))
is_gimbal_lock = tilt_deg > 75.0
```

**Шаг 5 — confidence_state**: передать как параметр (по умолчанию "GOOD") — quality.py будет вычислять его отдельно. `compute_orientation` не оценивает качество сама.

**Edge case**: если норма вектора акселерометра < 0.1 (датчик не отвечает) — вернуть `OrientationState(heading_deg=0.0, pitch_deg=0.0, roll_deg=0.0, tilt_deg=0.0, confidence_state="POOR", is_gimbal_lock=False)`.

---

## Задача 2: `core/filters.py` — EMA с обёрткой углов

Создай `core/filters.py`. Только `math`, никакого `numpy`.

### Класс `EMAFilter`:
- `__init__(self, alpha: float = 0.2)`: коэффициент сглаживания (0 < alpha ≤ 1).
- `update(self, new_value: float) -> float`: EMA для **линейных** значений (pitch, roll, tilt).
- `_value`: текущее значение фильтра; `None` до первого вызова (первый вызов = инициализация без сглаживания).

### Класс `CircularEMAFilter` (наследует `EMAFilter`):
- Переопределяет `update(self, new_value: float) -> float` для угловых значений (heading 0–360).
- Алгоритм circular interpolation:
  ```
  delta = ((new_value - self._value) + 180) % 360 - 180
  self._value = (self._value + alpha * delta) % 360
  ```
- Это корректно обрабатывает переход 359° → 1°.

---

## Задача 3: `core/calibration.py` — Hard-Iron Offset

Создай `core/calibration.py`. Только `json`, `os`, `logging`.

### Класс `CalibrationManager`:
- `__init__(self, storage_path: str)`: путь к файлу `calibration.json`.
- `reset(self)`: очищает накопленные выборки, устанавливает `_samples = []`.
- `add_sample(self, mx: float, my: float, mz: float)`: добавляет точку в `_samples`.
- `compute(self) -> dict`: вычисляет bias по алгоритму Min-Max из `docs/calibration.md`. Возвращает `{"bias_x": …, "bias_y": …, "bias_z": …, "sample_count": N}`. Если `len(_samples) < 20` — возбуждает `ValueError("Insufficient samples")`.
- `save(self)`: записывает результат `compute()` + `timestamp_iso` в `storage_path` через `json.dump`.
- `load(self) -> dict | None`: загружает файл, возвращает dict или None если файл отсутствует.
- `apply(self, mx: float, my: float, mz: float) -> tuple[float,float,float]`: применяет сохранённый bias. Если калибровка не загружена — возвращает значения без изменений и логирует WARNING.

---

## Задача 4: `core/quality.py` — Confidence Scoring

Создай `core/quality.py`. Только `math`.

### Функция `evaluate_confidence(frame: RawSensorFrame, tilt_deg: float) -> str`:

Возвращает `"GOOD"`, `"WARNING"` или `"POOR"` по трём критериям:

**Критерий 1 — Магнитное поле (норма):**
```
mag_norm = sqrt(mx² + my² + mz²)
# Нормальный диапазон: 25–65 µT (типично для Земли)
# POOR если < 15 или > 120
# WARNING если < 25 или > 65
```

**Критерий 2 — Gimbal Lock:**
```
# WARNING если tilt_deg > 60°
# POOR если tilt_deg > 75°
```

**Критерий 3 — Gravity norm (стабильность акселерометра):**
```
accel_norm = sqrt(ax² + ay² + az²)
# POOR если отклонение от 9.81 > 3.0 (сильное движение/вибрация)
# WARNING если > 1.5
```

Логика приоритетов: если хоть один критерий POOR → вернуть "POOR". Если хоть один WARNING (и нет POOR) → "WARNING". Иначе → "GOOD".

---

## Задача 5: Unit-тесты для Core Logic (`tests/test_core.py`)

Создай `tests/test_core.py`. Только `unittest`, `math`.

### TestOrientationEngine:
- `test_heading_north`: frame с `ax=0, ay=0, az=9.81, mx=30, my=0, mz=0` → `heading_deg` ≈ 0° (±5°).
- `test_heading_east`: `mx=0, my=-30, mz=0` (при az=9.81) → heading ≈ 90° (±5°).
- `test_heading_south`: `mx=-30, my=0, mz=0` → heading ≈ 180° (±5°).
- `test_heading_west`: `mx=0, my=30, mz=0` → heading ≈ 270° (±5°).
- `test_gimbal_lock_detection`: frame с `ax=9.5, ay=0, az=1.0` → `is_gimbal_lock=True`.
- `test_zero_accel_returns_poor`: frame с `ax=0,ay=0,az=0` → `confidence_state="POOR"`.

### TestEMAFilter:
- `test_first_call_no_smoothing`: первый `update(100.0)` возвращает `100.0`.
- `test_smoothing_converges`: 50 вызовов `update(100.0)` начиная с `_value=0` → результат > 99.0.
- `test_circular_wraparound`: `CircularEMAFilter`, `_value=359.0`, `update(1.0)` → результат между 359.5 и 360.5 (или 0–1), а не ~180°.

### TestCalibrationManager:
- `test_compute_raises_on_insufficient_samples`: < 20 samples → `ValueError`.
- `test_compute_bias_correct`: 100 samples, `mx` от -10 до +10, `my` от -5 до +5, `mz` от -2 до +2 → `bias_x=0.0`, `bias_y=0.0`, `bias_z=0.0` (±0.01).
- `test_save_load_roundtrip`: `save()` → `load()` → bias совпадает с исходным. Использовать `tempfile.NamedTemporaryFile`.

### TestQualityEvaluator:
- `test_good_signal`: нормальный frame (az=9.81, mag_norm=40µT, tilt=10°) → "GOOD".
- `test_poor_magnetic_interference`: `mx=200, my=200, mz=200` (норма >> 120µT) → "POOR".
- `test_poor_gimbal_lock`: `tilt_deg=80°` → "POOR".

Запусти `python -m unittest tests/test_core.py -v`. Покажи вывод.

---

## Задача 6: Финальный коммит

1. `git add . && git commit -m "feat(core): Phase 3 complete — orientation/filters/calibration/quality + tests"`
2. `git push`
3. Обнови `docs/progress.md`: Phase 3 — COMPLETED, Current Phase → Phase 4 (UI & Server).
4. Запиши `Decision-018` в `docs/decisions.md`: выбор `math` вместо `numpy` для `filters.py` и `quality.py` — скалярные операции не требуют матричных вычислений, numpy нужен только для rotation matrix в `orientation.py`.
5. Очисти `CURRENT_SESSION.md`.
```