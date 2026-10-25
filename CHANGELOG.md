# Changelog

All notable changes to the Orthotect Interface Architecture are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.5] - 2026-10-25

### Fixed
- **Sanitizer Property Mutation & Overwrite Detection (`gates/gate_security_audit.py`)**:
  - Implemented `mutation_pattern` in `resolve_trusted_sanitizers()` to detect direct property assignments (`DOMPurify.sanitize = ...`, `DOMPurify['sanitize'] = ...`), root object reassignments (`DOMPurify = ...`), and mutation helpers (`Object.assign(DOMPurify, ...)`, `Object.defineProperty(DOMPurify, ...)`).
  - Any local property overwrite or object mutation targeting trusted sanitizers immediately strips the affected sanitizer from `trusted`, eliminating false trust bypasses.
- **Expanded Dangerous DOM XSS Sinks (`gates/gate_security_audit.py`)**:
  - Expanded `sink_pattern` and `INJECTION_PATTERNS` to track `.insertAdjacentHTML(position, html)`, `iframe.srcdoc = html`, and `Range.createContextualFragment(html)` across both direct pattern matching and intra-file taint flow analysis.
- **Block-Level Sequential Statement Splitting (`gates/gate_security_audit.py`)**:
  - Removed `brace_depth` suppression on semicolons in `split_statements()`. Semicolons inside `{ ... }` now correctly delimit executable statement boundaries, ensuring single-line blocks (e.g. `function render() { const raw = location.search; element.innerHTML = raw; }`) are parsed into sequential sub-statements where taint assignment is recorded before sink consumption.
- **Accurate Scope Filtering & Transparent Reporting**:
  - Explicitly excluded the gate runner itself (`gate_security_audit.py`) from `files_to_scan` to prevent self-referential false positives, standardizing the active audit scope to exactly **132 scannable application source files** across local CLI and GitHub Actions CI.
- **Test Suite Expansion**:
  - Added 7 new negative and positive security regression unit tests in `tests/test_security_gate.py` (total 59 security tests), bringing total repository tests to **355 Automated Tests** (100% pass rate).
- **Ecosystem Synchronization**:
  - Synchronized version `1.8.5` across all 28 repository files, tokens, style recipes, and docs.

## [1.8.4] - 2026-10-25

### Fixed
- **Zero-Trust for In-File Function Sanitizers & Anti-Shadowing Resolver (`gates/gate_security_audit.py`)**:
  - Completely replaced text-matching heuristics (`has_entity_escaping()`) with strict Zero-Trust: any locally declared function, variable, or class shadowing a sanitizer identifier (`sanitizeHtml`, `escapeHTML`, `DOMPurify`, etc.) is immediately disqualified from the trusted set.
  - Bare sanitizers (`sanitizeHtml`, `escapeHTML`, `escapeHtml`) are ONLY trusted when explicitly imported from vetted packages (`sanitize-html`, `escape-html`).
  - Base trusted sanitizers strictly scoped to audited namespaces: `DOMPurify.sanitize`, `validator.escape`, `he.encode`.
- **Multi-Variable Comma-Separated Declarations Parser (`gates/gate_security_audit.py`)**:
  - Added `split_comma_declarations()` with string literal, parenthesis, bracket, and brace depth tracking to decompose comma-separated declarators (e.g., `const raw = location.search, clean = raw;`).
  - Ensures intra-statement taint propagation across intermediate variable declarations in single statements without false splits on nested expressions or object literals.
- **Accurate SAST Scope Specification & CI Precision**:
  - Clarified CI step description and documentation to accurately report "Eligible Application Source Files" (133 files), explicitly distinguishing scanned application source files from test fixtures, CI workflows, and non-scannable infrastructure files.
- **Test Suite Expansion**:
  - Added 4 new negative and positive security regression unit tests in `tests/test_security_gate.py` (total 52 tests), bringing total repository tests to **348 Automated Tests** (100% pass rate).
- **Ecosystem Synchronization**:
  - Synchronized version `1.8.4` across all 28 repository files, tokens, style recipes, and docs.

## [1.8.3] - 2026-10-25

