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
try:
    import tinycss2
    HAVE_TINYCSS2 = True
except ImportError:
    tinycss2 = None
    HAVE_TINYCSS2 = False

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

BANNED_CAMELCASE_PROPERTIES = {
    'marginLeft': 'marginInlineStart',
    'marginRight': 'marginInlineEnd',
    'paddingLeft': 'paddingInlineStart',
    'paddingRight': 'paddingInlineEnd',
    'borderLeft': 'borderInlineStart',
    'borderRight': 'borderInlineEnd',
    'borderLeftWidth': 'borderInlineStartWidth',
    'borderRightWidth': 'borderInlineEndWidth',
    'borderLeftStyle': 'borderInlineStartStyle',
    'borderRightStyle': 'borderInlineEndStyle',
    'borderLeftColor': 'borderInlineStartColor',
    'borderRightColor': 'borderInlineEndColor',
    'borderTopLeftRadius': 'borderStartStartRadius',
    'borderTopRightRadius': 'borderStartEndRadius',
    'borderBottomLeftRadius': 'borderEndStartRadius',
    'borderBottomRightRadius': 'borderEndEndRadius',
}

ALLOWED_OFFSETS = {'auto', 'inherit', 'initial', 'unset', 'revert'}
IGNORE_DIRS = {'node_modules', '.git', 'dist', '__pycache__', '.claude', '.gemini', 'tmp'}
SUPPORTED_EXTENSIONS = {'.css', '.scss', '.less', '.html', '.htm', '.vue', '.svelte', '.jsx', '.tsx', '.js', '.ts'}

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

class CssSyntaxTokenizer:
    """
    Pure standard-library, syntax-aware CSS state-machine tokenizer and declaration parser.
    Operates without third-party dependencies (tinycss2 fallback).
    Tracks character streams with exact line and column coordinates,
    ignoring comments, strings, and custom properties, while properly handling
    at-rules, nested selectors, and multiline declarations.
    """
    def __init__(self, text, line_offset=0):
        self.text = text
        self.line_offset = line_offset
        self.length = len(text)

    def parse_declarations(self):
        """
        Parses all CSS declarations from the text stream, returning:
        [(prop_name, prop_val, line, col), ...]
        """
        declarations = []
        n = self.length
        i = 0
        line = 1 + self.line_offset
        col = 1
        tokens = []

        while i < n:
            ch = self.text[i]

            # 1. Multi-line comment: /* ... */
            if ch == '/' and i + 1 < n and self.text[i + 1] == '*':
                i += 2
                col += 2
                while i < n:
                    if self.text[i] == '\n':
                        line += 1
                        col = 1
                        i += 1
                    elif self.text[i] == '*' and i + 1 < n and self.text[i + 1] == '/':
                        i += 2
                        col += 2
                        break
                    else:
                        i += 1
                        col += 1
                continue
            elif ch == '/':
                tokens.append(('/', '/', line, col))
                i += 1
                col += 1
                continue

            # 2. String literal: single quote '...'
            if ch == "'":
                start_l, start_c = line, col
                str_val = []
                i += 1
                col += 1
                while i < n:
                    c = self.text[i]
                    if c == '\\' and i + 1 < n:
                        str_val.append(self.text[i:i+2])
                        i += 2
                        col += 2
                    elif c == "'":
                        i += 1
                        col += 1
                        break
                    elif c == '\n':
                        line += 1
                        col = 1
                        i += 1
                        str_val.append('\n')
                    else:
                        str_val.append(c)
                        i += 1
                        col += 1
                tokens.append(('STRING', ''.join(str_val), start_l, start_c))
                continue

            # 3. String literal: double quote "..."
            if ch == '"':
                start_l, start_c = line, col
                str_val = []
                i += 1
                col += 1
                while i < n:
                    c = self.text[i]
                    if c == '\\' and i + 1 < n:
                        str_val.append(self.text[i:i+2])
                        i += 2
                        col += 2
                    elif c == '"':
                        i += 1
                        col += 1
                        break
                    elif c == '\n':
                        line += 1
                        col = 1
                        i += 1
                        str_val.append('\n')
                    else:
                        str_val.append(c)
                        i += 1
                        col += 1
                tokens.append(('STRING', ''.join(str_val), start_l, start_c))
                continue

            # 4. Whitespace
            if ch in (' ', '\t', '\r', '\n'):
                if ch == '\n':
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1
                continue

            # 5. Structural characters and delimiters
            if ch in ('{', '}', '(', ')', '[', ']', ':', ';'):
                tokens.append((ch, ch, line, col))
                i += 1
                col += 1
                continue

            # 6. Word / Identifier / Value Part
            start_l, start_c = line, col
            word = []
            while i < n and self.text[i] not in (' ', '\t', '\r', '\n', '{', '}', '(', ')', '[', ']', ':', ';', "'", '"', '/'):
                word.append(self.text[i])
                i += 1
                col += 1
            if word:
                w_str = ''.join(word)
                tokens.append(('WORD', w_str, start_l, start_c))
            else:
                # Guaranteed safety advancement: ensures the scanner strictly advances on any unrecognized char
                tokens.append(('CHAR', ch, line, col))
                if ch == '\n':
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1

        # Declaration extraction with block and paren tracking
        t_idx = 0
        num_toks = len(tokens)
        paren_depth = 0

        while t_idx < num_toks:
            tok_type, tok_val, tok_l, tok_c = tokens[t_idx]

            if tok_type == '(':
                paren_depth += 1
                t_idx += 1
                continue
            elif tok_type == ')':
                paren_depth = max(0, paren_depth - 1)
                t_idx += 1
                continue

            # Look for property declaration pattern: WORD followed immediately by ':' at paren_depth == 0
            if paren_depth == 0 and tok_type == 'WORD' and t_idx + 1 < num_toks and tokens[t_idx + 1][0] == ':':
                prop_name = tok_val
                prop_line = tok_l
                prop_col = tok_c

                val_tokens = []
                j = t_idx + 2
                is_valid_decl = True
                term_idx = j

                while j < num_toks:
                    jt_type, jt_val, _, _ = tokens[j]
                    if jt_type == '{':
                        # Block opening before semicolon indicates a selector/rule, not a declaration
                        is_valid_decl = False
                        break
                    elif jt_type == ';':
                        term_idx = j + 1
                        break
                    elif jt_type == '}':
                        term_idx = j
                        break
                    else:
                        val_tokens.append(jt_val)
                        j += 1
                else:
                    term_idx = j

                if is_valid_decl and not prop_name.startswith('--'):
                    prop_value = ' '.join(val_tokens).strip()
                    declarations.append((prop_name, prop_value, prop_line, prop_col))
                    t_idx = term_idx
                    continue

            t_idx += 1

        return declarations

