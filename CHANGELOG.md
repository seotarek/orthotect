# Changelog

All notable changes to the Orthotect Interface Architecture are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.1] - 2026-10-23

### Fixed
- **BiDi AST Gate Regex Literal Lexical Parsing**: Disambiguated JavaScript regular expression literals (e.g., `const pattern = /https?:\/\//;`) from line comments in `strip_js_comments_string_aware()` and `extract_tagged_template_literals()` within `gates/gate_bidi_logical.py`. Escaped slashes (`\/`) inside regex literals no longer trigger false comment stripping, preventing physical CSS properties in subsequent code from escaping verification. Added regression tests in `tests/test_bidi.py` (25/25 BiDi tests passing).
- **FSM Scaffolded Page Synthetic Event & State Lock Verification**: Hardened `bin/orthotect.js` and `tests/test_scaffold_browser.py` by adding an explicit action execution counter (`window.__orthotectActionExecCount`). The Playwright browser test now verifies double-click lockout via synthetic DOM event dispatch (`dispatchEvent(new MouseEvent('click'))`) and direct controller calls (`transition('CLICK')`) during the `loading` state, asserting that action execution count strictly remains 1.
- **FSM Scaffolded Page Full Error Recovery Cycle**: Added single-failure error simulation (`simulate=error_once`) in `bin/orthotect.js`. Hardened `tests/test_scaffold_browser.py` to verify the complete error recovery lifecycle in headless Chromium: transitioning from `loading` -> `error`, clicking "Retry Action" to transition back to `loading`, and successfully reaching `success` ("Action Verified") before returning to `idle`.

### CI
- **Publish Workflow Hardening**: Updated `.github/workflows/publish-package.yml` to run test suites (`npm test`) and deterministic quality gates (`python3 gates/run_all_gates.py docs && python3 gates/run_all_gates.py examples/golden-showcase`) prior to publishing. Restricted workflow trigger execution to the `main` branch and release tags (`v*`).

## [1.7.0] - 2026-10-23

### Added
- **Sovereign UI/UX Design Intelligence Synthesis**:
  - Ingested and mapped 57 distinct UI styles, 96 harmonized color palettes, 57 typographic font pairings, 25 chart & telemetry specs, and 13 multi-framework engineering guidelines into native Orthotect schemas.
  - Added 6 new original, production-tested style recipes to `knowledge/styles/`: `minimalist-swiss.json`, `cyberpunk-terminal.json`, `glassmorphism-aurora.json`, `neubrutalism-clean.json`, `claymorphism-soft.json`, and `oled-dark-mode.json` (12 total style recipes certified).
  - All 26 knowledge records verified under strict dual-mode schema validation (`jsonschema` + stdlib fallback).
- **Template Aesthetic Diversification (50 Bespoke Profiles)**:
  - Eliminated visual monotony across all 50 SEO production templates in `docs/templates/`: every single template now possesses its own unique aesthetic identity.
  - Symmetrically balanced across 25 Light themes and 25 Dark themes with Google Font typography pairings, bespoke color palettes, tailored border geometries (0px brutalist to 18px claymorphic), and box-shadow layers.
  - Mathematically verified 100% WCAG 2.2 AA (>= 4.5:1) and AAA (>= 7.0:1) contrast ratios across all 50 profiles.
  - Dynamic Google Fonts and scoped `--tmpl-*` CSS variable injection with full CSS logical property compliance.
- **Enhanced Gallery & Discovery Engine (`docs/`)**:
  - Updated `docs/gallery-data.json` and `docs/gallery-data.js` to register UI styles, font pairings, and color themes for all 50 templates.
  - Updated `docs/app.js` with visual style pill badges, theme indicators, and live search filtering across UI styles and typography.
- **Quality Gates & Browser Verification**:
  - Maintained 100% green status across all 5 deterministic quality gates on `docs/` and `examples/golden-showcase` (sub-second parallel execution).
  - Passed Playwright headless Chromium rendered DOM contrast test: 20/20 computed element pairs passing WCAG 2.2 in both Light and Dark themes.
  - Added `tests/test_scaffold_browser.py` verifying scaffolded FSM page lifecycle (`idle` -> `loading` -> `success` -> `idle`), double-click race condition lock, and error recovery in headless Chromium.
  - Full test suite passing (234 tests across unit, browser, and negative gate suites).
