"""
`--fix`: rewriting physical properties to logical ones.

The fixers are the inverse of the scanners and must stay in lock-step with them:
a rewrite the scanner would not recognise as fixed is a partial fix that reports
success. `apply_bidi_fixes_to_file` therefore re-scans after writing and raises
`PartialFixError` if anything survived.
"""
import os
import re

from ._model import (
    ALLOWED_OFFSETS,
    BANNED_CAMELCASE_PROPERTIES,
    BANNED_PROPERTIES,
    SHORTHAND_PROPERTIES,
)
from ._dispatch import scan_file
from ._paths import SUPPORTED_EXTENSIONS
from ._shorthand import logical_shorthand_pair, split_css_values
from ._js import _JSX_SHORTHAND_CAMEL

def mask_css_comments_and_strings(css_text):
    """
    Masks comments /* ... */ and string literals '...' / "..." in CSS text.
    Returns (masked_text, placeholders_dict).
    """
    placeholders = {}
    counter = 0

    def comment_repl(m):
        nonlocal counter
        key = f"__OT_CSS_COMMENT_{counter}__"
        counter += 1
        placeholders[key] = m.group(0)
        return key

    masked = re.sub(r'/\*[\s\S]*?\*/', comment_repl, css_text)

    def string_repl(m):
        nonlocal counter
        key = f"__OT_CSS_STR_{counter}__"
        counter += 1
        placeholders[key] = m.group(0)
        return key

    masked = re.sub(r'"(?:\\.|[^"\\])*"', string_repl, masked)
    masked = re.sub(r"'(?:\\.|[^'\\])*'", string_repl, masked)

    return masked, placeholders


def unmask_css(masked_text, placeholders):
    """Restores masked comments and strings back into the CSS text."""
    for key, original in reversed(list(placeholders.items())):
        masked_text = masked_text.replace(key, original)
    return masked_text


def transform_css_declarations(text):
    """
    Transforms physical CSS property declarations and values into logical equivalents.
    """
    # 1. Banned kebab-case properties
    for prop, repl in BANNED_PROPERTIES.items():
        pattern = re.compile(r'(?<![a-zA-Z0-9_-])' + re.escape(prop) + r'(\s*:)', re.IGNORECASE)
        text = pattern.sub(repl + r'\1', text)

    # 2. Offsets left: and right:
    def repl_offset(m):
        prop = m.group(1).lower()
        val_raw = m.group(3).strip()
        val_clean = re.sub(r'\s*!\s*important', '', val_raw, flags=re.IGNORECASE).strip().lower().strip('\'"')
        if val_clean in ALLOWED_OFFSETS:
            return m.group(0)
        sug = 'inset-inline-start' if prop == 'left' else 'inset-inline-end'
        return sug + m.group(2) + m.group(3)

    offset_pattern = re.compile(r'(?<![a-zA-Z0-9_-])(left|right)(\s*:\s*)([^;}\n]+)', re.IGNORECASE)
    text = offset_pattern.sub(repl_offset, text)

    # 3. text-align: left / right
    def repl_text_align(m):
        prop = m.group(1)
        sep = m.group(2)
        val = m.group(3)
        rest = m.group(4)
        sug_val = 'start' if val.lower() == 'left' else 'end'
        return prop + sep + sug_val + rest

    ta_pattern = re.compile(r'(?<![a-zA-Z0-9_-])(text-align)(\s*:\s*)(left|right)(\b[^;}\n]*)', re.IGNORECASE)
    text = ta_pattern.sub(repl_text_align, text)

    # 4. float: left / right
    def repl_float(m):
        prop = m.group(1)
        sep = m.group(2)
        val = m.group(3)
        rest = m.group(4)
        sug_val = 'inline-start' if val.lower() == 'left' else 'inline-end'
        return prop + sep + sug_val + rest

    float_pattern = re.compile(r'(?<![a-zA-Z0-9_-])(float)(\s*:\s*)(left|right)(\b[^;}\n]*)', re.IGNORECASE)
    text = float_pattern.sub(repl_float, text)

    # 5. clear: left / right
    def repl_clear(m):
        prop = m.group(1)
        sep = m.group(2)
        val = m.group(3)
        rest = m.group(4)
        sug_val = 'inline-start' if val.lower() == 'left' else 'inline-end'
        return prop + sep + sug_val + rest

    clear_pattern = re.compile(r'(?<![a-zA-Z0-9_-])(clear)(\s*:\s*)(left|right)(\b[^;}\n]*)', re.IGNORECASE)
    text = clear_pattern.sub(repl_clear, text)

    # 6. Asymmetric four-value shorthands.
    #
    # The evaluator has flagged these since C1, but the repair path never handled
    # them: a CSS shorthand was reported, `--fix` left the file untouched, and the
    # run ended in [PARTIAL FIX]. Only the JSX path expanded them. Detection and
    # repair must cover the same rule set, so the expansion below mirrors
    # evaluate_declaration() exactly — same predicate (token[1] != token[3]),
    # same value mapping, same property pair from logical_shorthand_pair().
    def expand_shorthand(match):
        name = match.group(1).lower()
        separator = match.group(2)
        raw_value = match.group(3)
        rest = match.group(4)

        # `!important` applies to the whole shorthand; it must survive the split
        # or the repaired declarations silently change cascade priority.
        has_important = re.search(r'!\s*important\s*$', raw_value, re.IGNORECASE) is not None
        stripped = re.sub(r'\s*!\s*important\s*$', '', raw_value, flags=re.IGNORECASE)
        important = ' !important' if has_important else ''
        tokens = split_css_values(stripped)
        if len(tokens) != 4 or tokens[1] == tokens[3]:
            return match.group(0)

        # `tokens` is [block-start, inline-end, block-end, inline-start]. The logical
        # pair is <block-start> <block-end> and <inline-start> <inline-end>, which is
        # the CSS 2-value order (start, end) for both axes.
        block_prop, inline_prop = logical_shorthand_pair(name)
        block_value = f"{tokens[0]} {tokens[2]}"
        inline_value = f"{tokens[3]} {tokens[1]}"
        return (f"{block_prop}{separator}{block_value}{important}; "
                f"{inline_prop}{separator}{inline_value}{important}{rest}")

    # The terminator is `;`, `}`, or end-of-input: the last declaration in an HTML
    # `style="..."` attribute has no trailing semicolon, and requiring one left every
    # inline-style shorthand detected but unrepairable.
    shorthand_names = '|'.join(re.escape(p) for p in SHORTHAND_PROPERTIES)
    shorthand_pattern = re.compile(
        r'(?<![a-zA-Z0-9_-])(' + shorthand_names + r')(\s*:\s*)([^;}]*?)(\s*;|\s*}|$)',
        re.IGNORECASE,
    )
    text = shorthand_pattern.sub(expand_shorthand, text)

    return text


