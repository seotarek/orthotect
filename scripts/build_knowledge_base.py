#!/usr/bin/env python3
"""
Orthotect Knowledge Base Builder & Validator
Generates original, rigorously validated UI/UX knowledge records and style recipes.
All records conform strictly to JSON schemas in knowledge/schemas/.
"""

import json
import os
import sys
from pathlib import Path
import jsonschema

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
SCHEMAS_DIR = KNOWLEDGE_DIR / "schemas"

# Load Schemas
with open(SCHEMAS_DIR / "style-recipe.schema.json", "r", encoding="utf-8") as f:
    STYLE_RECIPE_SCHEMA = json.load(f)

with open(SCHEMAS_DIR / "knowledge-record.schema.json", "r", encoding="utf-8") as f:
    KNOWLEDGE_RECORD_SCHEMA = json.load(f)

# 1. STYLE RECIPES
STYLE_RECIPES = [
    {
        "$schema": "../schemas/style-recipe.schema.json",
        "id": "restrained-editorial-clarity",
        "name": "Restrained Editorial Clarity",
        "version": "1.0.0",
        "designThesis": "Elevated, content-first readability with disciplined typographic scale, generous asymmetric whitespace, and muted tonal surfaces. Eliminates artificial decorative chrome in favor of clear semantic hierarchy.",
        "bestFitContexts": [
            "Long-form publication platforms",
            "Technical documentation portals",
            "Architecture and design monograph sites",
            "Thought-leadership blogs",
            "High-end corporate manifestos"
        ],
        "poorFitContexts": [
            "High-frequency telemetry consoles",
            "Multi-stream operational dashboards",
            "Dense enterprise transaction forms",
            "Low-latency trading terminals"
        ],
        "colorStrategy": {
            "canvasTone": "Warm off-white (#fbfbf9) in light mode; deep obsidian graphite (#0d0e11) in dark mode",
            "accentUsage": "Single accent (burnt amber or cold slate) reserved exclusively for active navigation and primary text highlights",
            "contrastTarget": "Minimum 7.0:1 AAA on body copy; 4.5:1 AA on secondary captions"
        },
        "typographyStrategy": {
            "fontPairing": "Editorial serif display (Newsreader / Playfair / Charter) paired with neutral humanist sans body (Inter / Geist / system-ui)",
            "hierarchyEmphasis": "High contrast between display titles and body text; tight line tracking on titles, generous 1.65 line-height on long-form prose",
            "scaleFactor": "1.333 (Perfect Fourth) modular scale with max reading width clamped to 68ch"
        },
        "layoutRhythm": {
            "density": "comfortable",
            "gridStructure": "12-column asymmetric grid with wide margins (min 48px), offset blockquotes, and dedicated margin annotation rail",
            "whitespaceDiscipline": "Generous vertical cadence (48px–96px between semantic chapters); zero cramped card containers"
        },
        "surfaceTreatment": {
            "radius": "2px to 4px subtle rounded corners; sharp architectural edges on structural panels",
            "borderStyle": "1px hairline solid using semi-transparent border tokens (var(--ot-border-subtle))",
            "depthElevation": "Flat planar elevation with subtle ambient contact shadows (0 1px 3px rgba(0,0,0,0.04))"
        },
        "componentGuidelines": {
            "primaryActionStyle": "Underlined textual links or restrained hairline outline buttons with subtle background fill on hover",
            "cardStructure": "Borderless or hairline-bounded content cells with generous internal padding (min 24px) and zero gradient fills",
            "tablePresentation": "Open tabular layout with subtle horizontal rules only; no vertical borders, right-aligned numeric data"
        },
        "accessibilityProfile": {
            "targetWcagRatio": 7.0,
            "keyboardHandling": "Prominent 2px solid focus ring with 2px offset; skip-to-content link always present at document start",
            "reducedMotionRules": "All scroll and fade transitions disabled or collapsed to immediate 0ms when prefers-reduced-motion is active"
        },
        "antiPatterns": [
            "Gimmicky multi-color gradient text",
            "Emoji icons in section headings",
            "Overcrowded multi-column sidebars on reading pages",
            "Unclamped text containers exceeding 80 characters per line"
        ],
        "verificationProtocol": {
            "requiredGates": [
                "gate_contrast_wcag.py",
                "gate_no_slop.py",
                "gate_bidi_logical.py"
            ],
            "browserChecks": [
                "Verify text readability at 100%, 150%, and 200% zoom",
                "Verify line-length clamps across viewports (375px to 1440px)",
                "Verify high contrast mode renders all text with system borders"
            ]
        }
    },
    {
        "$schema": "../schemas/style-recipe.schema.json",
        "id": "precision-analytical-console",
        "name": "Precision Analytical Console",
        "version": "1.0.0",
        "designThesis": "High-signal, cognitive-ergonomic telemetry and operations interface. Employs tabular numeric alignment, scannable data density, micro-sparklines, and zero decorative fluff to minimize cognitive load under time-critical operational conditions.",
        "bestFitContexts": [
            "Cloud infrastructure observability consoles",
            "Security operations center (SOC) event monitors",
            "Financial market trading workstations",
            "Industrial telemetry and IoT telemetry monitors",
            "Developer CI/CD runtime dashboards"
        ],
        "poorFitContexts": [
            "Consumer e-commerce storefronts",
            "Lifestyle blog landing pages",
            "Marketing campaign micro-sites",
            "Creative portfolio showcases"
        ],
        "colorStrategy": {
            "canvasTone": "Deep technical slate-black (#090d16) in dark mode; clinical ice-neutral (#f1f5f9) in light mode",
            "accentUsage": "Strict intent-based palette: emerald green for nominal/healthy, amber for warning/degraded, crimson for critical/failure, cyan for active selection",
            "contrastTarget": "Minimum 7.0:1 AAA on metrics and code values; 5.0:1 on status badges"
        },
        "typographyStrategy": {
            "fontPairing": "Technical monospaced data font (JetBrains Mono / Fira Code) with condensed grotesque sans (Geist / IBM Plex Sans)",
            "hierarchyEmphasis": "Metrics emphasized by numeral weight and size, accompanied by muted micro-labels; tabular lining figures (font-variant-numeric: tabular-nums) mandatory",
            "scaleFactor": "1.125 (Major Second) tight scale for maximum information compactness without visual clutter"
        },
        "layoutRhythm": {
            "density": "compact",
            "gridStructure": "16-column dense data grid with 8px gutters; collapsible telemetry rails and fixed-height scrollable log streams",
            "whitespaceDiscipline": "Calibrated tight spacing (4px–8px padding inside data cells, 16px between macro widgets)"
        },
        "surfaceTreatment": {
            "radius": "0px to 2px sharp precision edges; absolutely no pill-shaped buttons in data tables",
            "borderStyle": "1px technical hairline grid borders using var(--ot-border-subtle)",
            "depthElevation": "Flat planar surfaces with 1px border separation; zero drop shadows to maintain razor-sharp pixel boundary alignment"
        },
        "componentGuidelines": {
            "primaryActionStyle": "Compact rectangular buttons with mono hotkey indicators (e.g., [⌘K], [R]) and tactile pressed state",
            "cardStructure": "Self-contained metric cards with inline SVG sparklines, status pills, and delta indicators",
            "tablePresentation": "Dense data grid with sticky headers, column sorting indicators, hover crosshairs, and monospaced alignment"
        },
        "accessibilityProfile": {
            "targetWcagRatio": 7.0,
            "keyboardHandling": "Full vim-style or arrow-key cell navigation; [Esc] to dismiss modals/drawers; screen reader aria-live regions for streaming alerts",
            "reducedMotionRules": "Streaming chart updates render via requestAnimationFrame without spring transitions when reduced-motion is detected"
        },
        "antiPatterns": [
            "Floating bubbly card layouts with 16px border-radius",
            "Soft colorful drop shadows under metric numbers",
            "Proportional non-tabular numbers that cause table layout jitter",
            "Unlabeled icon-only status indicators without text or tooltip"
        ],
        "verificationProtocol": {
            "requiredGates": [
                "gate_contrast_wcag.py",
                "gate_fsm_integrity.py",
                "gate_bidi_logical.py",
                "gate_cwv_budget.mjs"
            ],
            "browserChecks": [
                "Verify tabular-nums alignment across streaming numeric updates",
                "Verify zero layout shift during asynchronous data polling",
                "Verify keyboard-only table row selection and filtering"
            ]
        }
    },
    {
        "$schema": "../schemas/style-recipe.schema.json",
        "id": "contemporary-product-saas",
        "name": "Contemporary Product SaaS",
        "version": "1.0.0",
        "designThesis": "Purposeful, balanced modern product architecture. Combines clean structural bento cards, restrained brand accentuation, crisp micro-interactions, and accessible typography into an efficient enterprise workflow environment.",
        "bestFitContexts": [
            "B2B SaaS workflow tools",
            "Customer relationship management platforms",
            "Team collaboration and issue tracking workspaces",
            "Project management consoles",
            "Billing and subscription management portals"
        ],
        "poorFitContexts": [
            "High-frequency algorithmic trading terminals",
            "Immersive 3D gaming hubs",
            "Brutalist underground art zines",
            "Purely textual legal archives"
        ],
        "colorStrategy": {
            "canvasTone": "Neutral balanced canvas (#ffffff / #f8fafc in light; #0f172a / #0b0f17 in dark)",
            "accentUsage": "Single primary brand color (e.g., electric cobalt, deep teal) for primary CTAs and active states; semantic tokens for status",
            "contrastTarget": "Minimum 4.5:1 AA for UI text, 7.0:1 AAA for body copy"
        },
        "typographyStrategy": {
            "fontPairing": "Modern geometric/neo-grotesque sans (Inter, Geist, Plus Jakarta Sans, SF Pro)",
            "hierarchyEmphasis": "Clear 6-level type hierarchy; medium-weight subheadings (500), bold section titles (600), clean regular body (400)",
            "scaleFactor": "1.250 (Major Third) modular scale with balanced optical sizing"
        },
        "layoutRhythm": {
            "density": "default",
            "gridStructure": "12-column responsive layout with flexible bento grids (1/3, 2/3, full-width configurations)",
            "whitespaceDiscipline": "Consistent 8pt spatial grid (8px, 16px, 24px, 32px, 48px token steps)"
        },
        "surfaceTreatment": {
            "radius": "6px to 8px smooth rounded corners; 9999px for status badges only",
            "borderStyle": "1px subtle hairline border (var(--ot-border-subtle)) with subtle surface contrast",
            "depthElevation": "Multi-tier elevation system: level-1 for cards (subtle border + 1px shadow), level-2 for dropdowns, level-3 for modals"
        },
        "componentGuidelines": {
            "primaryActionStyle": "Solid high-contrast button with 6px radius, clear hover highlight, and spring-physics active press",
            "cardStructure": "Clean bento cards with distinct header, body, and action footer; consistent 20px internal padding",
            "tablePresentation": "Zebra or border-divided data rows with hover state, action menus on row hover, and pagination footer"
        },
        "accessibilityProfile": {
            "targetWcagRatio": 4.5,
            "keyboardHandling": "Standard tab-order traversal; full aria-expanded and aria-controls binding on dropdowns and drawers",
            "reducedMotionRules": "Modal fade/scale animations replaced with instantaneous display state"
        },
        "antiPatterns": [
            "Generic indigo-to-purple gradient blobs",
            "Cards nested inside cards nested inside cards (card nesting syndrome)",
            "Disabled buttons that drop contrast below 3.0:1 without explanation tooltip",
            "Inconsistent border radius mixing 4px, 12px, 24px arbitrarily"
        ],
        "verificationProtocol": {
            "requiredGates": [
                "gate_contrast_wcag.py",
                "gate_fsm_integrity.py",
                "gate_bidi_logical.py",
                "gate_no_slop.py"
            ],
            "browserChecks": [
                "Verify responsive reflow at 768px, 1024px, and 1280px breakpoints",
                "Verify modal focus trapping and restoration on dismiss",
                "Verify LTR to RTL bidirectional symmetry"
            ]
        }
    },
    {
        "$schema": "../schemas/style-recipe.schema.json",
        "id": "high-density-operational",
        "name": "High-Density Operational",
        "version": "1.0.0",
        "designThesis": "Extreme spatial efficiency for complex multi-parameter control rooms and administrative dispatchers. Maximizes above-the-fold information throughput while preventing sensory fatigue through monochrome data grids and selective color alerts.",
        "bestFitContexts": [
            "Logistics fleet dispatch consoles",
            "Network operations center (NOC) topology controls",
            "Aviation / maritime flight path trackers",
            "Enterprise resource planning (ERP) batch processing views",
            "Audio/video production multi-track matrixes"
        ],
        "poorFitContexts": [
            "Casual consumer onboarding screens",
            "Brand marketing microsites",
            "Photo portfolio galleries",
            "Minimalist personal notes applications"
        ],
        "colorStrategy": {
            "canvasTone": "Deep matte carbon (#121316) in dark mode; high-clarity ash gray (#eceef2) in light mode",
            "accentUsage": "Monochrome default with surgical application of amber (#f59e0b) and red (#ef4444) strictly for anomalies",
            "contrastTarget": "Minimum 7.0:1 AAA across all control elements and indicators"
        },
        "typographyStrategy": {
            "fontPairing": "Condensed sans-serif (IBM Plex Sans Condensed, Roboto Condensed) paired with tabular monospace for values",
            "hierarchyEmphasis": "Distinction achieved via font-weight and background badge contrast rather than large font size leaps",
            "scaleFactor": "1.100 (Minor Second) micro-scale to fit dense matrices without overflowing"
        },
        "layoutRhythm": {
            "density": "compact",
            "gridStructure": "24-column ultra-granular grid with 4px gutters; multi-pane splitters and dockable toolbars",
            "whitespaceDiscipline": "Zero wasted margin space; 2px to 4px padding on actionable cells"
        },
        "surfaceTreatment": {
            "radius": "0px to 2px utilitarian architectural corners",
            "borderStyle": "1px hairline grid dividing lines; high-contrast focus rings",
            "depthElevation": "Flat layered docking planes with z-index separation and 1px inset borders"
        },
        "componentGuidelines": {
            "primaryActionStyle": "Tactile micro-buttons with distinct armed / triggered / locked states",
            "cardStructure": "Collapsible metric cells with miniature status bars and instantaneous refresh indicators",
            "tablePresentation": "Spreadsheet-style dense grid with multi-column sorting, row grouping, column reordering, and cell editing"
        },
        "accessibilityProfile": {
            "targetWcagRatio": 7.0,
            "keyboardHandling": "Full spreadsheet navigation (arrow keys, Tab, Enter, Space, Home, End, PageUp/Down); keyboard shortcuts for all commands",
            "reducedMotionRules": "Zero spatial translation motion; updates are instantaneous DOM changes"
        },
        "antiPatterns": [
            "Large decorative illustrations taking up vertical viewport space",
            "Excessive 32px padding inside data cards",
            "Hidden data behind decorative hover tooltips that could be shown directly",
            "Animated spinning loaders that delay interaction"
        ],
        "verificationProtocol": {
            "requiredGates": [
                "gate_contrast_wcag.py",
                "gate_fsm_integrity.py",
                "gate_bidi_logical.py",
                "gate_cwv_budget.mjs"
            ],
            "browserChecks": [
                "Verify DOM node count efficiency under 1000+ displayed data cells",
                "Verify zero CPU lockup during high-frequency data push",
                "Verify keyboard shortcuts operate reliably across all pane states"
            ]
        }
    },
    {
        "$schema": "../schemas/style-recipe.schema.json",
        "id": "material-led-commerce",
        "name": "Material-Led Commerce",
        "version": "1.0.0",
        "designThesis": "Tactile, product-celebrating digital merchandising architecture. Emphasizes authentic product geometry, crisp imagery bounding, transparent specification matrices, and friction-free transactional ergonomics.",
        "bestFitContexts": [
            "High-end hardware and electronics stores",
            "Architectural materials catalog and ordering portals",
            "Industrial equipment procurement platforms",
            "Direct-to-consumer luxury goods marketplaces",
            "B2B wholesale inventory portals"
        ],
        "poorFitContexts": [
            "Text-only terminal applications",
            "Developer CLI outputs",
            "Server error logs",
            "Purely numeric accounting ledgers"
        ],
        "colorStrategy": {
            "canvasTone": "Neutral optical white (#ffffff) or warm stone (#f7f7f5) in light; velvety deep space (#0a0a0c) in dark",
            "accentUsage": "Single checkout / primary CTA accent; secondary actions remain architectural neutral",
            "contrastTarget": "Minimum 4.5:1 AA on product spec labels; 7.0:1 AAA on pricing and primary CTA"
        },
        "typographyStrategy": {
            "fontPairing": "Clean Swiss neo-grotesque (Inter, Neue Haas Grotesk, Helvetica Now) with tabular numerals for prices",
            "hierarchyEmphasis": "Clear typographic hierarchy separating product name, price, stock availability, and technical specs",
            "scaleFactor": "1.200 (Minor Third) scale with crisp price display"
        },
        "layoutRhythm": {
            "density": "default",
            "gridStructure": "Dynamic 12-column product grid with sticky purchase summary rail and horizontal specification comparison tables",
            "whitespaceDiscipline": "Generous product framing whitespace; product imagery bounded in fixed aspect ratios (1:1, 4:3, 16:9)"
        },
        "surfaceTreatment": {
            "radius": "4px to 6px subtle modern curves",
            "borderStyle": "1px clean boundary borders (var(--ot-border-subtle)); zero blurry drop shadows around imagery",
            "depthElevation": "Flat product cards with crisp 1px border highlight on hover; floating sticky action bar on mobile"
        },
        "componentGuidelines": {
            "primaryActionStyle": "Prominent Add to Cart / Order CTA with explicit loading and optimistic cart badge feedback",
            "cardStructure": "Clean image-first card with aspect-ratio enclosure, badge overlay, title, price, and instant action",
            "tablePresentation": "Structured technical specification matrix with alternating subtle rows and clear unit column"
        },
        "accessibilityProfile": {
            "targetWcagRatio": 4.5,
            "keyboardHandling": "Accessible image gallery with arrow key navigation; live announcer for cart addition; modal dialog for quick-view",
            "reducedMotionRules": "Image carousel sliding transitions replaced with instant swap"
        },
        "antiPatterns": [
            "Fake countdown urgency timers and spammy popups",
            "Unbounded product images causing cumulative layout shift (CLS)",
            "Hiding technical specs behind multiple nested accordion clicks",
            "Emoji ratings instead of accessible SVG star reviews"
        ],
        "verificationProtocol": {
            "requiredGates": [
                "gate_contrast_wcag.py",
                "gate_fsm_integrity.py",
                "gate_bidi_logical.py",
                "gate_cwv_budget.mjs",
                "gate_no_slop.py"
            ],
            "browserChecks": [
                "Verify CLS = 0 during image asset loading",
                "Verify cart quantity FSM prevents double-submission race conditions",
                "Verify mobile sticky checkout bar does not obscure primary content"
            ]
        }
    },
    {
        "$schema": "../schemas/style-recipe.schema.json",
        "id": "accessible-high-contrast",
        "name": "Accessible High Contrast",
        "version": "1.0.0",
        "designThesis": "Uncompromising universal accessibility and perceptual clarity. Guarantees WCAG 2.2 AAA 7.0:1+ contrast across all states, tactile 3px keyboard focus indicators, dual visual cues (never color alone), and robust assistive tech compatibility.",
        "bestFitContexts": [
            "Public sector and government civic portals",
            "Healthcare and clinical patient portals",
            "Educational and assistive learning platforms",
            "Emergency notification systems",
            "Regulated utility and banking service platforms"
        ],
        "poorFitContexts": [
            "Low-contrast atmospheric art exhibitions",
            "Subtle monochromatic mood boards",
            "Dark, low-light experimental gaming visuals",
            "Sub-4.5:1 washed-out pastel aesthetic experiments"
        ],
        "colorStrategy": {
            "canvasTone": "Absolute pure canvas (#ffffff in light, #000000 in dark) with high-contrast structural borders",
            "accentUsage": "High-contrast primary action (#0052cc / #004494 in light, #38bdf8 / #7dd3fc in dark); every state verified > 7:1",
            "contrastTarget": "Minimum 7.0:1 AAA across ALL text, badges, and icons without exception"
        },
        "typographyStrategy": {
            "fontPairing": "Highly legible humanist sans with distinct letterforms (Atkinson Hyperlegible, Inter, Arial)",
            "hierarchyEmphasis": "High optical weight distinction; minimum 16px body text; 1.6 line height; generous letter tracking",
            "scaleFactor": "1.250 (Major Third) scale with responsive text resizing up to 200% without clipping"
        },
        "layoutRhythm": {
            "density": "comfortable",
            "gridStructure": "Clean, predictable single-column or 2-column linear layouts; unambiguous visual reading flow",
            "whitespaceDiscipline": "Wide touch targets (minimum 48×48px); generous margins separating clickable interactive elements"
        },
        "surfaceTreatment": {
            "radius": "2px to 4px slight rounding or crisp 0px corners for maximum border contrast",
            "borderStyle": "2px solid high-contrast borders on all interactive inputs, cards, and buttons",
            "depthElevation": "Flat high-contrast borders; zero diffuse drop shadows that blur edge definition"
        },
        "componentGuidelines": {
            "primaryActionStyle": "High-contrast solid button with 2px solid border, distinct text underline or icon, and 3px offset focus ring",
            "cardStructure": "High-contrast boxed containers with 2px borders, explicit headings, and clear separator rules",
            "tablePresentation": "Fully bordered data grid with bold headers, row numbers, and accessible table caption"
        },
        "accessibilityProfile": {
            "targetWcagRatio": 7.0,
            "keyboardHandling": "Unmistakable 3px solid focus indicator with 2px outer outline; full keyboard accessibility across all components; skip links",
            "reducedMotionRules": "All animations disabled by default; instantaneous transitions only"
        },
        "antiPatterns": [
            "Light gray text (#888888 or #9ca3af) on white canvas",
            "Relying on color alone to indicate error, warning, or success status",
            "Focus rings set to outline: none or outline: 0 without replacement",
            "Placeholder text inside inputs used as substitutes for permanent labels"
        ],
        "verificationProtocol": {
            "requiredGates": [
                "gate_contrast_wcag.py",
                "gate_bidi_logical.py",
                "gate_fsm_integrity.py",
                "gate_no_slop.py"
            ],
            "browserChecks": [
                "Verify full keyboard navigation flow without mouse interaction",
                "Verify 200% browser zoom reflow without text overlapping or horizontal scrolling",
                "Verify Windows High Contrast / Forced Colors mode support"
            ]
        }
    }
]

