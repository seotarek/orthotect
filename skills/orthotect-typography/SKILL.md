---
name: orthotect-typography
description: Engineer accessible, fluid typography scales with CSS clamp(), high-contrast readable hierarchy, dyslexia-friendly font pairings (Lexend), and variable font weights. Use when configuring typography, type scales, font pairings, or readability standards.
license: MIT
---

# Skill: Orthotect Accessible & Fluid Typography

Use this skill when configuring typographic systems, fluid scales, font pairings, or reading ergonomics.

## Core Typography Principles
1. **Fluid Typography without Breakpoint Jumps:**
   Use mathematical fluid `clamp()` equations from `knowledge/typography/scale.json`:
   ```css
   --ot-font-size-hero: clamp(2.5rem, 1.8rem + 3.5vw, 4.5rem);
   --ot-font-size-h1: clamp(2rem, 1.5rem + 2.5vw, 3.25rem);
   --ot-font-size-body: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
   ```
2. **Clinical Readability & Dyslexia Optimization:**
   For civic, clinical, and high-readability domains, use `Lexend` (hyper-calibrated character spacing for cognitive processing) paired with `Inter` or `Space Grotesk`.
3. **Tabular Numerals for Telemetry & Finance:**
   Always declare `font-variant-numeric: tabular-nums` on metric counters, financial tickers, and tables.
4. **Line-Length Budgets:**
   Paragraph text must never exceed 75 characters per line (`max-inline-size: 68ch`) to maintain reading ergonomics.

## Knowledge Base References
- `knowledge/typography/font-pairings.json`: 12 verified high-contrast font combinations.
- `knowledge/typography/hierarchy.json`: Typographic ratios (Major Second 1.125 to Perfect Fourth 1.333).
- `knowledge/typography/readability.json`: Line-height and letter-spacing formulas.

## Verification
```bash
# Validate typography schemas
python3 core/knowledge_search.py "typography fluid" --category typography
```
