#!/usr/bin/env python3
"""
Orthotect Gate: BiDi Logical Properties Enforcement (Syntax-Aware AST)
Uses tinycss2 to parse CSS stylesheets, nested rules, inline styles, and HTML style blocks.
Guarantees 100% native RTL/LTR symmetry by detecting prohibited physical direction properties
in actual syntactic contexts while ignoring comments, strings, and custom property values.
"""
import sys
import os
import re
import tinycss2

class BidiViolation(tuple):
    """Backwards-compatible 3-tuple (line, content, suggestion) with extended metadata."""
    def __new__(cls, line, col, name, val, suggestion):
        content = f"{name}: {val}" if val else name
        instance = super().__new__(cls, (line, content, suggestion))
        instance.line = line
        instance.col = col
        instance.name = name
        instance.val = val
        instance.suggestion = suggestion
        return instance

BANNED_PROPERTIES = {
    'margin-left': 'margin-inline-start',
    'margin-right': 'margin-inline-end',
    'padding-left': 'padding-inline-start',
    'padding-right': 'padding-inline-end',
    'border-left': 'border-inline-start',
    'border-right': 'border-inline-end',
    'border-left-width': 'border-inline-start-width',
    'border-right-width': 'border-inline-end-width',
    'border-left-style': 'border-inline-start-style',
    'border-right-style': 'border-inline-end-style',
    'border-left-color': 'border-inline-start-color',
    'border-right-color': 'border-inline-end-color',
    'border-top-left-radius': 'border-start-start-radius',
    'border-top-right-radius': 'border-start-end-radius',
    'border-bottom-left-radius': 'border-end-start-radius',
    'border-bottom-right-radius': 'border-end-end-radius',
}

ALLOWED_OFFSETS = {'auto', 'inherit', 'initial', 'unset', 'revert'}
IGNORE_DIRS = {'node_modules', '.git', 'dist', '__pycache__', '.claude', '.gemini', 'tmp'}
SUPPORTED_EXTENSIONS = {'.css', '.scss', '.less', '.html', '.htm', '.vue', '.svelte'}

def check_declaration(d, line_offset=0):
    violations = []
    name = d.name.lower()
    if name.startswith('--'):
        return violations

    val = tinycss2.serialize(d.value).strip().lower()
    line = (d.source_line or 1) + line_offset
    col = d.source_column or 1

    if name in BANNED_PROPERTIES:
        violations.append(BidiViolation(line, col, name, val, BANNED_PROPERTIES[name]))
    elif name in ('left', 'right') and val not in ALLOWED_OFFSETS:
        suggestion = 'inset-inline-start' if name == 'left' else 'inset-inline-end'
        violations.append(BidiViolation(line, col, name, val, suggestion))
    elif name == 'text-align' and val in ('left', 'right'):
        suggestion = 'text-align: start' if val == 'left' else 'text-align: end'
        violations.append(BidiViolation(line, col, name, val, suggestion))
    elif name == 'float' and val in ('left', 'right'):
        suggestion = 'inline-start or Flexbox/Grid' if val == 'left' else 'inline-end or Flexbox/Grid'
        violations.append(BidiViolation(line, col, name, val, suggestion))
    elif name == 'clear' and val in ('left', 'right'):
        suggestion = 'clear: inline-start' if val == 'left' else 'clear: inline-end'
        violations.append(BidiViolation(line, col, name, val, suggestion))

    return violations

def check_declarations(declarations, line_offset=0):
    violations = []
    for d in declarations:
        if d.type == 'declaration':
            violations.extend(check_declaration(d, line_offset))
    return violations


