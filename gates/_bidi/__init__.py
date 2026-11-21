#!/usr/bin/env python3
"""
Orthotect Gate: BiDi Logical Properties Enforcement (Syntax-Aware AST).

This package replaces the single-module gate of the same name and keeps its
public surface byte-for-byte: `from gate_bidi_logical import scan_file` and
`import gates.gate_bidi_logical as bidi_mod; bidi_mod.HAVE_TINYCSS2 = False`
both still work, which is what the existing tests and the auto-fix CLI rely on.

Layout — each module owns one rule family, and dependencies point one way:

    _runtime    optional deps (tinycss2, config, cli_args), exit codes
    _model      banned-property tables, BidiViolation
    _shorthand  split a value, decide whether a declaration is directional
    _css        CSS/HTML/stylesheet scanning (tinycss2 + fallback tokenizer)
    _js         JS/JSX/tagged-template scanning
    _fix        `--fix` rewrites, with post-write verification
    _paths      which files are in scope
    _dispatch   extension -> scanner, shared by the CLI and the fixer
    gate        SARIF and the CLI

Nothing imports `gate`, so the graph is acyclic and a rule module can be tested
without the CLI.

Why a module subclass
---------------------
`HAVE_TINYCSS2` is *reassigned* by callers, not just read. A plain re-export
would leave the scanners reading their own copy of the flag while the caller's
assignment rebinds only the facade's namespace — the fallback path would look
exercised and never run. The facade forwards the documented mutable names to
`_runtime`, so an assignment is visible to every module that reads them.
"""

import sys
import types

from . import _runtime
from ._css import scan_css_content, scan_css_content_fallback, scan_html_content
from ._dispatch import scan_file
from ._fix import PartialFixError, apply_bidi_fixes_to_file, fix_css_content, fix_html_content, fix_js_content
from ._js import (
    extract_tagged_template_literals,
    scan_js_content,
    scan_js_style_block,
    strip_js_comments_string_aware,
)
from ._model import ALLOWED_OFFSETS, BANNED_CAMELCASE_PROPERTIES, BANNED_PROPERTIES, BidiViolation
from ._paths import IGNORE_DIRS, SUPPORTED_EXTENSIONS
from ._shorthand import (
    SHORTHAND_PROPERTIES,
    check_declaration,
    check_declarations,
    evaluate_declaration,
    logical_shorthand_pair,
    normalize_declared_value,
    split_css_values,
)
from .gate import main

# Names that callers may reassign on the gate module. Assignments are routed to
# `_runtime`; reads fall through to whatever `_runtime` currently holds.
_FORWARDED = frozenset({'HAVE_TINYCSS2', 'tinycss2'})


class GateModule(types.ModuleType):
    """A module whose mutable runtime flags live in `_runtime`, not in itself."""

    def __getattr__(self, name):
        if name in _FORWARDED:
            return getattr(_runtime, name)
        raise AttributeError(f"module {self.__name__!r} has no attribute {name!r}")

    def __setattr__(self, name, value):
        if name in _FORWARDED:
            setattr(_runtime, name, value)
            return
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = GateModule

__all__ = [
    'ALLOWED_OFFSETS', 'BANNED_CAMELCASE_PROPERTIES', 'BANNED_PROPERTIES',
    'BidiViolation', 'IGNORE_DIRS', 'PartialFixError', 'SHORTHAND_PROPERTIES',
    'SUPPORTED_EXTENSIONS', 'apply_bidi_fixes_to_file', 'check_declaration',
    'check_declarations', 'evaluate_declaration', 'extract_tagged_template_literals',
    'fix_css_content', 'fix_html_content', 'fix_js_content', 'logical_shorthand_pair',
    'main', 'normalize_declared_value', 'scan_css_content', 'scan_css_content_fallback',
    'scan_file', 'scan_html_content', 'scan_js_content', 'scan_js_style_block',
    'split_css_values', 'strip_js_comments_string_aware', 'GateModule',
]
