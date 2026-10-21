import unittest
import subprocess
import tempfile
import os
import shutil

class TestOrthotectE2E(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.temp_dir = tempfile.mkdtemp(prefix='orthotect_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_e2e_init_scaffolds_real_files(self):
        """Verifies that 'orthotect init' creates real tokens, FSM, and AGENTS.md."""
        res = subprocess.run(['node', os.path.join(self.root_dir, 'bin', 'orthotect.js'), 'init', self.temp_dir],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'core', 'tokens', 'primitives.json')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'core', 'tokens', 'semantics.json')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'core', 'fsm', 'button-states.json')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'AGENTS.md')))

    def test_e2e_verify_rejects_empty_directory(self):
        """Negative test: 'orthotect verify' must REJECT an empty directory with code 1."""
        empty_dir = os.path.join(self.temp_dir, 'empty_proj')
        os.makedirs(empty_dir, exist_ok=True)
        res = subprocess.run(['node', os.path.join(self.root_dir, 'bin', 'orthotect.js'), 'verify', empty_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("REJECT", res.stdout)

    def test_e2e_verify_rejects_missing_tokens(self):
        """Negative test: A project with HTML/CSS but missing tokens must fail contrast check."""
        proj_dir = os.path.join(self.temp_dir, 'no_tokens_proj')
        os.makedirs(proj_dir, exist_ok=True)
        with open(os.path.join(proj_dir, 'index.html'), 'w') as f:
            f.write("<!DOCTYPE html><html><head></head><body><h1>Hello</h1></body></html>")
        res = subprocess.run(['python3', os.path.join(self.root_dir, 'gates', 'gate_contrast_wcag.py'), proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required Design Token files", res.stdout)

    def test_e2e_verify_rejects_missing_fsm(self):
        """Negative test: A project missing FSM specifications must fail FSM gate."""
        proj_dir = os.path.join(self.temp_dir, 'no_fsm_proj')
        os.makedirs(proj_dir, exist_ok=True)
        res = subprocess.run(['python3', os.path.join(self.root_dir, 'gates', 'gate_fsm_integrity.py'), proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required FSM specifications", res.stdout)

    def test_e2e_verify_rejects_physical_css(self):
        """Negative test: A project with physical CSS margin-left must fail BiDi gate."""
        proj_dir = os.path.join(self.temp_dir, 'physical_css_proj')
        os.makedirs(proj_dir, exist_ok=True)
        with open(os.path.join(proj_dir, 'style.css'), 'w') as f:
            f.write(".card { margin-left: 16px; }")
        res = subprocess.run(['python3', os.path.join(self.root_dir, 'gates', 'gate_bidi_logical.py'), proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Physical direction properties found", res.stdout)

    def test_e2e_verify_passes_on_golden_showcase(self):
        """Positive test: The verified golden showcase must pass 100% of gates."""
        showcase_dir = os.path.join(self.root_dir, 'examples', 'golden-showcase')
        res = subprocess.run(['node', os.path.join(self.root_dir, 'bin', 'orthotect.js'), 'verify', showcase_dir],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("ALL GATES PASSED", res.stdout)

if __name__ == '__main__':
    unittest.main()
