---
name: orthotect-doctrine
description: The 7 Non-Negotiable Laws of High-Integrity Interface Engineering. Load first whenever authoring, reviewing, or styling any component or screen.
---

# Orthotect Engineering Doctrine

The house constitution for building production-grade enterprise interfaces. Every autonomous agent must uphold these 7 laws:

## Law 1: Verification Protocol (No Hallucinated Claims)
Never state a contrast number, performance metric, or accessibility pass you did not measure. Run the deterministic gates (`python3 gates/run_all_gates.py`) and quote their exact machine output.

## Law 2: Directional Neutrality (True BiDi)
Physical directions (`left`, `right`, `margin-left`, `padding-right`, `float: left`) are strictly forbidden. You MUST use CSS Logical Properties (`margin-inline-start`, `padding-inline-end`, `inset-inline`, `text-align: start`). The application must render identically in LTR and RTL without writing separate CSS.

## Law 3: Finite State Machine Completeness
Every interactive or async element must be backed by a declared FSM. A button cannot just be "styled"; it must explicitly handle:
`idle` → `hover` → `pressed` → `loading` → `successFeedback` / `errorFeedback` → `disabled`.
Loading states must NEVER dim text below WCAG contrast thresholds.

## Law 4: Spring Physics over Arbitrary Timing
Never write lazy transitions like `transition: all 0.2s ease`. Use Orthotect Spring Physics tokens (`--ot-motion-snappy` / `--ot-motion-expressive`) calibrated for mass, stiffness, and damping.

## Law 5: Strict Intent Token Mapping
Color must reflect intent:
- Destructive actions MUST map to `var(--ot-action-danger)`.
- Primary actions MUST map to `var(--ot-action-primary)`.
- Hardcoded hex/rgb values in components are immediate gate rejections.

## Law 6: Cognitive Ergonomics & Fitts' Law
- Touch targets must satisfy minimum 44×44px (pointer 32×32px).
- Information density must follow Miller's 7±2 Law (max 7 top-level navigation items, max 4 primary stat cards per row).

## Law 7: Zero AI Slop
The following statistical AI tropes are banned on sight:
- Generic indigo-to-purple linear gradients.
- Raw emojis used as icons inside buttons or headers.
- Single uniform border radius applied to every element regardless of scale.