# 2. CORE KNOWLEDGE RECORDS
KNOWLEDGE_RECORDS = [
    # Category: palettes
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "semantic-roles",
        "title": "Deterministic Semantic Color Token Roles & Contrast Architecture",
        "category": "palettes",
        "summary": "Formal specification of intent-driven color roles, canvas surfaces, and dark/light mode token mappings satisfying WCAG 2.2 contrast thresholds.",
        "whenToUse": "When designing or implementing color tokens, styling components, or theming application surfaces across light and dark modes.",
        "whenNotToUse": "Do not use arbitrary hex codes or component-scoped ad-hoc colors outside the 3-tier token system.",
        "rules": [
            "All color assignments must use semantic tokens: var(--ot-surface-canvas), var(--ot-surface-card), var(--ot-action-primary), var(--ot-action-danger).",
            "Text on canvas must achieve at least 4.5:1 contrast for regular text and 3.0:1 for large text (AA); AAA targets 7.0:1 and 4.5:1.",
            "Dark mode must elevate surface brightness as hierarchy increases (surface-0 < surface-1 < surface-2 < surface-3).",
            "Light mode must maintain contrast without cutting harsh white blocks through colored grids or dark terminal backgrounds."
        ],
        "antiPatterns": [
            "Hardcoded hex or rgba color codes in component CSS",
            "Flipping dark to light by inverting colors without re-verifying contrast ratios",
            "Using gray text with contrast below 4.5:1 on light backgrounds",
            "Mixing saturated colored drop shadows under neutral text cards"
        ],
        "applicableStacks": ["css", "scss", "tailwind", "react", "vue", "svelte", "design-tokens"],
        "accessibilityNotes": "Every semantic token pair must pass the automated gate_contrast_wcag.py analyzer before deployment.",
        "provenance": "Synthesized independently from DTCG specification, WCAG 2.2 APG guidelines, and Orthotect architecture doctrine.",
        "verificationStatus": "VERIFIED_DETERMINISTIC",
        "tags": ["palettes", "contrast", "wcag", "tokens", "dark-mode", "light-mode", "semantic-colors"]
    },
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "dark-mode-mapping",
        "title": "Dual-Theme Surface Layering & Reactive Contrast Synchronization",
        "category": "palettes",
        "summary": "Rules for seamless dual-theme (light/dark) switching, ensuring high contrast, terminal legibility, and zero visual jarring.",
        "whenToUse": "When configuring multi-theme applications, dark/light toggle controls, and scoped terminal or code viewer surfaces.",
        "whenNotToUse": "Do not apply dark mode styles to dedicated terminal components that must stay consistently high-contrast in both modes.",
        "rules": [
            "Dedicated terminal boxes and code viewports must maintain scoped dark surface tokens (e.g., #0d1117 with #f0f6fc text) regardless of page mode.",
            "Theme switching must update both CSS custom properties and interactive asset variants (e.g., logo SVG) via reactive DOM attributes.",
            "Subordinate controls (toolbars, density buttons, bidi switches) must reflect the active theme without requiring manual page reload.",
            "Playground or preview viewports must offer independent or synchronized theme toggles with clear state indicators."
        ],
        "antiPatterns": [
            "Allowing dark text on dark backgrounds when toggling from dark to light mode",
            "White horizontal strips cutting through background grids in light mode",
            "Missing brand logos or unreadable wordmarks in light mode",
            "Flickering theme flashes (FOUC) during initial page load"
        ],
        "applicableStacks": ["css", "html", "javascript", "react", "nextjs", "vue"],
        "accessibilityNotes": "Verified through automated Playwright browser tests checking computed getComputedStyle contrast in both light and dark modes.",
        "provenance": "Developed during Orthotect UI/UX contrast resolution and browser regression verification.",
        "verificationStatus": "VERIFIED_BROWSER",
        "tags": ["theming", "dark-mode", "light-mode", "contrast", "terminals", "reactivity"]
    },

    # Category: typography
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "type-scales",
        "title": "Modular Typographic Scale Factors & Tabular Numeric Discipline",
        "category": "typography",
        "summary": "Mathematical typographic scale systems, responsive fluid clamping (clamp()), and tabular numeric alignment for interfaces.",
        "whenToUse": "When setting up typographic tokens, heading hierarchies, data tables, telemetry counters, and long-form prose.",
        "whenNotToUse": "Do not invent random font sizes per component; all sizes must bind to the typographic scale tokens.",
        "rules": [
            "Use standard modular scales: 1.125 (Major Second) for dense dashboards, 1.250 (Major Third) for SaaS, 1.333 (Perfect Fourth) for editorial.",
            "All numeric data in tables, counters, and telemetry metrics must use font-variant-numeric: tabular-nums.",
            "Line height must decrease as font size increases: 1.6 to 1.7 for body text (14-16px), 1.2 to 1.3 for section headings (24-32px), 1.1 for hero displays.",
            "Max line length for prose reading must be clamped to 65-75ch using max-inline-size."
        ],
        "antiPatterns": [
            "Proportional numbers in data tables that cause column jitter during real-time updates",
            "Six-line headline wraps caused by excessively large unscaled typography on small laptops",
            "Tight line-height (<1.4) on small body copy causing ascender/descender collisions",
            "Using more than 3 distinct font families in a single application interface"
        ],
        "applicableStacks": ["css", "web-fonts", "tailwind", "design-tokens", "react", "vue"],
        "accessibilityNotes": "Text must remain fully readable and reflow cleanly when zoomed up to 200% without horizontal scrollbars (WCAG 1.4.4).",
        "provenance": "Orthotect typographic engineering canon and Bringhurst typographic harmony principles.",
        "verificationStatus": "VERIFIED_DETERMINISTIC",
        "tags": ["typography", "scale", "tabular-nums", "fluid-type", "readability", "responsive"]
    },

    # Category: components
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "component-contracts",
        "title": "Interactive Component FSM State Contracts & Keyboard Accessibility",
        "category": "components",
        "summary": "Strict Finite State Machine contracts for standard UI components: Button, Input, Modal, Tabs, Dropdown, Table, and Toast.",
        "whenToUse": "When authoring or reviewing interactive UI components, asynchronous form controls, and accessible navigation widgets.",
        "whenNotToUse": "Do not treat UI components as purely visual templates; every interactive element must declare its state transitions.",
        "rules": [
            "Every interactive element must handle 7 explicit states: idle, hover, active/pressed, focus-visible, loading, disabled, and error/success.",
            "Loading state must maintain accessible label (aria-busy='true', aria-live='polite') and never drop contrast below 3.0:1.",
            "Buttons must prevent double-submission race conditions using deterministic event locks.",
            "Interactive cards with clickable nested actions must isolate click targets using stopPropagation and distinct focus boundaries."
        ],
        "antiPatterns": [
            "Buttons with loading spinners that completely remove the button label causing layout shift",
            "Disabling buttons without providing an explanation for why the action is disabled",
            "Clickable divs (<div onClick=...>) without role='button', tabindex='0', and Enter/Space key listeners",
            "Nested buttons inside anchor tags violating HTML specifications"
        ],
        "applicableStacks": ["javascript", "typescript", "react", "vue", "svelte", "web-components", "html"],
        "accessibilityNotes": "Component contracts are deterministically verified by gate_fsm_integrity.py and WAI-ARIA APG pattern checkers.",
        "provenance": "Orthotect FSM architecture and W3C WAI-ARIA 1.2 authoring practices.",
        "verificationStatus": "VERIFIED_DETERMINISTIC",
        "tags": ["components", "fsm", "state-machine", "keyboard", "wai-aria", "accessibility", "contracts"]
    },
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "dialog-focus-trap",
        "title": "Accessible Modal Dialog Focus Trapping & Restoration Protocol",
        "category": "components",
        "summary": "Mandatory focus trapping, background inertia (aria-hidden), Escape key dismissal, and focus restoration for modal dialogs.",
        "whenToUse": "When creating confirmation dialogs, modal overlays, slide-out drawer sheets, or fullscreen wizard overlays.",
        "whenNotToUse": "Do not trap focus for non-modal popovers or inline expandable panels.",
        "rules": [
            "On open: shift focus to first interactive element or dialog title with role='dialog' and aria-modal='true'.",
            "While open: Tab and Shift+Tab key presses must cycle strictly within the dialog interactive elements.",
            "Pressing Escape key must immediately dismiss the dialog and restore focus to the triggering element.",
            "Underlying page content must be marked with aria-hidden='true' or inert attribute while dialog is active."
        ],
        "antiPatterns": [
            "Keyboard focus leaking into background page content behind an open modal",
            "Dismissing a dialog and dropping focus onto <body> or top of page",
            "Dialogs lacking an explicit visible close button or aria-label",
            "Background scroll unlocking when interacting inside long modal bodies"
        ],
        "applicableStacks": ["html", "javascript", "react", "vue", "svelte", "wcag"],
        "accessibilityNotes": "Fulfills WCAG 2.1 Criterion 2.1.2 (No Keyboard Trap) and WAI-ARIA Modal Dialog APG pattern.",
        "provenance": "Synthesized from W3C WAI-ARIA modal dialog recommendations and browser focus management standards.",
        "verificationStatus": "VERIFIED_BROWSER",
        "tags": ["dialog", "modal", "focus-trap", "keyboard", "accessibility", "wai-aria"]
    },

    # Category: patterns
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "layout-patterns",
        "title": "Architectural Layout Patterns: Bento Grids, Split Rails & Responsive Containers",
        "category": "patterns",
        "summary": "Compositional grid systems, asymmetric bento layouts, sticky telemetry rails, and responsive breakpoint reflow structures.",
        "whenToUse": "When structuring page architectures, dashboard layouts, feature showcases, and multi-pane applications.",
        "whenNotToUse": "Do not force complex multi-column grids onto narrow mobile viewports (<640px) without single-column linear reflow.",
        "rules": [
            "Containers must define explicit max-inline-size (e.g., 1280px / 1440px) and margin-inline: auto.",
            "Bento grids must establish clear visual hierarchy: 1 primary hero anchor cell (2x2 or 2x1) supported by secondary 1x1 cells.",
            "Use CSS Grid with minmax(min(100%, ...), 1fr) to guarantee intrinsic responsiveness without unexpected horizontal overflows.",
            "Sticky sidebars and control rails must account for viewport height (max-block-size: 100vh; overflow-y: auto)."
        ],
        "antiPatterns": [
            "Symmetric flat bento grids where every card has identical dimensions and visual weight",
            "Layouts causing horizontal scrollbars on 375px mobile screens",
            "Sticky rails with fixed pixel heights that clip action buttons on small laptop screens",
            "Using absolute positioning for structural page layout columns"
        ],
        "applicableStacks": ["css", "html", "grid", "flexbox", "tailwind", "responsive"],
        "accessibilityNotes": "Grid layout reading order in DOM must match visual reading order to ensure logical screen reader navigation.",
        "provenance": "Synthesized from modern interface composition research and CSS Grid level 2 standards.",
        "verificationStatus": "VERIFIED_DETERMINISTIC",
        "tags": ["layout", "grid", "bento", "responsive", "containers", "composition"]
    },

    # Category: ux-guidelines
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "patterns",
        "title": "Cognitive Ergonomic Laws & Progressive Disclosure Discipline",
        "category": "ux-guidelines",
        "summary": "Core interface ergonomics applying Fitts's Law, Miller's 7±2 Rule, Hick's Law, and feedback latency thresholds to UI design.",
        "whenToUse": "When organizing navigation systems, complex forms, dense settings pages, and interactive workflows.",
        "whenNotToUse": "Do not hide critical immediate actions or primary navigation behind excessive nested accordion menus.",
        "rules": [
            "Apply Miller's Rule: Limit primary navigation to 7±2 top-level items; group dense actions into clear semantic clusters.",
            "Apply Fitts's Law: Primary CTA target areas must be minimum 44×44px on touch interfaces and positioned for effortless acquisition.",
            "Apply Hick's Law: Reduce decision fatigue in complex flows through progressive disclosure (staging advanced settings behind clear toggles).",
            "Feedback timing: UI responses must acknowledge user action within 100ms; show skeleton/loader if operation exceeds 300ms."
        ],
        "antiPatterns": [
            "Overwhelming users with 20+ unstructured form fields on a single unpaginated screen",
            "Action buttons placed in obscure corners with tiny 16×16px click targets",
            "Silent asynchronous failures where no toast or error banner notifies the user",
            "Disabling form submit buttons without highlighting which required fields are invalid"
        ],
        "applicableStacks": ["ux", "product-design", "frontend", "forms", "navigation"],
        "accessibilityNotes": "Reduces cognitive load for all users, including individuals with attention and memory cognitive disabilities.",
        "provenance": "Human-Computer Interaction (HCI) foundations and Nielsen Norman Group empirical research.",
        "verificationStatus": "HEURISTIC",
        "tags": ["ux", "ergonomics", "fitts-law", "millers-law", "progressive-disclosure", "cognitive"]
    },

    # Category: accessibility
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "wcag-matrix",
        "title": "WCAG 2.2 AA/AAA Deterministic Verification Matrix & Checklist",
        "category": "accessibility",
        "summary": "Comprehensive engineering rules for contrast, keyboard traps, touch target sizes, focus states, and ARIA semantic attributes.",
        "whenToUse": "Mandatory checklist for every UI screen, component library, and automated CI pull-request gate verification.",
        "whenNotToUse": "Never bypass accessibility checks; all production interface code must comply with WCAG 2.2 Level AA minimum.",
        "rules": [
            "1.4.3 Contrast (Minimum): Normal text must meet 4.5:1; large text (>=18pt or 14pt bold) must meet 3.0:1. AAA requires 7.0:1 / 4.5:1.",
            "1.4.11 Non-text Contrast: UI components and graphical objects must meet 3.0:1 against adjacent colors.",
            "2.1.1 Keyboard: All functionality must be operable via keyboard without mouse dependency.",
            "2.4.7 Focus Visible & 2.4.13 Focus Appearance: Focus indicators must have at least 2px thickness and 3.0:1 contrast against background.",
            "2.5.8 Target Size (Minimum): Interactive pointer targets must be at least 24×24px, with 44×44px recommended for touch devices."
        ],
        "antiPatterns": [
            "Removing focus outlines (outline: none or outline: 0) without a custom high-contrast replacement",
            "Interactive buttons or links without accessible name (empty text and no aria-label)",
            "Using color alone to communicate state (e.g. red text without error icon or prefix)",
            "Form inputs missing associated <label> elements or aria-labelledby attributes"
        ],
        "applicableStacks": ["html", "css", "wai-aria", "javascript", "react", "vue"],
        "accessibilityNotes": "Directly enforced in CI by gate_contrast_wcag.py and automated browser axe/playwright test suites.",
        "provenance": "W3C Web Content Accessibility Guidelines (WCAG) 2.2 official recommendation.",
        "verificationStatus": "VERIFIED_DETERMINISTIC",
        "tags": ["accessibility", "wcag", "contrast", "keyboard", "focus", "aria", "target-size"]
    },

    # Category: motion
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "motion-tokens",
        "title": "Spring Physics Motion Tokens & Reduced-Motion Accessibility Rules",
        "category": "motion",
        "summary": "Physically grounded transition tokens, spring physics curves, and mandatory @media (prefers-reduced-motion) overrides.",
        "whenToUse": "When implementing UI transitions, modal entry/exit animations, accordion expansion, and hover feedback.",
        "whenNotToUse": "Never animate structural layout properties (width, height, margin) that trigger CPU/GPU browser layout recalculations.",
        "rules": [
            "Animate only composite properties: transform and opacity for smooth 60fps/120fps hardware-accelerated motion.",
            "Use calibrated spring physics tokens: --ot-motion-snappy (150ms cubic-bezier(0.16, 1, 0.3, 1)) and --ot-motion-expressive (300ms cubic-bezier(0.34, 1.56, 0.64, 1)).",
            "Mandatory reduced motion: wrap animations in @media (prefers-reduced-motion: reduce) to collapse duration to 0ms or simple opacity fade.",
            "Avoid continuous looping rotations or pulsing animations that distract or cause vestibular discomfort."
        ],
        "antiPatterns": [
            "Lazy transition: all 0.2s ease that animates layout properties and degrades rendering performance",
            "Ignoring prefers-reduced-motion settings, causing nausea for users with vestibular disorders",
            "Excessively slow animations (>500ms) for everyday micro-interactions that make the app feel sluggish",
            "Bouncing animations on data cards in professional telemetry or trading consoles"
        ],
        "applicableStacks": ["css", "animation", "motion", "transitions", "tailwind", "design-tokens"],
        "accessibilityNotes": "Fulfills WCAG 2.2 Criterion 2.3.3 (Animation from Interactions) and prevents vestibular disturbance.",
        "provenance": "Orthotect motion doctrine and Apple Human Interface Guidelines spatial physics principles.",
        "verificationStatus": "VERIFIED_DETERMINISTIC",
        "tags": ["motion", "spring-physics", "transitions", "reduced-motion", "accessibility", "performance"]
    },

    # Category: bidi
    {
        "$schema": "../schemas/knowledge-record.schema.json",
        "id": "logical-rules",
        "title": "True Bidirectional (BiDi) Engineering via CSS Logical Properties",
        "category": "bidi",
        "summary": "Mandatory use of CSS Logical Properties and directional vector isolation for flawless LTR and RTL symmetric layout rendering.",
        "whenToUse": "Mandatory on all layout, spacing, alignment, and directional styling across components and screens.",
        "whenNotToUse": "Physical directions (left, right, margin-left, padding-right) are strictly forbidden under Orthotect Law 2.",
        "rules": [
            "Replace margin-left with margin-inline-start; replace margin-right with margin-inline-end.",
            "Replace padding-left with padding-inline-start; replace padding-right with padding-inline-end.",
            "Replace text-align: left with text-align: start; replace text-align: right with text-align: end.",
            "Replace left/right position offsets with inset-inline-start and inset-inline-end.",
            "Directional vectors (e.g. forward arrow →) must flip automatically in RTL via [dir='rtl'] svg { transform: scaleX(-1); }."
        ],
        "antiPatterns": [
            "Writing duplicate stylesheets (style-rtl.css) or hardcoded .rtl overrides",
            "Using float: left or float: right in modern CSS",
            "Hardcoding physical left/right margins that invert incorrectly in Arabic or Hebrew",
            "Flipping non-directional icons (e.g., search magnifying glass, clock, checkmark) in RTL"
        ],
        "applicableStacks": ["css", "html", "bidi", "rtl", "arabic", "hebrew", "internationalization"],
        "accessibilityNotes": "Guarantees full cognitive symmetry and natural reading order for right-to-left language users.",
        "provenance": "W3C CSS Logical Properties and Values Level 1 recommendation and Orthotect Law 2.",
        "verificationStatus": "VERIFIED_DETERMINISTIC",
        "tags": ["bidi", "rtl", "logical-properties", "css-logical", "internationalization", "symmetry"]
    }
]

