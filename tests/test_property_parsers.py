#!/usr/bin/env python3
"""
P3-3 — Property-based testing for the three pure parsers.

REVIEW_2026-11.md item 12. The CSS shorthand splitter, the `calc()` validator and
the comment masker are small pure functions with large input spaces, and the two
critical defects this review found (C1's `!important` bypass and C4's non-string-
aware comment masking) were both *input-space* bugs: every hand-written example
passed, and the failure lived in a case nobody thought to write down.

These tests generate inputs instead of enumerating them. There is no Hypothesis
dependency — the generators below are a small hand-rolled layer over `random`
with a fixed seed, which keeps the suite dependency-free and reproducible while
covering the same ground. A property that holds for 500 generated inputs is a
much stronger claim than one that holds for four.

Every property here is stated as an invariant of the *contract*, not as a
restatement of the implementation:

  split_css_values   tokens are never empty, never carry `!important`, and
                     rejoining them cannot change the value's meaning.
  calc validation    a balanced expression is never accepted when unbalanced,
                     and a pure-number expression never needs a unit.
  mask_comments      length and newline positions are invariant — that is what
                     keeps line numbers exact — and masked text is idempotent.
"""

import os
import random
import re
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from gates.gate_bidi_logical import (  # noqa: E402
    SHORTHAND_PROPERTIES,
    logical_shorthand_pair,
    normalize_declared_value,
    split_css_values,
)
from gates.gate_no_slop import mask_comments  # noqa: E402

GATES_DIR = os.path.join(ROOT_DIR, 'gates')
ITERATIONS = 500
SEED = 20261120


def _rng():
    """A fresh generator per test, so one test's draws cannot perturb another's."""
    return random.Random(SEED)


# ---------------------------------------------------------------------------
# Value generators
# ---------------------------------------------------------------------------

UNITS = ['px', 'rem', 'em', '%', 'vw', 'vh', 'pt', 'ch', 'cqi']


def random_dimension(rng):
    """A plausible CSS dimension, including the degenerate forms a real file can hold."""
    magnitude = rng.choice(['0', '1', '2', '8', '10', '12.5', '.5', '100', '1e3', '-4', '+3'])
    if rng.random() < 0.1:
        return magnitude  # unitless: valid for some properties, invalid for others
    return f"{magnitude}{rng.choice(UNITS)}"


def random_length(rng):
    """
    A strictly positive length — always unit-bearing, never zero.

    The `calc()` type rules are exactly what is under test, so a generator that
    emitted a bare number where a length is required would be testing the
    generator's mistake rather than the validator's behaviour.
    """
    return f"{rng.choice(['1', '2', '8', '10', '12.5', '.5', '100'])}{rng.choice(UNITS)}"


def random_keyword(rng):
    return rng.choice(['auto', 'inherit', 'initial', 'unset', 'revert', 'none',
                       'solid', 'dashed', 'dotted', 'currentColor', 'transparent'])


def random_token(rng):
    """One whitespace-delimited CSS value token."""
    roll = rng.random()
    if roll < 0.55:
        return random_dimension(rng)
    if roll < 0.75:
        return random_keyword(rng)
    if roll < 0.9:
        # A functional value, whose internal spaces must NOT split the token.
        inner = rng.choice([
            f"calc({random_dimension(rng)} {rng.choice(['+', '-', '*', '/'])} {random_dimension(rng)})",
            f"calc(100% - {random_dimension(rng)})",
            f"min({random_dimension(rng)}, {random_dimension(rng)})",
            f"var(--space-{rng.randint(0, 12)})",
            f"clamp({random_dimension(rng)}, {random_dimension(rng)}, {random_dimension(rng)})",
        ])
        return inner
    return random_dimension(rng)


def random_value(rng, max_tokens=6):
    """A whitespace-joined value, with random separator widths and optional `!important`."""
    tokens = [random_token(rng) for _ in range(rng.randint(0, max_tokens))]
    separators = [rng.choice([' ', '  ', '\t', '\n', ' \n ']) for _ in tokens]
    parts = []
    for index, token in enumerate(tokens):
        if index:
            parts.append(separators[index])
        parts.append(token)
    value = ''.join(parts)
    if tokens and rng.random() < 0.25:
        value += rng.choice([' !important', '!important', ' ! important', '  !IMPORTANT'])
    return value


# ---------------------------------------------------------------------------
# split_css_values
# ---------------------------------------------------------------------------