### Fixed
- **Loop Header Statement Splitting & Unbraced Body Tracking (`gates/gate_security_audit.py`)**:
  - Hardened `split_statements()` with parenthesis (`()`), bracket (`[]`), and brace (`{}`) depth tracking. Semicolons inside `for (...)` loop headers (`for (let i = 0; i < 1; i++)`) no longer split the loop header from its body, ensuring loops on the same line are accurately identified as conditional statements.
  - Added pending conditional tracking for multi-line control statements (`for`, `if`, `while`, `else`) without braces, ensuring unbraced loop/conditional bodies do not clear variable taint.
- **Sanitizer Trust Model & Anti-Shadowing Resolver (`gates/gate_security_audit.py`)**:
  - Implemented `resolve_trusted_sanitizers(content)`: detects and rejects local dummy or identity functions (e.g. `const escapeHTML = value => value` or `const DOMPurify = { sanitize: x => x }`).
  - Required verified HTML entity escaping logic (`&amp;`, `&lt;`, regexes, textContent) or explicit external imports for custom sanitizer identifiers.
  - Excluded `encodeURI` and `encodeURIComponent` from HTML sink sanitizers because URI encoding does not neutralize HTML entities for DOM XSS sinks (`innerHTML`, `outerHTML`, `document.write`).
- **Standardized SAST Scannable Scope**:
  - Added `.agents` and `skills-lock.json` to ignored SAST scope, guaranteeing identical file counts (exactly 133 files) across local environments and shallow CI checkouts.
- **Test Suite Expansion**:
  - Added 5 new negative and positive security tests in `tests/test_security_gate.py` (total 48 tests), bringing total repository tests to **344 Automated Tests** (100% pass rate).
- **Ecosystem Synchronization**:
  - Synchronized version `1.8.3` across all 28 repository files, tokens, style recipes, and docs.

## [1.8.2] - 2026-10-25

### Fixed
- **Branch-Aware Taint Flow Tracking (`gates/gate_security_audit.py`)**:
  - Implemented conservative branch sensitivity: safe variable reassignments inside conditional blocks (`if`, `else`, `switch`, `case`, `catch`, loops) do NOT clear taint, preventing false negatives on conditional paths (`if (cond) { msg = "safe"; }`).
  - Added sequential statement parsing (`split_statements`) to accurately evaluate multiple statements on a single line separated by semicolons (`const raw = location.search; element.innerHTML = raw;`).
  - Narrowed trusted sanitizer whitelist to proven HTML sanitizers (`DOMPurify.sanitize`, `escapeHTML`, `encodeURIComponent`, `validator.escape`, `he.encode`), eliminating false trust on custom objects or bare methods (`validator.sanitize`).
  - Expanded security suite to 43 automated unit tests and repository total to **339 tests** (100% pass rate).
- **Exit Code 2 for Unverified Release Checks (`scripts/check-release-sync.mjs`)**:
  - Updated release synchronization script to exit with code `2` when remote publication checks cannot be verified in offline/sandboxed environments, preventing automated pipelines from misinterpreting unverified runs as exit code 0.
- **Ecosystem Synchronization**:
  - Bumped version to `1.8.2` across package metadata, tokens, styles, docs, and lockfile to ensure synchronized publication on GitHub Packages.

## [1.8.1] - 2026-10-25

### Fixed
- **Taint Analysis Mixed-Expression Hardening (`gates/gate_security_audit.py`)**:
  - Implemented balanced-parenthesis sanitizer masking (`mask_sanitizers`) supporting arbitrary nesting depths.
  - Closed mixed-expression taint bypass where partially sanitized compound expressions (`DOMPurify.sanitize(raw) + raw`) bypassed detection.
  - Added automatic taint state clearing upon variable re-assignment to fully sanitized or static values (`raw = DOMPurify.sanitize(raw)`), eliminating false positives.
  - Added 4 new dedicated unit tests covering mixed assignments, mixed direct sinks, and reassignment clearing (expanding security suite to 39 tests).
