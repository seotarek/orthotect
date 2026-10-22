import unittest
import sys
import os
import subprocess
import tempfile
import shutil

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
        self.assertEqual(res.returncode, 0)
        self.assertIn("BiDi Logical Check Passed", res.stdout)

if __name__ == '__main__':
    unittest.main()
