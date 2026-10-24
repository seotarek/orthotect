# 🏛️ Orthotect

### The Deterministic Interface Engineering & Runtime Gate Architecture for AI Coding Agents

[![Version](https://img.shields.io/badge/version-1.7.4-6366f1?style=for-the-badge)](https://github.com/seotarek/orthotect/releases)
[![Live Showcase](https://img.shields.io/badge/Live_Showcase-GitHub_Pages-0ea5e9?style=for-the-badge)](https://seotarek.github.io/orthotect/)
[![CI Status](https://github.com/seotarek/orthotect/actions/workflows/ci.yml/badge.svg)](https://github.com/seotarek/orthotect/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)
[![WCAG 2.2 Contrast Matrix](https://img.shields.io/badge/WCAG_2.2-Contrast_Matrix_(AA%2FAAA)-a855f7?style=for-the-badge)](#)
[![Gates: 100% Deterministic](https://img.shields.io/badge/Quality_Gates-Deterministic-14b8a6?style=for-the-badge)](#)
[![BiDi: 100% Logical](https://img.shields.io/badge/BiDi-True_RTL/LTR-f97316?style=for-the-badge)](#)

> **Live Interactive Showcase & Playground:** [https://seotarek.github.io/orthotect/](https://seotarek.github.io/orthotect/)  
> **Engineering Whitepapers:** [Competitor Teardown (COMPETITORS.md)](COMPETITORS.md) | [The 7 Laws Manifesto (MANIFESTO.md)](MANIFESTO.md)

Orthotect is an enterprise-grade interface engineering toolkit built to enforce **deterministic architectural quality gates and state machine rigor** onto autonomous coding agents (Antigravity, Cursor, Claude Code, Codex, Grok). 

Unlike superficial prompt libraries that merely request "good design", Orthotect provides a **mathematical token foundation**, **Finite State Machine (FSM) graph reachability**, and **objective quality gates** that fail the build with `exit 1` if standards are breached.

---

## ⚡ Architectural Comparison & Ecosystem Delineation

For an in-depth technical analysis, read our [Architectural Comparison Whitepaper](COMPETITORS.md).

| Capability / Dimension | Prompt-Only Skills (e.g. XIAS / taste-skill) | Component Libraries (e.g. shadcn/ui) | 🏛️ Orthotect Architecture (Deterministic Gates) |
|---|---|---|---|
| **Verification Model** | Textual guidelines & system prompt rules; no native AST gate runner | Visual inspection, Storybook, or manual unit testing | **Target-Aware & Zero-Fallback:** Inspects user project directory (`orthotect verify <dir>`) with strict path boundaries and real exit codes |
| **Project Initialization** | Prompt instructions without direct filesystem scaffolding | Code copy-pasting / CLI component adder | **Deterministic File Scaffolding:** Copies tokens, FSM specs, and `AGENTS.md` directly into target repository (`orthotect init <dir>`) |
| **State Engineering** | Static UI snapshots without transition graphs | Ad-hoc `isLoading` boolean flags | **Formal Finite State Machines (FSM)** with graph reachability, double-submission race locks & async recovery |
| **BiDi / RTL Support** | Textual guidance recommending logical properties | Physical utility classes (`ml-*`, `pr-*`) common | **Enforced CSS Logical Properties** (`margin-inline`, `padding-inline`, `border-inline`, `inset-inline`) across audited fixtures |
| **Layout Shift Budget** | Subjective reminders in prompt | Dependent on developer discipline | **Structural Layout-Shift (CLS) Budget** enforcing reserved media dimensions (`width` + `height` or `aspect-ratio`) and stream-based DOM nesting limits |
| **Motion Engineering** | Generic `0.2s ease` transitions | CSS transition presets | **Spring Physics Curves** (Stiffness, Damping, Mass) |
| **Cognitive Ergonomics** | Arbitrary card layouts | Component presets | **Fitts' Law** touch targets (≥44px) & **Miller's 7±2 Law** density constraints |
| **Anti-Slop Defense** | Subjective prompt instructions | Out of scope (styling only) | **Lexical & Pattern Inspectors** that reject AI indigo-purple gradients, raw emoji icons, and untokenized styles |
| **Design Tokens** | Variable guidance in markdown | Tailwind configuration | **W3C DTCG 3-Tier Compiler** generating `:root` light and `[data-theme="dark"]` scopes |

---

## 🏗️ Architecture Overview

```text
orthotect/
├── core/
│   ├── compiler.py          # W3C DTCG Token Compiler (:root light and [data-theme="dark"])
│   ├── knowledge_search.py  # Zero-dependency UI/UX knowledge base search engine
│   ├── context_optimizer.py # Token-optimizer, density profiler & semantic chunker
│   ├── tokens/              # W3C DTCG 3-Tier Design Tokens (Primitives, Semantics, Motion, Ergonomics)
│   └── fsm/                 # State Machine Specifications (Buttons, Data Tables, Modal Dialogs)
├── knowledge/               # UI/UX Design Intelligence & Validated Style Recipes
│   ├── schemas/             # JSON Schemas (design-reasoning, style-recipe, knowledge-record)
│   ├── styles/              # 6 Original Style Recipes (editorial, analytical, saas, operational, etc.)
│   └── [category]/          # Curated Knowledge Records (palettes, typography, components, etc.)
├── docs/                    # 7-View Skill Studio Platform & Interactive Showcase (GitHub Pages)
│   ├── index.html           # 7-view bilingual (EN/AR) interactive workbench
│   ├── styles.css           # 100% CSS Logical Properties & DTCG token variables
│   └── app.js               # Client-side router, 18-skill catalog, playground, builder, and gate simulator
├── gates/                   # Objective Deterministic Checkers (Python & Node.js)
│   ├── gate_contrast_wcag.py     # Mathematical Relative Luminance (WCAG 2.2 AAA/AA)
│   ├── gate_bidi_logical.py      # Strict Enforcement of CSS Logical Properties
│   ├── gate_fsm_integrity.py     # State Machine Graph Reachability & Lock Integrity
│   ├── gate_no_slop.py           # Lexical & Pattern Slop Inspector
│   ├── gate_cwv_budget.mjs       # WHATWG-Compliant DOM & Layout-Shift Budget
│   └── run_all_gates.py          # Parallel Master Gate Orchestrator (ThreadPoolExecutor)
├── skills/                  # 18 Agent Skills (Progressive Disclosure)
│   ├── orthotect-doctrine        # The 7 Non-Negotiable Laws
│   ├── orthotect-uiux            # Master UI/UX Design Intelligence & Orchestrator
│   ├── orthotect-design-systems  # DTCG Token Hierarchy & Multi-Brand Themes
│   ├── orthotect-components      # Accessible Component Contracts & 8 FSM States
│   ├── orthotect-accessibility   # WCAG 2.2 AA/AAA Deterministic Verification
│   ├── orthotect-bidi            # Directional Neutrality & RTL Engineering
│   ├── orthotect-dashboard       # High-Density Console Design
│   ├── orthotect-fsm             # State Machine Implementation Workflows
│   ├── orthotect-forms           # Resilient Forms & Double-Submit Locks
│   ├── orthotect-responsive      # Adaptive Bento Layouts & Fluid Scales
│   ├── orthotect-motion          # Spring Physics Motion Tokens & Reduced-Motion
│   ├── orthotect-data-viz        # Accessible Telemetry & Tabular Numbers
│   ├── orthotect-tokens          # Token Management & Theme Compilation
│   ├── orthotect-gates           # Gate Execution Workflows
│   ├── orthotect-visual-qa       # Automated Browser Visual Regression Gate
│   ├── orthotect-context         # Token-Optimizer & Context Architecture Guard
│   ├── orthotect-cro             # Interface Conversion Rate Optimization & Form Ergonomics
│   └── orthotect-schema          # Semantic Structured Data & Schema.org JSON-LD
├── scripts/                 # Skills Specification Validator, Packager & Metadata Guards
│   ├── validate-skills.mjs       # Agent Skills specification validator (SPDX & recursive refs)
│   ├── package_skills.py         # Deterministic cross-agent skill packager & security scanner
│   └── check-package-metadata.mjs# Synchronized package version & lockfile guard
├── tests/                   # Comprehensive Unit, Browser & Negative Test Suite (291 Tests)
│   ├── test_contrast.py          # Relative luminance & contrast threshold unit tests
│   ├── test_bidi.py              # BiDi logical scanner positive/negative tests
│   ├── test_auto_fix.py          # BiDi auto-healing (--fix) remediation tests
│   ├── test_hooks_cli.py         # Git pre-commit hook installation & enforcement tests
│   ├── test_config.py            # Configuration loader, deep-merge & path exclusion tests
│   ├── test_fsm.py               # FSM graph reachability and deadlock tests
│   ├── test_core_sync.py         # Canonical FSM schemas & DTCG tokens single-source-of-truth tests
│   ├── test_cwv.py               # Media dimension, aspect-ratio & iterative parse5 DOM depth tests
│   ├── test_slop.py              # AI purple gradient & raw emoji anti-pattern tests
│   ├── test_compiler.py          # W3C DTCG CSS custom property compiler tests
│   ├── test_skills_sync.py       # Skills directory / docs/app.js catalog sync tests
│   ├── test_knowledge_search.py  # Knowledge base search, filtering & schema validation tests
│   ├── test_context_optimizer.py # Token estimation, density profiling & skeleton tests
│   ├── test_cli_expanded.py      # Doctor, skills show/validate, and design CLI tests
│   ├── test_docs_browser.py      # Playwright 7-view Skill Studio browser integration & negative benchmark tests
│   ├── test_modal_browser.py     # Playwright headless Chrome focus trap & FSM tests
│   ├── test_scaffold_browser.py  # Playwright scaffolded page FSM lifecycle & race lock browser tests
│   ├── test_cli_e2e.py           # E2E CLI verification, boundary & negative rejection tests
│   ├── test_skill_evals.py       # Skill evaluation fixture schema & JSON-LD template validity tests
│   └── test_skill_packaging.py   # Skill packager reproducibility, security & manifest tests
├── .github/workflows/       # Automated CI & GitHub Pages Deployment Pipelines
│   ├── ci.yml                    # 291 Unit, Browser & Negative Gate Tests & Full Gate Verification
│   ├── publish-package.yml       # Release concurrency & fail-closed package publisher
│   └── pages.yml                 # Automated GitHub Pages Deployment
├── agents/
│   └── orthotect-auditor.md      # Adversarial Quality Auditor Role
├── AGENTS.md                # Universal multi-agent system doctrine and lifecycle rules
├── CLAUDE.md                # Claude Code configuration & command-agent-skill guidance
├── CHANGELOG.md             # Full version history (v1.0.0 → v1.7.4)
├── CONTRIBUTING.md          # Enterprise engineering guidelines
├── COMPETITORS.md           # Exhaustive architectural competitor teardown
├── MANIFESTO.md             # The 7 Laws of Interface Engineering
└── examples/
    └── golden-showcase/          # Reference Enterprise Console passing 100% of gates
```

---

## 🚦 Deterministic Quality Gates & Auto-Healing

Run the verification suite against your project:

```bash
# Verify current project
npx orthotect verify .

# Auto-heal physical CSS properties in-place (margin-left → margin-inline-start, etc.)
npx orthotect verify . --fix

# Install automated Git pre-commit hook (blocks violating commits before landing)
npx orthotect hooks install

# Generate machine-readable JSON or Markdown audit reports
npx orthotect verify ./src --json
npx orthotect verify ./src --md
```

### ⚙️ Configuration Engine (`orthotect.config.json`)

Customize file exclusion globs, DOM nesting depth limits, and gate toggles per project:

```json
{
  "exclude": ["node_modules/**", "dist/**", "build/**", "legacy/**"],
  "cwv": {
    "maxDomDepth": 32,
    "maxDomNodes": 1500
  },
  "bidi": {
    "allowCamelCase": false
  },
  "contrast": {
    "level": "AA"
  }
}
```

Illustrative Reference Verification Output (Target: `examples/golden-showcase`):
> *Note: Parallel gate execution latencies are measured dynamically per run and scale with repository size and host hardware (typically 120ms – 590ms; latest GitHub Actions CI run executed in ~126ms).*

```text
╔═══════════════════════════════════════════════════════════════╗
║            ORTHOTECT DETERMINISTIC QUALITY GATES              ║
║     Deterministic High-Integrity Engineering Protocol         ║
╚═══════════════════════════════════════════════════════════════╝
 Target Path: /your/project/path

GATE NAME                              STATUS           TIME
───────────────────────────────────────────────────────────────
WCAG 2.2 Mathematical Contrast         ✅ PASS        121.4ms
True BiDi & Logical Properties         ✅ PASS        118.7ms
Finite State Machine Integrity         ✅ PASS        120.9ms
Anti-Slop Pattern Inspector            ✅ PASS        124.9ms
DOM & Layout-Shift Budget              ✅ PASS        551.4ms
───────────────────────────────────────────────────────────────
Total Verification Time (Parallel): 554.2ms

🎉 ALL GATES PASSED! Target files verified against evaluated interface standards.
   Verified Standards: WCAG 2.2 Contrast, CSS Logical BiDi, FSM Integrity, Anti-Slop, DOM CLS Budget.
   Notice: Verifies deterministic interface constraints; does not replace runtime security, auth, or load audits.
```

---

## 🛡️ Dual-Layer Verification Architecture & Scope Delineation

Orthotect provides **Deterministic Static & AST Gate Verification** designed to run at millisecond speed in CLI, agent loops, and pre-commit hooks:

| Layer | Tooling & Mechanism | Target Scope | Orthotect Alignment |
|---|---|---|---|
| **Layer 1: Static AST & Pattern Verification** | Orthotect Python AST & Node Gates | Lexical slop, CSS logical properties, color tokens, FSM graph locks, DOM layout shift budgets | 🏛️ **Orthotect Native Core** (Pre-commit / CI gate / Subagent feedback loop) |
| **Layer 2: Dynamic Browser & Runtime Audit** | axe-core, Playwright, Chrome DevTools, XState | Live ARIA tree calculation, dynamic color contrast across complex background filters, focus management, end-to-end user journeys | 🤝 **Complements Layer 1** (Recommended companion in dynamic CI pipelines) |

> [!NOTE]
> **Deterministic AST Scope**: Orthotect's static gates verify structural invariants (such as physical vs. logical CSS properties across CSS/JSX/TSX, lexical token compliance, FSM definition validity, and explicit image dimensions) before deployment. 100% logical property compliance and contrast metrics apply to Orthotect's audited core showcase and verified test fixtures; arbitrary legacy codebases should be audited iteratively. For comprehensive accessibility audits covering computed runtime styles, screen reader virtual buffers, and complex DOM tree computations, we recommend pairing Orthotect with dynamic evaluation tools like `axe-core`, `Playwright`, and `Style Dictionary`.

---

## 🚀 Quick Start

Initialize Orthotect into your repository:

```bash
# Copies tokens, FSM models, and AGENTS.md rulebook into current directory
npx orthotect init .

# Compile W3C DTCG tokens into pure CSS Custom Properties (:root & dark theme)
npx orthotect compile core/tokens --out styles/tokens.css
```

Run independent unit and E2E test suite:

```bash
npm test
```

---

## 🤖 Agentic Engineering & Multi-Agent Orchestration

Orthotect is built specifically to transition coding agents from unconstrained "vibe coding" into disciplined **Agentic Engineering**. It provides the deterministic harness that binds autonomous agents (Antigravity, Claude Code, Cursor Agent, OpenAI Codex, Grok Build, OpenCode) to mathematical rigor and zero-defect delivery.

### 🏛️ Orchestration Model: Command → Agent → Skill

```
┌────────────────────────────────────────────────────────┐
│  1. COMMANDS (Entry Points)                            │
│  npx orthotect verify | init | compile | doctor        │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│  2. AGENTS (Autonomous Implementers & Auditors)        │
│  Antigravity · Claude Code · Cursor · Codex · Grok     │
│  Lifecycle: Research ──> Plan ──> Execute ──> Review   │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│  3. SKILLS (Domain Knowledge & State Machines)         │
│  18 Modular Skills in skills/*/SKILL.md                │
│  DTCG Tokens · FSM Schemas · Logical Properties · CRO  │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│  4. DETERMINISTIC RUNTIME GATES                        │
│  WCAG 2.2 AAA Contrast · BiDi · FSM · Slop · DOM CLS   │
│  Exit 0 = Land & Ship  |  Exit 1 = Halt & Fix Line     │
└────────────────────────────────────────────────────────┘
```

- **Command Layer**: Discrete CLI and slash commands gather intent, validate scope boundaries, and invoke tools without contaminating primary context memory.
- **Agent Lifecycle (Research → Plan → Execute → Review → Ship)**:
  - **Research**: Use `core/context_optimizer.py` to extract compact symbol skeletons before reading whole files.
  - **Plan**: Define formal state machines (`button-states.json`, `modal-dialog.json`) and token mappings prior to coding.
  - **Execute**: Author markup strictly referencing CSS Logical Properties and W3C DTCG tokens.
  - **Review & Gate**: Run `python3 gates/run_all_gates.py` in the foreground. Never assert success without real exit code 0 evidence.
  - **Ship**: Commit clean, professional conventional commits with zero conversational metadata.
- **Skill Engine**: 18 certified skills strictly adhering to the Agent Skills Specification (frontmatter with `name`, `description`, `when_to_use`, `argument-hint`, `allowed-tools`, `model`, `effort`, `license`, `compatibility`).
- **Security & Portability**: `scripts/package_skills.py` generates deterministic, byte-for-byte reproducible ZIP archives with symlink boundary containment (`is_relative_to`) and byte-level scanning against private keys and API tokens.

---

## 📜 The 7 Non-Negotiable Laws

Read the complete manifesto in [MANIFESTO.md](MANIFESTO.md).

1. **Verification Protocol:** Never declare a metric or contrast score without running deterministic gates on target files.
2. **Directional Neutrality:** Physical directions (`left`, `right`) are banned; CSS Logical Properties are mandatory.
3. **Mathematical Contrast:** Primary typography and controls must satisfy WCAG 2.2 AAA (7:1) or AA (4.5:1) relative luminance equations.
4. **FSM Completeness:** Every interactive control must implement explicit async states with graph reachability and double-click race condition guards.
5. **Layout Stability:** Media assets must allocate dimensions before render; DOM nesting must not exceed 32 nodes.
6. **Token Purity:** Hardcoded styling values are banned; all properties resolve to W3C DTCG 3-tier tokens.
7. **Anti-Slop:** Banned raw emoji icons in controls, banned generic indigo-purple gradients, zero untokenized styles.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
