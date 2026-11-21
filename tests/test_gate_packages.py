#!/usr/bin/env python3
"""
P3-1 — the two large gates are packages; these are the invariants of the split.

Splitting a 1,400-line module into a package is invisible when it works and
catastrophic when it half-works: a module that imports a name it does not bind
raises `NameError` only on the code path that reaches it, and a facade that
re-exports a *reassigned* flag silently stops honouring the reassignment. Both
failures are quiet, so each is pinned directly.

The tests here are about the shape of the refactor, not about gate behaviour —
`test_bidi.py`, `test_security_gate.py` and the SARIF suite already cover that.
"""

import os
import subprocess
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GATES_DIR = os.path.join(ROOT_DIR, 'gates')

PACKAGES = {
    'gates/_bidi': 'gates/gate_bidi_logical.py',
    'gates/_security': 'gates/gate_security_audit.py',
}


def _modules(package):
    directory = os.path.join(ROOT_DIR, package)
    return sorted(os.path.join(directory, name) for name in os.listdir(directory)
                  if name.endswith('.py'))


class TestPackageLayout(unittest.TestCase):
    def test_each_gate_entry_point_is_a_thin_facade(self):
        """
        The entry point must stay small. If rule logic creeps back into it, the
        package split is undone one function at a time and nobody notices.
        """
        for entry in PACKAGES.values():
            with self.subTest(entry=entry):
                with open(os.path.join(ROOT_DIR, entry), encoding='utf-8') as handle:
                    lines = handle.read().splitlines()
                self.assertLess(len(lines), 60, f'{entry} has grown back into a gate')
                self.assertIn('from _', ''.join(lines),
                              f'{entry} does not delegate to its package')

    def test_every_package_module_is_importable(self):
        for package in PACKAGES:
            with self.subTest(package=package):
                self.assertGreaterEqual(len(_modules(package)), 5)

    def test_the_package_name_cannot_be_shadowed_from_sys_path(self):
        """
        `_bidi` and `_security` are private names, so a bare `import _security`
        would accept any module of that name earlier on `sys.path`. Both
        facades pin their own directory first; this proves it by planting a
        sabotaged module and requiring the real gate to still import.

        The shadow is exercised through `import gates.gate_*` from a foreign
        working directory. A direct `python3 gates/gate_*.py` run is not a valid
        probe: the interpreter already puts the script's directory first, so the
        facade would import correctly with or without its own anchor and the
        test would pass while the guard was missing.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as shadow:
            for name in ('_bidi.py', '_security.py'):
                with open(os.path.join(shadow, name), 'w', encoding='utf-8') as handle:
                    handle.write('raise RuntimeError("hijacked")\n')
            env = dict(os.environ, PYTHONPATH=os.pathsep.join([shadow, ROOT_DIR]))
            probe = (
                'import gates.gate_bidi_logical as b\n'
                'import gates.gate_security_audit as s\n'
                'print(b.logical_shorthand_pair("margin"))\n'
                'print(callable(s.scan_file))\n'
            )
            res = subprocess.run([sys.executable, '-c', probe],
                                 capture_output=True, text=True, cwd=shadow, env=env)
            self.assertNotIn('hijacked', res.stderr, res.stderr)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(res.stdout.split(),
                             ["('margin-block',", "'margin-inline')", 'True'])


class TestNoUnboundGlobals(unittest.TestCase):
    """
    A `NameError` from a split module fires only on the branch that reaches it,
    so a passing suite is not evidence that every module is wired correctly.
    `symtable` gives the scope-accurate answer: every name a module reads as a
    global must be bound in that module.
    """

    def test_every_module_binds_what_it_reads(self):
        import builtins
        import symtable

        injected = {'__file__', '__name__', '__doc__', '__spec__',
                    '__package__', '__loader__'}
        builtin_names = set(dir(builtins)) | injected

        for package in PACKAGES:
            for path in _modules(package):
                with self.subTest(module=os.path.relpath(path, ROOT_DIR)):
                    with open(path, encoding='utf-8') as handle:
                        src = handle.read()
                    table = symtable.symtable(src, path, 'exec')
                    bound = {sym.get_name() for sym in table.get_symbols()
                             if sym.is_assigned() or sym.is_imported() or sym.is_namespace()}
                    scopes = [table] + list(table.get_children())
                    for scope in scopes:
                        for sym in scope.get_symbols():
                            if not (sym.is_global() and sym.is_referenced()):
                                continue
                            name = sym.get_name()
                            self.assertTrue(
                                name in bound or name in builtin_names,
                                f'{os.path.basename(path)}: {scope.get_name()} '
                                f'reads unbound global {name!r}')


class TestFacadeKeepsThePublicSurface(unittest.TestCase):
    """
    The split must be invisible to callers. These are the exact import styles
    the suite, the CLI and the published package use.
    """

    def test_import_styles_agree(self):
        probe = (
            'import sys\n'
            'sys.path.insert(0, %r)\n'
            'import gates.gate_bidi_logical as via_gates\n'
            'import gates.gate_security_audit as sec_via_gates\n'
            'sys.path.insert(0, %r)\n'
            'import gate_bidi_logical as bare\n'
            'print(via_gates.logical_shorthand_pair("margin"))\n'
            'print(bare.logical_shorthand_pair("margin"))\n'
            'print(callable(via_gates.scan_file), callable(bare.scan_file))\n'
            'print(callable(sec_via_gates.scan_file), callable(sec_via_gates.main))\n'
        ) % (ROOT_DIR, GATES_DIR)
        res = subprocess.run([sys.executable, '-c', probe],
                             capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(res.returncode, 0, res.stderr)
        lines = res.stdout.split('\n')
        self.assertEqual(lines[0], "('margin-block', 'margin-inline')")
        self.assertEqual(lines[0], lines[1])
        self.assertEqual(lines[2], 'True True')
        self.assertEqual(lines[3], 'True True')

    def test_the_mutable_runtime_flag_is_forwarded_not_copied(self):
        """
        The bug this prevents: `bidi_mod.HAVE_TINYCSS2 = False` rebinding only
        the facade's namespace while the scanners keep reading their own `True`.
        The fallback path would appear tested and never run.
        """
        probe = (
            'import sys\n'
            'sys.path.insert(0, %r)\n'
            'import gates.gate_bidi_logical as g\n'
            'print(g.HAVE_TINYCSS2)\n'
            'g.HAVE_TINYCSS2 = False\n'
            'print(g.HAVE_TINYCSS2)\n'
            'print(g._runtime.HAVE_TINYCSS2)\n'
            'print(len(g.scan_html_content("<style>.a{margin-left:1px}</style>")))\n'
        ) % ROOT_DIR
        res = subprocess.run([sys.executable, '-c', probe],
                             capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(res.returncode, 0, res.stderr)
        first, patched, runtime, scanned = res.stdout.split()
        self.assertEqual(first, 'True')
        self.assertEqual(patched, 'False')
        self.assertEqual(runtime, 'False', 'the assignment did not reach _runtime')
        self.assertEqual(scanned, '1', 'the fallback scanner stopped detecting')


class TestEngineSelfExemption(unittest.TestCase):
    """
    The security gate must never report its own rule table as a vulnerability.

    Before the split, one filename check covered the whole engine. Afterwards
    the patterns live in `gates/_security/_patterns.py`, and a filename-only
    check made the gate fail on itself — a fail-closed gate that cannot pass its
    own audit is unusable.
    """

    def test_engine_files_are_exempt_and_user_files_are_not(self):
        sys.path.insert(0, ROOT_DIR)
        from gates.gate_security_audit import is_engine_file

        engine = [
            'gate_security_audit.py',
            '/app/gates/gate_security_audit.py',
            '/app/gates/_security/_patterns.py',
            '/app/gates/_security/_ast.py',
            'gates/_security/_taint.py',
        ]
        for path in engine:
            with self.subTest(path=path):
                self.assertTrue(is_engine_file(path))

        user = [
            '/app/src/server.js',
            '/app/gates/gate_contrast_wcag.py',
            # A file merely *named* like an engine module is still user code.
            '/app/src/_security/helpers.py',
            '/app/src/security_audit.py',
        ]
        for path in user:
            with self.subTest(path=path):
                self.assertFalse(is_engine_file(path))

    def test_the_gate_passes_on_its_own_directory(self):
        """The end-to-end form of the exemption."""
        res = subprocess.run(
            [sys.executable, os.path.join(GATES_DIR, 'gate_security_audit.py'), GATES_DIR],
            capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(res.returncode, 0, res.stdout[-1500:])


if __name__ == '__main__':
    unittest.main()
