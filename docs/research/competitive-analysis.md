# Orthotect Competitive Analysis & Capability Matrix

## 1. Overview & Research Scope

To evolve Orthotect into an industry-leading UI/UX design intelligence and verification platform, we conducted a rigorous comparative analysis of 10 prominent developer tools, design skills, component frameworks, and official specifications:
1. **UI/UX Pro Max** (`https://github.com/nextlevelbuilder/ui-ux-pro-max-skill`)
2. **Anthropic Frontend Design** (`https://github.com/anthropics/skills/tree/main/skills/frontend-design`)
3. **Impeccable** (`https://github.com/pbakaus/impeccable`)
4. **Taste Skill** (`https://github.com/Leonxlnx/taste-skill`)
5. **Radix UI Primitives** (`https://www.radix-ui.com/primitives/docs/overview/introduction`)
6. **W3C WCAG 2.2** (`https://www.w3.org/TR/WCAG22/`)
7. **WAI-ARIA Authoring Practices Guide (APG)** (`https://www.w3.org/WAI/ARIA/apg/`)
8. **Playwright Visual Testing** (`https://playwright.dev/docs/test-snapshots`)
9. **Apple Human Interface Guidelines (HIG)** (`https://developer.apple.com/design/human-interface-guidelines/`)
10. **Design Tokens Community Group (DTCG) W3C Spec** (`https://tr.designtokens.org/format/`)

---

## 2. Comparative Matrix

| Capability Dimension | Existing Orthotect | Reference Systems (Competitors) | Observed Limitation in Competitors | Orthotect Evolved Improvement | Evidence & Test Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Design Reasoning & Art Direction** | Generic principles in doctrine | UI/UX Pro Max, Taste Skill | Uncalibrated keyword-matching; identical output for different products | 19-dimensional structured Design Reasoning Model (`knowledge/schemas/design-reasoning.schema.json`) | Test: 2 distinct briefs produce different art directions (`test_design_reasoning.py`) |
| **Deterministic Quality Gates** | 5 AST/math gates | None (competitors are pure text prompts or linting rules) | Prompt-only systems cannot guarantee zero regressions in CI | Enhanced 5 gates + Scoped AST CSS analyzer + honest `NOT_EVALUATED` semantics | Positive & negative fixtures in `tests/test_cwv.py`, `tests/test_contrast.py` |
| **Token Architecture** | 3-tier DTCG JSON compiler | DTCG Spec, Style Dictionary | Most agent skills hardcode hex values in raw Tailwind classes | Formal DTCG 3-tier tokens (`primitives`, `semantics`, `components`) with cycle detection & export | `tests/test_compiler.py` (61 tests passing) |
| **True Bidirectional Layout (BiDi)** | 100% CSS logical properties gate | None (competitors rely on LTR-only assumptions) | Arabic RTL layouts completely broken or manually inverted with patchy classes | Semantic BiDi rules: logical spacing, vector arrow isolation, mirrored layouts | AST regex gate (`gate_bidi_logical.py`) + browser RTL tests (`test_docs_browser.py`) |
| **State Machine Integrity (FSM)** | Finite state JSON checking | Radix UI, XState | UI libraries leave race conditions & double-submissions to developers | Formally verified UI FSMs: loading locks, terminal states, reachability BFS | Gate 3 (`gate_fsm_integrity.py`) + browser modal dialog focus trap |
| **Accessibility (WCAG 2.2 & ARIA)** | Mathematical contrast check (AA/AAA) | W3C WCAG 2.2, WAI-ARIA APG | Contrast checkers only scan static palettes, missing dynamic hybrid DOM | Mathematical Contrast Matrix + Real browser computed style tests + ARIA APG roles | Automated browser contrast tests in `test_docs_browser.py` |
| **Local Searchable Knowledge Base** | Fragmented prompt docs | UI/UX Pro Max (large markdown files) | Giant single-file prompt dumps cause LLM context bloat and token exhaustion | Modular local JSON/YAML knowledge base with BM25/keyword relevance ranking & provenance | `core/knowledge_search.py` + `tests/test_knowledge_search.py` |
| **CLI Tooling & Developer Experience** | Basic `init`, `verify`, `compile` | Tailwind CLI, Shadcn CLI | Competitor tools lack built-in diagnostics, skill discovery, and auditing | Rich CLI: `doctor`, `skills list/search/show`, `design init/system/page`, `audit --json/--md` | `bin/orthotect.js` + `tests/test_cli_expanded.py` |
| **Interactive Skill Studio** | Client-side SPA (`docs/`) | Storybook, Component catalogs | Static component galleries lack in-browser gate verification | Live Skill Studio with 15 synchronized skills, interactive playground, and real-time gate benchmark | Real Chromium tests in `test_docs_browser.py` |

---

## 3. Key Architectural Takeaways

1. **Avoid Monolithic Prompt Bloat:** Instead of forcing coding agents to load 50,000 tokens of raw rules on every turn, Orthotect uses **Progressive Disclosure**: a compact, highly actionable primary skill (`orthotect-uiux`) that dynamically references specialized modules and queries the local knowledge engine.
2. **Never Confuse Advice with Verification:** Pure prompt libraries cannot prevent a developer or AI from creating unreadable low-contrast text or broken layouts. Orthotect pairs deep design guidance with **deterministic mathematical gates** that execute in sub-second CI pipelines.
3. **True Directional Neutrality:** Unlike US/Euro-centric design tools that treat RTL as an afterthought, Orthotect builds Arabic RTL and English LTR symmetry into the core design tokens and quality gates.