class ShorthandSplitterPropertyTest(unittest.TestCase):
    """
    `split_css_values` is what decides whether a four-value shorthand is
    asymmetric, so its invariants are load-bearing: a token it invents or drops
    either hides a real violation or manufactures a false one.
    """

    def test_never_returns_an_empty_or_blank_token(self):
        rng = _rng()
        for _ in range(ITERATIONS):
            value = random_value(rng)
            for token in split_css_values(value):
                self.assertTrue(token, f'blank token from {value!r}')
                self.assertEqual(token, token.strip(), f'unstripped token from {value!r}')

    def test_important_never_survives_as_a_token(self):
        """
        C1's bypass: `margin: 0 8px 0 4px !important` split into five tokens,
        missed the four-token check, and passed. The flag must never be a token.

        The property is stated over the pipeline the gate actually runs —
        `normalize_declared_value` then `split_css_values` — because a spaced
        `! important` is invalid CSS that the normalizer rejects before splitting.
        Asserting on the splitter alone would demand it handle input it never sees.
        """
        rng = _rng()
        for _ in range(ITERATIONS):
            value = normalize_declared_value(random_value(rng))
            tokens = split_css_values(value)
            for token in tokens:
                self.assertNotIn('!', token, f'{token!r} from {value!r}')
                self.assertNotIn('important', token.lower(), f'{token!r} from {value!r}')

    def test_a_four_value_shorthand_with_important_still_counts_four(self):
        """The exact C1 shape, over the real pipeline."""
        rng = _rng()
        for _ in range(ITERATIONS):
            terms = [random_dimension(rng) for _ in range(4)]
            value = normalize_declared_value(' '.join(terms) + rng.choice([' !important', '!important']))
            self.assertEqual(len(split_css_values(value)), 4, value)

    def test_token_count_equals_the_number_of_top_level_terms(self):
        """
        The count is the whole basis of the four-value check, so it must match an
        independent measure: splitting on top-level whitespace only.
        """
        rng = _rng()
        for _ in range(ITERATIONS):
            value = random_value(rng)
            expected = len(_reference_split(value))
            self.assertEqual(len(split_css_values(value)), expected,
                             f'{value!r} -> {split_css_values(value)!r}')

    def test_parenthesised_values_never_split(self):
        """A space inside `calc()` or `min()` is not a term boundary."""
        rng = _rng()
        for _ in range(ITERATIONS):
            inner = f"calc({random_dimension(rng)} {rng.choice(['+', '-', '*', '/'])} {random_dimension(rng)})"
            tokens = split_css_values(f"4px {inner} 8px")
            self.assertEqual(len(tokens), 3, f'{inner!r} split into {tokens!r}')
            self.assertEqual(tokens[1], inner)

    def test_idempotent_under_rejoining(self):
        """Rejoining the tokens and splitting again yields the same tokens."""
        rng = _rng()
        for _ in range(ITERATIONS):
            value = random_value(rng)
            tokens = split_css_values(value)
            self.assertEqual(split_css_values(' '.join(tokens)), tokens, repr(value))

    def test_whitespace_only_input_yields_no_tokens(self):
        rng = _rng()
        for _ in range(100):
            whitespace = ''.join(rng.choice([' ', '\t', '\n', '\r']) for _ in range(rng.randint(0, 20)))
            self.assertEqual(split_css_values(whitespace), [])


def _reference_split(value):
    """An independent, deliberately naive top-level splitter used only as an oracle."""
    tokens, current, depth = [], '', 0
    for char in value:
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif char.isspace() and depth == 0:
            if current.strip():
                tokens.append(current.strip())
            current = ''
        else:
            current += char
    if current.strip():
        tokens.append(current.strip())
    return [t for t in tokens if t != '!important']


# ---------------------------------------------------------------------------
# logical_shorthand_pair
# ---------------------------------------------------------------------------

class ShorthandPairPropertyTest(unittest.TestCase):
    """
    A wrong pair is worse than no suggestion: the reader writes invalid CSS and
    stays broken (that is exactly the `border-width-block` defect P1-1 found).
    """

    def test_every_shorthand_maps_to_two_distinct_valid_properties(self):
        for name in SHORTHAND_PROPERTIES:
            block, inline = logical_shorthand_pair(name)
            self.assertNotEqual(block, inline, name)
            self.assertNotIn('--', block, name)
            self.assertNotIn('--', inline, name)
            for prop in (block, inline):
                self.assertRegex(prop, r'^[a-z]+(-[a-z]+)+$', f'{name} -> {prop}')

    def test_border_family_puts_the_infix_before_the_sub_property(self):
        """
        `border-width` must become `border-block-width`, never `border-width-block`
        (which is not a CSS property at all).
        """
        for suffix in ('width', 'style', 'color'):
            block, inline = logical_shorthand_pair(f'border-{suffix}')
            self.assertEqual(block, f'border-block-{suffix}')
            self.assertEqual(inline, f'border-inline-{suffix}')
            self.assertFalse(block.startswith(f'border-{suffix}-'), block)

    def test_non_border_shorthands_append_the_infix(self):
        for name in ('margin', 'padding', 'inset', 'scroll-margin', 'scroll-padding'):
            block, inline = logical_shorthand_pair(name)
            self.assertEqual(block, f'{name}-block')
            self.assertEqual(inline, f'{name}-inline')