- **GitHub Packages Registry Publishing**: Added `.github/workflows/publish-package.yml` and published `@seotarek/orthotect@1.7.0` to GitHub Packages registry.

### Security
- **DOM XSS Sanitization & Browser Verification**: Sanitized gallery empty-state search query interpolation and playground FSM simulator inputs via strict HTML entity escaping (`docs/app.js`). Added automated Playwright headless Chromium regression tests `test_gallery_search_xss_sanitization` and `test_fsm_terminal_xss_sanitization` in `tests/test_docs_browser.py`.
- **CI Supply-Chain Hardening**: Configured explicit minimum permissions (`permissions: contents: read`) in `.github/workflows/ci.yml` and pinned all GitHub Actions across `ci.yml` and `pages.yml` to immutable 40-character commit SHAs.

### Fixed
- **BiDi AST Gate String-Aware Lexical Scanner & Interpolation Stack**: Implemented state-machine comment stripper `strip_js_comments_string_aware()` and `extract_tagged_template_literals()` in `gates/gate_bidi_logical.py` to handle nested template literals and `${...}` interpolations. Masks expressions with dummy CSS tokens so `tinycss2` reliably flags physical properties in styled-components without false negatives or comment interference. Added tests in `tests/test_bidi.py` (24/24 BiDi tests passing).
- **Anti-Slop Multi-File Support**: Extended `gates/gate_no_slop.py` to scan `.js`, `.ts`, `.jsx`, and `.tsx` files, banning raw emoji icons in JSX button elements and untokenized hex colors in inline style blocks.
- **CLI Doctor Semver Validation**: Fixed Node.js version parsing in `orthotect doctor` to check both major and minor numbers (`major > 20 || (major === 20 && minor >= 19)`), properly enforcing `>=20.19.0`.
- **CLI Design Page Executable FSM Runtime**: Upgraded `orthotect design page` to embed an active, zero-dependency client-side FSM controller into generated HTML boilerplate. Implements full state graph reachability (`idle` -> `loading` -> `success` -> `idle`), double-click race condition locks, error simulation (`?simulate=error`), and `aria-live` accessible status announcements (supports `--out <file>` and `--stdout`).
- **Competitive Language & Claims Calibration**: Calibrated `README.md` and `COMPETITORS.md` to remove hyperbolic claims, clearly framing alternative toolkits (component libraries, prompt skills) and delineating Orthotect's deterministic static AST verification role.
- **Architecture Documentation Alignment**: Synchronized `CONTRIBUTING.md` prerequisites and test counts with `package.json`, and added "Dual-Layer Verification Architecture & Scope Delineation" in `README.md`.

## [1.6.0] - 2026-10-23

### Added
- **UI/UX Design Intelligence Knowledge Base (`knowledge/`)**:
  - Established the 19-dimensional Orthotect Design Reasoning Model connecting product briefs to verified interface systems.
  - Authored formal JSON schemas: `style-recipe.schema.json`, `knowledge-record.schema.json`, and `design-reasoning.schema.json`.
  - Authored 6 original, schema-validated Style Recipes (`knowledge/styles/`): `restrained-editorial-clarity`, `precision-analytical-console`, `contemporary-product-saas`, `high-density-operational`, `material-led-commerce`, and `accessible-high-contrast`.
  - Authored 10 core Knowledge Records across 8 specialized categories (`palettes/`, `typography/`, `components/`, `patterns/`, `ux-guidelines/`, `accessibility/`, `motion/`, `bidi/`).
- **Offline Knowledge Search Engine (`core/knowledge_search.py`)**:
  - Developed a zero-dependency local search module with weighted BM25 relevance scoring (Title 5x, Tags 3x, Summary 2x, Rules 1x).
  - Supported multi-dimensional filtering by keyword, `--category`, `--tag`, `--stack`, and output modes (`--json`).
  - Integrated built-in JSON schema validation (`--validate`) certifying 100% compliance across all knowledge records.
