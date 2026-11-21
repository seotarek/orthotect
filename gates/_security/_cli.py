"""
Command-line surface: format and target resolution, SARIF emission, rule-set
metadata, and `main`.
"""
import json
import os
import sys

from ._patterns import IGNORE_DIRS
from ._runtime import _PARSE_ARGS, _RESOLVE_FORMAT, EXIT_PASS, EXIT_TOOL_ERROR, EXIT_VIOLATION
from ._scanner import is_engine_file, is_scannable_file, scan_file

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


def _resolve_requested_format(argv):
    """Resolves --json / --md / --sarif / --format <fmt> to 'json' | 'md' | 'sarif' | None."""
    if _RESOLVE_FORMAT:
        return _RESOLVE_FORMAT(argv)
    if '--json' in argv:
        return 'json'
    if '--md' in argv:
        return 'md'
    if '--sarif' in argv:
        return 'sarif'
    for i, token in enumerate(argv):
        if token == '--format' and i + 1 < len(argv):
            value = argv[i + 1].lower()
            return value if value in ('json', 'md', 'sarif') else None
        if token.startswith('--format='):
            value = token.split('=', 1)[1].lower()
            return value if value in ('json', 'md', 'sarif') else None
    return None


def _resolve_target(argv):
    """
    First positional argument, skipping values bound to value-taking flags.
    A bare `--format json` must never be interpreted as the target directory.
    """
    if _PARSE_ARGS:
        return _PARSE_ARGS(argv).target()
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith('-'):
            if token in ('--format', '--out', '--output', '--config', '-o'):
                i += 2
                continue
            i += 1
            continue
        return token
    return None


def _load_sarif_module():
    """Loads `core/sarif.py`, anchored to the package so cwd cannot change it."""
    try:
        from core import sarif
        return sarif
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
        from core import sarif
        return sarif


def _rule_set_metadata():
    """
    The rule-set version block for the JSON report, or an empty dict.

    Absent rather than invented when the registry cannot be read: a placeholder
    version looks pinnable and is not.
    """
    try:
        from core.rule_registry import metadata
        return metadata()
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
        try:
            from core.rule_registry import metadata
            return metadata()
        except Exception:
            return {}


def classify_label(gate, label):
    """
    Maps a finding label onto its registry rule id, or None.

    Delegates to `core.rule_registry`, the same table `orthotect explain` reads,
    so a rule's id can never drift between the documentation and the report. A
    missing registry degrades to None (a visible gap in the report) rather than
    inventing an id that no rule page describes.
    """
    try:
        from core.rule_registry import classify_label as _classify
        return _classify(gate, label)
    except Exception:
        try:
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
            from core.rule_registry import classify_label as _classify
            return _classify(gate, label)
        except Exception:
            return None


