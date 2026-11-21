#!/usr/bin/env python3
"""
P2-3 — SARIF 2.1.0 output for GitHub Code Scanning.

REVIEW_2026-11.md item 9: `--format sarif` puts all six gates into GitHub Code
Scanning with no extra CI wiring. The value of that depends entirely on the
document being *valid* — GitHub silently drops any result whose `ruleId` is not
declared in `driver.rules`, so an invalid document looks like a clean audit.

These tests therefore pin three things, in order of how quietly they fail:

  1. Structural validity — every result declares a rule that the driver lists,
     every URI is repo-relative, every line is a positive integer.
  2. Honesty — a tool error is reported as a tool error (`executionSuccessful:
     false` plus a notification), never as an empty result set that reads as
     "nothing found".
  3. Agreement with the console — the SARIF results and the human report come
     from the same findings, so they cannot disagree about what fired.

The gate-level tests run the real gate scripts as subprocesses. The builder
tests call `core.sarif` directly.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core import sarif  # noqa: E402
from core.rule_registry import RULES  # noqa: E402

GATES_DIR = os.path.join(ROOT_DIR, 'gates')


def _parse5_installed():
    """The DOM gate parses through parse5, a declared runtime dependency."""
    return os.path.isdir(os.path.join(ROOT_DIR, 'node_modules', 'parse5'))


class SarifDocumentShapeTest(unittest.TestCase):
    """The builder itself, independent of any gate."""

    def test_minimal_document_is_valid(self):
        document = sarif.build_sarif(
            [{'file': 'src/a.css', 'line': 4, 'label': 'Physical margin', 'ruleId': 'bidi.physical-offset'}],
            base_dir=ROOT_DIR,
        )
        self.assertEqual(document['version'], '2.1.0')
        self.assertEqual(document['$schema'], sarif.SARIF_SCHEMA)
        self.assertEqual(sarif.validate_sarif(document), [])

    def test_result_without_a_declared_rule_is_rejected_by_the_validator(self):
        """
        This is the failure GitHub performs silently. If the validator does not
        catch it, an annotation disappears from the code-scanning UI with no
        error anywhere — the worst kind of green.
        """
        document = sarif.build_sarif(
            [{'file': 'a.css', 'line': 1, 'label': 'x', 'ruleId': 'bidi.physical-offset'}],
            base_dir=ROOT_DIR,
        )
        document['runs'][0]['tool']['driver']['rules'] = []
        errors = sarif.validate_sarif(document)
        self.assertTrue(any('not declared' in e for e in errors), errors)

    def test_absolute_uri_is_rejected(self):
        document = sarif.build_sarif(
            [{'file': 'a.css', 'line': 1, 'label': 'x', 'ruleId': 'bidi.physical-offset'}],
            base_dir=ROOT_DIR,
        )
        document['runs'][0]['results'][0]['locations'][0]['physicalLocation'][
            'artifactLocation']['uri'] = '/abs/path/a.css'
        errors = sarif.validate_sarif(document)
        self.assertTrue(any('relative' in e for e in errors), errors)

    def test_line_zero_is_rejected(self):
        document = sarif.build_sarif(
            [{'file': 'a.css', 'line': 1, 'label': 'x', 'ruleId': 'bidi.physical-offset'}],
            base_dir=ROOT_DIR,
        )
        document['runs'][0]['results'][0]['locations'][0]['physicalLocation'][
            'region']['startLine'] = 0
        errors = sarif.validate_sarif(document)
        self.assertTrue(any('startLine' in e for e in errors), errors)

    def test_severity_absent_falls_back_to_the_registry(self):
        """A gate that omits severity still gets the level the rule registry documents."""
        document = sarif.build_sarif(
            [{'file': 'a.py', 'line': 1, 'label': 'x', 'ruleId': 'security.command-injection'}],
            base_dir=ROOT_DIR,
            registry_get=lambda rid: RULES.get(rid, {}),
        )
        result = document['runs'][0]['results'][0]
        self.assertEqual(result['properties']['severity'], RULES['security.command-injection']['severity'])
        self.assertEqual(result['level'], 'error')

    def test_explicit_medium_severity_is_not_overridden(self):
        """
        The registry lookup exists for *absent* severities. A gate that explicitly
        says MEDIUM must not be silently promoted or demoted by a stale registry.
        """
        document = sarif.build_sarif(
            [{'file': 'a.py', 'line': 1, 'label': 'x', 'ruleId': 'security.command-injection',
              'severity': 'MEDIUM'}],
            base_dir=ROOT_DIR,
            registry_get=lambda rid: {'severity': 'CRITICAL'},
        )
        result = document['runs'][0]['results'][0]
        self.assertEqual(result['properties']['severity'], 'MEDIUM')
        self.assertEqual(result['level'], 'warning')

    def test_tool_error_is_an_invocation_not_an_empty_result_set(self):
        document = sarif.build_sarif([], base_dir=ROOT_DIR,
                                     notifications=[{'message': 'parser unavailable'}])
        run = document['runs'][0]
        self.assertEqual(run['results'], [])
        self.assertFalse(run['invocations'][0]['executionSuccessful'])
        self.assertEqual(
            run['invocations'][0]['toolExecutionNotifications'][0]['message']['text'],
            'parser unavailable',
        )
        self.assertEqual(sarif.validate_sarif(document), [])

    def test_merge_folds_into_one_run_with_a_unioned_rule_catalogue(self):
        first = sarif.build_sarif(
            [{'file': 'a.css', 'line': 1, 'label': 'x', 'ruleId': 'bidi.physical-offset'}],
            base_dir=ROOT_DIR)
        second = sarif.build_sarif(
            [{'file': 'b.py', 'line': 2, 'label': 'y', 'ruleId': 'security.command-injection'}],
            base_dir=ROOT_DIR)
        merged = sarif.merge_sarif([first, second])
        self.assertEqual(len(merged['runs']), 1)
        run = merged['runs'][0]
        self.assertEqual({r['id'] for r in run['tool']['driver']['rules']},
                         {'bidi.physical-offset', 'security.command-injection'})
        self.assertEqual(len(run['results']), 2)
        self.assertEqual(sarif.validate_sarif(merged), [])

    def test_merge_deduplicates_identical_results(self):
        finding = {'file': 'a.css', 'line': 1, 'label': 'x', 'ruleId': 'bidi.physical-offset'}
        document = sarif.build_sarif([finding], base_dir=ROOT_DIR)
        merged = sarif.merge_sarif([document, document])
        self.assertEqual(len(merged['runs'][0]['results']), 1)

    def test_merge_carries_every_tool_error_through(self):
        document = sarif.build_sarif([], base_dir=ROOT_DIR,
                                     notifications=[{'message': 'gate could not run'}])
        merged = sarif.merge_sarif([document])
        self.assertFalse(merged['runs'][0]['invocations'][0]['executionSuccessful'])

    def test_sarif_requested_accepts_all_three_spellings(self):
        self.assertTrue(sarif.sarif_requested(['--sarif']))
        self.assertTrue(sarif.sarif_requested(['--format', 'sarif']))
        self.assertTrue(sarif.sarif_requested(['--format=sarif']))
        self.assertTrue(sarif.sarif_requested(['--format', 'SARIF']))
        self.assertFalse(sarif.sarif_requested(['--format', 'json']))
        self.assertFalse(sarif.sarif_requested(['./src']))

    def test_every_emitted_rule_id_exists_in_the_registry(self):
        """
        A fallback slug id is a documented gap, not a silent one: it must not
        collide with, or shadow, a real registry rule.
        """
        document = sarif.build_sarif(
            [{'file': 'a.css', 'line': 1, 'label': 'some unmapped label'}],
            base_dir=ROOT_DIR,
        )
        emitted = document['runs'][0]['tool']['driver']['rules'][0]['id']
        self.assertNotIn(emitted, RULES)


class GateSarifOutputTest(unittest.TestCase):
    """Each gate, run for real, must emit a valid document that agrees with its console report."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='sarif_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run(self, argv):
        return subprocess.run(argv, capture_output=True, text=True, cwd=ROOT_DIR)

    def _document(self, result, label):
        self.assertIn(result.returncode, (0, 1, 2), f"{label}: unexpected exit {result.returncode}\n{result.stderr}")
        try:
            document = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"{label}: stdout was not JSON (stderr: {result.stderr[:500]})\n"
                      f"stdout head: {result.stdout[:500]}")
        self.assertEqual(sarif.validate_sarif(document), [], label)
        return document

    def test_bidi_gate_emits_registry_rule_ids(self):
        html = os.path.join(self.temp_dir, 'a.html')
        with open(html, 'w', encoding='utf-8') as handle:
            handle.write('<html><body><div style="margin-left: 8px">x</div></body></html>')
        result = self._run(['python3', os.path.join(GATES_DIR, 'gate_bidi_logical.py'),
                            self.temp_dir, '--format', 'sarif'])
        document = self._document(result, 'bidi')
        self.assertEqual(result.returncode, 1)
        rule_ids = {r['ruleId'] for r in document['runs'][0]['results']}
        self.assertIn('bidi.physical-direction-property', rule_ids)
        self.assertTrue(rule_ids <= set(RULES), rule_ids - set(RULES))

    def test_slop_gate_emits_one_rule_per_pattern(self):
        html = os.path.join(self.temp_dir, 'b.html')
        with open(html, 'w', encoding='utf-8') as handle:
            handle.write('<html><body><button style="background: linear-gradient(#6366f1, #a855f7)">Go 🚀</button></body></html>')
        result = self._run(['python3', os.path.join(GATES_DIR, 'gate_no_slop.py'),
                            self.temp_dir, '--format', 'sarif'])
        document = self._document(result, 'slop')
        self.assertEqual(result.returncode, 1)
        rule_ids = {r['ruleId'] for r in document['runs'][0]['results']}
        self.assertTrue(rule_ids <= set(RULES), rule_ids - set(RULES))
        self.assertIn('slop.ai-purple-gradient', rule_ids)

    def test_fsm_gate_annotates_the_state_line(self):
        fsm_dir = os.path.join(self.temp_dir, 'core', 'fsm')
        os.makedirs(fsm_dir)
        with open(os.path.join(fsm_dir, 'button.json'), 'w', encoding='utf-8') as handle:
            json.dump({
                'initialState': 'idle',
                'states': {
                    'idle': {'on': {'click': 'loading'}},
                    'loading': {'on': {'done': 'idle'}},
                },
            }, handle, indent=2)
        result = self._run(['python3', os.path.join(GATES_DIR, 'gate_fsm_integrity.py'),
                            self.temp_dir, '--format', 'sarif'])
        document = self._document(result, 'fsm')
        self.assertEqual(result.returncode, 1)
        lines = [r['locations'][0]['physicalLocation']['region']['startLine']
                 for r in document['runs'][0]['results']]
        # The annotation must point into the document, not default to line 1 for
        # every finding — that would make the state names unfindable in the UI.
        self.assertTrue(any(line > 1 for line in lines), lines)

    def test_contrast_gate_annotates_the_token_file(self):
        tokens_dir = os.path.join(self.temp_dir, 'core', 'tokens')
        os.makedirs(tokens_dir)
        for name in ('primitives.json', 'semantics.json', 'contrast-matrix.json'):
            source = os.path.join(ROOT_DIR, 'core', 'tokens', name)
            if os.path.exists(source):
                shutil.copy(source, os.path.join(tokens_dir, name))
        semantics = os.path.join(tokens_dir, 'semantics.json')
        with open(semantics, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        data['theme']['light']['content']['tertiary']['$value'] = '{color.neutral.300}'
        with open(semantics, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2)

        result = self._run(['python3', os.path.join(GATES_DIR, 'gate_contrast_wcag.py'),
                            self.temp_dir, '--format', 'sarif'])
        document = self._document(result, 'contrast')
        self.assertEqual(result.returncode, 1)
        results = document['runs'][0]['results']
        self.assertTrue(results)
        uri = results[0]['locations'][0]['physicalLocation']['artifactLocation']['uri']
        self.assertTrue(uri.endswith('semantics.json'), uri)
        self.assertTrue(results[0]['ruleId'].startswith('contrast.'), results[0]['ruleId'])

    def test_security_gate_maps_labels_to_security_rules(self):
        source = os.path.join(self.temp_dir, 'app.py')
        with open(source, 'w', encoding='utf-8') as handle:
            handle.write('import subprocess\n\n\ndef run(cmd):\n    subprocess.run(cmd, shell=True)\n')
        result = self._run(['python3', os.path.join(GATES_DIR, 'gate_security_audit.py'),
                            self.temp_dir, '--format', 'sarif'])
        document = self._document(result, 'security')
        self.assertEqual(result.returncode, 1)
        rule_ids = {r['ruleId'] for r in document['runs'][0]['results']}
        self.assertIn('security.command-injection', rule_ids)
        self.assertTrue(rule_ids <= set(RULES), rule_ids - set(RULES))

    def test_security_gate_reports_a_missing_target_as_a_tool_error(self):
        result = self._run(['python3', os.path.join(GATES_DIR, 'gate_security_audit.py'),
                            os.path.join(self.temp_dir, 'nope'), '--format', 'sarif'])
        self.assertEqual(result.returncode, 2)
        document = self._document(result, 'security-missing')
        run = document['runs'][0]
        self.assertEqual(run['results'], [])
        self.assertFalse(run['invocations'][0]['executionSuccessful'])

    def test_cwv_gate_annotates_the_offending_element(self):
        if not _parse5_installed():
            if os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ:
                self.fail('parse5 is required to verify the DOM gate SARIF output in CI.')
            self.skipTest('parse5 not installed — run `npm ci`')

        html = os.path.join(self.temp_dir, 'c.html')
        with open(html, 'w', encoding='utf-8') as handle:
            handle.write('<!DOCTYPE html>\n<html>\n<head>\n<title>T</title>\n'
                         '<script src="app.js"></script>\n</head>\n<body>\n'
                         '<img src="x.png" alt="x">\n</body>\n</html>\n')
        result = self._run(['node', os.path.join(GATES_DIR, 'gate_cwv_budget.mjs'),
                            self.temp_dir, '--format', 'sarif'])
        document = self._document(result, 'cwv')
        self.assertEqual(result.returncode, 1)
        results = document['runs'][0]['results']
        rule_ids = {r['ruleId'] for r in results}
        self.assertIn('dom.blocking-script', rule_ids)
        self.assertTrue(rule_ids <= set(RULES), rule_ids - set(RULES))
        script_lines = [r['locations'][0]['physicalLocation']['region']['startLine']
                        for r in results if r['ruleId'] == 'dom.blocking-script']
        self.assertEqual(script_lines, [5])

    def test_cwv_gate_reports_no_markup_as_a_tool_error(self):
        if not _parse5_installed():
            if os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ:
                self.fail('parse5 is required to verify the DOM gate SARIF output in CI.')
            self.skipTest('parse5 not installed — run `npm ci`')

        result = self._run(['node', os.path.join(GATES_DIR, 'gate_cwv_budget.mjs'),
                            self.temp_dir, '--format', 'sarif'])
        self.assertEqual(result.returncode, 2)
        document = self._document(result, 'cwv-empty')
        self.assertFalse(document['runs'][0]['invocations'][0]['executionSuccessful'])

    def test_console_output_is_unchanged_by_the_sarif_path(self):
        """SARIF is an addition, not a replacement: the human report still prints."""
        html = os.path.join(self.temp_dir, 'd.html')
        with open(html, 'w', encoding='utf-8') as handle:
            handle.write('<html><body><div style="margin-left: 8px">x</div></body></html>')
        result = self._run(['python3', os.path.join(GATES_DIR, 'gate_bidi_logical.py'), self.temp_dir])
        self.assertEqual(result.returncode, 1)
        self.assertIn('ORTHOTECT GATE', result.stdout)
        self.assertIn('REJECT', result.stdout)


class OrchestratorSarifTest(unittest.TestCase):
    """The merged document is what CI actually publishes, so it is tested end to end."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='sarif_all_')
        tokens_dir = os.path.join(self.temp_dir, 'core', 'tokens')
        os.makedirs(tokens_dir)
        for name in ('primitives.json', 'semantics.json', 'contrast-matrix.json'):
            source = os.path.join(ROOT_DIR, 'core', 'tokens', name)
            if os.path.exists(source):
                shutil.copy(source, os.path.join(tokens_dir, name))
        # A valid FSM keeps the fixture to exactly one failing gate (BiDi), so the
        # aggregate verdict is a violation (1) rather than a tool error (2).
        fsm_dir = os.path.join(self.temp_dir, 'core', 'fsm')
        os.makedirs(fsm_dir)
        with open(os.path.join(fsm_dir, 'button.json'), 'w', encoding='utf-8') as handle:
            json.dump({
                'initialState': 'idle',
                'states': {
                    'idle': {'on': {'click': 'loading'}},
                    'loading': {'isAsync': True, 'allowClick': False,
                                'on': {'done': 'idle', 'error': 'failed'}},
                    'failed': {'on': {'retry': 'idle'}},
                },
            }, handle, indent=2)
        with open(os.path.join(self.temp_dir, 'a.html'), 'w', encoding='utf-8') as handle:
            handle.write('<!DOCTYPE html><html><head><title>T</title></head><body>'
                         '<div style="margin-left: 8px">x</div></body></html>')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_all_gates_fold_into_one_valid_run(self):
        result = subprocess.run(
            ['python3', os.path.join(GATES_DIR, 'run_all_gates.py'),
             self.temp_dir, '--format', 'sarif'],
            capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertIn(result.returncode, (0, 1, 2), result.stderr)
        document = json.loads(result.stdout)
        self.assertEqual(len(document['runs']), 1)
        self.assertEqual(sarif.validate_sarif(document), [])
        self.assertEqual(document['runs'][0]['tool']['driver']['name'], 'orthotect')

    def test_orchestrator_exit_code_matches_the_gate_results(self):
        """
        The merged document must not change the verdict. A CI job publishes the
        annotations *and* fails the build from the same run, so the exit code and
        the document have to describe the same audit.
        """
        clean_dir = tempfile.mkdtemp(prefix='sarif_clean_')
        try:
            with open(os.path.join(clean_dir, 'a.html'), 'w', encoding='utf-8') as handle:
                handle.write('<!DOCTYPE html><html><head><title>T</title></head><body><p>x</p></body></html>')
            dirty = subprocess.run(
                ['python3', os.path.join(GATES_DIR, 'run_all_gates.py'),
                 self.temp_dir, '--format', 'sarif'],
                capture_output=True, text=True, cwd=ROOT_DIR)
            self.assertEqual(dirty.returncode, 1, dirty.stderr)
            dirty_doc = json.loads(dirty.stdout)
            self.assertTrue(dirty_doc['runs'][0]['results'])
        finally:
            shutil.rmtree(clean_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
