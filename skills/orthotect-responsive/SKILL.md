---
name: orthotect-responsive
description: Engineer resilient responsive layouts using CSS Grid, container queries, fluid typography (clamp()), and adaptive bento layouts. Prevents horizontal overflows and layout shifts across viewports from 360px to 2560px.
---

# Skill: Orthotect Responsive & Adaptive Layouts

Use this skill to design responsive layouts that adapt seamlessly from mobile viewports (360px) to ultrawide displays (2560px) without horizontal scrolling or cumulative layout shift.

## Architectural Guidelines
1. **Container Queries Over Media Queries:** Use `@container` for component-level reflow based on container width rather than whole viewport width.
2. **Fluid Typography:** Use `clamp()` for scalable headings:
   `font-size: clamp(1.5rem, 1rem + 2vw, 3rem);`
3. **Intrinsic Grid Sizing:** Avoid fixed pixel widths in grid columns:
   `grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));`
4. **Aspect Ratio Bounding:** Bound all media with `aspect-ratio` to eliminate Cumulative Layout Shift (CLS = 0).

## Anti-Patterns
- Fixed `width: 1200px` causing mobile horizontal scrolling.
- Cluttered navigation menus that overflow viewport boundaries on tablet portrait screens.
- Hiding critical action buttons on mobile instead of adapting their presentation.
