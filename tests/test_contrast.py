import unittest
import sys
import os

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

if __name__ == '__main__':
    unittest.main()
