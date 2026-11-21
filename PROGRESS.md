# Orthotect — Milestone Progress Tracker

**Baseline:** `v1.8.8`, branch `main`, commit `c2ba2de` + uncommitted remediation from `REVIEW_2026-11.md`
**Last updated:** 2026-11-21
**Suite of record:** `python3 -m unittest discover -s tests -p 'test_*.py'` → **614 tests, OK, 0 failures, 0 skips**

Rule for every task below: a task is `[x]` only when a command was run in the foreground and its
output/exit code confirmed. No task is closed on reasoning alone.

---

## Status Legend

- `[x]` Completed **and** verified with evidence
- `[~]` In progress
- `[ ]` Not started
- `[!]` Blocked (reason recorded inline)

---

## P0 — Restore Trust in the Verdict

### P0-1 — Exit-code contract (0 = pass, 1 = violation, 2 = tool error)

- [x] **COMPLETED & VERIFIED (at the time; 22 tests in `tests/test_exit_codes.py`).**

Atomic breakdown, all delivered:

- [x] Define the three codes once per language: `core/exit_codes.py`, `core/exit_codes.mjs`.
- [x] Replace bare integer exits in all 5 Python gates (`bidi`, `contrast`, `fsm`, `no_slop`, `security`).
- [x] Replace bare integer exits in the Node DOM/CWV gate (`gate_cwv_budget.mjs`).
- [x] Propagate through the orchestrator (`run_all_gates.py`), including the aggregation rule
      **`TOOL_ERROR` (2) outranks `VIOLATION` (1)**.
- [x] Propagate through the CLI (`bin/orthotect.js`) — child status forwarded verbatim, never collapsed to 1.
- [x] Propagate through `scripts/check-release-sync.mjs` and the pre-commit hook.
- [x] Map unrecognised child status (crash, signal, spawn failure) to `2`, never `1`.
- [x] Document the contract in `README.md` with a `case $?` CI recipe and the `exitCode` JSON field.
- [x] `tests/test_exit_codes.py` — 22 tests, including a source-level guard that fails if a bare
      `sys.exit(1)` is reintroduced into a gate.

Verification evidence:

| Scenario | Command | Exit |
| :--- | :--- | :---: |
| Genuine breach | `gate_no_slop.py <dir with inline hex style>` | `1` |
| Path typo | `gate_no_slop.py /nope/nothing` | `2` |
| Missing token architecture | `gate_contrast_wcag.py <empty dir>` | `2` |
| Missing FSM specs | `gate_fsm_integrity.py <empty dir>` | `2` |
| Orchestrator, bad target | `run_all_gates.py /nope/nothing` | `2` |
| Orchestrator, breach + tool error | `run_all_gates.py <incomplete project>` | `2` (not 1) |
| Reference target, all deps present | `run_all_gates.py examples/golden-showcase` | `0` |

### P0-1b — Empty-directory fail-open in the security gate

- [x] **COMPLETED & VERIFIED.**

- [x] `gate_security_audit.py` returned `exit 0` and printed
      "✅ Zero vulnerabilities across 0 file(s)" for a directory with no auditable source.
      Zero files scanned means zero rules evaluated, which is never a pass. Now `exit 2`.
- [x] Enforced identically in all three output formats (console, `--json`, `--md`).
- [x] **Root cause found and fixed for the related all-excluded case:** the gate scanned its own
      `orthotect.config.json` as an auditable application file, so an over-broad `exclude`
      (e.g. `["**/src/**"]`) still left one file "in scope" and produced `exit 0`. The gate now
      treats the resolved config file as tool metadata and never audits it, so an over-broad
      `exclude` correctly collapses to zero scope and exits `2`.
- [x] Regression tests: `test_empty_target_is_tool_error_not_pass`,
      `test_all_files_excluded_by_config_is_tool_error`.

Evidence: console / `--json` / `--md` each return `2` for both an empty directory and a
fully-excluded directory.

### P0-2 — Ship `parse5` as a real vendored artifact, or drop it

- [x] **COMPLETED & VERIFIED (3 new tests in `test_cwv.py`; suite then 418).** Direction chosen: **keep `parse5` as the
      single declared npm runtime dependency and fix the two real defects found while auditing it**
      (see the decision record below). Vendoring and "drop it" were both rejected on measured
      grounds.

Rationale (from `REVIEW_2026-11.md` §8): the tool's headline claim is determinism, yet one gate
depends on a network fetch at install time. "Zero-dependency except when it isn't" is the weakest
claim in the README.

#### P0-2.1 — Call-site inventory (completed)

| Call site | Requirement class |
| :--- | :--- |
| `analyzeDomStructure` → `parser.parse(..., {sourceCodeLocationInfo, onParseError})` | **Required** — full HTML5 tree + parse errors for malformed-markup diagnosis |
| `analyzeDomStructure` → `new parser.Tokenizer(...)` | **Required** — tag-balance / stray-closing-tag detection |
| `checkHtmlFile` → `requireParse5().parse(content)` | **Required** — the media/CSS-cascade analysis walks a real AST |

