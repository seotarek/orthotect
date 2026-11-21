#!/usr/bin/env python3
"""
Orthotect Rule Registry
=======================

One machine-readable description of every rule the gates enforce, with the
citation that justifies it.

Why this exists
---------------
A gate that says "margin-left is banned" is only half a verdict. The reader needs
to know *why* — which WCAG success criterion, which CSS specification section,
which CWE — or the rule reads as an arbitrary house style and gets argued with
instead of fixed. `orthotect explain <rule-id>` surfaces that citation, and
because the registry is the same object the gates describe, the explanation
cannot drift from the enforcement.

This module deliberately contains **no detection logic**. It is data plus a
lookup. Detection stays in the gates, which remain the single authority on what
fires; the registry is the authority on what a rule *means*.

Rule ids
--------
Stable, kebab-case, prefixed by the gate that owns them:

    bidi.<property>            gate_bidi_logical
    contrast.<check>           gate_contrast_wcag
    fsm.<condition>            gate_fsm_integrity
    slop.<pattern>             gate_no_slop
    dom.<condition>            gate_cwv_budget
    security.<rule>            gate_security_audit

Ids are part of the public surface: they appear in `--format sarif`, in the
baseline file, and in suppression justifications. Renaming one is a breaking
change and requires a `rulesVersion` major bump.

Rule-set versioning
-------------------
`RULES_VERSION` is deliberately **not** the package version. A pattern that
tightens, or a rule that is added, changes what a report says without changing
any API — so tying the two together would either force a semver-major package
release for every rule tweak, or (worse) let behaviour change under a version
number a consumer had pinned.

It is a semver string, so the compatibility signal is explicit:

    major  a rule id was renamed or removed, or an entry's meaning changed
           incompatibly (a consumer's baseline or SARIF filter breaks)
    minor  a rule was added (new findings can appear)
    patch  a detection pattern tightened, or a citation/summary was corrected
           (same rules, better behaviour)

`rules_digest()` additionally fingerprints the whole registry, so a consumer can
verify that two reports came from byte-identical rules rather than trusting a
hand-maintained version number that someone forgot to bump. Both are emitted by
every machine-readable report and by `orthotect explain --json`.
"""

import hashlib
import json as _json

#: Rule-set version. Independent of the package version — see the module docstring
#: for the bump policy.
RULES_VERSION = '1.0.0'


class RuleNotFound(KeyError):
    """Raised when an unknown rule id is requested."""