- **Fail-Safe Release Synchronization & Truthful Reporting (`scripts/check-release-sync.mjs`)**:
  - Differentiated between verified, unverified (offline/sandboxed), and failed checks.
  - Returns explicit `[UNVERIFIED]` status for remote checks when network is inaccessible, preventing false claims of 100% parity outside CI.
- **Package Registry Parity**:
  - Bumped version to `1.8.1` across repository, tokens, styles, docs, and lockfile to ensure published GitHub Packages artifact matches the final commit.

## [1.8.0] - 2026-10-25

### Added
- **Gate 6: Enterprise Full-Stack Cybersecurity & Threat Audit (`gates/gate_security_audit.py`)**:
  - Zero-dependency AST and lexical SAST scanner enforcing OWASP Top 10 and CWE Top 25 defenses across Python and Node.js.
  - Detects SQLi, OS Command Injection, NoSQL Injection, SSTI, DOM XSS, Prototype Pollution, Insecure PostMessage, and SSRF.
  - Features recursive environment file scanning (`.env`, `.env.local`, `.env.production`) and intra-file lexical taint tracking.
  - Dedicated CLI command: `npx orthotect security [path]`.
- **Skill 22: Autonomous Security Defense (`skills/orthotect-security`)**:
  - Full Agent Skills Specification compliance with deep reference guides (`owasp-top-10.md`, `injection-vectors.md`, `security-checklist.md`, `frontend-security.md`, `backend-security.md`).
- **Universal Vercel Skills Manifest (`skills.sh.json`)**:
  - Added official Vercel Skills CLI package distribution defining 9 curated skill bundles for `npx skills add seotarek/orthotect`.
- **Law 8: Zero-Trust Cybersecurity Defense in `AGENTS.md`**:
  - Added mandatory security defense law to the core Interface Engineering Laws.
- **Architectural Superiority Whitepaper (`ARCHITECTURAL_SUPERIORITY.md`)**:
  - 16-dimensional benchmark analyzing Orthotect vs. Anthropic Superpowers, Vercel skills.sh, UX/UI Expert Skills, and Prompt-only Skills.

### Changed
- Refactored YAML deserialization checks to AST-based inspection verifying `Loader=SafeLoader` or `yaml.SafeLoader` with zero false positives.
- Calibrated security report assertions to reflect exact static analysis boundaries and intra-file taint tracking.
- Expanded automated unit test suite to 323 passing tests.

## [1.7.4] - 2026-10-24

### Added
- **Auto-Healing Engine (`--fix`)**:
  - Implemented automated remediation in `gates/gate_bidi_logical.py`, `gates/run_all_gates.py`, and `bin/orthotect.js` via `npx orthotect verify [path] --fix`.
  - Automatically transforms prohibited physical declarations (`margin-left` → `margin-inline-start`, `paddingRight` → `paddingInlineEnd`, `text-align: left` → `text-align: start`, `float: right` → `float: inline-end`, `clear: left` → `clear: inline-start`) into standard W3C CSS Logical Properties in-place.
  - Comment- and string-protected state machine preserves original formatting, whitespace, comments, and strings across CSS, HTML, Vue, Svelte, JSX, and TSX files.
  - Added dedicated verification suite in `tests/test_auto_fix.py`.
- **Git Pre-Commit Hook Integration (`npx orthotect hooks install|uninstall`)**:
  - Implemented one-click Git pre-commit hook installation in `bin/orthotect.js` writing an executable `.git/hooks/pre-commit` script.
  - Blocks non-compliant commits before they can reach branches, prompting with automated `--fix` guidance.
  - Added safety checks for non-git directories and clean uninstallation in `tests/test_hooks_cli.py`.
- **Zero-Dependency Configuration Engine (`orthotect.config.json`)**:
  - Implemented dual Python (`core/config.py`) and Node.js (`core/config.mjs`) configuration engines with upward directory search and deep merging.
  - Supports custom file exclusion patterns (`exclude: [...]`), customized DOM nesting depth ceilings (`cwv: { maxDomDepth: 32 }`), and gate toggles.
  - Integrated into `gates/gate_bidi_logical.py`, `gates/gate_cwv_budget.mjs`, and `gates/run_all_gates.py`.
  - Added full test coverage in `tests/test_config.py`.