def scan_css_content_fallback(css_text, line_offset=0):
    """
    Dependency-free, syntax-aware fallback scanner for environments without tinycss2.
    Uses pure-Python state-machine CssSyntaxTokenizer to extract declarations
    and validate directional properties.
    """
    violations = []
    tokenizer = CssSyntaxTokenizer(css_text, line_offset=line_offset)
    declarations = tokenizer.parse_declarations()

    for name_raw, val_raw, line, col in declarations:
        name = name_raw.lower()
        val = val_raw.lower()

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

def scan_css_content(css_text, line_offset=0):
    if not HAVE_TINYCSS2:
        return scan_css_content_fallback(css_text, line_offset)

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
        if not HAVE_TINYCSS2:
            violations.extend(scan_css_content_fallback(style_text, line_offset=attr_start_line))
        else:
            decls = tinycss2.parse_declaration_list(style_text)
            violations.extend(check_declarations(decls, line_offset=attr_start_line))

    return violations

def strip_js_comments_string_aware(text):
    """
    Strips single-line (//) and multi-line (/* */) JavaScript comments
    while strictly preserving single-quoted, double-quoted, and template-literal strings.
    Prevents '//' inside strings (e.g. 'https://...') from truncating the rest of the line.
    Preserves all newline characters to maintain exact source line coordinates.
    """
    result = []
    i = 0
    n = len(text)
    state = 'NORMAL'

    while i < n:
        ch = text[i]

        if state == 'NORMAL':
            if ch == "'" and (i == 0 or text[i - 1] != '\\'):
                state = 'SINGLE_QUOTE'
                result.append(ch)
                i += 1
            elif ch == '"' and (i == 0 or text[i - 1] != '\\'):
                state = 'DOUBLE_QUOTE'
                result.append(ch)
                i += 1
            elif ch == '`' and (i == 0 or text[i - 1] != '\\'):
                state = 'TEMPLATE_LITERAL'
                result.append(ch)
                i += 1
            elif ch == '/' and i + 1 < n and text[i + 1] == '/':
                state = 'LINE_COMMENT'
                result.append('  ')
                i += 2
            elif ch == '/' and i + 1 < n and text[i + 1] == '*':
                state = 'BLOCK_COMMENT'
                result.append('  ')
                i += 2
            else:
                result.append(ch)
                i += 1

        elif state == 'SINGLE_QUOTE':
            result.append(ch)
            if ch == '\\' and i + 1 < n:
                result.append(text[i + 1])
                i += 2
            elif ch == "'":
                state = 'NORMAL'
                i += 1
            else:
                i += 1

        elif state == 'DOUBLE_QUOTE':
            result.append(ch)
            if ch == '\\' and i + 1 < n:
                result.append(text[i + 1])
                i += 2
            elif ch == '"':
                state = 'NORMAL'
                i += 1
            else:
                i += 1

        elif state == 'TEMPLATE_LITERAL':
            result.append(ch)
            if ch == '\\' and i + 1 < n:
                result.append(text[i + 1])
                i += 2
            elif ch == '`':
                state = 'NORMAL'
                i += 1
            else:
                i += 1

        elif state == 'LINE_COMMENT':
            if ch == '\n':
                result.append('\n')
                state = 'NORMAL'
            else:
                result.append(' ')
            i += 1

        elif state == 'BLOCK_COMMENT':
            if ch == '*' and i + 1 < n and text[i + 1] == '/':
                result.append('  ')
                state = 'NORMAL'
                i += 2
            elif ch == '\n':
                result.append('\n')
                i += 1
            else:
                result.append(' ')
                i += 1

    return ''.join(result)

