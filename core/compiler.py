#!/usr/bin/env python3
"""
Orthotect Token Compiler: W3C DTCG -> CSS Custom Properties
Compiles 3-tier DTCG tokens (primitives, semantics, motion, ergonomics)
into production-ready CSS variables with automatic light/dark theme scopes,
and computes mathematical WCAG 2.2 contrast ratios for paired semantic tokens.
"""
import json
import os
import sys

def parse_hex(hex_str):
    if not isinstance(hex_str, str):
        return None
    clean = hex_str.strip().lstrip('#')
    if len(clean) == 3:
        clean = ''.join([c * 2 for c in clean])
    if len(clean) != 6:
        return None
    try:
        return tuple(int(clean[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return None

def relative_luminance(rgb):
    if not rgb:
        return 0.0
    r, g, b = [x / 255.0 for x in rgb]
    vals = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in (r, g, b)]
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]

def calculate_contrast(hex1, hex2):
    rgb1 = parse_hex(hex1)
    rgb2 = parse_hex(hex2)
    if not rgb1 or not rgb2:
        return None
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def resolve_ref(val, primitives):
    if isinstance(val, str) and val.startswith('{') and val.endswith('}'):
        path = val[1:-1].split('.')
        curr = primitives
        for p in path:
            curr = curr[p]
        return curr.get('$value', curr)
    return val

def verify_theme_contrast(theme_dict, prims, theme_label):
    results = []
    # Dynamic pairing: test all surface tokens against content.primary and content.secondary
    surfaces = theme_dict.get('surface', {})
    contents = theme_dict.get('content', {})

    pairs = []
    for s_name in surfaces.keys():
        if 'primary' in contents:
            pairs.append((('surface', s_name), ('content', 'primary')))
        if 'secondary' in contents:
            pairs.append((('surface', s_name), ('content', 'secondary')))

    if 'primary' in theme_dict.get('action', {}) and 'inverse' in contents:
        pairs.append((('action', 'primary'), ('content', 'inverse')))
    if 'danger' in theme_dict.get('action', {}) and 'inverse' in contents:
        pairs.append((('action', 'danger'), ('content', 'inverse')))

    for (bg_grp, bg_tok), (fg_grp, fg_tok) in pairs:
        bg_val = theme_dict.get(bg_grp, {}).get(bg_tok, {}).get('$value')
        fg_val = theme_dict.get(fg_grp, {}).get(fg_tok, {}).get('$value')

        if bg_val and fg_val:
            res_bg = resolve_ref(bg_val, prims)
            res_fg = resolve_ref(fg_val, prims)
            cr = calculate_contrast(res_bg, res_fg)
            if cr is not None:
                # Mandatory enforcement threshold: reject if below WCAG AA (4.5:1)
                if cr < 4.5:
                    raise ValueError(
                        f"WCAG 2.2 Contrast Failure during token compilation: [{theme_label}] "
                        f"{bg_grp}.{bg_tok} ({res_bg}) vs {fg_grp}.{fg_tok} ({res_fg}) "
                        f"contrast ratio is {cr:.2f}:1 (Must be >= 4.5:1 to pass WCAG AA)."
                    )
                rating = "WCAG AAA" if cr >= 7.0 else "WCAG AA"
                results.append(f" *   - [{theme_label}] {bg_grp}.{bg_tok} vs {fg_grp}.{fg_tok}: {cr:.1f}:1 ({rating})")

    return results

def compile_tokens(tokens_dir):
    prim_file = os.path.join(tokens_dir, 'primitives.json')
    sem_file = os.path.join(tokens_dir, 'semantics.json')
    motion_file = os.path.join(tokens_dir, 'motion.json')
    ergo_file = os.path.join(tokens_dir, 'ergonomics.json')

    if not os.path.exists(prim_file) or not os.path.exists(sem_file):
        raise FileNotFoundError(f"Missing required token files in {tokens_dir}")

    with open(prim_file, 'r', encoding='utf-8') as f:
        prims = json.load(f)
    with open(sem_file, 'r', encoding='utf-8') as f:
        sems = json.load(f)

    motion = {}
    if os.path.exists(motion_file):
        with open(motion_file, 'r', encoding='utf-8') as f:
            motion = json.load(f)

    ergo = {}
    if os.path.exists(ergo_file):
        with open(ergo_file, 'r', encoding='utf-8') as f:
            ergo = json.load(f)

    # Perform mathematical contrast verification on declared semantic pairs
    light_theme = sems.get('theme', {}).get('light', {})
    dark_theme = sems.get('theme', {}).get('dark', {})

    contrast_logs = []
    if light_theme:
        contrast_logs.extend(verify_theme_contrast(light_theme, prims, "light"))
    if dark_theme:
        contrast_logs.extend(verify_theme_contrast(dark_theme, prims, "dark"))

    lines = [
        "/**",
        " * Orthotect Design System Tokens",
        " * Generated deterministically from W3C DTCG token architecture.",
        " * Directional-Neutral (100% CSS Logical Properties).",
        " *",
        " * Semantic Contrast Verification (WCAG 2.2 Math):"
    ]
    lines.extend(contrast_logs)
    lines.extend([
        " * Note: Full interface markup contrast is certified via gates/gate_contrast_wcag.py.",
        " */",
        "",
        ":root {"
    ])

    # 1. Motion tokens
    if 'motion' in motion:
        lines.append("  /* --- Motion Springs --- */")
        for k, v in motion['motion'].items():
            val = v.get('$value', '')
            lines.append(f"  --ot-motion-{k}: {val};")
        lines.append("")

    # 2. Ergonomics tokens
    if 'ergonomics' in ergo:
        lines.append("  /* --- Cognitive Ergonomics & Fitts Law --- */")
        for category, items in ergo['ergonomics'].items():
            if isinstance(items, dict):
                for k, v in items.items():
                    val = v.get('$value', '')
                    lines.append(f"  --ot-{category}-{k}: {val};")
        lines.append("")

    # 3. Light Semantic Theme
    lines.append("  /* --- Semantic Tokens (Light Default) --- */")
    for group_name, group_data in light_theme.items():
        if isinstance(group_data, dict):
            for token_name, token_data in group_data.items():
                if isinstance(token_data, dict) and '$value' in token_data:
                    raw_val = token_data['$value']
                    resolved = resolve_ref(raw_val, prims)
                    lines.append(f"  --ot-{group_name}-{token_name}: {resolved};")
    lines.append("}")
    lines.append("")

    # 4. Dark Semantic Theme
    if dark_theme:
        lines.append("/* --- Semantic Tokens (Dark Mode) --- */")
        lines.append('[data-theme="dark"] {')
        for group_name, group_data in dark_theme.items():
            if isinstance(group_data, dict):
                for token_name, token_data in group_data.items():
                    if isinstance(token_data, dict) and '$value' in token_data:
                        raw_val = token_data['$value']
                        resolved = resolve_ref(raw_val, prims)
                        lines.append(f"  --ot-{group_name}-{token_name}: {resolved};")
        lines.append("}")
        lines.append("")

        lines.append("@media (prefers-color-scheme: dark) {")
        lines.append("  :root:not([data-theme=\"light\"]) {")
        for group_name, group_data in dark_theme.items():
            if isinstance(group_data, dict):
                for token_name, token_data in group_data.items():
                    if isinstance(token_data, dict) and '$value' in token_data:
                        raw_val = token_data['$value']
                        resolved = resolve_ref(raw_val, prims)
                        lines.append(f"    --ot-{group_name}-{token_name}: {resolved};")
        lines.append("  }")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)

def main():
    tokens_dir = sys.argv[1] if len(sys.argv) > 1 else 'core/tokens'
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'tokens.css'

    try:
        css = compile_tokens(tokens_dir)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(css)
        print(f"✅ Successfully compiled DTCG tokens from '{tokens_dir}' -> '{output_path}'")
    except Exception as e:
        print(f"❌ Error compiling tokens: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
