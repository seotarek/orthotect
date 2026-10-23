# Orthotect Design Reference Methodology & Information Architecture

## 1. Executive Overview

Modern design reference catalogs (such as `styles.refero.design`, Material Design, Apple HIG, and Radix UI) demonstrate that high-performance interface design requires more than superficial CSS styles. High-integrity design systems communicate a cohesive, multi-layered information architecture.

This document analyzes the information architecture of modern design references, establishes the 8 core dimensions of legitimate design analysis, and introduces the formal **19-Dimensional Orthotect Design Reasoning Model**.

---

## 2. The 8 Structural Dimensions of Design References

When analyzing public design references under the Orthotect Research Policy, the inspection must evaluate 8 functional dimensions rather than recording a simple palette list:

1. **Design Thesis & Visual Direction:** The central visual metaphor, audience context, emotional tone, and density calibration.
2. **Color Architecture:** Semantic role assignments (canvas, surface, panel, primary action, destructive action, feedback, borders) rather than raw hex values.
3. **Typography & Content Hierarchy:** Typeface personalities, proportional type scales, line heights, letter spacings, and responsive heading behaviors.
4. **Layout, Composition & Spatial Rhythm:** Grid systems, content max-widths, asymmetric balance, vertical rhythm, and section transitions.
5. **Surfaces, Shape & Depth:** Border radii, double-bezel borders, elevation layering, blur effects, and depth hierarchy.
6. **Components & Interaction Behavior:** Buttons, inputs, tables, modals, active states, focus rings, and transition contracts.
7. **Imagery, Icons & Visual Assets:** Iconography consistency, image bounding, aspect-ratio preservation, and asset density.
8. **Explicit Constraints & Anti-Patterns:** Rules that prevent generic AI tropes, uncalibrated gradients, and contrast failures.

---

## 3. The 19-Dimensional Orthotect Design Reasoning Model

To transform product briefs into coherent, mathematically certified visual systems, Orthotect implements an original 19-dimensional reasoning model:

1. **Product & User-Task Context:** Transactional, analytical, editorial, operational, or promotional.
2. **Audience & Domain Constraints:** Consumer, enterprise B2B, developer tooling, fintech, healthcare.
3. **Chosen Art Direction:** Concrete visual archetype selected based on contextual fit.
4. **Visual Hierarchy:** Primary focal anchor ("One Thing Leads"), secondary scan paths, and tertiary metadata.
5. **Composition & Layout:** Split views, bento grids, full-width data consoles, centered reading columns.
6. **Color-Role Architecture:** Canvas, surface tiers (1, 2, 3), text primary/secondary/muted, action primary/danger/warning.
7. **Typography System:** Display font, body font, monospace data font, modular ratio scale (e.g. 1.25 Major Third).
8. **Spacing & Sizing Scale:** Base 4px/8px modular rhythm, container limits, comfortable vs. compact density.
9. **Component Language:** Anatomy, variant matrix, size tiers, double-bezel frames.
10. **Interaction States:** The 8 canonical states (idle, hover, active, focus-visible, selected, loading, disabled, error).
11. **Content & Asset Treatment:** Visual assets, micro-telemetry sparklines, vector isolation.
12. **Responsive Adaptations:** 7 viewport tiers (320px, 360px, 390px, 768px, 1024px, 1280px, 1440px), fluid reflow.
13. **BiDi (RTL/LTR) Behavior:** 100% CSS logical properties, directional vector isolation, mirror-safe layouts.
14. **Accessibility Constraints:** WCAG 2.2 AA (4.5:1 text, 3.0:1 controls) & AAA (7.0:1) contrast, focus traps, ARIA APG.
15. **Motion Character:** Duration tokens (100ms-300ms), physics-based easing curves, `prefers-reduced-motion` compliance.
16. **Design Anti-Patterns:** Explicit list of forbidden tropes (uncalibrated purple gradients, raw emojis in buttons, unbudgeted media).
17. **Implementation-Specific Decisions:** Stack adapters (vanilla HTML/CSS, React/Tailwind, Vue, Next.js).
18. **Verification Requirements:** Exact CLI commands, quality gate assertions, and browser test checks.
19. **Confidence & Known Limitations:** Transparent declaration of what is mathematically proven vs. heuristic.
