# Orthotect System Doctrine for AI Coding Agents

Orthotect provides deterministic interface engineering rules, W3C DTCG design tokens, and objective AST runtime quality gates for autonomous coding agents (Antigravity, Claude Code, Cursor Agent, Codex, Grok, OpenCode).

---

## 🏛️ 1. Orchestration Architecture: Command → Agent → Skill

Autonomous work in this codebase adheres to the structured three-tier orchestration model:
- **Commands (Entry Points)**: Scoped CLI commands (`bin/orthotect.js` or slash commands) that validate arguments, inspect paths, and invoke agents without polluting the primary context window.
- **Agents (Autonomous Workers)**: Specialized execution roles with explicit tool allowlists, bounded iteration limits, and isolated workspaces or subagent sessions.
- **Skills (Domain Capabilities)**: Modular specifications in `skills/*/SKILL.md` that enforce deterministic constraints, semantic token bindings, and state machine graphs.

---

## 🔄 2. Mandatory Engineering Lifecycle: Research → Plan → Execute → Review → Ship

All agents operating in or on Orthotect must follow this five-stage progression:

```
[ Research ] ──> [ Plan ] ──> [ Execute ] ──> [ Review & Gate ] ──> [ Ship ]
  Inspect         Draft FSM &     Pure Logical    Run Parallel       Clean Git
  Tokens & AST    Token Spec      Properties      Deterministic      Conventional
  Context Skeletons               & DTCG Tokens   Gates (exit 0)     Commit
```

1. **Research (Zero-Scan Start)**:
   - Avoid bulk-reading whole directories. Use `core/context_optimizer.py` symbol skeletons and targeted file views to preserve context window budget.
   - Inspect existing token bindings in `core/tokens/` and canonical state machines in `core/fsm/`.
2. **Plan (Spec & FSM First)**:
   - Identify interactive states (idle, hover, active, focus-visible, loading, disabled, error, success).
   - Formulate explicit FSM transition graphs with double-submission locks before generating markup or handlers.
3. **Execute (Deterministic Implementation)**:
   - Enforce 100% CSS Logical Properties (`margin-inline`, `padding-inline`, `inset-inline`, `border-inline`).
   - Reference W3C DTCG semantic tokens (`var(--ot-color-...)`, `var(--ot-space-...)`). Never hardcode hex values or physical pixel offsets.
4. **Review & Gate (Evidence Before Assertions)**:
   - Execute the deterministic quality gates in the foreground:
     ```bash
     python3 gates/run_all_gates.py docs
     python3 gates/run_all_gates.py examples/golden-showcase
     npm test
     ```
   - Inspect the actual exit code (`exit 0`). Never claim gates passed without quoting real command output.
5. **Ship (Hygiene & Privacy)**:
   - Commit directly using standard Conventional Commits format (`feat:`, `fix:`, `docs:`, `chore:`).
   - Maintain strict confidentiality and privacy: never commit conversational commentary, chat transcripts, internal prompts, or secrets to git history.

---

## 📜 3. The 7 Non-Negotiable Laws of Interface Engineering

1. **Verification Protocol**: Never declare a metric, contrast score, or pass claim without executing deterministic gates on actual files.
2. **Directional Neutrality**: Physical coordinates (`left`, `right`, `margin-left`, `padding-right`, `float`) are banned. Modern CSS Logical Properties are mandatory.
3. **Mathematical Contrast**: Primary typography and interactive elements must satisfy WCAG 2.2 AAA (7:1) or AA (4.5:1) relative luminance equations across both light and dark themes.
4. **FSM Completeness**: Every interactive control must implement explicit async states with graph reachability and double-submission race condition guards (`core/fsm/`).
5. **Layout Stability**: Media assets must allocate dimensions before render (`width` + `height` or `aspect-ratio`); DOM nesting depth must not exceed 32 nodes.
6. **Token Purity**: Zero hardcoded hex colors or arbitrary values; all properties resolve to W3C DTCG 3-tier tokens (`:root` light and `[data-theme="dark"]`).
7. **Anti-Slop Defense**: Zero AI indigo-purple gradients, zero raw emoji controls, zero untokenized styles.

---

## 🔒 4. Privacy, Discretion & Git Hygiene

- **Clean Commits**: Commit messages must remain purely technical, descriptive, and professional.
- **Zero Chat Leakage**: Do not commit conversation transcripts, user instructions, personal discussions, or temporary scratch transcripts to repository branches or documentation.
- **No Credentials**: Never stage or package `.env`, private keys, SSH keys, or API tokens (`ghp_`, `AKIA`, `sk-`). All skill packages are scanned by `scripts/package_skills.py` with fail-closed security guards.
