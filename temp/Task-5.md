```markdown
# ЗАДАЧА: Phase 4.5 — Починка окружения + venv + Расширенное тестирование

## Контекст
Прочитай: `GEMINI.md` → `docs/progress.md` → `.agent/tasks/BACKLOG.md`.

При запуске `python main.py` возникает `ModuleNotFoundError: No module named 'numpy'`.
Задача: диагностировать, починить окружение, организовать venv, провести полное тестирование.

---

## Задача 1: Диагностика и починка окружения

### 1a — Диагностика (выполни все команды, покажи весь вывод):
```bash
# Что за python используется
which python && python --version

# Что установлено в системном site-packages
pkg list-installed | grep -E "numpy|python"

# Где лежит numpy если установлен
find /data/data/com.termux/files/usr -name "numpy" -type d 2>/dev/null | head -5

# Текущий sys.path
python -c "import sys; [print(p) for p in sys.path]"

# Есть ли venv уже
ls -la | grep -E "venv|env"
```

### 1b — Установка numpy через pkg (ОБЯЗАТЕЛЬНО, не pip):
```bash
pkg install python-numpy -y
```

### 1c — Проверка после установки:
```bash
python -c "import numpy; print('numpy OK:', numpy.__version__)"
python -c "import flask; print('flask OK:', flask.__version__)"
```

---

## Задача 2: Создание venv с доступом к системному numpy

Согласно `docs/spec.md §3` и `CORE_RULES.md §3`: numpy устанавливается ТОЛЬКО через `pkg install` (Bionic libc ABI-совместимость). venv должен создаваться с флагом `--system-site-packages` чтобы numpy был доступен внутри venv, а остальные зависимости (flask) устанавливались изолированно.

```bash
# Создать venv с доступом к системным пакетам (numpy через pkg)
python -m venv venv --system-site-packages

# Активировать
source venv/bin/activate

# Убедиться что numpy видно из venv (из системного pkg)
python -c "import numpy; print('numpy from pkg:', numpy.__version__)"

# Установить flask внутри venv
pip install flask

# Проверить flask
python -c "import flask; print('flask in venv:', flask.__version__)"

# Показать что установлено в venv (должен быть только flask + его зависимости)
pip list
```

### Обновить `.gitignore`:
Добавь в `.gitignore` строку `venv/` если её ещё нет (проверь сначала: `cat .gitignore | grep venv`).

### Записать `Decision-020` в `docs/decisions.md`:
- **Decision**: venv создаётся с `--system-site-packages` для доступа к pkg-numpy.
- **Reason**: numpy установлен через `pkg install` в системный site-packages Termux (Bionic ABI). pip-версия numpy несовместима с Bionic libc. `--system-site-packages` — единственный способ использовать numpy в изолированном venv без перекомпиляции.
- **Impact**: `venv/` в `.gitignore`; активация: `source venv/bin/activate`; установка Flask: `pip install flask` внутри venv.

---

## Задача 3: Smoke-тесты (из venv)

Все тесты запускать **внутри активированного venv** (`source venv/bin/activate`).

### 3a — Unit-тесты (регрессия):
```bash
python -m unittest discover -s tests -v 2>&1 | tail -20
```
Ожидание: все тесты OK (их было 22 — 7 sensor + 15 core).

### 3b — CLI smoke-тест:
```bash
timeout 5 python main.py --mock --no-ui 2>&1 | head -15
```
Ожидание: строки `[Compass] HDG: X.X°...` без ошибок импорта.

### 3c — Web smoke-тест (запуск + curl):
```bash
# Запустить в фоне
python main.py --mock --mode web > /tmp/compass.log 2>&1 &
COMPASS_PID=$!
sleep 3

# Проверить что запустился
curl -s http://localhost:8080/health
echo ""

# Проверить SSE поток (3 события)
curl -N --max-time 4 http://localhost:8080/stream 2>/dev/null | head -6

# Проверить index.html отдаётся
curl -s http://localhost:8080/ | grep -c "EventSource"

# Проверить calibrate endpoint
curl -s -X POST http://localhost:8080/calibrate

