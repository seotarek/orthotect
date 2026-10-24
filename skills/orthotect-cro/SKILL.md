---
name: orthotect-cro
description: Interface Conversion Rate Optimization (CRO) engineering. Optimize form completion, CTA visual hierarchy, value proposition clarity, mobile tap targets, and friction reduction. Use when analyzing conversion barriers, improving sign-up/checkout flows, or reducing form abandonment.
metadata:
  version: 1.0.0
---

# Skill: Orthotect Interface Conversion Rate Optimization (CRO)

Engineering high-converting, accessible, and resilient digital interfaces. CRO in Orthotect merges behavioral psychology with deterministic interface engineering: high-contrast call-to-actions, cognitive load minimization, zero layout shift, and resilient form state machines.

## Reference Routing

Load the matching reference before implementing or auditing specific interface components:

| User Intent & Focus Area | Reference File | Covers |
|---|---|---|
| Form abandonment, field reduction, inline validation, progressive disclosure | [form-cro.md](references/form-cro.md) | Form layout ergonomics, cognitive friction reduction, FSM integration, and accessible error handling |
| Call-to-action prominence, contrast hierarchy, sticky mobile bars | [cta-hierarchy.md](references/cta-hierarchy.md) | Button token mapping, visual hierarchy, mobile tap target ergonomics, and microcopy clarity |

---

## The 5 Pillars of Interface CRO

### 1. Value Proposition & Visual Focus (5-Second Rule)
- **Primary Hero Visual**: Ensure the primary value statement and primary CTA are immediately visible above the fold on 360px mobile and 1440px desktop viewports without layout shift.
- **Cognitive Clarity**: Avoid generic hero claims. Pair a concrete headline with a subhead explaining *how* the product delivers value.

### 2. CTA Prominence & Token Discipline
- **One Primary Action**: Every screen must feature one unmistakable primary action using the high-contrast semantic token (`--ot-color-primary`).
- **Secondary Actions**: Demote competing actions to ghost or outlined styles (`--ot-bg-subtle` or border-only) to avoid choice paralysis.
- **Ergonomic Tap Targets**: All clickable and touch targets must measure at least 48x48px on touch viewports (`min-inline-size: 48px; min-block-size: 48px`).

### 3. Friction Elimination & Form Resilience
- **Radical Field Reduction**: Remove optional fields; defer non-critical inputs post-conversion.
- **Inline Validation & Immediate Feedback**: Validate on blur, not on submit. Use `aria-describedby` to link input to helper text.
- **Double-Submission Prevention**: Always wire form submission buttons to an explicit FSM state machine preventing duplicate submits (see `orthotect-fsm`).

### 4. Trust Signals & Social Proof Integration
- **Contextual Proof**: Place security badges, uptime metrics, or customer logos directly adjacent to the conversion trigger (e.g., right under the primary CTA button or payment form).
- **Accessible Verification**: Never use flat low-contrast images for logos. Ensure SVG trust icons meet WCAG AA contrast (4.5:1).

### 5. Layout Shift & CWV Speed Protection
- **Zero CLS**: Reserve aspect ratios for all hero images, video embeds, and dynamic elements to eliminate layout shifts that induce mis-clicks.
- **Sub-100ms INP**: Ensure button hover and active states respond instantly using hardware-accelerated CSS transforms.

---

## Attribution & Licensing

Portions of the conversion analysis framework adapted from [marketingskills](https://github.com/coreyhaines31/marketingskills) by Corey Haines under the MIT License (Copyright 2025 Corey Haines).
