#!/usr/bin/env python3
"""
Orthotect Gate: Anti-Slop Lexical & Pattern Inspector
Rejects statistical AI anti-patterns across markup and stylesheets:
- Hardcoded purple/indigo gradients (linear-gradient(#6366f1, #a855f7))
- Raw emojis used as icons inside interactive buttons and primary headings
- Hardcoded inline styles bypassing the DTCG token architecture
"""

# Exit-code contract (see core/exit_codes.py):
#   0 = PASS, 1 = rule violation in the audited code, 2 = the gate could not run.
try:
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
except ImportError:
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
import sys
import os
import re

try:
    from core.cli_args import positionals as cli_positionals
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from core.cli_args import positionals as cli_positionals

# (pattern, label, registry rule id). The id is carried alongside the label so a
# machine-readable report names the same rule `orthotect explain` documents,
# without re-deriving it from the human message.
SLOP_PATTERNS = [
    (r'linear-gradient\s*\([^)]*(#6366f1|#a855f7|#7c3aed|#8b5cf6|#9333ea|#c084fc|indigo|purple|violet)[^)]*\)', 'Generic AI Purple/Indigo Gradient', 'slop.ai-purple-gradient'),
    (r'<([A-Za-z0-9_:-]*button)\b[^>]*>(?:(?!</?\1\b)[\s\S])*?[🚀🔥✨💡🎉📈📊🧠🤖⚡💥⭐🎯💬🛠️⚙️🔒📦🏆🪄👑💎](?:(?!</?\1\b)[\s\S])*?</\1\s*>', 'Raw Emoji in Button Icon instead of SVG vector', 'slop.raw-emoji-icon'),
    (r'<h[1-6][^>]*>(?:(?!</h[1-6]>)[\s\S])*?[🚀🔥✨💡🎉📈📊🧠🤖⚡💥⭐🎯💬🛠️⚙️🔒📦🏆🪄👑💎]', 'Raw Emoji in Heading element', 'slop.raw-emoji-icon'),
    (r'style\s*=\s*[\'"][^\'"]*(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\))[^\'"]*[\'"]', 'Inline style bypassing DTCG tokens', 'slop.inline-style-hex'),
    (r'style\s*=\s*\{\{\s*[^}]*(?:color|background|backgroundColor)\s*:\s*[\'"](#[0-9a-fA-F]{3,8}|rgba?\([^)]+\))[\'"]', 'JSX Inline style bypassing DTCG tokens', 'slop.inline-style-hex'),
]

IGNORE_DIRS = {
    'node_modules', '.git', 'dist', '__pycache__', '.claude', 'tmp',
    'coverage', '.next', '.cache', 'vendor', 'build', '.turbo', '.parcel-cache'
}
EXTENSIONS = {'.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte', '.css', '.scss', '.less', '.js', '.ts'}


def mask_comments(content):
    """
    Replaces comment bodies (CSS/JS/HTML) with spaces while preserving newlines and byte
    offsets, so line numbers stay exact. Prevents flagging anti-patterns that only appear
    in documentation comments (e.g. a changelog note about a removed gradient).

    The scan is string-aware: a `//` inside `"https://example.com"` or a `/*` inside a
    template literal is ordinary text, not a comment opener. Without that, everything
    after a URL in a string literal was blanked and real slop later on the same line
    silently passed the gate (fail-open).

    String contents themselves are NOT masked — genuine slop inside attribute values or
    template strings must still be detected.
    """
    out = list(content)
    n = len(content)

    def blank(start, stop):
        for k in range(start, min(stop, n)):
            if out[k] != '\n':
                out[k] = ' '

    state = 'normal'
    quote = ''
    i = 0
    while i < n:
        ch = content[i]

        if state == 'normal':
            if content.startswith('<!--', i):
                end = content.find('-->', i + 4)
                stop = n if end == -1 else end + 3
                blank(i, stop)
                i = stop
                continue
            if content.startswith('/*', i):
                end = content.find('*/', i + 2)
                stop = n if end == -1 else end + 2
                blank(i, stop)
                i = stop
                continue
            if content.startswith('//', i):
                end = content.find('\n', i + 2)
                stop = n if end == -1 else end
                blank(i, stop)
                i = stop
                continue
            if ch in ('"', "'", '`'):
                state = 'string'
                quote = ch
                i += 1
                continue
            i += 1
            continue

        # state == 'string'
        if ch == '\\':
            i += 2
            continue
        if ch == quote:
            state = 'normal'
            quote = ''
        elif quote != '`' and ch == '\n':
            # Unterminated single-line string: recover instead of swallowing the file.
            state = 'normal'
            quote = ''
        i += 1

    return ''.join(out)


