import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SELF_AUDIT = os.path.join(ROOT_DIR, 'scripts', 'self-audit.mjs')


class TestSelfAuditGate(unittest.TestCase):
    """
    P0-3: Orthotect must audit itself.

    Every critical defect in REVIEW_2026-11.md was found because a gate was
    checking other people's code while the same rule was violated in this
    repository. `npm run audit:self` closes that gap; these tests pin its
    contract so it cannot silently rot into a no-op.
    """

    def _run(self, *args, cwd=None):
        return subprocess.run(['node', SELF_AUDIT, *args],
                              capture_output=True, text=True, cwd=cwd or ROOT_DIR)

    def test_self_audit_script_exists_and_is_wired_into_package_json(self):
        self.assertTrue(os.path.isfile(SELF_AUDIT), 'scripts/self-audit.mjs is missing')
        with open(os.path.join(ROOT_DIR, 'package.json'), encoding='utf-8') as f:
            pkg = json.load(f)
        self.assertIn('audit:self', pkg.get('scripts', {}),
                      '`npm run audit:self` must be a declared script')

    def test_clean_tree_passes_and_exits_zero(self):
        """
        The repository at HEAD must satisfy its own six gates.

        This is the assertion that makes the self-audit meaningful: if a future
        change introduces an inline hex color or a physical CSS property into
        gates/ or core/, this test fails rather than the defect shipping.
        """
        res = self._run()
        self.assertEqual(res.returncode, 0, res.stdout[-4000:] + res.stderr[-2000:])
        self.assertIn('Self-audit passed', res.stdout)

    def test_missing_parser_is_reported_as_tool_error_not_a_finding(self):
        """
        An absent parse5 means no gate ran — that is exit 2 with an actionable
        message, never exit 1 (which would read as "Orthotect's code is bad").
        """
        sandbox = tempfile.mkdtemp(prefix='selfaudit_nodeps_')
        try:
            shutil.copytree(os.path.join(ROOT_DIR, 'scripts'), os.path.join(sandbox, 'scripts'))
            os.makedirs(os.path.join(sandbox, 'gates'))
            shutil.copy(os.path.join(ROOT_DIR, 'gates', 'run_all_gates.py'),
                        os.path.join(sandbox, 'gates', 'run_all_gates.py'))
            # Deliberately no node_modules/ → parse5 unresolvable.
            res = subprocess.run(['node', os.path.join(sandbox, 'scripts', 'self-audit.mjs')],
                                 capture_output=True, text=True, cwd=sandbox)
            self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
            self.assertIn('parse5', res.stderr)
            self.assertIn('npm ci', res.stderr)
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)

    def test_missing_orchestrator_is_reported_as_tool_error(self):
        """A broken checkout must not be reported as a passing audit."""
        sandbox = tempfile.mkdtemp(prefix='selfaudit_noorch_')
        try:
            shutil.copytree(os.path.join(ROOT_DIR, 'scripts'), os.path.join(sandbox, 'scripts'))
            # node_modules present (so the parse5 check passes) but no gates/ dir.
            os.makedirs(os.path.join(sandbox, 'node_modules', 'parse5'))
            res = subprocess.run(['node', os.path.join(sandbox, 'scripts', 'self-audit.mjs')],
                                 capture_output=True, text=True, cwd=sandbox)
            self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
            self.assertIn('orchestrator not found', res.stderr)
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)


class TestSelfAuditIsReferencedByCI(unittest.TestCase):
    """The self-audit only has value if CI enforces it."""

    def test_ci_workflow_runs_the_self_audit(self):
        ci = os.path.join(ROOT_DIR, '.github', 'workflows', 'ci.yml')
        self.assertTrue(os.path.isfile(ci), 'CI workflow is missing')
        with open(ci, encoding='utf-8') as f:
            content = f.read()
        self.assertIn('audit:self', content,
                      'CI must run `npm run audit:self` so self-violations cannot merge')


if __name__ == '__main__':
    unittest.main()
