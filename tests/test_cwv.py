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

if __name__ == '__main__':
    unittest.main()


