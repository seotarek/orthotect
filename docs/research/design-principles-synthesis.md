# Orthotect Design Principles Synthesis

## 1. Executive Summary

By studying world-class design engineering systems across the industry and formalizing the 19-dimensional Orthotect Design Reasoning Model, we synthesize 8 core design principles that guide all Orthotect skills, components, and quality gates.

---

## 2. The 8 Foundational Design Principles

### Principle 1: Purpose-Driven Hierarchy ("One Thing Leads")
* **The Problem:** Generic AI interfaces suffer from visual flattening: equal-sized cards, identical headers, and lack of visual gravity make it impossible for users to discern the primary task.
* **The Principle:** Every view must establish a singular focal anchor that captures user attention within 200ms. Secondary scan paths and tertiary metadata must visually support, not compete with, the primary task.
* **Verification:** Visual hierarchy audit and DOM density analysis in `orthotect-visual-qa`.

### Principle 2: Semantic Token Binding
* **The Problem:** Hardcoding hex codes (e.g. `#3b82f6`) or arbitrary spacing units produces fragile, fragmented interfaces that break when switching themes or screen densities.
* **The Principle:** All visual values must resolve through a 3-tier DTCG token architecture (`primitives` $\to$ `semantics` $\to$ `components`). Interfaces bind strictly to intent tokens (e.g. `var(--ot-action-primary)`), never raw color values.
* **Verification:** Gate 1 WCAG Contrast Matrix (`gate_contrast_wcag.py`) and token compiler (`core/compiler.py`).

### Principle 3: Scoped Surface Isolation for Terminals & Consoles
* **The Problem:** Mixing global dynamic theme tokens inside fixed-surface components (such as a dark CLI console) causes severe contrast failures in Light Mode (e.g. dark charcoal text on dark navy surface).
* **The Principle:** Fixed-surface components must declare an isolated, dedicated token scope (`--term-bg`, `--term-fg`, `--term-prompt`, `--term-muted`) with mathematically guaranteed contrast ($\ge 7.0:1$) across all global theme states.
* **Verification:** `test_cli_terminal_quickstart_contrast_and_interactivity` in Chromium browser test suite.

### Principle 4: Directional Invariance vs. Symmetrical Mirroring
* **The Problem:** Naive RTL localization either breaks by mirroring non-directional controls (such as video scrubber bars and telephone numbers) or fails to mirror navigation and padding.
* **The Principle:** Interface layouts use 100% CSS logical properties (`margin-inline`, `padding-inline`, `inset-inline`, `text-align: start`). Non-directional elements remain invariant; directional vectors (breadcrumbs, arrows, workflow steppers) mirror symmetrically.
* **Verification:** Gate 2 True BiDi AST analyzer (`gate_bidi_logical.py`).

### Principle 5: Resilient Finite State Machines (FSM Completeness)
* **The Problem:** Modern web applications frequently fail when networks lag: users double-submit forms, UI enters unhandled error deadlocks, or skeleton loaders flash perpetually.
* **The Principle:** Every interactive component must model a formal finite state machine encompassing all canonical edge states: `idle`, `loading`, `error`, `empty`, and `populated`, with double-click locks on transitions.
* **Verification:** Gate 3 FSM Integrity validator (`gate_fsm_integrity.py`).

### Principle 6: Pre-Emptive Media Bounding
* **The Problem:** Layout shifts (Cumulative Layout Shift, CLS) degrade user experience and violate Core Web Vitals when images and charts render without reserved dimensions.
* **The Principle:** Every media element (`<img>`, `<video>`, `<svg>`, `<iframe>`) must declare explicit positive integer dimensions or CSS `aspect-ratio` bounding to reserve layout space prior to asset load.
* **Verification:** Gate 5 DOM Depth & Media Budget analyzer (`gate_cwv_budget.mjs`).

### Principle 7: Cognitive Ergonomics in Data Visualization
* **The Problem:** Cluttered dashboards dump dozens of uncalibrated charts with rainbow color schemes that create cognitive overload.
* **The Principle:** Data displays use restrained semantic palettes (cyan for active telemetry, emerald for healthy thresholds, amber for warnings, crimson for critical limits). Inline SVG micro-charts provide instant context with zero external dependencies.
* **Verification:** `orthotect-dashboard` and `orthotect-data-viz` component validation.

### Principle 8: Accessible Keyboard & Dialog Focus Traps
* **The Problem:** Modal dialogs, drawers, and popovers frequently leak keyboard focus into the background page, trapping screen reader users and breaking WCAG 2.2 AA conformance.
* **The Principle:** Overlays must declare `role="dialog"`, `aria-modal="true"`, trap Tab navigation within their bounds, close on Escape key, and cleanly restore focus to the triggering element upon dismissal.
* **Verification:** Automated Playwright browser tests (`test_mobile_drawer_dialog_and_focus_trap` and `test_docs_modal_dialog_focus_trap_and_lifecycle`).