# Each entry: id -> {title, gate, severity, citation, summary, fix}
RULES = {
    # ---------------------------------------------------------------- BiDi
    'bidi.physical-direction-property': {
        'title': 'Physical direction property',
        'gate': 'gate_bidi_logical',
        'severity': 'HIGH',
        'citation': 'CSS Logical Properties and Values Level 1 (W3C Candidate Recommendation)',
        'summary': (
            'A physical property such as `margin-left` pins a box to the left edge '
            'regardless of writing direction, so the layout breaks when the document '
            'is rendered right-to-left. Logical properties (`margin-inline-start`) '
            'resolve against the inline axis and follow the writing mode.'
        ),
        'fix': 'Replace with the logical equivalent, e.g. `margin-left` -> `margin-inline-start`.',
    },
    'bidi.asymmetric-shorthand': {
        'title': 'Asymmetric four-value shorthand',
        'gate': 'gate_bidi_logical',
        'severity': 'HIGH',
        'citation': 'CSS Logical Properties and Values Level 1, §2 (Flow-relative values)',
        'summary': (
            'The four-value shorthand orders values as top / right / bottom / left, '
            'which is physical. When the inline-start and inline-end values differ, '
            'the asymmetry is baked in and cannot mirror in RTL. `margin: 0 8px 0 24px` '
            'always has 24px on the left, in every direction.'
        ),
        'fix': (
            'Split into the logical pair: `margin-block: <start> <end>` and '
            '`margin-inline: <start> <end>`. The border family inflects differently: '
            '`border-block-width` / `border-inline-width`.'
        ),
    },
    'bidi.text-align-physical': {
        'title': 'Physical text alignment',
        'gate': 'gate_bidi_logical',
        'severity': 'HIGH',
        'citation': 'CSS Text Level 3, §7.1 (text-align: start | end)',
        'summary': (
            '`text-align: left` aligns to the physical left edge. In an RTL document '
            'the text should begin at the right edge, so a physical value silently '
            'misaligns every paragraph.'
        ),
        'fix': 'Use `text-align: start` or `text-align: end`.',
    },
    'bidi.float-physical': {
        'title': 'Physical float direction',
        'gate': 'gate_bidi_logical',
        'severity': 'HIGH',
        'citation': 'CSS Logical Properties and Values Level 1, §3 (float: inline-start | inline-end)',
        'summary': (
            '`float: left` floats toward the physical left edge, which in RTL places '
            'the element on the wrong side of its container.'
        ),
        'fix': 'Use `float: inline-start` / `inline-end`, or prefer Flexbox/Grid.',
    },
    'bidi.clear-physical': {
        'title': 'Physical clear direction',
        'gate': 'gate_bidi_logical',
        'severity': 'MEDIUM',
        'citation': 'CSS Logical Properties and Values Level 1, §3 (clear: inline-start | inline-end)',
        'summary': (
            '`clear: left` clears only physical-left floats. Combined with logical '
            'floats the two no longer correspond, so the cleared element overlaps.'
        ),
        'fix': 'Use `clear: inline-start` / `inline-end`.',
    },
    'bidi.physical-offset': {
        'title': 'Physical inset offset',
        'gate': 'gate_bidi_logical',
        'severity': 'HIGH',
        'citation': 'CSS Logical Properties and Values Level 1, §4 (inset-inline-start)',
        'summary': (
            '`left` / `right` position against a physical edge. A positioned element '
            'pinned with `left: 0` stays on the left in RTL, which is usually the '
            'wrong edge for a start-aligned element.'
        ),
        'fix': 'Use `inset-inline-start` / `inset-inline-end`.',
    },
    'bidi.camelcase-property': {
        'title': 'camelCase physical property in a style object',
        'gate': 'gate_bidi_logical',
        'severity': 'HIGH',
        'citation': 'React DOM style-object property naming (CSS-in-JS)',
        'summary': (
            'React style objects cannot express `margin-left`, so the same physical '
            'property appears as `marginLeft`. It carries the identical RTL defect '
            'and must be checked in both spellings.'
        ),
        'fix': 'Use `marginInlineStart` (or the quoted kebab form `"margin-inline-start"`).',
    },

    # ------------------------------------------------------------ Contrast
    'contrast.wcag-aa-normal-text': {
        'title': 'Insufficient contrast for normal text (AA)',
        'gate': 'gate_contrast_wcag',
        'severity': 'CRITICAL',
        'citation': 'WCAG 2.2 Success Criterion 1.4.3 (Contrast — Minimum), 4.5:1',
        'summary': (
            'Normal-size text must reach a 4.5:1 contrast ratio against its '
            'background. Below that, low-vision users cannot reliably read it.'
        ),
        'fix': 'Adjust the foreground or background token until the computed ratio is >= 4.5:1.',
    },
    'contrast.wcag-aaa-normal-text': {
        'title': 'Insufficient contrast for normal text (AAA)',
        'gate': 'gate_contrast_wcag',
        'severity': 'CRITICAL',
        'citation': 'WCAG 2.2 Success Criterion 1.4.6 (Contrast — Enhanced), 7:1',
        'summary': (
            'The enhanced level requires 7:1 for normal text. Orthotect enforces it '
            'when `contrast.level` is set to "AAA" in `orthotect.config.json`.'
        ),
        'fix': 'Adjust the token pair until the computed ratio is >= 7:1.',
    },
    'contrast.wcag-non-text': {
        'title': 'Insufficient contrast for non-text UI components',
        'gate': 'gate_contrast_wcag',
        'severity': 'HIGH',
        'citation': 'WCAG 2.2 Success Criterion 1.4.11 (Non-text Contrast), 3:1',
        'summary': (
            'Borders, icons and control boundaries that convey information need '
            '3:1 against their adjacent colour, or the control becomes invisible '
            'to users with low contrast sensitivity.'
        ),
        'fix': 'Raise the component boundary colour to at least 3:1 against its background.',
    },

    # ----------------------------------------------------------------- FSM
    'fsm.missing-initial-state': {
        'title': 'Missing initialState',
        'gate': 'gate_fsm_integrity',
        'severity': 'HIGH',
        'citation': 'Orthotect FSM specification (core/fsm/)',
        'summary': 'A state machine without a declared initial state has no defined entry point.',
        'fix': 'Declare `initialState` as a non-empty string naming one of the declared states.',
    },
    'fsm.undefined-transition-target': {
        'title': 'Transition targets an undefined state',
        'gate': 'gate_fsm_integrity',
        'severity': 'CRITICAL',
        'citation': 'Orthotect FSM specification (core/fsm/)',
        'summary': (
            'A transition pointing at a state that does not exist leaves the machine '
            'in a state it cannot render, which surfaces as a stuck or blank UI.'
        ),
        'fix': 'Add the missing state definition, or retarget the transition to an existing state.',
    },
    'fsm.missing-loading-lock': {
        'title': 'Async state does not lock interaction',
        'gate': 'gate_fsm_integrity',
        'severity': 'CRITICAL',
        'citation': 'Orthotect FSM specification — double-submission race condition lock',
        'summary': (
            'A loading/pending state that still accepts clicks allows a second '
            'submission before the first resolves — the double-submit race that '
            'produces duplicate orders and duplicate writes.'
        ),
        'fix': 'Declare `allowClick: false` (or `locksInteraction: true`) on the async state.',
    },
    'fsm.missing-error-transition': {
        'title': 'State machine has no error path',
        'gate': 'gate_fsm_integrity',
        'severity': 'HIGH',
        'citation': 'Orthotect FSM specification — resilience requirement',
        'summary': (
            'Without an explicit error transition, a failed request has nowhere to '
            'go and the UI remains in its pending state indefinitely.'
        ),
        'fix': 'Add an ERROR/FAILURE transition from the async state to a declared error state.',
    },
    'fsm.deadlock': {
        'title': 'Non-final state with no outgoing transition',
        'gate': 'gate_fsm_integrity',
        'severity': 'HIGH',
        'citation': 'Orthotect FSM specification — deadlock freedom',
        'summary': (
            'A state that is not marked final and declares no transitions is a trap: '
            'the machine can enter it and can never leave, which the user experiences '
            'as a permanently frozen screen.'
        ),
        'fix': 'Add an outgoing transition, or mark the state `final: true` if it is genuinely terminal.',
    },
    'fsm.unreachable-state': {
        'title': 'Unreachable orphaned state',
        'gate': 'gate_fsm_integrity',
        'severity': 'MEDIUM',
        'citation': 'Orthotect FSM specification — reachability',
        'summary': (
            'A state no transition leads to is dead specification: it is documented, '
            'reviewed and maintained, but can never be rendered. It is either a '
            'missing transition or a leftover that should be deleted.'
        ),
        'fix': 'Add the transition that reaches the state, or remove the state.',
    },
    'fsm.invalid-structure': {
        'title': 'Malformed FSM specification',
        'gate': 'gate_fsm_integrity',
        'severity': 'CRITICAL',
        'citation': 'Orthotect FSM specification (core/fsm/)',
        'summary': (
            'A specification that is not a JSON object with a `states` map cannot be '
            'analysed at all, so no behavioural guarantee can be made about the '
            'component it describes.'
        ),
        'fix': 'Correct the JSON structure: root object, `initialState` string, `states` object.',
    },

    # ---------------------------------------------------------------- Slop
    'slop.ai-purple-gradient': {
        'title': 'Generic AI purple/indigo gradient',
        'gate': 'gate_no_slop',
        'severity': 'MEDIUM',
        'citation': 'Orthotect Anti-Slop Invariant',
        'summary': (
            'The indigo-purple gradient is the default output of most generative '
            'styling prompts. Its presence signals an untokenized, templated design '
            'rather than a deliberate palette decision.'
        ),
        'fix': 'Use a palette token from `core/tokens/` and a gradient defined in the token layer.',
    },
    'slop.raw-emoji-icon': {
        'title': 'Raw emoji used as an icon',
        'gate': 'gate_no_slop',
        'severity': 'MEDIUM',
        'citation': 'Orthotect Anti-Slop Invariant',
        'summary': (
            'Emoji render differently on every platform, cannot be recoloured or '
            'sized by CSS, and are announced inconsistently by screen readers. '
            'An icon inside a control must be a vector.'
        ),
        'fix': 'Replace the emoji with an inline SVG that inherits `currentColor`.',
    },
    'slop.inline-style-hex': {
        'title': 'Inline style bypassing design tokens',
        'gate': 'gate_no_slop',
        'severity': 'MEDIUM',
        'citation': 'Orthotect Token Purity invariant (W3C DTCG)',
        'summary': (
            'A hardcoded hex or rgba value in an inline style cannot be themed, '
            'cannot participate in dark mode, and escapes the contrast gate.'
        ),
        'fix': 'Use a `var(--token)` reference resolved from `core/tokens/`.',
    },

    # ----------------------------------------------------------------- DOM
    'dom.excessive-depth': {
        'title': 'Excessive DOM nesting depth',
        'gate': 'gate_cwv_budget',
        'severity': 'MEDIUM',
        'citation': 'Core Web Vitals — rendering cost / INP',
        'summary': (
            'Deep nesting increases style recalculation and layout cost on every '
            'frame, which shows up as poor interaction responsiveness.'
        ),
        'fix': 'Flatten the markup, or set `cwv.maxDomDepth` if the depth is genuinely required.',
    },
    'dom.excessive-nodes': {
        'title': 'Excessive DOM node count',
        'gate': 'gate_cwv_budget',
        'severity': 'MEDIUM',
        'citation': 'Core Web Vitals — rendering cost / INP',
        'summary': (
            'A large node count slows initial render and every subsequent layout. '
            'Lists that render every row at once are the usual cause.'
        ),
        'fix': 'Virtualize long lists, or raise `cwv.maxDomNodes` deliberately.',
    },
    'dom.unbalanced-markup': {
        'title': 'Unbalanced or malformed markup',
        'gate': 'gate_cwv_budget',
        'severity': 'HIGH',
        'citation': 'WHATWG HTML Living Standard — tree construction',
        'summary': (
            'A stray closing tag or an unclosed element makes the parser build a '
            'tree the author did not write, which silently changes layout and '
            'accessibility structure.'
        ),
        'fix': 'Correct the tag balance at the reported location.',
    },
    'dom.layout-shift-risk': {
        'title': 'Media without intrinsic dimensions',
        'gate': 'gate_cwv_budget',
        'severity': 'HIGH',
        'citation': 'Core Web Vitals — Cumulative Layout Shift (CLS)',
        'summary': (
            'An `img`, `video` or `iframe` without width/height or aspect-ratio '
            'occupies zero height until it loads, then pushes the content below it '
            'down — the classic layout shift.'
        ),
        'fix': 'Add `width`/`height` attributes or a CSS `aspect-ratio`.',
    },

    # ------------------------------------------------------------ Security
    'security.secret-exposure': {
        'title': 'Hardcoded secret or credential',
        'gate': 'gate_security_audit',
        'severity': 'CRITICAL',
        'citation': 'OWASP Top 10 A07:2021 — Identification and Authentication Failures',
        'summary': (
            'A committed API key, private key or token is permanently compromised '
            'the moment it enters version control, even if removed later.'
        ),
        'fix': 'Rotate the credential, move it to an environment variable, and add it to the baseline only if it is a deliberate fixture.',
    },
    'security.dom-xss': {
        'title': 'Untrusted source assigned to a DOM HTML sink',
        'gate': 'gate_security_audit',
        'severity': 'CRITICAL',
        'citation': 'OWASP Top 10 A03:2021 — Injection / CWE-79',
        'summary': (
            'Assigning a URL parameter or location value to `innerHTML` executes '
            'attacker-controlled markup in the page origin.'
        ),
        'fix': 'Use `textContent`, or sanitize through a vetted library before assigning markup.',
    },
    'security.command-injection': {
        'title': 'Untrusted input reaching a command sink',
        'gate': 'gate_security_audit',
        'severity': 'CRITICAL',
        'citation': 'OWASP Top 10 A03:2021 — Injection / CWE-78',
        'summary': (
            'Concatenating request data into a shell command lets an attacker run '
            'arbitrary commands with the process privileges.'
        ),
        'fix': 'Use an argument vector (never `shell: true`) and validate against an allowlist.',
    },
    'security.sql-injection': {
        'title': 'Untrusted input concatenated into SQL',
        'gate': 'gate_security_audit',
        'severity': 'CRITICAL',
        'citation': 'OWASP Top 10 A03:2021 — Injection / CWE-89',
        'summary': (
            'String-built SQL lets an attacker alter the statement, reading or '
            'destroying data outside the intended query.'
        ),
        'fix': 'Use parameterized queries; never interpolate values into SQL text.',
    },
    'security.unsafe-deserialization': {
        'title': 'Unsafe deserialization of untrusted data',
        'gate': 'gate_security_audit',
        'severity': 'HIGH',
        'citation': 'OWASP Top 10 A08:2021 — Software and Data Integrity Failures / CWE-502',
        'summary': (
            'Deserializing untrusted input with a format that can instantiate '
            'arbitrary objects is a well-known remote code execution vector.'
        ),
        'fix': 'Use a data-only format (JSON) with a schema, and never unpickle untrusted bytes.',
    },
    'security.dynamic-code-execution': {
        'title': 'Dynamic code execution with untrusted input',
        'gate': 'gate_security_audit',
        'severity': 'CRITICAL',
        'citation': 'OWASP Top 10 A03:2021 — Injection / CWE-95',
        'summary': (
            'Passing dynamic input to `eval` or the `Function` constructor lets an '
            'attacker execute arbitrary script in the page or process context.'
        ),
        'fix': 'Remove the dynamic evaluation; parse data with `JSON.parse` or a schema validator instead.',
    },
    'security.nosql-injection': {
        'title': 'Untrusted input reaching a NoSQL query operator',
        'gate': 'gate_security_audit',
        'severity': 'CRITICAL',
        'citation': 'OWASP Top 10 A03:2021 — Injection / CWE-943',
        'summary': (
            'A MongoDB `$where` clause built by string concatenation is executed as '
            'JavaScript on the server and can bypass the query entirely.'
        ),
        'fix': 'Use the query builder with typed operators; never concatenate user input into `$where`.',
    },
    'security.ssrf': {
        'title': 'Server-side request to a private address',
        'gate': 'gate_security_audit',
        'severity': 'CRITICAL',
        'citation': 'OWASP Top 10 A10:2021 — Server-Side Request Forgery / CWE-918',
        'summary': (
            'A request to localhost, a link-local address, or an RFC1918 range can '
            'reach cloud metadata endpoints and internal services the caller was '
            'never meant to access.'
        ),
        'fix': 'Validate the destination against an allowlist and block private, loopback and link-local ranges.',
    },
    'security.path-traversal': {
        'title': 'Directory traversal in a file read',
        'gate': 'gate_security_audit',
        'severity': 'HIGH',
        'citation': 'OWASP Top 10 A01:2021 — Broken Access Control / CWE-22',
        'summary': (
            'Concatenating `../` into a filesystem path lets an attacker read files '
            'outside the intended directory.'
        ),
        'fix': 'Resolve the path and assert it stays inside the permitted root before opening it.',
    },
    'security.weak-crypto': {
        'title': 'Deprecated or broken cryptography',
        'gate': 'gate_security_audit',
        'severity': 'HIGH',
        'citation': 'OWASP Top 10 A02:2021 — Cryptographic Failures / CWE-327',
        'summary': (
            '`crypto.createCipher`, MD5 and SHA-1 are broken for integrity and '
            'password storage; using them silently voids the protection they appear '
            'to provide.'
        ),
        'fix': 'Use AES-GCM via `crypto.createCipheriv`, and SHA-256 or stronger for integrity.',
    },
    'security.insecure-cors': {
        'title': 'Wildcard CORS origin with credentials',
        'gate': 'gate_security_audit',
        'severity': 'HIGH',
        'citation': 'OWASP Top 10 A05:2021 — Security Misconfiguration / CWE-942',
        'summary': (
            '`Access-Control-Allow-Origin: *` combined with credentials lets any '
            'origin read authenticated responses from your API.'
        ),
        'fix': 'Reflect only an explicit allowlist of origins, never `*`, when credentials are enabled.',
    },
    'security.insecure-postmessage': {
        'title': 'postMessage with a wildcard target origin',
        'gate': 'gate_security_audit',
        'severity': 'HIGH',
        'citation': 'OWASP Top 10 A05:2021 — Security Misconfiguration / CWE-346',
        'summary': (
            'Sending a message with target origin `*` delivers it to whatever frame '
            'occupies that window, including one an attacker navigated.'
        ),
        'fix': 'Pass an explicit target origin, and validate `event.origin` on the receiver.',
    },
    'security.prototype-pollution': {
        'title': 'Object prototype mutation',
        'gate': 'gate_security_audit',
        'severity': 'CRITICAL',
        'citation': 'OWASP Top 10 A03:2021 — Injection / CWE-1321',
        'summary': (
            'Assigning to `__proto__` or `constructor.prototype` pollutes every '
            'object in the process, which can escalate into remote code execution '
            'or authentication bypass.'
        ),
        'fix': 'Reject `__proto__`/`constructor`/`prototype` keys when merging untrusted objects.',
    },

    # ---------------------------------------------------------- Structural
    'bidi.parse-error': {
        'title': 'Unparseable CSS',
        'gate': 'gate_bidi_logical',
        'severity': 'HIGH',
        'citation': 'CSS Syntax Module Level 3 (W3C)',
        'summary': (
            'A declaration the CSS parser cannot read is dropped by the browser, so '
            'the style silently never applies — and the BiDi analysis cannot '
            'evaluate what it cannot parse.'
        ),
        'fix': 'Correct the syntax at the reported location.',
    },
    'dom.blocking-script': {
        'title': 'Synchronous blocking script in head',
        'gate': 'gate_cwv_budget',
        'severity': 'MEDIUM',
        'citation': 'Core Web Vitals — render-blocking resources / LCP',
        'summary': (
            'A synchronous external script in `<head>` halts HTML parsing until it '
            'downloads and executes, delaying first paint.'
        ),
        'fix': 'Add `defer` (or `async` where order does not matter) to the script tag.',
    },
    'dom.invalid-dimension': {
        'title': 'Invalid media dimension value',
        'gate': 'gate_cwv_budget',
        'severity': 'HIGH',
        'citation': 'WHATWG HTML Living Standard — dimension attributes / CLS',
        'summary': (
            'A `width`/`height` value that is not a positive integer (or a CSS '
            'dimension with a valid unit) reserves no space, so the element still '
            'shifts the layout when it loads.'
        ),
        'fix': 'Use a positive unitless integer for the HTML attribute, or a CSS value with a unit.',
    },
    'dom.resource-limit': {
        'title': 'Markup exceeds the AST traversal limit',
        'gate': 'gate_cwv_budget',
        'severity': 'MEDIUM',
        'citation': 'Core Web Vitals — rendering cost',
        'summary': (
            'A document with more nodes than the traversal budget is rejected as '
            'adversarial: analysis cannot complete, and such a tree is pathological '
            'for the browser as well.'
        ),
        'fix': 'Reduce the node count; if the size is genuinely required, split the page.',
    },
    'dom.empty-document': {
        'title': 'Empty or non-scannable document',
        'gate': 'gate_cwv_budget',
        'severity': 'MEDIUM',
        'citation': 'WHATWG HTML Living Standard',
        'summary': (
            'An empty, whitespace-only or comment-only file contains no markup to '
            'verify, so a pass would certify nothing.'
        ),
        'fix': 'Remove the file, or add the markup it is meant to contain.',
    },
}


