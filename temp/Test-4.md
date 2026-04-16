```markdown
# ЗАДАЧА: Phase 4 — UI & Server + AppController (Точка сборки)

## Контекст
Прочитай последовательно: `GEMINI.md` → `docs/progress.md` → `.agent/tasks/BACKLOG.md` → `docs/spec.md` (§3.3, §7.3, §8, §10, §16, §17, §28, §29, §30) → `docs/architecture.md`.

Phase 3 завершена. Все модули `core/` и `sensors/` реализованы и протестированы.
Phase 4 — точка финальной сборки. Результат: запускаемый компас `python main.py --mock`.

---

## Задача 1: `ui/web_server.py` — Flask + SSE + CompassStateAnnouncer

Создай `ui/web_server.py`. Скопируй архитектуру **точно** из `spec.md §3.3`.

### Требования:

**Класс `CompassStateAnnouncer`** (из spec.md §3.3 — не изобретать заново):
- `__init__`: `self._listeners: list[queue.Queue] = []`, `self._lock = threading.Lock()`.
- `listen() -> queue.Queue`: создаёт `queue.Queue(maxsize=5)`, добавляет в `_listeners` под локом, возвращает.
- `announce(msg: str) -> None`: под локом итерирует `_listeners`, вызывает `q.put_nowait(msg)`, собирает индексы переполненных очередей (`queue.Full`), удаляет их в обратном порядке.

**Глобальные объекты модуля:**
```python
announcer = CompassStateAnnouncer()
_calibration_trigger = threading.Event()
_calibration_save_trigger = threading.Event()
```

**Flask маршруты:**
- `GET /` → `send_from_directory` отдаёт `ui/static/index.html`. Путь вычисляется динамически через `os.path.join(os.path.dirname(__file__), "static")` — без хардкода.
- `GET /stream` → бесконечный SSE-генератор. `messages = announcer.listen()`. Цикл: `messages.get(timeout=15)` → `yield _format_sse(msg)`. При `queue.Empty` (timeout) → `yield _format_sse("{}", event="heartbeat")`. `mimetype="text/event-stream"`, headers `Cache-Control: no-cache` и `X-Accel-Buffering: no`.
- `POST /calibrate` → `_calibration_trigger.set()`, возвращает `{"status": "calibration_triggered"}, 202`.
- `POST /calibrate/save` → `_calibration_save_trigger.set()`, возвращает `{"status": "save_triggered"}, 202`.
- `GET /health` → `{"status": "ok", "listeners": len(announcer._listeners)}, 200`.

**Функция `push_state(state_dict: dict) -> None`**:
- Принимает словарь OrientationState-совместимых данных.
- Форматирует SSE-сообщение: `_format_sse(json.dumps(state_dict))`.
- Вызывает `announcer.announce(msg)`.

**Функция `start_server(port: int = 8080) -> None`**:
- Читает порт из `int(os.environ.get("COMPASS_PORT", port))`.
- Запускает Flask в `threading.Thread(daemon=True)`.
- `app.run(host="127.0.0.1", port=port, threaded=True, debug=False, use_reloader=False)`.
- Логирует `"Web UI: http://localhost:%d"`.

**Функция `get_calibration_trigger() -> threading.Event`**: возвращает `_calibration_trigger`.
**Функция `get_calibration_save_trigger() -> threading.Event`: возвращает `_calibration_save_trigger`.

---

## Задача 2: `ui/static/index.html` — Полный SVG-компас (inline все)

Создай `ui/static/index.html`. Всё inline: CSS, JS, SVG. **Ноль внешних ресурсов** (spec.md §28.1).

### CSS (в `<style>`):
- `body`: `margin:0`, `background:#0d1117`, `color:#c9d1d9`, `font-family:monospace`, flex column, `align-items:center`, `min-height:100vh`, `touch-action:manipulation`.
- `svg`: `max-width:300px`, `width:90vmin`, `height:90vmin`.
- `#needle`: `transform-origin:150px 150px`, `transition:transform 0.1s ease-out`, `will-change:transform`.
- `.badge`: `padding:4px 10px`, `border-radius:4px`, `font-size:13px`.
- `.badge-good`: `background:#238636; color:white`.
- `.badge-warning`: `background:#9e6a03; color:white`.
- `.badge-poor`: `background:#da3633; color:white`.
- `button`: `min-height:44px`, `padding:0 24px`, `border-radius:6px`, `font-size:14px`, `cursor:pointer`.

