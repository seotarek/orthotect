---
name: orthotect-motion
description: Design physically grounded UI motion using Orthotect spring physics tokens, choreographed staggered reveals, and mandatory @media (prefers-reduced-motion) overrides. Use when implementing high-performance animations.
---

# Skill: Orthotect Spring Physics Motion & Animation

Use this skill to implement polished micro-interactions, modal transitions, and dashboard data streaming animations.

## Spring Physics Tokens
- `--ot-motion-snappy`: `150ms cubic-bezier(0.16, 1, 0.3, 1)` (Tactile button presses, checkboxes, toggles).
- `--ot-motion-expressive`: `300ms cubic-bezier(0.34, 1.56, 0.64, 1)` (Modal dialog entry, drawer reveal, toast notification).

## The Non-Negotiable Motion Rules
1. **GPU Acceleration Only:** Animate strictly `transform` and `opacity`. Never animate `width`, `height`, `top`, or `margin`.
2. **Reduced Motion Law:** Every animation must include a `@media (prefers-reduced-motion: reduce)` override collapsing transition times to 0ms or simple opacity cross-fade.
3. **Duration Budget:** Never exceed 400ms for everyday UI transitions.

## Verification
```bash
python3 gates/gate_no_slop.py <path>
```
