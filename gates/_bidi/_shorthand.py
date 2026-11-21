"""
Shorthand evaluation: splitting a value into terms and deciding what it means.

This is the rule *semantics* — given a declaration, is it directional? — with no
file I/O, no HTML, no JSX. The scanners in `_css` and `_js` all funnel into
`evaluate_declaration`, so a rule changed here changes every syntax at once.
That is deliberate: the C1 defect existed precisely because JSX had its own
evaluation path that drifted from the CSS one.
"""
import re

from ._model import (
    ALLOWED_OFFSETS,
    BANNED_PROPERTIES,
    BidiViolation,
    SHORTHAND_PROPERTIES,
)
from ._runtime import tinycss2

def split_css_values(val):
    values = []
    current = []
    depth = 0
    for char in val:
        if char == '(':
            depth += 1
            current.append(char)
        elif char == ')':
            depth -= 1
            current.append(char)
        elif char in (' ', '\t', '\n') and depth == 0:
            if current:
                token = "".join(current).strip()
                if token and token != '!important':
                    values.append(token)
                current = []
        else:
            current.append(char)
    if current:
        token = "".join(current).strip()
        if token and token != '!important':
            values.append(token)
    return values


def normalize_declared_value(val):
    """
    Lowercases a serialized CSS value and strips a trailing `!important` flag so that
    directional keyword comparisons (`text-align: left !important`) cannot bypass the gate.
    Whitespace is collapsed so `left   !important` is treated identically to `left!important`.
    """
    if not val:
        return ''
    clean = ' '.join(str(val).lower().split())
    clean = re.sub(r'\s*!\s*important\s*$', '', clean).strip()
    return clean


def logical_shorthand_pair(name):
    """
    Maps a physical four-value shorthand to the logical block/inline pair that
    expresses the same asymmetry.

    The block/inline infix is not uniformly a suffix: the border family puts it
    before the sub-property (`border-width` -> `border-block-width`), so a blanket
    `f"{name}-block"` produced `border-width-block`, which is not a CSS property at
    all. An agent following that suggestion would write invalid CSS and stay broken.
    """
    radix, _, suffix = name.partition('-')
    if radix == 'border' and suffix in ('width', 'style', 'color'):
        return f"border-block-{suffix}", f"border-inline-{suffix}"
    return f"{name}-block", f"{name}-inline"


def evaluate_declaration(name, val, line, col):
    """
    Single source of truth for directional-property evaluation, shared by the tinycss2 AST
    path and the zero-dependency tokenizer fallback so both enforce identical rules.
    """
    violations = []
    name = name.lower().strip()
    if not name or name.startswith('--'):
        return violations

    val = normalize_declared_value(val)
    if not val:
        return violations

    if name in BANNED_PROPERTIES:
        violations.append(BidiViolation(
            line, col, name, val, BANNED_PROPERTIES[name],
            rule='bidi.physical-direction-property'))
    elif name in ('left', 'right') and val not in ALLOWED_OFFSETS:
        suggestion = 'inset-inline-start' if name == 'left' else 'inset-inline-end'
        violations.append(BidiViolation(
            line, col, name, val, suggestion, rule='bidi.physical-offset'))
    elif name == 'text-align' and val in ('left', 'right'):
        suggestion = 'text-align: start' if val == 'left' else 'text-align: end'
        violations.append(BidiViolation(
            line, col, name, val, suggestion, rule='bidi.text-align-physical'))
    elif name == 'float' and val in ('left', 'right'):
        suggestion = 'inline-start or Flexbox/Grid' if val == 'left' else 'inline-end or Flexbox/Grid'
        violations.append(BidiViolation(
            line, col, name, val, suggestion, rule='bidi.float-physical'))
    elif name == 'clear' and val in ('left', 'right'):
        suggestion = 'clear: inline-start' if val == 'left' else 'clear: inline-end'
        violations.append(BidiViolation(
            line, col, name, val, suggestion, rule='bidi.clear-physical'))
    elif name in SHORTHAND_PROPERTIES:
        tokens = split_css_values(val)
        if len(tokens) == 4 and tokens[1] != tokens[3]:
            block_prop, inline_prop = logical_shorthand_pair(name)
            suggestion = (
                f"Logical separation: {block_prop}: {tokens[0]} {tokens[2]}; "
                f"{inline_prop}: {tokens[3]} {tokens[1]};"
            )
            violations.append(BidiViolation(
                line, col, name, val, suggestion, rule='bidi.asymmetric-shorthand'))

    return violations


def check_declaration(d, line_offset=0):
    name = d.name.lower()
    if name.startswith('--'):
        return []

    val = tinycss2.serialize(d.value).strip()
    line = (d.source_line or 1) + line_offset
    col = d.source_column or 1
    return evaluate_declaration(name, val, line, col)


def check_declarations(declarations, line_offset=0):
    violations = []
    for d in declarations:
        if d.type == 'declaration':
            violations.extend(check_declaration(d, line_offset))
    return violations
