"""
Process-level runtime: optional dependencies, the exit-code contract, and the
config loader.

These live in their own module for one reason: they are the only names callers
*reassign* rather than merely read. `tests/test_bidi.py` flips
`HAVE_TINYCSS2 = False` to prove the dependency-free fallback enforces the same
rules as the tinycss2 path, and the package facade forwards that assignment
here so every module sees it.

Had the flag stayed a plain module global in `_css`, the assignment would have
rebound the name in the facade's namespace while `_css` kept reading its own
copy — a silent no-op, and the fallback would never actually be exercised.
Routing mutable state through one small module makes the indirection explicit
and keeps it in a single place.
"""

import os
import sys

try:
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR

try:
    import tinycss2
    HAVE_TINYCSS2 = True
except ImportError:
    tinycss2 = None
    HAVE_TINYCSS2 = False

try:
    from core.config import load_orthotect_config, is_path_excluded
except ImportError:
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
        from core.config import load_orthotect_config, is_path_excluded
    except Exception:
        load_orthotect_config = None
        is_path_excluded = None

try:
    from core.cli_args import positionals as cli_positionals
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from core.cli_args import positionals as cli_positionals

__all__ = [
    'EXIT_PASS', 'EXIT_VIOLATION', 'EXIT_TOOL_ERROR',
    'HAVE_TINYCSS2', 'tinycss2',
    'load_orthotect_config', 'is_path_excluded', 'cli_positionals',
]
