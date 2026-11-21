import unittest
import subprocess
import tempfile
import os
import shutil

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _require_parse5(test_case):
    """
    Full `verify` runs include the DOM & Layout-Shift gate, which parses through
    parse5. Without `npm ci` the dependency is absent, so these tests cannot make a
    real assertion; failing closed in CI keeps missing coverage visible.
    """
    if os.path.isdir(os.path.join(ROOT_DIR, 'node_modules', 'parse5')):
        return
    if os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ:
        test_case.fail("parse5 missing in CI: `npm ci` must run before the test step.")
    test_case.skipTest("parse5 not installed — run `npm ci` to enable end-to-end gate verification")


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
        _require_parse5(self)
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
        _require_parse5(self)
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
        _require_parse5(self)
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
        _require_parse5(self)
        showcase_dir = os.path.join(self.root_dir, 'examples', 'golden-showcase')
        res = subprocess.run(['node', self.cli_path, 'verify', showcase_dir],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("ALL GATES PASSED", res.stdout)

    def test_e2e_verify_json_format(self):
        """Positive test: 'orthotect verify --json' produces valid JSON scorecard."""
        _require_parse5(self)
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
        _require_parse5(self)
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


class TestCLIArgumentResolution(unittest.TestCase):
    """
    Regression suite for positional argument parsing.

    Historical defect: flags were stripped with a naive filter, so
    `orthotect security --json ./src` resolved the target to the literal token
    "json" (or to the repo cwd) instead of ./src — the CLI audited the wrong tree
    while still exiting 0. Flags may now appear before, after, or between positionals.
    """

    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.cli_path = os.path.join(self.root_dir, 'bin', 'orthotect.js')
        self.temp_dir = tempfile.mkdtemp(prefix='orthotect_args_')
        self.project = os.path.join(self.temp_dir, 'my-app')
        os.makedirs(self.project, exist_ok=True)
        with open(os.path.join(self.project, 'app.js'), 'w') as f:
            f.write("const el = document.getElementById('out');\nel.textContent = 'ok';\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _security_target(self, argv):
        import json
        res = subprocess.run(['node', self.cli_path, *argv],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        data = json.loads(res.stdout)
        return os.path.realpath(data['target'])

    def test_flag_before_path_resolves_same_target(self):
        """`security --json <dir>` must audit <dir>, not the literal token 'json'."""
        expected = os.path.realpath(self.project)
        self.assertEqual(self._security_target(['security', '--json', self.project]), expected)

    def test_flag_after_path_resolves_same_target(self):
        expected = os.path.realpath(self.project)
        self.assertEqual(self._security_target(['security', self.project, '--json']), expected)

    def test_format_json_value_is_not_treated_as_path(self):
        """`--format json` consumes 'json' as a value, never as the target."""
        expected = os.path.realpath(self.project)
        self.assertEqual(
            self._security_target(['security', '--format', 'json', self.project]), expected)

    def test_equals_form_flag_resolves_same_target(self):
        expected = os.path.realpath(self.project)
        self.assertEqual(
            self._security_target(['security', '--format=json', self.project]), expected)

    def test_verify_flag_before_path_resolves_same_target(self):
        """The same parser feeds `verify`, which must pass the real path to the orchestrator."""
        import json
        res = subprocess.run(['node', self.cli_path, 'verify', '--json', self.project],
                             capture_output=True, text=True)
        data = json.loads(res.stdout)
        self.assertEqual(os.path.realpath(data['target']), os.path.realpath(self.project))


class TestGateStandaloneFlagParsing(unittest.TestCase):
    """
    Each gate is also runnable on its own (documented via `npm run gate:*`).
    A flag placed before the target must not become the audited path.
    """

    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.showcase = os.path.join(self.root_dir, 'examples', 'golden-showcase')

    def test_contrast_gate_accepts_leading_flag(self):
        res = subprocess.run(['python3', os.path.join(self.root_dir, 'gates', 'gate_contrast_wcag.py'),
                              '--json', self.showcase], capture_output=True, text=True)
        self.assertNotIn("target: --json", res.stdout)
        self.assertEqual(res.returncode, 0, res.stdout[-400:])

    def test_fsm_gate_accepts_leading_flag(self):
        res = subprocess.run(['python3', os.path.join(self.root_dir, 'gates', 'gate_fsm_integrity.py'),
                              '--md', self.showcase], capture_output=True, text=True)
        self.assertNotIn("target: --md", res.stdout)
        self.assertEqual(res.returncode, 0, res.stdout[-400:])

    def test_slop_gate_accepts_leading_flag(self):
        res = subprocess.run(['python3', os.path.join(self.root_dir, 'gates', 'gate_no_slop.py'),
                              '--quiet', self.showcase], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout[-400:])

    def test_cwv_gate_accepts_leading_flag(self):
        if not os.path.isdir(os.path.join(self.root_dir, 'node_modules', 'parse5')):
            if os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ:
                self.fail("parse5 missing in CI.")
            self.skipTest("parse5 not installed — run `npm ci`")
        res = subprocess.run(['node', os.path.join(self.root_dir, 'gates', 'gate_cwv_budget.mjs'),
                              '--json', self.showcase], capture_output=True, text=True)
        self.assertNotIn("Target path not found: --json", res.stdout + res.stderr)
        self.assertEqual(res.returncode, 0, (res.stdout + res.stderr)[-400:])


if __name__ == '__main__':
    unittest.main()
