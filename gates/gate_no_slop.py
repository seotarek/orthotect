#!/usr/bin/env python3
"""
Orthotect Gate: Anti-Slop Lexical & Pattern Inspector
Rejects statistical AI anti-patterns across markup and stylesheets:
- Hardcoded purple/indigo gradients (linear-gradient(#6366f1, #a855f7))
- Raw emojis used as icons inside interactive buttons and primary headings
- Hardcoded inline styles bypassing the DTCG token architecture
"""
import sys
import os
import re

SLOP_PATTERNS = [
    (r'linear-gradient\s*\([^)]*(#6366f1|#a855f7|indigo|purple)[^)]*\)', 'Generic AI Purple/Indigo Gradient'),
    (r'<button[^>]*>[^<]*[🚀🔥✨💡🎉📈📊🧠🤖][^<]*</button>', 'Raw Emoji in Button Icon instead of SVG vector'),
    (r'<h[1-3][^>]*>[^<]*[🚀🔥✨💡🎉📈📊🧠🤖]', 'Raw Emoji in Heading element'),
    (r'style="[^"]*(#[0-9a-fA-F]{3,6}|rgb\([^)]+\))[^"]*"', 'Inline style bypassing DTCG tokens'),
]

IGNORE_DIRS = {'node_modules', '.git', 'dist', '__pycache__', '.claude', 'tmp'}
EXTENSIONS = {'.html', '.jsx', '.tsx', '.vue', '.svelte', '.css', '.scss'}

def scan_file(filepath):
    findings = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        for pattern, label in SLOP_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for m in matches:
                line_no = content.count('\n', 0, m.start()) + 1
                snippet = m.group(0)[:70].replace('\n', ' ')
                findings.append((line_no, label, snippet))
    return findings

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else 'examples'
    if not os.path.exists(target_dir):
        print(f"❌ [REJECT] Target path not found: {target_dir}")
        sys.exit(1)

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: Anti-Slop Lexical & Pattern Inspector")
    print("═══════════════════════════════════════════════════════════════")

    total_slop = 0
    scanned_files = 0

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
        scanned_files += 1
        fpath = os.path.join(root, file)
        findings = scan_file(fpath)
        if findings:
            print(f"\n❌ [FAIL] Anti-pattern detected in: {fpath}")
            for line_no, label, snippet in findings:
                print(f"   Line {line_no:4d}: {label}")
                print(f"              Snippet: '{snippet}'")
            total_slop += len(findings)

    if scanned_files == 0:
        print(f"\n❌ [REJECT] No source code files found to inspect in: {target_dir}")
        print("   Orthotect requires verifiable frontend source files.")
        sys.exit(1)

    if total_slop == 0:
        print(f"\n✅ [PASS] No AI Slop detected across {scanned_files} file(s)!")
        sys.exit(0)
    else:
        print(f"\n❌ [REJECT] {total_slop} anti-pattern(s) flagged.")
        sys.exit(1)

if __name__ == '__main__':
    main()
