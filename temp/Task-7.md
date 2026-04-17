```markdown
# ВОССТАНОВЛЕНИЕ КОНТЕКСТА + ЗАДАЧИ Phase 5 (продолжение)

## Восстановление сессии

Прочитай по порядку ВСЕ файлы перед любыми действиями:
`GEMINI.md` → `.agent/rules/CORE_RULES.md` → `.agent/rules/AGENT_DIRECTIVES.md` → `docs/progress.md` → `.agent/tasks/BACKLOG.md` → `docs/decisions.md` → `docs/spec.md` (только §3.3, §7.3, §8, §28) → `main.py` → `sensors/mock_adapter.py` → `core/orientation.py` → `ui/web_server.py` → `ui/static/index.html`

Восстанови текущее состояние из этих файлов. После восстановления кратко подтверди: текущая фаза, последний Decision-номер, статус SSE-бага.

---

## Статус на момент прерывания (для контекста)

- SSE double-prefix баг (`data: data:`) — **ИСПРАВЛЕН** в `ui/web_server.py` (Decision-022).
- MCP Playwright — установка прервана на запросе `y/n`. Нужно завершить.
- Компас в браузере: данные меняются, но стрелка визуально неподвижна.

---

## Задача 1: Диагностика заморозки стрелки (корневая причина)

### 1a — Запустить диагностический тест heading-sweep:

```bash
source venv/bin/activate 2>/dev/null || true
python - << 'EOF'
import time, math
from sensors.mock_adapter import MockAdapter
from core.orientation import compute_orientation, RawSensorFrame
from core.filters import CircularEMAFilter

adapter = MockAdapter(freq_hz=10.0)
adapter.start()
filt = CircularEMAFilter(alpha=0.15)

print("t(s) | raw_mx | raw_my | heading_raw | heading_filt")
print("-" * 60)
for i in range(15):
    raw = adapter.read()
    frame = RawSensorFrame(ax=raw["ax"], ay=raw["ay"], az=raw["az"],
                           mx=raw["mx"], my=raw["my"], mz=raw["mz"])
    state = compute_orientation(frame)
    filt_h = filt.update(state.heading_deg)
    print(f"t={i*0.1:.1f}s | mx={raw['mx']:+.2f} | my={raw['my']:+.2f} | "
          f"hdg_raw={state.heading_deg:.1f} | hdg_filt={filt_h:.1f}")
    time.sleep(0.1)

adapter.stop()
EOF
```

Покажи полный вывод. Если `heading_raw` не меняется — проблема в `MockAdapter` или `compute_orientation`. Если `heading_filt` застывает — проблема в фильтре или частоте вызовов в main.py.

### 1b — Диагностика main loop (есть ли sleep между фреймами):

Прочитай `main.py`, найди основной цикл `while self._running`. Проверь: есть ли `time.sleep()` после `push_state()`. Если нет — mock_adapter вызывается тысячи раз в секунду, heading_filter получает одинаковые значения и сходится мгновенно.

### 1c — Исправить main loop (добавить rate-limiting):

Если `time.sleep` отсутствует в цикле — добавить:

```python
# В конце while self._running после push_state и cli_render:
time.sleep(0.05)  # 20 Hz максимум — даём MockAdapter время для движения синусоиды
```

### 1d — Проверить что MockAdapter действительно генерирует sweep:

```bash
python - << 'EOF'
import time, math
from sensors.mock_adapter import MockAdapter

adapter = MockAdapter(freq_hz=10.0)
adapter.start()
print("Проверка sweep за 2 секунды (20 отсчётов):")
mx_vals = []
for i in range(20):
    raw = adapter.read()
    mx_vals.append(round(raw["mx"], 2))
    time.sleep(0.1)
