```markdown
# ЗАДАЧА: Phase 2 — Sensors (Полная реализация)

## Контекст
Прочитай последовательно: `GEMINI.md` → `docs/progress.md` → `.agent/tasks/BACKLOG.md` → `docs/spec.md` → `docs/sensors.md` → `docs/api.md`.

Pre-Phase 2 Prep завершена. Git инициализирован. Unit-тесты для заглушек проходят.
Текущие файлы `sensors/mock_adapter.py` и `sensors/termux_adapter.py` — минимальные заглушки. Их нужно заменить полноценными реализациями.

---

## Задача 1: `sensors/base_adapter.py` — Абстрактный интерфейс

Создай файл `sensors/base_adapter.py`:
- Абстрактный класс `BaseSensorAdapter` с методами:
  - `@abstractmethod start(self) -> None`
  - `@abstractmethod read(self) -> dict | None`
  - `@abstractmethod stop(self) -> None`
- Документация (docstring) для каждого метода.
- Импорт: только `abc`.

---

## Задача 2: `sensors/mock_adapter.py` — Полноценная замена заглушки

Перепиши `sensors/mock_adapter.py`, наследуя от `BaseSensorAdapter`:
- `__init__(self, freq_hz: float = 1.0)`: инициализация.
- `start(self)`: записывает `self._start_time = time.time()`.
- `read(self) -> dict`: возвращает dict со всеми 6 ключами (`ax, ay, az, mx, my, mz`). Используй `sin/cos` от `(time.time() - self._start_time) * 2π * freq_hz`.
  - `ax = sin(t)`, `ay = cos(t)`, `az = 9.81` (гравитация константа)
  - `mx = sin(t + π/4)`, `my = cos(t + π/4)`, `mz = 0.0`
- `stop(self)`: `pass` (нет ресурсов для освобождения).
- Логирование через `logging` (не `print`).

---

## Задача 3: `sensors/termux_adapter.py` — Полноценная замена заглушки

Перепиши `sensors/termux_adapter.py`, наследуя от `BaseSensorAdapter`. Согласно `docs/sensors.md` и `docs/spec.md` — используй `termux-sensor` через `subprocess`.

Требования:
- `__init__(self, sensor_name: str)`: сохраняет имя датчика, `self._process = None`.
- `start(self) -> None`: запускает `termux-sensor -s <sensor_name>` (без `-n 1` — непрерывный поток). `stdout=PIPE`, `stderr=PIPE`, `text=True`.
- `read(self) -> dict | None`: читает одну строку из `self._process.stdout`. Парсит JSON. Формат ответа `termux-sensor`: `{"values": [x, y, z]}` — распакуй в dict с ключами `ax/ay/az` (акселерометр) или `mx/my/mz` (магнетометр) в зависимости от `sensor_name`. Если JSON невалидный или строка пустая — возвращает `None`, логирует WARNING.
- `stop(self) -> None`: вызывает `self._process.terminate()` и `self._process.wait()` если `_process` не None.
- Всё логирование через `logging`.

---

## Задача 4: Обновление unit-тестов `tests/test_sensors.py`

Заглушки заменены полноценными реализациями. Обнови тесты:

**Группа A (MockAdapter)** — существующие 3 теста должны продолжать проходить. Добавь:
- `test_mock_start_sets_start_time`: после `start()` атрибут `_start_time` существует и является `float`.

**Группа B (TermuxAdapter)** — обнови моки под новую реализацию (непрерывный поток, `readline()` вместо `communicate()`):
- `test_termux_read_parses_valid_json`: мок `Popen`, `stdout.readline()` возвращает `'{"values": [1.0, 2.0, 3.0]}\n'`. Проверь, что `read()` возвращает dict (не None).
- `test_termux_read_handles_malformed_json`: `readline()` возвращает `'error: sensor not found\n'`. Проверь, что `read()` возвращает `None`.
- `test_termux_stop_terminates_process`: после `stop()` проверь, что `terminate()` вызван один раз.

Запусти `python -m unittest tests/test_sensors.py -v`. Покажи вывод.

---

## Задача 5: Финальный коммит

1. `git add . && git commit -m "feat(sensors): Phase 2 complete — base/mock/termux adapters + unit tests"`
2. `git push`
3. Обнови `docs/progress.md`: Phase 2 (Sensors) — статус COMPLETED.
4. Запиши `Decision-016` в `docs/decisions.md`: выбор `readline()` вместо `communicate()` для непрерывного потока `termux-sensor`.
5. Очисти `CURRENT_SESSION.md`.
```