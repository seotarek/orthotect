"""
File-level scanning: which files are in scope, which matches are safe, and how
the per-family findings are combined into one deduplicated report.
"""
import os
import re

from ._ast import scan_python_ast
from ._patterns import INJECTION_PATTERNS, SCANNABLE_EXTENSIONS, SECRET_PATTERNS
from ._taint import scan_intrafile_taint

def is_scannable_file(filename):
    """Detect if a file is eligible for SAST scanning, including dotfiles (.env, .env.local, .env.production)."""
    if filename in ('skills-lock.json',):
        return False
    lower = filename.lower()
    if lower == '.env' or lower.startswith('.env.'):
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in SCANNABLE_EXTENSIONS


def is_engine_file(filepath):
    """
    True if `filepath` is part of the scanner engine rather than the audited code.

    The engine necessarily contains the sink patterns it hunts for — every rule
    is a string like `subprocess.run(cmd, shell=True)` — so scanning it yields
    findings about the detector, not about the user's project. That is noise at
    best and, at worst, an unreleasable audit: a fail-closed gate cannot report
    its own rule table as a vulnerability.

    The exemption was a single filename before this gate became a package. It
    now covers the package directory too, because the patterns moved into
    `gates/_security/` and a filename check would quietly stop matching and make
    the gate fail on itself. Anything else — including a file merely *named*
    like an engine module — stays auditable; the check is on the path's tail
    segments, not on a substring.
    """
    parts = os.path.normpath(filepath).replace('\\', '/').lower().split('/')

    if parts[-1] == 'gate_security_audit.py':
        return True

    # Any file inside a `gates/_security/` directory.
    return any(parts[i] == 'gates' and parts[i + 1] == '_security'
               for i in range(len(parts) - 1))


def is_safe_context(snippet, filepath):
    """
    Filter out genuinely non-exploitable contexts.

    Path-level trust is deliberately narrow: only the scanner engine itself and the
    curated educational knowledge/reference corpora are exempt. Test *directories* are
    NOT exempt, because shipping code frequently lives under a `tests/` or `test/` helper
    path (fixtures, e2e drivers, mock servers) and would otherwise be silently un-audited.
    Tests that need to assert on dangerous-looking strings should be excluded via the
    orchestrator's scan scope, not by trusting the path blindly.
    """
    lower_path = filepath.lower().replace('\\', '/')
    lower_snip = snippet.lower().strip()

    # Safe if this is the scanner engine itself (it necessarily contains sink patterns)
    if is_engine_file(filepath):
        return True

    # Safe if inside the curated educational knowledge base or reference corpus
    if ('/knowledge/' in lower_path or '/references/' in lower_path
            or lower_path.startswith('knowledge/') or lower_path.startswith('references/')):
        return True

    # Safe if the matched line is a pure comment or documentation quote
    if lower_snip.startswith(('//', '#', '/*', '*', '<!--', '"""', "'''", '>')):
        return True

    return False


def scan_file(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return findings

    # Skip if file itself is this gate script
    if os.path.abspath(filepath) == os.path.abspath(__file__):
        return []

    lines = content.splitlines()

    # 1. Check Hardcoded Secrets
    for pattern, label, severity in SECRET_PATTERNS:
        for m in re.finditer(pattern, content):
            snippet = m.group(0)[:80].replace('\n', ' ')
            if is_safe_context(snippet, filepath):
                continue
            line_no = content.count('\n', 0, m.start()) + 1
            findings.append((line_no, label, severity, snippet))

    # 2. Check Sinks and Injection Patterns
    for pattern, label, severity in INJECTION_PATTERNS:
        for m in re.finditer(pattern, content):
            snippet = m.group(0)[:80].replace('\n', ' ')
            if is_safe_context(snippet, filepath):
                continue
            line_no = content.count('\n', 0, m.start()) + 1
            findings.append((line_no, label, severity, snippet))

    # 3. Python AST Analysis
    if filepath.endswith('.py'):
        ast_findings = scan_python_ast(filepath, content)
        for line_no, label, severity, snippet in ast_findings:
            if not is_safe_context(snippet, filepath):
                findings.append((line_no, label, severity, snippet))

    # 4. Intra-file Taint Flow Analysis
    if any(filepath.endswith(ext) for ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte', '.html')):
        taint_findings = scan_intrafile_taint(filepath, content)
        for line_no, label, severity, snippet in taint_findings:
            if not is_safe_context(snippet, filepath):
                findings.append((line_no, label, severity, snippet))

    # Deduplicate findings by line and label
    deduped = []
    seen = set()
    for f in findings:
        key = (f[0], f[1])
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return sorted(deduped, key=lambda x: x[0])