- **Universal Release Version Synchronization**:
  - Synchronized CLI package fallback in `bin/orthotect.js` to `1.7.4`.
  - Synchronized canonical contrast matrix specifications (`core/tokens/contrast-matrix.json` and `examples/golden-showcase/...`) to `1.7.4`.
  - Synchronized verification revision tags across all 12 UI/UX style recipes in `knowledge/styles/*.json` to `v1.7.4`.
  - Updated SEO gallery generator (`scripts/generate_seo_gallery.py`) and regenerated all 50 standalone production HTML templates (`docs/templates/*.html`) with `v1.7.4` terminal bars and changelog entries.

## [1.7.3] - 2026-10-23

### Added
- **Marketingskills Interface Engineering Capabilities Integration**:
  - `skills/orthotect-cro`: Interface Conversion Rate Optimization (CRO) skill focusing on primary CTA visual hierarchy, form friction elimination, 48px minimum touch targets, sticky mobile bars, and FSM submit locks.
  - `skills/orthotect-schema`: Semantic Structured Data & Schema.org JSON-LD engineering with unified `@graph` architecture, visible page content alignment, and rich snippet templates.
  - `scripts/validate-skills.mjs`: Agent Skills Specification validator enforcing YAML frontmatter delimiters, directory/name match, trigger descriptions, 500-line progressive disclosure, and reference file integrity.
  - `scripts/package_skills.py`: Deterministic cross-agent portable skill packager generating reproducible ZIP bundles with fixed epoch (1980-01-01), LICENSE inclusion, and SHA-256 manifests.
  - `tests/test_skill_evals.py` & `evals/evals.json`: Evaluation fixtures verifying positive/negative trigger cases and deterministic assertions.
  - `tests/test_skill_packaging.py`: Unit tests verifying reproducible byte-for-byte ZIP generation and manifest integrity.
  - Catalog and CLI synchronization: Expanded Orthotect modular disciplines from 16 to 18 in `docs/app.js` and `bin/orthotect.js`, and hooked specification validation into `npx orthotect skills validate`.
- **Multi-Agent Orchestration & Agentic Engineering Integration**:
  - Formalized the **Command → Agent → Skill** architecture across `AGENTS.md`, `CLAUDE.md`, and `README.md`, binding autonomous coding agents (Antigravity, Claude Code, Cursor, Codex, Grok) to deterministic engineering.
  - Defined the 5-phase agent lifecycle: **Research → Plan → Execute → Review → Ship**, with strict foreground verification gates and zero unbacked metric assertions.
  - Enforced strict Git Hygiene and privacy policies prohibiting conversational disclosures, chat history, or personal commentary in repository commits.
- **Universal Release Version Synchronization**:
  - Synchronized CLI package fallback in `bin/orthotect.js` to `1.7.3`.
  - Synchronized canonical contrast matrix specifications (`core/tokens/contrast-matrix.json` and `examples/golden-showcase/...`) to `1.7.3`.
  - Synchronized verification revision tags across all 12 UI/UX style recipes in `knowledge/styles/*.json` to `v1.7.3`.
  - Updated SEO gallery generator (`scripts/generate_seo_gallery.py`) and regenerated all 50 standalone production HTML templates (`docs/templates/*.html`) with `v1.7.3` terminal bars and changelog entries.

### Fixed
- **Semantic Chunking & Strict Token Budget Accounting (`core/context_optimizer.py`)**:
  - Enforced strict `max_tokens` ceiling across all chunk outputs by calculating and reserving token overhead for continuation breadcrumbs (`// [Context Continuation: ... | chunk #N]`).
  - Implemented single-line oversized isolation ensuring that only an indivisible single line can exceed `max_tokens`.
  - Implemented hierarchical scope tracking with `context_path: [...]`, nested boundary decomposition (`split_strategy: 'nested_boundary' | 'line_window'`), and explicit `oversized_scope: {name, type, start_line, end_line}` metadata.
  - Compound structures (classes with multiple methods) are partitioned strictly at member method boundaries, preserving method closures and local scopes.
  - Preserved template literal expression `${...}` brace balance and nesting depth during lexical code masking in `mask_js_code()`.
