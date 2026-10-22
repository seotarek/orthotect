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
                        "panel": { "$value": "{color.gray.canvas}" }
                    },
                    "action": {
                        "primary": { "$value": "{color.gray.text_bad}" },
                        "danger": { "$value": "{color.gray.text_bad}" }
                    },
                    "content": {
                        "primary": { "$value": "{color.gray.text_bad}" },
                        "secondary": { "$value": "{color.gray.text_bad}" },
                        "inverse": { "$value": "{color.gray.canvas}" }
                    },
                    "border": {
                        "strong": { "$value": "{color.gray.text_bad}" }
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

    def test_empty_subdirectory_in_repo_fails_without_tokens(self):
        """Negative test: A subdirectory located inside the repository tree without its own tokens must NOT borrow root tokens."""
        bin_dir = os.path.join(self.root_dir, 'bin')
        res = self.run_gate(bin_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required Design Token files", res.stdout)


    def test_contrast_checks_content_primary_on_panel(self):
        """Positive test: Gate 1 must evaluate 'Content Primary on Panel' and test 14 total pairs across light & dark themes."""
        showcase_dir = os.path.join(self.root_dir, 'examples', 'golden-showcase')
        res = self.run_gate(showcase_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Content Primary on Panel", res.stdout)
        self.assertIn("14 semantic token pairs evaluated", res.stdout)

if __name__ == '__main__':
    unittest.main()

