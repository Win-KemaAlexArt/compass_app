---
name: skill-creator
description: Use when you need to create or update an agent skill in the project. This skill provides the correct directory structure and template for SKILL.md.
---

# Skill Creator

## Purpose
This skill ensures that all project skills follow the standard "Progressive Disclosure" pattern, making the agent more efficient and preventing context bloat.

## Instructions
1. **Identify Need**: Determine if a new skill is needed (e.g., for complex repetitive tasks like "deployment", "testing", or "sensor-debugging").
2. **Directory Structure**: Create a folder in `.agent/skills/<skill-name>`.
3. **Template**: Create a `SKILL.md` with YAML frontmatter (name, description).
4. **Metadata**: The `description` must be a clear, one-sentence trigger for the LLM.
5. **Procedure**: Write step-by-step instructions in the body.
6. **Registration**: Update `GEMINI.md` if necessary to acknowledge the new skill.

## Example
**User**: "Help me create a skill for automatic testing."
**Agent**: [Creates .agent/skills/tester/SKILL.md with instructions on how to run and validate tests]