adapter.stop()
print("mx values:", mx_vals)
range_val = max(mx_vals) - min(mx_vals)
print(f"Диапазон mx: {range_val:.2f} (должен быть > 10.0)")
EOF
```

Если диапазон < 1.0 — MockAdapter сломан. Если > 10.0 — MockAdapter работает, проблема дальше по пайплайну.

---

## Задача 2: Завершение установки MCP Playwright

### 2a — Установить с автоподтверждением:
```bash
echo "y" | npm install -g @playwright/mcp@latest 2>&1 | tail -5
```

### 2b — Проверить установку:
```bash
ls $(npm root -g)/@playwright/mcp/dist/index.js 2>/dev/null && echo "OK" || echo "FAIL"
```

### 2c — Установить Chromium (с автоподтверждением, записать результат):
```bash
PLAYWRIGHT_BROWSERS_PATH=/data/data/com.termux/files/home/.playwright \
  npx playwright install chromium 2>&1 | tail -10
echo "Exit code: $?"
```

Если exit code != 0 — зафиксировать как Decision-023 с причиной и перейти к п. 2d.

### 2d — Обновить `.gemini/settings.json`:

Прочитай файл: `cat .gemini/settings.json`

Добавь секцию `playwright` в `mcpServers`. Используй `replace` для точечного редактирования — не перезаписывай весь файл. Итог должен выглядеть так:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "/data/data/com.termux/files/home/.playwright"
      }
    }
  }
}
```

**Важно**: MCP Playwright будет доступен только в СЛЕДУЮЩЕЙ сессии Gemini CLI после перезапуска. Зафикисровать это в `CURRENT_SESSION.md`.

---

## Задача 3: E2E тесты (независимо от Playwright)

### 3a — Запустить полный набор тестов:
```bash
source venv/bin/activate
python -m coverage run --source=core,sensors,ui -m unittest discover -s tests -v 2>&1 | tail -30
python -m coverage report --show-missing 2>&1
```

### 3b — Если `tests/test_e2e.py` не существует — создать его:

Прочитай `temp/Task-6.md` раздел "Задача 3" — там полный код `tests/test_e2e.py`. Создай файл и запусти тесты повторно.

### 3c — Критическая верификация SSE-фикса:

После запуска тестов найди в выводе строку:
```
test_sse_single_prefix ... ok
```
Если этот тест зелёный — SSE-баг подтверждённо исправлен на уровне кода, а не только визуально.

---

## Задача 4: Финальная проверка компаса в браузере

После исправлений из Задачи 1 запустить:
```bash
./run.sh --mock &
sleep 2
echo "=== SSE данные (должны меняться) ==="
curl -N --max-time 5 http://localhost:8080/stream 2>/dev/null | grep "^data:" | head -8
kill %1
```

Проверить что `"heading"` меняется между строками. Если меняется — открыть `http://localhost:8080` в браузере и подтвердить вращение стрелки.

---

## Задача 5: Коммит и документация

1. `git add -A && git commit -m "fix(mock): heading sweep; fix(main): rate-limiting; feat(tests): e2e suite; feat(mcp): playwright config"`
2. `git push`
3. Обнови `docs/progress.md`.
4. Запиши `Decision-023` (результат Playwright: успех или блокировка + альтернатива).
5. Создай/обнови `.agent/tasks/CURRENT_SESSION.md`:

```markdown
# Current Session Status

## Objective
Phase 5: Диагностика и исправление заморозки стрелки + MCP Playwright

## Sub-tasks
- [x] Decision-022: SSE double-prefix исправлен
- [x] Задача 1: Диагностика и исправление heading sweep
- [x] Задача 2: MCP Playwright установлен и сконфигурирован
- [x] Задача 3: E2E тесты созданы и пройдены
- [x] Задача 4: Компас вращается в браузере

## Status: COMPLETED

## Next Action
- Перезапустить Gemini CLI для активации MCP Playwright
- Phase 6: Полевые испытания с реальными датчиками (termux-sensor)
```

6. Очисти `CURRENT_SESSION.md` после коммита (согласно lifecycle contract).
```