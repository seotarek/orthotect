import unittest
import subprocess
import tempfile
import os
import shutil


def _parse5_installed(root_dir):
    """The DOM gate parses through parse5, a declared runtime dependency."""
    return os.path.isdir(os.path.join(root_dir, 'node_modules', 'parse5'))


class TestCWVBudgetGate(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.gate_script = os.path.join(self.root_dir, 'gates', 'gate_cwv_budget.mjs')
        self.temp_dir = tempfile.mkdtemp(prefix='cwv_test_')

        # Fail closed in CI (a missing dependency must break the build, never silently
        # reduce coverage) but skip locally, where `npm ci` may legitimately not have run.
        if not _parse5_installed(self.root_dir):
            if os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ:
                self.fail("Mandatory DOM gate tests cannot run: parse5 is not installed in CI. "
                          "Run `npm ci` before the test step.")
            self.skipTest("parse5 not installed — run `npm ci` to enable the DOM & CLS budget suite")

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

    def test_data_width_and_data_height_fails_cls_gate(self):
        """Negative test: data-width/data-height attributes must NOT bypass width/height validation."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" data-width="800" data-height="450" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("data-width/data-height", res.stdout)

    def test_zero_or_invalid_width_attribute_fails(self):
        """Negative test: width="0" or width="invalid" must be rejected."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" width="0" height="100" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid width attribute", res.stdout)

    def test_empty_width_attribute_fails(self):
        """Negative test: width="" must be rejected."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" width="" height="100" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid width attribute", res.stdout)

    def test_missing_height_fails_cls_gate(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" width="200" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_aspect_ratio_inside_custom_css_variable_fails(self):
        """Negative test: aspect-ratio inside another CSS variable value must NOT be accepted as real aspect-ratio."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="--custom-prop: aspect-ratio: 16/9;" alt="Logo"></body></html>')
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
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="aspect-ratio: invalid-value;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid CSS aspect-ratio value", res.stdout)

    def test_mismatched_closing_tag_fails(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><div><p>Hello</div></p></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("mismatched closing tag", res.stdout)

    def test_unclosed_tags_at_eof_fails(self):
        """Negative test: unclosed non-void tags remaining at EOF must be rejected."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><div><section><p>Unclosed paragraph')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("unclosed tag(s) remaining at end of file", res.stdout)

    def test_unclosed_opening_syntax_at_eof_fails(self):
        """Negative test: unclosed '<' syntax at EOF must be rejected."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><div>Hello <span class=')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("unclosed tag opening or attribute syntax", res.stdout)

    def test_attributes_with_tag_characters_handled_correctly(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><div title="a < b and c > d"><img src="logo.png" width="10" height="10" alt="Logo"></div></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_minified_deep_dom_fails(self):
        html_file = os.path.join(self.temp_dir, 'index.html')
        nested = "<div>" * 35 + "Text" + "</div>" * 35
        with open(html_file, 'w') as f:
            f.write(f"<!DOCTYPE html><html><head></head><body>{nested}</body></html>")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Excessive DOM depth", res.stdout)

    def test_width_with_px_unit_rejected(self):
        """Negative test: width="200px" must be rejected per HTML5 integer dimension rules."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" width="200px" height="100" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid width attribute value", res.stdout)

    def test_width_with_decimal_rejected(self):
        """Negative test: decimal dimensions like width="150.5" must be rejected."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" width="150.5" height="100" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid width attribute value", res.stdout)

    def test_aspect_ratio_inside_css_comment_fails(self):
        """Negative test: aspect-ratio inside a CSS comment must not satisfy dimensions."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="/* aspect-ratio: 16/9; */ display: block;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_repeated_aspect_ratio_with_invalid_override_fails(self):
        """Negative test: later invalid aspect-ratio overrides earlier valid one in CSS cascade."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="aspect-ratio: 16/9; aspect-ratio: invalid;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid CSS aspect-ratio value", res.stdout)

    def test_div_trailing_solidus_rejected(self):
        """Negative test: <div/> trailing solidus is invalid self-closing in HTML5."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><div/><p>Hello</p></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("trailing solidus", res.stdout)

    def test_html5_optional_closing_tags_with_media_pass(self):
        """Ensure standard HTML5 optional closing tags on lists with media pass without errors."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><ul><li>Item 1<li>Item 2</ul><img src="a.png" width="10" height="10" alt="x"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_custom_elements_supported_and_budgeted(self):
        """Ensure custom elements are counted towards DOM depth."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><app-root><nav-bar><user-card><img src="a.png" width="10" height="10" alt="x"></user-card></nav-bar></app-root></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_negative_width_rejected(self):
        """Negative test: width="-50" must be rejected per HTML5 positive integer dimension rules."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" width="-50" height="100" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid width attribute value", res.stdout)

    def test_aspect_ratio_auto_alone_rejected(self):
        """Negative test: 'aspect-ratio: auto' without a fixed ratio does not reserve layout space."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><img src="logo.png" style="aspect-ratio: auto;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_unclosed_attribute_at_eof_fails(self):
        """Negative test: unclosed attribute string at EOF triggers parse error."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head></head><body><div id="open_attr')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Malformed HTML", res.stdout)

    def test_adversarial_deep_nesting_handled_without_call_stack_overflow(self):
        """Stress test: 500 levels of nested tags must be handled iteratively without Node.js stack overflow."""
        html_file = os.path.join(self.temp_dir, 'index.html')
        nested = "<div>" * 500 + "Leaf Node" + "</div>" * 500
        with open(html_file, 'w') as f:
            f.write(f"<!DOCTYPE html><html><head></head><body>{nested}</body></html>")
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Excessive DOM depth", res.stdout)
        self.assertNotIn("RangeError: Maximum call stack size exceeded", res.stderr)

    def test_empty_html_file_rejected(self):
        """Negative test: completely empty HTML file must be rejected as non-scannable."""
        html_file = os.path.join(self.temp_dir, 'empty.html')
        with open(html_file, 'w') as f:
            f.write('')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Empty or non-scannable HTML file", res.stdout)

    def test_comment_only_html_file_rejected(self):
        """Negative test: HTML file with only comments must be rejected as non-scannable."""
        html_file = os.path.join(self.temp_dir, 'comments.html')
        with open(html_file, 'w') as f:
            f.write('<!-- Just an HTML comment with no markup -->')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Empty or non-scannable HTML file", res.stdout)

    def test_html5_optional_closing_tags_pass(self):
        """Standard compliance test: Valid HTML5 optional closing tags (li, p, tr, td) must pass."""
        html_file = os.path.join(self.temp_dir, 'valid_lists.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Test</title></head><body><ul><li>Item 1<li>Item 2<li>Item 3</ul></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_unbudgeted_video_element_fails(self):
        """Negative test: <video> element without width/height or aspect-ratio must fail Gate 5."""
        html_file = os.path.join(self.temp_dir, 'video.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Video</title></head><body><video src="hero.mp4"></video></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("<video> tag lacks complete dimensions", res.stdout)

    def test_unbudgeted_iframe_element_fails(self):
        """Negative test: <iframe> element without width/height or aspect-ratio must fail Gate 5."""
        html_file = os.path.join(self.temp_dir, 'iframe.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Frame</title></head><body><iframe src="https://example.com"></iframe></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("<iframe> tag lacks complete dimensions", res.stdout)

    def test_calc_zero_dimension_fails(self):
        """Negative test: media element with non-reserving calc(0px) dimensions must fail Gate 5."""
        html_file = os.path.join(self.temp_dir, 'calc_zero.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Zero</title></head><body><img src="logo.png" style="width: calc(0px); height: calc(0px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_net_zero_dimension_fails(self):
        """Negative test: media element with net-zero calc(100% - 100%) dimensions must fail Gate 5."""
        html_file = os.path.join(self.temp_dir, 'calc_net_zero.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Net Zero</title></head><body><img src="logo.png" style="width: calc(100% - 100%); height: calc(100% - 100%);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_negative_dimension_fails(self):
        """Negative test: media element with negative calc(10px - 20px) dimensions must fail Gate 5."""
        html_file = os.path.join(self.temp_dir, 'calc_negative.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Negative</title></head><body><img src="logo.png" style="width: calc(10px - 20px); height: calc(10px - 20px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_link_stylesheet_href_before_rel_passes(self):
        """Functional test: <link href="style.css" rel="stylesheet"> with href before rel must be correctly parsed."""
        css_file = os.path.join(self.temp_dir, 'style.css')
        with open(css_file, 'w') as f:
            f.write('.banner-img { width: 400px; height: 250px; }')
        html_file = os.path.join(self.temp_dir, 'link_order.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Link Order</title><link href="style.css" rel="stylesheet"></head><body><img class="banner-img" src="banner.png" alt="Banner"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_compound_and_descendant_selectors_pass(self):
        """Functional test: compound (img.hero) and descendant (.gallery img) CSS selectors must be matched."""
        css_file = os.path.join(self.temp_dir, 'selectors.css')
        with open(css_file, 'w') as f:
            f.write('.gallery img { width: 300px; height: 200px; }\nimg.hero { aspect-ratio: 16/9; }')
        html_file = os.path.join(self.temp_dir, 'selectors.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Selectors</title><link rel="stylesheet" href="selectors.css"></head><body><img class="hero" src="hero.png" alt="Hero"><div class="gallery"><img src="thumb.png" alt="Thumb"></div></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_calc_unbalanced_parentheses_fails(self):
        """Negative test: media element with unbalanced calc((10px) dimensions must fail Gate 5."""
        html_file = os.path.join(self.temp_dir, 'calc_unbalanced.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Unbalanced</title></head><body><img src="logo.png" style="width: calc((10px); height: calc((10px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_length_multiplied_by_length_fails(self):
        """Negative test: W3C CSS Values Level 4 (§ 8.1.1) disallows multiplying length by length (calc(10px * 20px))."""
        html_file = os.path.join(self.temp_dir, 'calc_length_mul_length.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Mul Length</title></head><body><img src="logo.png" style="width: calc(10px * 20px); height: calc(10px * 20px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_length_added_to_unitless_number_fails(self):
        """Negative test: W3C CSS Values Level 4 (§ 8.1.1) disallows adding incompatible types (calc(10px + 2))."""
        html_file = os.path.join(self.temp_dir, 'calc_length_add_number.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Add Number</title></head><body><img src="logo.png" style="width: calc(10px + 2); height: calc(10px + 2);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_valid_scalar_multiplication_and_division_passes(self):
        """Positive test: valid W3C scalar operations calc(10px * 2) and calc(100px / 2) must pass Gate 5."""
        html_file = os.path.join(self.temp_dir, 'calc_valid_scalar.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Valid</title></head><body><img src="logo.png" style="width: calc(10px * 2); height: calc(100px / 2);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_calc_missing_whitespace_around_subtraction_fails(self):
        """Negative test: W3C CSS Values Level 4 (§ 8.1.1) requires whitespace around '-' operator (calc(10px-5px))."""
        html_file = os.path.join(self.temp_dir, 'calc_no_space_sub.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc No Space</title></head><body><img src="logo.png" style="width: calc(10px-5px); height: calc(10px-5px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_missing_whitespace_around_addition_fails(self):
        """Negative test: W3C CSS Values Level 4 (§ 8.1.1) requires whitespace around '+' operator (calc(10px+5px))."""
        html_file = os.path.join(self.temp_dir, 'calc_no_space_add.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc No Space</title></head><body><img src="logo.png" style="width: calc(10px+5px); height: calc(10px+5px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_malformed_number_multiple_dots_fails(self):
        """Negative test: CSS number token rejects multiple decimal points (calc(1.2.3px))."""
        html_file = os.path.join(self.temp_dir, 'calc_multi_dot.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Multi Dot</title></head><body><img src="logo.png" style="width: calc(1.2.3px); height: calc(1.2.3px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_whitespace_after_unary_minus_fails(self):
        """Negative test: CSS Syntax Level 3 disallows whitespace between unary sign and number (calc(- 10px + 20px))."""
        html_file = os.path.join(self.temp_dir, 'calc_unary_space.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Unary Space</title></head><body><img src="logo.png" style="width: calc(- 10px + 20px); height: calc(- 10px + 20px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_whitespace_after_unary_minus_in_operand_fails(self):
        """Negative test: CSS Syntax Level 3 disallows whitespace after unary sign in operand (calc(10px + - 5px))."""
        html_file = os.path.join(self.temp_dir, 'calc_unary_operand_space.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Unary Space 2</title></head><body><img src="logo.png" style="width: calc(10px + - 5px); height: calc(10px + - 5px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_calc_unary_minus_without_whitespace_passes(self):
        """Positive test: Valid unary minus directly preceding number passes (calc(-10px + 20px) and calc(10px + -5px))."""
        html_file = os.path.join(self.temp_dir, 'calc_unary_valid.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Unary Valid</title></head><body><img src="logo.png" style="width: calc(-10px + 20px); height: calc(10px + -5px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_calc_scientific_notation_passes(self):
        """Positive test: CSS Syntax Level 3 scientific notation exponents pass (calc(1e2px) and calc(1.5e2px + 50px))."""
        html_file = os.path.join(self.temp_dir, 'calc_scientific.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Scientific</title></head><body><img src="logo.png" style="width: calc(1e2px); height: calc(1.5e2px + 50px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_calc_em_and_ex_units_pass(self):
        """Positive test: W3C font-relative length units em and ex pass in calc expressions (calc(10em + 2px) and calc(10ex + 2px))."""
        html_file = os.path.join(self.temp_dir, 'calc_em_ex.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc EM EX</title></head><body><img src="logo.png" style="width: calc(10em + 2px); height: calc(10ex + 2px);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_calc_mixed_scientific_and_font_relative_units_pass(self):
        """Positive test: calc expressions combining scientific notation and em/ex units pass cleanly."""
        html_file = os.path.join(self.temp_dir, 'calc_mixed.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Calc Mixed</title></head><body><img src="logo.png" style="width: calc(1e2px + 2em); height: calc(1.5e1rem - 5ex);" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_direct_decimal_dimensions_below_one_pass(self):
        """Positive test: W3C valid positive decimal dimensions below 1 (0.5px, .5em, 0.25rem) pass Gate 5."""
        html_file = os.path.join(self.temp_dir, 'direct_decimal.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Decimal Dims</title></head><body><img src="logo.png" style="width: 0.5px; height: 0.5em;" alt="Logo"><img src="icon.png" style="width: .5rem; height: .5ex;" alt="Icon"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_direct_zero_dimension_fails(self):
        """Negative test: Zero direct dimensions (0px, 0.0em) must be rejected as non-reserving."""
        html_file = os.path.join(self.temp_dir, 'direct_zero.html')
        with open(html_file, 'w') as f:
            f.write('<!DOCTYPE html><html><head><title>Zero Dims</title></head><body><img src="logo.png" style="width: 0px; height: 0.0em;" alt="Logo"></body></html>')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("invalid non-reserving CSS dimensions in style", res.stdout)

    def test_css_cascade_specificity_override_fails_cls(self):
        """Negative test: A higher specificity CSS rule with width:0/height:0 overrides an earlier general rule and fails Gate 5."""
        html_file = os.path.join(self.temp_dir, 'cascade_fail.html')
        with open(html_file, 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
<title>Cascade Specificity Fail</title>
<style>
img { width: 100px; height: 100px; }
img.hero { width: 0; height: 0; }
</style>
</head>
<body>
<img src="hero.png" class="hero" alt="Hero">
</body>
</html>''')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_css_cascade_specificity_override_passes_cls(self):
        """Positive test: A higher specificity CSS rule with valid dimensions overrides a lower specificity 0-dimension rule."""
        html_file = os.path.join(self.temp_dir, 'cascade_pass.html')
        with open(html_file, 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
<title>Cascade Specificity Pass</title>
<style>
img { width: 0; height: 0; }
img.hero { width: 200px; height: 150px; }
</style>
</head>
<body>
<img src="hero.png" class="hero" alt="Hero">
</body>
</html>''')
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("PASS", res.stdout)

    def test_css_source_order_override_fails_cls(self):
        """Negative test: At equal specificity, a later CSS rule in source order overrides an earlier rule."""
        html_file = os.path.join(self.temp_dir, 'source_order_fail.html')
        with open(html_file, 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
<title>Source Order Fail</title>
<style>
img { width: 100px; height: 100px; }
img { width: 0; height: 0; }
</style>
</head>
<body>
<img src="logo.png" alt="Logo">
</body>
</html>''')
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_symlink_directory_outside_target_is_not_traversed(self):
        """Negative test: Directory symlinks pointing outside targetDir must not be followed or cause false failures."""
        outside_dir = tempfile.mkdtemp(prefix='outside_cwv_')
        try:
            bad_html = os.path.join(outside_dir, 'bad.html')
            with open(bad_html, 'w') as f:
                f.write('<!DOCTYPE html><html><body><img src="bad.png"></body></html>')
            
            valid_html = os.path.join(self.temp_dir, 'valid.html')
            with open(valid_html, 'w') as f:
                f.write('<!DOCTYPE html><html><body><img src="good.png" width="100" height="100" alt="Good"></body></html>')

            symlink_dir = os.path.join(self.temp_dir, 'outside_link')
            try:
                os.symlink(outside_dir, symlink_dir)
            except (OSError, NotImplementedError):
                return # Skip if platform disallows symlinks

            res = self.run_gate(self.temp_dir)
            self.assertEqual(res.returncode, 0)
            self.assertIn("PASS", res.stdout)
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)


class TestCWVNodeBudget(unittest.TestCase):
    """
    Regression suite for the `cwv.maxDomNodes` budget.

    Historical defect: the config key was read into defaults and documented, but the
    gate only ever measured nesting depth — a flat 5,000-node page passed cleanly.
    """

    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.gate_script = os.path.join(self.root_dir, 'gates', 'gate_cwv_budget.mjs')
        self.temp_dir = tempfile.mkdtemp(prefix='cwv_nodes_')
        if not _parse5_installed(self.root_dir):
            if os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ:
                self.fail("Mandatory DOM gate tests cannot run: parse5 is not installed in CI.")
            self.skipTest("parse5 not installed — run `npm ci` to enable the DOM & CLS budget suite")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_page(self, sibling_count):
        body = '<div class="card"><span>row</span></div>' * sibling_count
        html = (f'<!DOCTYPE html><html><head><title>t</title></head><body>{body}</body></html>')
        with open(os.path.join(self.temp_dir, 'index.html'), 'w') as f:
            f.write(html)

    def run_gate(self):
        return subprocess.run(['node', self.gate_script, self.temp_dir],
                              capture_output=True, text=True)

    def test_flat_dom_exceeding_max_dom_nodes_fails(self):
        """2 nodes per card: 400 cards = 802 elements, over a 500-node budget."""
        self._write_page(400)
        with open(os.path.join(self.temp_dir, 'orthotect.config.json'), 'w') as f:
            f.write('{"cwv": {"maxDomNodes": 500}}')
        res = self.run_gate()
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Excessive DOM size", res.stdout)

    def test_flat_dom_within_budget_passes(self):
        self._write_page(10)
        with open(os.path.join(self.temp_dir, 'orthotect.config.json'), 'w') as f:
            f.write('{"cwv": {"maxDomNodes": 500}}')
        res = self.run_gate()
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_default_node_budget_rejects_very_wide_dom(self):
        """Without config the 1,500-element default must still bind."""
        self._write_page(800)
        res = self.run_gate()
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Excessive DOM size", res.stdout)

    def test_zero_disables_node_budget(self):
        """maxDomNodes: 0 is the documented opt-out and must not reject a wide page."""
        self._write_page(800)
        with open(os.path.join(self.temp_dir, 'orthotect.config.json'), 'w') as f:
            f.write('{"cwv": {"maxDomNodes": 0}}')
        res = self.run_gate()
        self.assertEqual(res.returncode, 0, res.stdout)


class TestMissingParserContract(unittest.TestCase):
    """
    The DOM gate must fail closed at exit 2 when its parser is absent.

    Two defects are pinned here, both found while resolving P0-2:

    1. The remediation message told the user to install `parse5` in the project
       being verified. Node resolves the import relative to the gate file, so that
       advice could never work — a user following it would loop forever.
    2. Calling an exported analysis function without the parser raised
       `TypeError: Cannot read properties of null (reading 'parse')` — a crash
       reported as exit 1, i.e. a tool error masquerading as a code violation.
    """

    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        # Mirror the real layout (gates/ + core/) so relative imports resolve, but
        # deliberately omit node_modules so the parser is unresolvable.
        self.sandbox = tempfile.mkdtemp(prefix='cwv_noparse5_')
        os.makedirs(os.path.join(self.sandbox, 'gates'))
        os.makedirs(os.path.join(self.sandbox, 'core'))
        os.makedirs(os.path.join(self.sandbox, 'target'))
        shutil.copy(os.path.join(self.root_dir, 'gates', 'gate_cwv_budget.mjs'),
                    os.path.join(self.sandbox, 'gates', 'gate_cwv_budget.mjs'))
        for name in ('config.mjs', 'exit_codes.mjs', 'cli_args.mjs'):
            shutil.copy(os.path.join(self.root_dir, 'core', name),
                        os.path.join(self.sandbox, 'core', name))
        with open(os.path.join(self.sandbox, 'target', 'index.html'), 'w') as f:
            f.write('<!DOCTYPE html><html><body><div>x</div></body></html>')

    def tearDown(self):
        shutil.rmtree(self.sandbox, ignore_errors=True)

    def _run(self, *args):
        return subprocess.run(['node', *args], capture_output=True, text=True,
                              cwd=self.sandbox)

    def test_missing_parser_exits_2_not_1(self):
        """A gate that cannot run is a tool error, never a rule violation."""
        res = self._run(os.path.join('gates', 'gate_cwv_budget.mjs'), 'target')
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn('missing required package "parse5"', res.stderr)

    def test_missing_shared_arg_parser_exits_2_not_1(self):
        """
        A missing `core/cli_args.mjs` is a broken installation. Node would report
        an uncaught import error as exit 1, which inverts the contract by claiming
        the audited code violated a rule when in fact nothing was evaluated.
        """
        os.remove(os.path.join(self.sandbox, 'core', 'cli_args.mjs'))
        res = self._run(os.path.join('gates', 'gate_cwv_budget.mjs'), 'target')
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn('cli_args.mjs', res.stderr)
        self.assertNotIn('missing required package', res.stderr,
                         'a missing internal module must not be reported as a missing parser')

    def test_remediation_advice_does_not_send_user_to_the_wrong_directory(self):
        """
        Regression: the old message said to install parse5 "in the project being
        verified", which cannot work because the import resolves from the gate file.
        """
        res = self._run(os.path.join('gates', 'gate_cwv_budget.mjs'), 'target')
        self.assertEqual(res.returncode, 2)
        self.assertIn('will NOT fix this', res.stderr)
        self.assertIn('inside the orthotect package directory', res.stderr)
        self.assertNotIn('Install it in the project being verified', res.stderr)

    def test_missing_parser_surfaces_a_typed_error_to_library_callers(self):
        """
        Exported helpers must throw ParserUnavailableError rather than dereference
        null, so an embedding caller can distinguish "no parser" from "bad HTML".
        """
        script = (
            "import('./gates/gate_cwv_budget.mjs').then(m => {"
            "  try { m.analyzeDomStructure('<div>x</div>'); console.log('NO_ERROR'); }"
            "  catch (e) { console.log('THREW:' + e.name); }"
            "}).catch(e => { console.log('IMPORT_FAILED:' + e.message); });"
        )
        res = self._run('-e', script)
        self.assertIn('THREW:ParserUnavailableError', res.stdout,
                      res.stdout + res.stderr)


if __name__ == '__main__':
    unittest.main()