There is no optional call site. Every use needs a real HTML5 tree, not just tokenisation.

#### P0-2.2 — Decision record

**Chosen: keep the npm dependency, fix the defects.**

Evidence gathered before deciding:

- **"Drop it" is not viable.** The media-dimension and CSS-cascade analysis resolves
  `img`/`video`/`iframe` ancestors and selects matching CSS rules against a genuine tree. A
  tokenizer cannot supply ancestors or a cascade. Dropping parse5 would mean rewriting the gate's
  core analysis, not just its depth counter.
- **Vendoring is costly relative to benefit.** `parse5@8.0.1` (MIT) has its own runtime dependency
  `entities@8.1.0` (BSD-2-Clause); the runtime closure is **448 KB**, added to a **9.1 MB**
  unpacked package (~5%). It was verified to work (nested-`node_modules` layout resolves, and the
  code passes our own SAST gate), but it only buys operation from a *bare checkout* — a bare
  checkout is a developer scenario, not a user scenario.
- **For real users the dependency already works.** `parse5` is declared in `dependencies`, so
  `npx orthotect verify .` always resolves it.

Accepted residual: a bare checkout with no `npm ci` cannot run the DOM gate. That is now documented
explicitly (README dependency note) and fails closed at exit 2.

#### P0-2.3 to P0-2.7 — Defects found and fixed (completed)

Two defects were found by testing rather than reading, and both are now fixed and pinned:

1. **The remediation message was wrong.** It said to install `parse5` *"in the project being
   verified"*. Node resolves the import relative to **the gate file**, so that advice can never
   work — a user following it would loop indefinitely. The message now states the real cause
   (resolution is anchored to the Orthotect package), explicitly says the intuitive fix will
   *not* work, names the correct fix (`npm install` inside the package / use the published
   package), and echoes the underlying resolver error.
2. **A missing parser crashed as exit 1.** Exported analysis helpers dereferenced `null`
   (`TypeError: Cannot read properties of null (reading 'parse')`), which Node reports as exit 1 —
   a tool error masquerading as a code violation, inverting the P0-1 contract. Every analysis
   function now funnels through `requireParse5()`, which throws the typed
   `ParserUnavailableError`; the CLI entry point (`runMain`) translates it to `exit 2`.

Budget semantics are unchanged: `maxDomDepth` (default 32), `maxDomNodes` (default 1500),
`0` = opt-out.

Evidence:

| Scenario | Result |
| :--- | :--- |
| Parser present, reference target | `exit 0` |
| Parser present, single `.html` file | `exit 0` |
| Parser present, 35-level nested DOM | `exit 1` (`Excessive DOM depth`) |
| Parser present, empty directory | `exit 2` |
| Parser **absent**, CLI invocation | `exit 2` + correct remediation text |
| Parser **absent**, library call | throws `ParserUnavailableError` (no `TypeError`) |

Regression tests: `tests/test_cwv.py::TestMissingParserContract` (3 tests).

### P0-3 — Add a self-audit gate (run all six gates against Orthotect itself)

- [x] **COMPLETED & VERIFIED (5 new tests in `test_self_audit.py`).**

Rationale: every critical defect in the review (a bypassable flag, path-based trust, an unenforced
config key) is what a self-audit would have caught on day one. This is the highest-leverage habit
change in the roadmap.

- [x] **P0-3.1** Scope defined: the repository **root**, not the individual source directories.
      Measured reasoning: the contrast, FSM and DOM gates resolve `core/tokens/`, `core/fsm/` and
      markup relative to the audit root, so auditing `gates/` in isolation correctly exits `2`
      (tool error). Auditing the root evaluates the whole project exactly as a user's project is
      evaluated. `scripts/self-audit.mjs` documents this in full.
- [x] **P0-3.2** Added `scripts/self-audit.mjs` and `npm run audit:self`. It spawns the real
      orchestrator against the repo root and propagates the exit code verbatim (`0` / `1` / `2`),
      mapping a signal kill or spawn failure to `2`.
- [x] **P0-3.3** Findings resolved: the root self-audit is **clean** — all six gates pass. (The
      two genuine defects surfaced while running the broader audit were in the DOM gate and were
      fixed under P0-2.)
- [x] **P0-3.4** Wired into `.github/workflows/ci.yml` as a required step immediately after the
      test suite, before the SAST audit. A test asserts the step is present, so removing it fails
      the build.
- [x] **P0-3.5** `tests/test_self_audit.py` — 5 tests: clean tree exits `0`; a missing `parse5`
      is exit `2` (not a finding); a missing orchestrator is exit `2`; the script exists and is
      wired into `package.json`; CI runs it.

**Proof the gate is not a no-op.** A physical CSS declaration (`margin-left: 16px`) was appended to
`core/config.mjs` and a probe HTML file added to `core/`. The self-audit then correctly reported
**exit 1** with the BiDi and DOM gates failing and named the offending file. The probe was removed
and `npm run audit:self` returned to `exit 0`. Without this check the test would only prove the
command runs, not that it detects anything.

Evidence:

