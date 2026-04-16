# Project Technical Backlog (Compass App)

## Phase 2: Sensors (Priority: HIGH)
- [ ] Implement `sensors/termux_adapter.py` with subprocess management for `termux-sensor`.
- [ ] Implement `sensors/mock_adapter.py` with deterministic sinusoids for testing.
- [ ] Implement `sensors/base_adapter.py` (Abstract Interface).

## Phase 3: Core Logic (Priority: HIGH)
- [ ] `core/orientation.py`: Implement Tilt-Compensation (Rotation matrix based).
- [ ] `core/filters.py`: Implement EMA (Exponential Moving Average) with circular wrap-around.
- [ ] `core/calibration.py`: Implement Hard-Iron offset calculation.

## Phase 4: UI & Server (Priority: MEDIUM)
- [ ] `ui/web_server.py`: Flask + SSE integration.
- [ ] `ui/static/index.html`: SVG + CSS animation (inline everything).

## Phase 5: Testing & Validation (Priority: MEDIUM)
- [ ] Integration test: Mock Sensor -> Core -> SSE -> Client.
- [ ] Field test: Real Termux sensors validation.