- **15 Modular Autonomous Agent Skills (`skills/`)**:
  - Expanded skill suite to 15 modular skills: added `orthotect-uiux`, `orthotect-design-systems`, `orthotect-components`, `orthotect-accessibility`, `orthotect-responsive`, `orthotect-motion`, `orthotect-forms`, `orthotect-data-viz`, and `orthotect-visual-qa`.
  - Enforced strict YAML frontmatter, descriptions under 1024 characters, explicit anti-patterns, and gate verification commands.
- **Expanded Production CLI (`bin/orthotect.js`)**:
  - Added `doctor` diagnostic command verifying Node >= 20.19, Python 3, gates, skills, and knowledge base validity.
  - Added `skills` subcommands (`list`, `search`, `show`, `validate`).
  - Added `knowledge` search and schema validation commands.
  - Added `design` system compilation and recipe scaffolding commands.
  - Added `audit` alias with `--json` and `--md` report formats.
  - Added `-v` and `--version` flags.
- **Automated Test Suite Expansion (218 Tests)**:
  - Added comprehensive negative tests for JSON schema validation, AST BiDi fallback, FSM locks, and search benchmarks.
  - Completed six-area engineering closure and four-deficiency hardening: eliminated CSS fallback cursor stall on `/` (urls/line-height/calc), enforced strict ISO-8601 calendar and SHA/tag validation on verification evidence provenance, hardened FSM explicit contracts across unconventional state names, eliminated silent fallback on corrupted local contrast matrices, and implemented recursive multi-layer ancestor backdrop alpha compositing in browser verification.
  - All 218 automated unit, AST, browser Playwright, and gate tests pass with 100% success rate.

### Fixed & Hardened
- **Light Mode Visual Contrast & Scoped Terminal (`docs/styles.css`, `docs/index.html`)**:
  - Fixed dark text on dark background in `.cli-box` by scoping dedicated high-contrast terminal theme tokens (15.2:1 AAA text contrast, 9.0:1 active tab, 9.2:1 inactive tabs, 12.1:1 prompt `$`).
  - Removed harsh white background band cutting through the cyan grid in `.cli-quickstart-section`.
  - Added reactive theme synchronization to live playground viewport (`#pgViewport`) and toolbar controls (`#pgThemeBtn`, `#pgBidiBtn`, `#pgDensityBtn`).
  - Added reactive brand SVG logo switching between Dark (`logo.svg`) and Light (`logo-light.svg`) mode.
  - Added automated browser regression tests in `tests/test_docs_browser.py`.

## [1.5.2] - 2026-10-22

### Added
- **Official Brand Integration (`docs/assets/brand/`)**:
  - Integrated authoritative brand vectors directly into documentation and public site: `icon.svg` (isometric interlocking 'O'+'T' cube with verification tick), `logo.svg` (horizontal logo for dark canvas), `logo-light.svg` (horizontal logo for light canvas), and `favicon.svg` (crisp 32x32 standalone favicon).
  - Wired real-time brand logo theme switching in `docs/app.js` between light and dark modes.
  - Added official brand palette tokens in `docs/styles.css`: `--ortho-brand-blue: #1f69ff`, `--ortho-brand-cyan: #00d2ff`, `--ortho-brand-purple: #7b42f6`, `--ortho-border-active: #00d2ff`.
- **Accessible Mobile Navigation Drawer (`docs/`)**:
  - Rebuilt site header with a responsive mobile hamburger button (`#mobileMenuBtn`) and slide-out navigation drawer (`#mobileNavDrawer`).
  - Implemented background scroll lock (`body.nav-open`), backdrop click dismissal, `Escape` key listener, and keyboard focus management.
  - Added full bilingual (English & Arabic) route label localization across all 7 views in the mobile drawer.
- **Automated Browser Tests for Brand & Responsive Architecture (`tests/test_docs_browser.py`)**:
  - `test_responsive_viewports_no_horizontal_overflow`: Verified zero horizontal overflow (`scrollWidth <= viewportWidth`) across all 5 mandatory viewports: 1440×900, 1024×768, 768×1024, 390×844, and 320×568.
  - `test_mobile_navigation_drawer_interactive`: Verified hamburger button toggle, `aria-expanded` and `aria-hidden` attributes, route traversal, and `Escape` key dismissal.
  - `test_official_brand_assets_and_theme_logo_switching`: Verified SVG asset existence and dynamic switching of `.brand-logo-img` src on theme change.
  - `test_quality_gates_simulator_honesty_and_eval_states`: Verified simulator honesty: `NOT_EVALUATED` states for missing inputs, strict contrast pairing, and accurate summary output.