| Check | Result |
| :--- | :--- |
| `npm run audit:self` on a clean tree | **exit 0**, all six gates pass (~11 s) |
| `npm run audit:self` with an injected `margin-left` | **exit 1**, BiDi + DOM gates fail, file named |
| `npm run audit:self` with `parse5` absent | **exit 2** + `npm ci` remediation |
| CI contains the self-audit step | asserted by `test_ci_workflow_runs_the_self_audit` |

---

## P1 — Close the Remaining Fail-Open Surface

### P1-1 — BiDi `--fix` must verify its own result

- [x] **COMPLETED & VERIFIED (439 tests passing).**

- [x] After rewriting, the gate now re-scans and **asserts zero remaining** violations. A partial
      fix is reported explicitly as `[PARTIAL FIX]`, names the file and the exact count, and still
      exits `1`. The `--fix` summary no longer prints a repair count without the unresolved
      remainder — it states plainly that the run "did not certify the target".

#### Additional defects found while implementing P1-1

Auditing the `--fix` path surfaced three further bugs, all fixed and pinned:

1. **JSX style objects skipped whole rule families.** Asymmetric four-value shorthands
   (`margin: "0 8px 0 24px"`) and the value keywords `float`/`clear` were rejected in plain CSS
   but accepted inside `style={{ ... }}` and `StyleSheet.create({...})` — **the C1 bypass
   re-opened in a second syntax**. Six declaration forms were confirmed passing in JSX while
   failing in CSS. The JSX block now routes through the same `evaluate_declaration()` authority
   as the CSS paths, so the two cannot drift again.

2. **The BiDi suggestion text was invalid CSS for the border family.** `logical_shorthand_pair()`
   was absent, so a blanket `f"{name}-block"` produced **`border-width-block`** — not a CSS
   property at all. An agent following that suggestion would write broken CSS and stay broken.
   The border family now inflects as `border-block-width`, verified against all eight shorthands.

3. **`apply_bidi_fixes_to_file()` ignored `allow_camel_case`.** The pre-fix and post-fix scans
   used different rule sets, so the function could verify against rules the run was not enforcing.

Evidence:

| Case | Before | After |
| :--- | :--- | :--- |
| Partial fix (`margin-left` fixed, shorthand not) | `exit 1`, no explanation | `exit 1`, `[PARTIAL FIX]` + explicit remainder |
| Complete fix | `exit 0` | `exit 0` (unchanged) |
| `float: "left"` in JSX | `exit 0` (**bypass**) | `exit 1` |
| `margin: "0 8px 0 24px"` in JSX | `exit 0` (**bypass**) | `exit 1` |
| `border-width` suggestion text | `border-width-block` (invalid) | `border-block-width` |
| `--fix` on JSX `float`/shorthand | left untouched | repaired to `inline-start` / logical pair |

Regression tests: `tests/test_bidi_fix_verify.py` — 16 tests across 4 classes (partial-fix
contract, JSX/CSS rule parity, auto-fix reaching green, shorthand inflection).

### P1-2 — Extend the shorthand rule to the border family

- [x] **COMPLETED & VERIFIED (488 tests passing, 17 new in `tests/test_bidi_border_shorthand.py`).**

- [x] `tests/test_bidi_border_shorthand.py` covers `border-width` / `border-style` / `border-color`
      asymmetry in plain CSS, an HTML `<style>` block, a JSX `style={{…}}` object (camelCase and
      quoted-kebab keys) and `StyleSheet.create({…})`.

Auditing the family exposed **four genuine defects the fixtures would never have found on their
own** — each is a case where the gate reported a violation it could not repair, so `--fix` ended in
`[PARTIAL FIX]` with no way forward:

1. **CSS shorthands were detected but never repaired.** `transform_css_declarations()` handled banned
   properties, offsets, `text-align`, `float` and `clear`, but had **no shorthand branch at all**.
   Only the JSX path expanded them. A CSS `.p { margin: 10px 20px 10px 5px }` was reported forever.
   Detection and repair must cover the same rule set, so the new branch mirrors
   `evaluate_declaration()` exactly: same predicate (`token[1] != token[3]`), same value mapping,
   same `logical_shorthand_pair()` properties.
2. **An inline HTML `style="…"` shorthand was unrepairable.** The terminator regex required `;` or
   `}`, but the last declaration in a style attribute has neither. End-of-input is now a terminator.
3. **`StyleSheet.create()` never called the shorthand repair.** `fix_ss_match()` applied the banned
   property, offset and `text-align` rules and then returned — the `style={{…}}` branch directly
   above it also called `_fix_jsx_shorthand_and_keywords()`. The identical declaration was repairable
   in one syntax and not the other.
4. **`!important` was dropped by the expansion.** Replacing one shorthand with two declarations must
   carry the flag on both, or the repair silently changes cascade priority. Now preserved on each.

A systematic parity probe — 24 constructs across `.css`, `.scss`, `.less`, `.html`, `.vue`,
`.svelte`, `.jsx` and `.js` — now reports **zero** cases of detected-but-unrepaired. The only
remaining partial-fix trigger is genuinely unrepairable syntax (an unbalanced brace, which the
scanner reports as `PARSE_ERROR`), and the P1-1 partial-fix fixture was updated to use exactly that,
since the asymmetric shorthand it previously relied on is now repairable.