- **Lexical Scanning & Ghost Declaration Elimination (`core/context_optimizer.py`)**:
  - Implemented `mask_js_code()` state machine masking line/block comments, quotes, regex literals, and template strings outside `${...}`, eliminating ghost matches while preserving source coordinates.
  - Implemented `_is_regex_start()` for JS/TS `/` token disambiguation against arithmetic division.
  - Implemented collision-free symbol IDs (`{type}_{name}_L{line}_C{col}`) and scope hierarchy tracking.
  - Fixed Python decorator chains (@decorator) staying attached across lines and consecutive functions.
  - Pruned directory recursion with in-place `dirs[:] = []` in `generate_context_skeleton(max_depth)`.
- **Search Central Compliance & Template Grounding (`skills/orthotect-schema`)**:
  - Removed fabricated default ratings and review counts from `skills/orthotect-schema/references/jsonld-templates.md`.
  - Reframed `aggregateRating` as an optional extension component to be added only when genuine, visibly rendered user ratings exist on the page.
  - Aligned `skills/orthotect-schema/SKILL.md` SoftwareApplication requirements strictly with Google Search Central documentation.
- **Skill Packager Security Hardening (`scripts/package_skills.py`)**:
  - Added strict symlink boundary enforcement preventing path traversal and symlink escapes outside the skill root directory.
  - Added byte-level secret scanning rejecting packages containing private keys, SSH keys, or high-entropy credentials (`ghp_`, `AKIA`, `sk-`).
  - Refined sensitive filename regex to distinguish security credentials from legitimate design token files (`design-tokens.md`).
- **Specification Validator Hardening (`scripts/validate-skills.mjs`)**:
  - Expanded license validation to comprehensive standard SPDX license identifiers.
  - Implemented recursive reference file discovery auditing all nested `references/**/*.md` files for dead relative links and broken `#fragment` anchors.
- **Evidence-Based Documentation**:
  - Removed unbacked percentage claims (`95%+` in `skills/orthotect-context/SKILL.md` and `>85%` in `core/context_optimizer.py`).
- **Lockfile Package Metadata Alignment (`package-lock.json`)**:
  - Synchronized package name to `"@seotarek/orthotect"` in `package-lock.json` root and workspace specifier, resolving metadata drift against `package.json`.

### CI & Package Guards
- **Publish Concurrency & Fail-Closed Guards (`.github/workflows/publish-package.yml`)**:
  - Added workflow concurrency group `concurrency: group: publish-package, cancel-in-progress: false` to prevent race conditions during concurrent release events.
  - Restricted package publishing strictly to `github.event_name == 'release'`.
  - Enhanced registry pre-check with fail-closed semantics (`exit 1` on ambiguous registry response) and `E409` conflict error recovery.
- **Package Metadata Consistency Guard (`scripts/check-package-metadata.mjs`)**:
  - Created automated pre-publish check enforcing version and package name alignment across `package.json` and `package-lock.json`.

### Tests
- **BiDi Adversarial Edge Cases (`tests/test_bidi.py`)**:
  - Added adversarial regression tests for escaped slashes, regex character classes, division after calls/expressions, and trailing comment slashes.
- **Context Optimizer Test Suite (`tests/test_context_optimizer.py`)**:
  - Expanded test suite to 21 tests covering lexical masking, scope collisions, Python decorators with tabs, direct `os.walk` spy pruning, and boundary depths.
- **Skills Parity & Sync Suite (`tests/test_skills_sync.py`)**:
  - Expanded tests to verify 18 skills across disk, `docs/app.js`, `bin/orthotect.js`, and verified clean execution of `scripts/validate-skills.mjs`.

## [1.7.2] - 2026-10-23

