#!/usr/bin/env python3
"""
Orthotect Gate: WCAG 2.2 Mathematical Contrast Verifier (AA & AAA)
Calculates relative luminance and contrast ratios mathematically based on W3C specs:
L = 0.2126 * R + 0.7152 * G + 0.0722 * B
Ratio = (L1 + 0.05) / (L2 + 0.05)
"""

# Exit-code contract (see core/exit_codes.py):
#   0 = PASS, 1 = rule violation in the audited code, 2 = the gate could not run.
try:
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
except ImportError:
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
import sys
import json
import re
import os

try:
    from core.cli_args import positionals as cli_positionals
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from core.cli_args import positionals as cli_positionals

HEX_REGEX = re.compile(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')

def parse_hex_color(hex_str):
    if not isinstance(hex_str, str):
        raise ValueError(f"Invalid hex color: {hex_str}")
    clean = hex_str.strip()
    m = HEX_REGEX.match(clean)
    if not m:
        raise ValueError(f"Invalid hex color: {hex_str}")
    hex_body = m.group(1)
    if len(hex_body) == 3:
        hex_body = ''.join([c * 2 for c in hex_body])
    return tuple(int(hex_body[i:i+2], 16) for i in (0, 2, 4))

def channel_to_luminance(c):
    s = c / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

def relative_luminance(rgb):
    r, g, b = [channel_to_luminance(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(color1, color2):
    lum1 = relative_luminance(color1)
    lum2 = relative_luminance(color2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)

def resolve_ref(val, primitives, visited=None):
    """
    Resolves DTCG token references (e.g. '{color.neutral.900}') against primitives dictionary.
    Includes circular reference cycle detection and missing reference validation.
    """
    if not isinstance(val, str) or not (val.startswith('{') and val.endswith('}')):
        return val

    if visited is None:
        visited = []

    if val in visited:
        chain = " -> ".join(visited + [val])
        raise ValueError(f"Circular reference detected in design tokens: {chain}")

    visited_next = list(visited) + [val]
    path = val[1:-1].split('.')
    curr = primitives
    for p in path:
        if not isinstance(curr, dict) or p not in curr:
            raise ValueError(f"Unresolved token reference '{val}': missing key '{p}' in token dictionary.")
        curr = curr[p]

    resolved = curr.get('$value', curr) if isinstance(curr, dict) else curr
    if isinstance(resolved, str) and resolved.startswith('{') and resolved.endswith('}'):
        return resolve_ref(resolved, primitives, visited_next)

    return resolved

def find_target_tokens(target_path):
    target_abs = os.path.abspath(target_path)
    root_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Root fallback is strictly allowed ONLY when auditing the root repo itself or the documentation site
    is_root_or_docs = (target_abs == root_pkg or target_abs == os.path.join(root_pkg, 'docs'))

    candidates = [
        target_abs,
        os.path.join(target_abs, 'core', 'tokens'),
        os.path.join(target_abs, 'tokens'),
        os.path.join(target_abs, '.orthotect', 'tokens')
    ]
    if is_root_or_docs:
        candidates.append(os.path.join(root_pkg, 'core', 'tokens'))

    for c in candidates:
        p_file = os.path.join(c, 'primitives.json')
        s_file = os.path.join(c, 'semantics.json')
        if os.path.exists(p_file) and os.path.exists(s_file):
            return p_file, s_file
            
    return None, None

def load_contrast_matrix(target_path=None):
    root_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    package_matrix = os.path.abspath(os.path.join(root_pkg, 'core', 'tokens', 'contrast-matrix.json'))

    candidates = []
    if target_path:
        target_abs = os.path.abspath(target_path)
        candidates.extend([
            target_abs,
            os.path.join(target_abs, 'core', 'tokens'),
            os.path.join(target_abs, 'tokens'),
            os.path.join(target_abs, '.orthotect', 'tokens')
        ])

    for c in candidates:
        m_file = os.path.join(c, 'contrast-matrix.json') if not c.endswith('.json') else c
        m_abs = os.path.abspath(m_file)
        if os.path.exists(m_abs) and m_abs != package_matrix:
            try:
                with open(m_abs, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as err:
                raise ValueError(f"Corrupted or invalid contrast matrix at '{m_abs}': {err}")

    # Fall back to canonical package matrix
    if os.path.exists(package_matrix):
        try:
            with open(package_matrix, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as err:
            raise ValueError(f"Corrupted canonical contrast matrix at '{package_matrix}': {err}")

    return None

class ContrastPair(tuple):
    """
    A `(label, fg_rgb, bg_rgb, aa_req, aaa_req, usage)` 6-tuple with metadata.

    Tuple-compatible so every existing consumer keeps unpacking it, plus the two
    facts a machine-readable report needs: which registry rule the pair belongs
    to, and which semantic token to point the annotation at. A contrast finding
    has no source line — it is a property of a token pair, not of a line of code
    — so the location has to name the token instead.
    """

    def __new__(cls, label, fg_rgb, bg_rgb, aa_req, aaa_req, usage,
                rule=None, fg_token='', bg_token=''):
        instance = super().__new__(cls, (label, fg_rgb, bg_rgb, aa_req, aaa_req, usage))
        instance.label = label
        instance.usage = usage
        instance.rule = rule
        instance.fg_token = fg_token
        instance.bg_token = bg_token
        return instance


def _contrast_rule_for(aa_req, level):
    """Selects the registry rule a failing pair belongs to."""
    if aa_req < 4.5:
        return 'contrast.wcag-non-text'
    return 'contrast.wcag-aaa-normal-text' if level == 'AAA' else 'contrast.wcag-aa-normal-text'


def evaluate_semantic_pairs(theme_name, theme_data, prims, matrix_data=None):
    """
    Builds and evaluates the canonical semantic contrast matrix covering:
    - Primary, secondary, tertiary text across canvas, panel, subtle, and elevated surfaces
    - Action controls (primary and danger) and their hover states
    - Non-text UI components (borders, boundaries, and focus indicators) under WCAG 2.2 SC 1.4.11
    Loads from canonical contrast-matrix.json when available.
    """
    surfaces = theme_data.get('surface')
    contents = theme_data.get('content')
    borders = theme_data.get('border')
    actions = theme_data.get('action')

    if not isinstance(surfaces, dict) or not isinstance(contents, dict) or not isinstance(borders, dict) or not isinstance(actions, dict):
        raise ValueError(f"Theme '{theme_name}' is missing required token groups (surface, content, border, action)")

    def get_rgb(group, key):
        grp_data = theme_data.get(group, {})
        tok = grp_data.get(key)
        if not tok or not isinstance(tok, dict) or '$value' not in tok:
            raise ValueError(f"Missing required semantic token in theme [{theme_name}]: '{group}.{key}'")
        raw_val = tok['$value']
        resolved = resolve_ref(raw_val, prims)
        try:
            return parse_hex_color(resolved), resolved
        except Exception as e:
            raise ValueError(f"Invalid color value for [{theme_name}] '{group}.{key}' ({raw_val} -> {resolved}): {e}")

    if matrix_data is None:
        matrix_data = load_contrast_matrix()

    if matrix_data and 'pairs' in matrix_data:
        tiers = matrix_data.get('tiers', {})
        pairs = []
        for pair in matrix_data['pairs']:
            label = pair.get('name', 'Unnamed Pair')
            bg_grp, bg_tok = pair['background']
            fg_grp, fg_tok = pair['foreground']
            tier = pair.get('tier', 'normal_text')
            role = pair.get('role', '')

            tier_info = tiers.get(tier, {})
            aa_req = tier_info.get('minRatioAA', 4.5)
            aaa_req = tier_info.get('minRatioAAA', 7.0)

            bg_rgb, bg_hex = get_rgb(bg_grp, bg_tok)
            fg_rgb, fg_hex = get_rgb(fg_grp, fg_tok)

            pairs.append(ContrastPair(
                label, fg_rgb, bg_rgb, aa_req, aaa_req, role,
                rule=_contrast_rule_for(aa_req, 'AA'),
                fg_token=f"{fg_grp}.{fg_tok}", bg_token=f"{bg_grp}.{bg_tok}",
            ))

        return pairs

    # Fallback to hardcoded canonical matrix if contrast-matrix.json is missing
    canvas_rgb, canvas_hex = get_rgb('surface', 'canvas')
    panel_rgb, panel_hex = get_rgb('surface', 'panel')
    subtle_rgb, subtle_hex = get_rgb('surface', 'subtle')
    elevated_rgb, elevated_hex = get_rgb('surface', 'elevated')

    cp_rgb, cp_hex = get_rgb('content', 'primary')
    cs_rgb, cs_hex = get_rgb('content', 'secondary')
    ct_rgb, ct_hex = get_rgb('content', 'tertiary')
    ci_rgb, ci_hex = get_rgb('content', 'inverse')

    ap_rgb, ap_hex = get_rgb('action', 'primary')
    aph_rgb, aph_hex = get_rgb('action', 'primaryHover')
    ad_rgb, ad_hex = get_rgb('action', 'danger')
    adh_rgb, adh_hex = get_rgb('action', 'dangerHover')

    bs_rgb, bs_hex = get_rgb('border', 'strong')
    bf_rgb, bf_hex = get_rgb('border', 'focus')

    # (label, fg, bg, aa, aaa, usage, fg token, bg token)
    table = [
        # Normal Body Text (WCAG 2.2 SC 1.4.3: 4.5:1 AA, 7.0:1 AAA)
        ("Content Primary on Canvas", cp_rgb, canvas_rgb, 4.5, 7.0, "Body Text", "content.primary", "surface.canvas"),
        ("Content Primary on Panel", cp_rgb, panel_rgb, 4.5, 7.0, "Panel Body Text", "content.primary", "surface.panel"),
        ("Content Primary on Subtle Surface", cp_rgb, subtle_rgb, 4.5, 7.0, "Subtle Surface Body Text", "content.primary", "surface.subtle"),
        ("Content Primary on Elevated Surface", cp_rgb, elevated_rgb, 4.5, 7.0, "Elevated Surface Body Text", "content.primary", "surface.elevated"),
        ("Content Secondary on Canvas", cs_rgb, canvas_rgb, 4.5, 7.0, "Secondary Text", "content.secondary", "surface.canvas"),
        ("Content Secondary on Panel", cs_rgb, panel_rgb, 4.5, 7.0, "Panel Secondary Text", "content.secondary", "surface.panel"),
        ("Content Secondary on Subtle Surface", cs_rgb, subtle_rgb, 4.5, 7.0, "Subtle Surface Secondary Text", "content.secondary", "surface.subtle"),
        ("Content Secondary on Elevated Surface", cs_rgb, elevated_rgb, 4.5, 7.0, "Elevated Surface Secondary Text", "content.secondary", "surface.elevated"),
        ("Content Tertiary on Canvas", ct_rgb, canvas_rgb, 4.5, 7.0, "Auxiliary Supporting Text (AA 4.5:1)", "content.tertiary", "surface.canvas"),
        ("Content Tertiary on Panel", ct_rgb, panel_rgb, 4.5, 7.0, "Auxiliary Panel Text (AA 4.5:1)", "content.tertiary", "surface.panel"),

        # Action Button Text & Hover States (4.5:1 AA, 7.0:1 AAA)
        ("Inverse Text on Action Primary", ci_rgb, ap_rgb, 4.5, 7.0, "Primary Button Label", "content.inverse", "action.primary"),
        ("Inverse Text on Action Primary Hover", ci_rgb, aph_rgb, 4.5, 7.0, "Primary Button Hover Label", "content.inverse", "action.primaryHover"),
        ("Inverse Text on Action Danger", ci_rgb, ad_rgb, 4.5, 7.0, "Destructive Button Label", "content.inverse", "action.danger"),
        ("Inverse Text on Action Danger Hover", ci_rgb, adh_rgb, 4.5, 7.0, "Destructive Button Hover Label", "content.inverse", "action.dangerHover"),

        # Non-Text UI Components (WCAG 2.2 SC 1.4.11: 3.0:1 AA, 4.5:1 AAA)
        ("Action Primary Control Boundary on Canvas", ap_rgb, canvas_rgb, 3.0, 4.5, "Primary Control Boundary", "action.primary", "surface.canvas"),
        ("Action Danger Control Boundary on Canvas", ad_rgb, canvas_rgb, 3.0, 4.5, "Destructive Control Boundary", "action.danger", "surface.canvas"),
        ("Border Strong on Surface Panel", bs_rgb, panel_rgb, 3.0, 4.5, "Panel Boundary Line", "border.strong", "surface.panel"),
        ("Border Strong on Surface Canvas", bs_rgb, canvas_rgb, 3.0, 4.5, "Canvas Boundary Line", "border.strong", "surface.canvas"),
        ("Focus Indicator on Surface Canvas", bf_rgb, canvas_rgb, 3.0, 4.5, "Focus Ring on Canvas", "border.focus", "surface.canvas"),
        ("Focus Indicator on Surface Panel", bf_rgb, panel_rgb, 3.0, 4.5, "Focus Ring on Panel", "border.focus", "surface.panel"),
    ]
    return [
        ContrastPair(label, fg, bg, aa, aaa, usage,
                     rule=_contrast_rule_for(aa, 'AA'),
                     fg_token=fg_tok, bg_token=bg_tok)
        for label, fg, bg, aa, aaa, usage, fg_tok, bg_tok in table
    ]

get_semantic_contrast_pairs = evaluate_semantic_pairs

def _load_sarif_module():
    """Loads `core/sarif.py`, anchored to the package so cwd cannot change it."""
    try:
        from core import sarif
        return sarif
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from core import sarif
        return sarif


def _token_line(sem_file, token_path):
    """
    1-based line of a semantic token's key in `semantics.json`, or 1.

    A contrast finding is a property of a token pair rather than of a line of
    code, so the only honest location is the token's own declaration. The key
    leaf is searched for because the JSON is nested (`theme.<name>.<group>.<key>`)
    and the leaf is what a reader recognises.
    """
    leaf = token_path.rsplit('.', 1)[-1]
    try:
        with open(sem_file, 'r', encoding='utf-8') as handle:
            for index, raw in enumerate(handle, start=1):
                if f'"{leaf}"' in raw:
                    return index
    except Exception:
        pass
    return 1


def main():
    # Flags may legally precede the target (`gate_contrast_wcag.py --json ./src`).
    # Resolving sys.argv[1] blindly made "--json" the audited path, so the gate
    # reported "missing design tokens in target: --json" instead of scanning ./src.
    args = sys.argv[1:]
    positional = cli_positionals(args)
    target_path = positional[0] if positional else '.'
    prim_file, sem_file = find_target_tokens(target_path)

    sarif = _load_sarif_module()
    as_sarif = sarif.sarif_requested(args)

    def fail_tool_error(message, extra=None):
        if as_sarif:
            sarif.print_gate_sarif('gate_contrast_wcag', [], os.path.abspath(target_path),
                                   tool_error=message)
        else:
            print(f"❌ [REJECT] {message}")
            for line in (extra or []):
                print(f"   {line}")
        sys.exit(EXIT_TOOL_ERROR)

    if not as_sarif:
        print("═══════════════════════════════════════════════════════════════")
        print("  ORTHOTECT GATE: WCAG 2.2 Mathematical Contrast Verifier")
        print("═══════════════════════════════════════════════════════════════")

    if not prim_file or not sem_file:
        fail_tool_error(
            f"Missing required Design Token files in target: {target_path}",
            ["Orthotect requires both 'primitives.json' and 'semantics.json' in core/tokens/.",
             "(Run 'npx orthotect init <path>' to scaffold standard tokens)."])

    try:
        with open(prim_file, 'r', encoding='utf-8') as f:
            prims = json.load(f)
        with open(sem_file, 'r', encoding='utf-8') as f:
            sems = json.load(f)
    except Exception as e:
        fail_tool_error(f"Failed to parse design token JSON: {e}")

    failures = 0
    tested_pairs = 0
    passed_aaa = 0
    passed_aa = 0
    all_findings = []

    # Honor orthotect.config.json `contrast.level` ("AA" default, "AAA" opt-in).
    # Previously this documented setting was silently ignored and the gate always
    # enforced AA, so projects declaring "level": "AAA" received a false PASS.
    enforced_level = 'AA'
    try:
        _pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if _pkg_root not in sys.path:
            sys.path.insert(0, _pkg_root)
        from core.config import load_orthotect_config, get_contrast_config
        cfg, _ = load_orthotect_config(target_path)
        enforced_level = str(get_contrast_config(cfg).get('level', 'AA')).upper()
    except Exception:
        enforced_level = 'AA'
    if enforced_level not in ('AA', 'AAA'):
        if not as_sarif:
            print(f"⚠️  [WARN] Unknown contrast.level '{enforced_level}' in orthotect.config.json; falling back to 'AA'.")
        enforced_level = 'AA'
    if enforced_level == 'AAA' and not as_sarif:
        print("\n  Enforced Level: AAA (from orthotect.config.json → contrast.level)")

    themes = sems.get('theme', {})
    if not themes or not isinstance(themes, dict):
        fail_tool_error("Missing 'theme' declarations in semantics.json")

    matrix_data = load_contrast_matrix(target_path)
    for theme_name, theme_data in themes.items():
        if not as_sarif:
            print(f"\nTheme Scope: [{theme_name.upper()}]")
        try:
            pairs = evaluate_semantic_pairs(theme_name, theme_data, prims, matrix_data)
        except Exception as e:
            if not as_sarif:
                print(f"❌ [REJECT] Token evaluation error in theme [{theme_name}]: {e}")
            failures += 1
            continue

        for pair in pairs:
            label, fg_rgb, bg_rgb, aa_req, aaa_req, usage = pair
            ratio = contrast_ratio(fg_rgb, bg_rgb)
            tested_pairs += 1

            meets_aa = ratio >= aa_req
            meets_aaa = ratio >= aaa_req
            required_req = aaa_req if enforced_level == 'AAA' else aa_req
            meets_required = ratio >= required_req

            if meets_aaa:
                tier = "PASS (AAA)"
                passed_aaa += 1
                passed_aa += 1
            elif meets_aa:
                tier = "PASS (AA)"
                passed_aa += 1
            else:
                tier = f"FAIL (Needs {aa_req}:1)"

            if not meets_required:
                failures += 1
                token = getattr(pair, 'fg_token', '') or ''
                all_findings.append({
                    'file': sem_file,
                    'line': _token_line(sem_file, token),
                    'label': f"[{theme_name}] {label}",
                    'snippet': f"{ratio:.2f}:1, requires {required_req}:1",
                    'suggestion': (f"Raise the contrast of '{token}' against "
                                   f"'{getattr(pair, 'bg_token', '')}'"),
                    'ruleId': getattr(pair, 'rule', None),
                })

            if not as_sarif:
                symbol = "✅" if meets_required else "❌"
                print(f"  {symbol} {label:<44}: {ratio:5.2f}:1 [{tier:<10}] ({usage})")

    if as_sarif:
        sarif.print_gate_sarif('gate_contrast_wcag', all_findings, os.path.abspath(target_path))
        sys.exit(EXIT_PASS if (failures == 0 and tested_pairs > 0) else EXIT_VIOLATION)

    print(f"\nSummary: {tested_pairs} semantic token pairs evaluated across {len(themes)} theme(s).")
    print("Scope: Static Design Token Semantic Matrix. (Rendered DOM element contrast must be separately evaluated via browser tests).")
    if failures == 0 and tested_pairs > 0:
        print(f"✅ [PASS] 100% of tested token pairs meet mandatory WCAG 2.2 AA standards ({passed_aa}/{tested_pairs}).")
        print(f"   Enhanced Tier: {passed_aaa}/{tested_pairs} pairs achieved full WCAG 2.2 AAA.")
        if enforced_level == 'AAA':
            print("   Enforced Level: AAA (orthotect.config.json → contrast.level).")
        sys.exit(EXIT_PASS)
    else:
        if enforced_level == 'AAA':
            print(f"❌ [REJECT] {failures} contrast check(s) failed enforced WCAG 2.2 AAA criteria (contrast.level=AAA).")
        else:
            print(f"❌ [REJECT] {failures} contrast check(s) failed mandatory WCAG 2.2 AA criteria.")
        sys.exit(EXIT_VIOLATION)


if __name__ == '__main__':
    main()