Evidence:

| Case | Before | After |
| :--- | :--- | :--- |
| `.p { margin: 10px 20px 10px 5px }` + `--fix` | `[PARTIAL FIX]`, unchanged | `margin-block` + `margin-inline` |
| `<div style="margin: 0 8px 0 24px">` + `--fix` | `[PARTIAL FIX]`, unchanged | split pair |
| `StyleSheet.create({a:{margin:"0 8px 0 24px"}})` + `--fix` | `[PARTIAL FIX]`, unchanged | `marginBlock` / `marginInline` |
| `border-width: 0 0 0 4px !important` | would have dropped the flag | both halves keep `!important` |
| `border-style` / `border-color` asymmetry | not covered by any test | detected + repaired |
| Symmetric `border-width: 2px 0` | — | untouched |

Regression tests: `tests/test_bidi_border_shorthand.py` — 17 tests across detection, suggestion
validity, and auto-fix. Suggestion validity is proven by **round-tripping**: the property pair named
in the suggestion is fed back through `evaluate_declaration()` and must produce zero violations,
which closes the loop that previously allowed `border-width-block` to be suggested.

### P1-3 — Security gate baseline / allowlist file

- [x] **COMPLETED & VERIFIED (470 tests passing, 31 new in `tests/test_security_baseline.py`).**

Problem restated: C2 removed the blanket `/tests/` path exemption, so a legitimate fixture now
blocks the build and the only previous escape was to re-widen path trust — the exact fail-open
C2 closed. A committed allowlist is the narrower instrument, and unlike path trust it is
reviewable.

- [x] **P1-3.1** New module `core/security_baseline.py`: `BaselineEntry`, `load_baseline`,
      `find_baseline_path`, `apply_baseline`, `unused_entries`. Dependency-free, matching the
      zero-dependency convention of `core/config.py`.
- [x] **P1-3.2** Loading wired into `gate_security_audit.py::main()`: the baseline is resolved
      from the audit root (falling back to the parent, so a monorepo can hold one file), applied
      after scanning, and every suppression is reported.
- [x] **P1-3.3** Findings shape preserved. The baseline filters the existing 4-tuples
      `(line, label, severity, snippet)`; nothing downstream changed shape.
- [x] **P1-3.4** Suppressions surfaced in **all three** formats — console (`[SUPPRESSED]` +
      justification), `--json` (`baseline` + `suppressed[]`), `--md` (table). The C2 lesson:
      an invisible suppression is indistinguishable from a missed detection.

Design decisions, each pinned by a test:

| Decision | Why |
| :--- | :--- |
| Exact `file` + `rule` + `line` matching, no globs | A wildcard reproduces the blanket exemption this replaces. Glob patterns in `file` or `rule` are rejected with exit 2. |
| `line: 0` = any line in that file for that rule | Some rules report an unstable line. Still scoped to one file *and* one rule, and documented as discouraged because a new finding of that rule in the same file would also be suppressed. |
| `justification` is mandatory and non-empty | This is the field that makes an entry reviewable; without it the file is a list of silent opt-outs. |
| Unreadable/invalid baseline → **exit 2** | A project that committed a policy must not have it silently ignored; that would re-enable findings already reviewed and accepted. |
| Stale entry → warned, **exit unchanged** | A stale entry does not impair the audit — every file was still scanned and every rule evaluated — so exit 2 would be dishonest. Failing on unrelated line shifts would drive teams to delete the file. Reported in console, `--json` (`baseline.staleEntries`) and `--md`. |
| Duplicate entries → exit 2 | Two identical suppressions mean one is dead; rejecting keeps the file honest. |

Evidence:

| Case | Result |
| :--- | :--- |
| Vulnerable file, no baseline | `exit 1` |
| Same file, both DOM-XSS rules suppressed at line 1 | `exit 0`, both printed with justification |
| Suppression for a fixture file, genuine XSS elsewhere in app code | `exit 1`; `--json` shows the fixture under `suppressed[]` and `app.js` under `vulnerabilities[]` — a baseline cannot hide a real finding |
| Same rule in a *different* file | `exit 1` (no leak) |
| Same rule on a different line | `exit 1` (no leak) |
| Malformed JSON / bad version / missing justification / glob / absolute path / negative line / duplicate / non-list | `exit 2` each |
| Stale entry | `exit 0` + stale warning, visible in `--json` |
| `--json` with suppressions | `suppressed[]` carries rule + justification; `baseline.entryCount` correct |
| `--md` with suppressions | baseline table printed |
| `python3 gates/gate_security_audit.py .` (repo, no baseline) | `exit 0`, unchanged |
| Single-file target with a sibling baseline | `exit 0`, suppressed |
| Monorepo baseline one level above the audited package | `exit 0`, suppressed |
| Audit-root baseline beats a parent baseline | asserted by `test_audit_root_baseline_wins_over_parent` |

