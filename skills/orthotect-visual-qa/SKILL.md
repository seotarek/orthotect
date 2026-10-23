---
name: orthotect-visual-qa
description: Execute automated browser visual regression, color contrast, and layout shift verification using Playwright. Use when verifying rendered UI, validating theme switching, or checking that light and dark modes have zero visual clashes.
---

# Skill: Orthotect Visual QA & Automated Browser Verification

Use this skill to execute deterministic browser-based visual QA, verify rendered computed styles, test theme reactivity, and catch visual regressions before shipping code.

## Verification Protocol
1. **Computed Style Auditing:** Never guess contrast from CSS files alone. Verify rendered contrast via `getComputedStyle(element).color` and `backgroundColor`.
2. **Dual-Theme Verification:** Test both `data-theme="dark"` and `data-theme="light"`. Light mode must never render dark text on dark surfaces or white bars through dark components.
3. **Reactive Synchronization:** When toggling themes, verify that subordinate viewports (playgrounds, terminals, toolbars, wordmarks) synchronize immediately.
4. **Cumulative Layout Shift (CLS):** Verify CLS stays under 0.05 during font and media asset loading.

## Automated Commands
```bash
# Run browser regression tests
python3 -m unittest tests/test_docs_browser.py

# Run all unit and browser tests
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Anti-Patterns
- Assuming a component looks good without rendering in headless Chromium.
- Inverting dark colors without testing contrast on secondary labels and borders.
- Disabling outline rings on focused elements during mouse clicks.
