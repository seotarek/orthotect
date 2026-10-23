---
name: orthotect-uiux
description: Master UI/UX design intelligence and autonomous interface orchestration. Selects original style recipes, establishes 19-dimensional design reasoning, enforces semantic tokens, and orchestrates specialized Orthotect skills for production-grade UI.
---

# Skill: Orthotect UI/UX Design Intelligence (Master Orchestrator)

The central entry point for autonomous UI/UX design and frontend interface architecture.

## Workflow Pipeline
1. **Context & Brief Analysis:** Map product requirements to the 19-dimensional Orthotect Design Reasoning Model.
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
