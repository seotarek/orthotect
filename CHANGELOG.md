# Changelog

All notable changes to the Orthotect Interface Architecture are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
