import unittest
import subprocess
import tempfile
import os
import shutil

class TestCWVBudgetGate(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.gate_script = os.path.join(self.root_dir, 'gates', 'gate_cwv_budget.mjs')
        self.temp_dir = tempfile.mkdtemp(prefix='cwv_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_gate(self, target):
        return subprocess.run(['node', self.gate_script, target],
                              capture_output=True, text=True)

    def test_valid_html_with_reserved_dimensions_passes(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Test</title><script src="app.js" defer></script></head><body><img src="logo.png" width="200" height="100" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_missing_height_fails_cls_gate(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" width="200" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_missing_width_fails_cls_gate(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" height="100" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_aspect_ratio_style_passes(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="aspect-ratio: 16/9;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_aspect_ratio_auto_with_ratio_passes(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="aspect-ratio: auto 16 / 9;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_invalid_aspect_ratio_value_fails(self):
        """Negative test: aspect-ratio with invalid non-numeric syntax must be rejected."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="aspect-ratio: invalid-value;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid CSS aspect-ratio value", res.stdout)

    def test_zero_aspect_ratio_fails(self):
        """Negative test: aspect-ratio: 0/0 must be rejected."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="aspect-ratio: 0 / 0;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid CSS aspect-ratio value", res.stdout)

    def test_aspect_ratio_in_class_name_fails(self):
        """Negative test: aspect-ratio inside class attribute must NOT bypass dimensions check."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" class="aspect-ratio-wrapper" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_mismatched_closing_tag_fails(self):
        """Negative test: malformed HTML with stray/mismatched closing tags must be rejected."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><div><p>Hello</div></p></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Malformed HTML", res.stdout)

    def test_attributes_with_tag_characters_handled_correctly(self):
        """Ensure quotes containing < or > do not confuse the stack tokenizer."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><div title="a < b and c > d"><img src="logo.png" width="10" height="10" alt="Logo"></div></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_blocking_script_in_head_fails(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><script src="heavy.js"></script></head><body><h1>Hello</h1></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Synchronous blocking <script>", res.stdout)

    def test_minified_deep_dom_fails(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        nested = "<div>" * 35 + "Text" + "</div>" * 35
        with open(html_file, 'w') as f:
            f.write(f"<!DOCTYPE html><html><head></head><body>{nested}</body></html>")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Excessive DOM depth", res.stdout)

if __name__ == '__main__':
    unittest.main()
