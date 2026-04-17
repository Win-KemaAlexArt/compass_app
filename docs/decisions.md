# Project Decisions Log (Compass App)

## Decision-001
- **Date**: 2026-04-15
- **Decision**: Web UI as primary mode (Flask SSE + SVG) instead of CLI-only.
- **Alternatives**: 1) textual TUI, 2) Kivy/pygame, 3) CLI-only.
- **Reason**: Compass is a visual tool. textual: 10Hz refresh flickering, unreadable on mobile. Kivy/pygame: require X11/VNC or APK — violate hard constraints. Flask SSE: pure Python, browser available on all Android, GPU-accelerated SVG, touch-friendly.
- **Status**: FINAL
- **Impact**: Added flask dependency; new modules `ui/web_server.py`, `ui/static/index.html`.

## Decision-002
- **Date**: 2026-04-15
- **Decision**: SSE (Server-Sent Events) instead of WebSocket for real-time UI.
- **Alternatives**: WebSocket (flask-sock), Long polling.
- **Reason**: Compass is a one-way data stream (server → client). SSE: no extra dependencies (stdlib queue.Queue + flask.Response), auto-reconnect in browser, HTTP-native. WebSocket would require extra dependencies.
- **Status**: FINAL
- **Impact**: `web_server.py`: CompassStateAnnouncer pattern; Flask `threaded=True` required.

## Decision-003
- **Date**: 2026-04-15
- **Decision**: NumPy installation via `pkg install python-numpy`, not pip.
- **Alternatives**: `pip install numpy`, compilation from source.
- **Reason**: Termux uses Bionic libc. PyPI-wheel numpy is compiled for glibc. ABI incompatibility makes pip install in Termux difficult. `pkg install` is pre-built for AArch64/Bionic.
- **Status**: FINAL
- **Impact**: `requirements.txt` does not contain numpy; README/docs contain pkg install instruction.

## Decision-004
- **Date**: 2026-04-15
- **Decision**: Flask dev server with `threaded=True`, no gunicorn/gevent.
- **Alternatives**: gunicorn with gevent workers, uvicorn + asyncio.
- **Reason**: Project designed for 1 concurrent client (localhost personal use). Flask `threaded=True`: each request handled in separate thread — sufficient. gunicorn/gevent: extra deps with native extensions → problems on Bionic libc.
- **Status**: FINAL
- **Impact**: `requirements.txt` does not contain gunicorn; `web_server.py`: `app.run(threaded=True)`.

## Decision-005
- **Date**: 2026-04-15
- **Decision**: `index.html` — single file, all inline (CSS + JS + SVG).
- **Alternatives**: separate .css and .js files in static/.
- **Reason**: Zero Internet constraint: no CDN. Single file — simplest deployment, no path issues, no separate static file serving needed.
- **Status**: FINAL
- **Impact**: `ui/static/` contains only `index.html`.

## Decision-006: MCP Configuration Repair
- **Date**: 2026-04-15
- **Decision**: Purge invalid keys from MCP config and isolate server scopes.
- **Reason**: Invalid keys (`enabled`, `sandboxAllowedPaths`) were causing MCP initialization failures. Global servers were leaking into projects.
- **Status**: FINAL
- **Impact**: Stable MCP subsystem across all workspaces.

## Decision-007
- **Date**: 2026-04-15
- **Decision**: Unified task tracking — BACKLOG.md as single agent task store; PROGRESS.md for epics only.
- **Reason**: task-manager skill was referencing PROGRESS.md inside .agent/tasks/, conflicting with GEMINI.md directive pointing to BACKLOG.md. Fragmentation caused ambiguity on agent context restore.
- **Status**: FINAL
- **Impact**: task-manager SKILL.md updated; Storage Contract table added; no behavioral change to BACKLOG.md structure.

## Decision-008
- **Date**: 2026-04-15
- **Decision**: Formalized CURRENT_SESSION.md lifecycle in docs/spec.md Docs Scaffold section.
- **Reason**: File was used by gemini-runtime skill but absent from official project manifest. Created orphaned memory node — agent had no documented rules for when to create, update, or clear it.
- **Status**: FINAL
- **Impact**: docs/spec.md updated; CURRENT_SESSION.md now has explicit lifecycle contract: ephemeral, cleared at session boundary.

## Decision-009
- **Date**: 2026-04-15
- **Decision**: Added ui/cli_view.py to Project Structure (spec.md §17) and Architecture Module Map.
- **Reason**: File was referenced in pipeline (§8) and CHANGELOG but missing from project structure manifest and architecture docs. Inconsistency would cause agent to skip creating the file during Phase 4 implementation.
- **Status**: FINAL
- **Impact**: docs/spec.md §17 updated; docs/architecture.md Module Map and Data Flow updated; no code changes.

## Decision-010
- **Date**: 2026-04-15
- **Decision**: Formalized SKILL.md grammar schema in CORE_RULES.md §5.
- **Reason**: Skills used YAML front-matter format borrowed from external conventions, but this was never documented in the project's own rules. skill-creator had no canonical schema to enforce, risking format drift on new skill generation.
- **Status**: FINAL
- **Impact**: CORE_RULES.md extended with §5; all existing skills already comply; new skills must follow schema.

## Decision-011
- **Date**: 2026-04-15
- **Decision**: Added verified tool registry to GEMINI.md §🔧 Available Agent Tools.
- **Reason**: mcp-configurator and other skills referenced tools (replace, system_pulse) without a canonical contract. Tool name changes in Gemini CLI would silently break skills with no fallback guidance.
- **Status**: FINAL (baseline — update when Gemini CLI version changes)
- **Impact**: GEMINI.md extended; agent now has authoritative tool reference; skills must use only listed tools.

