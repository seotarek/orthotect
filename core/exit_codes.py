#!/usr/bin/env python3
"""
Orthotect Exit-Code Contract
============================

A verification tool that reports the same code for "your code is bad" and
"the tool could not run" cannot be trusted in CI: a broken install, a missing
dependency or an unreadable config file all look like a code regression, and a
transient environment failure can block a release forever with no way to tell
the difference.

Three outcomes, three codes:

    0  PASS      Every enforced rule was evaluated and satisfied.
    1  VIOLATION At least one gate evaluated the code and found a breach.
                 The audited code must change.
    2  TOOL ERROR The gate could not evaluate the code: missing runtime
                 dependency, absent/invalid configuration, unreadable token
                 file, or a target path that does not exist.
                 The *environment* must change, not the audited code.

Exit 2 is never used for a rule breach, and exit 1 is never used for an
infrastructure problem. Consumers should treat `!= 0` as "do not ship" and use
`== 2` to route the failure to an environment/dependency alert instead of a
code-review alert.
"""

EXIT_PASS = 0
EXIT_VIOLATION = 1
EXIT_TOOL_ERROR = 2
