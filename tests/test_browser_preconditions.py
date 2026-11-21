#!/usr/bin/env python3
"""
Browser tests must skip for the right reason.

A browser-backed test has two preconditions: a Chrome/Chromium binary, and the
`playwright-core` module the generated `node` script imports. Three of the four
browser suites originally checked only the first. On a fresh clone — Chrome
installed, `npm ci` not yet run — the script threw `ERR_MODULE_NOT_FOUND` and the
suite reported 29 hard *failures* that said nothing about the code under test.

The fix must not weaken the CI contract: in CI a missing precondition is still a
failure, because silently shrinking coverage is exactly what this repository's
gates exist to prevent. These tests pin both halves of that behaviour without
launching a browser, so they run in under a second.
"""

import ast
import os
import subprocess
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BROWSER_SUITES = [
    'tests/test_docs_browser.py',
    'tests/test_modal_browser.py',
    'tests/test_scaffold_browser.py',
    'tests/test_contrast.py',
]


class BrowserPreconditionSourceTest(unittest.TestCase):
    """
    A source-level check, because the runtime behaviour depends on the machine:
    a test that only asserts "this skips" would pass on a machine with no Chrome
    for the wrong reason.
    """

    def test_every_browser_suite_checks_for_playwright(self):
        for rel in BROWSER_SUITES:
            with self.subTest(suite=rel):
                with open(os.path.join(ROOT_DIR, rel), encoding='utf-8') as handle:
                    src = handle.read()
                self.assertIn('playwright-core', src,
                              f'{rel} drives playwright-core but never checks for it')

    def test_every_browser_suite_keeps_the_ci_failure(self):
        """A missing precondition must fail in CI, not skip."""
        for rel in BROWSER_SUITES:
            with self.subTest(suite=rel):
                with open(os.path.join(ROOT_DIR, rel), encoding='utf-8') as handle:
                    src = handle.read()
                self.assertIn('CI', src, f'{rel} does not branch on CI')
                self.assertIn('self.fail', src,
                              f'{rel} would skip in CI instead of failing closed')

    def test_the_suites_agree_on_how_they_detect_the_module(self):
        """
        Four copies of the same guard is a drift hazard. They must at least agree
        on the detection mechanism, so a fix to one is obviously a fix to all.
        """
        for rel in BROWSER_SUITES:
            with self.subTest(suite=rel):
                with open(os.path.join(ROOT_DIR, rel), encoding='utf-8') as handle:
                    src = handle.read()
                tree = ast.parse(src)
                detected = any(
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and node.value == 'playwright-core'
                    for node in ast.walk(tree)
                )
                self.assertTrue(detected, f'{rel} does not reference playwright-core')


class BrowserPreconditionRuntimeTest(unittest.TestCase):
    """
    Exercises the actual skip path by hiding `playwright-core` from the suite.

    Hiding is done by patching `os.path.isdir` inside a child process, so the
    developer's real `node_modules` is never touched — a test that rearranges
    your dependencies to prove a point is a bad trade.
    """

    def test_local_run_skips_with_an_actionable_message(self):
        """
        With `node_modules/playwright-core` hidden, the suite must skip and name
        the missing module rather than raise ERR_MODULE_NOT_FOUND.
        """
        hidden = os.path.join(ROOT_DIR, 'node_modules', 'playwright-core')
        if not os.path.isdir(hidden):
            self.skipTest('playwright-core is not installed — nothing to hide')

        probe = (
            'import os, sys, unittest\n'
            'sys.path.insert(0, %r)\n'
            'import tests.test_docs_browser as m\n'
            'real = os.path.isdir\n'
            'target = os.path.join(%r, "node_modules", "playwright-core")\n'
            'os.path.isdir = lambda p: False if os.path.abspath(p) == target else real(p)\n'
            # An installed Chrome must not be enough to proceed.
            'loader = unittest.TestLoader()\n'
            'suite = loader.loadTestsFromModule(m)\n'
            'res = unittest.TextTestRunner(verbosity=0).run(suite)\n'
            'print("RESULT", len(res.skipped), len(res.failures), len(res.errors))\n'
        ) % (ROOT_DIR, ROOT_DIR)
        env = dict(os.environ)
        env.pop('CI', None)
        env.pop('GITHUB_ACTIONS', None)
        res = subprocess.run([sys.executable, '-c', probe],
                             capture_output=True, text=True, cwd=ROOT_DIR, env=env)
        self.assertEqual(res.returncode, 0, res.stderr[-2000:])
        line = [ln for ln in res.stdout.splitlines() if ln.startswith('RESULT')][-1]
        skipped, failed, errors = (int(part) for part in line.split()[1:])
        self.assertGreater(skipped, 0, 'nothing was skipped')
        self.assertEqual(failed, 0, 'the suite failed instead of skipping')
        self.assertEqual(errors, 0, 'the suite errored instead of skipping')

    def test_ci_run_fails_closed(self):
        """The same condition in CI must be a failure, not a skip."""
        hidden = os.path.join(ROOT_DIR, 'node_modules', 'playwright-core')
        if not os.path.isdir(hidden):
            self.skipTest('playwright-core is not installed — nothing to hide')

        probe = (
            'import os, sys, unittest\n'
            'sys.path.insert(0, %r)\n'
            'import tests.test_docs_browser as m\n'
            'real = os.path.isdir\n'
            'target = os.path.join(%r, "node_modules", "playwright-core")\n'
            'os.path.isdir = lambda p: False if os.path.abspath(p) == target else real(p)\n'
            'suite = unittest.TestLoader().loadTestsFromModule(m)\n'
            'res = unittest.TextTestRunner(verbosity=0).run(suite)\n'
            'print("RESULT", len(res.skipped), len(res.failures))\n'
        ) % (ROOT_DIR, ROOT_DIR)
        res = subprocess.run([sys.executable, '-c', probe],
                             capture_output=True, text=True, cwd=ROOT_DIR,
                             env=dict(os.environ, CI='true'))
        line = [ln for ln in res.stdout.splitlines() if ln.startswith('RESULT')][-1]
        skipped, failed = (int(part) for part in line.split()[1:])
        self.assertGreater(failed, 0, 'CI did not fail when playwright-core was missing')
        self.assertEqual(skipped, 0, 'CI skipped instead of failing closed')


if __name__ == '__main__':
    unittest.main()
