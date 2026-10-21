#!/usr/bin/env python3
"""
Orthotect Gate: AI Slop Detector
Rejects typical statistical AI defaults:
- Hardcoded purple/indigo gradients (e.g., linear-gradient(from indigo to purple))
- Raw emojis used as icons inside interactive buttons and primary headings
- Hardcoded absolute pixel values bypassing DTCG tokens
"""
import sys
import os
import re

SLOP_PATTERNS = [
    (r'linear-gradient\s*\([^)]*(#6366f1|#a855f7|indigo|purple)[^)]*\)', 'Hardcoded Generic AI Purple/Indigo Gradient'),
    (r'<button[^>]*>[^<]*[🚀🔥✨💡🎉📈📊🧠🤖][^<]*</button>', 'Raw Emoji used as Button Icon instead of SVG vector'),
    (r'<h[1-3][^>]*>[^<]*[🚀🔥✨💡🎉📈📊🧠🤖]', 'Raw Emoji used in Primary Heading (violates enterprise doctrine)'),
    (r'style="[^"]*(#[0-9a-fA-F]{3,6}|rgb\([^)]+\))[^"]*"', 'Inline hardcoded color bypassing DTCG token layer'),
]

IGNORE_DIRS = {'node_modules', '.git', 'dist', '__pycache__', '.claude'}
EXTENSIONS = {'.html', '.jsx', '.tsx', '.vue', '.svelte'}

def scan_file(filepath):
    findings = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        for pattern, label in SLOP_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for m in matches:
                # Find line number
                line_no = content.count('\n', 0, m.start()) + 1
                matched_snippet = m.group(0)[:80].replace('\n', ' ')
                findings.append((line_no, label, matched_snippet))
    return findings

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else 'examples'
    if not os.path.exists(target_dir):
        target_dir = '.'

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: Anti-Slop Architectural Guardian")
    print("═══════════════════════════════════════════════════════════════")

    total_slop = 0
    scanned_files = 0

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in EXTENSIONS:
                scanned_files += 1
                fpath = os.path.join(root, file)
                findings = scan_file(fpath)
                if findings:
                    print(f"\n❌ [FAIL] AI Slop pattern detected in: {fpath}")
                    for line_no, label, snippet in findings:
                        print(f"   Line {line_no:4d}: {label}")
                        print(f"              Snippet: '{snippet}'")
                    total_slop += len(findings)

    if total_slop == 0:
        print(f"\n✅ [PASS] No AI Slop detected in {scanned_files} files!")
        print("   Zero generic gradients, zero raw emojis as icons, zero untokenized styles.")
        sys.exit(0)
    else:
        print(f"\n❌ [REJECT] {total_slop} slop pattern(s) flagged.")
        sys.exit(1)

if __name__ == '__main__':
    main()