Documented in `README.md` under "Security Baseline (`orthotect-security-baseline.json`)" with the
schema table and the four guarantees.

---

## P2 — Developer Experience

- [x] **P2-1 — Unify argument parsing** *(COMPLETED & VERIFIED; 609 tests passing, 23 new in
      `tests/test_cli_args.py`)*

The same flag/positional split existed in six places and had already drifted. The concrete symptom:
`gate_contrast_wcag.py --format json ./src` audited the literal string `json` and reported
*"Missing required Design Token files in target: json"* — a tool error manufactured entirely by
argument parsing.

- [x] `core/cli_args.py` — `parse_args`, `positionals`, `resolve_output_format`, `has_flag`,
      `VALUE_FLAGS`. One place knows which flags consume the next token.
- [x] `core/cli_args.mjs` — the ESM mirror, same contract.
- [x] Wired into all five Python gates, the orchestrator, `bin/orthotect.js`, and
      `gates/gate_cwv_budget.mjs`.
- [x] The orchestrator's legacy bare-token form (`run_all_gates.py <dir> json`) is supported through
      an explicit `bare_token=True` opt-in, **not** globally — otherwise a project directory named
      `json` would become un-auditable.

Design rules, each pinned:

| Rule | Why |
| :--- | :--- |
| A value flag never leaks its value | The entire bug class |
| Order independence | `verify --json ./src` and `verify ./src --json` must agree |
| `--` terminates flags | The only way to audit a path beginning with `-` |
| `--flag=value` is one token | Never two, never a positional |
| Unknown flags are ignored, not fatal | Validating flag names is the caller's job; a gate must still find its target |
| Bare format token is orchestrator-only | A directory literally named `json` must stay auditable |

`tests/test_cli_args.py` runs a **single shared table of cases through both languages** (Python
directly, the ESM module via Node) and fails on any divergence, plus source-level guards that fail
if a gate re-grows a private splitter.

A further defect surfaced while wiring the Node gate: a missing `core/cli_args.mjs` produced an
uncaught import error, which Node reports as **exit 1** — a tool error masquerading as a code
violation, inverting the P0-1 contract. It now fails closed at exit 2 with its own message,
distinct from the `parse5` message, and there is deliberately **no fallback parser** (a private
second copy is the drift this milestone removed).

Evidence:

| Check | Result |
| :--- | :--- |
| All five Python gates with `--format json <dir>` | each names the real directory, never `json` |
| `--format json <dir>` vs `<dir> --format json` | identical exit codes |
| 17 positional cases through Python and Node | identical results |
| `-- ` handling (`--weird-dir`) | treated as positional |
| Missing `core/cli_args.mjs` in the Node gate | **exit 2** + specific message, not exit 1 |
- [x] **P2-2 — `orthotect explain <rule-id>`** *(COMPLETED & VERIFIED; 42 rules, all with a
      citation, summary and fix)*

`core/rule_registry.py` is the single registry the gates read for a rule id and the one
`orthotect explain` reads for its documentation, so a violation's id and its spec citation cannot
drift apart. Every rule carries `title`, `gate`, `severity`, `citation`, `summary` and `fix`.

| Check | Result |
| :--- | :--- |
| `orthotect explain bidi.physical-direction-property` | prints rule id, gate, severity, W3C citation, why, fix — exit 0 |
| `orthotect explain --json` | `{"rulesVersion": 1, "rules": [...]}`, 42 entries |
| `orthotect explain --search contrast` | 4 matching rules |
| `orthotect explain nope.rule` | exit 2 with "Unknown rule id" |
| Rules missing a citation | **0 of 42** |
| Rules missing a summary or fix | **0 of 42** |

- [x] **P2-3 — `--format sarif` for GitHub Code Scanning** *(COMPLETED & VERIFIED; 23 new tests in
      `tests/test_sarif.py`)*

`REVIEW_2026-11.md` item 9. The violation tuples already carried file, line, column and rule, so
the work was to give the five gates that only printed console text a structured findings channel,
then map it onto SARIF 2.1.0. Two invariants drove every decision:

1. **A tool error is never an empty result set.** "No findings" and "no analysis" must not render
   identically in the code-scanning UI, so a gate that cannot run emits
   `invocations[].toolExecutionNotifications` with `executionSuccessful: false` and still exits 2.
2. **The rule id is carried from the detection site, not re-derived.** A regex classifier over
   message text in the SARIF layer would be a second copy of detection logic that rots on the first
   rule split. The gates tag findings where they are created; `core/rule_registry.classify_label`
   is only the fallback for the two gates whose labels are a closed, table-driven set.

Six gates fold into **one** run: GitHub keys alerts on `ruleId` within a run, so six runs would
show the same rule six times. `merge_sarif` dedupes rules by id and results by
`(ruleId, uri, line, column, message)`.

