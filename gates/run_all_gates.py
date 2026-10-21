#!/usr/bin/env python3
"""
Orthotect Master Gate Orchestrator
Executes all objective quality gates against a designated target directory.
Exits with 0 ONLY if all gates pass.
"""
import sys
import subprocess
import time
import os

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
    
    # Target directory to verify
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root_dir, 'examples', 'golden-showcase')
    target_dir = os.path.abspath(target_dir)

    if not os.path.exists(target_dir):
        print(f"❌ Error: Target directory does not exist: {target_dir}")
        sys.exit(1)

    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║            ORTHOTECT DETERMINISTIC QUALITY GATES              ║")
    print("║         Google-Scale Interface Engineering Protocol           ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f" Target Path: {target_dir}\n")

    gates = [
        ("WCAG 2.2 Mathematical Contrast", ["python3", os.path.join(root_dir, "gates", "gate_contrast_wcag.py"), target_dir]),
        ("True BiDi & Logical Properties", ["python3", os.path.join(root_dir, "gates", "gate_bidi_logical.py"), target_dir]),
        ("Finite State Machine Integrity", ["python3", os.path.join(root_dir, "gates", "gate_fsm_integrity.py"), target_dir]),
        ("Anti-Slop Pattern Inspector", ["python3", os.path.join(root_dir, "gates", "gate_no_slop.py"), target_dir]),
        ("DOM & Layout-Shift Budget", ["node", os.path.join(root_dir, "gates", "gate_cwv_budget.mjs"), target_dir])
    ]

    overall_start = time.time()

    # Execute gates concurrently for maximum performance
    with ThreadPoolExecutor(max_workers=len(gates)) as executor:
        futures = [executor.submit(run_single_gate, g, root_dir) for g in gates]
        results = [f.result() for f in futures]

    all_passed = all(r[1] for r in results)

    print(f"{'GATE NAME':<38} {'STATUS':<10} {'TIME':>10}")
    print("─" * 63)
    for name, passed, dur, out, err in results:
        status_str = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<38} {status_str:<10} {dur:>8.1f}ms")
    print("─" * 63)
    total_dur = (time.time() - overall_start) * 1000
    print(f"Total Verification Time (Parallel): {total_dur:.1f}ms\n")

    if all_passed:
        print("🎉 ALL GATES PASSED! Build certified for enterprise production.\n")
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
