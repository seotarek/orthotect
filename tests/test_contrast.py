import unittest
import sys
import os
import subprocess
import tempfile
import json
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gates')))
from gate_contrast_wcag import parse_hex_color, contrast_ratio

class TestContrastCalculator(unittest.TestCase):
    def test_black_white_maximum_contrast(self):
        ratio = contrast_ratio((0, 0, 0), (255, 255, 255))
        self.assertAlmostEqual(ratio, 21.0, places=1)

    def test_identical_colors_minimum_contrast(self):
        ratio = contrast_ratio((255, 255, 255), (255, 255, 255))
        self.assertAlmostEqual(ratio, 1.0, places=1)

    def test_wcag_aa_threshold(self):
        # #595959 on #ffffff is approx 4.54:1 (Passes AA)
        ratio = contrast_ratio(parse_hex_color('#595959'), parse_hex_color('#ffffff'))
        self.assertGreaterEqual(ratio, 4.5)

    def test_failing_contrast(self):
        # #94a3b8 on #ffffff is approx 2.4:1 (Fails AA)
        ratio = contrast_ratio(parse_hex_color('#94a3b8'), parse_hex_color('#ffffff'))
        self.assertLess(ratio, 3.0)

class TestContrastGateE2E(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.gate_script = os.path.join(self.root_dir, 'gates', 'gate_contrast_wcag.py')
        self.temp_dir = tempfile.mkdtemp(prefix='contrast_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_gate(self, target):
        return subprocess.run(['python3', self.gate_script, target],
                              capture_output=True, text=True)

    def test_gate_rejects_empty_directory(self):
        """Negative test: Gate must REJECT directory missing tokens with code 1."""
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required Design Token files", res.stdout)

    def test_gate_rejects_corrupted_json(self):
        """Negative test: Gate must REJECT malformed token JSON."""
        tokens_dir = os.path.join(self.temp_dir, 'core', 'tokens')
        os.makedirs(tokens_dir, exist_ok=True)
        with open(os.path.join(tokens_dir, 'primitives.json'), 'w') as f:
            f.write("{ invalid json")
        with open(os.path.join(tokens_dir, 'semantics.json'), 'w') as f:
            f.write("{}")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Failed to parse design token JSON", res.stdout)

    def test_gate_rejects_failing_contrast_ratio(self):
        """Negative test: Gate must REJECT token pairs with contrast < 4.5:1."""
        tokens_dir = os.path.join(self.temp_dir, 'core', 'tokens')
        os.makedirs(tokens_dir, exist_ok=True)
        # Primitives with very low contrast foreground on canvas
        prims = {
            "color": {
                "gray": {
                    "canvas": { "$value": "#707070" },
                    "text_bad": { "$value": "#787878" } # ~1.14:1 contrast on #707070
                }
            }
        }
        sems = {
            "theme": {
                "light": {
                    "surface": {
                        "canvas": { "$value": "{color.gray.canvas}" },
                        "panel": { "$value": "{color.gray.canvas}" },
                        "subtle": { "$value": "{color.gray.canvas}" },
                        "elevated": { "$value": "{color.gray.canvas}" }
                    },
                    "action": {
                        "primary": { "$value": "{color.gray.text_bad}" },
                        "primaryHover": { "$value": "{color.gray.text_bad}" },
                        "danger": { "$value": "{color.gray.text_bad}" },
                        "dangerHover": { "$value": "{color.gray.text_bad}" }
                    },
                    "content": {
                        "primary": { "$value": "{color.gray.text_bad}" },
                        "secondary": { "$value": "{color.gray.text_bad}" },
                        "tertiary": { "$value": "{color.gray.text_bad}" },
                        "inverse": { "$value": "{color.gray.canvas}" }
                    },
                    "border": {
                        "strong": { "$value": "{color.gray.text_bad}" },
                        "focus": { "$value": "{color.gray.text_bad}" }
                    }
                }
            }
        }

        with open(os.path.join(tokens_dir, 'primitives.json'), 'w') as f:
            json.dump(prims, f)
        with open(os.path.join(tokens_dir, 'semantics.json'), 'w') as f:
            json.dump(sems, f)

        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("❌", res.stdout)
        self.assertIn("failed mandatory WCAG 2.2 AA criteria", res.stdout)

    def test_parse_hex_color_rejects_double_hash(self):
        """Negative test: parse_hex_color must reject double-hash or invalid prefix."""
        with self.assertRaises(ValueError):
            parse_hex_color("##ffffff")
        with self.assertRaises(ValueError):
            parse_hex_color("#fffffff")
        with self.assertRaises(ValueError):
            parse_hex_color("ffffff")
        with self.assertRaises(ValueError):
            parse_hex_color(12345)
        with self.assertRaises(ValueError):
            parse_hex_color(None)

    def test_recursive_alias_resolution(self):
        """Positive test: Multi-hop token references must resolve correctly."""
        from gate_contrast_wcag import resolve_ref
        prims = {
            "color": {
                "step1": { "$value": "{color.step2}" },
                "step2": { "$value": "{color.step3}" },
                "step3": { "$value": "#4f46e5" }
            }
        }
        res = resolve_ref("{color.step1}", prims)
        self.assertEqual(res, "#4f46e5")

    def test_circular_reference_cycle_detection(self):
        """Negative test: Circular token reference cycles must raise ValueError."""
        from gate_contrast_wcag import resolve_ref
        prims = {
            "color": {
                "loopA": { "$value": "{color.loopB}" },
                "loopB": { "$value": "{color.loopA}" }
            }
        }
        with self.assertRaises(ValueError) as ctx:
            resolve_ref("{color.loopA}", prims)
        self.assertIn("Circular reference detected", str(ctx.exception))

    def test_missing_token_reference_detected(self):
        """Negative test: Nonexistent token path must raise ValueError."""
        from gate_contrast_wcag import resolve_ref
        prims = { "color": { "a": { "$value": "#fff" } } }
        with self.assertRaises(ValueError) as ctx:
            resolve_ref("{color.missing}", prims)
        self.assertIn("Unresolved token reference", str(ctx.exception))

    def test_empty_subdirectory_in_repo_fails_without_tokens(self):
        """Negative test: A subdirectory located inside the repository tree without its own tokens must NOT borrow root tokens."""
        bin_dir = os.path.join(self.root_dir, 'bin')
        res = self.run_gate(bin_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required Design Token files", res.stdout)

    def test_contrast_checks_expanded_semantic_matrix(self):
        """Positive test: Gate 1 must evaluate 40 semantic pairs across light and dark themes."""
        showcase_dir = os.path.join(self.root_dir, 'examples', 'golden-showcase')
        res = self.run_gate(showcase_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Content Primary on Panel", res.stdout)
        self.assertIn("40 semantic token pairs evaluated across 2 theme(s)", res.stdout)

    def test_browser_rendered_contrast_verification(self):
        """Browser integration test: Real browser computed styles on golden-showcase meet WCAG criteria."""
        browser_script = os.path.join(self.root_dir, 'tests', 'verify_browser_contrast.mjs')
        res = subprocess.run(['node', browser_script], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Browser contrast verification failed:\n{res.stdout}\n{res.stderr}")
        self.assertIn("Real browser computed-style contrast verified", res.stdout)

    def test_compiler_and_gate_contrast_matrix_symmetry(self):
        """Verify that compiler and gate use identical canonical contrast matrix specification."""
        import core.compiler as compiler_mod
        import gates.gate_contrast_wcag as gate_mod

        comp_matrix = compiler_mod.load_contrast_matrix()
        gate_matrix = gate_mod.load_contrast_matrix()

        self.assertIsNotNone(comp_matrix)
        self.assertIsNotNone(gate_matrix)
        self.assertEqual(len(comp_matrix['pairs']), 20)
        self.assertEqual(len(gate_matrix['pairs']), 20)
        self.assertEqual([p['name'] for p in comp_matrix['pairs']], [p['name'] for p in gate_matrix['pairs']])

    def test_tertiary_content_enforces_aa_4_5_threshold(self):
        """Verify that Content Tertiary on Canvas and Panel require AA threshold of 4.5:1, not 3.0:1."""
        import gates.gate_contrast_wcag as gate_mod
        matrix = gate_mod.load_contrast_matrix()
        tiers = matrix['tiers']
        self.assertEqual(tiers['normal_text']['minRatioAA'], 4.5)

        tertiary_pairs = [p for p in matrix['pairs'] if 'Tertiary' in p['name']]
        self.assertEqual(len(tertiary_pairs), 2)
        for p in tertiary_pairs:
            self.assertEqual(p['tier'], 'normal_text')

    def test_corrupted_local_matrix_raises_fatal_error_without_fallback(self):
        """Negative test: Corrupted or unparseable local contrast-matrix.json must raise ValueError, not silently fall back."""
        import tempfile
        import core.compiler as compiler_mod
        import gates.gate_contrast_wcag as gate_mod

        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_matrix_path = os.path.join(tmp_dir, "contrast-matrix.json")
            with open(bad_matrix_path, "w") as f:
                f.write("{ invalid json syntax !!!")

            # Compiler must raise ValueError
            with self.assertRaises(ValueError) as cm:
                compiler_mod.load_contrast_matrix(tokens_dir=tmp_dir)
            self.assertIn("Corrupted or invalid contrast matrix", str(cm.exception))

            # Gate must raise ValueError
            with self.assertRaises(ValueError) as gm:
                gate_mod.load_contrast_matrix(target_path=tmp_dir)
            self.assertIn("Corrupted or invalid contrast matrix", str(gm.exception))

if __name__ == '__main__':
    unittest.main()


