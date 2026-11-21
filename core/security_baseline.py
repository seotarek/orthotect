#!/usr/bin/env python3
"""
Orthotect Security Baseline
===========================

A committed, reviewable allowlist for security-gate findings.

Why this exists
---------------
REVIEW_2026-11.md C2 removed a blanket `/tests/` path exemption from the SAST
gate, because shipping application code that merely lived under a test-shaped
path was silently un-audited. That was the right call, but it left a real
usability problem: a legitimate fixture — a test that asserts on an XSS payload,
a scanner's own rule table, a deliberately vulnerable example — now blocks the
build, and the only escape was to re-widen path trust, which is precisely the
fail-open the review closed.

A baseline is the narrower instrument. Every suppression is a committed record
(file, rule, line, justification), so it appears in code review, it has an
owner, and it can be audited. Path trust cannot be reviewed; a suppression list
can.

Design rules
------------
* **Fail closed on unreadable policy.** A baseline that exists but cannot be
  parsed or validated is a tool error (exit 2). Proceeding without a policy the
  project asked for would silently re-enable findings that were already reviewed
  and accepted.
* **Stale entries warn; they do not fail.** An entry that matches nothing this
  run is reported, but it does not change the exit code. A stale entry does not
  impair the audit — every file was still scanned and every rule still
  evaluated — so calling it an environment failure would be dishonest, and
  breaking the build on unrelated line shifts would push projects to abandon the
  baseline entirely. Reporting it keeps the file honest without that pressure.
* **Exact matching only.** A suppression matches one file, one rule, and one
  line. There are no globs and no "ignore this rule everywhere" escape, because
  a wildcard suppression reproduces the blanket exemption this module replaced.
  Line `0` means "any line in this file, for this rule" and exists for rules
  whose line number is not stable under edits; it is still scoped to one file
  and one rule, and is deliberately discouraged because a *new* finding of that
  rule in the same file would also be suppressed.
* **Every entry needs a justification.** An entry without a non-empty
  `justification` is rejected, so no suppression can be added without stating
  why. This is the field that makes the file reviewable.
"""

import json
import os

BASELINE_FILENAME = "orthotect-security-baseline.json"

# Bump when the on-disk shape changes incompatibly.
SUPPORTED_BASELINE_VERSION = 1


class BaselineError(Exception):
    """Raised when the baseline file is present but unusable. Always exit 2."""


class BaselineEntry:
    """One reviewed suppression."""

    __slots__ = ("file", "rule", "line", "justification")

    def __init__(self, file, rule, line, justification):
        self.file = file
        self.rule = rule
        self.line = line
        self.justification = justification

    def matches(self, abs_filepath, base_dir, line_no, label):
        """
        Exact match on file, rule and line. `line == 0` is the documented
        "any line in this file for this rule" form.
        """
        if self.rule != label:
            return False
        if self.line != 0 and self.line != line_no:
            return False
        return self.file == _relative_posix(abs_filepath, base_dir)

    def key(self):
        return (self.file, self.rule, self.line)

    def to_dict(self):
        """Serialised form, used by callers that need to echo an entry back."""
        return {
            "file": self.file,
            "rule": self.rule,
            "line": self.line,
            "justification": self.justification,
        }

    def __repr__(self):
        return f"BaselineEntry({self.file!r}, {self.rule!r}, {self.line})"


def _relative_posix(path, base_dir):
    """Normalises a path to a forward-slash path relative to the audit root."""
    try:
        abs_path = os.path.abspath(path)
    except Exception:
        abs_path = path
    if base_dir:
        try:
            rel = os.path.relpath(abs_path, os.path.abspath(base_dir))
        except ValueError:
            # Different drives on Windows: fall back to the absolute path.
            rel = abs_path
    else:
        rel = abs_path
    return rel.replace('\\', '/')


