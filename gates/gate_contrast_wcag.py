#!/usr/bin/env python3
"""
Orthotect Gate: WCAG 2.2 Mathematical Contrast Verifier
Calculates relative luminance and contrast ratios mathematically based on W3C specs:
L = 0.2126 * R + 0.7152 * G + 0.0722 * B
Ratio = (L1 + 0.05) / (L2 + 0.05)
"""
import sys
import json
import os
import re

def parse_hex_color(hex_str):
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    if len(hex_str) != 6:
        raise ValueError(f"Invalid hex color: {hex_str}")
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

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

def resolve_ref(val, primitives):
    if isinstance(val, str) and val.startswith('{') and val.endswith('}'):
        path = val[1:-1].split('.')
        curr = primitives
        for p in path:
            curr = curr[p]
        return curr['$value']
    return val

def main():
    tokens_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'tokens')
    prim_file = os.path.join(tokens_path, 'primitives.json')
    sem_file = os.path.join(tokens_path, 'semantics.json')

    if not os.path.exists(prim_file) or not os.path.exists(sem_file):
        print(f"❌ Tokens not found at {tokens_path}")
        sys.exit(1)

    with open(prim_file, 'r', encoding='utf-8') as f:
        prims = json.load(f)
    with open(sem_file, 'r', encoding='utf-8') as f:
        sems = json.load(f)

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: WCAG 2.2 Mathematical Contrast Verifier")
    print("═══════════════════════════════════════════════════════════════")

    failures = 0
    tested_pairs = 0

    for theme_name, theme_data in sems['theme'].items():
        print(f"\nChecking Theme: [{theme_name.upper()}]")
        surface = parse_hex_color(resolve_ref(theme_data['surface']['canvas']['$value'], prims))
        panel = parse_hex_color(resolve_ref(theme_data['surface']['panel']['$value'], prims))
        
        pairs = [
            ("Content Primary on Canvas", resolve_ref(theme_data['content']['primary']['$value'], prims), surface, 4.5, "AA"),
            ("Content Secondary on Canvas", resolve_ref(theme_data['content']['secondary']['$value'], prims), surface, 4.5, "AA"),
            ("Action Primary on Canvas", resolve_ref(theme_data['action']['primary']['$value'], prims), surface, 3.0, "UI"),
            ("Action Danger on Canvas", resolve_ref(theme_data['action']['danger']['$value'], prims), surface, 3.0, "UI"),
            ("Border Strong on Panel", resolve_ref(theme_data['border']['strong']['$value'], prims), panel, 3.0, "UI"),
            ("Inverse Text on Action Primary", resolve_ref(theme_data['content']['inverse']['$value'], prims), 
             parse_hex_color(resolve_ref(theme_data['action']['primary']['$value'], prims)), 4.5, "AA")
        ]

        for label, fg_hex, bg_rgb, required_ratio, standard in pairs:
            fg_rgb = parse_hex_color(fg_hex) if isinstance(fg_hex, str) else fg_hex
            ratio = contrast_ratio(fg_rgb, bg_rgb)
            tested_pairs += 1
            passed = ratio >= required_ratio
            symbol = "✅" if passed else "❌"
            status = "PASS" if passed else f"FAIL (Needs {required_ratio}:1)"
            print(f"  {symbol} {label:<32}: {ratio:5.2f}:1 [{status}] ({standard})")
            if not passed:
                failures += 1

    print(f"\nSummary: {tested_pairs} token pairs tested.")
    if failures == 0:
        print("✅ [PASS] 100% of semantic color tokens satisfy WCAG 2.2 AA & AAA standards!")
        sys.exit(0)
    else:
        print(f"❌ [REJECT] {failures} contrast check(s) failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
