---
name: orthotect-fsm
description: Architect interactive UI components as resilient Finite State Machines (FSM) with race condition guards, double-submission locks, and optimistic updates. Use when managing complex UI states or async flows.
---

# Skill: Orthotect FSM Engineering

Use this skill when building forms, action buttons, data tables, or async components to ensure rock-solid state management.

## Guidelines
1. **Declare States Explicitly:** Never rely on a single boolean `isLoading`. Use explicit status enums:
   `type Status = 'idle' | 'loading' | 'success' | 'error' | 'disabled';`
2. **Prevent Double-Submission:** During `loading`, disable pointer events and keyboard triggers while maintaining full visual contrast.
3. **Optimistic Updates:** If performing optimistic updates, always preserve a rollback snapshot to restore if the network fails.
4. **Accessible Announcers:** Use `aria-live="polite"` to announce state changes (e.g., "Deploying service...", "Service deployed successfully").

## Verification
Run:
`python3 gates/gate_fsm_integrity.py`
