# Orthotect System Doctrine for AI Coding Agents

Orthotect provides deterministic interface engineering rules, DTCG design tokens, and objective quality gates for coding agents (Antigravity, Cursor, Codex, Claude Code, Copilot).

## Mandatory Agent Workflow
1. **Read the Doctrine:** Always consult `skills/orthotect-doctrine/SKILL.md` before generating frontend code.
2. **Apply Directional Neutrality:** Write CSS Logical Properties (`margin-inline-start`, `padding-inline-end`). Never write `left` or `right` margin/padding.
3. **Enforce State Machines:** Interactive components must follow `core/fsm/button-states.json`.
4. **Run the Quality Gates:** Before submitting or declaring work finished, RUN:
   ```bash
   python3 gates/run_all_gates.py
   ```
   Never claim tests passed without running this command and quoting its output.
