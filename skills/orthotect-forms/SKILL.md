---
name: orthotect-forms
description: Engineer resilient forms with double-submission locks, asynchronous validation FSMs, inline error feedback, accessible field labels, and optimistic state recovery. Use when building login, checkout, settings, or multi-step wizard forms.
---

# Skill: Orthotect Resilient Form Engineering

Use this skill when building forms, checkout flows, settings panels, or multi-step input wizards.

## Form FSM State Machine
Forms must cycle through explicit states:
`pristine` → `editing` → `validating` → `submitting` → `successFeedback` / `submissionError`.

## Mandatory Engineering Rules
1. **Double-Submission Lock:** Immediately disable submit buttons on click; ignore duplicate click/enter events until resolution.
2. **Persistent Field Labels:** Never rely on placeholder text as a field label. Always provide `<label for="...">` with visible text.
3. **Dual Error Cues:** Errors must display both a colored indicator and an explicit descriptive error message linked via `aria-describedby`.
4. **Preserve User Input:** Never wipe form data on validation error.

## Verification
```bash
python3 gates/gate_fsm_integrity.py
```
