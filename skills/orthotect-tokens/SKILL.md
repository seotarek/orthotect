---
name: orthotect-tokens
description: Generate, extend, and compile DTCG W3C 3-tier design tokens (primitives -> semantics -> component tokens) across Light and Dark modes.
---

# Skill: Orthotect Design Tokens

Manage design tokens in accordance with the official W3C Design Tokens Community Group (DTCG) specification.

## 3-Tier Architecture
1. **Primitives (`core/tokens/primitives.json`):** Raw raw palette values (`neutral.900`, `brand.600`), dimensions, radii.
2. **Semantics (`core/tokens/semantics.json`):** Role-based mappings (`surface.canvas`, `content.primary`, `action.danger`) resolved for `light` and `dark` themes.
3. **Components:** Scoped tokens referencing semantic variables directly in CSS (`var(--ot-surface-panel)`).

## Verification
Run:
`python3 gates/gate_contrast_wcag.py`