#: Label-to-rule classification, in evaluation order (first match wins).
#:
#: The gates emit human sentences, not rule ids, and rewriting every emitted
#: string into an id would break the console output people read. This table is
#: the translation layer instead: each entry maps a gate's label family onto the
#: registry entry that documents it. Order matters — the specific patterns come
#: before the generic ones (`DOM XSS (Taint Flow)` before `DOM XSS`).
CLASSIFIERS = (
    # ---- BiDi
    ('gate_bidi_logical', 'PARSE_ERROR', 'bidi.parse-error'),
    ('gate_bidi_logical', 'Logical separation:', 'bidi.asymmetric-shorthand'),
    ('gate_bidi_logical', 'text-align', 'bidi.text-align-physical'),
    ('gate_bidi_logical', 'textAlign', 'bidi.text-align-physical'),
    ('gate_bidi_logical', 'float', 'bidi.float-physical'),
    ('gate_bidi_logical', 'clear', 'bidi.clear-physical'),
    # Camel-case properties are reported with their own name, so they are matched
    # by shape rather than by a keyword.
    ('gate_bidi_logical', r'^[a-z]+[A-Z]', 'bidi.camelcase-property'),
    ('gate_bidi_logical', r'^(left|right)$', 'bidi.physical-offset'),

    # ---- Contrast
    ('gate_contrast_wcag', 'AAA', 'contrast.wcag-aaa-normal-text'),
    ('gate_contrast_wcag', 'AA', 'contrast.wcag-aa-normal-text'),
    ('gate_contrast_wcag', 'non-text', 'contrast.wcag-non-text'),

    # ---- FSM
    ('gate_fsm_integrity', 'initialState', 'fsm.missing-initial-state'),
    ('gate_fsm_integrity', 'undefined target', 'fsm.undefined-transition-target'),
    ('gate_fsm_integrity', 'allowClick', 'fsm.missing-loading-lock'),
    ('gate_fsm_integrity', 'locksInteraction', 'fsm.missing-loading-lock'),
    ('gate_fsm_integrity', 'race condition', 'fsm.missing-loading-lock'),
    ('gate_fsm_integrity', 'error/failure transition', 'fsm.missing-error-transition'),

    # ---- Slop
    ('gate_no_slop', 'Purple/Indigo Gradient', 'slop.ai-purple-gradient'),
    ('gate_no_slop', 'Emoji', 'slop.raw-emoji-icon'),
    ('gate_no_slop', 'DTCG', 'slop.inline-style-hex'),

    # ---- DOM / CWV
    ('gate_cwv_budget', 'Excessive DOM depth', 'dom.excessive-depth'),
    ('gate_cwv_budget', 'Excessive DOM size', 'dom.excessive-nodes'),
    ('gate_cwv_budget', 'Malformed HTML', 'dom.unbalanced-markup'),
    ('gate_cwv_budget', 'stray closing tag', 'dom.unbalanced-markup'),
    ('gate_cwv_budget', 'unclosed tag', 'dom.unbalanced-markup'),
    ('gate_cwv_budget', 'mismatched closing tag', 'dom.unbalanced-markup'),
    ('gate_cwv_budget', 'trailing solidus', 'dom.unbalanced-markup'),
    ('gate_cwv_budget', 'duplicate attribute', 'dom.unbalanced-markup'),
    ('gate_cwv_budget', 'Synchronous blocking', 'dom.blocking-script'),
    ('gate_cwv_budget', 'Resource limit exceeded', 'dom.resource-limit'),
    ('gate_cwv_budget', 'Empty or non-scannable', 'dom.empty-document'),
    ('gate_cwv_budget', 'aspect-ratio', 'dom.layout-shift-risk'),
    ('gate_cwv_budget', 'width', 'dom.layout-shift-risk'),
    ('gate_cwv_budget', 'height', 'dom.layout-shift-risk'),
    ('gate_cwv_budget', 'data-width', 'dom.layout-shift-risk'),

    # ---- Security
    ('gate_security_audit', 'Taint Flow', 'security.dom-xss'),
    ('gate_security_audit', 'DOM XSS', 'security.dom-xss'),
    ('gate_security_audit', 'SQL Injection', 'security.sql-injection'),
    ('gate_security_audit', 'NoSQL Injection', 'security.nosql-injection'),
    ('gate_security_audit', 'Command Injection', 'security.command-injection'),
    ('gate_security_audit', 'Prototype Pollution', 'security.prototype-pollution'),
    ('gate_security_audit', 'Path Traversal', 'security.path-traversal'),
    ('gate_security_audit', 'Server-Side Request Forgery', 'security.ssrf'),
    ('gate_security_audit', 'Deserialization', 'security.unsafe-deserialization'),
    ('gate_security_audit', 'Weak Cryptography', 'security.weak-crypto'),
    ('gate_security_audit', 'Insecure CORS', 'security.insecure-cors'),
    ('gate_security_audit', 'postMessage', 'security.insecure-postmessage'),
    ('gate_security_audit', 'Dynamic Code Execution', 'security.dynamic-code-execution'),
    ('gate_security_audit', 'Function constructor', 'security.dynamic-code-execution'),
    ('gate_security_audit', 'Hardcoded', 'security.secret-exposure'),
    ('gate_security_audit', 'API Key', 'security.secret-exposure'),
    ('gate_security_audit', 'Secret Key', 'security.secret-exposure'),
    ('gate_security_audit', 'Private Key', 'security.secret-exposure'),
    ('gate_security_audit', 'JWT', 'security.secret-exposure'),
)

