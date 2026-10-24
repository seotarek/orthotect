import unittest
import os
import sys
import tempfile
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gates')))
from gate_bidi_logical import scan_file, apply_bidi_fixes_to_file

class TestAutoFix(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_fix_css_physical_properties(self):
        """Auto-fix must convert CSS physical declarations to standard logical properties."""
        raw_css = """
        .hero {
            margin-left: 16px;
            padding-right: 24px;
            border-left: 1px solid red;
            border-top-left-radius: 8px;
            text-align: left;
            float: right;
            clear: left;
            left: 10px;
            right: auto;
        }
        """
        fpath = os.path.join(self.temp_dir.name, "style.css")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(raw_css)

        # Confirm violations initially exist
        initial_viols = scan_file(fpath)
        self.assertGreater(len(initial_viols), 0)

        # Apply auto-fix
        fixed_count, details = apply_bidi_fixes_to_file(fpath)
        self.assertGreater(fixed_count, 0)

        # Verify 0 violations remain
        remaining_viols = scan_file(fpath)
        self.assertEqual(len(remaining_viols), 0, f"Remaining violations: {remaining_viols}")

        with open(fpath, "r", encoding="utf-8") as f:
            fixed_content = f.read()

        self.assertIn("margin-inline-start: 16px;", fixed_content)
        self.assertIn("padding-inline-end: 24px;", fixed_content)
        self.assertIn("border-inline-start: 1px solid red;", fixed_content)
        self.assertIn("border-start-start-radius: 8px;", fixed_content)
        self.assertIn("text-align: start;", fixed_content)
        self.assertIn("float: inline-end;", fixed_content)
        self.assertIn("clear: inline-start;", fixed_content)
        self.assertIn("inset-inline-start: 10px;", fixed_content)
        self.assertIn("right: auto;", fixed_content)

    def test_fix_preserves_comments_and_strings(self):
        """Auto-fix must never corrupt CSS comments or quoted string literals."""
        raw_css = """
        /* Note: margin-left: 10px; should not change here */
        .icon::before {
            content: "Turn left: margin-left: 5px;";
            margin-left: 12px;
        }
        """
        fpath = os.path.join(self.temp_dir.name, "comment_and_string.css")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(raw_css)

        initial_viols = scan_file(fpath)
        self.assertEqual(len(initial_viols), 1)

        fixed_count, _ = apply_bidi_fixes_to_file(fpath)
        self.assertEqual(fixed_count, 1)

        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("/* Note: margin-left: 10px; should not change here */", content)
        self.assertIn('content: "Turn left: margin-left: 5px;";', content)
        self.assertIn("margin-inline-start: 12px;", content)

        remaining = scan_file(fpath)
        self.assertEqual(len(remaining), 0)

    def test_fix_jsx_style_objects(self):
        """Auto-fix must convert camelCase and quoted properties in JSX and TSX style objects."""
        raw_jsx = """
        import React from 'react';
        export function Card() {
            return (
                <div style={{
                    marginLeft: 10,
                    paddingRight: '20px',
                    textAlign: 'left',
                    left: 15
                }}>
                    Content
                </div>
            );
        }
        """
        fpath = os.path.join(self.temp_dir.name, "Card.jsx")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(raw_jsx)

        initial_viols = scan_file(fpath)
        self.assertGreater(len(initial_viols), 0)

        fixed_count, _ = apply_bidi_fixes_to_file(fpath)
        self.assertGreater(fixed_count, 0)

        remaining = scan_file(fpath)
        self.assertEqual(len(remaining), 0, f"Remaining violations in JSX: {remaining}")

        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("marginInlineStart: 10", content)
        self.assertIn("paddingInlineEnd: '20px'", content)
        self.assertIn("textAlign: 'start'", content)
        self.assertIn("insetInlineStart: 15", content)

    def test_fix_html_styles(self):
        """Auto-fix must convert declarations inside HTML <style> blocks and style attributes."""
        raw_html = """<!DOCTYPE html>
        <html>
        <head>
            <style>
                .nav { margin-left: 10px; text-align: left; }
            </style>
        </head>
        <body>
            <div style="padding-right: 8px; text-align: right;">Hello</div>
        </body>
        </html>"""
        fpath = os.path.join(self.temp_dir.name, "index.html")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(raw_html)

        initial_viols = scan_file(fpath)
        self.assertGreater(len(initial_viols), 0)

        fixed_count, _ = apply_bidi_fixes_to_file(fpath)
        self.assertGreater(fixed_count, 0)

        remaining = scan_file(fpath)
        self.assertEqual(len(remaining), 0, f"Remaining violations in HTML: {remaining}")

        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("margin-inline-start: 10px;", content)
        self.assertIn("text-align: start;", content)
        self.assertIn("padding-inline-end: 8px;", content)
        self.assertIn("text-align: end;", content)

    def test_gate_cli_fix_flag(self):
        """CLI invocation of gate_bidi_logical.py with --fix should remediate files and exit 0."""
        raw_css = ".box { margin-left: 5px; float: left; }"
        fpath = os.path.join(self.temp_dir.name, "box.css")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(raw_css)

        gate_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gates', 'gate_bidi_logical.py'))
        res = subprocess.run([sys.executable, gate_script, self.temp_dir.name, "--fix"], capture_output=True, text=True)

        self.assertEqual(res.returncode, 0, f"Output: {res.stdout}\nErr: {res.stderr}")
        self.assertIn("[AUTO-FIX]", res.stdout)

        # File should be completely clean
        self.assertEqual(len(scan_file(fpath)), 0)

if __name__ == '__main__':
    unittest.main()