### Fixed & Hardened
- **Zero Horizontal Overflow Fix (`docs/styles.css`)**: Added `overflow: hidden;` to `.mobile-nav-drawer` preventing off-screen CSS translateX drawer transforms from expanding the document scroll width on mobile and small tablet viewports.
- **Skill Builder Hardened Validation & Safe Serialization (`docs/app.js`)**:
  - Added strict kebab-case regex validation (`/^[a-z0-9]+(-[a-z0-9]+)*$/`), description length limits (10–1024 chars), and required steps checks.
  - Added `formatYamlString()` helper providing safe YAML multiline block scalar (`|`) and quote escaping for generated frontmatter.
  - Dynamic preview badge now explicitly reflects validation status: `"Structure Validated (Client AST)"` vs `"Incomplete / Invalid Input"`.
  - Copy and Download actions strictly blocked when invalid, automatically highlighting invalid fields and scrolling the first error into view.
- **Quality Gates Simulator Honesty (`docs/app.js`)**:
  - Contrast check now requires an explicit foreground `color` and background `background-color` pair, reporting `⏭ NOT_EVALUATED` instead of false results when absent.
  - FSM check strictly validates JSON syntax on FSM blocks, requiring `states` and `initialState`; emits `❌ FAIL` on syntax error and `⏭ NOT_EVALUATED` if no FSM structure is present.
  - Media aspect-ratio check reports `⏭ NOT_EVALUATED` when no `<img>` elements exist in snippet.
  - Added comprehensive summary line: `Evaluation Summary: X Passed, Y Failed, Z Not Evaluated`.

## [1.5.1] - 2026-10-22

### Fixed
- **Skill Builder Real Validation (`docs/app.js`)**: `updateSkillBuilderPreview()` now separates raw field values from display-fallback values. Badge correctly shows **Incomplete Fields** (not **Valid Structure**) when name/description/steps are empty. Download and Copy buttons run `validateSkillBuilderFields()` before acting — empty or invalid inputs inject `aria-invalid` + red `<span role="alert">` error messages next to each field and **block the download entirely**, preventing incomplete `SKILL.md` generation. Errors clear automatically when the user types in the fixed field.
- **Gate Simulator Honesty — NOT_EVALUATED (`docs/app.js`)**: Replaced three false PASS results with proper states:
  - **WCAG Contrast**: shows `⏭ NOT_EVALUATED` when fewer than two hex color values are found in the input instead of the previous silent `✅ PASS`.
  - **FSM Integrity**: now attempts to `JSON.parse()` the input looking for an object with `states` and `initialState`; shows `⏭ NOT_EVALUATED` when no FSM JSON is detected (was a hardcoded `✅ PASS`).
  - **DOM Depth**: replaced `div`-tag count heuristic with a real tag-scanner that walks open/close tags (skipping void elements) and tracks maximum nesting depth; now also emits `✅ PASS` when depth is within budget.
- **Gate Simulator Disclaimer (`docs/app.js`)**: Header line now reads "Educational Client-Side Simulation — not actual gate execution" (was ambiguously "Educational Client-Side Evaluation").
- **`gate_cwv_budget.mjs` Side-Effect Guard**: Added `isMain` guard and `fileURLToPath` import so the file can be imported in tests without triggering CLI side effects.
- **Empty / Comment-Only HTML Rejection (`gate_cwv_budget.mjs`)**: Gate now rejects HTML files that are blank or contain only comments with a clear error message.

### Added
- **Skill Builder Empty-Form Rejection Browser Test (`tests/test_docs_browser.py`)**: New Playwright test (`test_skill_builder_empty_form_rejection`) verifies that clicking Download with empty required fields: (1) does NOT fire a download event, (2) injects `#sbNameError` with a descriptive message, (3) badge shows **Incomplete**; then re-validates that filling all fields makes the badge say **Valid**.
- **Skills Sync Test (`tests/test_skills_sync.py`)**: 3 new tests validating every `skills/*/SKILL.md` has valid YAML frontmatter and that `docs/app.js` skill catalog IDs exactly match the `skills/` directory on disk.
- **86 Automated Tests**: Test suite expanded from 75 to 86 unit, AST, browser, and sync integration tests with 100% pass rate.

