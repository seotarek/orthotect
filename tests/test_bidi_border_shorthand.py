#!/usr/bin/env python3
"""
P1-2 — Border-family shorthand asymmetry fixtures.

The four-value shorthand rule (`margin`, `padding`, `inset`, `scroll-*`) has been
enforced since C1, and P1-1 extended it into JSX style objects. The border family
was wired into `SHORTHAND_PROPERTIES` from the start but had **no fixture coverage
in any syntax**, so two things were never proven:

1. That `border-width` / `border-style` / `border-color` asymmetry is actually
   detected in plain CSS, HTML `<style>`, and JSX style objects.
2. That the *suggestion* the gate emits for those properties is real CSS. This is
   not hypothetical: before `logical_shorthand_pair()` existed, the gate advised
   `border-width-block`, which is not a CSS property. An agent following that
   advice writes broken CSS and stays broken, with the gate reporting the repair
   as done.

These fixtures pin detection, suggestion validity, and the auto-fix path for the
whole border family across every syntax the gate accepts.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GATES_DIR = os.path.join(ROOT_DIR, 'gates')
GATE = os.path.join(GATES_DIR, 'gate_bidi_logical.py')

if GATES_DIR not in sys.path:
    sys.path.insert(0, GATES_DIR)

from gate_bidi_logical import (              # noqa: E402
    evaluate_declaration,
    logical_shorthand_pair,
    split_css_values,
)

# Every border-family shorthand, with an asymmetric (block != inline) value.
# Note the rule compares token[1] with token[3] — inline-end vs inline-start — so
# `solid dashed solid dashed` is SYMMETRIC and must not be flagged.
ASYMMETRIC = {
    'border-width': '0 0 0 4px',
    'border-style': 'solid dashed solid dotted',
    'border-color': 'red red red blue',
}
# The matching symmetric form: block start == block end, inline start == inline end.
SYMMETRIC = {
    'border-width': '2px 0',
    'border-style': 'solid dashed',
    'border-color': 'red blue',
}
# All four-shorthand families the gate must treat alike.
ALL_FAMILIES = {
    'margin': '0 8px 0 24px',
    'padding': '1px 2px 3px 4px',
    'inset': '0 0 0 8px',
    'scroll-margin': '0 0 0 12px',
    'scroll-padding': '0 0 0 12px',
}
ALL_FAMILIES.update(ASYMMETRIC)


class TestBorderFamilyDetection(unittest.TestCase):
    """Detection in every syntax the gate accepts."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='bidi_border_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def scan(self, filename, body):
        path = os.path.join(self.temp_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
        return scan_path(path)

    def test_css_border_width_asymmetry_is_detected(self):
        viols = self.scan('a.css', '.x { border-width: 0 0 0 4px; }')
        self.assertEqual(len(viols), 1, viols)
        self.assertEqual(viols[0].name, 'border-width')

    def test_css_border_style_asymmetry_is_detected(self):
        viols = self.scan('a.css', '.x { border-style: solid dashed solid dotted; }')
        self.assertEqual(len(viols), 1, viols)
        self.assertEqual(viols[0].name, 'border-style')

    def test_css_border_color_asymmetry_is_detected(self):
        viols = self.scan('a.css', '.x { border-color: red red red blue; }')
        self.assertEqual(len(viols), 1, viols)
        self.assertEqual(viols[0].name, 'border-color')

    def test_html_style_block_detects_border_family(self):
        viols = self.scan('a.html', '<style>.x{border-width:0 0 0 4px}</style>')
        self.assertEqual(len(viols), 1, viols)

    def test_jsx_style_object_detects_camelcase_border_family(self):
        body = 'const C = () => <div style={{ borderWidth: "0 0 0 4px" }} />;\n'
        viols = self.scan('a.jsx', body)
        self.assertEqual(len(viols), 1, viols)
        self.assertEqual(viols[0].name, 'border-width')

    def test_jsx_stylesheet_create_detects_border_family(self):
        body = ('import { StyleSheet } from "react-native";\n'
                'const s = StyleSheet.create({ b: { borderColor: "red red red blue" } });\n')
        viols = self.scan('a.js', body)
        self.assertEqual(len(viols), 1, viols)

    def test_quoted_kebab_border_family_in_jsx_is_detected(self):
        """A quoted kebab key inside a style object is the same declaration."""
        body = 'const C = () => <div style={{ "border-width": "0 0 0 4px" }} />;\n'
        viols = self.scan('a.tsx', body)
        self.assertEqual(len(viols), 1, viols)

    def test_symmetric_border_shorthands_pass(self):
        """Two-value and symmetric four-value forms do not break BiDi symmetry."""
        for name, val in SYMMETRIC.items():
            with self.subTest(name=name, val=val):
                self.assertEqual(evaluate_declaration(name, val, 1, 1), [])

    def test_symmetric_four_value_border_shorthand_passes(self):
        self.assertEqual(evaluate_declaration('border-width', '1px 2px 1px 2px', 1, 1), [])

    def test_logical_border_properties_pass(self):
        self.assertEqual(evaluate_declaration('border-block-width', '1px 2px', 1, 1), [])
        self.assertEqual(evaluate_declaration('border-inline-color', 'red blue', 1, 1), [])


class TestBorderFamilySuggestionValidity(unittest.TestCase):
    """
    The suggestion must be a property an agent can paste into a stylesheet.

    This is the failure that actually happened: `border-width` -> `border-width-block`
    reads plausibly and is not CSS. Asserting the exact pair, and that the emitted
    text parses back into the rule set, is the only way to keep it honest.
    """

    EXPECTED = {
        'border-width': ('border-block-width', 'border-inline-width'),
        'border-style': ('border-block-style', 'border-inline-style'),
        'border-color': ('border-block-color', 'border-inline-color'),
        'margin': ('margin-block', 'margin-inline'),
        'padding': ('padding-block', 'padding-inline'),
        'inset': ('inset-block', 'inset-inline'),
        'scroll-margin': ('scroll-margin-block', 'scroll-margin-inline'),
        'scroll-padding': ('scroll-padding-block', 'scroll-padding-inline'),
    }

    def test_pair_table(self):
        for name, pair in self.EXPECTED.items():
            with self.subTest(name=name):
                self.assertEqual(logical_shorthand_pair(name), pair)

    def test_suggestion_names_only_real_logical_properties(self):
        """
        Every property named in a suggestion must be a logical property the gate
        itself accepts without complaint — i.e. feeding the suggestion back must
        produce zero violations. That closes the loop: the fix cannot suggest
        something the gate would reject.
        """
        for name in ALL_FAMILIES:
            for phys, (block_prop, inline_prop) in ((name, logical_shorthand_pair(name)),):
                with self.subTest(name=name):
                    viols = evaluate_declaration(name, ALL_FAMILIES[name], 1, 1)
                    self.assertEqual(len(viols), 1, f"{name} should be detected")

                    # Reconstruct the pair the suggestion describes and feed both
                    # back through the same evaluator.
                    tokens = split_css_values(ALL_FAMILIES[name])
                    block_val = f"{tokens[0]} {tokens[2]}"
                    inline_val = f"{tokens[3]} {tokens[1]}"
                    for prop, value in ((block_prop, block_val), (inline_prop, inline_val)):
                        with self.subTest(prop=prop, value=value):
                            self.assertEqual(
                                evaluate_declaration(prop, value, 1, 1), [],
                                f"suggested property {prop} is not accepted by the gate")

    def test_no_suggestion_contains_an_invalid_border_suffix_form(self):
        for name in ('border-width', 'border-style', 'border-color'):
            with self.subTest(name=name):
                viols = evaluate_declaration(name, ALL_FAMILIES[name], 1, 1)
                self.assertEqual(len(viols), 1)
                suggestion = viols[0].suggestion
                self.assertNotIn(f'{name}-block', suggestion)
                self.assertNotIn(f'{name}-inline', suggestion)
                radix, _, suffix = name.partition('-')
                self.assertIn(f'border-block-{suffix}', suggestion)
                self.assertIn(f'border-inline-{suffix}', suggestion)

    def test_suggestion_preserves_the_asymmetric_values(self):
        viols = evaluate_declaration('border-width', '0 0 0 4px', 1, 1)
        self.assertEqual(len(viols), 1)
        # block: top/bottom = 0 0; inline: left/right reversed into start/end.
        self.assertIn('border-block-width: 0 0', viols[0].suggestion)
        self.assertIn('border-inline-width: 4px 0', viols[0].suggestion)


class TestBorderFamilyAutoFix(unittest.TestCase):
    """`--fix` must repair the border family, and prove it did."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='bidi_border_fix_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write(self, name, body):
        path = os.path.join(self.temp_dir, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
        return path

    def run_gate(self, *args):
        return subprocess.run([sys.executable, GATE, *args],
                              capture_output=True, text=True)

    def test_fix_repairs_css_border_shorthand(self):
        path = self.write('a.css', '.x { border-width: 0 0 0 4px; }\n')
        res = self.run_gate(self.temp_dir, '--fix')
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        fixed = read_text(path)
        self.assertIn('border-block-width', fixed)
        self.assertIn('border-inline-width', fixed)
        self.assertNotIn('border-width: 0 0 0 4px', fixed)

    def test_fix_repairs_jsx_camelcase_border_shorthand(self):
        path = self.write(
            'a.jsx', 'const C = () => <div style={{ borderWidth: "0 0 0 4px" }} />;\n')
        res = self.run_gate(self.temp_dir, '--fix')
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        fixed = read_text(path)
        self.assertIn('borderBlockWidth', fixed)
        self.assertIn('borderInlineWidth', fixed)
        self.assertNotIn('borderWidthBlock', fixed)
        self.assertNotIn('borderWidthInline', fixed)

    def test_fix_leaves_symmetric_border_shorthand_alone(self):
        path = self.write('a.css', '.x { border-width: 2px 0; }\n')
        before = read_text(path)
        res = self.run_gate(self.temp_dir, '--fix')
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(read_text(path), before)


def read_text(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def scan_path(path):
    """Load scan_file lazily so the module import stays cheap on failure."""
    from gate_bidi_logical import scan_file
    return scan_file(path)


if __name__ == '__main__':
    unittest.main()
