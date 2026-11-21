"""
JavaScript, JSX and tagged-template scanning.

Two jobs live here: isolating CSS-looking regions from JS source without being
fooled by strings, comments or regex literals (`strip_js_comments_string_aware`,
`extract_tagged_template_literals`), and evaluating inline style objects
(`scan_js_style_block`).
"""
import re

from ._model import (
    ALLOWED_OFFSETS,
    BANNED_CAMELCASE_PROPERTIES,
    BANNED_PROPERTIES,
    SHORTHAND_PROPERTIES,
    BidiViolation,
)
from ._css import scan_css_content, scan_css_content_fallback
from ._runtime import HAVE_TINYCSS2, tinycss2
from ._shorthand import check_declarations, evaluate_declaration

def is_regex_start(text, i):
    """
    Determines whether a '/' character at index i begins a JavaScript regular expression literal.
    In JavaScript, '/' is a regex literal (rather than division) when it follows punctuation,
    operators, or expression keywords, and is not immediately followed by '/' or '*'.
    """
    j = i - 1
    while j >= 0 and text[j] in ' \t\r\n':
        j -= 1
    if j < 0:
        return True
    prev_ch = text[j]
    if prev_ch in '=(,{[;:!&|?~^+-*<>%':
        return True
    if prev_ch == ')':
        # In JavaScript, ')' before '/' can only precede a regex literal if the matching '(' belongs to a
        # control statement header (if, while, for, with, catch). E.g., `if (test) /pattern/.test(...)`
        # Otherwise, `(a + b) / 2` or `fn() / 2` is arithmetic division.
        depth = 1
        k = j - 1
        while k >= 0 and depth > 0:
            if text[k] == ')':
                depth += 1
            elif text[k] == '(':
                depth -= 1
            k -= 1
        if depth == 0:
            # text[k + 1] was the matching '('
            w = k
            while w >= 0 and text[w] in ' \t\r\n':
                w -= 1
            word_end = w
            while w >= 0 and (text[w].isalnum() or text[w] in '_$'):
                w -= 1
            kw = text[w + 1:word_end + 1]
            if kw in ('if', 'while', 'for', 'with', 'catch'):
                return True
        return False
    k = j
    while k >= 0 and (text[k].isalnum() or text[k] in '_$'):
        k -= 1
    word = text[k + 1:j + 1]
    if word in ('return', 'case', 'typeof', 'delete', 'void', 'throw', 'yield', 'await', 'default'):
        return True
    return False


