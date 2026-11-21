#!/usr/bin/env python3
"""
Orthotect Master Gate Orchestrator
Executes all objective quality gates against a designated target directory.
Supports parallel execution and JSON/Markdown formats.

Exit codes (see core/exit_codes.py):
  0  every gate ran and passed.
  1  at least one gate ran and found a rule violation; the audited code must change.
  2  at least one gate could not run (missing dependency/config/target); the
     environment must change. Takes precedence over 1, because an environment
     failure means the remaining results are incomplete and cannot be trusted.
"""
import sys
import subprocess
import time
import os
import json
from concurrent.futures import ThreadPoolExecutor

try:
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR

try:
    from core.cli_args import (
        positionals as cli_positionals,
        resolve_output_format as cli_resolve_output_format,
    )
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from core.cli_args import (
        positionals as cli_positionals,
        resolve_output_format as cli_resolve_output_format,
    )

OUTPUT_FORMATS = ('json', 'md', 'sarif')


def aggregate_exit_codes(codes):
    """
    Collapses per-gate codes into the worst outcome.
    TOOL_ERROR outranks VIOLATION outranks PASS, so an environment failure is never
    masked by an ordinary violation (nor by a passing gate).
    """
    worst = EXIT_PASS
    for code in codes:
        if code == EXIT_TOOL_ERROR:
            return EXIT_TOOL_ERROR
        if code != EXIT_PASS:
            worst = EXIT_VIOLATION
    return worst


def classify_gate_result(name, returncode):
    """Maps a gate process exit status onto the contract, mapping unknown codes safely."""
    if returncode == EXIT_PASS:
        return EXIT_PASS
    if returncode == EXIT_VIOLATION:
        return EXIT_VIOLATION
    if returncode == EXIT_TOOL_ERROR:
        return EXIT_TOOL_ERROR
    # A gate crashed with an unexpected status (uncaught traceback, signal, OOM kill).
    # That is an environment/tooling failure, never a statement about the audited code.
    return EXIT_TOOL_ERROR


def _load_sarif_module():
    """Loads `core/sarif.py`, anchored to the package so cwd cannot change it."""
    try:
        from core import sarif
        return sarif
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            from core.rule_registry import metadata
            return metadata()
        except Exception:
            return {}


def parse_requested_format(argv):
    """
    Resolves the output format from --json, --md, --format <fmt> or --format=<fmt>.
    Returns 'json', 'md', or None.

    Delegates to `core/cli_args.py`, with the orchestrator-only legacy form
    `run_all_gates.py <dir> json` enabled as a bare trailing token. That option is
    deliberately not enabled in the gates: a project directory literally named
    `json` must remain auditable.
    """
    return cli_resolve_output_format(argv, allowed=OUTPUT_FORMATS, bare_token=True)


def positional_arguments(argv):
    """Returns non-flag arguments, skipping the values bound to value-taking flags."""
    return cli_positionals(argv, bare_format_tokens=OUTPUT_FORMATS)


