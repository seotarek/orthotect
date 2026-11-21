#!/usr/bin/env python3
"""
P1-1 — `--fix` must verify its own result, and JSX style objects must enforce
the same rules as plain CSS.

Two defects are pinned here.

1. **A partial fix did not fail explicitly.** `apply_bidi_fixes_to_file()`
   subtracted the remaining violation count from the initial count and reported
   the difference as "repaired", then classified the file purely on the re-scan.
   A file containing both a repairable and an unrepairable violation therefore
   produced a run whose output read like a successful repair, with no statement
   that the file still failed.

2. **JSX style objects skipped whole rule families.** Asymmetric four-value
   shorthands (`margin: "0 8px 0 24px"`) and the value keywords `float`/`clear`
   were rejected in plain CSS but accepted inside `style={{ ... }}` and
   `StyleSheet.create({...})` — the C1 bypass re-opened in a second syntax.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GATE = os.path.join(ROOT_DIR, 'gates', 'gate_bidi_logical.py')

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


class FixHarness(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='bidi_p11_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write(self, name, body):
        path = os.path.join(self.temp_dir, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
        return path

    def run_gate(self, *args):
        return subprocess.run([sys.executable, GATE, self.temp_dir, *args],
                              capture_output=True, text=True)


class TestPartialFixFailsLoudly(FixHarness):
    """
    P1-1: a repair attempt that leaves violations must say so and fail.

    The fixture is CSS with an unbalanced closing brace. Asymmetric shorthands were
    used here originally, but the CSS repair path now handles them (P1-2), so they
    no longer exercise a partial fix; a malformed block still does, because the
    declaration transformer cannot rewrite text it could not parse.
    """

    MIXED = '.a { margin-left: 4px }\n.b { padding-right: 8px }}\n'

    def test_partial_fix_exits_one_and_names_remaining_violation(self):
        self.write('mixed.css', self.MIXED)
        res = self.run_gate('--fix')
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn('[PARTIAL FIX]', res.stdout)
        self.assertIn('1 violation(s) remain', res.stdout)

    def test_partial_fix_summary_does_not_read_as_success(self):
        """The repair count must never be printed without the unresolved remainder."""
        self.write('mixed.css', self.MIXED)
        res = self.run_gate('--fix')
        self.assertIn('did not certify the target', res.stdout)

    def test_complete_fix_still_passes(self):
        self.write('ok.css', '.a { margin-left: 4px; text-align: right; }\n')
        res = self.run_gate('--fix')
        self.assertEqual(res.returncode, 0, res.stdout)
        with open(os.path.join(self.temp_dir, 'ok.css'), encoding='utf-8') as f:
            content = f.read()
        self.assertIn('margin-inline-start', content)
        self.assertIn('text-align: end', content)

    def test_apply_returns_remaining_violations(self):
        """The function's contract now exposes the post-fix scan, not just a delta."""
        import importlib
        if ROOT_DIR not in sys.path:
            sys.path.insert(0, os.path.join(ROOT_DIR, 'gates'))
        gate_mod = importlib.import_module('gate_bidi_logical')
        path = self.write('mixed.css', '.a { margin-left: 4px }\n.b { padding-right: 8px }}\n')
        fixed, details, remaining = gate_mod.apply_bidi_fixes_to_file(path)
        # Both physical declarations are repairable, so both are counted; what
        # survives is the syntax error the transformer cannot rewrite.
        self.assertEqual(fixed, 2, 'both repairable declarations should be counted')
        self.assertEqual(len(details), 2)
        self.assertEqual(len(remaining), 1, remaining)
        self.assertEqual(remaining[0].name, 'PARSE_ERROR')

    def test_apply_returns_empty_remaining_when_fully_repaired(self):
        """A complete repair must report zero remaining, so `--fix` can reach green."""
        import importlib
        if ROOT_DIR not in sys.path:
            sys.path.insert(0, os.path.join(ROOT_DIR, 'gates'))
        gate_mod = importlib.import_module('gate_bidi_logical')
        path = self.write('ok.css', '.b { margin: 0 8px 0 24px; }\n')
        fixed, details, remaining = gate_mod.apply_bidi_fixes_to_file(path)
        self.assertEqual(fixed, 1)
        self.assertEqual(remaining, [])


