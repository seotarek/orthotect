#!/usr/bin/env python3
"""
Orthotect Gate: BiDi Logical Properties Enforcement
Ensures that all styling uses CSS Logical Properties (e.g., margin-inline-start)
rather than physical direction properties to guarantee 100% native RTL/LTR layouts.
"""
import sys
import os
import re

BANNED_PATTERNS = [
    (r'\bmargin-left\s*:', 'margin-inline-start'),
    (r'\bmargin-right\s*:', 'margin-inline-end'),
    (r'\bpadding-left\s*:', 'padding-inline-start'),
    (r'\bpadding-right\s*:', 'padding-inline-end'),
    (r'\bborder-left\b(?!-width|-color|-style)', 'border-inline-start'),
    (r'\bborder-right\b(?!-width|-color|-style)', 'border-inline-end'),
    (r'\bborder-top-left-radius\s*:', 'border-start-start-radius'),
    (r'\bborder-top-right-radius\s*:', 'border-start-end-radius'),
    (r'\bborder-bottom-left-radius\s*:', 'border-end-start-radius'),
    (r'\bborder-bottom-right-radius\s*:', 'border-end-end-radius'),
    (r'(?<![\w-])left\s*:\s*(?!auto|inherit|initial)[^;]+;', 'inset-inline-start'),
    (r'(?<![\w-])right\s*:\s*(?!auto|inherit|initial)[^;]+;', 'inset-inline-end'),
    (r'\btext-align\s*:\s*left\b', 'text-align: start'),
    (r'\btext-align\s*:\s*right\b', 'text-align: end'),
    (r'\bfloat\s*:\s*left\b', 'inline-start or Flexbox/Grid'),
    (r'\bfloat\s*:\s*right\b', 'inline-end or Flexbox/Grid'),
]

IGNORE_DIRS = {'node_modules', '.git', 'dist', '__pycache__', '.claude', '.gemini', 'tmp'}
EXTENSIONS = {'.css', '.scss', '.less', '.html', '.jsx', '.tsx', '.vue', '.svelte'}

def scan_file(filepath):
    violations = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            trimmed = line.strip()
            if trimmed.startswith('/*') or trimmed.startswith('//') or trimmed.startswith('*'):
                continue
            for pattern, replacement in BANNED_PATTERNS:
                if re.search(pattern, line):
                    violations.append((idx, line.strip(), replacement))
    return violations

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else 'examples'
    if not os.path.exists(target_dir):
        print(f"❌ Error: Target path not found: {target_dir}")
        sys.exit(1)

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: True BiDi Logical Properties Check")
    print("═══════════════════════════════════════════════════════════════")

    total_files = 0
    total_violations = 0

    if os.path.isfile(target_dir):
        files_to_scan = [(os.path.dirname(target_dir), os.path.basename(target_dir))]
    else:
        files_to_scan = []
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in EXTENSIONS:
                    files_to_scan.append((root, file))

    for root, file in files_to_scan:
        total_files += 1
        fpath = os.path.join(root, file)
        viols = scan_file(fpath)
        if viols:
            print(f"\n❌ [FAIL] Physical direction properties found in: {fpath}")
            for line_no, content, suggestion in viols:
                print(f"   Line {line_no:4d}: {content}")
                print(f"              ↪ Suggestion: Replace with '{suggestion}'")
            total_violations += len(viols)

    if total_files == 0:
        print(f"\n⚠️ [WARN] No style/markup files found to scan in: {target_dir}")
        sys.exit(0)

    if total_violations == 0:
        print(f"\n✅ [PASS] BiDi Logical Check Passed! Scanned {total_files} file(s).")
        print("   All layout rules use directional-independent logical properties.")
        sys.exit(0)
    else:
        print(f"\n❌ [REJECT] {total_violations} physical direction violation(s) found.")
        sys.exit(1)

if __name__ == '__main__':
    main()
