#!/usr/bin/env python3
"""
Orthotect Gate: BiDi Logical Properties Enforcement (Syntax-Aware AST).

The gate's implementation moved to `gates/_bidi/` (one module per rule family);
this file is its public surface and its command-line entry point. The name is
unchanged on purpose: `gates/gate_bidi_logical.py` is referenced by
`package.json`, the orchestrator, the published package manifest, the knowledge
base and the test suite, and a rename would be a breaking change for a refactor
that is meant to be invisible.

Both call styles keep working:

    python3 gates/gate_bidi_logical.py ./src        # CLI
    from gate_bidi_logical import scan_file         # import (gates/ on sys.path)
    import gates.gate_bidi_logical as bidi_mod      # import (repo root on sys.path)
"""

import os as _os
import sys as _sys

# Anchored unconditionally, and *before* the import, rather than inside an
# except branch. `_bidi` is a private name; importing it by bare name first
# would let an unrelated `_bidi` module elsewhere on `sys.path` win the lookup —
# a silent substitution of the entire gate. Pinning this file's own directory to
# the front of the path makes the import deterministic.
_here = _os.path.dirname(_os.path.abspath(__file__))
if _here not in _sys.path:
    _sys.path.insert(0, _here)

from _bidi import *                                             # noqa: E402,F401,F403
from _bidi import GateModule, __all__, __dict__ as _exports, main  # noqa: E402,F401

# A star-import keeps only public names, and the facade's mutable-flag
# forwarding needs `_runtime` reachable on THIS module, not only on `_bidi`.
_runtime = _exports['_runtime']
_sys.modules[__name__].__class__ = GateModule


if __name__ == '__main__':
    main()
