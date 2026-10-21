# 🏛️ Orthotect

### The Deterministic Interface Engineering & Runtime Gate Architecture for AI Coding Agents

[![Version](https://img.shields.io/badge/version-1.2.0-6366f1?style=for-the-badge)](https://github.com/seotarek/orthotect/releases/tag/v1.2.0)
[![CI Status](https://github.com/seotarek/orthotect/actions/workflows/ci.yml/badge.svg)](https://github.com/seotarek/orthotect/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)
[![WCAG 2.2 AAA/AA](https://img.shields.io/badge/WCAG-2.2_AAA→AA-a855f7?style=for-the-badge)](#)
[![Gates: 100% Deterministic](https://img.shields.io/badge/Quality_Gates-Deterministic-14b8a6?style=for-the-badge)](#)
[![BiDi: 100% Logical](https://img.shields.io/badge/BiDi-True_RTL/LTR-f97316?style=for-the-badge)](#)

Orthotect is an enterprise-grade interface engineering kit built to enforce **Google-caliber architectural rigor** onto autonomous coding agents (Antigravity, Cursor, Claude Code, Codex). 

Unlike superficial prompt libraries that merely request "good design", Orthotect provides a **mathematical token foundation**, **Finite State Machine (FSM) graph reachability**, and **objective quality gates** that fail the build with exit code 1 if standards are breached.

---

## ⚡ Why Orthotect Outperforms Competitors

| Feature | Competitor Toolkits (e.g. XIAS / taste-skill) | 🏛️ Orthotect Architecture |
|---|---|---|
| **CLI Verification** | Runs gates only on package internal fixtures | **Target-Aware & Zero-Fallback:** Inspects user project directory (`orthotect verify <dir>`) with strict path boundaries and real exit codes |
| **CLI Initialization** | Simulated console messages | **Real File Scaffolding:** Copies tokens, FSM specs, and `AGENTS.md` directly into target repository |
| **State Engineering** | Static UI snapshots (Hover/Active) | **Finite State Machines (FSM)** with graph reachability, double-submission locks & async error recovery |
| **BiDi / RTL Support** | Superficial `dir="rtl"` attribute | **100% CSS Logical Properties** (`margin-inline`, `padding-inline`, `border-inline`, `inset-inline`) |
| **Layout Shift Budget** | None or unverified assertions | **Structural Layout-Shift (CLS) Budget** enforcing reserved media dimensions (`width` + `height` or `aspect-ratio`) and stream-based DOM nesting limits |
| **Motion Engineering** | Generic `0.2s ease` transitions | **Spring Physics Curves** (Stiffness, Damping, Mass) |
| **Cognitive Ergonomics** | Arbitrary card layouts | **Fitts' Law** touch targets (≥44px) & **Miller's 7±2 Law** density constraints |
| **Slop Prevention** | Subjective guidelines | **Lexical & Pattern Inspectors** that reject AI indigo-purple gradients, raw emoji icons, and untokenized styles |

---

## 🏗️ Architecture Overview

```text
orthotect/
├── core/
│   ├── compiler.py      # W3C DTCG Token Compiler (:root light and [data-theme="dark"])
│   ├── tokens/          # W3C DTCG 3-Tier Design Tokens (Primitives, Semantics, Motion, Ergonomics)
│   └── fsm/             # State Machine Specifications (Buttons, Data Tables, Modal Dialogs)
├── gates/               # Objective Deterministic Checkers (Python & Node.js)
│   ├── gate_contrast_wcag.py     # Mathematical Relative Luminance (WCAG 2.2 AAA/AA)
│   ├── gate_bidi_logical.py      # Strict Enforcement of CSS Logical Properties
│   ├── gate_fsm_integrity.py     # State Machine Graph Reachability & Lock Integrity
│   ├── gate_no_slop.py           # Lexical & Pattern Slop Inspector
│   ├── gate_cwv_budget.mjs       # DOM & Layout-Shift (CLS) Structural Budget
│   └── run_all_gates.py          # Parallel Master Gate Orchestrator (ThreadPoolExecutor)
├── skills/              # Agent Skills (Progressive Disclosure)
│   ├── orthotect-doctrine        # The 7 Non-Negotiable Laws
│   ├── orthotect-fsm             # State Machine Implementation Workflows
│   ├── orthotect-tokens          # Token Management & Theme Compilation
│   ├── orthotect-bidi            # Directional Neutrality & RTL Engineering
│   ├── orthotect-dashboard       # High-Density Console Design
│   └── orthotect-gates           # Gate Execution Workflows
├── tests/               # Comprehensive Unit & Integration Test Suite (39 Tests)
│   ├── test_contrast.py          # Relative luminance & contrast threshold unit tests
│   ├── test_bidi.py              # BiDi logical scanner positive/negative tests
│   ├── test_fsm.py               # FSM graph reachability and deadlock tests
│   ├── test_cwv.py               # Media dimension, aspect-ratio & minified HTML DOM depth tests
│   ├── test_slop.py              # AI purple gradient & raw emoji anti-pattern tests
│   ├── test_compiler.py          # W3C DTCG CSS custom property compiler tests
│   └── test_cli_e2e.py           # E2E CLI verification, boundary & negative rejection tests
├── .github/workflows/   # Automated CI Pipeline
│   └── ci.yml
├── agents/
│   └── orthotect-auditor.md      # Adversarial Quality Auditor Role
├── CHANGELOG.md         # Full version history (v1.0.0 → v1.2.0)
├── CONTRIBUTING.md      # Enterprise engineering guidelines
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

Output:
```text
╔═══════════════════════════════════════════════════════════════╗
║            ORTHOTECT DETERMINISTIC QUALITY GATES              ║
║         Google-Scale Interface Engineering Protocol           ║
╚═══════════════════════════════════════════════════════════════╝
 Target Path: /your/project/path

GATE NAME                              STATUS           TIME
───────────────────────────────────────────────────────────────
WCAG 2.2 Mathematical Contrast         ✅ PASS        116.7ms
True BiDi & Logical Properties         ✅ PASS         82.7ms
Finite State Machine Integrity         ✅ PASS         61.0ms
Anti-Slop Pattern Inspector            ✅ PASS         95.1ms
DOM & Layout-Shift Budget              ✅ PASS        334.1ms
───────────────────────────────────────────────────────────────
Total Verification Time (Parallel): 339.5ms

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

1. **Verification Protocol:** Never declare a metric or contrast score without running deterministic gates on target files.
2. **Directional Neutrality:** Physical directions (`left`, `right`) are banned; CSS Logical Properties are mandatory.
3. **FSM Completeness:** Every interactive control must implement explicit async states with graph reachability.
4. **Spring Physics:** Motion must use calibrated mass, damping, and stiffness springs.
5. **Strict Intent Tokens:** Actions must map strictly to their semantic intent tokens.
6. **Cognitive Ergonomics:** Respect Fitts' Law (min 44px touch) and Miller's 7±2 Information Density limits.
7. **Zero AI Slop:** Banned raw emoji icons in controls, banned generic indigo-purple gradients, zero untokenized styles.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
