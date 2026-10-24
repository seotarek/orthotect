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

## Inline SVG Telemetry Patterns
- **Sparklines:** Use `<svg viewBox="0 0 100 24" preserveAspectRatio="none">` with `fill="none" stroke="currentColor" stroke-width="1.5"` and vector-effect `non-scaling-stroke`.
- **Radial Donut Gauges:** Calculate stroke-dasharray and stroke-dashoffset via mathematical circumferences (`2 * π * r`), reserving a square container with CSS `aspect-ratio: 1`.
- **Bid/Ask Depth Curves:** Area paths must close cleanly at the baseline (`V 100 H 0 Z`) to avoid rendering artifacts across themes.

## Verification
```bash
node gates/gate_cwv_budget.mjs examples/golden-showcase
```
