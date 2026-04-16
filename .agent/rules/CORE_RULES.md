# Core Agent Rules (Compass App)

## 1. Persistence & Context
- Source of truth is ONLY the files in /docs, gemini.md, and .agent/.
- ALWAYS update documentation after every task completion.
- NEVER assume external memory between sessions.

## 2. Language & Style
- Communication with User: РУССКИЙ (Russian).
- Technical Identifiers: English.
- Code Style: PEP 8 for Python, standard semantic HTML/CSS for Web UI.

## 3. Environment & Compatibility (Android/Termux)
- **NUMPY**: Install ONLY via `pkg install python-numpy`. Never use pip for numpy.
- **PATHS**: Zero hardcoding. Use `os.environ.get("PREFIX", "/usr")` and other dynamic methods.
- **TERMINAL**: No X11, no Kivy, no GUI frameworks requiring a display server.
- **FLASK**: Use `threaded=True` for concurrent SSE support without Redis.

## 4. Documentation Pipeline
After any change, record:
- What changed.
- Why it changed.
- Whether it's final or provisional.
- Update `docs/progress.md` and `docs/decisions.md`.

## 5. Skill File Schema (MANDATORY FORMAT)

Every file named `SKILL.md` inside `.agent/skills/<skill-name>/` MUST begin with a YAML front-matter block followed by the skill body:

```yaml
---
name: <skill-name-kebab-case>
description: <one-sentence description of WHEN to activate this skill>
---
```

### Required YAML keys:
| Key | Type | Rule |
|---|---|---|
| `name` | string | Must match the parent directory name exactly (kebab-case) |
| `description` | string | Must start with "Use when..." — triggers agent's `activate_skill` decision |

### Argument Syntax (MANDATORY):
When a skill accepts dynamic parameters (passed via `activate_skill <name> arg1 arg2`), the instructions MUST refer to them using the following variables:
- `$ARGUMENTS[0]`: The first argument after the skill name.
- `$ARGUMENTS[1]`: The second argument, and so on.
- `$ARGUMENTS_COUNT`: Total number of arguments provided.

### Required Markdown sections after front-matter:
```
# <Skill Title>
## Purpose          ← What this skill does
## Instructions     ← Step-by-step numbered procedure
## References       ← List of files this skill reads/writes
```

### Optional sections:
```
## Procedure for <X>   ← Named sub-procedures
## Storage Contract    ← If skill manages files
## Error Handling      ← If skill has failure modes
```

**NEVER** create a SKILL.md without the YAML front-matter. The `activate_skill` dispatcher relies on the `description` field for routing decisions.
