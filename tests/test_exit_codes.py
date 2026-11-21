"""
Regression tests for the Orthotect Exit-Code Contract.

The contract exists because a verification tool that reports the same code for
"your code is bad" and "the tool could not run" cannot be trusted in CI: a broken
install, a missing dependency or an unreadable config file all look like a code
regression, and a transient environment failure can block a release forever with
no way to tell the difference.

  0  PASS       every enforced rule was evaluated and satisfied
  1  VIOLATION  a gate evaluated the code and found a breach
  2  TOOL ERROR the gate could not evaluate the code

These tests pin the boundary from both sides: a genuine breach must never report
2, and an environment failure must never report 1.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GATES_DIR = os.path.join(ROOT_DIR, 'gates')
CORE_DIR = os.path.join(ROOT_DIR, 'core')


def read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


class TestExitCodeConstants(unittest.TestCase):
    """The three codes must be defined once per language and agree across them."""

    def test_python_constants(self):
        sys.path.insert(0, ROOT_DIR)
        from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
        self.assertEqual((EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR), (0, 1, 2))

    def test_js_mirror_matches_python(self):
        """
        core/exit_codes.mjs is a hand-maintained mirror of core/exit_codes.py.
        If they drift, the Node CLI and the Python gates disagree about what a
        given exit code means, which is exactly the ambiguity the contract removes.
        """
        py = read(os.path.join(CORE_DIR, 'exit_codes.py'))
        js = read(os.path.join(CORE_DIR, 'exit_codes.mjs'))
        for name, expected in (('EXIT_PASS', 0), ('EXIT_VIOLATION', 1), ('EXIT_TOOL_ERROR', 2)):
            self.assertRegex(py, rf'(?m)^{name}\s*=\s*{expected}\s*$', f'{name} missing from exit_codes.py')
            self.assertRegex(js, rf'export const {name}\s*=\s*{expected};', f'{name} missing from exit_codes.mjs')

    def test_no_gate_uses_a_bare_exit_literal(self):
        """
        Guards the whole contract at once. A new `sys.exit(1)` in a gate silently
        reintroduces the ambiguity, so fail loudly here instead of in a CI postmortem.
        """
        offenders = []
        for name in sorted(os.listdir(GATES_DIR)):
            if not name.endswith('.py'):
                continue
            if name == 'gate_visual_qa.py':  # browser gate, no exit-code surface
                continue
            body = read(os.path.join(GATES_DIR, name))
            for match in re.finditer(r'sys\.exit\(\s*(\d+)\s*\)', body):
                line = body.count('\n', 0, match.start()) + 1
                offenders.append(f'gates/{name}:{line} -> sys.exit({match.group(1)})')
        self.assertEqual(offenders, [], 'Bare numeric exit codes bypass the contract:\n  ' + '\n  '.join(offenders))


class TestGateExitCodes(unittest.TestCase):
    """Every gate must emit 1 for a real breach and 2 when it cannot evaluate anything."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='exitcode_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_gate(self, script, *args):
        return subprocess.run(
            ['python3', os.path.join(GATES_DIR, script), *args],
            capture_output=True, text=True, cwd=ROOT_DIR
        )

    def write(self, relpath, content):
        full = os.path.join(self.temp_dir, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(content)
        return full

    # ---- TOOL ERROR (2): the environment must change -------------------------

    def test_missing_target_is_tool_error_not_violation(self):
        """
        A path typo previously looked identical to a failing audit. Nothing was
        read, so nothing can be claimed about the code.
        """
        missing = os.path.join(self.temp_dir, 'does-not-exist')
        for script in ('gate_no_slop.py', 'gate_bidi_logical.py',
                       'gate_contrast_wcag.py', 'gate_fsm_integrity.py',
                       'gate_security_audit.py'):
            with self.subTest(gate=script):
                res = self.run_gate(script, missing)
                self.assertEqual(res.returncode, 2, f'{script} -> {res.returncode}\n{res.stdout}{res.stderr}')

    def test_missing_design_tokens_is_tool_error(self):
        """
        No token architecture means the contrast gate evaluated zero pairs; reporting
        that as a violation would send the reviewer to the wrong file.
        """
        empty = os.path.join(self.temp_dir, 'empty')
        os.makedirs(empty, exist_ok=True)
        res = self.run_gate('gate_contrast_wcag.py', empty)
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertIn('Missing required Design Token files', res.stdout)

    def test_missing_fsm_specs_is_tool_error(self):
        empty = os.path.join(self.temp_dir, 'empty')
        os.makedirs(empty, exist_ok=True)
        res = self.run_gate('gate_fsm_integrity.py', empty)
        self.assertEqual(res.returncode, 2, res.stdout)

    def test_malformed_token_json_is_tool_error(self):
        """Unparsable configuration is a tooling defect, not a WCAG failure."""
        self.write('core/tokens/primitives.json', '{ not json')
        self.write('core/tokens/semantics.json', '{}')
        res = self.run_gate('gate_contrast_wcag.py', self.temp_dir)
        self.assertEqual(res.returncode, 2, res.stdout)

    def test_unscannable_directory_is_tool_error(self):
        """Zero files in scope means zero rules ran; that is not a pass and not a violation."""
        empty = os.path.join(self.temp_dir, 'empty')
        os.makedirs(empty, exist_ok=True)
        res = self.run_gate('gate_no_slop.py', empty)
        self.assertEqual(res.returncode, 2, res.stdout)

    # ---- VIOLATION (1): the audited code must change -------------------------

    def test_slop_breach_is_violation(self):
        self.write('src/index.html', '<div style="color:#123456">x</div>\n')
        res = self.run_gate('gate_no_slop.py', os.path.join(self.temp_dir, 'src'))
        self.assertEqual(res.returncode, 1, res.stdout)

    def test_bidi_breach_is_violation(self):
        self.write('src/app.css', '.a { margin-left: 8px; }\n')
        res = self.run_gate('gate_bidi_logical.py', os.path.join(self.temp_dir, 'src'))
        self.assertEqual(res.returncode, 1, res.stdout)

    def test_fsm_breach_is_violation(self):
        """A syntactically valid but unsound state machine is a code defect, not a tool error."""
        self.write('core/fsm/checkout.json', json.dumps({
            'initialState': 'idle',
            'states': {
                'idle': {'on': {'start': 'loading'}},
                'loading': {'isAsync': True, 'allowClick': False, 'on': {'ok': 'idle'}},
                'orphan': {'on': {'back': 'idle'}},
            },
        }))
        res = self.run_gate('gate_fsm_integrity.py', self.temp_dir)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn('Unreachable', res.stdout)


class TestAggregation(unittest.TestCase):
    """The orchestrator must not let a violation mask a tool error, or vice versa."""

    def setUp(self):
        sys.path.insert(0, ROOT_DIR)
        from gates.run_all_gates import aggregate_exit_codes, classify_gate_result
        self.aggregate = aggregate_exit_codes
        self.classify = classify_gate_result

    def test_pass_wins_only_when_everything_passes(self):
        self.assertEqual(self.aggregate([0, 0, 0, 0, 0, 0]), 0)

    def test_violation_beats_pass(self):
        self.assertEqual(self.aggregate([0, 1, 0]), 1)

    def test_tool_error_beats_violation(self):
        """
        Exit 2 must dominate. If a gate could not run, the remaining results are
        incomplete, so CI must page the environment owner rather than the author.
        """
        self.assertEqual(self.aggregate([1, 2, 0]), 2)
        self.assertEqual(self.aggregate([2, 1, 1]), 2)

    def test_unexpected_status_is_a_tool_error(self):
        """
        A gate that crashed (traceback -> 1, SIGKILL -> -9, spawn failure -> None)
        must not be reported as a rule violation.
        """
        for status in (3, 127, -9, None):
            with self.subTest(status=status):
                self.assertEqual(self.classify('x', status), 2)

    def test_known_statuses_pass_through(self):
        self.assertEqual(self.classify('x', 0), 0)
        self.assertEqual(self.classify('x', 1), 1)
        self.assertEqual(self.classify('x', 2), 2)


class TestOrchestratorEndToEnd(unittest.TestCase):
    """Verifies the contract through the real subprocess boundary."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='exitcode_e2e_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_orchestrator(self, *args):
        return subprocess.run(
            ['python3', os.path.join(GATES_DIR, 'run_all_gates.py'), *args],
            capture_output=True, text=True, cwd=ROOT_DIR
        )

    def test_missing_target_reports_exit_2(self):
        res = self.run_orchestrator(os.path.join(self.temp_dir, 'nope'))
        self.assertEqual(res.returncode, 2, res.stdout)

    def test_missing_target_json_reports_exit_2(self):
        """
        Machine consumers read `exitCode` from the JSON payload. It must agree with
        the process status, or a CI step that parses stdout disagrees with its shell.
        """
        res = self.run_orchestrator(os.path.join(self.temp_dir, 'nope'), '--json')
        self.assertEqual(res.returncode, 2)
        payload = json.loads(res.stdout)
        self.assertEqual(payload['exitCode'], 2)
        self.assertFalse(payload['allPassed'])

    def test_violation_only_target_reports_exit_1(self):
        """
        A tree with a real breach and no missing tooling must report 1 only.

        The fixture therefore has to be a *complete* project: the contrast and FSM
        gates fail closed at exit 2 when their required token and state files are
        absent, which would (correctly) dominate the violation. Scaffolding them here
        keeps this test measuring the aggregation rule rather than the environment.
        """
        src = os.path.join(self.temp_dir, 'src')
        os.makedirs(src)
        with open(os.path.join(src, 'index.html'), 'w', encoding='utf-8') as f:
            f.write('<div style="color:#123456">x</div>\n')

        # Minimal but valid token architecture so the contrast gate can run.
        tokens_dir = os.path.join(self.temp_dir, 'core', 'tokens')
        os.makedirs(tokens_dir)
        with open(os.path.join(tokens_dir, 'primitives.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'color': {
                    'neutral': {
                        '0': {'$value': '#ffffff', '$type': 'color'},
                        '900': {'$value': '#0f172a', '$type': 'color'},
                    }
                }
            }, f)
        with open(os.path.join(tokens_dir, 'semantics.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'theme': {
                    'light': {
                        'surface': {'canvas': {'$value': '{color.neutral.0}', '$type': 'color'}},
                        'text': {'primary': {'$value': '{color.neutral.900}', '$type': 'color'}},
                    }
                }
            }, f)

        # Minimal sound FSM so the state-machine gate can run.
        fsm_dir = os.path.join(self.temp_dir, 'core', 'fsm')
        os.makedirs(fsm_dir)
        with open(os.path.join(fsm_dir, 'button.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'name': 'FixtureButton',
                'initialState': 'idle',
                'states': {
                    'idle': {'on': {'CLICK': 'loading'}},
                    'loading': {'isAsync': True, 'allowClick': False, 'on': {'RESOLVE_SUCCESS': 'idle'}},
                },
            }, f)

        probe = subprocess.run(
            ['node', os.path.join(GATES_DIR, 'gate_cwv_budget.mjs'), src],
            capture_output=True, text=True, cwd=ROOT_DIR
        )
        if probe.returncode == 2:
            self.skipTest('parse5 unavailable: the DOM gate legitimately reports 2, which is the correct behaviour')

        # The token and FSM gates resolve their requirements relative to the audit
        # root, so the root (not src/) is what must be verified.
        res = self.run_orchestrator(self.temp_dir)
        self.assertEqual(res.returncode, 1, res.stdout[-3000:])


class TestCLIPropagation(unittest.TestCase):
    """bin/orthotect.js must forward a child's exit code verbatim."""

    def setUp(self):
        self.cli = os.path.join(ROOT_DIR, 'bin', 'orthotect.js')
        self.temp_dir = tempfile.mkdtemp(prefix='exitcode_cli_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_cli(self, *args):
        return subprocess.run(
            ['node', self.cli, *args],
            capture_output=True, text=True, cwd=ROOT_DIR
        )

    def test_cli_missing_target_is_exit_2(self):
        """
        Previously the CLI collapsed every non-zero status into 1 via
        `process.exit(result.status || 1)`, erasing the distinction it took
        a whole contract to establish.
        """
        res = self.run_cli('verify', os.path.join(self.temp_dir, 'nope'))
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)

    def test_cli_security_missing_target_is_exit_2(self):
        res = self.run_cli('security', os.path.join(self.temp_dir, 'nope'))
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)

    def test_cli_does_not_coerce_child_status(self):
        """Source guard: no exit path may invent 1 for an unknown problem."""
        body = read(self.cli)
        self.assertNotIn('process.exit(result.status || 1)', body)
        self.assertNotIn('process.exit(proc.status || 1)', body)


if __name__ == '__main__':
    unittest.main()
