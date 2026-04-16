# System Architecture: Compass App MVP

## System Overview
Приложение представляет собой Python-сервис, работающий в Termux, который считывает данные акселерометра и магнетометра, вычисляет магнитный азимут с компенсацией наклона и транслирует его в реальном времени через Web UI (Flask SSE) и опционально в CLI.

## Module Map
- `main.py`: Точка входа, AppController, диспетчеризация режимов.
- `core/orientation.py`: Алгоритм вычисления (roll, pitch, azimuth).
- `core/filters.py`: Сглаживание данных (EMA, median).
- `core/calibration.py`: Управление калибровкой (hard-iron offset).
- `core/quality.py`: Оценка качества сигнала (0–100).
- `sensors/termux_adapter.py`: Мост к системным датчикам через `termux-sensor`.
- `ui/web_server.py`: Flask сервер, SSE публикация.
- `ui/cli_view.py`: ASCII-компас для CLI режима (`--no-ui`). Рендеринг в терминале без Flask.
- `ui/static/index.html`: Визуальный интерфейс (SVG).

## Data Flow (Dual-Mode)

### Web UI Mode (primary)
1. `termux-sensor` (JSON) → `TermuxAdapter`.
2. `RawSensorFrame` → `OrientationEngine`.
3. `OrientationState` (raw) → `FilterEngine`.
4. `OrientationState` (filtered) → `QualityEvaluator`.
5. `OrientationState` (final) → `Dispatcher`.
6. `Dispatcher` → `Web Server` (SSE) → `Browser` (SVG).

### CLI Mode (--no-ui flag)
Steps 1–5 identical.
6. `Dispatcher` → `cli_view.py` → stdout (ASCII compass, ANSI colors)

## Web UI Pipeline
- **Thread Model**: Flask запускается в `daemon thread`. `AppController` работает в `main thread`.
- **Sync**: `CompassStateAnnouncer` (pub-sub) передает состояния из сенсорного цикла в SSE-генераторы.
- **Frontend**: Браузер использует `EventSource` для получения данных и `requestAnimationFrame` для 60fps анимации.

## Failure Handling
- **Sensor Dropout**: Заморозка последнего значения + индикатор "STALE".
- **Gimbal Lock**: Предупреждение "TILT!" при наклоне >75°.
- **Subprocess Crash**: Автоматический перезапуск адаптера.
