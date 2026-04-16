---
trigger: always_on
---

# Roadmap & Task Management Rules (Compass App)

## 1. Strict Plan Adherence
- **Source of Truth**: Always follow the plan in `docs/progress.md` and `.agent/tasks/BACKLOG.md`.
- **Identify Next Step**: Before starting any task, clearly state which atomic step from the backlog is being addressed.
- **User Override**: If the user's request contradicts the roadmap, fulfill the request but document the deviation in `docs/decisions.md`.

## 2. Progress Tracking
- **Atomic Updates**: At the end of every task, update `docs/progress.md` and `.agent/tasks/BACKLOG.md`.
- **Checkbox Protocol**: Mark completed items with `[x]`.
- **Transparency**: At the end of each response, summarize the progress using the format:
  - `[X] <Step name from progress.md>`
  - `[ ] <Next step in queue>`

## 3. Communication
- **Update Notification**: If `docs/progress.md` or `BACKLOG.md` is modified, state: "🔄 Progress tracking updated."
- **Next Action**: Always conclude with the "Next Action" as defined in the updated roadmap.

## 4. Constraint Enforcement
- **No Premature Implementation**: Only implement items that are explicitly authorized or are immediate next steps in the roadmap. Do not "jump ahead" (e.g., implementing Phase 4 while in Phase 2) unless requested.
