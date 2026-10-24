import unittest
import subprocess
import tempfile
import os
import shutil

class TestOrthotectE2E(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.cli_path = os.path.join(self.root_dir, 'bin', 'orthotect.js')
        self.temp_dir = tempfile.mkdtemp(prefix='orthotect_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_e2e_init_scaffolds_real_files(self):
        """Verifies that 'orthotect init' creates real tokens, FSM, and AGENTS.md."""
        res = subprocess.run(['node', self.cli_path, 'init', self.temp_dir],
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
        res = subprocess.run(['node', self.cli_path, 'verify', empty_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("REJECT", res.stdout)

    def test_e2e_verify_rejects_examples_backup_directory(self):
        """Negative test: 'examples-backup' without tokens/FSM must FAIL via CLI verify (no path confusion)."""
        backup_dir = os.path.join(self.temp_dir, 'examples-backup')
        os.makedirs(backup_dir, exist_ok=True)
        with open(os.path.join(backup_dir, 'index.html'), 'w') as f:
            f.write("<!DOCTYPE html><html><head><title>Backup</title></head><body><h1>Backup</h1></body></html>")
        res = subprocess.run(['node', self.cli_path, 'verify', backup_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("REJECT", res.stdout)

    def test_e2e_verify_rejects_sibling_backup_dir_with_tokens_but_missing_fsm(self):
        """Negative test: 'examples-backup' with tokens present but FSM missing must FAIL (no silent fallback)."""
        backup_dir = os.path.join(self.temp_dir, 'examples-backup-tokens')
        # Scaffold tokens into the backup directory
        subprocess.run(['node', self.cli_path, 'init', backup_dir], capture_output=True)
        # Remove FSM models to isolate FSM gate check on sibling directory
        shutil.rmtree(os.path.join(backup_dir, 'core', 'fsm'))
        with open(os.path.join(backup_dir, 'index.html'), 'w') as f:
            f.write("<!DOCTYPE html><html><head><title>Backup</title></head><body><h1>Backup</h1></body></html>")
        res = subprocess.run(['node', self.cli_path, 'verify', backup_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required FSM specifications in target", res.stdout)

    def test_e2e_verify_rejects_missing_tokens(self):
        """Negative test: CLI verify must reject project missing tokens."""
        proj_dir = os.path.join(self.temp_dir, 'no_tokens_proj')
        os.makedirs(proj_dir, exist_ok=True)
        with open(os.path.join(proj_dir, 'index.html'), 'w') as f:
            f.write("<!DOCTYPE html><html><head></head><body><h1>Hello</h1></body></html>")
        res = subprocess.run(['node', self.cli_path, 'verify', proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("REJECT", res.stdout)

    def test_e2e_verify_rejects_missing_fsm(self):
        """Negative test: CLI verify must reject project missing FSM specifications."""
        proj_dir = os.path.join(self.temp_dir, 'no_fsm_proj')
        subprocess.run(['node', self.cli_path, 'init', proj_dir], capture_output=True)
        shutil.rmtree(os.path.join(proj_dir, 'core', 'fsm'))
        with open(os.path.join(proj_dir, 'index.html'), 'w') as f:
            f.write("<!DOCTYPE html><html><head></head><body><h1>Hello</h1></body></html>")
        res = subprocess.run(['node', self.cli_path, 'verify', proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("REJECT", res.stdout)

    def test_e2e_verify_rejects_physical_css(self):
        """Negative test: CLI verify must reject project with physical CSS margin-left."""
        proj_dir = os.path.join(self.temp_dir, 'bad_css_proj')
        subprocess.run(['node', self.cli_path, 'init', proj_dir], capture_output=True)
        with open(os.path.join(proj_dir, 'index.html'), 'w') as f:
            f.write("<!DOCTYPE html><html><head></head><body><div class=\"card\">Hello</div></body></html>")
        with open(os.path.join(proj_dir, 'style.css'), 'w') as f:
            f.write(".card { margin-left: 16px; }")
        res = subprocess.run(['node', self.cli_path, 'verify', proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Physical direction properties found", res.stdout)

    def test_e2e_verify_rejects_image_without_both_dimensions(self):
        """Negative test: <img> with only width (no height, no aspect-ratio) must be rejected."""
        proj_dir = os.path.join(self.temp_dir, 'bad_img_proj')
        subprocess.run(['node', self.cli_path, 'init', proj_dir], capture_output=True)
        with open(os.path.join(proj_dir, 'index.html'), 'w') as f:
            f.write('''<!DOCTYPE html><html><head></head><body><img src="foo.png" width="300"></body></html>''')
        res = subprocess.run(['node', self.cli_path, 'verify', proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_e2e_verify_rejects_aspect_ratio_in_class_name(self):
        """Negative test: <img> with class='aspect-ratio-box' but without explicit style or width+height must be rejected."""
        proj_dir = os.path.join(self.temp_dir, 'bad_class_img_proj')
        subprocess.run(['node', self.cli_path, 'init', proj_dir], capture_output=True)
        with open(os.path.join(proj_dir, 'index.html'), 'w') as f:
            f.write('''<!DOCTYPE html><html><head></head><body><img src="foo.png" class="aspect-ratio-card"></body></html>''')
        res = subprocess.run(['node', self.cli_path, 'verify', proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("lacks complete dimensions", res.stdout)

    def test_e2e_verify_detects_deep_minified_html(self):
        """Negative test: Minified single-line HTML with >32 levels of nesting must be rejected."""
        proj_dir = os.path.join(self.temp_dir, 'deep_html_proj')
        subprocess.run(['node', self.cli_path, 'init', proj_dir], capture_output=True)
        # Create single line with 35 nested divs
        opens = "<div>" * 35
        closes = "</div>" * 35
        minified = f"<!DOCTYPE html><html><head></head><body>{opens}Deep{closes}</body></html>"
        with open(os.path.join(proj_dir, 'index.html'), 'w') as f:
            f.write(minified)
        res = subprocess.run(['node', self.cli_path, 'verify', proj_dir],
                             capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Excessive DOM depth", res.stdout)

    def test_e2e_verify_passes_on_golden_showcase(self):
        """Positive test: The verified golden showcase must pass 100% of gates."""
        showcase_dir = os.path.join(self.root_dir, 'examples', 'golden-showcase')
        res = subprocess.run(['node', self.cli_path, 'verify', showcase_dir],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("ALL GATES PASSED", res.stdout)

    def test_e2e_verify_json_format(self):
        """Positive test: 'orthotect verify --json' produces valid JSON scorecard."""
        showcase_dir = os.path.join(self.root_dir, 'examples', 'golden-showcase')
        res = subprocess.run(['node', self.cli_path, 'verify', showcase_dir, '--json'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        import json
        # Extract JSON from output
        json_start = res.stdout.find('{')
        self.assertNotEqual(json_start, -1)
        data = json.loads(res.stdout[json_start:])
        self.assertTrue(data['allPassed'])
        self.assertEqual(len(data['gates']), 6)

    def test_e2e_verify_markdown_format(self):
        """Positive test: 'orthotect verify --md' produces clean Markdown report."""
        showcase_dir = os.path.join(self.root_dir, 'examples', 'golden-showcase')
        res = subprocess.run(['node', self.cli_path, 'verify', showcase_dir, '--md'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("### 🏛️ Orthotect Quality Gates Report", res.stdout)
        self.assertIn("| Gate Name | Status | Duration |", res.stdout)

    def test_e2e_compile_command(self):
        """Positive test: 'orthotect compile' compiles DTCG tokens into CSS variables."""
        out_css = os.path.join(self.temp_dir, 'cli_tokens.css')
        tokens_dir = os.path.join(self.root_dir, 'core', 'tokens')
        res = subprocess.run(['node', self.cli_path, 'compile', tokens_dir, '--out', out_css],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(out_css))

if __name__ == '__main__':
    unittest.main()
