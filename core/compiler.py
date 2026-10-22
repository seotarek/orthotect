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

import re

HEX_REGEX = re.compile(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')

def parse_hex(hex_str):
    if not isinstance(hex_str, str):
        return None
    clean = hex_str.strip()
    m = HEX_REGEX.match(clean)
    if not m:
        return None
    hex_body = m.group(1)
    if len(hex_body) == 3:
        hex_body = ''.join([c * 2 for c in hex_body])
    try:
        return tuple(int(hex_body[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def relative_luminance(rgb):
    """
    Computes relative luminance according to W3C WCAG 2.2 standard (IEC 61966-2-1).
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    """
    if not rgb:
        return 0.0
    r, g, b = [x / 255.0 for x in rgb]
    vals = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in (r, g, b)]
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]

def calculate_contrast(hex1, hex2):
    """
    Computes WCAG 2.2 contrast ratio between two hex colors:
    (L1 + 0.05) / (L2 + 0.05) where L1 is the lighter of the two colors.
    Returns ratio from 1.0 to 21.0, or None if invalid.
    """
    rgb1 = parse_hex(hex1)
    rgb2 = parse_hex(hex2)
    if not rgb1 or not rgb2:
        return None
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def resolve_ref(val, primitives, visited=None):
    """
    Resolves DTCG token references (e.g. '{color.gray.900}') against primitives dictionary.
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

# Explicit WCAG 2.2 Threshold Tiers
CONTRAST_TIERS = {
    'normal_text': 4.5,     # WCAG 2.2 SC 1.4.3 Level AA (Body & Headings < 18pt)
    'large_text': 3.0,      # WCAG 2.2 SC 1.4.3 Level AA (Large Text >= 18pt or 14pt bold)
    'ui_control': 3.0,      # WCAG 2.2 SC 1.4.11 Level AA (UI Components & Focus Indicators)
    'action_text': 4.5      # Primary interactive button text
}

# Required Semantic Token Pairs for every complete theme
MANDATORY_SEMANTIC_PAIRS = [
    (('surface', 'canvas'), ('content', 'primary'), 'normal_text'),
    (('surface', 'panel'), ('content', 'primary'), 'normal_text'),
    (('action', 'primary'), ('content', 'inverse'), 'action_text')
]

def verify_theme_contrast(theme_dict, prims, theme_label):
    results = []
    surfaces = theme_dict.get('surface', {})
    contents = theme_dict.get('content', {})
    actions = theme_dict.get('action', {})

    # 1. Verify all mandatory semantic pairs exist
    for (bg_grp, bg_tok), (fg_grp, fg_tok), tier in MANDATORY_SEMANTIC_PAIRS:
        grp_data = theme_dict.get(bg_grp, {})
        tok_data = grp_data.get(bg_tok)
        if not tok_data or not isinstance(tok_data, dict) or '$value' not in tok_data:
            raise ValueError(f"Missing required semantic token: [{theme_label}] '{bg_grp}.{bg_tok}'")

        fg_grp_data = theme_dict.get(fg_grp, {})
        fg_tok_data = fg_grp_data.get(fg_tok)
        if not fg_tok_data or not isinstance(fg_tok_data, dict) or '$value' not in fg_tok_data:
            raise ValueError(f"Missing required semantic token: [{theme_label}] '{fg_grp}.{fg_tok}'")

    # 2. Dynamic pairing: test all surface tokens against content.primary and content.secondary
    pairs = []
    for s_name in sorted(surfaces.keys()):
        if 'primary' in contents:
            pairs.append((('surface', s_name), ('content', 'primary'), 'normal_text'))
        if 'secondary' in contents:
            pairs.append((('surface', s_name), ('content', 'secondary'), 'normal_text'))

    if 'primary' in actions and 'inverse' in contents:
        pairs.append((('action', 'primary'), ('content', 'inverse'), 'action_text'))
    if 'danger' in actions and 'inverse' in contents:
        pairs.append((('action', 'danger'), ('content', 'inverse'), 'action_text'))

    for (bg_grp, bg_tok), (fg_grp, fg_tok), tier in pairs:
        bg_val = theme_dict.get(bg_grp, {}).get(bg_tok, {}).get('$value')
        fg_val = theme_dict.get(fg_grp, {}).get(fg_tok, {}).get('$value')

        if bg_val and fg_val:
            res_bg = resolve_ref(bg_val, prims)
            res_fg = resolve_ref(fg_val, prims)
            cr = calculate_contrast(res_bg, res_fg)
            required_threshold = CONTRAST_TIERS.get(tier, 4.5)

            if cr is None:
                raise ValueError(
                    f"Invalid or uncomputable color format for contrast pair: [{theme_label}] "
                    f"{bg_grp}.{bg_tok} ({res_bg}) vs {fg_grp}.{fg_tok} ({res_fg})"
                )
            if cr < required_threshold:
                raise ValueError(
                    f"WCAG 2.2 Contrast Failure during token compilation: [{theme_label}] "
                    f"{bg_grp}.{bg_tok} ({res_bg}) vs {fg_grp}.{fg_tok} ({res_fg}) "
                    f"contrast ratio is {cr:.2f}:1 (Must be >= {required_threshold}:1 for {tier})."
                )
            rating = "WCAG AAA" if cr >= 7.0 else "WCAG AA"
            results.append(f" *   - [{theme_label}] {bg_grp}.{bg_tok} vs {fg_grp}.{fg_tok}: {cr:.1f}:1 ({rating} - Tier: {tier})")


    return results

def compile_tokens(tokens_dir):
    prim_file = os.path.join(tokens_dir, 'primitives.json')
    sem_file = os.path.join(tokens_dir, 'semantics.json')
    motion_file = os.path.join(tokens_dir, 'motion.json')
    ergo_file = os.path.join(tokens_dir, 'ergonomics.json')

    if not os.path.exists(prim_file) or not os.path.exists(sem_file):
        raise FileNotFoundError(f"Missing required token files in {tokens_dir}")

    try:
        with open(prim_file, 'r', encoding='utf-8') as f:
            prims = json.load(f)
    except Exception as e:
        raise ValueError(f"Malformed JSON in primitives token file '{prim_file}': {e}")

    try:
        with open(sem_file, 'r', encoding='utf-8') as f:
            sems = json.load(f)
    except Exception as e:
        raise ValueError(f"Malformed JSON in semantics token file '{sem_file}': {e}")

    motion = {}
    if os.path.exists(motion_file):
        try:
            with open(motion_file, 'r', encoding='utf-8') as f:
                motion = json.load(f)
        except Exception as e:
            raise ValueError(f"Malformed JSON in motion token file '{motion_file}': {e}")

    ergo = {}
    if os.path.exists(ergo_file):
        try:
            with open(ergo_file, 'r', encoding='utf-8') as f:
                ergo = json.load(f)
        except Exception as e:
            raise ValueError(f"Malformed JSON in ergonomics token file '{ergo_file}': {e}")

    light_theme = sems.get('theme', {}).get('light', {})
    dark_theme = sems.get('theme', {}).get('dark', {})

    if not light_theme:
        raise ValueError("Missing required 'theme.light' definition in semantics.json")

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
        " *",
        " * NOTE: This is a compile-time mathematical token contrast audit for semantic token pairs.",
        " * It certifies token design contracts, NOT full-interface WCAG conformance.",
        " * Full runtime DOM and markup accessibility verification must be run using gates/gate_contrast_wcag.py.",
        " */",
        "",
        ":root {"
    ])

    # 1. Motion tokens (sorted deterministically)
    if 'motion' in motion and isinstance(motion['motion'], dict):
        lines.append("  /* --- Motion Springs --- */")
        for k in sorted(motion['motion'].keys()):
            v = motion['motion'][k]
            val = v.get('$value', '')
            lines.append(f"  --ot-motion-{k}: {val};")
        lines.append("")

    # 2. Ergonomics tokens (sorted deterministically)
    if 'ergonomics' in ergo and isinstance(ergo['ergonomics'], dict):
        lines.append("  /* --- Cognitive Ergonomics & Fitts Law --- */")
        for category in sorted(ergo['ergonomics'].keys()):
            items = ergo['ergonomics'][category]
            if isinstance(items, dict):
                for k in sorted(items.keys()):
                    v = items[k]
                    val = v.get('$value', '')
                    lines.append(f"  --ot-{category}-{k}: {val};")
        lines.append("")

    # 3. Light Semantic Theme (sorted deterministically)
    lines.append("  /* --- Semantic Tokens (Light Default) --- */")
    for group_name in sorted(light_theme.keys()):
        group_data = light_theme[group_name]
        if isinstance(group_data, dict):
            for token_name in sorted(group_data.keys()):
                token_data = group_data[token_name]
                if isinstance(token_data, dict) and '$value' in token_data:
                    raw_val = token_data['$value']
                    resolved = resolve_ref(raw_val, prims)
                    lines.append(f"  --ot-{group_name}-{token_name}: {resolved};")
    lines.append("}")
    lines.append("")

    # 4. Dark Semantic Theme (sorted deterministically)
    if dark_theme:
        lines.append("/* --- Semantic Tokens (Dark Mode) --- */")
        lines.append('[data-theme="dark"] {')
        for group_name in sorted(dark_theme.keys()):
            group_data = dark_theme[group_name]
            if isinstance(group_data, dict):
                for token_name in sorted(group_data.keys()):
                    token_data = group_data[token_name]
                    if isinstance(token_data, dict) and '$value' in token_data:
                        raw_val = token_data['$value']
                        resolved = resolve_ref(raw_val, prims)
                        lines.append(f"  --ot-{group_name}-{token_name}: {resolved};")
        lines.append("}")
        lines.append("")

        lines.append("@media (prefers-color-scheme: dark) {")
        lines.append("  :root:not([data-theme=\"light\"]) {")
        for group_name in sorted(dark_theme.keys()):
            group_data = dark_theme[group_name]
            if isinstance(group_data, dict):
                for token_name in sorted(group_data.keys()):
                    token_data = group_data[token_name]
                    if isinstance(token_data, dict) and '$value' in token_data:
                        raw_val = token_data['$value']
                        resolved = resolve_ref(raw_val, prims)
                        lines.append(f"    --ot-{group_name}-{token_name}: {resolved};")
        lines.append("  }")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)

PROTECTED_FILES = {
    'package.json', 'package-lock.json', 'CHANGELOG.md', 'README.md',
    'LICENSE', 'CONTRIBUTING.md', 'MANIFESTO.md', 'COMPETITORS.md',
    'bin/orthotect.js', 'core/compiler.py', 'docs/app.js', 'docs/index.html'
}

PROTECTED_DIRS = {'core', 'gates', 'tests', 'bin', 'skills', 'docs'}
PROTECTED_EXTENSIONS = {'.py', '.js', '.mjs', '.json', '.md', '.sh', '.yml', '.yaml', '.html'}

def is_safe_output_path(output_path):
    if not output_path or not isinstance(output_path, str):
        return False
    # A CSS token compiler must output CSS files only
    if not output_path.lower().endswith('.css'):
        return False

    abs_out = os.path.abspath(output_path)
    real_out = os.path.realpath(abs_out)

    # Check git directory
    if '/.git' in real_out or real_out.endswith('/.git') or '/.git' in abs_out:
        return False

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Check against individual protected files (both nominal and real destination)
    for p in PROTECTED_FILES:
        target_abs = os.path.abspath(os.path.join(repo_root, p))
        target_real = os.path.realpath(target_abs)
        if abs_out == target_abs or real_out == target_real or real_out == target_abs:
            return False

    # Check if target or realpath points to protected source files in repository
    for p in (abs_out, real_out):
        try:
            rel = os.path.relpath(p, repo_root)
            if not rel.startswith('..'):
                top_segment = rel.split(os.sep)[0]
                ext = os.path.splitext(p)[1].lower()
                if ext in PROTECTED_EXTENSIONS:
                    return False
                if top_segment in PROTECTED_DIRS:
                    return False
        except ValueError:
            pass

    return True


def main():
    tokens_dir = sys.argv[1] if len(sys.argv) > 1 else 'core/tokens'
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'tokens.css'

    if not is_safe_output_path(output_path):
        print(f"❌ Error compiling tokens: Refusing to overwrite protected repository file: '{output_path}'", file=sys.stderr)
        sys.exit(1)

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
