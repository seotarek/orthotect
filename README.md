# 🏛️ Orthotect

### The Deterministic Interface Engineering & Runtime Gate Architecture for AI Coding Agents

[![Version](https://img.shields.io/badge/version-1.0.0-6366f1?style=for-the-badge)](https://github.com/orthotect/orthotect)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](#license)
[![WCAG 2.2 AAA/AA](https://img.shields.io/badge/WCAG-2.2_AAA→AA-a855f7?style=for-the-badge)](#)
[![Gates: 100% Deterministic](https://img.shields.io/badge/Quality_Gates-Deterministic-14b8a6?style=for-the-badge)](#)
[![BiDi: 100% Logical](https://img.shields.io/badge/BiDi-True_RTL/LTR-f97316?style=for-the-badge)](#)

Orthotect is an enterprise-grade interface engineering kit built to enforce **Google-caliber architectural rigor** onto autonomous coding agents (Antigravity, Cursor, Claude Code, Codex). 

Unlike superficial prompt libraries that merely request "good design", Orthotect provides a **mathematical token foundation**, **Finite State Machine (FSM) resilience**, and **objective quality gates** that fail the build with exit code 1 if standards are breached.

---

## ⚡ Why Orthotect Outperforms Competitors

| Feature | Competitor Toolkits (e.g. XIAS / taste-skill) | 🏛️ Orthotect Architecture |
|---|---|---|
| **State Engineering** | Static UI snapshots (Hover/Active) | **Finite State Machines (FSM)** with double-submission locks & optimistic rollbacks |
| **BiDi / RTL Support** | Superficial `dir="rtl"` attribute | **100% CSS Logical Properties** (`margin-inline`, `inset-inline`) with zero layout bugs |
| **Performance Budgets** | Visual-only review | **Core Web Vitals Budgets** (CLS layout-shift prevention, DOM depth limits) |
| **Motion Engineering** | Generic `0.2s ease` transitions | **Spring Physics Curves** (Stiffness, Damping, Mass) |
| **Cognitive Ergonomics** | Arbitrary card layouts | **Fitts' Law** touch targets (≥44px) & **Miller's 7±2 Law** density constraints |
| **Slop Prevention** | Subjective guidelines | **Deterministic AST & Regex Gates** that reject AI indigo-purple gradients and emojis |

---

## 🏗️ Architecture Overview

```text
orthotect/
├── core/
│   ├── tokens/          # W3C DTCG 3-Tier Design Tokens (Primitives, Semantics, Motion, Ergonomics)
│   └── fsm/             # State Machine Specifications for Buttons, Tables, and Forms
├── gates/               # Objective Deterministic Checkers (Python & Node.js)
│   ├── gate_contrast_wcag.py     # Mathematical Relative Luminance (WCAG 2.2 AAA/AA)
│   ├── gate_bidi_logical.py      # Strict Enforcement of CSS Logical Properties
│   ├── gate_fsm_integrity.py     # State Machine Deadlock & Transition Verifier
│   ├── gate_no_slop.py           # AST Detector for AI Anti-Patterns
│   ├── gate_cwv_budget.mjs       # Core Web Vitals Structural Budget Verifier
│   └── run_all_gates.py          # Master Gate Orchestrator
├── skills/              # Agent Skills (Progressive Disclosure)
│   ├── orthotect-doctrine        # The 7 Non-Negotiable Laws
│   ├── orthotect-fsm             # State Machine Implementation Workflows
│   ├── orthotect-tokens          # Token Management & Theme Compilation
│   ├── orthotect-bidi            # Directional Neutrality & RTL Engineering
│   ├── orthotect-dashboard       # High-Density Console Design
│   └── orthotect-gates           # Gate Execution Workflows
├── agents/
│   └── orthotect-auditor.md      # Adversarial Quality Auditor Role
└── examples/
    └── golden-showcase/          # Reference Enterprise Console passing 100% of gates
```

---

## 🚦 Deterministic Quality Gates

Run the verification suite in one command:

```bash
python3 gates/run_all_gates.py
```

Output:
```text
╔═══════════════════════════════════════════════════════════════╗
║            ORTHOTECT DETERMINISTIC QUALITY GATES              ║
║         Google-Scale Interface Engineering Protocol           ║
╚═══════════════════════════════════════════════════════════════╝

GATE NAME                              STATUS           TIME
───────────────────────────────────────────────────────────────
WCAG 2.2 Mathematical Contrast         ✅ PASS        14.2ms
True BiDi & Logical Properties         ✅ PASS         8.6ms
Finite State Machine Integrity         ✅ PASS         5.1ms
Anti-Slop Architectural Guardian       ✅ PASS         9.4ms
Core Web Vitals Structural Budget      ✅ PASS        22.8ms
───────────────────────────────────────────────────────────────
Total Verification Time: 60.1ms

🎉 ALL GATES PASSED! Build certified for enterprise production.
```

---

## 🚀 Quick Start

Initialize Orthotect in any frontend repository:

```bash
npx orthotect init
```

Verify your project against all gates:

```bash
npx orthotect verify
```

---

## 📜 The 7 Non-Negotiable Laws

1. **Verification Protocol:** Never declare a metric or contrast score without running deterministic gates.
2. **Directional Neutrality:** Physical directions (`left`, `right`) are banned; CSS Logical Properties are mandatory.
3. **FSM Completeness:** Every interactive control must implement explicit async states.
4. **Spring Physics:** Motion must use calibrated mass, damping, and stiffness springs.
5. **Strict Intent Tokens:** Actions must map strictly to their semantic intent tokens.
6. **Cognitive Ergonomics:** Respect Fitts' Law and Miller's 7±2 Information Density limits.
7. **Zero AI Slop:** Banned raw emoji icons, banned generic indigo-purple gradients, zero untokenized styles.

---

## 📄 License

Distributed under the **MIT License**.