def strip_js_comments_string_aware(text):
    """
    Strips single-line (//) and multi-line (/* */) JavaScript comments
    while strictly preserving single-quoted, double-quoted, template-literal strings,
    and regular expression literals (e.g. /https?:\\/\\//), including arbitrarily nested
    template literal interpolations (${...}).
    Prevents '//' inside strings or regexes from truncating the rest of the line.
    Preserves all newline characters to maintain exact source line coordinates.
    """
    result = []
    i = 0
    n = len(text)
    stack = []

    while i < n:
        ch = text[i]

        in_expr = bool(stack and isinstance(stack[-1], list) and stack[-1][0] == 'EXPR')

        if not stack or in_expr:
            if ch == "'" and (i == 0 or text[i - 1] != '\\'):
                result.append(ch)
                i += 1
                while i < n:
                    c = text[i]
                    result.append(c)
                    if c == '\\' and i + 1 < n:
                        result.append(text[i + 1])
                        i += 2
                    elif c == "'":
                        i += 1
                        break
                    else:
                        i += 1
                continue

            elif ch == '"' and (i == 0 or text[i - 1] != '\\'):
                result.append(ch)
                i += 1
                while i < n:
                    c = text[i]
                    result.append(c)
                    if c == '\\' and i + 1 < n:
                        result.append(text[i + 1])
                        i += 2
                    elif c == '"':
                        i += 1
                        break
                    else:
                        i += 1
                continue

            elif ch == '`' and (i == 0 or text[i - 1] != '\\'):
                stack.append('TEMPLATE_LITERAL')
                result.append(ch)
                i += 1
                continue

            elif ch == '/' and i + 1 < n and text[i + 1] == '/':
                result.append('  ')
                i += 2
                while i < n:
                    if text[i] == '\n':
                        result.append('\n')
                        i += 1
                        break
                    else:
                        result.append(' ')
                        i += 1
                continue

            elif ch == '/' and i + 1 < n and text[i + 1] == '*':
                result.append('  ')
                i += 2
                while i < n:
                    if text[i] == '*' and i + 1 < n and text[i + 1] == '/':
                        result.append('  ')
                        i += 2
                        break
                    elif text[i] == '\n':
                        result.append('\n')
                        i += 1
                    else:
                        result.append(' ')
                        i += 1
                continue

            elif ch == '/' and i + 1 < n and text[i + 1] not in ('/', '*') and is_regex_start(text, i):
                result.append(ch)
                i += 1
                in_char_class = False
                while i < n:
                    c = text[i]
                    result.append(c)
                    if c == '\\' and i + 1 < n:
                        result.append(text[i + 1])
                        i += 2
                    elif c == '[' and not in_char_class:
                        in_char_class = True
                        i += 1
                    elif c == ']' and in_char_class:
                        in_char_class = False
                        i += 1
                    elif c == '/' and not in_char_class:
                        i += 1
                        while i < n and text[i].isalpha():
                            result.append(text[i])
                            i += 1
                        break
                    elif c == '\n':
                        break
                    else:
                        i += 1
                continue

            elif in_expr and ch == '{':
                stack[-1][1] += 1
                result.append(ch)
                i += 1
                continue

            elif in_expr and ch == '}':
                stack[-1][1] -= 1
                if stack[-1][1] == 0:
                    stack.pop()
                result.append(ch)
                i += 1
                continue

            else:
                result.append(ch)
                i += 1
                continue

        elif stack[-1] == 'TEMPLATE_LITERAL':
            if ch == '\\' and i + 1 < n:
                result.append(ch)
                result.append(text[i + 1])
                i += 2
            elif ch == '$' and i + 1 < n and text[i + 1] == '{':
                stack.append(['EXPR', 1])
                result.append('${')
                i += 2
            elif ch == '`':
                stack.pop()
                result.append(ch)
                i += 1
            else:
                result.append(ch)
                i += 1

    return ''.join(result)


def extract_tagged_template_literals(text):
    """
    Extracts tagged template literals (styled.xxx`...` or css`...`) from JS/TS code.
    Correctly skips nested template literals and expressions inside ${...}, replacing
    interpolations with dummy CSS values (' 0 ') to ensure tinycss2 can parse declarations.
    Preserves original newline and line offsets.
    """
    results = []
    tag_regex = re.compile(r'(?:styled(?:\.[a-zA-Z0-9_]+|\([^)]+\))?|css)\s*`')
    for m in tag_regex.finditer(text):
        start = m.end() - 1  # index of opening `
        i = start + 1
        n = len(text)
        stack = ["TEMPLATE_LITERAL"]
        css_chars = []

        while i < n and stack:
            ch = text[i]
            in_expr = bool(stack and isinstance(stack[-1], list) and stack[-1][0] == "EXPR")

            if not in_expr:
                if ch == "\\" and i + 1 < n:
                    css_chars.append(ch)
                    css_chars.append(text[i + 1])
                    i += 2
                elif ch == "$" and i + 1 < n and text[i + 1] == "{":
                    stack.append(["EXPR", 1])
                    expr_start = i
                    i += 2
                    while i < n and stack and isinstance(stack[-1], list) and stack[-1][0] == "EXPR":
                        ec = text[i]
                        if ec == "\\" and i + 1 < n:
                            i += 2
                        elif ec == '"':
                            i += 1
                            while i < n and text[i] != '"':
                                if text[i] == "\\" and i + 1 < n:
                                    i += 2
                                else:
                                    i += 1
                            if i < n:
                                i += 1
                        elif ec == "'":
                            i += 1
                            while i < n and text[i] != "'":
                                if text[i] == "\\" and i + 1 < n:
                                    i += 2
                                else:
                                    i += 1
                            if i < n:
                                i += 1
                        elif ec == '/' and i + 1 < n and text[i + 1] not in ('/', '*') and is_regex_start(text, i):
                            i += 1
                            in_cc = False
                            while i < n:
                                c = text[i]
                                if c == '\\' and i + 1 < n:
                                    i += 2
                                elif c == '[' and not in_cc:
                                    in_cc = True
                                    i += 1
                                elif c == ']' and in_cc:
                                    in_cc = False
                                    i += 1
                                elif c == '/' and not in_cc:
                                    i += 1
                                    while i < n and text[i].isalpha():
                                        i += 1
                                    break
                                elif c == '\n':
                                    break
                                else:
                                    i += 1
                        elif ec == "`":
                            i += 1
                            nest_stack = 1
                            while i < n and nest_stack > 0:
                                if text[i] == "\\" and i + 1 < n:
                                    i += 2
                                elif text[i] == "`":
                                    nest_stack -= 1
                                    i += 1
                                elif text[i] == "$" and i + 1 < n and text[i + 1] == "{":
                                    i += 2
                                    inner_braces = 1
                                    while i < n and inner_braces > 0:
                                        if text[i] == "{":
                                            inner_braces += 1
                                        elif text[i] == "}":
                                            inner_braces -= 1
                                        i += 1
                                else:
                                    i += 1
                        elif ec == "{":
                            stack[-1][1] += 1
                            i += 1
                        elif ec == "}":
                            stack[-1][1] -= 1
                            if stack[-1][1] == 0:
                                stack.pop()
                            i += 1
                        else:
                            i += 1
                    expr_str = text[expr_start:i]
                    newlines = expr_str.count("\n")
                    css_chars.append(" 0 " + ("\n" * newlines))
                elif ch == "`":
                    stack.pop()
                    i += 1
                    break
                else:
                    css_chars.append(ch)
                    i += 1

        css_text = "".join(css_chars)
        start_line = text[:start + 1].count("\n")
        results.append((css_text, start_line))
    return results