class SlopFinding(tuple):
    """
    A `(line, label, snippet)` 3-tuple that also carries the registry rule id.

    Tuple-compatible so the console report and any existing unpacking keep
    working, with the rule id alongside for the machine-readable path.
    """

    def __new__(cls, line, label, snippet, rule=None):
        instance = super().__new__(cls, (line, label, snippet))
        instance.line = line
        instance.label = label
        instance.snippet = snippet
        instance.rule = rule
        return instance


def scan_file(filepath):
    findings = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        masked = mask_comments(content)
        for pattern, label, rule_id in SLOP_PATTERNS:
            matches = list(re.finditer(pattern, masked, re.IGNORECASE))
            for m in matches:
                line_no = masked.count('\n', 0, m.start()) + 1
                snippet = m.group(0)[:70].replace('\n', ' ')
                findings.append(SlopFinding(line_no, label, snippet, rule_id))
    return findings

def _load_sarif_module():
    """Loads `core/sarif.py`, anchored to the package so cwd cannot change it."""
    try:
        from core import sarif
        return sarif
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from core import sarif
        return sarif


def main():
    # Skip flag tokens so `gate_no_slop.py --quiet ./src` inspects ./src rather than "--quiet".
    args = sys.argv[1:]
    positional = cli_positionals(args)
    target_dir = positional[0] if positional else 'examples'

    sarif = _load_sarif_module()
    as_sarif = sarif.sarif_requested(args)

    def fail_tool_error(message):
        if as_sarif:
            sarif.print_gate_sarif('gate_no_slop', [], os.path.abspath(target_dir),
                                   tool_error=message)
        else:
            print(f"❌ [REJECT] {message}")
        sys.exit(EXIT_TOOL_ERROR)

    if not os.path.exists(target_dir):
        # TOOL ERROR: the path does not exist, so nothing was evaluated.
        fail_tool_error(f"Target path not found: {target_dir}")

    # Honor orthotect.config.json `exclude` globs. Previously this gate used a hardcoded
    # ignore list, so user-configured exclusions (e.g. generated marketing/ dirs) were
    # silently scanned and could block commits with no way to opt out.
    config = None
    is_path_excluded = None
    try:
        _pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if _pkg_root not in sys.path:
            sys.path.insert(0, _pkg_root)
        from core.config import load_orthotect_config, is_path_excluded
        config, _ = load_orthotect_config(target_dir)
    except Exception:
        config = None
        is_path_excluded = None

    if not as_sarif:
        print("═══════════════════════════════════════════════════════════════")
        print("  ORTHOTECT GATE: Anti-Slop Lexical & Pattern Inspector")
        print("═══════════════════════════════════════════════════════════════")

    total_slop = 0
    scanned_files = 0
    all_findings = []

    if os.path.isfile(target_dir):
        files_to_scan = [(os.path.dirname(target_dir), os.path.basename(target_dir))]
    else:
        files_to_scan = []
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [
                d for d in dirs
                if d not in IGNORE_DIRS
                and not (is_path_excluded and is_path_excluded(os.path.join(root, d), config, target_dir))
            ]
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in EXTENSIONS:
                    fpath = os.path.join(root, file)
                    if is_path_excluded and is_path_excluded(fpath, config, target_dir):
                        continue
                    files_to_scan.append((root, file))

    for root, file in files_to_scan:
        scanned_files += 1
        fpath = os.path.join(root, file)
        findings = scan_file(fpath)
        if findings:
            if not as_sarif:
                print(f"\n❌ [FAIL] Anti-pattern detected in: {fpath}")
                for line_no, label, snippet in findings:
                    print(f"   Line {line_no:4d}: {label}")
                    print(f"              Snippet: '{snippet}'")
            for finding in findings:
                all_findings.append({
                    'file': fpath,
                    'line': finding.line,
                    'label': finding.label,
                    'snippet': finding.snippet,
                    'ruleId': finding.rule,
                })
            total_slop += len(findings)

    if scanned_files == 0:
        # TOOL ERROR: zero files in scope means zero rules were evaluated. Reporting this as
        # a violation would let a mis-pointed path masquerade as a code problem.
        fail_tool_error(
            f"No source code files found to inspect in: {target_dir}. "
            f"Orthotect requires verifiable frontend source files.")

    if as_sarif:
        sarif.print_gate_sarif('gate_no_slop', all_findings, os.path.abspath(target_dir))
        sys.exit(EXIT_PASS if total_slop == 0 else EXIT_VIOLATION)

    if total_slop == 0:
        print(f"\n✅ [PASS] No AI Slop detected across {scanned_files} file(s)!")
        sys.exit(EXIT_PASS)
    else:
        print(f"\n❌ [REJECT] {total_slop} anti-pattern(s) flagged.")
        sys.exit(EXIT_VIOLATION)

if __name__ == '__main__':
    main()
