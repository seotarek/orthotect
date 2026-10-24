import unittest
import subprocess
import tempfile
import os
import shutil

class TestAntiSlopGate(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.gate_script = os.path.join(self.root_dir, 'gates', 'gate_no_slop.py')
        self.temp_dir = tempfile.mkdtemp(prefix='slop_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_gate(self, target):
        return subprocess.run(['python3', self.gate_script, target],
                              capture_output=True, text=True)

    def test_clean_markup_and_css_passes(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><body><h1>Enterprise Console</h1><button class="btn">Deploy</button></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("No AI Slop detected", res.stdout)

    def test_ai_purple_gradient_fails(self):
        css_file = os.path.join(self.temp_dir, 'style.css')
        with open(css_file, 'w') as f:
            f.write('.hero { background: linear-gradient(135deg, #6366f1, #a855f7); }')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Generic AI Purple/Indigo Gradient", res.stdout)

    def test_emoji_in_button_fails(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<button>Launch 🚀</button>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Raw Emoji in Button Icon", res.stdout)

    def test_emoji_in_heading_fails(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<h2>Welcome ✨</h2>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Raw Emoji in Heading element", res.stdout)

    def test_untokenized_inline_style_fails(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<div style="color: #ff0000;">Alert</div>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Inline style bypassing DTCG tokens", res.stdout)

    def test_empty_directory_fails(self):
        empty_dir = os.path.join(self.temp_dir, 'empty')
        os.makedirs(empty_dir, exist_ok=True)
        res = self.run_gate(empty_dir)
        self.assertNotEqual(res.returncode, 0)
    def test_jsx_emoji_in_button_fails(self):
        jsx_file = os.path.join(self.temp_dir, 'Button.jsx')
        with open(jsx_file, 'w') as f:
            f.write('export const Action = () => <button>Deploy 🚀</button>;')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Raw Emoji in Button Icon", res.stdout)

    def test_emoji_nested_inside_button_fails(self):
        html_file = os.path.join(self.temp_dir, 'nested-button.html')
        with open(html_file, 'w') as f:
            f.write('<button class="launch">\n  <span aria-hidden="true">🚀</span>\n  Launch\n</button>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Raw Emoji in Button Icon", res.stdout)

    def test_jsx_untokenized_inline_style_fails(self):
        tsx_file = os.path.join(self.temp_dir, 'Card.tsx')
        with open(tsx_file, 'w') as f:
            f.write('export const Card = () => <div style={{ color: "#ff0000" }}>Alert</div>;')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("JSX Inline style bypassing DTCG tokens", res.stdout)

    def test_jsx_clean_component_passes(self):
        tsx_file = os.path.join(self.temp_dir, 'CleanCard.tsx')
        with open(tsx_file, 'w') as f:
            f.write('export const Card = () => <button className="btn">Deploy</button>;')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("No AI Slop detected", res.stdout)

    def test_clean_button_preceding_text_emoji_does_not_fail(self):
        html_file = os.path.join(self.temp_dir, 'clean-buttons.html')
        with open(html_file, 'w') as f:
            f.write('<button class="copy">Copy</button><p>Celebration 🎉 in paragraph</p><button class="save">Save</button>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0, "Clean buttons with intermediate paragraph emoji must NOT be flagged as button emoji")
        self.assertIn("No AI Slop detected", res.stdout)

    def test_nested_emoji_in_heading_fails(self):
        html_file = os.path.join(self.temp_dir, 'nested-heading.html')
        with open(html_file, 'w') as f:
            f.write('<h2><span>⚡</span> Lightning Performance</h2>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Raw Emoji in Heading element", res.stdout)

    def test_expanded_purple_gradient_fails(self):
        css_file = os.path.join(self.temp_dir, 'purple.css')
        with open(css_file, 'w') as f:
            f.write('.card { background: linear-gradient(to right, #7c3aed, #9333ea); }')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Generic AI Purple/Indigo Gradient", res.stdout)

if __name__ == '__main__':
    unittest.main()