def scan_js_content(js_text, allow_camel_case=False):
    violations = []

    # 1. Mask comments safely with string-aware state-machine scanner
    masked_js = strip_js_comments_string_aware(js_text)

    # 2. Extract and scan tagged template literals (styled-components, emotion, etc.)
    for css_text, start_line in extract_tagged_template_literals(masked_js):
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
        violations.extend(scan_js_style_block(block_text, line_offset=block_start_line,
                                              allow_camel_case=allow_camel_case))

    # 4. Extract and scan StyleSheet.create({ ... }) blocks
    ss_pattern = re.compile(r'StyleSheet\s*\.\s*create\s*\(\s*\{([\s\S]*?)\}\s*\)', re.DOTALL)
    for match in ss_pattern.finditer(masked_js):
        block_text = match.group(1)
        block_start_line = js_text[:match.start(1)].count('\n')
        violations.extend(scan_js_style_block(block_text, line_offset=block_start_line,
                                              allow_camel_case=allow_camel_case))

    return violations


def scan_js_style_block(block_text, line_offset=0, allow_camel_case=False):
    violations = []
    # Check camelCase banned properties. `bidi.allowCamelCase` in orthotect.config.json
    # was documented and deep-merged but never consulted, so the escape hatch silently
    # did nothing for React Native / JSX codebases that cannot use logical properties.
    if not allow_camel_case:
        for prop_camel, suggestion in BANNED_CAMELCASE_PROPERTIES.items():
            pattern = re.compile(r'\b(' + re.escape(prop_camel) + r')\s*:\s*([^,;}\n]+)')
            for match in pattern.finditer(block_text):
                line = block_text[:match.start()].count('\n') + 1 + line_offset
                col = match.start() - block_text.rfind('\n', 0, match.start())
                val = match.group(2).strip().strip('\'"')
                violations.append(BidiViolation(
                    line, col, match.group(1), val, suggestion,
                    rule='bidi.camelcase-property'))

    # Check kebab-case in quotes (e.g., 'margin-left': '10px')
    for prop_kebab, suggestion in BANNED_PROPERTIES.items():
        pattern = re.compile(r'[\'"](' + re.escape(prop_kebab) + r')[\'"]\s*:\s*([^,;}\n]+)')
        for match in pattern.finditer(block_text):
            line = block_text[:match.start()].count('\n') + 1 + line_offset
            col = match.start() - block_text.rfind('\n', 0, match.start())
            val = match.group(2).strip().strip('\'"')
            violations.append(BidiViolation(
                line, col, match.group(1), val, suggestion,
                rule='bidi.physical-direction-property'))

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
        violations.append(BidiViolation(
            line, col, prop, val, sug, rule='bidi.physical-offset'))

    # Check textAlign: 'left' / 'right'
    ta_pattern = re.compile(r'\b(?:textAlign|[\'"]text-align[\'"])\s*:\s*[\'"](left|right)[\'"]')
    for match in ta_pattern.finditer(block_text):
        line = block_text[:match.start()].count('\n') + 1 + line_offset
        col = match.start() - block_text.rfind('\n', 0, match.start())
        val = match.group(1).lower()
        sug = 'textAlign: "start"' if val == 'left' else 'textAlign: "end"'
        violations.append(BidiViolation(
            line, col, 'textAlign', val, sug, rule='bidi.text-align-physical'))

    # Shorthand + value-keyword enforcement, routed through the SAME evaluator the
    # CSS paths use. Without this, an asymmetric four-value shorthand
    # (`margin: "0 8px 0 24px"`) and the value keywords `float`/`clear` passed
    # silently inside JSX style objects while being rejected in plain CSS — the
    # exact C1 bypass, re-opened in a second syntax.
    shorthand_gaps = _scan_js_style_block_shorthands(block_text, line_offset, allow_camel_case)
    violations.extend(shorthand_gaps)

    return violations


