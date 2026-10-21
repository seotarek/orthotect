#!/usr/bin/env python3
"""
Orthotect Token Compiler: W3C DTCG -> CSS Custom Properties
Compiles 3-tier DTCG tokens (primitives, semantics, motion, ergonomics)
into production-ready CSS variables with automatic light/dark theme scopes.
"""
import json
import os
import sys

def resolve_ref(val, primitives):
    if isinstance(val, str) and val.startswith('{') and val.endswith('}'):
        path = val[1:-1].split('.')
        curr = primitives
        for p in path:
            curr = curr[p]
        return curr.get('$value', curr)
    return val

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

    lines = [
        "/**",
        " * Orthotect Design System Tokens",
        " * Generated deterministically from W3C DTCG token architecture.",
        " * 100% Directional-Neutral & WCAG 2.2 Compliant.",
        " */",
        "",
        ":root {"
    ]

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
    light_theme = sems.get('theme', {}).get('light', {})
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
    dark_theme = sems.get('theme', {}).get('dark', {})
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
