#!/usr/bin/env python3
"""
Orthotect Master Gate Orchestrator
Executes all objective quality gates against a designated target directory.
Exits with 0 ONLY if all gates pass. Supports parallel execution and JSON/Markdown formats.
"""
import sys
import subprocess
import time
import os
import json
from concurrent.futures import ThreadPoolExecutor

def run_single_gate(gate_spec, root_dir):
    name, cmd = gate_spec
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=root_dir)
    dur = (time.time() - t0) * 1000
    passed = (res.returncode == 0)
    return (name, passed, dur, res.stdout, res.stderr)

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Parse CLI flags
    args = sys.argv[1:]
    is_json = '--json' in args or ('--format' in args and 'json' in args)
    is_md = '--md' in args or ('--format' in args and 'md' in args)
    is_fix = '--fix' in args
    
    # Target path is first non-flag argument
    positional = [a for a in args if not a.startswith('--') and a not in ('json', 'md')]
    target_dir = positional[0] if positional else os.path.join(root_dir, 'examples', 'golden-showcase')
    target_dir = os.path.abspath(target_dir)

    if not os.path.exists(target_dir):
        err_msg = f"❌ Error: Target directory does not exist: {target_dir}"
        if is_json:
            print(json.dumps({"error": err_msg, "allPassed": False}))
        else:
            print(err_msg)
        sys.exit(1)

    bidi_cmd = ["python3", os.path.join(root_dir, "gates", "gate_bidi_logical.py"), target_dir]
    if is_fix:
        bidi_cmd.append("--fix")

    gates = [
        ("WCAG 2.2 Mathematical Contrast", ["python3", os.path.join(root_dir, "gates", "gate_contrast_wcag.py"), target_dir]),
        ("True BiDi & Logical Properties", bidi_cmd),
        ("Finite State Machine Integrity", ["python3", os.path.join(root_dir, "gates", "gate_fsm_integrity.py"), target_dir]),
        ("Anti-Slop Pattern Inspector", ["python3", os.path.join(root_dir, "gates", "gate_no_slop.py"), target_dir]),
        ("DOM & Layout-Shift Budget", ["node", os.path.join(root_dir, "gates", "gate_cwv_budget.mjs"), target_dir]),
        ("Enterprise Security & Threat Audit", ["python3", os.path.join(root_dir, "gates", "gate_security_audit.py"), target_dir])
    ]

    overall_start = time.time()

    # Execute gates concurrently for maximum performance
    with ThreadPoolExecutor(max_workers=len(gates)) as executor:
        futures = [executor.submit(run_single_gate, g, root_dir) for g in gates]
        results = [f.result() for f in futures]

    total_dur = (time.time() - overall_start) * 1000
    all_passed = all(r[1] for r in results)

    if is_json:
        report = {
            "target": target_dir,
            "allPassed": all_passed,
            "totalDurationMs": round(total_dur, 2),
            "gates": [
                {
                    "name": name,
                    "passed": passed,
                    "durationMs": round(dur, 2),
                    "stdout": out.strip(),
                    "stderr": err.strip()
                }
                for name, passed, dur, out, err in results
            ]
        }
        print(json.dumps(report, indent=2))
        sys.exit(0 if all_passed else 1)

    if is_md:
        print(f"### 🏛️ Orthotect Quality Gates Report")
        print(f"**Target:** `{target_dir}` | **Result:** {'✅ CERTIFIED' if all_passed else '❌ REJECTED'} | **Time:** {total_dur:.1f}ms\n")
        print("| Gate Name | Status | Duration |")
        print("| :--- | :---: | :---: |")
        for name, passed, dur, out, err in results:
            status_str = "✅ PASS" if passed else "❌ FAIL"
            print(f"| {name} | {status_str} | {dur:.1f}ms |")
        sys.exit(0 if all_passed else 1)

    # Standard ASCII console output
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║            ORTHOTECT DETERMINISTIC QUALITY GATES              ║")
    print("║     Deterministic High-Integrity Engineering Protocol         ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f" Target Path: {target_dir}\n")

    print(f"{'GATE NAME':<38} {'STATUS':<10} {'TIME':>10}")
    print("─" * 63)
    for name, passed, dur, out, err in results:
        status_str = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<38} {status_str:<10} {dur:>8.1f}ms")
    print("─" * 63)
    print(f"Total Verification Time (Parallel): {total_dur:.1f}ms\n")

    if all_passed:
        print("🎉 ALL GATES PASSED! Target files verified against evaluated interface standards.\n")
        print("   Verified Standards: WCAG 2.2 Contrast, CSS Logical BiDi, FSM Integrity, Anti-Slop, DOM CLS Budget, Enterprise Security Audit.")
        print("   Notice: Verifies deterministic interface and SAST constraints; does not replace production runtime penetration testing or load audits.\n")
        sys.exit(0)
    else:
        print("🚨 BUILD FAILED! One or more objective quality gates failed.\n")
        for name, passed, dur, out, err in results:
            if not passed:
                print(f"\n--- Details for failed gate: {name} ---")
                print(out)
                if err:
                    print(err)
        sys.exit(1)

if __name__ == '__main__':
    main()
