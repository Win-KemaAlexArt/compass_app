```markdown
# ЗАДАЧА: Предстартовая подготовка к Phase 2 (Sensors)

## Контекст
Прочитай последовательно: `GEMINI.md` → `.agent/rules/CORE_RULES.md` → `docs/progress.md` → `.agent/tasks/BACKLOG.md` → `docs/decisions.md` → `docs/spec.md`.

Текущее состояние: Phase 1 завершена, Phase 2 (Sensors) — следующий этап.

## Цель сессии
Выполнить три подготовительных задачи перед написанием кода Phase 2. После каждой задачи обновить `docs/progress.md` и записать решение в `docs/decisions.md`.

---

## Задача 1: Инициализация Git-репозитория

1. В корне проекта выполни `git init`.
2. Создай `.gitignore` со следующими секциями:
   - Python: `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, `.Python`
   - Virtual environments: `venv/`, `.venv/`, `env/`, `ENV/`
   - Termux-specific: `*.egg-info/`, `dist/`, `build/`
   - Project-specific: `CURRENT_SESSION.md` (эфемерный файл, не должен попадать в VCS)
   - Logs: `*.log`
3. Выполни первый коммит: `git add . && git commit -m "chore: initial project scaffold (Phase 1 complete)"`
4. Запиши `Decision-014` в `docs/decisions.md`.

---

## Задача 2: Дополнение `docs/api.md` недостающими интерфейсами

Текущий `docs/api.md` описывает только `sensors/base_adapter.py`. Добавь документацию для:

1. **`sensors/mock_adapter.py`**: Метод `__init__(freq_hz: float = 1.0)` — частота синусоиды. Метод `read() -> dict` — возвращает детерминированные значения `{"ax":…, "ay":…, "az":…, "mx":…, "my":…, "mz":…}` на основе `sin/cos` от текущего времени.
2. **`sensors/termux_adapter.py`**: Метод `__init__(sensor_name: str)`. Метод `start()` — запускает `termux-sensor -s <name> -n 1` через `subprocess`. Метод `read() -> dict` — парсит JSON-вывод из stdout. Метод `stop()` — завершает subprocess.
3. **`ui/cli_view.py`**: Функция `render(state: dict) -> None` — выводит форматированную строку компаса в stdout (для отладки без браузера). Формат вывода: `[Compass] HDG: {hdg:.1f}° | Tilt: {pitch:.1f}/{roll:.1f} | Cal: {calibrated}`.

---

## Задача 3: Создание unit-тестов для сенсоров (`tests/test_sensors.py`)

Создай файл `tests/test_sensors.py`. Используй только стандартную библиотеку (`unittest`, `unittest.mock`) — никаких `pytest` и других внешних зависимостей.

Напиши следующие тест-кейсы:

**Группа A — MockAdapter (детерминированность):**
- `test_mock_read_returns_all_keys`: `read()` возвращает dict с ключами `ax, ay, az, mx, my, mz`.
- `test_mock_read_returns_floats`: Все значения имеют тип `float`.
- `test_mock_sinusoid_changes_over_time`: Два вызова `read()` с задержкой `time.sleep(0.1)` возвращают разные значения (синусоида движется).

**Группа B — TermuxAdapter (изоляция от реального железа через mock):**
- `test_termux_read_parses_valid_json`: Мокируй `subprocess.Popen`. Stdout возвращает валидный JSON `termux-sensor` формата `{"values": [1.0, 2.0, 3.0]}`. Проверь, что `read()` корректно распаковывает значения.
- `test_termux_read_handles_malformed_json`: Stdout возвращает `b"error: sensor not found"`. Проверь, что `read()` возвращает `None` (или бросает кастомное исключение) без крэша.
- `test_termux_stop_terminates_process`: После вызова `stop()` проверь, что `subprocess.Popen.terminate()` был вызван ровно один раз.

После создания файла выполни `python -m unittest tests/test_sensors.py -v` и покажи вывод.
Запиши `Decision-015` в `docs/decisions.md`.

---

## Финальный шаг

После выполнения всех трёх задач:
1. Обнови `docs/progress.md`: Отметь "Pre-Phase 2 Prep" как завершённый этап.
2. Очисти `CURRENT_SESSION.md` (согласно lifecycle contract из Decision-008).
3. Выведи краткий итог на русском: что сделано, статус тестов, готовность к Phase 2.
```