import re as _re

_COMPILED_CLASSIFIERS = tuple(
    (gate, _re.compile(pattern), rule_id) for gate, pattern, rule_id in CLASSIFIERS
)


def classify_label(gate, label):
    """
    Maps a gate's emitted label onto a registry rule id, or None.

    This is the join between enforcement and documentation: the gate emits a
    sentence a human can read, `--format sarif` needs an id a machine can key on,
    and both must name the same thing. Returning None (rather than inventing an
    id) lets the caller fall back explicitly, so an unclassified label is a
    visible gap instead of a plausible-looking lie.
    """
    text = str(label or '')
    for gate_name, pattern, rule_id in _COMPILED_CLASSIFIERS:
        if gate_name != gate:
            continue
        if pattern.search(text):
            return rule_id
    return None


def rule_ids():
    """All rule ids, sorted. Stable ordering for machine-readable output."""
    return sorted(RULES)


def get_rule(rule_id):
    """
    Looks a rule up by id.

    Raises RuleNotFound for an unknown id — an `explain` that silently returns
    nothing for a typo is worse than one that says the id does not exist.
    """
    try:
        return RULES[rule_id]
    except KeyError:
        raise RuleNotFound(rule_id)


def describe(rule_id):
    """A printable description of one rule, as a dict with the id included."""
    rule = dict(get_rule(rule_id))
    rule['id'] = rule_id
    return rule