# Завершить
kill $COMPASS_PID 2>/dev/null
cat /tmp/compass.log | head -10
```

Ожидание:
- `/health` → `{"listeners": N, "status": "ok"}` 
- SSE → 3+ строки `data: {"heading":...}`
- index.html grep → `1`
- calibrate → `{"status": "calibration_triggered"}`

---

## Задача 4: Интеграционные тесты (`tests/test_integration.py`)

Создай `tests/test_integration.py`. Только `unittest`, `threading`, `time`, `json`. Никаких внешних зависимостей кроме flask (уже в venv).

Это тесты полного пайплайна: MockAdapter → core → web_server → SSE.

### TestPipelineIntegration:

**`setUp`**: импортирует и сбрасывает состояние `web_server` (создаёт новый `CompassStateAnnouncer` для изоляции тестов).

**`test_full_pipeline_mock_to_orientation`**:
- Создаёт `MockAdapter(freq_hz=1.0)`, вызывает `start()`.
- Читает 5 фреймов через `read()`.
- Каждый фрейм прогоняет через `compute_orientation(RawSensorFrame(...))`.
- Проверяет: все 5 результатов имеют `0 <= heading_deg < 360`.
- Проверяет: хотя бы 2 из 5 фреймов имеют разные `heading_deg` (синусоида движется).

**`test_filter_reduces_jitter`**:
- Создаёт `CircularEMAFilter(alpha=0.15)`.
- Подаёт 20 значений: чередующихся `355.0` и `5.0` (переход через 0°).
- Проверяет: финальное значение фильтра между `350` и `10` (не прыгнуло к 180°).

**`test_calibration_apply_corrects_values`**:
- Создаёт `CalibrationManager` с `tempfile`.
- Добавляет 30 сэмплов: mx от -20 до +20, my от -10 до +10, mz от -5 до +5.
- Вызывает `save()`.
- Создаёт новый `CalibrationManager`, загружает через `load()`.
- Применяет `apply(20.0, 10.0, 5.0)` → результат должен быть ≈ `(20.0, 10.0, 5.0)` (bias≈0 для симметричных данных).

**`test_quality_pipeline_good_signal`**:
- Создаёт `RawSensorFrame` с `az=9.81`, mag_norm ≈ 45µT.
- Прогоняет через `compute_orientation` → получает `tilt_deg`.
- Прогоняет через `evaluate_confidence(frame, tilt_deg)`.
- Проверяет: результат `"GOOD"`.

**`test_web_server_push_receive`**:
- Импортирует `web_server`, создаёт новый `CompassStateAnnouncer` и присваивает `web_server.announcer = новый`.
- Вызывает `q = web_server.announcer.listen()`.
- Вызывает `web_server.push_state({"heading": 45.0, "cardinal": "NE", "conf_state": "GOOD", "confidence": 90.0, "pitch": 0.0, "roll": 0.0, "mag_mag": 45.0, "azimuth": 45.0, "ts": 0})`.
- Читает из `q.get(timeout=1)`.
- Парсит SSE-строку: извлекает JSON после `data: `.
- Проверяет: `parsed["heading"] == 45.0`.

### TestGracefulDegradation:

**`test_none_frame_does_not_crash`**:
- Создаёт `MockAdapter`, вызывает `start()`.
- Мокирует `adapter.read` чтобы возвращал `None`.
- Имитирует цикл `_process_frame` из `main.py`: если `raw is None` → `continue`.
- Проверяет: никакого исключения за 10 итераций.

**`test_poor_quality_on_magnetic_interference`**:
- Создаёт frame с `mx=200, my=200, mz=200` (сильная интерференция, норма >> 120µT).
- `compute_orientation(frame)` → получает `tilt_deg`.
- `evaluate_confidence(frame, tilt_deg)` → проверяет `"POOR"`.

Запусти все тесты:
```bash
python -m unittest discover -s tests -v 2>&1 | tail -30
```

---

## Задача 5: E2E тест с измерением покрытия кода

### 5a — Установить coverage (внутри venv):
```bash
pip install coverage
```

### 5b — Запустить все тесты с измерением покрытия:
```bash
python -m coverage run --source=core,sensors,ui -m unittest discover -s tests -v
python -m coverage report --show-missing
```

### 5c — Анализ результата:
Покажи полный вывод `coverage report`. 

Если покрытие модулей ниже пороговых значений — зафикисруй как `Decision-021` с указанием каких именно строк не хватает (из колонки `Missing`):
- `core/orientation.py` — цель ≥ 85%
- `core/filters.py` — цель ≥ 90%
- `core/calibration.py` — цель ≥ 80%
- `core/quality.py` — цель ≥ 90%
- `sensors/mock_adapter.py` — цель ≥ 85%
- `sensors/termux_adapter.py` — цель ≥ 70% (subprocess сложно тестировать)
- `ui/web_server.py` — цель ≥ 50% (Flask routes сложно без test client)

---

## Задача 6: Финальный коммит

1. `git add . && git commit -m "fix(env): venv with --system-site-packages; feat(tests): integration + e2e + coverage"`
2. `git push`
3. Обнови `docs/progress.md`: добавь "Phase 4.5: Environment fix + Integration tests completed".
4. Запиши `Decision-021` в `docs/decisions.md` с результатами coverage (что покрыто, что нет, план на Phase 5).
5. Очисти `CURRENT_SESSION.md`.
```