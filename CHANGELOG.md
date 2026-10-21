# Changelog

All notable changes to the Orthotect Interface Architecture are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