def search(term):
    """
    Case-insensitive substring search across id, title, summary, citation and fix.

    Exists so `orthotect explain --search innerHTML` works: a reader who has a
    finding but not its id should not have to guess the registry's naming scheme.
    """
    needle = (term or '').strip().lower()
    if not needle:
        return []
    hits = []
    for rule_id in rule_ids():
        rule = RULES[rule_id]
        haystack = ' '.join([
            rule_id, rule.get('title', ''), rule.get('summary', ''),
            rule.get('citation', ''), rule.get('fix', ''), rule.get('gate', ''),
        ]).lower()
        if needle in haystack:
            hits.append(rule_id)
    return hits


def rules_by_gate():
    """Rule ids grouped by the gate that enforces them, for docs generation."""
    grouped = {}
    for rule_id in rule_ids():
        grouped.setdefault(RULES[rule_id]['gate'], []).append(rule_id)
    return grouped


def digest_projection():
    """
    The canonical `id|gate|severity` lines the rule-set digest is computed over.

    Deliberately not the whole registry: prose (titles, summaries, citations,
    fixes) can be corrected without changing a single finding, and a digest that
    moved on every typo fix would be noise. What a consumer comparing two reports
    actually needs to know is whether the same rules fired at the same severities.

    The projection is also what makes the digest computable from JavaScript: the
    DOM gate is the one non-Python gate and must stamp the same identity onto its
    SARIF document. Parsing three flat string fields is reliable; re-parsing the
    full Python data structure would not be.
    """
    return sorted(
        f"{rule_id}|{RULES[rule_id]['gate']}|{RULES[rule_id]['severity']}"
        for rule_id in RULES
    )


