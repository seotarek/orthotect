---
name: orthotect-data-viz
description: Build high-density, accessible data visualizations, sparklines, telemetry charts, and operational metrics using token-driven SVG geometry, tabular numerals, and zero layout shift. Use when building telemetry consoles or dashboards.
---

# Skill: Orthotect Data Visualization & Telemetry Engineering

Use this skill when engineering charts, operational telemetry, sparklines, or dense data matrices.

## Data Visualization Doctrine
1. **Tabular Numerals:** Apply `font-variant-numeric: tabular-nums` to all data cells and chart labels to prevent layout jitter during live updates.
2. **Intent-Driven Chart Tokens:** Use semantic tokens for chart metrics (emerald for normal, amber for warning, red for critical, cyan for secondary telemetry).
3. **Accessible Data Tables:** Every visual chart must provide an accessible alternative (e.g. an accessible table or screen-reader summary using `aria-label`).
4. **Zero Layout Shift:** Chart containers must reserve fixed aspect ratios or bounding boxes before data loads.

## Verification
```bash
python3 gates/gate_cwv_budget.mjs examples/golden-showcase
```