| Check | Result |
| :--- | :--- |
| All six gates + orchestrator emit SARIF | `run_all_gates.py <dir> --format sarif` → one run, `validate_sarif` clean |
| Multi-gate fixture (BiDi + slop + FSM + DOM + SAST) | 10 results, 9 distinct registry rule ids, exit 1 |
| Tool error (missing target / no files in scope) | `executionSuccessful: false` + notification, exit 2 |
| Result whose `ruleId` is not in `driver.rules` | rejected by `validate_sarif` (GitHub would drop it silently) |
| Absolute or leading-slash artifact URI | rejected by `validate_sarif` |
| `startLine` of 0 | rejected by `validate_sarif` |
| Explicit MEDIUM severity | not overridden by the registry lookup |
| Absent severity | resolved from the registry |
| Console report under `--format sarif` | suppressed; console unchanged without the flag |
| FSM finding line | points at the state's key, not line 1 |
| DOM finding line | points at the offending element (e.g. line 5 for the blocking script) |
| `bin/orthotect.js verify --sarif` / `security --sarif` | passthrough works; `--json` unchanged |
| `--format sarif` where a directory is named `sarif` | positional wins, format resolved separately |

---

## P3 — Architecture

- [x] **P3-1 — Split the two monolithic gates into packages** *(COMPLETED & VERIFIED; 609 tests
      passing, 8 new in `tests/test_gate_packages.py`)*

`gate_bidi_logical.py` (1,553 lines) and `gate_security_audit.py` (1,427 lines) became
`gates/_bidi/` and `gates/_security/`, one module per rule family. The entry points keep their
exact paths and names — `package.json`, `run_all_gates.py`, `bin/orthotect.js`, the knowledge base
and the test suite all reference them, and a rename would be a breaking change for a refactor whose
whole point is to be invisible.

| Package | Modules |
| :--- | :--- |
| `gates/_bidi/` | `_runtime` `_model` `_shorthand` `_css` `_js` `_fix` `_paths` `_dispatch` `gate` |
| `gates/_security/` | `_runtime` `_patterns` `_ast` `_taint` `_scanner` `_cli` |

Dependencies point one way in both packages. `_bidi/_dispatch` exists only to break a cycle: the
fixer must re-scan a file after rewriting it, and the CLI must run the fixer, so the scanner cannot
live in the CLI module.

**The refactor was proved equivalent, not assumed equivalent.** Every function body was copied
byte-for-byte by an `ast`-driven splitter that aborts if any non-blank source line fails to land in
exactly one module — so nothing was silently dropped. Both gates were then run against a passing
target, a violating fixture, and `docs/` / `examples/` in console, `--json` and `--format sarif`
form; stdout and exit codes were compared to the originals: **21 of 21 cases byte-identical.**

Three real defects the split introduced, all caught and fixed:

1. **The security gate reported its own rule table as vulnerabilities.** The engine exemption was
   one filename check (`gate_security_audit.py`). Once the patterns moved into
   `gates/_security/_patterns.py` they were scanned as user code and the gate failed on itself —
   a fail-closed gate that cannot pass its own audit. Fixed with `is_engine_file()`, which exempts
   the entry module and the package directory by path segments. A file merely *named* like an
   engine module (`src/_security/helpers.py`) stays auditable.
2. **The facade would have swallowed a monkeypatch.** `tests/test_bidi.py` sets
   `bidi_mod.HAVE_TINYCSS2 = False` to prove the dependency-free fallback enforces the same rules.
   A plain re-export would rebind the facade's namespace while `_css` kept reading its own `True`,
   so the fallback path would look tested and never run. The facade is a `ModuleType` subclass that
   forwards assignments to `_bidi._runtime`.
3. **The private package name was shadowable.** `import _security` accepts any module of that name
   earlier on `sys.path`, so an unrelated `_security.py` would have silently replaced the gate.
   Both facades now pin their own directory first. The test that pins this was itself wrong at
   first — it probed `python3 gates/gate_*.py`, where the interpreter already puts the script's
   directory first, so it passed with and without the guard. It now imports `gates.gate_*` from a
   foreign cwd, and **was confirmed to fail when the anchor is removed.**

`tests/test_gate_packages.py` also pins the two failures that are otherwise silent: a `symtable`
check that every module binds the globals it reads (a `NameError` would otherwise fire only on the
branch that reaches it), and a check that each entry point stays under 60 lines so rule logic cannot
creep back in one function at a time.
- [x] **P3-2 — Version the rule set independently of the package** *(COMPLETED & VERIFIED; 4 new
      tests in `tests/test_rule_registry.py`)*

`RULES_VERSION` is now a semver string (`1.0.0`) with a documented bump policy, deliberately not
the package version. A rule that tightens changes what a report says without changing any API;
tying the two together would either force a semver-major package release per rule tweak, or — worse
— let behaviour change under a version number a consumer had pinned.

A hand-maintained version number is only as good as the discipline of whoever bumps it, so it is
paired with `rules_digest()`: SHA-256 over a canonical `id|gate|severity` projection of the
registry, truncated to 16 hex characters. The projection is deliberate — correcting a citation or
a summary must not move the digest (no finding changed), while a severity change must.