def fix_css_content(content):
    """Fixes physical properties in CSS while preserving comments and string literals."""
    masked, placeholders = mask_css_comments_and_strings(content)
    transformed = transform_css_declarations(masked)
    return unmask_css(transformed, placeholders)


def _jsx_logical_pair(name):
    """
    camelCase counterpart of logical_shorthand_pair().

    React style objects use `marginBlock` / `marginInline`, but the border family
    keeps its sub-property last: `borderWidth` -> `borderBlockWidth` /
    `borderInlineWidth`.
    """
    canonical = _JSX_SHORTHAND_CAMEL.get(name)
    if canonical:
        kebab_block, kebab_inline = logical_shorthand_pair(canonical)
        return (
            re.sub(r'-([a-z])', lambda m: m.group(1).upper(), kebab_block),
            re.sub(r'-([a-z])', lambda m: m.group(1).upper(), kebab_inline),
        )
    # Quoted kebab-case spelling ('border-width' / 'margin') inside a style object.
    kebab_block, kebab_inline = logical_shorthand_pair(name)
    camel = lambda s: re.sub(r'-([a-z])', lambda m: m.group(1).upper(), s)
    if '-' in name:
        return camel(kebab_block), camel(kebab_inline)
    return name + 'Block', name + 'Inline'


