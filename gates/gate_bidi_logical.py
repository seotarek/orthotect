#!/usr/bin/env python3
"""
Orthotect Gate: BiDi Logical Properties Enforcement
Ensures that all styling uses CSS Logical Properties (e.g., margin-inline-start)
rather than physical direction properties (e.g., margin-left) to guarantee 100%
native RTL/LTR bidirectional layout rendering without hacks or separate stylesheets.
"""
import sys
import os
import re

BANNED_PATTERNS = [
    (r'\bmargin-left\s*:', 'margin-inline-start'),
    (r'\bmargin-right\s*:', 'margin-inline-end'),
    (r'\bpadding-left\s*:', 'padding-inline-start'),
    (r'\bpadding-right\s*:', 'padding-inline-end'),
    (r'(?<![\w-])left\s*:\s*(?!auto|inherit|initial)[^;]+;', 'inset-inline-start'),
    (r'(?<![\w-])right\s*:\s*(?!auto|inherit|initial)[^;]+;', 'inset-inline-end'),
    (r'\btext-align\s*:\s*left\b', 'text-align: start'),
    (r'\btext-align\s*:\s*right\b', 'text-align: end'),
    (r'\bfloat\s*:\s*left\b', 'inline-start or Flexbox/Grid'),
    (r'\bfloat\s*:\s*right\b', 'inline-end or Flexbox/Grid'),
]

IGNORE_DIRS = {'node_modules', '.git', 'dist', '__pycache__', '.claude', '.gemini'}
EXTENSIONS = {'.css', '.html', '.jsx', '.tsx', '.vue', '.svelte'}

def scan_file(filepath):
    violations = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            # Skip comments
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
        target_dir = '.'

    total_files = 0
    total_violations = 0

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: True BiDi Logical Properties Check")
    print("═══════════════════════════════════════════════════════════════")

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in EXTENSIONS:
                total_files += 1
                fpath = os.path.join(root, file)
                viols = scan_file(fpath)
                if viols:
                    print(f"\n❌ [FAIL] Physical direction properties found in: {fpath}")
                    for line_no, content, suggestion in viols:
                        print(f"   Line {line_no:4d}: {content}")
                        print(f"              ↪ Suggestion: Replace with '{suggestion}'")
                    total_violations += len(viols)

    if total_violations == 0:
        print(f"\n✅ [PASS] BiDi Logical Check Passed! Checked {total_files} file(s).")
        print("   All layout rules use directional-independent logical properties.")
        sys.exit(0)
    else:
        print(f"\n❌ [REJECT] {total_violations} physical direction violation(s) found.")
        print("   Orthotect enforces CSS Logical Properties to guarantee flawless RTL.")
        sys.exit(1)

if __name__ == '__main__':
    main()