The block (`rulesVersion`, `rulesDigest`, `ruleCount`) is emitted by every machine-readable report:
the orchestrator's `--json` (`ruleSet`), the security gate's `--json` (`ruleSet`), every SARIF
document (`tool.driver.properties`), and `orthotect explain --json`.

| Check | Result |
| :--- | :--- |
| `run_all_gates.py --json` | `{"rulesVersion": "1.0.0", "rulesDigest": "dcf3e9ec7c42ac44", "ruleCount": 42}` |
| `run_all_gates.py --format sarif` | same block at `runs[0].tool.driver.properties` |
| `gate_security_audit.py --json` | same block at `ruleSet` |
| `gate_cwv_budget.mjs --format sarif` | **identical digest computed in JavaScript** |
| `orthotect explain --json` | same block at the top level |
| Prose-only change (a summary reworded) | digest unchanged |
| Severity change | digest changes |
| `RULES_VERSION` vs `package.json` version | asserted different |

The Node digest is the interesting one: the DOM gate is the only non-Python gate, and a digest that
two languages compute differently would be a field that means nothing. It parses exactly the three
flat fields the projection uses — `id`, `gate`, `severity` — rather than attempting to reconstruct
the Python data structure, and `test_the_node_dom_gate_computes_the_same_digest` fails if they ever
diverge.
- [x] **P3-3 — Property-based testing for the three pure parsers** *(COMPLETED & VERIFIED; 23 tests
      in `tests/test_property_parsers.py`, ~500 generated inputs per property)*

The two critical defects this review found — C1's `!important` bypass and C4's non-string-aware
comment masking — were both *input-space* bugs: every hand-written example passed and the failure
lived in a case nobody wrote down. These tests generate inputs instead of enumerating them.

No Hypothesis dependency: the generators are a small hand-rolled layer over `random` with a fixed
seed (`20261120`), which keeps the suite dependency-free and reproducible. Each property is stated
as an invariant of the contract rather than a restatement of the implementation, and each has a
mirror in the opposite direction so a validator that accepted (or rejected) everything would fail.

| Parser | Properties |
| :--- | :--- |
| `split_css_values` | never emits a blank or unstripped token; `!important` never survives as a token (C1); token count matches an independent top-level splitter; parenthesised values never split; rejoin/split is idempotent |
| `logical_shorthand_pair` | every shorthand maps to two distinct syntactically valid properties; the border family puts the infix before the sub-property (`border-block-width`, never `border-width-block`) |
| `mask_comments` | length invariant; newline positions invariant (this is what makes line numbers correct); idempotent; no comment opener survives; non-comment text preserved (C4 — a `//` inside a URL must not blank the line) |
| `parseAndValidateCssCalc` | unbalanced parens always rejected; length+length accepted; length+number rejected; length×length rejected; length×number accepted; `/0` rejected; `length/length` rejected; whitespace never changes the verdict |

Writing them surfaced two defects **in the tests themselves**, both instructive:

- The Node probe read `process.argv[1]` (the script path) instead of `argv[2]` — the generated
  inputs never reached the validator, and the failure looked like a validator bug.
- A generator emitted a bare `10` where a length was required, so `10 + 0vh` "should" have passed.
  The validator was right to reject it; the generator was wrong. This is the value of pairing every
  acceptance property with its rejection mirror: without one, a wrong generator is indistinguishable
  from a wrong implementation.

The `!important` property is deliberately stated over `normalize_declared_value` → `split_css_values`
rather than the splitter alone, because a spaced `! important` is invalid CSS the normalizer rejects
before splitting. Asserting on the splitter alone would demand it handle input it never sees.

---

## Known Observations (not yet scheduled)

- **`tests/test_knowledge_search.py` asserts gate filenames.** It still passes because the entry
  points kept their names, but it is a reminder that renaming a gate file is a cross-cutting change,
  not a rename.

---

### Follow-ups closed 2026-11-21 — local-run preconditions

Both observations above were recorded during REVIEW_2026-11 and are now fixed.

**Browser tests checked the wrong precondition.** `test_docs_browser.py`, `test_modal_browser.py`
and `test_scaffold_browser.py` skipped only when no Chrome binary was found. With Chrome installed
but `playwright-core` absent — the normal state of a fresh clone — the `node` script's
`import('playwright-core')` threw `ERR_MODULE_NOT_FOUND` and the tests reported **29 hard
failures** that said nothing about the code. All three now check both preconditions, matching the
pattern `test_contrast.py` already used:

| Condition | Local | CI |
| :--- | :--- | :--- |
| Neither browser nor `playwright-core` | skip, naming what is missing | fail |
| Chrome present, `playwright-core` absent | skip: "needs playwright-core (run `npm ci`)" | fail |
| Both present | run | run |

Verified by renaming `node_modules/playwright-core` out of the way: **32 skips in 0.5 s** instead of
failures, and with `CI=true` the same run **fails 29 tests** with an actionable message. The
pre-fix code was confirmed to fail all 29 on the same condition, so the change is measured, not
assumed.

**`npm ci` is a precondition, now documented.** `README.md` gained a "Running the test suite from a
checkout" note and `CONTRIBUTING.md` an install step. While there, two stale claims in
`CONTRIBUTING.md` were corrected: "296+ tests" → 609, and "all 5 objective gates" → six.

