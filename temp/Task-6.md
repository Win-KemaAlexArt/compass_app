```markdown
# ЗАДАЧА: Phase 5 — Диагностика SSE-бага + MCP Playwright + E2E UI-тест

## Контекст
Прочитай: `GEMINI.md` → `docs/progress.md` → `docs/decisions.md` (последние 3) → `ui/web_server.py` → `ui/static/index.html` → `sensors/mock_adapter.py` → `main.py`.

Симптом: компас в браузере заморожен несмотря на работающий Flask и SSE-поток.
Уже известно из предыдущей сессии: в потоке наблюдается `data: data: {...}` — двойной префикс.

---

## Задача 1: Диагностика и починка SSE-бага (корневая причина)

### 1a — Воспроизвести баг в терминале:
```bash
./run.sh --mock > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2
echo "=== RAW SSE STREAM (5 строк) ==="
curl -N --max-time 3 http://localhost:8080/stream 2>/dev/null | head -5
kill $SERVER_PID 2>/dev/null
```
Покажи точный вывод. Если там `data: data: {` — баг подтверждён.

### 1b — Найти корневую причину:

Прочитай `ui/web_server.py` целиком. Найди **оба** места где вызывается `_format_sse`:

1. В функции `push_state()` — она вызывает `_format_sse(json.dumps(state_dict))` и кладёт результат (`data: {...}\n\n`) в `announcer.announce(msg)`.
2. В генераторе `/stream` — он читает из очереди `msg = messages.get(...)` и снова оборачивает: `yield _format_sse(msg)`.

Итог: `msg` уже содержит `data: {...}\n\n`, а `_format_sse(msg)` превращает его в `data: data: {...}\n\n\n\n`.

Браузер получает `event.data = 'data: {...}'` — строку, а не JSON. `JSON.parse('data: {...}')` → SyntaxError → `onmessage` молча падает. Стрелка никогда не получает `targetAngle`.

### 1c — Исправить баг (одно место):

В `ui/web_server.py` в функции `push_state()` замени логику:

**Было:**
```python
def push_state(state_dict: dict) -> None:
    event_name = state_dict.pop("event", None)
    payload = json.dumps(state_dict)
    msg = _format_sse(payload, event=event_name)
    announcer.announce(msg)
```

**Стало:**
```python
def push_state(state_dict: dict) -> None:
    """Сериализует state и кладёт RAW JSON в очередь.
    Форматирование SSE происходит ТОЛЬКО в генераторе /stream."""
    event_name = state_dict.pop("event", None)
    # Кладём в очередь только сырой JSON — без SSE-обёртки
    # _format_sse вызывается один раз в generate() внутри /stream
    announcer.announce(json.dumps(state_dict), event=event_name)
```

Теперь обнови `CompassStateAnnouncer.announce()` чтобы принимать опциональный `event`:
```python
def announce(self, msg: str, event: str = None) -> None:
    formatted = _format_sse(msg, event=event)
    with self._lock:
        dead_indices = []
        for i, q in enumerate(self._listeners):
            try:
                q.put_nowait(formatted)
            except queue.Full:
                dead_indices.append(i)
        for i in reversed(dead_indices):
            del self._listeners[i]
```

И в генераторе `/stream` убери лишний `_format_sse` — очередь уже содержит готовую SSE-строку:
```python
def generate():
    messages = announcer.listen()
    while True:
        try:
            msg = messages.get(timeout=15)
            yield msg  # уже отформатировано в announce()
        except queue.Empty:
            yield _format_sse("{}", event="heartbeat")
```

### 1d — Верифицировать исправление:
```bash
./run.sh --mock > /dev/null 2>&1 &
SERVER_PID=$!
sleep 2
echo "=== FIXED SSE STREAM ==="
curl -N --max-time 3 http://localhost:8080/stream 2>/dev/null | head -5
kill $SERVER_PID 2>/dev/null
```
Ожидание: `data: {"heading": X.X, ...}` — ровно один `data:` префикс. Значение `heading` должно меняться между строками.

Запиши `Decision-022` в `docs/decisions.md`:
- **Decision**: Исправлен двойной SSE-префикс `data: data:`.
- **Reason**: `push_state()` форматировала SSE и клала в очередь, затем генератор `/stream` форматировал снова. Браузер получал `event.data = 'data: {...}'` вместо JSON → `JSON.parse()` падал молча → `targetAngle` никогда не обновлялся → компас заморожен.
- **Impact**: SSE-поток теперь корректен. Форматирование происходит один раз — в `announce()`.

---

## Задача 2: Настройка MCP Playwright

### 2a — Проверить наличие Node.js и npm:
```bash
node --version && npm --version
```
Если Node.js отсутствует:
```bash
pkg install nodejs -y
node --version && npm --version
```

### 2b — Установить MCP-сервер Playwright:
```bash
npm install -g @playwright/mcp@latest
# Проверить установку
npx playwright --version 2>/dev/null || echo "playwright not bundled separately"
```

### 2c — Прочитать текущий `.gemini/settings.json`:
```bash
cat .gemini/settings.json
```

### 2d — Добавить Playwright MCP в `.gemini/settings.json`:

Прочитай файл, найди секцию `mcpServers` и добавь новую запись `playwright`. Итоговый файл должен содержать:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "/data/data/com.termux/files/home/.playwright"
      }
    }
  }
}
```

**Важно**: не удаляй существующие серверы. Использовать `replace` для точечного редактирования файла.

### 2e — Установить браузер для Playwright (Chromium headless):
```bash
# Создать директорию для браузеров
mkdir -p /data/data/com.termux/files/home/.playwright

# Установить Chromium
PLAYWRIGHT_BROWSERS_PATH=/data/data/com.termux/files/home/.playwright npx playwright install chromium 2>&1 | tail -5
```

Если установка Chromium завершается с ошибкой в Termux — зафиксировать как `Decision-023` (Playwright недоступен в Termux без root/proot, предложить альтернативу через Flask test client).

Запиши `Decision-023` в любом случае — с результатом (успех или блокировка + альтернатива).

---

## Задача 3: E2E тест через Flask Test Client (гарантированный fallback)

Независимо от результата Playwright — создай `tests/test_e2e.py` используя Flask встроенный test client. Это даёт полноценный E2E без браузера.

```python
# tests/test_e2e.py
import unittest
import threading
import time
import json
import queue as queue_module
from ui import web_server
from ui.web_server import app, CompassStateAnnouncer

class TestSSEEndToEnd(unittest.TestCase):
    """E2E тесты SSE пайплайна через Flask test client."""

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        # Изолируем announcer для каждого теста
        self.original_announcer = web_server.announcer
        web_server.announcer = CompassStateAnnouncer()

    def tearDown(self):
        web_server.announcer = self.original_announcer

    def test_health_endpoint(self):
        """GET /health должен вернуть JSON с status=ok."""
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('listeners', data)

    def test_index_returns_html(self):
        """GET / должен вернуть index.html с EventSource."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        body = resp.data.decode('utf-8')
        self.assertIn('EventSource', body)
        self.assertIn('needle', body)

    def test_calibrate_trigger(self):
        """POST /calibrate должен вернуть 202 и установить Event."""
        web_server._calibration_trigger.clear()
        resp = self.client.post('/calibrate')
        self.assertEqual(resp.status_code, 202)
        data = json.loads(resp.data)
        self.assertEqual(data['status'], 'calibration_triggered')
        self.assertTrue(web_server._calibration_trigger.is_set())

    def test_sse_single_prefix(self):
        """SSE-сообщение должно начинаться ровно с одного 'data: '."""
        q = web_server.announcer.listen()
        payload = {"heading": 42.0, "cardinal": "NE", "conf_state": "GOOD",
                   "confidence": 90.0, "pitch": 0.0, "roll": 0.0,
                   "mag_mag": 45.0, "azimuth": 42.0, "ts": 0}
        web_server.push_state(payload)
        msg = q.get(timeout=1)
        # Должен начинаться с 'data: ' ОДИН раз
        self.assertTrue(msg.startswith('data: '), f"Bad prefix: {repr(msg[:30])}")
        self.assertFalse(msg.startswith('data: data: '), f"Double prefix: {repr(msg[:40])}")

    def test_sse_valid_json_in_payload(self):
        """Данные после 'data: ' должны быть валидным JSON."""
        q = web_server.announcer.listen()
        payload = {"heading": 135.0, "cardinal": "SE", "conf_state": "GOOD",
                   "confidence": 85.0, "pitch": 2.1, "roll": -1.5,
                   "mag_mag": 48.3, "azimuth": 135.0, "ts": 12345}
        web_server.push_state(payload)
        msg = q.get(timeout=1)
        # Извлечь JSON-часть (после 'data: ' до '\n\n')
        json_str = msg.replace('data: ', '', 1).strip()
        parsed = json.loads(json_str)
        self.assertAlmostEqual(parsed['heading'], 135.0)
        self.assertEqual(parsed['cardinal'], 'SE')

    def test_sse_stream_response_mimetype(self):
        """GET /stream должен возвращать text/event-stream."""
        # Запустить в отдельном потоке (stream бесконечный)
        results = {}
        def fetch_stream():
            with app.test_client() as c:
                # Подписаться, отправить данные, прочитать первый чанк
                web_server.push_state({"heading": 0.0, "cardinal": "N",
                    "conf_state": "GOOD", "confidence": 100.0,
                    "pitch": 0.0, "roll": 0.0, "mag_mag": 45.0,
                    "azimuth": 0.0, "ts": 0})
                resp = c.get('/stream')
                results['content_type'] = resp.content_type
        t = threading.Thread(target=fetch_stream, daemon=True)
        t.start()
        t.join(timeout=2)
        self.assertIn('text/event-stream', results.get('content_type', ''))

    def test_named_sse_event_format(self):
        """push_state с event-ключом должен создавать named SSE event."""
        q = web_server.announcer.listen()
        web_server.push_state({"event": "calibration_start", "status": "started"})
        msg = q.get(timeout=1)
        self.assertIn('event: calibration_start', msg)
        self.assertIn('data: ', msg)


class TestMockAdapterE2E(unittest.TestCase):
    """E2E тест: MockAdapter генерирует изменяющиеся данные."""

    def test_mock_produces_changing_headings(self):
        """За 1 секунду при 10 Hz MockAdapter должен дать разные heading."""
        from sensors.mock_adapter import MockAdapter
        from core.orientation import compute_orientation, RawSensorFrame
        from core.filters import CircularEMAFilter

        adapter = MockAdapter(freq_hz=10.0)
        adapter.start()
        filt = CircularEMAFilter(alpha=0.15)

        headings = []
        for _ in range(10):
            raw = adapter.read()
            if raw:
                frame = RawSensorFrame(**raw)
                state = compute_orientation(frame)
                headings.append(filt.update(state.heading_deg))
            time.sleep(0.1)

        adapter.stop()
        # Данные должны меняться
        self.assertGreater(len(set(round(h, 1) for h in headings)), 2,
                           f"Headings не меняются: {headings}")

    def test_mock_heading_covers_full_circle(self):
        """За 10 секунд MockAdapter должен пройти полный круг (0-360)."""
        from sensors.mock_adapter import MockAdapter
        from core.orientation import compute_orientation, RawSensorFrame

        adapter = MockAdapter(freq_hz=10.0)
        adapter.start()

        headings = []
        # 100 отсчётов × 0.1с = 10 секунд = 1 полный оборот
        for _ in range(100):
            raw = adapter.read()
            if raw:
                frame = RawSensorFrame(**raw)
                state = compute_orientation(frame)
                headings.append(state.heading_deg)
            time.sleep(0.1)

        adapter.stop()
        heading_range = max(headings) - min(headings)
        self.assertGreater(heading_range, 270,
                           f"Диапазон вращения только {heading_range:.1f}° (ожидается >270°)")
```

Запусти тесты:
```bash
source venv/bin/activate
python -m unittest tests/test_e2e.py -v
```

**Критический тест** — `test_sse_single_prefix`. Если он падал ДО исправления Задачи 1 → должен зеленеть после. Покажи вывод до и после исправления.

---

## Задача 4: Полный прогон всех тестов с coverage

```bash
source venv/bin/activate
python -m coverage run --source=core,sensors,ui -m unittest discover -s tests -v 2>&1 | tail -40
python -m coverage report --show-missing
```

Ожидание: все тесты зелёные, `test_sse_single_prefix` — OK.

---

## Задача 5: Финальная проверка в браузере

```bash
# Запустить
./run.sh --mock &
sleep 2

# Проверить что SSE содержит одиночный data: с меняющимися heading
echo "=== Проверка 5 событий SSE ==="
curl -N --max-time 3 http://localhost:8080/stream 2>/dev/null | grep "^data:" | head -5

kill %1
```

Ожидание: 5 строк вида `data: {"heading": X.X, ...}` где X.X **различается** между строками.

---

## Задача 6: Коммит и документация

1. `git add . && git commit -m "fix(sse): double data: prefix bug; feat(tests): e2e test suite + playwright mcp config"`
2. `git push`
3. Обнови `docs/progress.md`: Phase 5 в статус IN PROGRESS, зафиксируй SSE-баг как исправленный.
4. Очисти `CURRENT_SESSION.md`.
```