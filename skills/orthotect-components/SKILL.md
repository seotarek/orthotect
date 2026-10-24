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

## Core Component Contracts

### 1. Action Button
- **Element:** `<button type="button|submit">` (never a clickable `<div>`).
- **States:** `disabled` attribute prevents click; `aria-busy="true"` during async action; spinner SVGs marked `aria-hidden="true"`.
- **Contrast:** Focus ring with minimum 3:1 contrast against both component surface and canvas.

### 2. Form Input Field
- **Structure:** Explicit `<label for="id">` coupled with `<input id="id">`.
- **Validation:** Error states link messages via `aria-describedby="err-id"` and set `aria-invalid="true"`.
- **Touch Target:** Minimum 44×44px interactive tap target boundary.

### 3. Accessible Modal Dialog
- **Anatomy:** `role="dialog"` and `aria-modal="true"` with `aria-labelledby="title-id"`.
- **Focus Management:** Focus trapped inside dialog while open; restored to trigger element upon close.
- **Escape Key:** Pressing Escape triggers dismissal; background container set to `inert`.

### 4. Tab Navigation (`role="tablist"`)
- **Structure:** `<div role="tablist">` contains buttons with `role="tab"` and `aria-selected="true|false"`.
- **Panels:** Associated panels declare `role="tabpanel"` and `aria-labelledby="tab-id"`.
- **Keyboard:** Horizontal Arrow keys cycle active tabs with roving tabindex.

### 5. Data Table
- **Structure:** `<table>` with `<caption>`, `<th scope="col">`, `<th scope="row">`.
- **Numerals:** Financial and metric cells use `font-variant-numeric: tabular-nums`.

## Verification
```bash
python3 -m unittest tests/test_modal_browser.py
python3 gates/gate_bidi_logical.py examples/golden-showcase
```
