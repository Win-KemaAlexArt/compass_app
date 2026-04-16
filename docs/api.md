# Module API Definitions: Compass App MVP

## Data Schemas (Dataclasses)

### `RawSensorFrame`
```python
@dataclass
class RawSensorFrame:
    timestamp_ns: int
    ax: float; ay: float; az: float
    mx: float; my: float; mz: float
    acc_source: str = ""
    mag_source: str = ""
```

### `OrientationState`
```python
@dataclass
class OrientationState:
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    azimuth_deg: float = 0.0
    heading_deg: float = 0.0
    confidence: float = 0.0
    confidence_state: str = "POOR"
    tilt_deg: float = 0.0
    mag_magnitude: float = 0.0
    timestamp_ns: int = 0
```

## Module Interfaces

### `sensors/base_adapter.py`
- `def get_sensors_stream(delay_ms: int) -> Generator[RawSensorFrame, None, None]`
- `def discover_sensors() -> Dict[str, str]`

### `core/orientation.py`
- `def compute_orientation(raw: RawSensorFrame) -> OrientationState`

### `core/filters.py`
- `def ema_circular(prev: float, current: float, alpha: float) -> float`

### `ui/web_server.py`
- `def start_server(port: int)`
- `def push_state(state: OrientationState)`
- `GET /`: index.html
- `GET /stream`: SSE stream (EventSource)
- `POST /calibrate`: trigger calibration
- `GET /health`: system health check
