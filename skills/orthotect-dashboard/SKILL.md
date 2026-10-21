---
name: orthotect-dashboard
description: Build high-density, cognitive-ergonomic enterprise dashboards and consoles with inline SVG telemetry and zero layout shift.
---

# Skill: Orthotect Enterprise Dashboard Architecture

Build telemetry screens, trading desks, and cloud consoles following Google Cloud and Linear ergonomics:

## Rules
1. **One Hero Figure Leads:** One primary metric rendered at 2.5x to 3x body scale.
2. **Asymmetric Bento Layout:** Breakdowns must vary in aspect ratio and shape (bar chart, sparkline, donut, sortable table). Never render 4 identical square cards.
3. **Inline SVG Visualizations:** Draw charts directly from tokens using inline SVG math; zero external heavy chart libraries.
4. **Reserved Dimensions:** Every chart container must have an explicit height and aspect-ratio to achieve 0.00 CLS (Cumulative Layout Shift).
