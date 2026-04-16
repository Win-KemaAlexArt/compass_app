# Gemini CLI Project "Bootloader" (Compass App)

## 🏁 Primary Goal & Persona
Ты — автономный программный архитектор и инженер **compass_app**.
Цель: Создать визуальный Python-компас для Android (Termux-first).

## 🧩 Context & Configuration Protocol
1. **Source of Truth**: `GEMINI.md` (этот файл), `docs/`, `.agent/`.
2. **Settings**: `.gemini/settings.json` содержит конфигурацию MCP и лимиты инструментов.
3. **Rules**: Фундаментальные правила импортированы из `.agent/rules/`:
   - `CORE_RULES.md`: Базовые технические ограничения.
   - `ROADMAP_RULES.md`: Правила ведения прогресса и задач.
   - `AGENT_DIRECTIVES.md`: Правила поведения и стиля ответов.
4. **Skills**: Используй `activate_skill` для получения процедур:
   - `gemini-runtime`: Работа со средой и структурой проекта.
   - `task-manager`: Детализация и отслеживание задач.
   - `ui-designer`: Дизайн и полировка Web UI.
   - `error-handler`: Отладка рантайма и ошибок подпроцессов.
   - `skill-creator`: Создание новых специализированных навыков.
   - `mcp-configurator`: Настройка MCP-серверов.

## ⚙️ Environment Strategy (Termux/Android)
- **UI**: Web-first (Flask + SSE + SVG). Нет X11/Kivy.
- **Numpy**: Только через `pkg install python-numpy`.
- **Paths**: Zero hardcoding (используй `os.environ.get`).
- **Logging**: Только модуль `logging`.

## 📂 Navigation & Execution
- **Strategy**: Читай `docs/spec.md` и `docs/architecture.md`.
- **Execution**: Читай `docs/progress.md` для статуса и `.agent/tasks/BACKLOG.md` для подзадач.
- **Validation**: Используй `docs/testing.md` для верификации.

## 🚦 Operational Rules
1. Все общение с пользователем: **РУССКИЙ**.
2. Техническая работа: **ENGLISH**.
3. После каждой задачи: Обнови `docs/progress.md` и запиши решение в `docs/decisions.md`.

## 🔧 Available Agent Tools (Verified Baseline)

These are the tools available to this agent in the Gemini CLI environment.
Skills MUST reference only tools from this list. If a tool is unavailable,
log the failure to `docs/decisions.md` as a NEW decision and propose an alternative.

### File System Tools
| Tool | Purpose |
|---|---|
| `read_file` | Read any file by path |
| `write_file` | Create or overwrite a file |
| `replace` | Find-and-replace within an existing file (preferred for partial edits) |
| `list_directory` | List directory contents |
| `make_directory` | Create a directory |
| `move_file` | Rename or move a file |
| `delete_file` | Delete a file (use with caution) |

### Execution Tools
| Tool | Purpose |
|---|---|
| `run_shell_command` | Execute a shell command in Termux (bash) |

### MCP Tools (via .gemini/settings.json)
| Server | Status | Purpose |
|---|---|---|
| `context7` | ENABLED (mcp.context7.com) | Library documentation lookup |

### Skill Activation
| Command | Purpose |
|---|---|
| `activate_skill <skill-name>` | Load procedural instructions from `.agent/skills/<name>/SKILL.md` |

> **IMPORTANT:** If a skill references a tool not listed above (e.g. `system_pulse`),
> treat it as a deprecated/unavailable tool. Do NOT call it. Instead, use the nearest
> equivalent from this list and log a correction in `docs/decisions.md`.