class TestJsxStyleObjectRuleParity(FixHarness):
    """
    The JSX scanner must enforce the same rule families as the CSS scanner.
    Each case is asserted in both syntaxes so a future regression shows up as a
    parity break rather than as a silently weakened gate.
    """

    def _scans_as_violation(self, body, name):
        self.write(name, body)
        return self.run_gate().returncode

    def test_asymmetric_shorthand_is_rejected_in_jsx(self):
        jsx = self._scans_as_violation(
            'export const A = () => <div style={{margin: "0 8px 0 24px"}} />;\n', 'a.jsx')
        css = self._scans_as_violation('.a { margin: 0 8px 0 24px; }\n', 'a.css')
        self.assertEqual(jsx, 1, 'asymmetric shorthand must fail in JSX')
        self.assertEqual(css, 1, 'asymmetric shorthand must fail in CSS')
        self.assertEqual(jsx, css, 'JSX and CSS must agree')

    def test_padding_and_inset_shorthands_rejected_in_jsx(self):
        for decl in ('padding: "0 8px 0 24px"', 'inset: "0 8px 0 24px"'):
            with self.subTest(decl=decl):
                path = os.path.join(self.temp_dir, 'p.jsx')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(f'export const A = () => <div style={{{{{decl}}}}} />;\n')
                self.assertEqual(self.run_gate().returncode, 1)

    def test_float_and_clear_keywords_rejected_in_jsx(self):
        for decl in ('float: "left"', 'clear: "right"'):
            with self.subTest(decl=decl):
                path = os.path.join(self.temp_dir, 'k.jsx')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(f'export const A = () => <div style={{{{{decl}}}}} />;\n')
                self.assertEqual(self.run_gate().returncode, 1)

    def test_symmetric_shorthand_still_accepted_in_jsx(self):
        """Guard against over-correction: direction-neutral shorthands stay valid."""
        path = os.path.join(self.temp_dir, 's.jsx')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('export const A = () => <div style={{margin: "0 8px"}} />;\n')
        self.assertEqual(self.run_gate().returncode, 0)

    def test_allow_camel_case_does_not_weaken_value_rules(self):
        """
        `bidi.allowCamelCase` exists so React Native may use camelCase property
        names; it must not permit directionally physical *values*.
        """
        with open(os.path.join(self.temp_dir, 'f.jsx'), 'w', encoding='utf-8') as f:
            f.write('export const A = () => <div style={{marginLeft: "4px", float: "left"}} />;\n')
        with open(os.path.join(self.temp_dir, 'orthotect.config.json'), 'w', encoding='utf-8') as f:
            f.write('{"bidi": {"allowCamelCase": true}}')
        self.assertEqual(self.run_gate().returncode, 1)


class TestJsxAutoFixReachesGreen(FixHarness):
    """`--fix` must repair what the new detection reports, or it is half a feature."""

    def _fix_and_rescan(self, body, name='f.jsx'):
        path = self.write(name, body)
        fixed = self.run_gate('--fix')
        with open(path, encoding='utf-8') as f:
            content = f.read()
        rescan = self.run_gate()
        return fixed, content, rescan

    def test_float_is_repaired_to_logical_keyword(self):
        fixed, content, rescan = self._fix_and_rescan(
            'export const A = () => <div style={{float: "left"}} />;\n')
        self.assertEqual(fixed.returncode, 0, fixed.stdout)
        self.assertIn('inline-start', content)
        self.assertEqual(rescan.returncode, 0)

    def test_camel_case_shorthand_expands_to_logical_pair(self):
        fixed, content, rescan = self._fix_and_rescan(
            'export const A = () => <div style={{margin: "0 8px 0 24px"}} />;\n')
        self.assertEqual(fixed.returncode, 0, fixed.stdout)
        self.assertIn('marginInline', content)
        self.assertIn('marginBlock', content)
        self.assertEqual(rescan.returncode, 0)

    def test_border_shorthand_uses_correct_infix(self):
        """
        `borderWidth` must become `borderBlockWidth`, not `borderWidthBlock`.
        The block/inline infix sits *before* the sub-property for the border family.
        """
        fixed, content, rescan = self._fix_and_rescan(
            'export const A = () => <div style={{borderWidth: "0 8px 0 24px"}} />;\n')
        self.assertEqual(fixed.returncode, 0, fixed.stdout)
        self.assertIn('borderBlockWidth', content)
        self.assertIn('borderInlineWidth', content)
        self.assertNotIn('borderWidthBlock', content)
        self.assertEqual(rescan.returncode, 0)

    def test_quoted_kebab_shorthand_keeps_valid_syntax(self):
        fixed, content, rescan = self._fix_and_rescan(
            'export const A = () => <div style={{\'border-width\': "0 8px 0 24px"}} />;\n')
        self.assertEqual(fixed.returncode, 0, fixed.stdout)
        self.assertIn("'border-block-width'", content)
        self.assertEqual(content.count('"'), content.count('"'), 'quotes must balance')
        self.assertEqual(content.count("'") % 2, 0, 'quotes must balance')
        self.assertEqual(rescan.returncode, 0)


class TestLogicalShorthandPairInflection(unittest.TestCase):
    """The suggestion text itself must be valid CSS, not just well-intentioned."""

    def setUp(self):
        if os.path.join(ROOT_DIR, 'gates') not in sys.path:
            sys.path.insert(0, os.path.join(ROOT_DIR, 'gates'))
        import importlib
        self.mod = importlib.import_module('gate_bidi_logical')

    def test_border_family_infix_precedes_sub_property(self):
        self.assertEqual(self.mod.logical_shorthand_pair('border-width'),
                         ('border-block-width', 'border-inline-width'))
        self.assertEqual(self.mod.logical_shorthand_pair('border-style'),
                         ('border-block-style', 'border-inline-style'))
        self.assertEqual(self.mod.logical_shorthand_pair('border-color'),
                         ('border-block-color', 'border-inline-color'))

    def test_other_shorthands_keep_suffix_form(self):
        self.assertEqual(self.mod.logical_shorthand_pair('margin'),
                         ('margin-block', 'margin-inline'))
        self.assertEqual(self.mod.logical_shorthand_pair('scroll-margin'),
                         ('scroll-margin-block', 'scroll-margin-inline'))

    def test_border_suggestion_is_real_css(self):
        viols = self.mod.evaluate_declaration('border-width', '0 8px 0 24px', 1, 1)
        self.assertEqual(len(viols), 1)
        self.assertIn('border-block-width', viols[0].suggestion)
        self.assertNotIn('border-width-block', viols[0].suggestion)


if __name__ == '__main__':
    unittest.main()
