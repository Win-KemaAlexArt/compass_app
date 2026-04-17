```markdown
# ЗАДАЧА: Настройка Playwright MCP через CDP + финализация Phase 5

## Контекст
Прочитай: `GEMINI.md` → `docs/progress.md` → `.gemini/settings.json` → `docs/decisions.md` (последние 3).

Статус: SSE-баг исправлен (Decision-022), компас вращается. Playwright MCP сконфигурирован но показывает Disconnected — браузерный бинарник несовместим с Bionic libc.

---

## Задача 1: Диагностика текущего состояния Playwright MCP

### 1a — Проверить что именно падает при старте MCP:
```bash
# Попробовать запустить MCP сервер вручную и посмотреть ошибку
timeout 5 npx @playwright/mcp@latest --headless 2>&1 | head -20
echo "Exit: $?"
```

### 1b — Проверить наличие системного Chromium:
```bash
# Есть ли chromium от pkg?
command -v chromium-browser 2>/dev/null || command -v chromium 2>/dev/null || echo "NOT FOUND"

# Если не найден — установить (требует x11-repo)
pkg list-installed 2>/dev/null | grep -E "chromium|x11-repo" || echo "chromium not installed"
```

### 1c — Установить системный Chromium если отсутствует:
```bash
pkg install x11-repo -y
pkg install chromium -y 2>&1 | tail -5
command -v chromium-browser && echo "OK" || command -v chromium && echo "OK"
```

---

## Задача 2: Настроить CDP-подход (рабочий метод для Termux)

Принцип: Playwright MCP **не запускает браузер сам** — он подключается к уже запущенному через CDP (Chrome DevTools Protocol). Это обходит проблему несовместимых бинарников.

### 2a — Создать скрипт запуска Chromium с CDP:
```bash
cat > /data/data/com.termux/files/home/compass_app/start_browser.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Запускает Chromium с CDP на порту 9222 для Playwright MCP
CHROMIUM=$(command -v chromium-browser || command -v chromium)
if [ -z "$CHROMIUM" ]; then
    echo "ERROR: chromium not found. Run: pkg install x11-repo && pkg install chromium"
    exit 1
fi

echo "Starting Chromium with remote debugging on port 9222..."
exec "$CHROMIUM" \
    --headless=new \
    --no-sandbox \
    --disable-gpu \
    --disable-dev-shm-usage \
    --remote-debugging-port=9222 \
    --remote-debugging-address=127.0.0.1 \
    about:blank 2>/dev/null &

sleep 2
# Проверить что CDP отвечает
curl -s http://localhost:9222/json/version | python -c "import sys,json; d=json.load(sys.stdin); print('CDP OK:', d.get('Browser','?'))" 2>/dev/null || echo "CDP not responding"
EOF
chmod +x /data/data/com.termux/files/home/compass_app/start_browser.sh
```

### 2b — Обновить `.gemini/settings.json` для CDP-режима:

Прочитай текущий файл, затем замени секцию `playwright` на CDP-конфигурацию:

```json
"playwright": {
  "command": "npx",
  "args": [
    "-y",
    "@playwright/mcp@latest",
    "--cdp-endpoint=http://localhost:9222",
    "--headless"
  ]
}
```

Используй `replace` для точечного редактирования — не перезаписывай весь файл.

### 2c — Проверить CDP workflow:
```bash
# Запустить Chromium с CDP
./start_browser.sh

# Проверить что CDP доступен
curl -s http://localhost:9222/json/version 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); print('Browser:', d.get('Browser')); print('Protocol:', d.get('Protocol'))" || echo "CDP не отвечает"

# Остановить Chromium
pkill chromium 2>/dev/null; pkill chromium-browser 2>/dev/null
echo "Done"
```

Если CDP ответил — workflow рабочий. Записать `Decision-024` в `docs/decisions.md`:
- **Decision**: Playwright MCP в Termux работает через CDP-подключение к системному Chromium.
- **Reason**: Playwright не может запустить собственные браузерные бинарники в Termux (Bionic libc несовместима с glibc-скомпилированными браузерами). Решение: системный Chromium из `pkg install` запускается с `--remote-debugging-port=9222`, Playwright MCP подключается через `--cdp-endpoint`.
- **Impact**: Для использования Playwright MCP нужно сначала запустить `./start_browser.sh`, затем запустить Gemini CLI.
- **Workflow**: `./start_browser.sh` → перезапустить Gemini CLI → `/mcp list` → playwright Connected.

---

## Задача 3: Если CDP тоже не работает — альтернативный MCP через puppeteer-termux

Если Chromium headless не запустился — использовать puppeteer-MCP с proot-distro (не требует X11):

### 3a — Проверить proot-distro:
```bash
command -v proot-distro && echo "OK" || echo "NOT FOUND"
proot-distro list 2>/dev/null | grep -E "alpine|ubuntu|debian" | head -3
```

### 3b — Если proot-distro доступен:
```bash
# Установить Alpine (самый лёгкий дистрибутив)
proot-distro install alpine 2>&1 | tail -3

# Установить Chromium внутри Alpine
proot-distro login alpine -- apk add --no-cache chromium nodejs npm 2>&1 | tail -5

# Проверить
proot-distro login alpine -- chromium-browser --version 2>/dev/null || \
proot-distro login alpine -- chromium --version 2>/dev/null
```

### 3c — Если ни CDP ни proot не работают:

Записать `Decision-024` с фактическим результатом и зафиксировать что для данного проекта (localhost Flask, простой SVG DOM) Playwright MCP избыточен. Достаточно Flask test client (уже реализован в `tests/test_e2e.py`).

---

## Задача 4: E2E тест Playwright (если MCP подключился)

Если `/mcp list` показывает playwright Connected — выполнить следующую проверку **в новой сессии** Gemini CLI после перезапуска:

Команда для новой сессии:
```
Используй playwright MCP. Запусти ./run.sh --mock в фоне. Подожди 3 секунды. Открой http://localhost:8080 в браузере. Сделай snapshot страницы. Найди элемент с id='needle'. Проверь что его transform атрибут содержит rotate(). Подожди 2 секунды. Сделай ещё один snapshot. Сравни transform значения needle в двух снапшотах — они должны отличаться (стрелка вращается). Покажи оба значения.
```

---

## Задача 5: Обновление документации и коммит

1. `git add -A && git commit -m "feat(mcp): playwright CDP config for Termux; docs: Decision-024"`
2. `git push`
3. Обнови `docs/progress.md`: зафикисруй статус Playwright MCP.
4. Обнови `.gitignore` — добавить `start_browser.sh` **не нужно** (это полезный скрипт), но добавить `*.log` если не добавлен.
5. Очисти `CURRENT_SESSION.md`.
```