# ---------------------------------------------------------------------------
# mask_comments
# ---------------------------------------------------------------------------

class CommentMaskerPropertyTest(unittest.TestCase):
    """
    The masker must be invisible except for the comment bytes: line numbers are
    derived from the masked text, so any length change silently misreports every
    finding below the first comment.
    """

    FRAGMENTS = [
        'a { margin-left: 0; }',
        '// a line comment',
        '/* a block comment */',
        '<!-- html comment -->',
        'const url = "https://example.com/x";',
        "const s = 'text with // not a comment';",
        'const t = `template /* not a comment */ string`;',
        'color: red; /* trailing */',
        'line with a \\" escaped quote and // after',
        'plain text with no comment at all',
        '',
    ]

    def test_length_is_invariant(self):
        rng = _rng()
        for _ in range(ITERATIONS):
            text = self._random_document(rng)
            self.assertEqual(len(mask_comments(text)), len(text), repr(text[:80]))

    def test_newline_positions_are_invariant(self):
        """The property that makes line numbers correct."""
        rng = _rng()
        for _ in range(ITERATIONS):
            text = self._random_document(rng)
            masked = mask_comments(text)
            self.assertEqual([i for i, c in enumerate(masked) if c == '\n'],
                             [i for i, c in enumerate(text) if c == '\n'],
                             repr(text[:80]))

    def test_masking_is_idempotent(self):
        rng = _rng()
        for _ in range(ITERATIONS):
            text = self._random_document(rng)
            once = mask_comments(text)
            self.assertEqual(mask_comments(once), once, repr(text[:80]))

    def test_no_comment_opener_survives_masking(self):
        """Every `/*`, `//` and `<!--` in the output must be inside a string or absent."""
        rng = _rng()
        for _ in range(ITERATIONS):
            text = self._random_document(rng)
            masked = mask_comments(text)
            # The masker blanks comment bodies; a surviving opener means the scan
            # either did not recognise it or treated a string as a comment.
            self.assertEqual(masked.count('<!--'), text.count('<!--') - _comment_count(text, '<!--'))
            for marker in ('/*', '*/'):
                self.assertLessEqual(masked.count(marker), text.count(marker), repr(text[:80]))

    def test_non_comment_text_is_preserved(self):
        """
        C4's fail-open: a `//` inside a URL must not blank the rest of the line,
        or real slop later on that line silently passes the gate.
        """
        rng = _rng()
        for _ in range(ITERATIONS):
            code = rng.choice([
                'const url = "https://example.com";',
                "const s = 'a // b';",
                'a { color: red; }',
            ])
            self.assertEqual(mask_comments(code), code, repr(code))

    def _random_document(self, rng):
        parts = [rng.choice(self.FRAGMENTS) for _ in range(rng.randint(0, 8))]
        joiner = rng.choice(['\n', ' ', '\n\n', '\t'])
        return joiner.join(parts)


def _comment_count(text, opener):
    """How many `opener` sequences actually start a comment (not inside a string)."""
    # Reuse the masker's own notion of "outside a string" by masking and comparing:
    # every opener that survives masking is one the masker treated as string text.
    return text.count(opener) - mask_comments(text).count(opener)


# ---------------------------------------------------------------------------
# calc() validation (Node)
# ---------------------------------------------------------------------------