_JSX_SHORTHAND_KEBAB = tuple(p for p in SHORTHAND_PROPERTIES if '-' in p)


_JSX_SHORTHAND_CAMEL = {
    'borderWidth': 'border-width',
    'borderStyle': 'border-style',
    'borderColor': 'border-color',
    'scrollMargin': 'scroll-margin',
    'scrollPadding': 'scroll-padding',
    'margin': 'margin',
    'padding': 'padding',
    'inset': 'inset',
}


def _scan_js_style_block_shorthands(block_text, line_offset, allow_camel_case):
    """
    Enforces asymmetric-shorthand and value-keyword rules inside a JSX style object.

    Delegates the actual decision to evaluate_declaration() so the JSX path cannot
    drift from the CSS paths again. `allow_camel_case` deliberately does NOT relax
    these rules: that config key exists so React Native codebases can use camelCase
    property *names*, and every one of these checks is about the property's *value*
    (or about a shorthand both syntaxes spell identically), which mirrors the
    documented promise that the escape hatch "relaxes the JSX property check only".
    """
    violations = []

    # Build a name -> canonical-CSS-name lookup for every shorthand spelling we accept.
    lookups = [(name, name) for name in _JSX_SHORTHAND_KEBAB]
    lookups.extend(_JSX_SHORTHAND_CAMEL.items())

    for js_name, css_name in lookups:
        quoted = re.escape(js_name)
        pattern = re.compile(
            r'(?:(?<=[{,\s])|^)[\'"]?' + quoted + r'[\'"]?\s*:\s*([\'"])([^\'"]*)\1'
        )
        for match in pattern.finditer(block_text):
            raw_value = match.group(2).strip()
            line = block_text[:match.start()].count('\n') + 1 + line_offset
            col = match.start() - block_text.rfind('\n', 0, match.start())
            violations.extend(evaluate_declaration(css_name, raw_value, line, col))

    # Value keywords that are illegal regardless of property spelling.
    for js_name, css_name in (('float', 'float'), ('clear', 'clear')):
        pattern = re.compile(
            r'(?:(?<=[{,\s])|^)[\'"]?' + js_name + r'[\'"]?\s*:\s*([\'"])(left|right)\1',
            re.IGNORECASE,
        )
        for match in pattern.finditer(block_text):
            line = block_text[:match.start()].count('\n') + 1 + line_offset
            col = match.start() - block_text.rfind('\n', 0, match.start())
            violations.extend(evaluate_declaration(css_name, match.group(2).lower(), line, col))

    return violations