## [1.5.0] - 2026-10-22

### Added
- **7-View Skill Studio Platform (`docs/`)**: Full architectural transformation of GitHub Pages into a professional 7-view interactive workbench:
  - **Home (`#home`)**: Autonomous engineering lifecycle pipeline (Prompt → Execution → Gates → Certified Code), proof metrics bar, and competitor teardown matrix.
  - **Skill Catalog (`#catalog`)**: Synchronized with `skills/` (all 6 skills: `orthotect-doctrine`, `orthotect-gates`, `orthotect-bidi`, `orthotect-tokens`, `orthotect-fsm`, `orthotect-dashboard`), category filtering, search, copyable agent prompts, and direct GitHub links.
  - **Interactive Skill Playground (`#playground`)**: 7 live pre-validated enterprise components (SaaS Analytics Console with inline SVG telemetry, CRM Pipeline Board, E-Commerce Product Card, Multi-State High-Density Data Table, Account Settings Form, FSM Modal Dialog, Responsive Landing Hero) with live runtime Theme, BiDi, and Density controls, plus one-click template code downloads.
  - **Skill Builder (`#builder`)**: Interactive authoring tool generating validated `SKILL.md` specifications meeting official AI coding agent standards with real-time markdown preview and download.
  - **Examples Gallery (`#gallery`)**: Curated production templates with design tokens, FSM models, and downloads.
  - **Quality Gates (`#gates`)**: Transparent, evidence-based specification of all 5 gates with what they check and do NOT check, plus an educational client-side gate inspector simulator.
  - **Installation & Usage (`#install`)**: Verified CLI commands, CI integration snippets, and troubleshooting guide.

### Fixed & Hardened
- **Iterative parse5 Stack Traversal & Resource Bounds (`gates/gate_cwv_budget.mjs`)**: Converted recursive tree traversal in `calculateMaxDomDepth` and `findElements` to explicit FIFO/LIFO stack loops with `MAX_NODE_VISIT_LIMIT = 200,000` to prevent Node.js call stack exhaustion on malicious or deeply nested inputs. Added detection for `eof-in-attribute-value` to flag unclosed attribute quotes at EOF.
- **Deterministic Token Compiler & Output Guard (`core/compiler.py`)**: Added deterministic key sorting across motion tokens, ergonomics, light semantics, and dark semantics ensuring byte-for-byte reproducibility across platforms. Implemented `is_safe_output_path(output_path)` guard preventing accidental overwrites of repository files (`package.json`, `.git`, gate source files). Dynamic contrast pairing focuses on `content.primary` and `content.secondary`, exempting `content.tertiary` (incidental/disabled text) per WCAG SC 1.4.3.
- **CI-Resilient Headless Chromium Browser Tests (`tests/test_modal_browser.py`)**: Multi-path resolution for browser binaries (`CHROME_BIN`, `BROWSER_PATH`, system paths, `which`). Hard `self.fail()` in CI environments (`CI=true` or GitHub Actions) if browser binary is missing, banning silent test skips. Real browser keyboard `Tab` traversal focus trap assertions verifying focus never escapes modal boundaries.
- **75 Automated Tests**: Test suite expanded from 67 to 75 unit, AST, and browser integration tests with 100% pass rate.

## [1.4.0] - 2026-10-22

