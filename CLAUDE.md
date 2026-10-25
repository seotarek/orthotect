# CLAUDE.md
# Guidance for Claude Code (claude.ai/code) in the Orthotect Repository

This document establishes operational best practices, architecture constraints, and verification protocols for Claude Code when developing or maintaining Orthotect.

---

## 🏛️ Repository Overview

Orthotect is an enterprise-grade interface engineering platform and deterministic runtime gate architecture for autonomous AI coding agents. It enforces mathematical token contrast, CSS logical properties, formal state machines, and layout-shift budgets via AST-aware runtime gates that fail the build (`exit 1`) if standards are breached.

---

## ⚡ Essential Commands

### Quality Gates & Verification
```bash
# Run all 5 deterministic quality gates in parallel (sub-600ms)
python3 gates/run_all_gates.py docs
python3 gates/run_all_gates.py examples/golden-showcase

# Run the complete test suite (skills validation, 355 unit tests, and 6 gates)
npm test

# Run Python unit tests only
npm run test:unit
# Or: python3 -m unittest discover -s tests -p 'test_*.py'
```

### Skills Specification & Packaging
```bash
# Validate all 22 installed skills against the Agent Skills specification
npm run validate:skills

# Build reproducible, security-scanned ZIP packages with SHA-256 manifest
python3 scripts/package_skills.py --output dist/packages

# Check package metadata consistency between package.json and package-lock.json
npm run check:package-metadata
```

### CLI Tooling
```bash
# Inspect environment and verify target project
bin/orthotect.js doctor
bin/orthotect.js verify ./docs
bin/orthotect.js security ./docs

# Compile W3C DTCG tokens into pure CSS Custom Properties
bin/orthotect.js compile core/tokens --out dist/tokens.css
```

---

## 🏗️ Architectural Patterns: Command → Agent → Skill

1. **Commands (`bin/orthotect.js` / `.claude/commands/`)**:
   - Provide clean, deterministic entry points for developers and agents.
   - Validate target directory arguments and execute sub-tools without polluting conversational memory.
2. **Agents (Autonomous Implementers & Auditors)**:
   - Operate under the 5-phase lifecycle: **Research → Plan → Execute → Review → Ship**.
   - Strictly respect permission modes and bounded iteration turns (`maxTurns`).
3. **Skills (`skills/*/SKILL.md`)**:
   - Discrete, single-purpose interface capabilities adhering to the Agent Skills Specification.
   - Frontmatter defines: `name`, `description`, `when_to_use`, `argument-hint`, `allowed-tools`, `model`, `effort`, `license`, `compatibility`.
   - Progressive disclosure: `SKILL.md` stays lean (<500 lines); deep domain references reside in `references/`.

---

## 🛡️ Critical Invariants & House Rules

1. **Evidence Before Assertions**: Never claim a test, gate, or contrast check passed without running the command in the foreground and confirming its real output and exit code.
2. **Directional Neutrality**: Write CSS Logical Properties (`margin-inline`, `padding-inline`, `inset-inline`, `border-inline`, `text-align: start|end`). Physical `left` and `right` coordinates are strictly banned.
3. **FSM Completeness**: Interactive components must implement explicit async states (idle, hover, active, focus-visible, loading, disabled, error, success) with double-submission race condition locks (`core/fsm/button-states.json`).
4. **Token Purity**: Never hardcode hex colors or arbitrary physical pixels. All visual attributes must resolve to W3C DTCG 3-tier tokens (`core/tokens/`).
5. **Anti-Slop Invariant**: Reject generic AI indigo-purple gradients, raw emoji icons inside button controls, and untokenized inline styles.
6. **Context Optimization**: For large multi-file operations, leverage `core/context_optimizer.py` to extract symbol skeletons and surgical line slices, preserving context window budget.

---

## 🔒 Privacy, Discretion & Git Hygiene

- **Conventional Commits**: Format commit messages strictly as standard conventional commits (e.g., `feat:`, `fix:`, `docs:`, `chore:`).
- **Confidentiality**: Never commit conversational transcripts, personal user instructions, internal scratch files, or private tokens to the repository.
- **Fail-Closed Security**: `scripts/package_skills.py` strictly prevents symlink directory traversal (`is_relative_to`) and scans file bytes for private keys, SSH keys, and API tokens. Maintain this defense.

