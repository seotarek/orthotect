# 🏛️ Orthotect

### The Deterministic Interface Engineering & Runtime Gate Architecture for AI Coding Agents

[![Version](https://img.shields.io/badge/version-1.5.2-6366f1?style=for-the-badge)](https://github.com/seotarek/orthotect/releases/tag/v1.5.2)
[![Live Showcase](https://img.shields.io/badge/Live_Showcase-GitHub_Pages-0ea5e9?style=for-the-badge)](https://seotarek.github.io/orthotect/)
[![CI Status](https://github.com/seotarek/orthotect/actions/workflows/ci.yml/badge.svg)](https://github.com/seotarek/orthotect/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)
[![WCAG 2.2 Contrast Matrix](https://img.shields.io/badge/WCAG_2.2-Contrast_Matrix_(AA%2FAAA)-a855f7?style=for-the-badge)](#)
[![Gates: 100% Deterministic](https://img.shields.io/badge/Quality_Gates-Deterministic-14b8a6?style=for-the-badge)](#)
[![BiDi: 100% Logical](https://img.shields.io/badge/BiDi-True_RTL/LTR-f97316?style=for-the-badge)](#)

> **Live Interactive Showcase & Playground:** [https://seotarek.github.io/orthotect/](https://seotarek.github.io/orthotect/)  
> **Engineering Whitepapers:** [Competitor Teardown (COMPETITORS.md)](COMPETITORS.md) | [The 7 Laws Manifesto (MANIFESTO.md)](MANIFESTO.md)

Orthotect is an enterprise-grade interface engineering kit built to enforce **Google-caliber architectural rigor** onto autonomous coding agents (Antigravity, Cursor, Claude Code, Codex, Grok). 

Unlike superficial prompt libraries that merely request "good design", Orthotect provides a **mathematical token foundation**, **Finite State Machine (FSM) graph reachability**, and **objective quality gates** that fail the build with `exit 1` if standards are breached.

---

## ⚡ Why Orthotect Outperforms Competitors

For an exhaustive technical breakdown, read our [Architectural Teardown Whitepaper](COMPETITORS.md).

| Feature | Competitor Toolkits (e.g. XIAS / taste-skill) | Component Libraries (e.g. shadcn/ui) | 🏛️ Orthotect Architecture (Google-Scale) |
|---|---|---|---|
| **CLI Verification** | Runs gates only on package internal fixtures | Manual visual testing / storybook | **Target-Aware & Zero-Fallback:** Inspects user project directory (`orthotect verify <dir>`) with strict path boundaries and real exit codes |
| **CLI Initialization** | Simulated console messages | Code copy-pasting | **Real File Scaffolding:** Copies tokens, FSM specs, and `AGENTS.md` directly into target repository (`orthotect init <dir>`) |
| **State Engineering** | Static UI snapshots (Hover/Active) | Ad-hoc `isLoading` boolean flags | **Finite State Machines (FSM)** with graph reachability, double-submission race locks & async recovery |
| **BiDi / RTL Support** | Superficial `dir="rtl"` attribute | Physical classes (`ml-*`, `pr-*`) | **100% CSS Logical Properties** (`margin-inline`, `padding-inline`, `border-inline`, `inset-inline`) |
| **Layout Shift Budget** | None or unverified assertions | Dependent on developer discipline | **Structural Layout-Shift (CLS) Budget** enforcing reserved media dimensions (`width` + `height` or `aspect-ratio`) and stream-based DOM nesting limits |
| **Motion Engineering** | Generic `0.2s ease` transitions | Hardcoded keyframes | **Spring Physics Curves** (Stiffness, Damping, Mass) |
| **Cognitive Ergonomics** | Arbitrary card layouts | Component presets | **Fitts' Law** touch targets (≥44px) & **Miller's 7±2 Law** density constraints |
| **Slop Prevention** | Subjective guidelines | None | **Lexical & Pattern Inspectors** that reject AI indigo-purple gradients, raw emoji icons, and untokenized styles |
| **Design Tokens** | Inconsistent CSS variables | Custom Tailwind theme | **W3C DTCG 3-Tier Compiler** generating `:root` light and `[data-theme="dark"]` scopes |

---

## 🏗️ Architecture Overview

```text
orthotect/
├── core/
│   ├── compiler.py      # W3C DTCG Token Compiler (:root light and [data-theme="dark"])
│   ├── tokens/          # W3C DTCG 3-Tier Design Tokens (Primitives, Semantics, Motion, Ergonomics)
│   └── fsm/             # State Machine Specifications (Buttons, Data Tables, Modal Dialogs)
├── docs/                # 7-View Skill Studio Platform & Interactive Showcase (GitHub Pages)
│   ├── index.html       # 7-view bilingual (EN/AR) interactive workbench
│   ├── styles.css       # 100% CSS Logical Properties & DTCG token variables
│   └── app.js           # Client-side router, catalog, playground, builder, and gate simulator
├── gates/               # Objective Deterministic Checkers (Python & Node.js)
│   ├── gate_contrast_wcag.py     # Mathematical Relative Luminance (WCAG 2.2 AAA/AA)
│   ├── gate_bidi_logical.py      # Strict Enforcement of CSS Logical Properties
│   ├── gate_fsm_integrity.py     # State Machine Graph Reachability & Lock Integrity
│   ├── gate_no_slop.py           # Lexical & Pattern Slop Inspector
│   ├── gate_cwv_budget.mjs       # WHATWG-Compliant DOM & Layout-Shift Budget
│   └── run_all_gates.py          # Parallel Master Gate Orchestrator (ThreadPoolExecutor)
├── skills/              # Agent Skills (Progressive Disclosure)
│   ├── orthotect-doctrine        # The 7 Non-Negotiable Laws
│   ├── orthotect-fsm             # State Machine Implementation Workflows
│   ├── orthotect-tokens          # Token Management & Theme Compilation
│   ├── orthotect-bidi            # Directional Neutrality & RTL Engineering
│   ├── orthotect-dashboard       # High-Density Console Design
│   └── orthotect-gates           # Gate Execution Workflows
├── tests/               # Comprehensive Unit, Browser & Negative Test Suite (108 Tests)
│   ├── test_contrast.py          # Relative luminance & contrast threshold unit tests
│   ├── test_bidi.py              # BiDi logical scanner positive/negative tests
│   ├── test_fsm.py               # FSM graph reachability and deadlock tests
│   ├── test_core_sync.py         # Canonical FSM schemas & DTCG tokens single-source-of-truth tests
│   ├── test_cwv.py               # Media dimension, aspect-ratio & iterative parse5 DOM depth tests
│   ├── test_slop.py              # AI purple gradient & raw emoji anti-pattern tests
│   ├── test_compiler.py          # W3C DTCG CSS custom property compiler tests
│   ├── test_skills_sync.py       # Skills directory / docs/app.js catalog sync tests
│   ├── test_docs_browser.py      # Playwright 7-view Skill Studio browser integration & negative benchmark tests
│   ├── test_modal_browser.py     # Playwright headless Chrome focus trap & FSM tests
│   └── test_cli_e2e.py           # E2E CLI verification, boundary & negative rejection tests
├── .github/workflows/   # Automated CI & GitHub Pages Deployment Pipelines
│   ├── ci.yml                    # 108 Unit, Browser & Negative Gate Tests & Full Gate Verification
│   └── pages.yml                 # Automated GitHub Pages Deployment
├── agents/
│   └── orthotect-auditor.md      # Adversarial Quality Auditor Role
├── CHANGELOG.md         # Full version history (v1.0.0 → v1.5.1)
├── CONTRIBUTING.md      # Enterprise engineering guidelines
├── COMPETITORS.md       # Exhaustive architectural competitor teardown
├── MANIFESTO.md         # The 7 Laws of Interface Engineering
└── examples/
    └── golden-showcase/          # Reference Enterprise Console passing 100% of gates
```

---

## 🚦 Deterministic Quality Gates

Run the verification suite against your project:

```bash
# Verify current project
npx orthotect verify .

# Or verify with automated reporting
npx orthotect verify ./src --json
npx orthotect verify ./src --md
```

Illustrative Reference Verification Output (Target: `examples/golden-showcase`):
> *Note: Parallel gate execution latencies are measured dynamically per run and scale with repository size and host hardware (typically 120ms – 590ms; latest GitHub Actions CI run executed in ~126ms).*

```text
╔═══════════════════════════════════════════════════════════════╗
║            ORTHOTECT DETERMINISTIC QUALITY GATES              ║
║         Google-Scale Interface Engineering Protocol           ║
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

🎉 ALL GATES PASSED! Build certified for enterprise production.
```

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