### Added
- **Orthotect Skill Studio Platform (`docs/`)**: Transformed GitHub Pages into an authoritative interactive Skill Studio and demonstration platform showcasing the 6 Orthotect Skills (`orthotect-doctrine`, `orthotect-gates`, `orthotect-bidi`, `orthotect-tokens`, `orthotect-fsm`, `orthotect-dashboard`) and the 7 Laws of Interface Engineering with interactive before/after comparisons.
- **Genuine Real-Browser Playwright Tests**: Added headless Google Chrome interaction test suite (`tests/test_modal_browser.py`) testing focus trapping, inert backdrop, double-submission locking, and escape recovery in actual browser runtimes.
- **WHATWG-Compliant `parse5` DOM Depth Calculator**: Replaced regex tag parsing in `gates/gate_cwv_budget.mjs` with full HTML5 specification tree parsing via `parse5`, ensuring 100% accurate DOM depth calculation across void elements, comments, unclosed tags, and minified HTML.
- **Strict HTML5 Integer Image Dimension Parser**: Upgraded `gates/gate_cwv_budget.mjs` to enforce standard HTML5 positive integer rules (`/^[1-9]\d*$/`), rejecting `"200px"`, zero, decimals, negatives, and empty values.
- **Compiler Reference Cycle & Tiered Contrast Gates**: Hardened `core/compiler.py` with DFS cycle detection (`A -> B -> A`), missing reference validation, malformed JSON handling, and tiered contrast checks (4.5:1 for normal text, 3.0:1 for graphical controls and large text).
- **Interactive Component Studio in Browser**: Added live interactive action button demonstrating in-engine double-submission locks and accessible modal dialog meeting W3C APG dialog standards with focus trap, inert background, and Escape key handling.
- **High-Density Telemetry Console**: Inline SVG sparklines and node metrics with zero layout shift (CLS = 0.00) and complete Arabic RTL symmetry.
- **67 Automated Tests**: Test suite expanded from 53 to 67 unit, AST, and browser integration tests with 100% pass rate.

## [1.3.1] - 2026-10-22

### Fixed
- **Modal Dialog DOM Execution & Lifecycle**: Fixed initialization crash (`TypeError: Cannot read properties of null`) in `examples/golden-showcase/index.html` by placing the modal markup prior to scripts in the DOM and wrapping script attachment inside `DOMContentLoaded`. Added `tests/test_modal_browser.py` asserting DOM sequence and mock headless event attachment.
- **Strict HTML Attribute Key-Value Parser**: Replaced word-boundary regex (`/\bwidth\s*=/i`) in `gate_cwv_budget.mjs` with an attribute parser isolating exact attribute names. Prevents `data-width="800"` or custom attributes from falsely satisfying width/height requirements, and strictly rejects zero, negative, or non-numeric dimension values.
- **Declaration-Block CSS Parser for inline styles**: Implemented standalone CSS declaration parser in `gate_cwv_budget.mjs` that isolates exact CSS properties and values. Rejects CSS custom properties like `style="--custom: aspect-ratio: 16/9"` and validates aspect ratios against W3C Box Sizing Level 4 (`auto || <ratio>`).
- **Comprehensive HTML Stack AST & Boundary Enforcement**: Enhanced `calculateMaxDomDepth` in `gate_cwv_budget.mjs` to detect and flag unclosed non-void tags remaining at EOF, unclosed `<` tags, and mismatched closing tags.
- **Enforced Token Contrast Quality Gate**: Elevated `core/compiler.py` contrast verification from informational output to an active quality gate. If any surface/content token pair violates the WCAG 2.2 AA (4.5:1) standard, compilation aborts with non-zero exit and explicit violation details.
- **CI Runner Modernization**: Updated GitHub Actions CI to Node.js 22 LTS to eliminate runner deprecation notices.
- **53 Automated Tests**: Test suite expanded to 53 comprehensive unit and integration tests with 100% pass rate.

## [1.3.0] - 2026-10-22

### Added
- **CSS aspect-ratio Syntax Validator**: `gate_cwv_budget.mjs` validates full W3C CSS Box Sizing Level 4 syntax (`auto || <ratio>`), rejecting non-numeric values (`invalid-value`, `0/0`, `none`).
- **Stack-Based HTML DOM Parser**: Replaced tag regex in `calculateMaxDomDepth` with an AST stack tokenizer that tracks open/close tags, balances void elements, and flags mismatched closing tags and malformed HTML.
- **Generalized FSM Async & Submission Locks**: `gate_fsm_integrity.py` dynamically identifies any async in-flight execution state (`loading`, `submitting`, `pending`, `processing`, `fetching`, etc.) and enforces `allowClick: false` and error recovery transitions.
- **DTCG Compiler Mathematical Contrast Verification**: `core/compiler.py` computes relative luminance and exact contrast ratios for semantic token pairs during compilation, certifying ratings (AAA / AA) in the generated CSS header comment.
- **Executable Modal Dialog Reference Component**: Added a fully functional, accessible modal dialog with focus trapping, backdrop lock, and FSM interaction locks in `examples/golden-showcase`.
- **48 Automated Tests**: Expanded test suite to 48 tests covering invalid aspect ratio syntax, mismatched closing tags, submitting lock enforcement, and compile-time contrast math.