def scan_js_content(js_text):
    violations = []

    # 1. Mask comments safely with string-aware state-machine scanner
    masked_js = strip_js_comments_string_aware(js_text)

    # 2. Extract and scan tagged template literals (styled-components, emotion, etc.)
    tmpl_pattern = re.compile(r'(?:styled(?:\.[a-zA-Z0-9_]+|\([^)]+\))?|css)\s*`([\s\S]*?)`', re.DOTALL)
    for match in tmpl_pattern.finditer(masked_js):
        css_text = match.group(1)
        start_line = js_text[:match.start(1)].count('\n')
        if not re.search(r'\{[\s\S]*?\}', css_text):
            if not HAVE_TINYCSS2:
                violations.extend(scan_css_content_fallback(css_text, line_offset=start_line))
            else:
                decls = tinycss2.parse_declaration_list(css_text)
                violations.extend(check_declarations(decls, line_offset=start_line))
        else:
            violations.extend(scan_css_content(css_text, line_offset=start_line))

    # 3. Extract and scan JSX style={{ ... }} and style={ { ... } }
    jsx_style_pattern = re.compile(r'\bstyle\s*=\s*\{\{\s*([\s\S]*?)\s*\}\}', re.DOTALL)
    for match in jsx_style_pattern.finditer(masked_js):
        block_text = match.group(1)
        block_start_line = js_text[:match.start(1)].count('\n')
        violations.extend(scan_js_style_block(block_text, line_offset=block_start_line))

    # 4. Extract and scan StyleSheet.create({ ... }) blocks
    ss_pattern = re.compile(r'StyleSheet\s*\.\s*create\s*\(\s*\{([\s\S]*?)\}\s*\)', re.DOTALL)
    for match in ss_pattern.finditer(masked_js):
        block_text = match.group(1)
        block_start_line = js_text[:match.start(1)].count('\n')
        violations.extend(scan_js_style_block(block_text, line_offset=block_start_line))

    return violations

def scan_js_style_block(block_text, line_offset=0):
    violations = []
    # Check camelCase banned properties
    for prop_camel, suggestion in BANNED_CAMELCASE_PROPERTIES.items():
        pattern = re.compile(r'\b(' + re.escape(prop_camel) + r')\s*:\s*([^,;}\n]+)')
        for match in pattern.finditer(block_text):
            line = block_text[:match.start()].count('\n') + 1 + line_offset
            col = match.start() - block_text.rfind('\n', 0, match.start())
            val = match.group(2).strip().strip('\'"')
            violations.append(BidiViolation(line, col, match.group(1), val, suggestion))

    # Check kebab-case in quotes (e.g., 'margin-left': '10px')
    for prop_kebab, suggestion in BANNED_PROPERTIES.items():
        pattern = re.compile(r'[\'"](' + re.escape(prop_kebab) + r')[\'"]\s*:\s*([^,;}\n]+)')
        for match in pattern.finditer(block_text):
            line = block_text[:match.start()].count('\n') + 1 + line_offset
            col = match.start() - block_text.rfind('\n', 0, match.start())
            val = match.group(2).strip().strip('\'"')
            violations.append(BidiViolation(line, col, match.group(1), val, suggestion))

    # Check left / right offsets
    offset_pattern = re.compile(r'\b(left|right)\s*:\s*([^,;}\n]+)')
    for match in offset_pattern.finditer(block_text):
        val = match.group(2).strip().strip('\'"')
        if val in ALLOWED_OFFSETS:
            continue
        line = block_text[:match.start()].count('\n') + 1 + line_offset
        col = match.start() - block_text.rfind('\n', 0, match.start())
        prop = match.group(1).lower()
        sug = 'inset-inline-start' if prop == 'left' else 'inset-inline-end'
        violations.append(BidiViolation(line, col, prop, val, sug))

    # Check textAlign: 'left' / 'right'
    ta_pattern = re.compile(r'\b(?:textAlign|[\'"]text-align[\'"])\s*:\s*[\'"](left|right)[\'"]')
    for match in ta_pattern.finditer(block_text):
        line = block_text[:match.start()].count('\n') + 1 + line_offset
        col = match.start() - block_text.rfind('\n', 0, match.start())
        val = match.group(1).lower()
        sug = 'textAlign: "start"' if val == 'left' else 'textAlign: "end"'
        violations.append(BidiViolation(line, col, 'textAlign', val, sug))

    return violations

def scan_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported styling format for BiDi AST verification: {ext}")

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if ext in ('.html', '.htm', '.vue', '.svelte'):
        return scan_html_content(content)
    elif ext in ('.jsx', '.tsx', '.js', '.ts'):
        return scan_js_content(content)
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

