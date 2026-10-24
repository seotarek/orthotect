---
name: orthotect-fsm
description: Architect interactive UI components as resilient Finite State Machines (FSM) with race condition guards, double-submission locks, and optimistic updates. Use when managing complex UI states or async flows.
---

# Skill: Orthotect FSM Engineering

Use this skill when building forms, action buttons, data tables, or async components to ensure rock-solid state management.

## Canonical State Models (`core/fsm/`)
Reference these validated JSON schemas when building interactive flows:
- `core/fsm/button-states.json`: Idle -> Loading (`allowClick: false`) -> Success / Error -> Idle timeout.
- `core/fsm/modal-dialog.json`: Closed -> Opening -> Open (focus trapped) -> Closing -> Closed.
- `core/fsm/data-table-loader.json`: Empty -> Fetching -> Ready / Error (with Retry transition).
- `core/fsm/multi-step-wizard.json`: Step 1 -> Validating -> Step 2 -> Submitting -> Completed.

## Architectural Rules
1. **Async Interaction Locks:** Any state performing async work must explicitly declare `"allowClick": false` or `"locksInteraction": true` to block re-triggering.
2. **Error Recovery Transitions:** Error states must never be terminal deadlocks; they must provide explicit retry or dismiss transitions back to an active state.
3. **Graph Reachability:** All states defined in `states` must be reachable via BFS traversal from `initialState`.

## Verification
Run deterministic state machine verification:
```bash
python3 gates/gate_fsm_integrity.py examples/golden-showcase
```