def main():
    print("=================================================================")
    print("      ORTHOTECT KNOWLEDGE BASE BUILDER & SCHEMA VALIDATOR        ")
    print("=================================================================\n")

    # Validate and write style recipes
    styles_dir = KNOWLEDGE_DIR / "styles"
    styles_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Building and validating {len(STYLE_RECIPES)} Style Recipes in {styles_dir}...")
    
    for recipe in STYLE_RECIPES:
        recipe_id = recipe["id"]
        # Validate against schema
        jsonschema.validate(instance=recipe, schema=STYLE_RECIPE_SCHEMA)
        out_file = styles_dir / f"{recipe_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(recipe, f, indent=2, ensure_ascii=False)
        print(f"  [OK] Validated & Wrote: {out_file.name}")

    # Validate and write knowledge records
    print(f"\n[*] Building and validating {len(KNOWLEDGE_RECORDS)} Knowledge Records across categories...")
    
    for record in KNOWLEDGE_RECORDS:
        record_id = record["id"]
        category = record["category"]
        cat_dir = KNOWLEDGE_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate against schema
        jsonschema.validate(instance=record, schema=KNOWLEDGE_RECORD_SCHEMA)
        out_file = cat_dir / f"{record_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        print(f"  [OK] Validated & Wrote: {category}/{out_file.name}")

    print("\n[+] SUCCESS! All style recipes and knowledge records conform 100% to schemas.")

if __name__ == "__main__":
    main()
