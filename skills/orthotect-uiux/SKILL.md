---
name: orthotect-uiux
description: Master UI/UX design intelligence and autonomous interface orchestration. Selects original style recipes, establishes 19-dimensional design reasoning, enforces semantic tokens, and orchestrates specialized Orthotect skills for production-grade UI.
---

# Skill: Orthotect UI/UX Design Intelligence (Master Orchestrator)

The central entry point for autonomous UI/UX design and frontend interface architecture.

## The 19-Dimensional Design Reasoning Model
Refer to the formal schema in `knowledge/schemas/design-reasoning.schema.json`:
1. **Product Context:** Product type (`saas`, `dashboard`, `ecommerce`), primary user task, data density.
2. **Audience Constraints:** Domain, user expertise level.
3. **Chosen Art Direction:** Recipe ID from `knowledge/styles/`, thesis statement, mood keywords.
4. **Visual Hierarchy:** Primary anchor, secondary scan paths.
5. **Composition & Layout:** Grid system (asymmetric, bento, fluid), layout rhythm.
6. **Color Role Architecture:** Semantic tokens for canvas, surfaces, borders, text, and action accents.
7. **Typography System:** Editorial pairing from `knowledge/typography/`, fluid type scales (`clamp()`).
8. **Spacing Scale:** 4px/8px DTCG rem multiples.
9. **Component Language:** Border radii, elevation shadows, borders.
10. **Interaction States:** 8 explicit states (idle, hover, pressed, focus-visible, loading, disabled, error, success).
11. **Content & Asset Treatment:** Technical SVGs, authentic schematics (no generic stock photos).
12. **Responsive Adaptations:** Breakpoint strategies, `@container` queries.
13. **BiDi Behavior:** 100% CSS logical properties, directional vector isolation.
14. **Accessibility Constraints:** WCAG 2.2 AAA contrast, touch targets (≥44px), ARIA APG roles.
15. **Motion Character:** Spring physics, duration tokens, `prefers-reduced-motion` fallbacks.
16. **Anti-Patterns to Avoid:** Banned purple AI gradients, emoji icon pollution, physical coordinates.
17. **Implementation Stack:** Framework (HTML, React, Vue, Svelte), CSS architecture.
18. **Verification Requirements:** Execution of all 5 deterministic quality gates.
19. **Confidence & Limitations:** Boundary checks, explicit fallback states.

## Workflow Pipeline
1. **Context & Brief Analysis:** Formulate the design brief across the 19 dimensions above.
2. **Style Recipe Selection:** Query `core/knowledge_search.py` to select the best-fitting style recipe (e.g. `restrained-editorial-clarity`, `precision-analytical-console`, `contemporary-product-saas`, `high-density-operational`, `material-led-commerce`, `accessible-high-contrast`).
3. **Token Binding:** Compile DTCG tokens (`node bin/orthotect.js compile`) and bind all surfaces to intent tokens.
4. **Component Architecture:** Design components backed by FSM state contracts (`orthotect-fsm` & `orthotect-components`).
5. **Bidirectional Symmetry:** Enforce CSS logical properties (`orthotect-bidi`).
6. **Gate Verification:** Execute the 5 deterministic quality gates before committing.

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