### SVG (в `<body>`, viewBox="0 0 300 300", id="compass-svg"):
- `<circle cx="150" cy="150" r="140">` — циферблат (stroke белый/серый, fill none).
- `<circle cx="150" cy="150" r="5">` — центральная точка.
- Метки сторон света (text): N (150,25), S (150,285), E (285,155), W (15,155). + NE, NW, SE, SW по диагоналям.
- Деления: 36 коротких (каждые 10°) и 4 длинных (главные стороны). Нарисовать как `<line>` или `<g transform="rotate(N 150 150)">`.
- `<g id="needle">`: две стрелки компаса:
  - Северная (красная): `<polygon points="150,30 143,150 157,150">` — острая вверх.
  - Южная (серая #666): `<polygon points="150,270 143,150 157,150">` — тупая вниз.
- `<text id="heading-text" x="150" y="175" text-anchor="middle" font-size="28" fill="#c9d1d9">---</text>` — числовой курс.

### Панели под SVG:
- `<div id="cardinal-text">` — крупный cardinal label (NNE, N, SE...).
- `<div id="confidence-badge" class="badge badge-poor">INIT</div>` — confidence badge.
- `<div id="debug-panel">`: строки `Pitch: <span id="pitch-val">--</span>°`, `Roll: <span id="roll-val">--</span>°`, `Mag: <span id="mag-val">--</span>µT`. По умолчанию скрыт (`display:none`).
- Кнопки: `<button id="btn-calibrate">Calibrate</button>` и `<button id="btn-debug">Debug</button>`.

### JavaScript (в `<script>`, полностью inline):
Точно по spec.md §28.4 с дополнениями:
- `let targetAngle = 0, currentAngle = 0`.
- `const evtSource = new EventSource('/stream')`.
- `evtSource.onmessage`: парсит JSON, проверяет `data.heading !== undefined`, устанавливает `targetAngle`, обновляет `heading-text` (padStart 3, + '°'), `cardinal-text`, вызывает `updateConfidenceBadge(data.conf_state, data.confidence)`, обновляет `pitch-val`, `roll-val`, `mag-val`.
- `evtSource.onerror`: badge → 'OFFLINE', класс `badge-poor`.
- `evtSource.addEventListener('heartbeat', ...)`: ничего не делать (keepalive прозрачен).
- `evtSource.addEventListener('calibration_start', ...)`: badge → 'CALIBRATING...', класс `badge-warning`.
- `evtSource.addEventListener('calibration_done', ...)`: badge → 'DONE', потом через 2с восстановить.
- `animateCompass()`: circular lerp `diff = ((targetAngle - currentAngle) + 540) % 360 - 180`, `currentAngle += diff * 0.15`, `currentAngle = ((currentAngle % 360) + 360) % 360`. `needle.style.transform = \`rotate(\${currentAngle}deg)\``. `requestAnimationFrame(animateCompass)`.
- `btn-calibrate click`: `fetch('/calibrate', {method:'POST'})`.
- `btn-debug click`: toggle `debug-panel` display `block`/`none`, toggle кнопки текст `Debug`/`Hide Debug`.
- `function updateConfidenceBadge(state, score)`: map state → CSS class, setText `\`\${state} \${Math.round(score||0)}\``.

---

## Задача 3: `main.py` — AppController (Центральная точка сборки)

Перепиши `main.py`. Это главный orchestrator.

### Импорты:
```python
import argparse, logging, os, time, signal, sys, json, math
from sensors.mock_adapter import MockAdapter
from sensors.termux_adapter import TermuxAdapter
from core.orientation import compute_orientation, RawSensorFrame
from core.filters import CircularEMAFilter, EMAFilter
from core.calibration import CalibrationManager
from core.quality import evaluate_confidence
from ui import web_server
from ui.cli_view import render as cli_render
```

### Настройка логирования:
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("compass.main")
```

### `heading_to_cardinal(deg: float) -> str`:
Реализовать точно по spec.md §10 (16-секторная роза, список `DIRECTIONS`, reversed loop).

### `class AppController`:

**`__init__(self, args)`**:
- Сохраняет `args`.
- Создаёт `CalibrationManager(storage_path)` где `storage_path = os.path.join(os.path.dirname(__file__), "calibration.json")`.
- Инициализирует фильтры: `self._heading_filter = CircularEMAFilter(alpha=0.15)`, `self._pitch_filter = EMAFilter(alpha=0.3)`, `self._roll_filter = EMAFilter(alpha=0.3)`.
- `self._last_state: dict | None = None`.
- `self._running = False`.

**`_create_adapter(self)`**:
- Если `args.mock` → `MockAdapter(freq_hz=0.5)`. Иначе → `TermuxAdapter("accelerometer,magnetic")`.

**`_process_frame(self, raw_dict: dict) -> dict | None`**:
- Проверяет наличие всех 6 ключей (`ax,ay,az,mx,my,mz`) → если нет, `return None`.
- Применяет калибровку: `mx,my,mz = self._cal.apply(...)`.
- Создаёт `frame = RawSensorFrame(...)`.
- `state = compute_orientation(frame)`.
- Вычисляет `confidence_str = evaluate_confidence(frame, state.tilt_deg)`.
- Прогоняет через фильтры: `heading = self._heading_filter.update(state.heading_deg)`, аналогично pitch и roll.
- Вычисляет `mag_magnitude = math.sqrt(mx**2 + my**2 + mz**2)`.
- Формирует SSE payload dict (по schema spec.md §7.3):
  ```python
  {
      "heading": round(heading, 1),
      "azimuth": round(state.heading_deg, 1),
      "cardinal": heading_to_cardinal(heading),
      "confidence": 0.0,  # упрощённо для MVP
      "conf_state": confidence_str,
      "pitch": round(self._pitch_filter.update(state.pitch_deg), 1),
      "roll": round(self._roll_filter.update(state.roll_deg), 1),
      "mag_mag": round(mag_magnitude, 2),
      "ts": int(time.time_ns()),
      "is_gimbal_lock": state.is_gimbal_lock
  }
  ```
- Обновляет `self._last_state = payload`.
- Возвращает payload.

**`run(self)`**:
- Загружает калибровку: `self._cal.load()`.
- Если `not args.no_ui` → `web_server.start_server()` + `time.sleep(0.5)` (дать Flask подняться).
- Создаёт адаптер через `_create_adapter()`, вызывает `adapter.start()`.
- `self._running = True`.
- Логирует режим запуска.
- Основной цикл `while self._running`:
  - `raw = adapter.read()`.
  - Если `raw is None`: `time.sleep(0.01)`, `continue`.
  - `payload = self._process_frame(raw)`.
  - Если `payload is None`: `continue`.
  - Если `not args.no_ui`: `web_server.push_state(payload)`.
  - Если `args.mode in ("cli", "both")` или `args.no_ui`: `cli_render(payload)`.
  - Проверяет `web_server.get_calibration_trigger().is_set()` → если да: вызвать `_run_calibration(adapter)`.
- `adapter.stop()`.

**`_run_calibration(self, adapter)`**:
- Сбрасывает `web_server.get_calibration_trigger().clear()`.
- Анонсирует через SSE: `web_server.push_state({"event": "calibration_start"})`.
- `self._cal.reset()`.
- Логирует "Calibration started. Rotate device in figure-eight for 20 seconds.".
- Цикл 20 секунд (200 итераций × 0.1с): читает `adapter.read()`, если есть `mx/my/mz` → `self._cal.add_sample(...)`.
- Ждёт `web_server.get_calibration_save_trigger()` (с timeout=60с).
- Если сработал: `self._cal.save()`, `web_server.get_calibration_save_trigger().clear()`.
- Анонсирует `web_server.push_state({"event": "calibration_done"})`.
- Логирует результат.

### `main()`:
```python
parser = argparse.ArgumentParser(description="Compass App")
parser.add_argument("--mock", action="store_true")
parser.add_argument("--no-ui", action="store_true")
parser.add_argument("--mode", choices=["web", "cli", "both"], default="web")
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

controller = AppController(args)

def _shutdown(sig, frame):
    log.info("Shutting down...")
    controller._running = False
    sys.exit(0)

signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

controller.run()

if __name__ == "__main__":
    main()
```