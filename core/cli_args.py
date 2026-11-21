#!/usr/bin/env python3
"""
Orthotect CLI Argument Parser
=============================

One implementation of the flag/positional split, shared by every Python entry
point. Before this module the same logic existed in five places
(`bin/orthotect.js`, `run_all_gates.py`, `gate_security_audit.py`,
`gate_bidi_logical.py`, `gate_fsm_integrity.py`, `gate_no_slop.py`,
`gate_contrast_wcag.py`), and they had already drifted: only some skipped the
value bound to `--format`, so `gate --format json ./src` used to interpret
`json` as the target path and report "missing design tokens in target: json".

The bug class is the same every time: a value-taking flag leaks its value into
the positional list. This module makes that impossible by knowing, in one place,
which flags consume the next token.

Design rules
------------
* **A value flag never leaks its value.** `--format json ./src` yields `['./src']`.
* **Order independence.** `verify --json ./src` and `verify ./src --json` agree.
* **`--` terminates flags.** Everything after it is positional, even if it starts
  with a dash, which is the only way to audit a path like `./--weird-dir`.
* **`--flag=value` is one token,** never two, and never yields a positional.
* **Unknown flags are ignored, not fatal.** A gate receiving an unrecognised flag
  should still find its target rather than silently scan the default directory;
  validating flag names is the caller's job, not the splitter's.
"""

VALUE_FLAGS = frozenset({
    '--format', '--out', '--output', '--config', '-o', '--level', '--include', '--exclude',
})

#: Output formats the gates understand.
#:
#: `sarif` is a machine format for GitHub Code Scanning, not a human report. It
#: still carries the gate's exit code, so a CI job can publish the annotations
#: *and* fail the build from one run.
OUTPUT_FORMATS = ('console', 'json', 'md', 'sarif')


class ParsedArgs:
    """Result of splitting one argv vector."""

    __slots__ = ('positionals', 'flags')

    def __init__(self, positionals, flags):
        self.positionals = positionals
        self.flags = flags

    def has(self, flag):
        return flag in self.flags

    def value(self, flag, default=None):
        """
        Value of a value-taking flag, supporting both `--flag value` and
        `--flag=value`. Returns `default` when the flag is absent or was given
        without a value.
        """
        for i, token in enumerate(self.flags):
            if token == flag:
                if i + 1 < len(self.flags):
                    return self.flags[i + 1]
                return default
            if token.startswith(flag + '='):
                return token.split('=', 1)[1]
        return default

    def target(self, default=None):
        """First positional argument, or `default` when there is none."""
        return self.positionals[0] if self.positionals else default

    def __repr__(self):
        return f"ParsedArgs(positionals={self.positionals!r}, flags={self.flags!r})"


def parse_args(argv):
    """
    Splits an argv vector (without the program name) into positionals and flags.

    The flags list keeps the original token order, values included, so `value()`
    can resolve `--flag value` pairs without a second pass.
    """
    positionals = []
    flags = []
    i = 0
    total = len(argv)
    while i < total:
        token = argv[i]
        if token == '--':
            positionals.extend(argv[i + 1:])
            break
        if token.startswith('-') and token != '-':
            flags.append(token)
            if token in VALUE_FLAGS and i + 1 < total:
                # Keep the value reachable through value(), but never positional.
                flags.append(argv[i + 1])
                i += 2
                continue
            i += 1
            continue
        positionals.append(token)
        i += 1
    return ParsedArgs(positionals, flags)


def resolve_output_format(argv, allowed=('json', 'md', 'sarif'), bare_token=False):
    """
    Resolves the requested output format from `--json`, `--md`, `--format <fmt>`
    or `--format=<fmt>`.

    `allowed` narrows what `--format` accepts; anything outside it resolves to
    None rather than propagating an unknown format to the reporter.

    `bare_token=True` additionally accepts the documented legacy form
    `run_all_gates.py <dir> json`, where the format arrives as a trailing
    positional. Only the orchestrator needs this; enabling it everywhere would
    make a project directory literally named `json` impossible to audit.

    Returns the format string or None.
    """
    parsed = parse_args(argv)
    if parsed.has('--json'):
        return 'json'
    if parsed.has('--md'):
        return 'md'
    # `--sarif` is checked against `allowed` for the same reason `--format sarif`
    # is: a caller that did not opt into machine output must not receive a SARIF
    # document from a bare flag it never advertised.
    if 'sarif' in allowed and parsed.has('--sarif'):
        return 'sarif'

    for i, token in enumerate(argv):
        if token == '--format':
            if i + 1 >= len(argv):
                return None
            value = argv[i + 1].strip().lower()
            return value if value in allowed else None
        if token.startswith('--format='):
            value = token.split('=', 1)[1].strip().lower()
            return value if value in allowed else None

    if bare_token:
        for token in parsed.positionals:
            if token in allowed:
                return token
    return None


def positionals(argv, bare_format_tokens=()):
    """
    Non-flag arguments with value-flag leakage prevented.

    `bare_format_tokens` removes legacy bare format tokens (`verify ./src json`)
    from the result so they are never mistaken for a path.
    """
    parsed = parse_args(argv)
    if not bare_format_tokens:
        return list(parsed.positionals)
    return [p for p in parsed.positionals if p not in bare_format_tokens]


def has_flag(argv, flag):
    """True when `flag` appears as its own token (never as a `--flag=value` prefix)."""
    return flag in parse_args(argv).flags
