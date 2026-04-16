---
name: task-manager
description: Use when you need to create, update, or track tasks in the project. This skill ensures that tasks are modular and clearly defined in `.agent/tasks/`.
---

# Task Manager

## Purpose
This skill manages the project's task lifecycle, ensuring that the agent always knows the next smallest useful step and maintains a clear trail of progress.

## Storage Contract (Task Tracking)

| File | Audience | Granularity | Format |
|---|---|---|---|
| `docs/progress.md` | Human + Agent | Epics / Phases | Markdown prose |
| `.agent/tasks/BACKLOG.md` | Agent-only | Atomic tickets `[ ]` | Checklist |
| `CURRENT_SESSION.md` | Agent-only | Immediate execution plan | Checklist, cleared each session |

**Rule**: Never mix these files. `docs/progress.md` tracks WHAT was achieved.
`BACKLOG.md` tracks WHAT must be done next (machine-readable tickets).
`CURRENT_SESSION.md` is ephemeral — it only tracks the CURRENT active session's sub-steps.

## Instructions
1. **Identify Task**: Break down larger goals into smaller, verifiable sub-tasks.
2. **Task Creation**: Create or update `BACKLOG.md` in `.agent/tasks/` with the new task.
3. **Format**: Each task must have a name, description, priority, and a "Verification" criteria.
4. **State Transitions**: Move tasks from "Pending" to "In Progress" to "Completed".
5. **Sync**: Ensure `docs/progress.md` is synchronized with the detailed task list in `.agent/tasks/`.

## Example
**User**: "What's the next step for the compass UI?"
**Agent**: [Reads .agent/tasks/BACKLOG.md and proposes the next logical task]