def find_baseline_path(target_path, base_dir=None):
    """
    Resolves the baseline for an audit.

    Lookup order:
      1. `<audit root>/orthotect-security-baseline.json`
      2. `<audit root parent>/orthotect-security-baseline.json`
    Returns None when nothing exists. A baseline in a parent directory is
    honoured so that a monorepo can hold one baseline for the whole tree.
    """
    root = os.path.abspath(base_dir or target_path)
    candidates = [
        os.path.join(root, BASELINE_FILENAME),
    ]
    if os.path.isdir(root):
        candidates.append(os.path.join(os.path.dirname(root), BASELINE_FILENAME))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def load_baseline(path):
    """
    Parses and structurally validates a baseline file.

    Raises BaselineError for anything unusable. Every failure mode here is a tool
    error: a security audit must never proceed on a baseline it could not read,
    because that would silently re-enable the findings the baseline suppressed.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise BaselineError(f"baseline file not found: {path}")
    except json.JSONDecodeError as e:
        raise BaselineError(f"baseline is not valid JSON ({path}): {e}")
    except OSError as e:
        raise BaselineError(f"baseline could not be read ({path}): {e}")

    if not isinstance(raw, dict):
        raise BaselineError(f"baseline root must be a JSON object ({path})")

    version = raw.get("version")
    if version != SUPPORTED_BASELINE_VERSION:
        raise BaselineError(
            f"baseline version {version!r} is unsupported; expected "
            f"{SUPPORTED_BASELINE_VERSION} ({path})"
        )

    entries_raw = raw.get("suppressions")
    if entries_raw is None:
        entries_raw = []
    if not isinstance(entries_raw, list):
        raise BaselineError(f"baseline 'suppressions' must be a list ({path})")

    entries = []
    seen = set()
    for index, item in enumerate(entries_raw):
        where = f"suppressions[{index}]"
        if not isinstance(item, dict):
            raise BaselineError(f"{where} must be an object ({path})")

        file_val = item.get("file")
        if not isinstance(file_val, str) or not file_val.strip():
            raise BaselineError(f"{where}.file must be a non-empty string ({path})")
        if os.path.isabs(file_val) or '\\' in file_val:
            raise BaselineError(
                f"{where}.file must be a repo-relative forward-slash path, got {file_val!r} ({path})"
            )
        if '*' in file_val or '?' in file_val:
            raise BaselineError(
                f"{where}.file must name one file; glob suppressions would "
                f"reproduce the blanket exemption this baseline replaced ({path})"
            )

        rule_val = item.get("rule")
        if not isinstance(rule_val, str) or not rule_val.strip():
            raise BaselineError(f"{where}.rule must be a non-empty string ({path})")
        if '*' in rule_val or '?' in rule_val:
            raise BaselineError(
                f"{where}.rule must name one rule exactly, not a pattern ({path})"
            )

        line_val = item.get("line", 0)
        if not isinstance(line_val, int) or isinstance(line_val, bool) or line_val < 0:
            raise BaselineError(
                f"{where}.line must be a non-negative integer ({path})"
            )

        justification = item.get("justification")
        if not isinstance(justification, str) or not justification.strip():
            raise BaselineError(
                f"{where}.justification must be a non-empty string; every "
                f"suppression must state why it is safe ({path})"
            )

        entry = BaselineEntry(file_val, rule_val, line_val, justification.strip())
        if entry.key() in seen:
            raise BaselineError(
                f"{where} duplicates an earlier suppression for "
                f"{entry.file}:{entry.line} ({entry.rule}) ({path})"
            )
        seen.add(entry.key())
        entries.append(entry)

    return entries


def apply_baseline(findings_by_file, entries, base_dir):
    """
    Splits findings into (surviving, suppressed).

    `findings_by_file` is the gate's `{abs_path: [(line, label, severity, snippet)]}`.
    Returns `(surviving, suppressed)` where both are the same mapping shape and
    `suppressed` records the entry that removed each finding, so the report can
    show what was exempted and why.
    """
    surviving = {}
    suppressed = {}
    for filepath, findings in findings_by_file.items():
        for finding in findings:
            line_no, label = finding[0], finding[1]
            hit = next((e for e in entries if e.matches(filepath, base_dir, line_no, label)), None)
            if hit is None:
                surviving.setdefault(filepath, []).append(finding)
            else:
                suppressed.setdefault(filepath, []).append((finding, hit))
    return surviving, suppressed


def unused_entries(entries, suppressed):
    """
    Entries that matched nothing during this run.

    A stale suppression is not harmless: it is a claim in the repository that a
    finding is reviewed and safe, while the code has moved on. Reporting them
    keeps the file honest. Returned sorted for deterministic output.
    """
    used = {entry.key() for _filepath, pairs in suppressed.items() for _finding, entry in pairs}
    stale = [e for e in entries if e.key() not in used]
    return sorted(stale, key=lambda e: (e.file, e.line, e.rule))
