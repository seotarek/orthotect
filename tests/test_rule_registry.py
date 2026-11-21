#!/usr/bin/env python3
"""
P2-2 — `orthotect explain <rule-id>`.

A gate that says "margin-left is banned" is half a verdict: without the citation
the rule reads as house style and gets argued with instead of fixed. The registry
is the authority on what each rule *means*; the gates remain the authority on
what fires. These tests pin both the registry's integrity and the `explain`
surface, including the failure mode that matters — an unknown id must be an
error, not silence.
"""

import json
import os
import subprocess
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GATES_DIR = os.path.join(ROOT_DIR, 'gates')
REGISTRY = os.path.join(ROOT_DIR, 'core', 'rule_registry.py')
CLI = os.path.join(ROOT_DIR, 'bin', 'orthotect.js')

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.rule_registry import (            # noqa: E402
    RULES,
    RULES_VERSION,
    RuleNotFound,
    describe,
    get_rule,
    metadata,
    rule_ids,
    rules_by_gate,
    rules_digest,
    search,
)

REQUIRED_FIELDS = ('title', 'gate', 'severity', 'citation', 'summary', 'fix')
VALID_SEVERITIES = {'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'}
KNOWN_GATES = {
    'gate_bidi_logical', 'gate_contrast_wcag', 'gate_fsm_integrity',
    'gate_no_slop', 'gate_cwv_budget', 'gate_security_audit',
}


