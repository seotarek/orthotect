#!/usr/bin/env python3
"""
Orthotect Gate: WCAG 2.2 Mathematical Contrast Verifier (AA & AAA)
Calculates relative luminance and contrast ratios mathematically based on W3C specs:
L = 0.2126 * R + 0.7152 * G + 0.0722 * B
Ratio = (L1 + 0.05) / (L2 + 0.05)
"""
import sys
import json
import re
import os

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

def evaluate_semantic_pairs(theme_name, theme_data, prims):
    """
    Builds and evaluates the canonical semantic contrast matrix covering:
    - Primary, secondary, tertiary text across canvas, panel, subtle, and elevated surfaces
    - Action controls (primary and danger) and their hover states
    - Non-text UI components (borders, boundaries, and focus indicators) under WCAG 2.2 SC 1.4.11
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

    pairs = [
        # Normal Body Text (WCAG 2.2 SC 1.4.3: 4.5:1 AA, 7.0:1 AAA)
        ("Content Primary on Canvas", cp_rgb, canvas_rgb, 4.5, 7.0, "Body Text"),
        ("Content Primary on Panel", cp_rgb, panel_rgb, 4.5, 7.0, "Panel Body Text"),
        ("Content Primary on Subtle Surface", cp_rgb, subtle_rgb, 4.5, 7.0, "Subtle Surface Body Text"),
        ("Content Primary on Elevated Surface", cp_rgb, elevated_rgb, 4.5, 7.0, "Elevated Surface Body Text"),
        ("Content Secondary on Canvas", cs_rgb, canvas_rgb, 4.5, 7.0, "Secondary Text"),
        ("Content Secondary on Panel", cs_rgb, panel_rgb, 4.5, 7.0, "Panel Secondary Text"),
        ("Content Secondary on Subtle Surface", cs_rgb, subtle_rgb, 4.5, 7.0, "Subtle Surface Secondary Text"),
        ("Content Secondary on Elevated Surface", cs_rgb, elevated_rgb, 4.5, 7.0, "Elevated Surface Secondary Text"),
        ("Content Tertiary on Canvas", ct_rgb, canvas_rgb, 3.0, 4.5, "Large/Auxiliary Supporting Text"),
        ("Content Tertiary on Panel", ct_rgb, panel_rgb, 3.0, 4.5, "Large/Auxiliary Panel Text"),


        # Action Button Text & Hover States (4.5:1 AA, 7.0:1 AAA)
        ("Inverse Text on Action Primary", ci_rgb, ap_rgb, 4.5, 7.0, "Primary Button Label"),
        ("Inverse Text on Action Primary Hover", ci_rgb, aph_rgb, 4.5, 7.0, "Primary Button Hover Label"),
        ("Inverse Text on Action Danger", ci_rgb, ad_rgb, 4.5, 7.0, "Destructive Button Label"),
        ("Inverse Text on Action Danger Hover", ci_rgb, adh_rgb, 4.5, 7.0, "Destructive Button Hover Label"),

        # Non-Text UI Components (WCAG 2.2 SC 1.4.11: 3.0:1 AA, 4.5:1 AAA)
        ("Action Primary Control Boundary on Canvas", ap_rgb, canvas_rgb, 3.0, 4.5, "Primary Control Boundary"),
        ("Action Danger Control Boundary on Canvas", ad_rgb, canvas_rgb, 3.0, 4.5, "Destructive Control Boundary"),
        ("Border Strong on Surface Panel", bs_rgb, panel_rgb, 3.0, 4.5, "Panel Boundary Line"),
        ("Border Strong on Surface Canvas", bs_rgb, canvas_rgb, 3.0, 4.5, "Canvas Boundary Line"),
        ("Focus Indicator on Surface Canvas", bf_rgb, canvas_rgb, 3.0, 4.5, "Focus Ring on Canvas"),
        ("Focus Indicator on Surface Panel", bf_rgb, panel_rgb, 3.0, 4.5, "Focus Ring on Panel"),
    ]
    return pairs

get_semantic_contrast_pairs = evaluate_semantic_pairs

def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    prim_file, sem_file = find_target_tokens(target_path)

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: WCAG 2.2 Mathematical Contrast Verifier")
    print("═══════════════════════════════════════════════════════════════")

    if not prim_file or not sem_file:
        print(f"❌ [REJECT] Missing required Design Token files in target: {target_path}")
        print("   Orthotect requires both 'primitives.json' and 'semantics.json' in core/tokens/.")
        print("   (Run 'npx orthotect init <path>' to scaffold standard tokens).")
        sys.exit(1)

    try:
        with open(prim_file, 'r', encoding='utf-8') as f:
            prims = json.load(f)
        with open(sem_file, 'r', encoding='utf-8') as f:
            sems = json.load(f)
    except Exception as e:
        print(f"❌ [REJECT] Failed to parse design token JSON: {e}")
        sys.exit(1)

    failures = 0
    tested_pairs = 0
    passed_aaa = 0
    passed_aa = 0

    themes = sems.get('theme', {})
    if not themes or not isinstance(themes, dict):
        print("❌ [REJECT] Missing 'theme' declarations in semantics.json")
        sys.exit(1)

    for theme_name, theme_data in themes.items():
        print(f"\nTheme Scope: [{theme_name.upper()}]")
        try:
            pairs = evaluate_semantic_pairs(theme_name, theme_data, prims)
        except Exception as e:
            print(f"❌ [REJECT] Token evaluation error in theme [{theme_name}]: {e}")
            failures += 1
            continue

        for label, fg_rgb, bg_rgb, aa_req, aaa_req, usage in pairs:
            ratio = contrast_ratio(fg_rgb, bg_rgb)
            tested_pairs += 1
            
            meets_aa = ratio >= aa_req
            meets_aaa = ratio >= aaa_req
            
            if meets_aaa:
                tier = "PASS (AAA)"
                passed_aaa += 1
                passed_aa += 1
            elif meets_aa:
                tier = "PASS (AA)"
                passed_aa += 1
            else:
                tier = f"FAIL (Needs {aa_req}:1)"
                failures += 1
                
            symbol = "✅" if meets_aa else "❌"
            print(f"  {symbol} {label:<44}: {ratio:5.2f}:1 [{tier:<10}] ({usage})")

    print(f"\nSummary: {tested_pairs} semantic token pairs evaluated across {len(themes)} theme(s).")
    print("Scope: Static Design Token Semantic Matrix. (Rendered DOM element contrast must be separately evaluated via browser tests).")
    if failures == 0 and tested_pairs > 0:
        print(f"✅ [PASS] 100% of tested token pairs meet mandatory WCAG 2.2 AA standards ({passed_aa}/{tested_pairs}).")
        print(f"   Enhanced Tier: {passed_aaa}/{tested_pairs} pairs achieved full WCAG 2.2 AAA.")
        sys.exit(0)
    else:
        print(f"❌ [REJECT] {failures} contrast check(s) failed mandatory WCAG 2.2 AA criteria.")
        sys.exit(1)


if __name__ == '__main__':
    main()