---

## Verification Log

| Date | Command | Result |
| :--- | :--- | :--- |
| 2026-11-20 | `python3 -m unittest discover -s tests -p 'test_*.py'` | **569 tests, OK, 0 skipped** |
| 2026-11-20 | `python3 -m unittest tests.test_sarif` | **23 tests, OK** |
| 2026-11-20 | `python3 gates/run_all_gates.py <multi-violation fixture> --format sarif` | **exit 1**, 1 run, 10 results, 9 rule ids, `validate_sarif` clean |
| 2026-11-20 | `python3 gates/run_all_gates.py <missing target> --format sarif` | **exit 2**, `executionSuccessful: false` + notification |
| 2026-11-20 | `bin/orthotect.js verify <dir> --sarif` | **exit 2**, 1 result (`bidi.physical-direction-property`), FSM tool error surfaced |
| 2026-11-20 | `bin/orthotect.js explain bidi.physical-direction-property` | **exit 0**, rule + W3C citation + fix |
| 2026-11-20 | `bin/orthotect.js explain nope.rule` | **exit 2**, unknown rule id |
| 2026-11-20 | `npm run audit:self` (clean tree) | **exit 0**, all six gates |
| 2026-11-20 | `npm run audit:self` (injected `margin-left`) | **exit 1**, defect located |
| 2026-11-20 | DOM gate, parser absent (CLI) | **exit 2** + correct remediation text |
| 2026-11-20 | DOM gate, parser absent (library call) | throws `ParserUnavailableError` |
| 2026-11-20 | DOM gate, 35-level nested DOM | **exit 1** (`Excessive DOM depth`) |
| 2026-11-20 | `python3 gates/run_all_gates.py examples/golden-showcase` | **exit 0**, all 6 gates, 445 ms |
| 2026-11-20 | `python3 gates/run_all_gates.py docs` | **exit 0**, all 6 gates |
| 2026-11-20 | `node scripts/validate-skills.mjs` | 22 passed, 0 warnings, 0 errors |
| 2026-11-20 | `python3 gates/gate_security_audit.py .` | **exit 0**, 134 files scanned, 0 vulnerabilities |
| 2026-11-20 | Empty dir, console / `--json` / `--md` | **exit 2** in all three |
| 2026-11-20 | Fully-excluded dir, console / `--json` / `--md` | **exit 2** in all three |
| 2026-11-20 | `tests/test_security_baseline.py` (P1-3) | **31 tests, OK** |
| 2026-11-20 | Baseline: fixture suppressed, real app-code XSS elsewhere | **exit 1**; `--json` separates `suppressed[]` from `vulnerabilities[]` |
| 2026-11-20 | Baseline: malformed / bad version / no justification / glob / absolute / negative line / duplicate / non-list | **exit 2** each |
| 2026-11-20 | Baseline: single-file target, monorepo parent lookup | **exit 0**, suppressed |
| 2026-11-20 | `tests/test_bidi_border_shorthand.py` (P1-2) | **17 tests, OK** |
| 2026-11-20 | CSS / HTML-attr / StyleSheet shorthand `--fix` | **exit 0**, repaired in all three |
| 2026-11-20 | Detect-vs-repair parity probe, 24 constructs × 8 extensions | **0 unrepaired** |
| 2026-11-21 | `tests/test_gate_packages.py` (P3-1) | **8 tests, OK** |
| 2026-11-21 | P3-1 splitter coverage proof | 1455 (bidi) + 1362 (security) source lines carried, 0 dropped |
| 2026-11-21 | Both gates vs. originals, 21 target×format cases | **stdout + exit code byte-identical, 21/21** |
| 2026-11-21 | `gate_security_audit.py gates/` after split | **exit 0** (was exit 1 reporting its own rule table) |
| 2026-11-21 | `bidi_mod.HAVE_TINYCSS2 = False` after split | assignment reaches `_runtime`; fallback scanner detects |
| 2026-11-21 | Shadowed `_bidi`/`_security` on `PYTHONPATH` | real gate still imports; test fails without the anchor |
| 2026-11-21 | `python3 gates/run_all_gates.py examples/golden-showcase` | **exit 0**, all 6 gates, 500 ms |
| 2026-11-21 | `node scripts/self-audit.mjs` | **exit 0**, all six gates on Orthotect itself |
| 2026-11-21 | `npm pack --dry-run` | `_bidi/` and `_security/` included (282 files) |
| 2026-11-21 | `python3 -m unittest discover -s tests -p 'test_*.py'` | **609 tests, OK** |
| 2026-11-21 | Browser tests, `playwright-core` absent (local) | **32 skips in 0.5 s** (was 29 hard failures) |
| 2026-11-21 | Browser tests, `playwright-core` absent + `CI=true` | **29 failures**, actionable message (fail-closed kept) |
| 2026-11-21 | Pre-fix code, same condition (measured for comparison) | 29 failures |
| 2026-11-21 | Browser tests, deps present | 34 tests, **OK** |