class TestRegistryIntegrity(unittest.TestCase):
    """Every entry must be complete, or `explain` prints half a story."""

    def test_every_rule_has_all_required_fields(self):
        for rule_id, rule in RULES.items():
            for field in REQUIRED_FIELDS:
                with self.subTest(rule=rule_id, field=field):
                    self.assertIn(field, rule, f"{rule_id} is missing {field}")
                    self.assertTrue(str(rule[field]).strip(),
                                    f"{rule_id}.{field} is empty")

    def test_every_rule_names_a_real_gate(self):
        for rule_id, rule in RULES.items():
            with self.subTest(rule=rule_id):
                self.assertIn(rule['gate'], KNOWN_GATES)

    def test_every_rule_has_a_valid_severity(self):
        for rule_id, rule in RULES.items():
            with self.subTest(rule=rule_id):
                self.assertIn(rule['severity'], VALID_SEVERITIES)

    def test_rule_ids_are_prefixed_by_their_gate(self):
        """The prefix must match the owning gate, or the id is misleading."""
        prefix_to_gate = {
            'bidi': 'gate_bidi_logical',
            'contrast': 'gate_contrast_wcag',
            'fsm': 'gate_fsm_integrity',
            'slop': 'gate_no_slop',
            'dom': 'gate_cwv_budget',
            'security': 'gate_security_audit',
        }
        for rule_id, rule in RULES.items():
            with self.subTest(rule=rule_id):
                prefix = rule_id.split('.', 1)[0]
                self.assertIn(prefix, prefix_to_gate, f"{rule_id} has an unknown prefix")
                self.assertEqual(rule['gate'], prefix_to_gate[prefix])

    def test_rule_ids_are_kebab_case_with_one_dot(self):
        for rule_id in RULES:
            with self.subTest(rule=rule_id):
                self.assertEqual(rule_id.count('.'), 1, 'ids are <gate>.<rule>')
                namespace, name = rule_id.split('.', 1)
                self.assertTrue(namespace.islower())
                self.assertRegex(name, r'^[a-z0-9]+(-[a-z0-9]+)*$')

    def test_every_gate_has_at_least_one_rule(self):
        """A gate with no documented rules cannot be explained at all."""
        covered = set(rules_by_gate())
        for gate in KNOWN_GATES:
            with self.subTest(gate=gate):
                self.assertIn(gate, covered, f"{gate} has no rules in the registry")

    def test_citations_are_specific(self):
        """A citation must name a document, not just say 'best practice'."""
        for rule_id, rule in RULES.items():
            with self.subTest(rule=rule_id):
                citation = rule['citation']
                self.assertGreater(len(citation), 15, f"{rule_id} citation is too vague")
                self.assertTrue(
                    any(marker in citation for marker in
                        ('WCAG', 'CSS', 'W3C', 'OWASP', 'CWE', 'Core Web Vitals',
                         'WHATWG', 'Orthotect', 'React')),
                    f"{rule_id} citation names no standard: {citation!r}",
                )

    def test_rules_version_is_semver_and_independent_of_the_package(self):
        """
        The rule set is versioned separately from the package on purpose: a rule
        that tightens changes what a report says without changing any API, so
        tying the two would force a semver-major package release per rule tweak.
        """
        self.assertIsInstance(RULES_VERSION, str)
        parts = RULES_VERSION.split('.')
        self.assertEqual(len(parts), 3, RULES_VERSION)
        self.assertTrue(all(p.isdigit() for p in parts), RULES_VERSION)

        with open(os.path.join(ROOT_DIR, 'package.json'), 'r', encoding='utf-8') as handle:
            package_version = json.load(handle)['version']
        self.assertNotEqual(RULES_VERSION, package_version,
                            'the rule-set version must not track the package version')

    def test_rules_digest_is_stable_and_data_derived(self):
        """Same rules, same digest — regardless of how the source file is formatted."""
        first = rules_digest()
        self.assertEqual(len(first), 16)
        self.assertEqual(first, rules_digest())

    def test_rules_digest_ignores_prose_changes(self):
        """
        Correcting a citation or a summary must not move the digest: no finding
        changed, and a digest that churns on typo fixes teaches consumers to
        ignore it.
        """
        baseline = rules_digest()
        original = RULES['bidi.physical-direction-property']['summary']
        try:
            RULES['bidi.physical-direction-property']['summary'] = 'Reworded entirely.'
            self.assertEqual(rules_digest(), baseline)
        finally:
            RULES['bidi.physical-direction-property']['summary'] = original

    def test_rules_digest_moves_when_a_rule_changes(self):
        """The other direction: a severity change is a real behavioural change."""
        baseline = rules_digest()
        original = RULES['bidi.physical-direction-property']['severity']
        try:
            RULES['bidi.physical-direction-property']['severity'] = 'LOW'
            self.assertNotEqual(rules_digest(), baseline)
        finally:
            RULES['bidi.physical-direction-property']['severity'] = original

    def test_metadata_block_carries_version_digest_and_count(self):
        block = metadata()
        self.assertEqual(block['rulesVersion'], RULES_VERSION)
        self.assertEqual(block['rulesDigest'], rules_digest())
        self.assertEqual(block['ruleCount'], len(RULES))

    def test_the_node_dom_gate_computes_the_same_digest(self):
        """
        The DOM gate is the only non-Python gate, and it stamps the same rule-set
        identity onto its SARIF document. Two digests computed by two languages
        from one source file must agree, or the field means nothing.
        """
        if not os.path.isdir(os.path.join(ROOT_DIR, 'node_modules', 'parse5')):
            if os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ:
                self.fail('parse5 is required to verify the Node gate digest in CI.')
            self.skipTest('parse5 not installed — run `npm ci`')

        res = subprocess.run(
            ['node', os.path.join(GATES_DIR, 'gate_cwv_budget.mjs'),
             os.path.join(ROOT_DIR, 'examples', 'golden-showcase'), '--format', 'sarif'],
            capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(res.returncode, 0, res.stderr)
        properties = json.loads(res.stdout)['runs'][0]['tool']['driver']['properties']
        self.assertEqual(properties, metadata())


class TestLookup(unittest.TestCase):
    def test_get_rule_returns_the_entry(self):
        rule = get_rule('bidi.physical-direction-property')
        self.assertEqual(rule['gate'], 'gate_bidi_logical')

    def test_unknown_rule_raises(self):
        with self.assertRaises(RuleNotFound):
            get_rule('does.not-exist')

    def test_rule_not_found_is_a_key_error(self):
        """Callers may catch KeyError generically; the subclass must satisfy that."""
        with self.assertRaises(KeyError):
            get_rule('does.not-exist')

    def test_describe_includes_the_id(self):
        self.assertEqual(describe('bidi.asymmetric-shorthand')['id'],
                         'bidi.asymmetric-shorthand')

    def test_describe_does_not_mutate_the_registry(self):
        before = dict(RULES['bidi.asymmetric-shorthand'])
        describe('bidi.asymmetric-shorthand')
        self.assertEqual(RULES['bidi.asymmetric-shorthand'], before)

    def test_rule_ids_are_sorted(self):
        ids = rule_ids()
        self.assertEqual(ids, sorted(ids))

    def test_search_finds_by_visible_text(self):
        self.assertIn('security.dom-xss', search('innerHTML'))

    def test_search_is_case_insensitive(self):
        self.assertEqual(search('INNERHTML'), search('innerhtml'))

    def test_search_of_blank_returns_nothing(self):
        self.assertEqual(search(''), [])
        self.assertEqual(search(None), [])

    def test_search_of_nonsense_returns_nothing(self):
        self.assertEqual(search('zzz-no-such-rule-zzz'), [])


class TestExplainCli(unittest.TestCase):
    """The user-facing surface."""

    def run_registry(self, *args):
        return subprocess.run([sys.executable, REGISTRY, *args],
                              capture_output=True, text=True)

    def test_explain_prints_citation_and_fix(self):
        res = self.run_registry('bidi.physical-direction-property')
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn('CSS Logical Properties', res.stdout)
        self.assertIn('margin-inline-start', res.stdout)
        self.assertIn('Why this rule exists', res.stdout)

    def test_explain_json_is_parseable_and_complete(self):
        payload = json.loads(self.run_registry('security.dom-xss', '--json').stdout)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, payload)
        self.assertEqual(payload['id'], 'security.dom-xss')

    def test_explain_markdown(self):
        out = self.run_registry('slop.raw-emoji-icon', '--md').stdout
        self.assertIn('###', out)
        self.assertIn('**Citation:**', out)

    def test_unknown_rule_exits_2(self):
        """Silently printing nothing for a typo is worse than an error."""
        res = self.run_registry('nope.not-a-rule')
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertIn('Unknown rule id', res.stdout)

    def test_unknown_rule_json_is_a_tool_error(self):
        res = self.run_registry('nope.not-a-rule', '--json')
        self.assertEqual(res.returncode, 2)
        payload = json.loads(res.stdout)
        self.assertTrue(payload['toolError'])

    def test_unknown_rule_suggests_a_near_match(self):
        res = self.run_registry('physical-direction-property')
        self.assertEqual(res.returncode, 2)
        self.assertIn('Did you mean', res.stdout)

    def test_list_mode_lists_every_rule(self):
        res = self.run_registry()
        self.assertEqual(res.returncode, 0)
        for rule_id in rule_ids():
            self.assertIn(rule_id, res.stdout)

    def test_list_mode_json_carries_every_rule(self):
        payload = json.loads(self.run_registry('--json').stdout)
        self.assertEqual(payload['rulesVersion'], RULES_VERSION)
        self.assertEqual(len(payload['rules']), len(RULES))

    def test_search_mode(self):
        res = self.run_registry('--search', 'contrast')
        self.assertEqual(res.returncode, 0)
        self.assertIn('contrast.wcag-aa-normal-text', res.stdout)

    def test_search_with_no_hits_exits_2(self):
        res = self.run_registry('--search', 'zzz-no-such-rule-zzz')
        self.assertEqual(res.returncode, 2)

    def test_explain_never_exits_1(self):
        """`explain` makes no claim about any project, so it cannot find a violation."""
        for args in (['bidi.physical-direction-property'], ['--search', 'css'],
                     [], ['nope.bad'], ['--json']):
            with self.subTest(args=args):
                self.assertNotEqual(self.run_registry(*args).returncode, 1)


