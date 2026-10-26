#!/usr/bin/env python3
"""
Orthotect Skill Catalog Builder
Authors and validates all 15 modular skills in skills/*/SKILL.md.
"""

import sys
from pathlib import Path

# Deprecation Guard: prevent accidental overwriting of mature skills
if __name__ == '__main__':
    print("❌ [DEPRECATED] scripts/build_skills_catalog.py is deprecated.")
    print("   Skills in skills/*/SKILL.md are actively maintained and validated via 'npm run validate:skills'.")
    print("   To prevent clobbering mature skills, this generator is disabled.")
    sys.exit(1)

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT_DIR / "skills"

SKILLS_DATA = [
    {
        "dir": "orthotect-visual-qa",
        "name": "orthotect-visual-qa",
        "description": "Execute automated browser visual regression, color contrast, and layout shift verification using Playwright. Use when verifying rendered UI, validating theme switching, or checking that light and dark modes have zero visual clashes.",
        "content": """# Skill: Orthotect Visual QA & Automated Browser Verification

Use this skill to execute deterministic browser-based visual QA, verify rendered computed styles, test theme reactivity, and catch visual regressions before shipping code.

## Verification Protocol
1. **Computed Style Auditing:** Never guess contrast from CSS files alone. Verify rendered contrast via `getComputedStyle(element).color` and `backgroundColor`.
2. **Dual-Theme Verification:** Test both `data-theme="dark"` and `data-theme="light"`. Light mode must never render dark text on dark surfaces or white bars through dark components.
3. **Reactive Synchronization:** When toggling themes, verify that subordinate viewports (playgrounds, terminals, toolbars, wordmarks) synchronize immediately.
4. **Cumulative Layout Shift (CLS):** Verify CLS stays under 0.05 during font and media asset loading.

## Automated Commands
```bash
# Run browser regression tests
python3 -m unittest tests/test_docs_browser.py

# Run all unit and browser tests
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Anti-Patterns
- Assuming a component looks good without rendering in headless Chromium.
- Inverting dark colors without testing contrast on secondary labels and borders.
- Disabling outline rings on focused elements during mouse clicks.
"""
    },
    {
        "dir": "orthotect-uiux",
        "name": "orthotect-uiux",
        "description": "Master UI/UX design intelligence and autonomous interface orchestration. Selects original style recipes, establishes 19-dimensional design reasoning, enforces semantic tokens, and orchestrates specialized Orthotect skills for production-grade UI.",
        "content": """# Skill: Orthotect UI/UX Design Intelligence (Master Orchestrator)

The central entry point for autonomous UI/UX design and frontend interface architecture.

## Workflow Pipeline
1. **Context & Brief Analysis:** Map product requirements to the 19-dimensional Orthotect Design Reasoning Model.
2. **Style Recipe Selection:** Query `core/knowledge_search.py` to select the best-fitting style recipe (e.g. `restrained-editorial-clarity`, `precision-analytical-console`, `contemporary-product-saas`, `high-density-operational`, `material-led-commerce`, `accessible-high-contrast`).
3. **Token Binding:** Compile DTCG tokens (`node bin/orthotect.js compile`) and bind all surfaces to intent tokens.
4. **Component Architecture:** Design components backed by FSM state contracts (`orthotect-fsm` & `orthotect-components`).
5. **Bidirectional Symmetry:** Enforce CSS logical properties (`orthotect-bidi`).
6. **Gate Verification:** Execute the 6 deterministic quality gates before committing.

## Querying Knowledge Base
```bash
# Search for relevant design patterns or style recipes
python3 core/knowledge_search.py "dashboard operational" --category styles

# Validate UI/UX knowledge schemas
python3 core/knowledge_search.py --validate
```

## Anti-Patterns
- Generic purple/indigo AI slop gradients.
- Generating screens without querying design tokens or state contracts.
- Skipping quality gate verification.
"""
    },
    {
        "dir": "orthotect-design-systems",
        "name": "orthotect-design-systems",
        "description": "Architect and maintain enterprise design systems, W3C DTCG token hierarchies (primitives -> semantics -> components), multi-brand theming, and cross-platform token compilation. Use when establishing design tokens or multi-theme support.",
        "content": """# Skill: Orthotect Design Systems Architecture

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
"""
    },
    {
        "dir": "orthotect-components",
        "name": "orthotect-components",
        "description": "Author production-grade, accessible UI components with full WAI-ARIA APG contracts, keyboard navigation, focus management, and 8 explicit states (idle, hover, active, focus, loading, disabled, error, success).",
        "content": """# Skill: Orthotect Accessible Component Engineering

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
"""
    },
    {
        "dir": "orthotect-accessibility",
        "name": "orthotect-accessibility",
        "description": "Audit and enforce WCAG 2.2 Level AA/AAA accessibility standards. Verifies color contrast, keyboard navigation, focus appearance, touch target sizes (min 44x44px), and screen reader announcements. Use before shipping any UI.",
        "content": """# Skill: Orthotect WCAG 2.2 Accessibility Auditing

Use this skill to audit, diagnose, and resolve accessibility barriers in web applications according to WCAG 2.2 Level AA (and Level AAA where required).

## Critical Verification Criteria
1. **WCAG 1.4.3 / 1.4.6 Contrast:** Normal text >= 4.5:1 (AA) or >= 7.0:1 (AAA); large text >= 3.0:1 (AA) or >= 4.5:1 (AAA).
2. **WCAG 1.4.11 Non-text Contrast:** UI components and focus indicators >= 3.0:1 against background.
3. **WCAG 2.1.1 Keyboard Navigation:** 100% of interactive controls operable without a mouse.
4. **WCAG 2.4.7 / 2.4.13 Focus Appearance:** High-contrast visible focus indicator on keyboard tab navigation.
5. **WCAG 2.5.8 Target Size:** Minimum pointer target 24×24px; touch target minimum 44×44px.

## Deterministic Verification
```bash
# Mathematical contrast verification across all token pairs
python3 gates/gate_contrast_wcag.py
```
"""
    },
    {
        "dir": "orthotect-responsive",
        "name": "orthotect-responsive",
        "description": "Engineer resilient responsive layouts using CSS Grid, container queries, fluid typography (clamp()), and adaptive bento layouts. Prevents horizontal overflows and layout shifts across viewports from 360px to 2560px.",
        "content": """# Skill: Orthotect Responsive & Adaptive Layouts

Use this skill to design responsive layouts that adapt seamlessly from mobile viewports (360px) to ultrawide displays (2560px) without horizontal scrolling or cumulative layout shift.

## Architectural Guidelines
1. **Container Queries Over Media Queries:** Use `@container` for component-level reflow based on container width rather than whole viewport width.
2. **Fluid Typography:** Use `clamp()` for scalable headings:
   `font-size: clamp(1.5rem, 1rem + 2vw, 3rem);`
3. **Intrinsic Grid Sizing:** Avoid fixed pixel widths in grid columns:
   `grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));`
4. **Aspect Ratio Bounding:** Bound all media with `aspect-ratio` to eliminate Cumulative Layout Shift (CLS = 0).

## Anti-Patterns
- Fixed `width: 1200px` causing mobile horizontal scrolling.
- Cluttered navigation menus that overflow viewport boundaries on tablet portrait screens.
- Hiding critical action buttons on mobile instead of adapting their presentation.
"""
    },
    {
        "dir": "orthotect-motion",
        "name": "orthotect-motion",
        "description": "Design physically grounded UI motion using Orthotect spring physics tokens, choreographed staggered reveals, and mandatory @media (prefers-reduced-motion) overrides. Ensures high-performance 60fps/120fps hardware-accelerated transitions.",
        "content": """# Skill: Orthotect Spring Physics Motion & Animation

Use this skill to implement polished micro-interactions, modal transitions, and dashboard data streaming animations.

## Spring Physics Tokens
- `--ot-motion-snappy`: `150ms cubic-bezier(0.16, 1, 0.3, 1)` (Tactile button presses, checkboxes, toggles).
- `--ot-motion-expressive`: `300ms cubic-bezier(0.34, 1.56, 0.64, 1)` (Modal dialog entry, drawer reveal, toast notification).

## The Non-Negotiable Motion Rules
1. **GPU Acceleration Only:** Animate strictly `transform` and `opacity`. Never animate `width`, `height`, `top`, or `margin`.
2. **Reduced Motion Law:** Every animation must include a `@media (prefers-reduced-motion: reduce)` override collapsing transition times to 0ms or simple opacity cross-fade.
3. **Duration Budget:** Never exceed 400ms for everyday UI transitions.

## Verification
```bash
python3 gates/gate_no_slop.py <path>
```
"""
    },
    {
        "dir": "orthotect-forms",
        "name": "orthotect-forms",
        "description": "Engineer resilient forms with double-submission locks, asynchronous validation FSMs, inline error feedback, accessible field labels, and optimistic state recovery. Use when building login, checkout, settings, or multi-step wizard forms.",
        "content": """# Skill: Orthotect Resilient Form Engineering

Use this skill when building forms, checkout flows, settings panels, or multi-step input wizards.

## Form FSM State Machine
Forms must cycle through explicit states:
`pristine` → `editing` → `validating` → `submitting` → `successFeedback` / `submissionError`.

## Mandatory Engineering Rules
1. **Double-Submission Lock:** Immediately disable submit buttons on click; ignore duplicate click/enter events until resolution.
2. **Persistent Field Labels:** Never rely on placeholder text as a field label. Always provide `<label for="...">` with visible text.
3. **Dual Error Cues:** Errors must display both a colored indicator and an explicit descriptive error message linked via `aria-describedby`.
4. **Preserve User Input:** Never wipe form data on validation error.

## Verification
```bash
python3 gates/gate_fsm_integrity.py
```
"""
    },
    {
        "dir": "orthotect-data-viz",
        "name": "orthotect-data-viz",
        "description": "Build high-density, accessible data visualizations, sparklines, telemetry charts, and operational metrics using token-driven SVG geometry, tabular numerals, and zero layout shift. Use when building telemetry consoles or dashboards.",
        "content": """# Skill: Orthotect Data Visualization & Telemetry Engineering

Use this skill when engineering charts, operational telemetry, sparklines, or dense data matrices.

## Data Visualization Doctrine
1. **Tabular Numerals:** Apply `font-variant-numeric: tabular-nums` to all data cells and chart labels to prevent layout jitter during live updates.
2. **Intent-Driven Chart Tokens:** Use semantic tokens for chart metrics (emerald for normal, amber for warning, red for critical, cyan for secondary telemetry).
3. **Accessible Data Tables:** Every visual chart must provide an accessible alternative (e.g. an accessible table or screen-reader summary using `aria-label`).
4. **Zero Layout Shift:** Chart containers must reserve fixed aspect ratios or bounding boxes before data loads.

## Verification
```bash
python3 gates/gate_cwv_budget.mjs examples/golden-showcase
```
"""
    }
]

def main():
    print("=================================================================")
    print("           ORTHOTECT MODULAR SKILLS CATALOG BUILDER              ")
    print("=================================================================\n")

    for skill in SKILLS_DATA:
        s_dir = SKILLS_DIR / skill["dir"]
        s_dir.mkdir(parents=True, exist_ok=True)
        skill_file = s_dir / "SKILL.md"
        
        full_content = f"""---
name: {skill["name"]}
description: {skill["description"]}
---

{skill["content"].strip()}
"""
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(full_content)
        print(f"  [OK] Authored: skills/{skill['dir']}/SKILL.md (desc len: {len(skill['description'])} chars)")

    print(f"\n[+] SUCCESS! All {len(SKILLS_DATA)} modular skills authored successfully.")

if __name__ == "__main__":
    main()
