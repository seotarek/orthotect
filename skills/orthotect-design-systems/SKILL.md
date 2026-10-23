---
name: orthotect-design-systems
description: Architect and maintain enterprise design systems, W3C DTCG token hierarchies (primitives -> semantics -> components), multi-brand theming, and cross-platform token compilation. Use when establishing design tokens or multi-theme support.
---

# Skill: Orthotect Design Systems Architecture

Use this skill when architecting scalable design token hierarchies, implementing multi-brand theming, or configuring cross-platform token pipelines.

## Token Hierarchy Architecture
1. **Tier 1: Primitives:** Pure values (e.g., `ot.primitive.color.cyan.400 = #38bdf8`). Never reference primitives directly in UI components.
2. **Tier 2: Semantics:** Contextual intent tokens (e.g., `ot.semantic.action.primary = {ot.primitive.color.cyan.400}`).
3. **Tier 3: Components:** Scoped element tokens (e.g., `ot.component.button.primary.bg = {ot.semantic.action.primary}`).

## Multi-Theme Compilation
```bash
# Compile tokens into production CSS variables with light/dark scopes
node bin/orthotect.js compile core/tokens --out styles/tokens.css
```

## Rules
- Every color token must declare its WCAG contrast pairing in metadata.
- Theme switching must be accomplished via CSS variables under `[data-theme="light"]` and `[data-theme="dark"]`.
- Components must consume only semantic and component tokens.