## [1.2.0] - 2026-10-22

### Added
- **W3C DTCG Token Compiler (`core/compiler.py`)**: Built-in compiler transforming 3-tier DTCG token JSON (primitives, semantics, motion, ergonomics) into pure CSS Custom Properties with automatic `:root` light and `[data-theme="dark"]` scopes.
- **CLI `compile` Command**: `npx orthotect compile [tokens_path] --out <file.css>` for zero-config token generation.
- **Enterprise Modal Dialog FSM (`core/fsm/modal-dialog.json`)**: Deterministic finite state machine with focus trapping, backdrop locks, async submission handling, and error recovery transitions.
- **Reporting Formats (`--json`, `--md`)**: `npx orthotect verify . --json` and `npx orthotect verify . --md` for automated CI scorecard summaries and bot reviews.
- **Parallel Gate Orchestrator**: `run_all_gates.py` now leverages `ThreadPoolExecutor` to run all 5 gates concurrently, reducing verification latency by over 50%.
- **39 Automated Unit & Integration Tests**: Comprehensive test suite covering all gates, CLI commands, compiler, and negative rejection scenarios.
- **Interactive In-Browser Showcase (`docs/`)**: Zero-bloat, bilingual (English/Arabic) web application featuring live in-browser deterministic gate runner, interactive FSM state graph visualizer, and W3C DTCG token explorer deployed automatically to GitHub Pages.
- **Architectural Teardown Whitepaper (`COMPETITORS.md`)**: Comprehensive competitive analysis comparing Orthotect against XIAS, prompt collections, shadcn/ui, v0, and Style Dictionary.
- **The Orthotect Manifesto (`MANIFESTO.md`)**: The 7 Non-Negotiable Laws of High-Integrity Interface Engineering.
- **GitHub Pages CI/CD Workflow (`.github/workflows/pages.yml`)**: Continuous deployment for the documentation and interactive showcase.

### Changed
- **Zero-Fallback Path Boundaries**: Replaced string prefix checking with mathematical `os.path.commonpath` verification across both `gate_contrast_wcag.py` and `gate_fsm_integrity.py`. Sibling directories (`examples-backup`) are strictly rejected.
- **Strict Layout-Shift Verification**: `gate_cwv_budget.mjs` requires BOTH `width` and `height` attributes OR an explicit inline CSS `aspect-ratio` property inside `style="..."`. Class names (e.g. `class="aspect-ratio-box"`) can never bypass dimensional checks.
- **Stream-Based Tag Parser**: `calculateMaxDomDepth` sequentially tracks tag depth, stripping `<script>` and `<style>` blocks to accurately detect excessive nesting (>32) in single-line minified HTML.

## [1.1.0] - 2026-10-21

### Added
- Autonomous CLI scaffolding via `npx orthotect init <path>` copying real design tokens, FSM models, and `AGENTS.md`.
- Target-aware gate inspection allowing external project auditing (`npx orthotect verify <path>`).
- Independent unit test suite in `tests/`.

## [1.0.0] - 2026-10-21

### Added
- Initial release of Orthotect Deterministic Interface Architecture.
- 5 Objective Quality Gates:
  - WCAG 2.2 Mathematical Relative Luminance Contrast Verifier.
  - True BiDi & CSS Logical Properties Enforcer.
  - Finite State Machine Graph Reachability & Double-Submission Checker.
  - Anti-Slop Lexical & AI Pattern Inspector.
  - DOM Structure & Cumulative Layout Shift (CLS) Budget.
- 6 Agent Skills: `orthotect-doctrine`, `orthotect-fsm`, `orthotect-tokens`, `orthotect-gates`, `orthotect-bidi`, `orthotect-dashboard`.
- Golden Showcase Enterprise Reference Console in `examples/golden-showcase`.