def rules_digest():
    """
    SHA-256 over `digest_projection()`, truncated to 16 hex characters.

    A hand-maintained version number is only as good as the discipline of whoever
    bumps it. This is the checkable half: two reports carrying the same digest
    were produced by the same rule identities, whatever the version string says.
    """
    canonical = '\n'.join(digest_projection())
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]


def metadata():
    """
    The version block every machine-readable report embeds.

    `rulesVersion` says what a consumer should pin; `rulesDigest` says whether the
    two runs they are comparing actually used the same rules; `ruleCount` makes a
    truncated or filtered registry visible at a glance.
    """
    return {
        'rulesVersion': RULES_VERSION,
        'rulesDigest': rules_digest(),
        'ruleCount': len(RULES),
    }


def _main(argv=None):
    """
    `orthotect explain <rule-id>` entry point.

    Exit codes follow the same contract as every other entry point: 0 when the
    requested information was produced, 2 when it could not be (unknown rule id,
    bad usage). Exit 1 is not used — `explain` makes no claim about any project,
    so it can never find a violation.
    """
    import json
    import sys

    args = list(sys.argv[1:] if argv is None else argv)

    try:
        from core.exit_codes import EXIT_PASS, EXIT_TOOL_ERROR
    except ImportError:
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from core.exit_codes import EXIT_PASS, EXIT_TOOL_ERROR

    as_json = '--json' in args
    as_md = '--md' in args
    search_term = None
    for i, token in enumerate(args):
        if token == '--search' and i + 1 < len(args):
            search_term = args[i + 1]
        elif token.startswith('--search='):
            search_term = token.split('=', 1)[1]

    positional = [a for a in args
                  if not a.startswith('-') and a != search_term]

    def emit_error(message):
        if as_json:
            print(json.dumps({'error': message, 'toolError': True}, indent=2))
        else:
            print(f"❌ [ERROR] {message}")
        sys.exit(EXIT_TOOL_ERROR)

    if search_term is not None:
        hits = search(search_term)
        if not hits:
            emit_error(f"No rule matches {search_term!r}. Run `orthotect explain --list` to see all rules.")
        if as_json:
            print(json.dumps({'query': search_term, 'matches': [describe(h) for h in hits]}, indent=2))
        elif as_md:
            print(f"### Rules matching `{search_term}`\n")
            print("| Rule ID | Gate | Severity | Title |")
            print("| :--- | :--- | :---: | :--- |")
            for rule_id in hits:
                rule = RULES[rule_id]
                print(f"| `{rule_id}` | {rule['gate']} | {rule['severity']} | {rule['title']} |")
        else:
            print(f"Rules matching '{search_term}':\n")
            for rule_id in hits:
                rule = RULES[rule_id]
                print(f"  {rule_id}")
                print(f"    {rule['title']} [{rule['severity']}] — {rule['gate']}")
        sys.exit(EXIT_PASS)

    if not positional:
        if as_json:
            payload = metadata()
            payload['rules'] = [describe(r) for r in rule_ids()]
            print(json.dumps(payload, indent=2))
        else:
            print("Usage: orthotect explain <rule-id>")
            print("       orthotect explain --search <term>")
            print("       orthotect explain --list\n")
            print(f"Rule registry v{RULES_VERSION} (digest {rules_digest()}) — "
                  f"{len(RULES)} rules across {len(rules_by_gate())} gates:\n")
            for gate, ids in sorted(rules_by_gate().items()):
                print(f"  {gate}")
                for rule_id in ids:
                    print(f"    {rule_id:<42} {RULES[rule_id]['title']}")
        sys.exit(EXIT_PASS)

    rule_id = positional[0]
    try:
        rule = describe(rule_id)
    except RuleNotFound:
        suggestions = search(rule_id.split('.')[-1].replace('-', ' '))
        hint = ''
        if suggestions:
            hint = f" Did you mean: {', '.join(suggestions[:3])}?"
        emit_error(f"Unknown rule id {rule_id!r}.{hint} Run `orthotect explain --list`.")

    if as_json:
        print(json.dumps(rule, indent=2))
    elif as_md:
        print(f"### `{rule['id']}` — {rule['title']}\n")
        print(f"**Gate:** `{rule['gate']}` | **Severity:** {rule['severity']}\n")
        print(f"**Citation:** {rule['citation']}\n")
        print(f"{rule['summary']}\n")
        print(f"**Fix:** {rule['fix']}")
    else:
        print("═" * 67)
        print(f"  {rule['title']}")
        print("═" * 67)
        print(f" Rule ID:  {rule['id']}")
        print(f" Gate:     {rule['gate']}")
        print(f" Severity: {rule['severity']}")
        print()
        print(f" Citation: {rule['citation']}")
        print()
        print(" Why this rule exists:")
        for line in _wrap(rule['summary'], 62):
            print(f"   {line}")
        print()
        print(" Fix:")
        for line in _wrap(rule['fix'], 62):
            print(f"   {line}")
        print()
    sys.exit(EXIT_PASS)


def _wrap(text, width):
    """Minimal greedy word wrap, so `explain` needs no dependency."""
    words = str(text).split()
    lines, current = [], ''
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += ' ' + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or ['']


if __name__ == '__main__':
    _main()
