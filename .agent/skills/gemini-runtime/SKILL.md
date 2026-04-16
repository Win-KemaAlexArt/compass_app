---
name: gemini-runtime
description: Use when you need to interact with the project's meta-structure, configure MCP servers, update .agent folders, or interpret Gemini CLI-specific instructions (GEMINI.md, system.md).
---

# Gemini CLI Runtime Expert

## Purpose
This skill provides a deep technical understanding of the Gemini CLI environment within the context of the `compass_app` project on Android/Termux. It ensures consistency between workspace settings, skills, and documentation.

## Instructions
1. **Hierarchy Protocol**:
   - Always prioritize `GEMINI.md` at the root as the primary "Bootloader".
   - Respect `.gemini/settings.json` for MCP and tool-trust configurations.
   - Use modular rules from `.agent/rules/` by referencing them in `GEMINI.md`.

2. **Skill Management**:
   - Every skill MUST reside in `.agent/skills/<name>/`.
   - `SKILL.md` is the only required file, but assets go in `scripts/`, `references/`, or `assets/`.
   - Use `activate_skill` only when specific procedural guidance is needed to save context tokens.

3. **Task & Progress Control**:
   - Track high-level progress in `docs/progress.md`.
   - Maintain detailed technical sub-tasks in `.agent/tasks/BACKLOG.md`.
   - Use `CURRENT_SESSION.md` for the immediate execution plan.

4. **Termux/Android Nuances**:
   - Paths: Use `os.environ.get("PREFIX", "/usr")` for Termux compatibility.
   - UI: Web UI (Flask) is the only native-friendly GUI (No X11).
   - Numpy: Pre-installed binary only (`pkg install python-numpy`).

5. **MCP Config (Cortex-Tracker/Context7)**:
   - Configuration lives in `.gemini/settings.json` under the `mcpServers` key.
   - Ensure servers are enabled before calling their specific tools.

## Procedure for Environment Update
1. Update `.gemini/settings.json` if MCP settings change.
2. Update `GEMINI.md` if core strategy or rules change.
3. Update `.agent/skills/...` if a new specialized workflow is defined.
4. Update `docs/decisions.md` for every architectural change.

## References
- `.gemini/settings.json`: Project-wide CLI config.
- `GEMINI.md`: Main strategy and rules.
- `.agent/rules/CORE_RULES.md`: Fundamental constraints.