## Decision-012: Knowledge Transfer from Binary_Cortex_Fresh
- **Date**: 2026-04-15
- **Decision**: Integrated advanced agent directives, roadmap tracking rules, and UI design skills from the Binary_Cortex_Fresh project.
- **Reason**: To improve agent autonomy, communication style, and design capabilities. The "Roadmap Compliance" and "Variations Decorator" concepts were highly relevant for compass_app.
- **Status**: FINAL
- **Impact**: Created .agent/rules/AGENT_DIRECTIVES.md, .agent/rules/ROADMAP_RULES.md, and .agent/skills/ui-designer/SKILL.md. Updated GEMINI.md.

## Decision-013: System Consistency & Grammar Standardization
- **Date**: 2026-04-15
- **Decision**: Applied corrections to eliminate "phantom" task file references, standardized skill argument syntax, and added an error-handler skill.
- **Reason**: Discrepancies between spec.md and the new task-manager logic caused ambiguity. Skill parameter parsing lacked a formal standard.
- **Status**: FINAL
- **Impact**: Updated docs/spec.md, CORE_RULES.md, mcp-configurator/SKILL.md, ui-designer/SKILL.md; Created error-handler skill; Updated GEMINI.md.

## Decision-014: Git Repository Initialization
- **Date**: 2026-04-16
- **Decision**: Initialize Git-repository and setup `.gitignore` for Phase 2 preparation.
- **Reason**: To enable version control and exclude temporary/environment-specific files from the repository.
- **Status**: FINAL
- **Impact**: `.gitignore` created, initial commit made.

## Decision-015: Sensor Unit Testing Strategy
- **Date**: 2026-04-16
- **Decision**: Implemented `unittest` based sensor verification for `MockAdapter` and `TermuxAdapter`.
- **Reason**: To ensure data deterministicity and robust subprocess management before Phase 2 implementation.
- **Status**: FINAL
- **Impact**: `tests/test_sensors.py` created, basic adapter logic verified.

## Decision-016: Continuous Stream Reading Strategy
- **Date**: 2026-04-16
- **Decision**: Used `stdout.readline()` with `bufsize=1` for `termux-sensor` continuous stream instead of `communicate()`.
- **Reason**: `communicate()` waits for process termination, which is incompatible with infinite sensor streams. `readline()` allows real-time data processing as it arrives.
- **Status**: FINAL
- **Impact**: `TermuxAdapter` now supports 10Hz+ real-time updates.

## Decision-017: Combined Sensor Reading in TermuxAdapter
- **Date**: 2026-04-16
- **Decision**: Use a single `TermuxAdapter("accelerometer,magnetic")` that reads a combined JSON and unpacks both sensors in one `read()` call.
- **Reason**: `spec.md §3.2` explicitly describes this pattern. Two separate adapters would require two processes, causing timestamp desync and increased resource usage.
- **Impact**: `TermuxAdapter.read()` will return a dictionary with up to 6 keys (`ax,ay,az,mx,my,mz`). Logic will be updated to handle multiple sensors in a single JSON frame.

## Decision-018: Library Selection for Core Modules
- **Date**: 2026-04-16
- **Decision**: Used standard `math` library instead of `numpy` for `filters.py` and `quality.py`.
- **Reason**: Scalar operations in these modules do not benefit from matrix acceleration. Keeping dependencies minimal where possible. `numpy` remains the choice for `orientation.py` due to future rotation matrix plans.
- **Status**: FINAL
- **Impact**: Reduced overhead in filtering loop.

## Decision-019: Zero External Resource UI
- **Date**: 2026-04-16
- **Decision**: All UI assets (CSS, JS, SVG) are inlined into a single `index.html`.
- **Reason**: To comply with "Zero Internet" constraint and ensure the application works entirely offline in Termux environment without CDN or external dependencies.
- **Status**: FINAL
- **Impact**: Simplified deployment and guaranteed availability in isolated environments.

## Decision-020: venv with --system-site-packages
- **Date**: 2026-04-17
- **Decision**: venv is created with `--system-site-packages` flag.
- **Reason**: numpy must be installed via `pkg install` in Termux to ensure Bionic libc ABI compatibility. Standard venv isolates system packages, making pkg-numpy inaccessible. `--system-site-packages` allows the venv to use the system-installed numpy while keeping other dependencies (like flask) isolated.
- **Status**: FINAL
- [Impact]: `venv/` added to `.gitignore`. Development and testing must be performed within this venv.

## Decision-021: Code Coverage and Testing Baseline
- **Date**: 2026-04-17
- **Decision**: Established a testing baseline with `coverage` measurement.
- **Reason**: To ensure reliability of core logic and sensors before field testing.
- **Status**: COMPLETED (Phase 4.5)
- **Impact**: 
    - `tests/test_integration.py` created for full pipeline verification.
    - Coverage Report Summary:
        - `core/orientation.py`: 100% (Goal: 85%) - OK
        - `core/filters.py`: 95% (Goal: 90%) - OK
        - `core/calibration.py`: 79% (Goal: 80%) - Minor debt
        - `core/quality.py`: 82% (Goal: 90%) - Minor debt
        - `sensors/mock_adapter.py`: 93% (Goal: 85%) - OK
        - `sensors/termux_adapter.py`: 71% (Goal: 70%) - OK
        - `ui/web_server.py`: 64% (Goal: 50%) - OK
    - Known issue: SSE stream has double `data: data:` prefix; requires refactoring in Phase 6.
    - Coverage gaps in `calibration.py` and `quality.py` to be addressed in Phase 5.

