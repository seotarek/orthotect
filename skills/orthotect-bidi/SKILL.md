---
name: orthotect-bidi
description: Engineer true bidirectional interfaces with flawless Arabic/English RTL/LTR symmetry using CSS logical properties and directional vector isolation.
---

# Skill: Orthotect True BiDi Engineering

Build interfaces that look and feel completely native in both Arabic (RTL) and English (LTR).

## Logical Replacement Table
| Physical Property (BANNED) | Logical Property (MANDATORY) |
|---|---|
| `margin-left: 1rem` | `margin-inline-start: 1rem` |
| `margin-right: 1rem` | `margin-inline-end: 1rem` |
| `padding-left: 0.5rem` | `padding-inline-start: 0.5rem` |
| `padding-right: 0.5rem` | `padding-inline-end: 0.5rem` |
| `left: 0` | `inset-inline-start: 0` |
| `right: 0` | `inset-inline-end: 0` |
| `text-align: left` | `text-align: start` |
| `text-align: right` | `text-align: end` |

## Directional Icons & Vectors
- Back/Forward arrows MUST mirror in RTL: `[dir="rtl"] .icon-directional { transform: scaleX(-1); }`
- Media controls (Play/Pause/Volume) MUST NOT mirror (universal convention).

## Verification
Run:
`python3 gates/gate_bidi_logical.py <path>`
