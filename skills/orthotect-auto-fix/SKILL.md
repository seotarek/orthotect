---
name: orthotect-auto-fix
description: Automatically heal and remediate physical CSS coordinates to directional logical properties, correct non-compliant contrast tokens, and inject missing media aspect ratios using Orthotect in-place auto-healing engine. Use when running code fixes with --fix or remediating gate failures.
license: MIT
---

# Skill: Orthotect Auto-Healing & Self-Remediation Engine

Use this skill when encountering quality gate failures or when tasked with automatically repairing legacy codebases to comply with Orthotect's deterministic standards.

## Capabilities of `--fix`
Orthotect includes an in-place AST remediation engine (`core/auto_fix.py`) capable of healing:
1. **Physical CSS Properties to Logical Properties:**
   - `margin-left` -> `margin-inline-start`
   - `margin-right` -> `margin-inline-end`
   - `padding-left` -> `padding-inline-start`
   - `padding-right` -> `padding-inline-end`
   - `border-left` -> `border-inline-start`
   - `border-right` -> `border-inline-end`
   - `border-top-left-radius` -> `border-start-start-radius`
   - `border-bottom-right-radius` -> `border-end-end-radius`
   - `left: 0` -> `inset-inline-start: 0`
   - `right: 0` -> `inset-inline-end: 0`
   - `text-align: left` -> `text-align: start`
   - `float: left` -> `float: inline-start`
2. **JSX / TSX CamelCase Inline Styles:**
   - `marginLeft: 16` -> `marginInlineStart: 16`
   - `paddingRight: '8px'` -> `paddingInlineEnd: '8px'`
3. **Cumulative Layout Shift (CLS) Media Attributes:**
   - Automatically detects unconstrained `<img>` elements and computes missing `width`, `height`, or CSS `aspect-ratio` based on natural image dimensions.

## CLI Invocation
Execute in-place auto-healing across any target directory:
```bash
# Auto-heal all physical properties and layout shifts in project
npx orthotect verify . --fix

# Auto-heal a specific directory or component
npx orthotect verify src/components --fix
```

## Anti-Patterns
- Manually editing dozens of physical coordinates when `--fix` executes deterministically in sub-second time.
- Blindly committing fixes without re-running `npx orthotect verify .` to confirm all 6 gates pass.
