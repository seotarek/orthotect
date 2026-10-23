import unittest
import sys
import os
import subprocess
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gates')))
from gate_bidi_logical import scan_file, scan_css_content_fallback

class TestBidiScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_logical_properties_pass(self):
        clean_css = """
        .card {
            margin-inline-start: 1rem;
            padding-inline-end: 2rem;
            border-inline-start: 1px solid var(--border);
            text-align: start;
        }
        """
        fpath = os.path.join(self.temp_dir.name, "clean.css")
        with open(fpath, "w") as f:
            f.write(clean_css)
        viols = scan_file(fpath)
        self.assertEqual(len(viols), 0)

    def test_physical_properties_rejected(self):
        physical_css = """
        .card {
            margin-left: 10px;
            padding-right: 20px;
            border-left: 2px solid red;
            text-align: left;
        }
        """
        fpath = os.path.join(self.temp_dir.name, "physical.css")
        with open(fpath, "w") as f:
            f.write(physical_css)
        viols = scan_file(fpath)
    def test_comments_with_prohibited_terms_ignored(self):
        """Comments containing physical property terms must be completely ignored by the AST parser."""
        css_with_comments = """
        /* margin-left: 20px; float: left; padding-right: 10px; */
        .box {
            /* text-align: left; */
            margin-inline-start: 1rem;
        }
        """
        fpath = os.path.join(self.temp_dir.name, "commented.css")
        with open(fpath, "w") as f:
            f.write(css_with_comments)
        viols = scan_file(fpath)
        self.assertEqual(len(viols), 0)

    def test_quoted_strings_and_custom_properties_ignored(self):
        """Quoted strings in content and CSS custom properties (--*) must not trigger false positives."""
        css_strings = """
        .badge::before {
            content: "margin-left: 10px; float: right;";
            --direction-margin-left: 1rem;
            --custom-padding-right: 2rem;
            margin-inline: 1rem;
        }
        """
        fpath = os.path.join(self.temp_dir.name, "strings.css")
        with open(fpath, "w") as f:
            f.write(css_strings)
        viols = scan_file(fpath)
        self.assertEqual(len(viols), 0)

    def test_multiline_declarations_detected(self):
        """Multiline declarations must be detected with accurate line and column diagnostics."""
        css_multiline = """
        .card {
            margin-left:
                24px;
        }
        """
        fpath = os.path.join(self.temp_dir.name, "multiline.css")
        with open(fpath, "w") as f:
            f.write(css_multiline)
        viols = scan_file(fpath)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].line, 3)
        self.assertEqual(viols[0].col, 13)
        self.assertEqual(viols[0].suggestion, "margin-inline-start")

    def test_physical_border_longhands_and_corner_radii_detected(self):
        """Physical border longhands (width, style, color) and corner radii must be rejected."""
        css_borders = """
        .panel {
            border-left-width: 2px;
            border-right-color: #ff0000;
            border-top-left-radius: 8px;
            border-bottom-right-radius: 4px;
        }
        """
        fpath = os.path.join(self.temp_dir.name, "borders.css")
        with open(fpath, "w") as f:
            f.write(css_borders)
        viols = scan_file(fpath)
        self.assertEqual(len(viols), 4)

    def test_html_style_blocks_and_inline_attributes_detected(self):
        """HTML documents must be parsed for both <style> tags and inline style attributes."""
        html_content = """<!DOCTYPE html>
        <html>
        <head>
            <style>
                .hero { margin-left: 32px; }
            </style>
        </head>
        <body>
            <!-- <div style="margin-left: 99px;">Commented out markup</div> -->
            <div style="padding-left: 16px; float: left;">Content</div>
        </body>
        </html>
        """
        fpath = os.path.join(self.temp_dir.name, "page.html")
        with open(fpath, "w") as f:
            f.write(html_content)
        viols = scan_file(fpath)
        # Should detect: .hero margin-left, inline padding-left, inline float: left (commented out one ignored)
        self.assertEqual(len(viols), 3)

    def test_nested_rules_and_media_queries_detected(self):
        """Declarations inside media queries and nested CSS rules must be validated."""
        css_nested = """
        @media (max-width: 768px) {
            .container {
                .sidebar {
                    margin-right: 12px;
                }
            }
        }
        """
        fpath = os.path.join(self.temp_dir.name, "nested.css")
        with open(fpath, "w") as f:
            f.write(css_nested)
        viols = scan_file(fpath)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].suggestion, "margin-inline-end")

    def test_unsupported_file_extension_raises_explicit_error(self):
        """Gate must reject unsupported file extensions rather than claiming full verification."""
        fpath = os.path.join(self.temp_dir.name, "script.py")
        with open(fpath, "w") as f:
            f.write("print('hello')")
        with self.assertRaises(ValueError) as ctx:
            scan_file(fpath)
        self.assertIn("Unsupported styling format", str(ctx.exception))

    def test_bidi_fallback_parser_without_tinycss2(self):
        """Verify the pure standard-library fallback parser ignores comments/strings and flags physical CSS properties."""
        from gates.gate_bidi_logical import scan_css_content_fallback
        sample_css = """
        /* margin-left: 20px in comment */
        .card {
            --sidebar-left: 300px;
            content: "margin-right: 50px";
            margin-left: 16px;
            padding-right: 8px;
            text-align: left;
        }
        """
        viols = scan_css_content_fallback(sample_css)
        self.assertEqual(len(viols), 3)
        props = [v.name for v in viols]
        self.assertIn("margin-left", props)
        self.assertIn("padding-right", props)
        self.assertIn("text-align", props)
        # Verify custom property and comment were ignored
        self.assertNotIn("--sidebar-left", props)

    def test_css_syntax_tokenizer_nested_at_rules_and_escapes(self):
        """Verify the state-machine CssSyntaxTokenizer handles nested @media, escaped quotes, and pseudo-classes."""
        from gates.gate_bidi_logical import scan_css_content_fallback
        complex_css = """
        @media screen and (max-width: 900px) {
            /* Nested media query */
            .box:hover {
                content: "escaped \\"margin-left\\" string";
                padding-left: 12px;
            }
            .safe {
                margin-inline-start: 1rem;
            }
        }
        """
        viols = scan_css_content_fallback(complex_css)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].name, "padding-left")
        self.assertEqual(viols[0].suggestion, "padding-inline-start")

    def test_fallback_slash_handling_and_no_infinite_loop(self):
        """Verify fallback tokenizer parses '/' (font line-height, urls, calc) without cursor stall."""
        css_with_slashes = """
        .icon {
            background-image: url(/images/icon.svg);
            background-size: 100% / 50%;
        }
        .typography {
            font: 14px/1.5 system-ui, sans-serif;
            line-height: calc(100% / 2);
            aspect-ratio: 16 / 9;
        }
        .banned-with-slash {
            margin-left: calc(10px / 2);
        }
        """
        viols = scan_css_content_fallback(css_with_slashes)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].name, "margin-left")
        self.assertEqual(viols[0].suggestion, "margin-inline-start")

    def test_html_inline_and_block_styles_scan(self):
        """Verify HTML files with both <style> blocks and inline style attributes are detected correctly."""
        import gates.gate_bidi_logical as bidi_mod
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .nav { margin-left: 20px; }
            </style>
        </head>
        <body>
            <div style="padding-right: 15px; text-align: left;">Content</div>
            <div style="margin-inline-start: 10px;">Valid logical style</div>
        </body>
        </html>
        """
        # Test with current tinycss2 state
        viols_default = bidi_mod.scan_html_content(sample_html)
        self.assertEqual(len(viols_default), 3)

        # Test simulating HAVE_TINYCSS2 = False
        orig_tinycss2 = bidi_mod.HAVE_TINYCSS2
        try:
            bidi_mod.HAVE_TINYCSS2 = False
            viols_fallback = bidi_mod.scan_html_content(sample_html)
            self.assertEqual(len(viols_fallback), 3)
            props = [v.name for v in viols_fallback]
            self.assertIn("margin-left", props)
            self.assertIn("padding-right", props)
            self.assertIn("text-align", props)
        finally:
            bidi_mod.HAVE_TINYCSS2 = orig_tinycss2

class TestBidiGateE2E(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.gate_script = os.path.join(self.root_dir, 'gates', 'gate_bidi_logical.py')
        self.temp_dir = tempfile.mkdtemp(prefix='bidi_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_gate(self, target):
        return subprocess.run(['python3', self.gate_script, target],
                              capture_output=True, text=True)

    def test_gate_cli_rejects_empty_directory(self):
        """Negative test: Gate must REJECT directory with no style/HTML files."""
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("No styling or markup files", res.stdout)

    def test_gate_cli_rejects_physical_properties(self):
        """Negative test: Gate must REJECT CSS with margin-left and padding-right."""
        css_file = os.path.join(self.temp_dir, 'style.css')
        with open(css_file, 'w') as f:
            f.write(".container { margin-left: 24px; padding-right: 12px; }")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("margin-left", res.stdout)
        self.assertIn("margin-inline-start", res.stdout)

    def test_gate_cli_rejects_physical_floats_and_offsets(self):
        """Negative test: Gate must REJECT float: left and left: 0."""
        css_file = os.path.join(self.temp_dir, 'style.css')
        with open(css_file, 'w') as f:
            f.write(".sidebar { float: left; left: 0; }")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("float: left", res.stdout)

    def test_gate_cli_accepts_clean_logical_properties(self):
        """Positive verification: Gate PASSES pure CSS Logical Properties."""
        css_file = os.path.join(self.temp_dir, 'style.css')
        with open(css_file, 'w') as f:
            f.write(".card { margin-inline: auto; padding-inline: 1.5rem; inset-inline-start: 0; }")
        res = self.run_gate(self.temp_dir)
    def test_jsx_inline_styles_camelcase_rejected(self):
        """Negative test: Gate must REJECT React JSX/TSX with camelCase physical properties like marginLeft."""
        jsx_file = os.path.join(self.temp_dir, 'Component.jsx')
        with open(jsx_file, 'w') as f:
            f.write("export const Card = () => <div style={{ marginLeft: 16, paddingRight: '8px' }}>Test</div>;")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("marginLeft", res.stdout)
        self.assertIn("paddingRight", res.stdout)

    def test_js_styled_components_rejected(self):
        """Negative test: Gate must REJECT styled-components template literals with physical properties."""
        js_file = os.path.join(self.temp_dir, 'styled.js')
        with open(js_file, 'w') as f:
            f.write("const Box = styled.div`\n  margin-left: 20px;\n  border-left: 1px solid red;\n`;")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("margin-left", res.stdout)

    def test_jsx_logical_properties_pass(self):
        """Positive test: Gate must PASS JSX using CSS Logical Properties."""
        tsx_file = os.path.join(self.temp_dir, 'Card.tsx')
        with open(tsx_file, 'w') as f:
            f.write("export const Card = () => <div style={{ marginInlineStart: 16, paddingInlineEnd: '8px' }}>Test</div>;")
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("BiDi Logical Check Passed", res.stdout)

if __name__ == '__main__':
    unittest.main()