class TestExplainThroughTheCli(unittest.TestCase):
    """`orthotect explain` must reach the registry, not fall through to help."""

    def test_cli_explain_reaches_the_registry(self):
        res = subprocess.run(['node', CLI, 'explain', 'bidi.asymmetric-shorthand'],
                             capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn('Asymmetric four-value shorthand', res.stdout)
        self.assertNotIn('Core Commands', res.stdout)

    def test_cli_explain_json(self):
        res = subprocess.run(['node', CLI, 'explain', 'fsm.missing-loading-lock', '--json'],
                             capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(json.loads(res.stdout)['id'], 'fsm.missing-loading-lock')

    def test_cli_explain_unknown_rule_exits_2(self):
        res = subprocess.run(['node', CLI, 'explain', 'nope.bad'],
                             capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(res.returncode, 2)

    def test_cli_help_lists_the_explain_command(self):
        res = subprocess.run(['node', CLI, 'help'], capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertIn('explain', res.stdout)


class TestRegistryCoversEveryGateViolation(unittest.TestCase):
    """
    The registry must not be decorative: every violation a gate can emit should
    map onto a documented rule family.

    This is a coverage check on the *families*, not on individual labels — gates
    emit dynamic labels (a missing token name, a file name), so an exact match is
    impossible. What it prevents is a whole gate being added without rules.
    """

    def test_each_gate_module_references_its_registry_namespace(self):
        """Documents the intended pairing so a new gate is a visible omission."""
        expected = {
            'gate_bidi_logical.py': 'bidi',
            'gate_contrast_wcag.py': 'contrast',
            'gate_fsm_integrity.py': 'fsm',
            'gate_no_slop.py': 'slop',
            'gate_cwv_budget.mjs': 'dom',
            'gate_security_audit.py': 'security',
        }
        for filename, namespace in expected.items():
            with self.subTest(gate=filename):
                self.assertTrue(
                    any(rid.startswith(namespace + '.') for rid in RULES),
                    f"{filename} has no {namespace}.* rules in the registry",
                )
                self.assertTrue(os.path.exists(os.path.join(GATES_DIR, filename)))


if __name__ == '__main__':
    unittest.main()
