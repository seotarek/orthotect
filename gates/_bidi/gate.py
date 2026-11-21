"""
Gate entry point: file dispatch, SARIF emission and the CLI.

`scan_file` is the only function the orchestrator and the tests call; it exists
so the extension-to-scanner mapping lives in one place rather than being
repeated in `main` and in the fixer.
"""
import os
import sys

from ._dispatch import scan_file
from ._fix import apply_bidi_fixes_to_file
from ._paths import IGNORE_DIRS, SUPPORTED_EXTENSIONS
from ._runtime import EXIT_PASS, EXIT_TOOL_ERROR, EXIT_VIOLATION
from ._runtime import cli_positionals, is_path_excluded, load_orthotect_config

def _load_sarif_module():
    """Loads `core/sarif.py`, anchored to the package so cwd cannot change it."""
    try:
        from core import sarif
        return sarif
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
        from core import sarif
        return sarif


def _violation_to_finding(violation, filepath):
    """
    Converts a BidiViolation into the neutral finding dict SARIF consumes.

    Kept here rather than in `core/sarif.py` because only this gate knows what a
    BidiViolation is; the SARIF layer stays free of gate-specific types.
    """
    return {
        'file': filepath,
        'line': violation.line,
        'column': getattr(violation, 'col', 0) or 0,
        'label': violation.name,
        'snippet': violation.val or '',
        'suggestion': violation.suggestion,
        'ruleId': getattr(violation, 'rule', None),
    }


def main():
    args = sys.argv[1:]
    # Shared parser: a value bound to a value-taking flag must never be mistaken
    # for the target path. See core/cli_args.py.
    is_fix = '--fix' in args
    positional = cli_positionals(args)
    target_dir = positional[0] if positional else 'examples'

    sarif = _load_sarif_module()
    as_sarif = sarif.sarif_requested(args)

    def fail_tool_error(message, findings=None):
        """
        Emits a tool error in the requested format and exits 2.

        A SARIF document still has to be produced: a CI job that uploads it must
        see "the analysis did not run", not an empty file, which code scanning
        would read as a clean audit.
        """
        if as_sarif:
            sarif.print_gate_sarif('gate_bidi_logical', findings or [],
                                   os.path.abspath(target_dir), tool_error=message)
        else:
            print(f"❌ [REJECT] {message}")
        sys.exit(EXIT_TOOL_ERROR)

    if not os.path.exists(target_dir):
        fail_tool_error(f"Target path not found: {target_dir}")

    # Load configuration if available
    config = None
    allow_camel_case = False
    if load_orthotect_config:
        config, _ = load_orthotect_config(target_dir)
        try:
            from core.config import get_bidi_config
            allow_camel_case = bool(get_bidi_config(config).get('allowCamelCase', False))
        except Exception:
            allow_camel_case = False

    if not as_sarif:
        print("═══════════════════════════════════════════════════════════════")
        print(f"  ORTHOTECT GATE: True BiDi Logical Properties Check (AST){' [AUTO-FIX MODE]' if is_fix else ''}")
        print("═══════════════════════════════════════════════════════════════")

    total_files = 0
    total_violations = 0
    fixed_files_count = 0
    fixed_violations_count = 0
    all_findings = []

    if os.path.isfile(target_dir):
        files_to_scan = [(os.path.dirname(target_dir), os.path.basename(target_dir))]
    else:
        files_to_scan = []
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not (is_path_excluded and is_path_excluded(os.path.join(root, d), config, target_dir))]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    fpath = os.path.join(root, file)
                    if is_path_excluded and is_path_excluded(fpath, config, target_dir):
                        continue
                    files_to_scan.append((root, file))

    for root, file in files_to_scan:
        total_files += 1
        fpath = os.path.join(root, file)
        try:
            viols = scan_file(fpath, allow_camel_case=allow_camel_case)
        except Exception as e:
            if not as_sarif:
                print(f"\n❌ [FAIL] Error evaluating styling in {fpath}: {e}")
            total_violations += 1
            all_findings.append({
                'file': fpath, 'line': 1, 'label': 'PARSE_ERROR',
                'snippet': str(e), 'suggestion': 'Fix the file so it can be scanned',
            })
            continue

        if viols and is_fix:
            try:
                num_fixed, _, remaining = apply_bidi_fixes_to_file(
                    fpath, allow_camel_case=allow_camel_case)
            except Exception as e:
                # An unreadable/unwritable file is a tool error, not a code defect.
                fail_tool_error(f"Auto-fix failed in {fpath}: {e}",
                                [_violation_to_finding(v, fpath) for v in viols])

            if num_fixed > 0:
                fixed_files_count += 1
                fixed_violations_count += num_fixed
            # Post-fix verification: a repair is only accepted if the file now
            # scans clean. A partial fix must fail loudly rather than report
            # partial success and leave the reason implicit.
            if remaining and not as_sarif:
                print(f"\n⚠️  [PARTIAL FIX] {fpath}: {len(remaining)} violation(s) remain "
                      f"after auto-fix ({num_fixed} repaired).")
                print("   This file still violates the BiDi contract and will not pass.")
                print("   Auto-fix cannot rewrite this construct; apply the suggestion manually.")
            viols = remaining

        if viols:
            if not as_sarif:
                print(f"\n❌ [FAIL] Physical direction properties found in: {fpath}")
                for v in viols:
                    line_no, content, suggestion = v
                    col_str = f":{v.col}" if hasattr(v, 'col') and v.col else ""
                    print(f"   Line {line_no:4d}{col_str}: {content}")
                    print(f"              ↪ Suggestion: Replace with '{suggestion}'")
            all_findings.extend(_violation_to_finding(v, fpath) for v in viols)
            total_violations += len(viols)

    if total_files == 0:
        fail_tool_error(
            f"No styling or markup files ({', '.join(sorted(SUPPORTED_EXTENSIONS))}) "
            f"found in: {target_dir}. Orthotect cannot certify BiDi compliance on an empty project.")

    if as_sarif:
        sarif.print_gate_sarif('gate_bidi_logical', all_findings, os.path.abspath(target_dir))
        sys.exit(EXIT_PASS if total_violations == 0 else EXIT_VIOLATION)

    if is_fix and fixed_violations_count > 0:
        print(f"\n✨ [AUTO-FIX] Repaired {fixed_violations_count} violation(s) across {fixed_files_count} file(s).")
        if total_violations > 0:
            # Never let the repair count read as a clean result while the build
            # is still red. --fix repairs what it can; it does not certify.
            print(f"   ⚠️  {total_violations} violation(s) still unresolved — this run did not certify the target.")
            print("   Auto-fix is a convenience, not a guarantee: re-run without --fix to see what remains.")

    if total_violations == 0:
        print(f"\n✅ [PASS] BiDi Logical Check Passed! Scanned {total_files} file(s) via CSS AST.")
        print("   All layout rules use directional-independent logical properties.")
        sys.exit(EXIT_PASS)
    else:
        print(f"\n❌ [REJECT] {total_violations} physical direction violation(s) found.")
        sys.exit(EXIT_VIOLATION)