def _fix_jsx_shorthand_and_keywords(inner):
    """
    Repairs asymmetric shorthands and directional value keywords inside a JSX style
    object, mirroring what _scan_js_style_block_shorthands detects.

    Detection and repair must cover the same rule set: a violation the gate can
    report but never repair leaves `--fix` unable to reach a green build, and one
    it repairs but never reports is dead code. Both now derive from the same
    SHORTHAND_PROPERTIES / evaluate_declaration contract.

    An asymmetric four-value shorthand expands into the logical pair the gate
    suggests, e.g. margin: "0 8px 0 24px" -> marginBlock: "0 0", marginInline: "24px 8px".
    """
    # 1. Asymmetric four-value shorthands.
    #    Two spellings are possible and they keep their own output form:
    #      camelCase   margin: / borderWidth:        -> marginBlock: / borderBlockWidth:
    #      quoted kebab 'margin': / 'border-width':  -> 'margin-block': / 'border-block-width':
    #    The scanned name set matches _scan_js_style_block_shorthands exactly, so a
    #    violation can never be reported but left unrepaired.
    camel_names = list(_JSX_SHORTHAND_CAMEL.keys())
    kebab_names = list(SHORTHAND_PROPERTIES)

    def expand_shorthand(match, output_kebab):
        value = match.group(match.lastindex)
        tokens = split_css_values(value)
        if len(tokens) != 4 or tokens[1] == tokens[3]:
            return match.group(0)
        q = match.group(match.lastindex - 1)
        name = match.group(0).split(':', 1)[0].strip().strip('\'"')
        canonical = _JSX_SHORTHAND_CAMEL.get(name, name)
        block_prop, inline_prop = logical_shorthand_pair(canonical)
        if not output_kebab:
            camel = lambda s: re.sub(r'-([a-z])', lambda m: m.group(1).upper(), s)
            block_prop, inline_prop = camel(block_prop), camel(inline_prop)
            return (f"{block_prop}: {q}{tokens[0]} {tokens[2]}{q}, "
                    f"{inline_prop}: {q}{tokens[3]} {tokens[1]}{q}")
        nq = match.group(1)
        return (f"{nq}{block_prop}{nq}: {q}{tokens[0]} {tokens[2]}{q}, "
                f"{nq}{inline_prop}{nq}: {q}{tokens[3]} {tokens[1]}{q}")

    for js_name in camel_names:
        pattern = re.compile(
            r'(?:(?<=[{,\s])|^)' + re.escape(js_name) + r'\s*:\s*([\'"])([^\'"]*)\1'
        )
        inner = pattern.sub(lambda m: expand_shorthand(m, False), inner)

    for js_name in kebab_names:
        # Quote-aware variant: a bare `margin` (no quotes) is not a valid React
        # style key, so only the quoted spelling is repaired here.
        pattern = re.compile(
            r'([\'"])' + re.escape(js_name) + r'\1\s*:\s*([\'"])([^\'"]*)\2'
        )
        inner = pattern.sub(lambda m: expand_shorthand(m, True), inner)

    # 2. Directional value keywords: float / clear.
    for js_name in ('float', 'clear'):
        kw_pattern = re.compile(
            r'(?:(?<=[{,\s])|^)([\'"]?)(' + js_name + r'[\'"]?\s*:\s*)([\'"])(left|right)\3'
        )

        def repl_kw(m):
            val = m.group(4).lower()
            sug = 'inline-start' if val == 'left' else 'inline-end'
            return m.group(1) + m.group(2) + m.group(3) + sug + m.group(3)

        inner = kw_pattern.sub(repl_kw, inner)

    return inner


def fix_js_content(content):
    """Fixes physical properties in JSX, TSX, and JS style declarations."""
    # 1. Fix JSX style={{ ... }} blocks
    def fix_jsx_style_match(m):
        inner = m.group(1)
        for prop, repl in BANNED_CAMELCASE_PROPERTIES.items():
            inner = re.sub(r'(?<![a-zA-Z0-9_])' + re.escape(prop) + r'(\s*:)', repl + r'\1', inner)
        for prop, repl in BANNED_PROPERTIES.items():
            inner = re.sub(r'([\'"])' + re.escape(prop) + r'([\'"]\s*:)', r'\1' + repl + r'\2', inner)
        def repl_js_offset(om):
            val_clean = om.group(3).strip().strip('\'"').lower()
            if val_clean in ALLOWED_OFFSETS:
                return om.group(0)
            sug = 'insetInlineStart' if om.group(1) == 'left' else 'insetInlineEnd'
            return sug + om.group(2) + om.group(3)
        inner = re.sub(r'(?<![a-zA-Z0-9_])(left|right)(\s*:\s*)([^,;}\n]+)', repl_js_offset, inner)
        def repl_js_ta(tam):
            sug = 'start' if tam.group(3).lower() == 'left' else 'end'
            return tam.group(1) + tam.group(2) + sug + tam.group(4)
        inner = re.sub(r'\b(textAlign\s*:\s*)([\'"])(left|right)([\'"])', repl_js_ta, inner, flags=re.IGNORECASE)
        inner = _fix_jsx_shorthand_and_keywords(inner)
        return 'style={{' + inner + '}}'

    content = re.sub(r'\bstyle\s*=\s*\{\{\s*([\s\S]*?)\s*\}\}', fix_jsx_style_match, content)

    # 2. Fix StyleSheet.create({ ... }) blocks
    def fix_ss_match(m):
        inner = m.group(1)
        for prop, repl in BANNED_CAMELCASE_PROPERTIES.items():
            inner = re.sub(r'(?<![a-zA-Z0-9_])' + re.escape(prop) + r'(\s*:)', repl + r'\1', inner)
        for prop, repl in BANNED_PROPERTIES.items():
            inner = re.sub(r'([\'"])' + re.escape(prop) + r'([\'"]\s*:)', r'\1' + repl + r'\2', inner)
        def repl_js_offset(om):
            val_clean = om.group(3).strip().strip('\'"').lower()
            if val_clean in ALLOWED_OFFSETS:
                return om.group(0)
            sug = 'insetInlineStart' if om.group(1) == 'left' else 'insetInlineEnd'
            return sug + om.group(2) + om.group(3)
        inner = re.sub(r'(?<![a-zA-Z0-9_])(left|right)(\s*:\s*)([^,;}\n]+)', repl_js_offset, inner)
        def repl_js_ta(tam):
            sug = 'start' if tam.group(3).lower() == 'left' else 'end'
            return tam.group(1) + tam.group(2) + sug + tam.group(4)
        inner = re.sub(r'\b(textAlign\s*:\s*)([\'"])(left|right)([\'"])', repl_js_ta, inner, flags=re.IGNORECASE)
        # StyleSheet.create() objects carry the same rule families as style={{...}}.
        # Omitting this made an asymmetric shorthand detected-but-unrepairable here
        # while the identical declaration was repaired one branch above.
        inner = _fix_jsx_shorthand_and_keywords(inner)
        return 'StyleSheet.create({' + inner + '})'

    content = re.sub(r'StyleSheet\s*\.\s*create\s*\(\s*\{([\s\S]*?)\}\s*\)', fix_ss_match, content)

    # 3. Fix tagged template literals (styled.div`...` or css`...`)
    def fix_template_literals(m):
        tag = m.group(1)
        css_body = m.group(2)
        fixed_body = fix_css_content(css_body)
        return tag + '`' + fixed_body + '`'

    content = re.sub(r'(\b(?:styled(?:\.[a-zA-Z0-9_]+|\([^\)]+\))|css|keyframes|injectGlobal|createGlobalStyle)\s*)`([\s\S]*?)`', fix_template_literals, content)

    return content