### Added
- **Context Architecture & Token Optimizer Subsystem (`core/context_optimizer.py` & `skills/orthotect-context/`)**:
  - Implemented zero-dependency context engine featuring calibrated heuristic token estimation, AST-density profiling, and semantic symbol extraction.
  - Added nesting-aware semantic chunking (`semantic_chunk`) decomposing source files along top-level class, function, and component boundaries without severing closure scopes. When large classes exceed token budgets, partitions at nested method boundaries with context continuation breadcrumbs (e.g. `// [Context Continuation: class X | chunk #N]`).
  - Added progressive architectural skeleton generation (`generate_context_skeleton`) with directory traversal depth pruning (`dirs[:] = []` at `depth >= max_depth`), preventing unnecessary filesystem traversals.
  - Authored official autonomous agent skill `orthotect-context` (16 total modular skills certified).
  - Integrated `orthotect context <inspect|chunk|skeleton>` into production CLI and diagnostic doctor.
  - Added unit test suite `tests/test_context_optimizer.py` and CLI E2E tests in `tests/test_cli_expanded.py`.

### Fixed
- **BiDi AST Gate Control Statement Regex Parsing (`gates/gate_bidi_logical.py`)**:
  - Enhanced `is_regex_start()` to disambiguate regular expression literals following statement-header parentheses (e.g., `if (test) /pattern/`, `while (...) /pattern/`, `for (...) /pattern/`, `with (...) /pattern/`, `catch (...) /pattern/`), scanning backward to match the balancing open parenthesis while strictly distinguishing arithmetic division `(a + b) / 2`. Added regression test in `tests/test_bidi.py` (26/26 BiDi tests passing).
- **Semantic Chunking Nesting Integrity (`core/context_optimizer.py`)**:
  - Updated `extract_symbols()` to track lexical nesting depth (`brace_depth` in JS/TS, indentation in Python) and tag symbols with `is_top_level: bool` and `parent: str | None`. Prevented inner class methods and closure functions from being split into isolated, out-of-scope chunks.
- **Directory Traversal Depth Pruning (`core/context_optimizer.py`)**:
  - In `generate_context_skeleton()`, added `dirs[:] = []` when `depth >= max_depth`, avoiding wasteful filesystem traversal into subdirectories beyond the specified depth budget.

### CI
- **Publish Workflow Idempotency (`.github/workflows/publish-package.yml`)**:
  - Added pre-publish registry version check via `npm view` before calling `npm publish`, preventing `E409` duplicate release build errors when workflow dispatch or tags re-run.

## [1.7.1] - 2026-10-23

### Fixed
- **BiDi AST Gate Regex Literal Lexical Parsing**: Disambiguated JavaScript regular expression literals (e.g., `const pattern = /https?:\/\//;`) from line comments in `strip_js_comments_string_aware()` and `extract_tagged_template_literals()` within `gates/gate_bidi_logical.py`. Escaped slashes (`\/`) inside regex literals no longer trigger false comment stripping, preventing physical CSS properties in subsequent code from escaping verification. Added regression tests in `tests/test_bidi.py` (25/25 BiDi tests passing).
- **FSM Scaffolded Page Synthetic Event & State Lock Verification**: Hardened `bin/orthotect.js` and `tests/test_scaffold_browser.py` by adding an explicit action execution counter (`window.__orthotectActionExecCount`). The Playwright browser test now verifies double-click lockout via synthetic DOM event dispatch (`dispatchEvent(new MouseEvent('click'))`) and direct controller calls (`transition('CLICK')`) during the `loading` state, asserting that action execution count strictly remains 1.
- **FSM Scaffolded Page Full Error Recovery Cycle**: Added single-failure error simulation (`simulate=error_once`) in `bin/orthotect.js`. Hardened `tests/test_scaffold_browser.py` to verify the complete error recovery lifecycle in headless Chromium: transitioning from `loading` -> `error`, clicking "Retry Action" to transition back to `loading`, and successfully reaching `success` ("Action Verified") before returning to `idle`.
- **Anti-Slop Button Emoji Boundary Isolation**: Hardened `gates/gate_no_slop.py` button emoji regex with negative boundary lookaheads `(?:(?!</?\1\b)[\s\S])*?` to prevent cross-element multi-button greedy spans. Clean buttons preceding text or paragraphs with emojis are no longer falsely flagged. Escaped mock playground snippet emoji in `docs/app.js` and added regression tests in `tests/test_slop.py` (11/11 Anti-Slop tests passing).

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