def main():
    args = sys.argv[1:]
    requested_format = _resolve_requested_format(args)
    is_json = requested_format == 'json'
    is_md = requested_format == 'md'
    is_sarif = requested_format == 'sarif'

    resolved_target = _resolve_target(args)
    target_dir = resolved_target if resolved_target else 'examples/golden-showcase'
    target_dir = os.path.abspath(target_dir)

    sarif = _load_sarif_module() if is_sarif else None

    def _emit_sarif(findings, tool_error=None):
        """Writes this gate's SARIF document; the exit code is decided by the caller."""
        sarif.print_gate_sarif('gate_security_audit', findings, target_dir,
                               tool_error=tool_error)

    if not os.path.exists(target_dir):
        err = f"Target path does not exist: {target_dir}"
        if is_sarif:
            _emit_sarif([], tool_error=err)
        elif is_json:
            print(json.dumps({"error": err, "passed": False, "toolError": True}))
        else:
            print(f"❌ [REJECT] {err}")
        sys.exit(EXIT_TOOL_ERROR)

    # Honor orthotect.config.json `exclude` globs (previously ignored by this gate).
    config = None
    config_file = None
    is_path_excluded = None
    try:
        _pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if _pkg_root not in sys.path:
            sys.path.insert(0, _pkg_root)
        from core.config import load_orthotect_config, is_path_excluded
        config, config_file = load_orthotect_config(target_dir)
    except Exception:
        config = None
        config_file = None
        is_path_excluded = None

    # The gate's own configuration is tool metadata, not application source. Auditing it
    # would keep the scan non-empty even when every real source file is excluded, which
    # would let an over-broad `exclude` produce a green certificate for code never read.
    excluded_config_path = os.path.abspath(config_file) if config_file else None

    files_to_scan = []
    if os.path.isfile(target_dir):
        files_to_scan.append(target_dir)
    else:
        for root, dirs, files in os.walk(target_dir):
            # 'tests'/'test' are excluded only when they sit at the scan root (conventional
            # repository-level test trees). Nested ones such as `src/tests/` or
            # `app/test/` are application code and MUST remain auditable.
            at_root = os.path.abspath(root) == target_dir
            allowed = IGNORE_DIRS if at_root else (IGNORE_DIRS - {'tests', 'test'})
            dirs[:] = [
                d for d in dirs
                if d not in allowed
                and not (is_path_excluded and is_path_excluded(os.path.join(root, d), config, target_dir))
            ]
            for file in files:
                full_p = os.path.join(root, file)
                if not is_scannable_file(file) or is_engine_file(full_p):
                    continue
                if excluded_config_path and os.path.abspath(full_p) == excluded_config_path:
                    continue
                if is_path_excluded and is_path_excluded(full_p, config, target_dir):
                    continue
                files_to_scan.append(full_p)

    # Load the committed allowlist, if one exists. Every failure here is a tool
    # error: proceeding without a baseline that was asked for would silently
    # re-enable findings the project has already reviewed and accepted.
    baseline_entries = []
    baseline_path = None

    def _baseline_tool_error(message):
        if is_sarif:
            _emit_sarif([], tool_error=message)
        elif is_json:
            print(json.dumps({"target": target_dir, "passed": False, "toolError": True,
                              "error": message}, indent=2))
        elif is_md:
            print("### 🛡️ Orthotect Cybersecurity Gate Report")
            print(f"**Target:** `{target_dir}` | **Status:** ⛔ TOOL ERROR — invalid baseline\n")
            print(f"> {message}\n")
        else:
            print(f"❌ [REJECT] {message}")
            print("   A security audit never proceeds on a baseline it could not read.")
        sys.exit(EXIT_TOOL_ERROR)

    try:
        _pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if _pkg_root not in sys.path:
            sys.path.insert(0, _pkg_root)
        from core.security_baseline import (
            find_baseline_path, load_baseline, apply_baseline, unused_entries, BaselineError,
        )
    except Exception as e:
        _baseline_tool_error(f"Security baseline module unavailable: {e}")

    # A single-file target resolves its baseline from the containing directory; a
    # directory target resolves from itself.
    baseline_root = target_dir if os.path.isdir(target_dir) else os.path.dirname(
        os.path.abspath(target_dir))
    try:
        baseline_path = find_baseline_path(baseline_root)
        if baseline_path:
            baseline_entries = load_baseline(baseline_path)
    except BaselineError as e:
        _baseline_tool_error(f"Invalid security baseline: {e}")

    # Suppression paths are relative to the directory that holds the baseline file,
    # not to the audit root. Those are the same directory in the common case, but
    # they differ when a target is a single file, or when a monorepo holds one
    # baseline above the package being audited. Resolving against the audit root in
    # those cases would make every entry silently fail to match.
    baseline_base = os.path.dirname(baseline_path) if baseline_path else baseline_root

    raw_findings = {}
    for fpath in files_to_scan:
        findings = scan_file(fpath)
        if findings:
            raw_findings[fpath] = findings

    surviving, suppressed = apply_baseline(raw_findings, baseline_entries, baseline_base)
    file_reports = surviving
    total_vulns = sum(len(v) for v in surviving.values())
    suppressed_count = sum(len(v) for v in suppressed.values())
    stale_entries = unused_entries(baseline_entries, suppressed)

    passed = (total_vulns == 0)
    # Zero files in scope means zero rules were evaluated. A mis-pointed path, an
    # over-broad `exclude`, or a directory that failed to mount must never yield a
    # green security certificate (exit 0); it is an environment problem (exit 2).
    no_scope = not files_to_scan
    if passed and no_scope:
        exit_code = EXIT_TOOL_ERROR
    elif passed:
        exit_code = EXIT_PASS
    else:
        exit_code = EXIT_VIOLATION

    no_scope_json = {
        "target": target_dir,
        "passed": False,
        "scannedFiles": 0,
        "vulnerabilityCount": 0,
        "error": "No application source files found to audit; zero security rules were evaluated.",
        "toolError": True,
    }

    if is_sarif:
        if no_scope:
            _emit_sarif([], tool_error=no_scope_json["error"])
            sys.exit(EXIT_TOOL_ERROR)
        _emit_sarif([
            {
                "file": fpath,
                "line": line,
                "label": label,
                "severity": sev,
                "snippet": snip,
                "ruleId": classify_label('gate_security_audit', label),
            }
            for fpath, vulns in file_reports.items()
            for line, label, sev, snip in vulns
        ])
        sys.exit(exit_code)

    if is_json:
        if no_scope:
            print(json.dumps(no_scope_json, indent=2))
            sys.exit(EXIT_TOOL_ERROR)
        report = {
            "target": target_dir,
            "passed": passed,
            "scannedFiles": len(files_to_scan),
            "vulnerabilityCount": total_vulns,
            "ruleSet": _rule_set_metadata(),
            "scope": {
                "included": "Application frontend & backend source files (.py, .js, .ts, .html, .json, .env*)",
                "excluded": "root-level tests/ and test/, .github/, node_modules/, dist/, build/, vendor/, gate_security_audit.py (scanner engine). Nested tests/ directories (e.g. src/tests/) remain in scope."
            },
            "notice": "Deterministic SAST verification passed (AST & intra-file taint analysis). Verifies static syntax, dangerous sinks, and secrets; does not replace runtime penetration testing.",
            "baseline": {
                "path": baseline_path,
                "entryCount": len(baseline_entries),
                "suppressedCount": suppressed_count,
                "staleEntries": [e.to_dict() for e in stale_entries],
            },
            "suppressed": [
                {
                    "file": fpath,
                    "line": finding[0],
                    "label": finding[1],
                    "severity": finding[2],
                    "justification": entry.justification,
                }
                for fpath, pairs in suppressed.items()
                for finding, entry in pairs
            ],
            "vulnerabilities": [
                {
                    "file": fpath,
                    "line": line,
                    "label": label,
                    "severity": sev,
                    "snippet": snip
                }
                for fpath, vulns in file_reports.items()
                for line, label, sev, snip in vulns
            ]
        }
        print(json.dumps(report, indent=2))
        sys.exit(exit_code)

    if is_md:
        if no_scope:
            print(f"### 🛡️ Orthotect Cybersecurity Gate Report")
            print(f"**Target:** `{target_dir}` | **Status:** ⛔ TOOL ERROR — no files in scope | **Files Scanned:** 0\n")
            print("> Zero application source files were found to audit, so zero security rules were evaluated. This is not a pass. Check the target path or the `exclude` globs in `orthotect.config.json`.\n")
            sys.exit(EXIT_TOOL_ERROR)
        print(f"### 🛡️ Orthotect Cybersecurity Gate Report")
        print(f"**Target:** `{target_dir}` | **Status:** {'✅ PASSED (Deterministic SAST)' if passed else '❌ VULNERABILITIES DETECTED'} | **Files Scanned:** {len(files_to_scan)}")
        print(f"**Scope:** Application source files (.py, .js, .ts, .html, .json, .env*). Excluded: root-level tests/, .github/, node_modules/, dist/, gate_security_audit.py (scanner engine). Nested tests/ directories remain in scope.\n")
        if not passed:
            print("| File | Line | Severity | Vulnerability | Snippet |")
            print("| :--- | :---: | :---: | :--- | :--- |")
            for fpath, vulns in file_reports.items():
                rel = os.path.relpath(fpath, baseline_base)
                for line, label, sev, snip in vulns:
                    print(f"| `{rel}` | {line} | **{sev}** | {label} | `{snip}` |")
        else:
            print("> **Scope Notice:** Deterministic SAST verification passed (AST & intra-file taint analysis). Verifies static syntax, dangerous sinks, and secrets. Does not replace dynamic runtime penetration testing, DAST, or manual security review.\n")
        if baseline_path:
            print(f"**Baseline:** `{os.path.relpath(baseline_path, baseline_base)}` — "
                  f"{len(baseline_entries)} entry/entries, {suppressed_count} finding(s) suppressed.\n")
            if suppressed:
                print("| File | Line | Rule | Justification |")
                print("| :--- | :---: | :--- | :--- |")
                for fpath, pairs in suppressed.items():
                    rel = os.path.relpath(fpath, baseline_base)
                    for finding, entry in pairs:
                        print(f"| `{rel}` | {finding[0]} | {finding[1]} | {entry.justification} |")
                print("")
            if stale_entries:
                print(f"> ⚠️  **{len(stale_entries)} stale baseline entr(y/ies)** matched nothing. "
                      f"The code has moved on; remove or update them.\n")
                for e in stale_entries:
                    print(f"> - `{e.file}`:{e.line} — {e.rule}")
                print("")
        sys.exit(exit_code)

    # Standard Console ASCII Banner
    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE 6: Deterministic SAST Security & Threat Audit")
    print("  Deterministic SAST & Dangerous Sink Inspection (OWASP / CWE)")
    print("═══════════════════════════════════════════════════════════════")
    print(f" Target Path: {target_dir}")
    print(f" Scanned Scope: {len(files_to_scan)} application source files (.py, .js, .ts, .html, .json, .env*)")
    print(f" Excluded Scope: Root-level tests/, CI (.github/), Vendor (node_modules/), Build (dist/), Scanner Engine (gate_security_audit.py)\n")

    if baseline_path:
        print(f" Baseline: {os.path.relpath(baseline_path, baseline_base)} "
              f"({len(baseline_entries)} entry/entries, {suppressed_count} finding(s) suppressed)")
        for fpath, pairs in suppressed.items():
            rel = os.path.relpath(fpath, baseline_base)
            for finding, entry in pairs:
                print(f"   [SUPPRESSED] {rel}:{finding[0]} — {finding[1]}")
                print(f"                Justification: {entry.justification}")
        if stale_entries:
            print(f"   ⚠️  {len(stale_entries)} stale baseline entr(y/ies) matched nothing — remove or update:")
            for e in stale_entries:
                print(f"      - {e.file}:{e.line} — {e.rule}")
        print("")

    if not passed:
        for fpath, vulns in file_reports.items():
            print(f"❌ [VULNERABILITY DETECTED] in: {fpath}")
            for line, label, sev, snip in vulns:
                print(f"   Line {line:4d} [{sev}]: {label}")
                print(f"              Snippet: '{snip}'")
        print(f"\n❌ [REJECT] {total_vulns} cybersecurity vulnerability/vulnerabilities detected.")
        print("   Security gates are fail-closed. Remediation required before release.")
        sys.exit(EXIT_VIOLATION)
    elif not files_to_scan:
        # TOOL ERROR: zero files in scope means zero rules were evaluated. Reporting this as
        # PASS was the worst case of all: a mis-pointed path, an over-broad `exclude`, or a
        # directory that failed to mount produced a green security certificate for nothing.
        print(f"❌ [REJECT] No application source files found to audit in: {target_dir}")
        print("   Zero files scanned means zero security rules were evaluated, which is not a pass.")
        sys.exit(EXIT_TOOL_ERROR)
    else:
        print(f"✅ [PASS] Zero cybersecurity vulnerabilities detected across {len(files_to_scan)} file(s)!")
        print("   Scope: Syntactic AST patterns, dangerous sink detection, and intra-file taint tracking.")
        print("   Notice: Verifies static patterns & secrets. Does not replace dynamic runtime penetration testing or load audits.")
        print("⭐ If Orthotect helps secure your application, star the project: https://github.com/seotarek/orthotect\n")
        sys.exit(EXIT_PASS)
