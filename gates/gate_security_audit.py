#!/usr/bin/env python3
"""
Orthotect Deterministic Quality Gate 6: Enterprise Full-Stack Security & Threat Audit.

The gate's implementation moved to `gates/_security/` (one module per rule
family); this file is its public surface and its command-line entry point. The
name is unchanged on purpose: `package.json`, the orchestrator, the published
package manifest, the knowledge base and the test suite all reference
`gates/gate_security_audit.py`, and a rename would be a breaking change for a
refactor that is meant to be invisible.

Both call styles keep working:

    python3 gates/gate_security_audit.py ./src      # CLI
    from gate_security_audit import scan_file       # import (gates/ on sys.path)
    import gates.gate_security_audit as sec         # import (repo root on sys.path)

One subtlety worth stating: this module and its package are both exempt from
the scan by filename, because they necessarily contain the sink patterns the
gate hunts for. `is_engine_file` keys off `gate_security_audit.py` and
`gates/_security/`, and this module keeps that name so the exemption keeps
matching.
"""

import os as _os
import sys as _sys

# Anchored unconditionally, and *before* the import, rather than inside an
# except branch. `_security` is a private name; importing it by bare name first
# would let an unrelated `_security` module elsewhere on `sys.path` win the
# lookup — a silent substitution of the entire gate. Pinning this file's own
# directory to the front of the path makes the import deterministic.
_here = _os.path.dirname(_os.path.abspath(__file__))
if _here not in _sys.path:
    _sys.path.insert(0, _here)

from _security import *                                        # noqa: E402,F401,F403
from _security import __all__, main                            # noqa: E402,F401


if __name__ == '__main__':
    main()
