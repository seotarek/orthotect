"""
Process-level runtime: the exit-code contract and the shared argument parser.

Both are resolved once at import, with the same package-relative fallback the
monolithic gate used, so the gate still runs from an unusual deployment where
`core/` is not already importable.
"""

import os
import sys

try:
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR


def _cli_helpers():
    """
    Imports the shared argument parser, anchored to the Orthotect package.

    Delegating to `core/cli_args.py` keeps this gate's flag handling identical to
    the other gates and the CLI. The local fallbacks below exist only so the gate
    still runs if the module is missing from an unusual deployment; they are not
    a second implementation to maintain, and `tests/test_cli_args.py` asserts the
    shared module is what is actually used.
    """
    try:
        _pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if _pkg_root not in sys.path:
            sys.path.insert(0, _pkg_root)
        from core.cli_args import resolve_output_format, parse_args
        return resolve_output_format, parse_args
    except Exception:
        return None, None


_RESOLVE_FORMAT, _PARSE_ARGS = _cli_helpers()

__all__ = ['EXIT_PASS', 'EXIT_VIOLATION', 'EXIT_TOOL_ERROR',
           '_RESOLVE_FORMAT', '_PARSE_ARGS']
