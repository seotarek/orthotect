# Call-To-Action (CTA) Hierarchy & Visual Prominence

A high-converting interface directs user attention decisively toward the primary business objective while accommodating secondary exploration paths.

## 1. Visual Weight Hierarchy
Every view must have exactly one dominant CTA. Competing visual elements dilute action rates.

| Level | Visual Treatment | DTCG Token Mapping | Usage |
|---|---|---|---|
| **Primary** | Solid saturated fill, high contrast text | `background: var(--ot-color-primary); color: var(--ot-color-primary-fg);` | Main conversion action ("Start Free Trial", "Deploy Now") |
| **Secondary** | Outlined or subtle background fill | `background: transparent; border: 1px solid var(--ot-border-default); color: var(--ot-fg-default);` | Supporting action ("View Demo", "Read Documentation") |
| **Tertiary** | Text link with chevron or subtle underline | `color: var(--ot-fg-muted); hover: var(--ot-fg-default);` | Auxiliary info ("Pricing Details", "Contact Sales") |

## 2. Copywriting Patterns for Action Triggers
Button copy must state the value or outcome received, not just the mechanical action required.

- **Outcome-Oriented**:
  - *Weak*: "Submit" -> *Strong*: "Generate My Free Audit"
  - *Weak*: "Continue" -> *Strong*: "Access Developer Sandbox"
  - *Weak*: "Register" -> *Strong*: "Claim Free API Key"
- **Friction-Reducing Microcopy**:
  Always place reassuring microcopy directly beneath the primary button:
  - "No credit card required • Instant 14-day access"
  - "Takes less than 60 seconds • Cancel anytime"

## 3. Mobile Viewport Sticky CTAs
On mobile viewports (<768px), scrolling through lengthy feature explanations often causes the user to lose sight of the conversion action.

- **Implementation Pattern**:
  ```css
  @media (max-width: 767px) {
    .ot-sticky-cta-bar {
      position: sticky;
      inset-block-end: 0;
      inset-inline: 0;
      background: var(--ot-bg-surface);
      border-block-start: 1px solid var(--ot-border-subtle);
      padding-block: var(--ot-space-sm);
      padding-inline: var(--ot-space-md);
      z-index: 50;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
    }
  }
  ```
- **Accessibility Safeguard**: Ensure sticky bottom bars do not occlude inputs or content by adding corresponding bottom padding to the main container (`padding-block-end: 72px`).

## 4. Directional Symmetry & BiDi Mirroring
- Arrow icons inside CTAs must reflect direction:
  - LTR: `→` (forward arrow points right)
  - RTL: `←` (forward arrow points left)
- Use `[dir="rtl"] .ot-cta-icon { transform: scaleX(-1); }` to maintain seamless flow in Arabic interfaces.