def run_single_gate(gate_spec, root_dir):
    name, cmd = gate_spec
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=root_dir)
    dur = (time.time() - t0) * 1000
    exit_code = classify_gate_result(name, res.returncode)
    passed = (exit_code == EXIT_PASS)
    return (name, passed, dur, res.stdout, res.stderr, exit_code)

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Parse CLI flags
    args = sys.argv[1:]
    requested_format = parse_requested_format(args)
    is_json = requested_format == 'json'
    is_md = requested_format == 'md'
    is_sarif = requested_format == 'sarif'
    is_fix = '--fix' in args

    # Target path is the first non-flag argument (values bound to --format/--out are skipped)
    positional = positional_arguments(args)
    target_dir = positional[0] if positional else os.path.join(root_dir, 'examples', 'golden-showcase')
    target_dir = os.path.abspath(target_dir)

    if not os.path.exists(target_dir):
        err_msg = f"❌ Error: Target directory does not exist: {target_dir}"
        if is_json:
            print(json.dumps({"error": err_msg, "allPassed": False, "exitCode": EXIT_TOOL_ERROR}, indent=2))
        else:
            print(err_msg)
        # TOOL ERROR: nothing was audited, so this says nothing about the code.
        sys.exit(EXIT_TOOL_ERROR)

    bidi_cmd = ["python3", os.path.join(root_dir, "gates", "gate_bidi_logical.py"), target_dir]
    if is_fix:
        bidi_cmd.append("--fix")
        # Be explicit about remediation scope instead of implying every gate self-heals.
        # Only the BiDi gate performs in-place AST rewriting today; the remaining five
        # gates report violations and require manual remediation.
        if not is_json and not is_md and not is_sarif:
            print("ℹ️  [AUTO-FIX] In-place remediation is enabled for: True BiDi & Logical Properties.")
            print("   Other gates (Contrast, FSM, Anti-Slop, CWV, Security) report violations for manual repair.\n")

    gates = [
        ("WCAG 2.2 Mathematical Contrast", ["python3", os.path.join(root_dir, "gates", "gate_contrast_wcag.py"), target_dir]),
        ("True BiDi & Logical Properties", bidi_cmd),
        ("Finite State Machine Integrity", ["python3", os.path.join(root_dir, "gates", "gate_fsm_integrity.py"), target_dir]),
        ("Anti-Slop Pattern Inspector", ["python3", os.path.join(root_dir, "gates", "gate_no_slop.py"), target_dir]),
        ("DOM & Layout-Shift Budget", ["node", os.path.join(root_dir, "gates", "gate_cwv_budget.mjs"), target_dir]),
        ("Enterprise Security & Threat Audit", ["python3", os.path.join(root_dir, "gates", "gate_security_audit.py"), target_dir])
    ]

    if is_sarif:
        # Ask each gate for its own SARIF document rather than re-deriving findings
        # here: the gate is the only component that knows which rule fired and where.
        # The orchestrator's job is then purely to fold the documents into one run.
        gates = [(name, cmd + ["--format", "sarif"]) for name, cmd in gates]

    overall_start = time.time()

    # Execute gates concurrently for maximum performance
    with ThreadPoolExecutor(max_workers=len(gates)) as executor:
        futures = [executor.submit(run_single_gate, g, root_dir) for g in gates]
        results = [f.result() for f in futures]

    total_dur = (time.time() - overall_start) * 1000
    all_passed = all(r[1] for r in results)
    overall_exit = aggregate_exit_codes([r[5] for r in results])
    tool_errors = [r for r in results if r[5] == EXIT_TOOL_ERROR]

    if is_sarif:
        sarif = _load_sarif_module()
        documents = []
        notifications = []
        for name, passed, dur, out, err, code in results:
            try:
                document = json.loads(out)
            except Exception:
                # A gate that could not produce a document is itself a tool error,
                # and saying so is the whole point of the notifications channel.
                notifications.append({
                    'level': 'error',
                    'message': {'text': f"{name}: gate produced no readable SARIF document "
                                         f"(exit {code}): {(err or out).strip()[:500]}"},
                })
                continue
            if not isinstance(document, dict) or not document.get('runs'):
                notifications.append({
                    'level': 'error',
                    'message': {'text': f"{name}: gate returned a malformed SARIF document (exit {code})."},
                })
                continue
            # Prefix each gate's own tool-error notifications with the gate name so
            # a merged report says which one could not run. `merge_sarif` collects
            # the notifications from the documents themselves, so they are not
            # passed twice.
            for run in document['runs']:
                for invocation in run.get('invocations') or []:
                    for notification in invocation.get('toolExecutionNotifications') or []:
                        notification.setdefault('message', {})
                        text = notification['message'].get('text', '')
                        notification['message']['text'] = f"{name}: {text}"
            documents.append(document)

        merged = sarif.merge_sarif(documents, tool_version=sarif.tool_version(),
                                   notifications=notifications)
        print(json.dumps(merged, indent=2))
        sys.exit(overall_exit)

    if is_json:
        report = {
            "target": target_dir,
            "allPassed": all_passed,
            "exitCode": overall_exit,
            "totalDurationMs": round(total_dur, 2),
            "ruleSet": _rule_set_metadata(),
            "gates": [
                {
                    "name": name,
                    "passed": passed,
                    "exitCode": code,
                    "durationMs": round(dur, 2),
                    "stdout": out.strip(),
                    "stderr": err.strip()
                }
                for name, passed, dur, out, err, code in results
            ]
        }
        print(json.dumps(report, indent=2))
        sys.exit(overall_exit)

    if is_md:
        print(f"### 🏛️ Orthotect Quality Gates Report")
        print(f"**Target:** `{target_dir}` | **Result:** {'✅ CERTIFIED' if all_passed else '❌ REJECTED'} | **Time:** {total_dur:.1f}ms\n")
        print("| Gate Name | Status | Duration |")
        print("| :--- | :---: | :---: |")
        for name, passed, dur, out, err, code in results:
            status_str = "✅ PASS" if passed else ("⛔ TOOL ERROR" if code == EXIT_TOOL_ERROR else "❌ FAIL")
            print(f"| {name} | {status_str} | {dur:.1f}ms |")
        sys.exit(overall_exit)

    # Standard ASCII console output
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║            ORTHOTECT DETERMINISTIC QUALITY GATES              ║")
    print("║     Deterministic High-Integrity Engineering Protocol         ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f" Target Path: {target_dir}\n")

    print(f"{'GATE NAME':<38} {'STATUS':<12} {'TIME':>10}")
    print("─" * 63)
    for name, passed, dur, out, err, code in results:
        if passed:
            status_str = "✅ PASS"
        elif code == EXIT_TOOL_ERROR:
            status_str = "⛔ TOOL ERROR"
        else:
            status_str = "❌ FAIL"
        print(f"{name:<38} {status_str:<12} {dur:>8.1f}ms")
    print("─" * 63)
    print(f"Total Verification Time (Parallel): {total_dur:.1f}ms\n")

    if all_passed:
        print("🎉 ALL GATES PASSED! Target files verified against evaluated interface standards.\n")
        print("   Verified Standards: WCAG 2.2 Contrast, CSS Logical BiDi, FSM Integrity, Anti-Slop, DOM CLS Budget, Enterprise Security Audit.")
        print("   Notice: Verifies deterministic interface and SAST constraints; does not replace production runtime penetration testing or load audits.\n")
        print("⭐ If Orthotect saves your UI from regressions, star the repo on GitHub:")
        print("   https://github.com/seotarek/orthotect\n")
        sys.exit(EXIT_PASS)
    else:
        if tool_errors:
            print("🛠️  VERIFICATION INCOMPLETE! The following gate(s) could not run:\n")
            for name, passed, dur, out, err, code in tool_errors:
                print(f"   - {name}")
            print("\n   This is an environment/configuration failure, not a code violation (exit 2).")
            print("   Fix the tooling above, then re-run: the audited code has not been fully verified.\n")
        if any(r[5] == EXIT_VIOLATION for r in results):
            print("🚨 BUILD FAILED! One or more objective quality gates failed.\n")
        for name, passed, dur, out, err, code in results:
            if not passed:
                label = "gate could not run" if code == EXIT_TOOL_ERROR else "failed gate"
                print(f"\n--- Details for {label}: {name} ---")
                print(out)
                if err:
                    print(err)
        sys.exit(overall_exit)

if __name__ == '__main__':
    main()