def fix_html_content(content):
    """Fixes physical properties in HTML <style> tags and inline style attributes."""
    # 1. <style> blocks
    def fix_style_tag(m):
        open_tag = m.group(1)
        body = m.group(2)
        close_tag = m.group(3)
        return open_tag + fix_css_content(body) + close_tag

    content = re.sub(r'(<style[^>]*>)([\s\S]*?)(</style>)', fix_style_tag, content, flags=re.IGNORECASE)

    # 2. Inline style="..." attributes
    def fix_style_attr(m):
        prefix = m.group(1)
        q = m.group(2)
        body = m.group(3)
        fixed_body = transform_css_declarations(body)
        return prefix + q + fixed_body + q

    content = re.sub(r'(\bstyle\s*=\s*)([\'"])([\s\S]*?)\2', fix_style_attr, content, flags=re.IGNORECASE)
    return content


class PartialFixError(Exception):
    """
    Raised when `--fix` rewrote a file but could not eliminate every violation.

    A partial fix must never be reported as success. Before this existed the
    gate subtracted the remaining count from the initial count and printed the
    difference as "repaired", then classified the file purely on the re-scan —
    so a single unrepaired rule alongside repaired ones produced a run that
    looked like a clean repair attempt but still exited 1 with no explanation of
    why the count never reached zero.
    """

    def __init__(self, filepath, remaining):
        self.filepath = filepath
        self.remaining = remaining
        super().__init__(
            f"{filepath}: {len(remaining)} violation(s) remain after auto-fix"
        )


def apply_bidi_fixes_to_file(filepath, allow_camel_case=False):
    """
    Reads filepath, applies deterministic logical property transformations, writes
    back, and **verifies that the file now scans clean**.

    Returns (num_fixed, details_list, remaining_violations).

    `remaining_violations` is the post-write re-scan. The caller treats a non-empty
    result as a failed repair: P1-1 requires that a partial fix fail rather than
    quietly pass. Scan configuration is threaded through so the post-fix
    verification uses exactly the rules the pre-fix scan used.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return 0, [], []

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        original = f.read()

    initial_viols = scan_file(filepath, allow_camel_case=allow_camel_case)
    if not initial_viols:
        return 0, [], []

    if ext in ('.html', '.htm', '.vue', '.svelte'):
        fixed = fix_html_content(original)
    elif ext in ('.jsx', '.tsx', '.js', '.ts'):
        fixed = fix_js_content(original)
    else:
        fixed = fix_css_content(original)

    if fixed != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed)

    remaining_viols = scan_file(filepath, allow_camel_case=allow_camel_case)
    remaining_keys = {(v.line, v.name, v.val) for v in remaining_viols}
    repaired = [v for v in initial_viols if (v.line, v.name, v.val) not in remaining_keys]
    details = [f"Repaired {v.name} -> {v.suggestion}" for v in repaired]
    return len(repaired), details, remaining_viols