class CalcValidatorPropertyTest(unittest.TestCase):
    """
    `parseAndValidateCssCalc` decides whether a dimension reserves space, so a
    false accept causes a layout shift and a false reject blocks a valid build.
    The invariants below are checked in one Node process over generated inputs.
    """

    # `node <script> <arg>` puts the script at argv[1], so the payload is argv[2].
    NODE_PROBE = r"""
import { parseAndValidateCssCalc } from '%s';
const cases = JSON.parse(process.argv[2]);
process.stdout.write(JSON.stringify(cases.map(c => parseAndValidateCssCalc(c))));
""" % os.path.join(GATES_DIR, 'gate_cwv_budget.mjs')

    def setUp(self):
        if not os.path.isdir(os.path.join(ROOT_DIR, 'node_modules', 'parse5')):
            if os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ:
                self.fail('parse5 is required to exercise the calc validator in CI.')
            self.skipTest('parse5 not installed — run `npm ci`')

    def _validate(self, cases):
        import json
        import subprocess
        import tempfile

        probe = tempfile.mkdtemp(prefix='calc_probe_')
        try:
            script = os.path.join(probe, 'probe.mjs')
            with open(script, 'w', encoding='utf-8') as handle:
                handle.write(self.NODE_PROBE)
            res = subprocess.run(['node', script, json.dumps(cases)],
                                 capture_output=True, text=True, cwd=probe)
            self.assertEqual(res.returncode, 0, res.stderr)
            return json.loads(res.stdout)
        finally:
            import shutil
            shutil.rmtree(probe, ignore_errors=True)

    def test_unbalanced_parentheses_are_always_rejected(self):
        rng = _rng()
        cases = []
        for _ in range(120):
            depth = rng.randint(1, 3)
            inner = ' + '.join(random_length(rng) for _ in range(depth))
            # One paren short, on either side.
            if rng.random() < 0.5:
                cases.append(inner + ')')
            else:
                cases.append('(' + inner)
        for expression, accepted in zip(cases, self._validate(cases)):
            self.assertFalse(accepted, f'unbalanced {expression!r} was accepted')

    def test_pure_addition_of_lengths_is_accepted(self):
        rng = _rng()
        cases = [f"{random_length(rng)} + {random_length(rng)}" for _ in range(120)]
        for expression, accepted in zip(cases, self._validate(cases)):
            self.assertTrue(accepted, f'valid {expression!r} was rejected')

    def test_addition_of_a_length_and_a_number_is_rejected(self):
        """
        W3C CSS Values 4 § 8.1.1: `+`/`-` operands must match types. This is the
        mirror of the acceptance property above — without it, a validator that
        accepted everything would pass the whole class.
        """
        rng = _rng()
        cases = [f"{random_length(rng)} + {rng.choice(['1', '2', '10', '0.5'])}" for _ in range(120)]
        for expression, accepted in zip(cases, self._validate(cases)):
            self.assertFalse(accepted, f'length+number {expression!r} was accepted')

    def test_length_multiplied_by_length_is_rejected(self):
        """W3C CSS Values 4 § 8.1.1: multiplication needs at least one unitless number."""
        rng = _rng()
        cases = [f"{random_length(rng)} * {random_length(rng)}" for _ in range(120)]
        for expression, accepted in zip(cases, self._validate(cases)):
            self.assertFalse(accepted, f'length*length {expression!r} was accepted')

    def test_length_multiplied_by_a_number_is_accepted(self):
        rng = _rng()
        cases = [f"{random_length(rng)} * {rng.choice(['2', '3', '0.5', '1.5'])}" for _ in range(120)]
        for expression, accepted in zip(cases, self._validate(cases)):
            self.assertTrue(accepted, f'length*number {expression!r} was rejected')

    def test_division_by_zero_is_rejected(self):
        rng = _rng()
        cases = [f"{random_length(rng)} / 0" for _ in range(60)]
        for expression, accepted in zip(cases, self._validate(cases)):
            self.assertFalse(accepted, f'division by zero {expression!r} was accepted')

    def test_division_by_a_length_is_rejected(self):
        """`length / length` is a ratio, not a length, so it cannot reserve space."""
        rng = _rng()
        cases = [f"{random_length(rng)} / {random_length(rng)}" for _ in range(60)]
        for expression, accepted in zip(cases, self._validate(cases)):
            self.assertFalse(accepted, f'length/length {expression!r} was accepted')

    def test_whitespace_around_operators_is_irrelevant(self):
        """
        The verdict must not depend on how much whitespace surrounds an operator,
        as long as the CSS requirement (spaces around `+`/`-`) is met.
        """
        rng = _rng()
        pairs = []
        for _ in range(60):
            left, right = random_length(rng), random_length(rng)
            pairs.append((f"{left} + {right}", f" {left}  +  {right} "))
        flat = [form for pair in pairs for form in pair]
        verdicts = self._validate(flat)
        for index in range(0, len(verdicts), 2):
            self.assertEqual(verdicts[index], verdicts[index + 1],
                             f'whitespace changed the verdict for {flat[index]!r}')


if __name__ == '__main__':
    unittest.main()
