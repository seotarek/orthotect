#!/usr/bin/env python3
"""
P1-3 — Security baseline / allowlist.

REVIEW_2026-11.md C2 removed a blanket `/tests/` path exemption from the SAST
gate, because shipping code under a test-shaped path was silently un-audited.
The correct replacement is a committed allowlist where every suppression names a
file, a rule, a line and a justification — reviewable in a diff, rather than
invisible path trust.

These tests pin both directions: a valid baseline suppresses exactly what it
names, and an unusable baseline fails closed instead of silently re-enabling
(or silently hiding) findings.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GATE = os.path.join(ROOT_DIR, 'gates', 'gate_security_audit.py')

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

DOM_XSS = 'function r(){const b=document.getElementById("n");b.innerHTML=location.search;}\n'
CLEAN = 'export const ok = document.getElementById("a").textContent;\n'

# The exact labels the scanner emits for DOM_XSS (two distinct rules fire).
DOM_XSS_RULES = [
    "DOM XSS: Direct assignment of un-sanitized URL/location source to DOM HTML sink",
    "DOM XSS (Direct Sink): Direct untrusted source assigned to dangerous DOM sink without sanitization",
]


class BaselineHarness(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='sec_baseline_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write(self, rel, body):
        path = os.path.join(self.temp_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
        return path

    def write_baseline(self, suppressions, version=1):
        payload = {"version": version, "suppressions": suppressions}
        with open(os.path.join(self.temp_dir, 'orthotect-security-baseline.json'),
                  'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)

    def run_gate(self, *args):
        return subprocess.run([sys.executable, GATE, self.temp_dir, *args],
                              capture_output=True, text=True)


class TestBaselineSuppression(BaselineHarness):
    """A valid entry suppresses exactly its finding and nothing else."""

    def test_no_baseline_still_fails_on_vulnerability(self):
        self.write('src/app.js', DOM_XSS)
        self.assertEqual(self.run_gate().returncode, 1)

    def test_baseline_suppresses_named_findings(self):
        self.write('src/app.js', DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 1,
             "justification": "Red-team fixture that asserts on an XSS payload."}
            for rule in DOM_XSS_RULES
        ])
        res = self.run_gate()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn('[SUPPRESSED]', res.stdout)

    def test_suppression_is_reported_with_its_justification(self):
        """A suppression that is not shown is indistinguishable from no finding."""
        self.write('src/app.js', DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 1,
             "justification": "Deliberate vulnerable fixture for gate self-tests."}
            for rule in DOM_XSS_RULES
        ])
        res = self.run_gate()
        self.assertIn('Deliberate vulnerable fixture for gate self-tests.', res.stdout)

    def test_suppression_does_not_leak_to_other_files(self):
        """
        A scoped allowlist is the property that makes this better than path trust:
        the same rule in a different file must still fail.
        """
        self.write('src/app.js', DOM_XSS)
        self.write('src/other.js', DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 1, "justification": "Fixture."}
            for rule in DOM_XSS_RULES
        ])
        res = self.run_gate()
        self.assertEqual(res.returncode, 1, res.stdout)

    def test_suppression_does_not_leak_to_other_lines(self):
        self.write('src/app.js', DOM_XSS + DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 1, "justification": "Line 1 only."}
            for rule in DOM_XSS_RULES
        ])
        res = self.run_gate()
        self.assertEqual(res.returncode, 1, res.stdout)

    def test_line_zero_suppresses_any_line_for_that_rule(self):
        """The documented escape for unstable line numbers stays scoped to one file+rule."""
        self.write('src/app.js', DOM_XSS + DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 0, "justification": "Whole-file fixture."}
            for rule in DOM_XSS_RULES
        ])
        res = self.run_gate()
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_clean_file_with_baseline_passes(self):
        self.write('src/ok.js', CLEAN)
        self.write_baseline([
            {"file": "src/ok.js", "rule": DOM_XSS_RULES[0], "line": 1, "justification": "Unused."}
        ])
        self.assertEqual(self.run_gate().returncode, 0)


class TestBaselineFailsClosed(BaselineHarness):
    """An unusable baseline is a tool error (exit 2), never a pass."""

    def test_malformed_json_is_tool_error(self):
        self.write('src/ok.js', CLEAN)
        with open(os.path.join(self.temp_dir, 'orthotect-security-baseline.json'), 'w') as f:
            f.write('{not valid json')
        res = self.run_gate()
        self.assertEqual(res.returncode, 2, res.stdout)

    def test_bad_version_is_tool_error(self):
        self.write('src/ok.js', CLEAN)
        self.write_baseline([], version=99)
        self.assertEqual(self.run_gate().returncode, 2)

    def test_missing_justification_is_tool_error(self):
        """The field that makes a suppression reviewable cannot be optional."""
        self.write('src/ok.js', CLEAN)
        self.write_baseline([{"file": "src/ok.js", "rule": "X", "line": 1}])
        res = self.run_gate()
        self.assertEqual(res.returncode, 2)
        self.assertIn('justification', res.stdout)

    def test_glob_in_file_is_tool_error(self):
        """A glob would reproduce the blanket exemption this baseline replaced."""
        self.write('src/ok.js', CLEAN)
        self.write_baseline([{"file": "src/*.js", "rule": "X", "line": 1, "justification": "y"}])
        res = self.run_gate()
        self.assertEqual(res.returncode, 2)
        self.assertIn('must name one file', res.stdout)

    def test_glob_in_rule_is_tool_error(self):
        self.write('src/ok.js', CLEAN)
        self.write_baseline([{"file": "src/ok.js", "rule": "DOM XSS*", "line": 1, "justification": "y"}])
        self.assertEqual(self.run_gate().returncode, 2)

    def test_absolute_path_is_tool_error(self):
        """Suppressions must be repo-relative so they stay valid across checkouts."""
        self.write('src/ok.js', CLEAN)
        self.write_baseline([{"file": "/etc/passwd", "rule": "X", "line": 1, "justification": "y"}])
        self.assertEqual(self.run_gate().returncode, 2)

    def test_negative_line_is_tool_error(self):
        self.write('src/ok.js', CLEAN)
        self.write_baseline([{"file": "src/ok.js", "rule": "X", "line": -1, "justification": "y"}])
        self.assertEqual(self.run_gate().returncode, 2)

    def test_duplicate_entry_is_tool_error(self):
        self.write('src/ok.js', CLEAN)
        entry = {"file": "src/ok.js", "rule": "X", "line": 1, "justification": "y"}
        self.write_baseline([entry, dict(entry)])
        self.assertEqual(self.run_gate().returncode, 2)

    def test_suppressions_must_be_a_list(self):
        self.write('src/ok.js', CLEAN)
        with open(os.path.join(self.temp_dir, 'orthotect-security-baseline.json'), 'w') as f:
            json.dump({"version": 1, "suppressions": {"file": "a"}}, f)
        self.assertEqual(self.run_gate().returncode, 2)


class TestStaleEntriesAreReported(BaselineHarness):
    """A suppression that no longer matches anything must be visible, not silent."""

    def test_stale_entry_warns_but_does_not_fail(self):
        """
        A stale entry does not impair the audit — every file was still scanned —
        so it must not be reported as an environment failure. It must, however, be
        surfaced, or the file rots into a set of claims nobody has verified.
        """
        self.write('src/ok.js', CLEAN)
        self.write_baseline([
            {"file": "src/ok.js", "rule": "A Rule That Does Not Fire", "line": 1,
             "justification": "No longer needed."}
        ])
        res = self.run_gate()
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn('stale baseline', res.stdout)

    def test_stale_entries_appear_in_json(self):
        self.write('src/ok.js', CLEAN)
        self.write_baseline([
            {"file": "src/ok.js", "rule": "Gone Rule", "line": 1, "justification": "old"}
        ])
        res = self.run_gate('--json')
        payload = json.loads(res.stdout)
        self.assertEqual(len(payload['baseline']['staleEntries']), 1)
        self.assertEqual(payload['baseline']['staleEntries'][0]['rule'], 'Gone Rule')

    def test_matched_entries_are_not_reported_stale(self):
        self.write('src/app.js', DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 1, "justification": "Fixture."}
            for rule in DOM_XSS_RULES
        ])
        res = self.run_gate('--json')
        payload = json.loads(res.stdout)
        self.assertEqual(payload['baseline']['staleEntries'], [])
        self.assertEqual(payload['baseline']['suppressedCount'], 2)


class TestBaselineJsonReport(BaselineHarness):
    """Machine consumers must be able to see what was exempted and why."""

    def test_json_reports_suppressed_findings_with_justification(self):
        self.write('src/app.js', DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 1,
             "justification": "Reviewed fixture."}
            for rule in DOM_XSS_RULES
        ])
        payload = json.loads(self.run_gate('--json').stdout)
        self.assertTrue(payload['passed'])
        self.assertEqual(len(payload['suppressed']), 2)
        self.assertTrue(all(s['justification'] == 'Reviewed fixture.'
                            for s in payload['suppressed']))
        self.assertEqual(payload['baseline']['entryCount'], 2)

    def test_json_without_baseline_reports_null_path(self):
        self.write('src/ok.js', CLEAN)
        payload = json.loads(self.run_gate('--json').stdout)
        self.assertIsNone(payload['baseline']['path'])
        self.assertEqual(payload['baseline']['suppressedCount'], 0)

    def test_markdown_report_lists_suppressions(self):
        self.write('src/app.js', DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 1, "justification": "Reviewed fixture."}
            for rule in DOM_XSS_RULES
        ])
        out = self.run_gate('--md').stdout
        self.assertIn('Baseline:', out)
        self.assertIn('Reviewed fixture.', out)


class TestBaselinePathResolution(BaselineHarness):
    """
    Suppression paths are relative to the directory holding the baseline file.

    These two cases were real bugs: resolving against the audit root made every
    entry silently fail to match when the target was a single file, and when a
    monorepo kept one baseline above the package being audited.
    """

    def test_single_file_target_resolves_sibling_baseline(self):
        self.write('src/app.js', DOM_XSS)
        self.write_baseline([
            {"file": "src/app.js", "rule": rule, "line": 1, "justification": "Fixture."}
            for rule in DOM_XSS_RULES
        ])
        res = subprocess.run(
            [sys.executable, GATE, os.path.join(self.temp_dir, 'src', 'app.js')],
            capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn('[SUPPRESSED]', res.stdout)

    def test_monorepo_parent_baseline_uses_its_own_directory(self):
        """
        A baseline one level above the audited package must keep its paths
        relative to itself, not to the package under audit.
        """
        pkg = os.path.join(self.temp_dir, 'packages', 'app')
        os.makedirs(os.path.join(pkg, 'src'))
        with open(os.path.join(pkg, 'src', 'a.js'), 'w') as f:
            f.write(DOM_XSS)
        with open(os.path.join(self.temp_dir, 'packages',
                               'orthotect-security-baseline.json'), 'w') as f:
            json.dump({"version": 1, "suppressions": [
                {"file": "app/src/a.js", "rule": rule, "line": 1,
                 "justification": "Monorepo fixture."}
                for rule in DOM_XSS_RULES
            ]}, f)
        res = subprocess.run([sys.executable, GATE, pkg], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_audit_root_baseline_wins_over_parent(self):
        pkg = os.path.join(self.temp_dir, 'pkg')
        os.makedirs(pkg)
        with open(os.path.join(pkg, 'a.js'), 'w') as f:
            f.write(DOM_XSS)
        for d in (self.temp_dir, pkg):
            with open(os.path.join(d, 'orthotect-security-baseline.json'), 'w') as f:
                json.dump({"version": 1, "suppressions": []}, f)
        payload = json.loads(subprocess.run(
            [sys.executable, GATE, pkg, '--json'], capture_output=True, text=True).stdout)
        self.assertEqual(payload['baseline']['path'],
                         os.path.join(pkg, 'orthotect-security-baseline.json'))


class TestBaselineModuleUnit(unittest.TestCase):
    """Direct unit coverage of the parsing/matching layer."""

    def setUp(self):
        if ROOT_DIR not in sys.path:
            sys.path.insert(0, ROOT_DIR)
        from core import security_baseline as mod
        self.mod = mod

    def test_relative_posix_normalises_separators(self):
        rel = self.mod._relative_posix('/a/b/c.js', '/a')
        self.assertEqual(rel, 'b/c.js')

    def test_baseline_entry_matches_exact_rule_only(self):
        entry = self.mod.BaselineEntry('src/a.js', 'Rule A', 5, 'why')
        self.assertTrue(entry.matches('/root/src/a.js', '/root', 5, 'Rule A'))
        self.assertFalse(entry.matches('/root/src/a.js', '/root', 5, 'Rule B'))
        self.assertFalse(entry.matches('/root/src/a.js', '/root', 6, 'Rule A'))
        self.assertFalse(entry.matches('/root/src/b.js', '/root', 5, 'Rule A'))

    def test_find_baseline_path_prefers_audit_root(self):
        import tempfile, json
        d = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(d, 'proj'))
            with open(os.path.join(d, 'orthotect-security-baseline.json'), 'w') as f:
                json.dump({"version": 1, "suppressions": []}, f)
            with open(os.path.join(d, 'proj', 'orthotect-security-baseline.json'), 'w') as f:
                json.dump({"version": 1, "suppressions": []}, f)
            found = self.mod.find_baseline_path(os.path.join(d, 'proj'))
            self.assertEqual(found, os.path.join(d, 'proj', 'orthotect-security-baseline.json'))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_find_baseline_path_returns_none_when_absent(self):
        import tempfile
        d = tempfile.mkdtemp()
        try:
            self.assertIsNone(self.mod.find_baseline_path(d))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_load_baseline_rejects_non_object_root(self):
        import tempfile
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, 'b.json')
            with open(path, 'w') as f:
                json.dump(["not", "an", "object"], f)
            with self.assertRaises(self.mod.BaselineError):
                self.mod.load_baseline(path)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_load_baseline_accepts_missing_suppressions_key(self):
        import tempfile
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, 'b.json')
            with open(path, 'w') as f:
                json.dump({"version": 1}, f)
            self.assertEqual(self.mod.load_baseline(path), [])
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
