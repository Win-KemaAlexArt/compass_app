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