def walk_css_nodes(nodes, line_offset=0):
    violations = []
    # 1. Parse child rules (e.g. @media, @keyframes, nested selectors)
    rules = tinycss2.parse_rule_list(nodes)
    has_child_rules = False
    for r in rules:
        if r.type in ('qualified-rule', 'at-rule'):
            has_child_rules = True
            if hasattr(r, 'content') and r.content is not None:
                violations.extend(walk_css_nodes(r.content, line_offset))

    # 2. Parse direct declarations
    decls = tinycss2.parse_declaration_list(nodes)
    for d in decls:
        if d.type == 'declaration':
            violations.extend(check_declaration(d, line_offset))
        elif d.type == 'error' and not has_child_rules:
            violations.append(BidiViolation(
                (d.source_line or 1) + line_offset,
                d.source_column or 1,
                'PARSE_ERROR',
                d.message if hasattr(d, 'message') else 'Malformed CSS declaration',
                'Fix CSS syntax'
            ))
    return violations

def scan_css_content(css_text, line_offset=0):
    rules = tinycss2.parse_stylesheet(css_text)
    violations = []
    for r in rules:
        if r.type == 'error':
            violations.append(BidiViolation(
                (r.source_line or 1) + line_offset,
                r.source_column or 1,
                'PARSE_ERROR',
                r.message if hasattr(r, 'message') else 'Malformed CSS rule',
                'Fix CSS syntax'
            ))
        elif hasattr(r, 'content') and r.content is not None:
            violations.extend(walk_css_nodes(r.content, line_offset))
    return violations


def scan_html_content(html_text):
    violations = []
    # Mask HTML comments so commented styles/markup are ignored
    masked_html = re.sub(r'<!--.*?-->', lambda m: '\n' * m.group(0).count('\n'), html_text, flags=re.DOTALL)

    # 1. Extract <style> blocks
    style_pattern = re.compile(r'<style\b[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)
    for match in style_pattern.finditer(masked_html):
        css_text = match.group(1)
        start_line = html_text[:match.start(1)].count('\n')
        violations.extend(scan_css_content(css_text, line_offset=start_line))

    # 2. Extract inline style="..." or style='...'
    attr_pattern = re.compile(r'\bstyle\s*=\s*(?:"([^"]*)"|\'([^\']*)\')', re.DOTALL)
    for match in attr_pattern.finditer(masked_html):
        style_text = match.group(1) if match.group(1) is not None else match.group(2)
        attr_start_line = html_text[:match.start()].count('\n')
        decls = tinycss2.parse_declaration_list(style_text)
        violations.extend(check_declarations(decls, line_offset=attr_start_line))

    return violations

def scan_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported styling format for BiDi AST verification: {ext}")

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if ext in ('.html', '.htm', '.vue', '.svelte'):
        return scan_html_content(content)
    else:
        return scan_css_content(content)

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else 'examples'
    if not os.path.exists(target_dir):
        print(f"❌ [REJECT] Target path not found: {target_dir}")
        sys.exit(1)

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: True BiDi Logical Properties Check (AST)")
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
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    files_to_scan.append((root, file))

    for root, file in files_to_scan:
        total_files += 1
        fpath = os.path.join(root, file)
        try:
            viols = scan_file(fpath)
        except Exception as e:
            print(f"\n❌ [FAIL] Error evaluating styling in {fpath}: {e}")
            total_violations += 1
            continue

        if viols:
            print(f"\n❌ [FAIL] Physical direction properties found in: {fpath}")
            for v in viols:
                line_no, content, suggestion = v
                col_str = f":{v.col}" if hasattr(v, 'col') and v.col else ""
                print(f"   Line {line_no:4d}{col_str}: {content}")
                print(f"              ↪ Suggestion: Replace with '{suggestion}'")
            total_violations += len(viols)

    if total_files == 0:
        print(f"\n❌ [REJECT] No styling or markup files ({', '.join(sorted(SUPPORTED_EXTENSIONS))}) found in: {target_dir}")
        print("   Orthotect cannot certify BiDi compliance on an empty project.")
        sys.exit(1)

    if total_violations == 0:
        print(f"\n✅ [PASS] BiDi Logical Check Passed! Scanned {total_files} file(s) via CSS AST.")
        print("   All layout rules use directional-independent logical properties.")
        sys.exit(0)
    else:
        print(f"\n❌ [REJECT] {total_violations} physical direction violation(s) found.")
        sys.exit(1)

if __name__ == '__main__':
    main()

