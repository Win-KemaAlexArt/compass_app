---
name: ui-designer
description: Use when you need to design, polish, or create variations for the Web UI (HTML/CSS/SVG).
---

# UI Designer Skill

## Purpose
This skill provides advanced capabilities for designing and iterating on the project's visual interface, specifically focusing on the Web UI (Compass App).

## Instructions

### 1. Design Variation Mode
When activated with `activate_skill ui-designer <number> <temperature>`:
- `$ARGUMENTS[0]`: The number of variations to create (1-10).
- `$ARGUMENTS[1]`: The temperature (0.1-2.0) for creativity:
  - 0.1-0.5: Minor tweaks (colors, fonts, spacing).
  - 0.6-1.0: Moderate changes (layout, components).
  - 1.1-1.5: Significant changes (structure, concept).
  - 1.6-2.0: Radical changes (complete redesign).

### 2. Design System Analysis
When analyzing a visual reference or existing UI:
- Extract color palette (primary, secondary, neutral, semantic).
- Define typography (families, sizes, line heights).
- Specify spacing, shadows, and border radii.
- Ensure all resources are local/inline (Zero Internet constraint).

### 3. SVG Compass Customization
- Handle rotation logic via CSS `transform: rotate()`.
- Ensure 60fps performance with `requestAnimationFrame`.
- Use GPU-friendly properties only.

## References
- `ui/static/index.html`: Main UI file.
- `docs/spec.md` §28: Web UI Specification.
