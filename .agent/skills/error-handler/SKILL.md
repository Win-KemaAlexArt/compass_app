---
name: error-handler
description: Use when you need to debug runtime failures, subprocess crashes, or SSE stream errors.
---

# Error Handler Skill

## Purpose
Provides procedural guidance for identifying, diagnosing, and fixing runtime issues within the `compass_app` environment.

## Instructions
1. **Initial Diagnosis**: Identify the failing component (e.g., `termux-sensor` subprocess, Flask server, SSE stream).
2. **Log Analysis**:
   - Use `run_shell_command` to check Python stderr logs.
   - Example: `python main.py --debug 2> error.log`.
3. **Subprocess Check**:
   - If `termux-sensor` fails, verify visibility via `termux-sensor -l`.
   - Check if `termux-api` is installed and has necessary permissions.
4. **SSE Debugging**:
   - Use `curl -N http://localhost:8080/stream` to verify raw SSE output.
   - Check Flask `threaded=True` status.
5. **Recovery**:
   - If a crash occurs, perform a clean restart: `termux-sensor -c` (cleanup).
   - Log the failure and fix in `docs/decisions.md`.

## Error Handling Procedure
- **Step 1**: Run with `--debug` and capture stderr.
- **Step 2**: Verify hardware sensor access via shell.
- **Step 3**: Isolate the failing module (Core vs UI vs Sensor).
