---
name: orthotect-components
description: Author production-grade, accessible UI components with full WAI-ARIA APG contracts, keyboard navigation, focus management, and 8 explicit states. Use when developing accessible component libraries.
---

# Skill: Orthotect Accessible Component Engineering

Use this skill when developing UI component libraries (Button, Input, Modal, Tabs, Dropdown, Table, Card) across any frontend framework (React, Vue, Svelte, Lit, Web Components, HTML).

## Component Contract Matrix
Every component must implement:
1. **Anatomy:** Semantic HTML elements with appropriate ARIA roles.
2. **Explicit 8-State Handling:** `idle`, `hover`, `active`/`pressed`, `focus-visible`, `loading`, `disabled`, `error`, `success`.
3. **Keyboard Map:** Tab traversal, Enter/Space activation, Esc dismissal, Arrow-key navigation where applicable.
4. **Focus Boundary:** Visible 2px outline with 2px offset; never set `outline: none` without replacement.

## Example: Accessible Modal Dialog
- `role="dialog"` and `aria-modal="true"`.
- Focus trapped inside dialog while open.
- Esc key dismisses dialog and restores focus to trigger.
- Background marked `inert` or `aria-hidden="true"`.

## Verification
```bash
python3 gates/gate_fsm_integrity.py
```
