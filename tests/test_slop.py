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

    def test_anti_pattern_inside_comment_is_ignored(self):
        """Regression: comments mentioning a removed gradient were wrongly rejected.
        Documentation of a past violation must never fail the gate."""
        css_file = os.path.join(self.temp_dir, 'style.css')
        with open(css_file, 'w') as f:
            f.write("""/* Legacy look, removed: linear-gradient(#6366f1, #a855f7) */
/* button used to carry a raw emoji: 🚀 */
.card { color: var(--ot-fg-default); }
""")
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("No AI Slop detected", res.stdout)

    def test_anti_pattern_outside_comment_still_fails(self):
        """Guard against over-correction: real slop next to a comment must still reject."""
        css_file = os.path.join(self.temp_dir, 'style.css')
        with open(css_file, 'w') as f:
            f.write("""/* decorative note */
.hero { background: linear-gradient(90deg, #6366f1, #a855f7); }
""")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Generic AI Purple/Indigo Gradient", res.stdout)

    def test_config_exclude_is_honored(self):
        """Regression: user-configured `exclude` globs were ignored by this gate."""
        gen_dir = os.path.join(self.temp_dir, 'generated')
        os.makedirs(gen_dir, exist_ok=True)
        with open(os.path.join(gen_dir, 'bundle.css'), 'w') as f:
            f.write('.x{background:linear-gradient(#6366f1,#a855f7);}')
        # A clean, in-scope file keeps the scan non-empty so the gate can actually pass.
        with open(os.path.join(self.temp_dir, 'app.css'), 'w') as f:
            f.write('.card{color:var(--ot-fg-default);}')
        with open(os.path.join(self.temp_dir, 'orthotect.config.json'), 'w') as f:
            f.write('{"exclude": ["**/generated/**"]}')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("No AI Slop detected", res.stdout)

    def test_anti_pattern_after_url_in_string_still_fails(self):
        """Regression: `//` inside a string literal is not a comment opener.

        The naive masker blanked everything after "https://" on the line, so slop
        sharing that line passed the gate untouched (fail-open)."""
        jsx_file = os.path.join(self.temp_dir, 'Link.tsx')
        with open(jsx_file, 'w') as f:
            f.write('export const L = () => <button data-doc="https://x.io">Go 🚀</button>;')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Raw Emoji in Button Icon", res.stdout)

    def test_css_slop_after_url_in_string_still_fails(self):
        css_file = os.path.join(self.temp_dir, 'url.css')
        with open(css_file, 'w') as f:
            f.write('.a{background-image:url("https://x.io/a.png")}\n.hero{background:linear-gradient(#6366f1,#a855f7);}\n')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Generic AI Purple/Indigo Gradient", res.stdout)

    def test_comment_marker_inside_url_does_not_mask_later_lines(self):
        """A URL in a comment must not leave the state machine stuck in 'string'."""
        css_file = os.path.join(self.temp_dir, 'doc.css')
        with open(css_file, 'w') as f:
            f.write('/* see https://example.com/docs for the removed gradient */\n.bad{background:linear-gradient(#6366f1,#a855f7);}\n')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Generic AI Purple/Indigo Gradient", res.stdout)

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

