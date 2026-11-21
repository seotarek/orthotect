"""
CSS, HTML and stylesheet scanning.

`_scan_css_content` is the tinycss2 path; `_scan_css_content_fallback` is the
dependency-free tokenizer used when tinycss2 is absent. Both must enforce
byte-identical rules, which is why both delegate to `evaluate_declaration`
rather than carrying their own checks.
"""
import re

from ._model import BidiViolation
from ._shorthand import check_declaration, check_declarations, evaluate_declaration
from ._runtime import HAVE_TINYCSS2, tinycss2

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
                'Fix CSS syntax',
                rule='bidi.parse-error'
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
    and validate directional properties. Shares `evaluate_declaration` with the
    tinycss2 AST path so both modes enforce byte-identical rules.
    """
    violations = []
    tokenizer = CssSyntaxTokenizer(css_text, line_offset=line_offset)
    declarations = tokenizer.parse_declarations()

    for name_raw, val_raw, line, col in declarations:
        violations.extend(evaluate_declaration(name_raw, val_raw, line, col))

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
                'Fix CSS syntax',
                rule='bidi.parse-error'
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
