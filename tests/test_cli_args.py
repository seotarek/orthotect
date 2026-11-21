#!/usr/bin/env python3
"""
P2-1 — One argument parser, in two languages.

Before `core/cli_args.py`, the flag/positional split existed in six places, and
they had drifted. Only some implementations skipped the value bound to
`--format`, so `gate_contrast_wcag.py --format json ./src` treated `json` as the
target path and reported "missing design tokens in target: json" — a tool error
caused entirely by argument parsing.

The cases below are a single table run through **both** implementations: the
Python module directly, and the ESM module via Node. A divergence fails here
rather than in production, where it would surface as the CLI auditing a
different path than the gate.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GATES_DIR = os.path.join(ROOT_DIR, 'gates')
NODE_MODULE = os.path.join(ROOT_DIR, 'core', 'cli_args.mjs')

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.cli_args import (                 # noqa: E402
    parse_args,
    positionals,
    resolve_output_format,
    has_flag,
    VALUE_FLAGS,
)

# (argv, expected positionals) — the contract both languages must implement.
POSITIONAL_CASES = [
    ([], []),
    (['./src'], ['./src']),
    (['--json', './src'], ['./src']),
    (['./src', '--json'], ['./src']),
    (['--format', 'json', './src'], ['./src']),
    (['./src', '--format', 'json'], ['./src']),
    (['--format=json', './src'], ['./src']),
    (['./src', '--format=json'], ['./src']),
    (['--format', 'md', '--out', 'report.md', './src'], ['./src']),
    (['-o', 'out.md', './src'], ['./src']),
    (['--config', 'orthotect.config.json', './src'], ['./src']),
    (['--', '--weird-dir'], ['--weird-dir']),
    (['./src', '--', '--also-a-path'], ['./src', '--also-a-path']),
    (['--fix', './src'], ['./src']),
    (['-'], ['-']),  # a lone dash is a positional (stdin convention), not a flag
    # Two positionals: the first is the target, the second must survive intact.
    (['--format', 'json', './src', './other'], ['./src', './other']),
    # A repeated value flag keeps its value out of the positionals both times.
    (['--out', 'a', '--out', 'b', './src'], ['./src']),
]


class TestPositionalSplitting(unittest.TestCase):
    def test_positional_cases(self):
        for argv, expected in POSITIONAL_CASES:
            with self.subTest(argv=argv):
                self.assertEqual(positionals(argv), expected)

    def test_no_value_flag_value_leaks(self):
        """Any value-taking flag must be swallowed along with its value."""
        for flag in sorted(VALUE_FLAGS):
            argv = [flag, 'VALUE', './target']
            with self.subTest(flag=flag):
                self.assertEqual(positionals(argv), ['./target'])

    def test_target_returns_first_positional(self):
        self.assertEqual(parse_args(['--format', 'json', './src']).target(), './src')

    def test_target_returns_default_when_empty(self):
        self.assertEqual(parse_args(['--json']).target('fallback'), 'fallback')

    def test_equals_form_value_is_retrievable_but_not_positional(self):
        parsed = parse_args(['--format=json', './src'])
        self.assertEqual(parsed.value('--format'), 'json')
        self.assertEqual(parsed.positionals, ['./src'])

    def test_space_form_value_is_retrievable_but_not_positional(self):
        parsed = parse_args(['--format', 'json', './src'])
        self.assertEqual(parsed.value('--format'), 'json')
        self.assertEqual(parsed.positionals, ['./src'])

    def test_value_flag_without_value_does_not_crash(self):
        parsed = parse_args(['--format'])
        self.assertIsNone(parsed.value('--format'))
        self.assertEqual(parsed.positionals, [])

    def test_has_flag_ignores_equals_form(self):
        self.assertTrue(has_flag(['--json'], '--json'))
        self.assertFalse(has_flag(['--json=true'], '--json'))


class TestFormatResolution(unittest.TestCase):
    def test_json_and_md_shorthands(self):
        self.assertEqual(resolve_output_format(['--json']), 'json')
        self.assertEqual(resolve_output_format(['--md']), 'md')

    def test_format_flag_both_spellings(self):
        self.assertEqual(resolve_output_format(['--format', 'json']), 'json')
        self.assertEqual(resolve_output_format(['--format=md']), 'md')

    def test_unknown_format_is_none(self):
        self.assertEqual(resolve_output_format(['--format', 'yaml']), None)

    def test_sarif_is_resolvable_in_all_three_spellings(self):
        self.assertEqual(resolve_output_format(['--format', 'sarif']), 'sarif')
        self.assertEqual(resolve_output_format(['--format=sarif']), 'sarif')
        self.assertEqual(resolve_output_format(['--format', 'SARIF']), 'sarif')
        self.assertEqual(resolve_output_format(['--sarif']), 'sarif')

    def test_sarif_flag_is_ignored_when_not_offered(self):
        """
        A caller that did not opt into SARIF must not receive a machine document
        from a flag it never advertised — the same rule `--format` follows.
        """
        self.assertEqual(resolve_output_format(['--sarif'], allowed=('json', 'md')), None)
        self.assertEqual(resolve_output_format(['--format', 'sarif'], allowed=('json', 'md')), None)

    def test_sarif_directory_stays_auditable(self):
        """A path literally named `sarif` is a positional, never the format."""
        self.assertEqual(resolve_output_format(['./sarif']), None)
        self.assertEqual(positionals(['./sarif'], bare_format_tokens=('json', 'md')), ['./sarif'])

    def test_absent_format_is_none(self):
        self.assertEqual(resolve_output_format(['./src']), None)

    def test_bare_token_requires_opt_in(self):
        """A directory literally named `json` must stay auditable."""
        self.assertEqual(resolve_output_format(['./src', 'json']), None)
        self.assertEqual(resolve_output_format(['./src', 'json'], bare_token=True), 'json')

    def test_bare_token_opt_in_does_not_eat_a_path(self):
        argv = ['./src', 'json']
        self.assertEqual(positionals(argv, bare_format_tokens=('json', 'md')), ['./src'])
        self.assertEqual(positionals(argv), ['./src', 'json'])


class TestNodeParity(unittest.TestCase):
    """
    The ESM mirror must produce identical results for every case above.

    A single implementation is the goal; two implementations that disagree is
    worse than the six duplicated copies this replaced, because the disagreement
    is silent.
    """

    def run_node(self, argv):
        script = f"""
