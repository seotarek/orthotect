import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gates')))
from gate_bidi_logical import scan_file

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
        self.assertEqual(len(viols), 4)

if __name__ == '__main__':
    unittest.main()