import {{ parseArgs, positionals, resolveOutputFormat }} from {json.dumps(NODE_MODULE)};
const argv = {json.dumps(argv)};
const parsed = parseArgs(argv);
process.stdout.write(JSON.stringify({{
  positionals: parsed.positionals,
  flags: parsed.flags,
  target: parsed.target(),
  format: resolveOutputFormat(argv),
  formatBare: resolveOutputFormat(argv, {{ bareToken: true }}),
}}));
"""
        temp = tempfile.mkdtemp(prefix='cli_args_')
        try:
            path = os.path.join(temp, 'probe.mjs')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(script)
            res = subprocess.run(['node', path], capture_output=True, text=True, cwd=temp)
            self.assertEqual(res.returncode, 0, res.stderr)
            return json.loads(res.stdout)
        finally:
            shutil.rmtree(temp, ignore_errors=True)

    def test_node_matches_python_positionals(self):
        for argv, expected in POSITIONAL_CASES:
            with self.subTest(argv=argv):
                out = self.run_node(argv)
                self.assertEqual(out['positionals'], expected,
                                 f"Node disagrees with Python for {argv}")

    def test_node_matches_python_format_resolution(self):
        for argv in (['--json'], ['--md'], ['--format', 'json'], ['--format=md'],
                     ['--format', 'yaml'], ['./src'], ['./src', 'json'],
                     ['--sarif'], ['--format', 'sarif'], ['--format=sarif'], ['./sarif']):
            with self.subTest(argv=argv):
                out = self.run_node(argv)
                self.assertEqual(out['format'], resolve_output_format(argv))
                self.assertEqual(out['formatBare'],
                                 resolve_output_format(argv, bare_token=True))

    def test_node_matches_python_target(self):
        for argv, _expected in POSITIONAL_CASES:
            with self.subTest(argv=argv):
                self.assertEqual(self.run_node(argv)['target'],
                                 parse_args(argv).target())


class TestGatesUseTheSharedParser(unittest.TestCase):
    """
    Every gate must delegate, not keep a private copy.

    The source-level guard is deliberate: a gate that re-grows a local
    `[a for a in sys.argv[1:] if not a.startswith('-')]` reintroduces exactly the
    class of bug this milestone removed, and it would do so silently.
    """

    # Each entry is the gate's entry module plus every module its implementation
    # lives in. `gate_bidi_logical` and `gate_security_audit` became packages, so
    # the parser import moved into the package — checking only the facade would
    # make this guard pass by inspecting a file that no longer contains the code.
    GATES = [
        ['gates/gate_bidi_logical.py'],
        ['gates/gate_contrast_wcag.py'],
        ['gates/gate_fsm_integrity.py'],
        ['gates/gate_no_slop.py'],
        ['gates/gate_security_audit.py'],
        ['gates/run_all_gates.py'],
    ]

    PACKAGES = {
        'gates/gate_bidi_logical.py': [
            'gates/_bidi/_css.py', 'gates/_bidi/_dispatch.py', 'gates/_bidi/_fix.py',
            'gates/_bidi/_js.py', 'gates/_bidi/_model.py', 'gates/_bidi/_paths.py',
            'gates/_bidi/_runtime.py', 'gates/_bidi/_shorthand.py', 'gates/_bidi/gate.py',
        ],
        'gates/gate_security_audit.py': [
            'gates/_security/_ast.py', 'gates/_security/_cli.py',
            'gates/_security/_patterns.py', 'gates/_security/_runtime.py',
            'gates/_security/_scanner.py', 'gates/_security/_taint.py',
        ],
    }

    def _sources(self, rel):
        """The entry module plus every module of its implementation package."""
        paths = [rel] + self.PACKAGES.get(rel, [])
        for path in paths:
            with open(os.path.join(ROOT_DIR, path), encoding='utf-8') as handle:
                yield path, handle.read()

    def test_python_gates_import_the_shared_parser(self):
        for rel in self.GATES:
            with self.subTest(gate=rel):
                found = [path for path, src in self._sources(rel[0])
                         if 'core.cli_args' in src]
                self.assertTrue(found,
                                f"{rel[0]} does not use the shared argument parser")

    def test_no_python_gate_reintroduces_a_private_positional_split(self):
        banned = "for a in sys.argv[1:] if not a.startswith('-')"
        for rel in self.GATES:
            with self.subTest(gate=rel):
                for path, src in self._sources(rel[0]):
                    self.assertNotIn(banned, src, f"{path} re-grew a private positional split")

    def test_the_split_packages_are_covered_by_this_guard(self):
        """
        A package's modules must all be reachable from the guard list, or a new
        module can reintroduce a private parser where nothing looks.
        """
        for _entry, declared in self.PACKAGES.items():
            package_dir = os.path.dirname(declared[0])
            on_disk = sorted(
                f'{package_dir}/{name}'
                for name in os.listdir(os.path.join(ROOT_DIR, package_dir))
                if name.endswith('.py') and name != '__init__.py'
            )
            with self.subTest(package=package_dir):
                self.assertEqual(sorted(declared), on_disk,
                                 f'{package_dir} has modules the parser guard does not read')

    def test_node_entry_points_import_the_shared_parser(self):
        for rel in ('bin/orthotect.js', 'gates/gate_cwv_budget.mjs'):
            with self.subTest(entry=rel):
                with open(os.path.join(ROOT_DIR, rel), encoding='utf-8') as f:
                    src = f.read()
                self.assertIn('cli_args.mjs', src,
                              f"{rel} does not use the shared argument parser")

    def test_node_cli_has_no_private_parse_positionals(self):
        with open(os.path.join(ROOT_DIR, 'bin', 'orthotect.js'), encoding='utf-8') as f:
            src = f.read()
        self.assertNotIn('function parsePositionals', src,
                         'bin/orthotect.js re-grew a private positional parser')


class TestValueFlagLeakIsActuallyFixed(unittest.TestCase):
    """
    End-to-end: the original symptom, run against a real gate process.

    `gate_contrast_wcag.py --format json <dir>` used to audit the literal string
    "json". The distinguishing observable is the tool error text: the fixed gate
    names the real directory, the broken one names "json".
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='cli_leak_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_contrast_gate_targets_the_directory_not_the_format_value(self):
        res = subprocess.run(
            [sys.executable, os.path.join(GATES_DIR, 'gate_contrast_wcag.py'),
             '--format', 'json', self.temp_dir],
            capture_output=True, text=True)
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertNotIn('target: json', res.stdout)
        self.assertIn(self.temp_dir, res.stdout)

    def test_no_slop_gate_targets_the_directory_not_the_format_value(self):
        res = subprocess.run(
            [sys.executable, os.path.join(GATES_DIR, 'gate_no_slop.py'),
             '--format', 'json', self.temp_dir],
            capture_output=True, text=True)
        # An empty directory is a valid, clean scan for the no-slop gate.
        self.assertNotIn('not found: json', res.stdout)


if __name__ == '__main__':
    unittest.main()
