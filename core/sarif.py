#!/usr/bin/env python3
"""
Orthotect SARIF Export
======================

Converts gate findings into SARIF 2.1.0, the format GitHub Code Scanning reads.
That is the difference between a gate result that lives in a CI log nobody opens
and an inline annotation on the pull request that introduced the defect.

Design notes
------------
* **One run, one tool.** All findings from one audit go into a single `runs[]`
  entry with a shared `rules[]` catalogue, which is what GitHub expects. Emitting
  one run per gate makes the code-scanning UI show the same file six times.
* **Stable rule ids.** `ruleId` comes from `core/rule_registry.py`, so a
  suppression, a SARIF alert and an `orthotect explain` invocation all name the
  same thing. Gates that emit dynamic labels (a missing token name, a filename)
  fall back to a synthetic id derived from the gate, which is still stable across
  runs because it is keyed on the label's leading family rather than the whole
  string.
* **Severity mapping is explicit.** SARIF's `level` is only `error`/`warning`/
  `note`. Mapping CRITICAL and HIGH to `error` and everything else to `warning`
  keeps GitHub's default "fail on error" behaviour aligned with Orthotect's own
  exit-code contract: anything that exits 1 shows up as an error annotation.
* **Relative URIs.** GitHub resolves artifact locations against the repository
  root, so paths must be relative and forward-slashed. An absolute path produces
  an annotation that silently never attaches to a file.
* **A gate that could not run is still visible.** A tool error contributes an
  `invocations[].toolExecutionNotifications` entry rather than an empty result
  set, because "no findings" and "no analysis" must never look the same.
"""

import json
import os

SARIF_VERSION = '2.1.0'
SARIF_SCHEMA = 'https://json.schemastore.org/sarif-2.1.0.json'
TOOL_NAME = 'orthotect'
TOOL_URI = 'https://github.com/seotarek/orthotect'

#: Severities that must fail a build. Anything else is advisory.
ERROR_LEVEL_SEVERITIES = ('CRITICAL', 'HIGH')


def _rule_id_for(gate, label):
    """
    Fallback rule id for a finding no gate classified explicitly.

    Gates emit dynamic labels (`Missing required FSM specifications`, a token
    name, a filename), so an exact registry match is not always possible. The
    fallback id is derived from the gate plus a slug of the label's first few
    words, which is stable across runs — SARIF consumers key alert state on
    `ruleId`, so an unstable id would re-open the same alert every build.
    """
    gate_slug = (str(gate).replace('gate_', '').replace('_', '-')
                 .replace('.mjs', '').replace('.py', ''))
    words = ''.join(ch if ch.isalnum() or ch == ' ' else ' ' for ch in str(label)).lower().split()
    label_slug = '-'.join(words[:6]) or 'finding'
    return f"{gate_slug or 'orthotect'}.{label_slug}"


def _level_for(severity):
    """SARIF has three levels; Orthotect has four. Map conservatively."""
    return 'error' if str(severity).upper() in ERROR_LEVEL_SEVERITIES else 'warning'


def _relativize(path, base_dir):
    """Repo-relative, forward-slash path. Absolute paths never attach in GitHub."""
    try:
        rel = os.path.relpath(os.path.abspath(path), os.path.abspath(base_dir or '.'))
    except (ValueError, TypeError):
        rel = str(path)
    return rel.replace('\\', '/')


def _rule_name(rule_id):
    """SARIF `name` should be a PascalCase identifier."""
    parts = [p for p in str(rule_id).replace('.', '-').split('-') if p]
    return ''.join(p[:1].upper() + p[1:] for p in parts) or 'Finding'


def _rule_entry(rule_id, label, severity, registry_get, gate):
    """Builds one `rules[]` entry, enriched from the registry when it is available."""
    entry = {
        'id': rule_id,
        'name': _rule_name(rule_id),
        'shortDescription': {'text': str(label)},
        'defaultConfiguration': {'level': _level_for(severity)},
        'helpUri': f"{TOOL_URI}#{rule_id}",
    }
    rule = None
    if registry_get:
        try:
            rule = registry_get(rule_id)
        except Exception:
            rule = None
    if rule:
        entry['fullDescription'] = {'text': rule.get('summary', str(label))}
        entry['help'] = {
            'text': f"{rule.get('summary', '')}\n\nFix: {rule.get('fix', '')}".strip(),
        }
        entry['properties'] = {
            'citation': rule.get('citation', ''),
            'gate': rule.get('gate', gate),
            'severity': rule.get('severity', severity),
        }
    return entry


def build_sarif(findings, base_dir, gate='orthotect', tool_version='0.0.0',
                registry_get=None, notifications=None):
    """
    Builds a SARIF 2.1.0 document.

    `findings` is a list of dicts with at least `file`, `line` and `label`, and
    optionally `column`, `severity`, `snippet`, `suggestion`, `ruleId` and
    `suppressions` (a list of `{'justification': str}`).

    `notifications` is a list of `{'message': str, 'level': 'error'|'warning'|
    'note'}` describing gates that could not run. They are emitted as
    `invocations[].toolExecutionNotifications`, so a tool error is visible in the
    code-scanning UI instead of looking like a clean audit.

    Returns a dict ready for `json.dumps`.
    """
    rules = {}
    results = []

    for finding in findings:
        filepath = finding.get('file', '')
        line = finding.get('line', 0) or 0
        column = finding.get('column', 0) or 0
        label = finding.get('label', 'finding')

        rule_id = finding.get('ruleId') or _rule_id_for(gate, label)
        severity = finding.get('severity')
        if not severity:
            # The registry is the authority when the gate did not state a
            # severity: it is the same table `orthotect explain` prints, so the
            # annotation level in GitHub cannot contradict the documentation.
            severity = 'MEDIUM'
            if registry_get:
                try:
                    severity = registry_get(rule_id).get('severity', severity)
                except Exception:
                    pass

        if rule_id not in rules:
            rules[rule_id] = _rule_entry(rule_id, label, severity, registry_get, gate)

        message = str(label)
        if finding.get('snippet'):
            message = f"{message}: {finding['snippet']}"
        if finding.get('suggestion'):
            message = f"{message} — {finding['suggestion']}"

        region = {'startLine': max(int(line), 1)}
        if column:
            region['startColumn'] = max(int(column), 1)

        result = {
            'ruleId': rule_id,
            'level': _level_for(severity),
            'message': {'text': message},
            'locations': [{
                'physicalLocation': {
                    'artifactLocation': {'uri': _relativize(filepath, base_dir)},
                    'region': region,
                },
            }],
            'properties': {'severity': severity, 'gate': gate},
        }

        suppressions = finding.get('suppressions')
        if suppressions:
            result['suppressions'] = [
                {'kind': 'external', 'justification': str(s.get('justification', ''))}
                for s in suppressions
            ]

        results.append(result)

    run = {
        'tool': {
            'driver': _driver(rules, tool_version),
        },
        'results': results,
        'columnKind': 'utf16CodeUnits',
    }

    if notifications:
        run['invocations'] = [{
            'executionSuccessful': False,
            'toolExecutionNotifications': [
                {
                    'level': n.get('level', 'error'),
                    'message': {'text': str(n.get('message', ''))},
                }
                for n in notifications
            ],
        }]
    else:
        run['invocations'] = [{'executionSuccessful': True}]

    return {
        '$schema': SARIF_SCHEMA,
        'version': SARIF_VERSION,
        'runs': [run],
    }


def merge_sarif(documents, tool_version='0.0.0', notifications=None):
    """
    Folds several single-gate SARIF documents into one run.

    GitHub keys its code-scanning alerts on `ruleId` within a run, so six runs
    would show the same rule six times. One run with a unioned rule catalogue is
    the shape the code-scanning UI is designed for. Duplicate rules keep the
    first definition; duplicate results are dropped, because a gate that ran
    twice on the same file must not double-annotate it.
    """
    rules = {}
    results = []
    seen = set()
    all_notifications = list(notifications or [])

    for document in documents:
        if not document:
            continue
        for run in document.get('runs', []) or []:
            driver = run.get('tool', {}).get('driver', {})
            for rule in driver.get('rules', []) or []:
                rules.setdefault(rule['id'], rule)
            for result in run.get('results', []) or []:
                locations = result.get('locations') or [{}]
                physical = locations[0].get('physicalLocation', {}) if locations else {}
                key = (
                    result.get('ruleId'),
                    physical.get('artifactLocation', {}).get('uri'),
                    physical.get('region', {}).get('startLine'),
                    physical.get('region', {}).get('startColumn'),
                    result.get('message', {}).get('text'),
                )
                if key in seen:
                    continue
                seen.add(key)
                results.append(result)
            for invocation in run.get('invocations', []) or []:
                all_notifications.extend(
                    invocation.get('toolExecutionNotifications', []) or [])

    merged_run = {
        'tool': {
            'driver': _driver(rules, tool_version),
        },
        'results': results,
        'columnKind': 'utf16CodeUnits',
        'invocations': [{
            'executionSuccessful': not all_notifications,
            'toolExecutionNotifications': all_notifications,
        }],
    }

    return {
        '$schema': SARIF_SCHEMA,
        'version': SARIF_VERSION,
        'runs': [merged_run],
    }


def dump_sarif(document, pretty=True):
    """Serialises a SARIF document. Stable key order keeps diffs reviewable."""
    return json.dumps(document, indent=2 if pretty else None, sort_keys=False)


def _driver(rules, tool_version):
    """
    Builds the SARIF `tool.driver` object.

    `rules` is the id -> entry map. The rule-set version travels in
    `driver.properties`, because SARIF has no first-class slot for "the rule
    catalogue changed but the tool did not": a consumer reading the document
    needs to know whether two reports used the same rules, and the package
    version alone cannot tell them that.
    """
    driver = {
        'name': TOOL_NAME,
        'informationUri': TOOL_URI,
        'version': str(tool_version),
        'rules': [rules[k] for k in sorted(rules)],
    }
    metadata = rule_set_metadata()
    if metadata:
        driver['properties'] = metadata
    return driver


def tool_version():
    """
    The Orthotect version, read from the package manifest.

    Read here rather than passed in so every gate stamps the same value without
    six copies of the lookup. Falls back to '0.0.0' when the manifest is not
    reachable (a vendored copy of the gates), which is honest: an unknown version
    must not be reported as a real one.
    """
    manifest = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'package.json'))
    try:
        with open(manifest, 'r', encoding='utf-8') as handle:
            return str(json.load(handle).get('version') or '0.0.0')
    except Exception:
        return '0.0.0'


def _classifier():
    """Returns `classify_label` from the registry, or None when it is unavailable."""
    try:
        from core.rule_registry import classify_label
        return classify_label
    except ImportError:
        try:
            import sys
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if root not in sys.path:
                sys.path.insert(0, root)
            from core.rule_registry import classify_label
            return classify_label
        except Exception:
            return None


def _registry_getter():
    """Returns `get_rule` from the registry, or None when it is unavailable."""
    try:
        from core.rule_registry import get_rule
        return get_rule
    except ImportError:
        try:
            import sys
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if root not in sys.path:
                sys.path.insert(0, root)
            from core.rule_registry import get_rule
            return get_rule
        except Exception:
            return None


def rule_set_metadata():
    """
    The rule-set version block, or an empty dict when the registry is unavailable.

    Empty rather than a placeholder: a made-up version in a published report is
    worse than an absent one, because it looks pinnable and is not.
    """
    try:
        from core.rule_registry import metadata
        return metadata()
    except ImportError:
        try:
            import sys
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if root not in sys.path:
                sys.path.insert(0, root)
            from core.rule_registry import metadata
            return metadata()
        except Exception:
            return {}


def gate_document(gate, findings, base_dir, tool_error=None):
    """
    Builds the SARIF document for one gate.

    `findings` is a list of dicts with `file`, `line`, optional `column`,
    `label`, `severity`, `snippet` and `suggestion`. Each is classified against
    the registry so `ruleId` matches what `orthotect explain` documents.

    `tool_error` is an optional message: when the gate could not run, the
    document records it as a tool execution notification, because "no findings"
    and "no analysis" must never produce the same report.
    """
    classify = _classifier()
    resolved = []
    for finding in findings:
        entry = dict(finding)
        if not entry.get('ruleId') and classify:
            entry['ruleId'] = classify(gate, entry.get('label', ''))
        resolved.append(entry)

    notifications = None
    if tool_error:
        notifications = [{'message': tool_error, 'level': 'error'}]

    return build_sarif(
        resolved,
        base_dir,
        gate=gate,
        tool_version=tool_version(),
        registry_get=_registry_getter(),
        notifications=notifications,
    )


def print_gate_sarif(gate, findings, base_dir, tool_error=None):
    """Prints one gate's SARIF document to stdout."""
    print(dump_sarif(gate_document(gate, findings, base_dir, tool_error)))


def sarif_requested(argv):
    """
    True when the caller asked for SARIF.

    Accepts `--sarif`, `--format sarif` and `--format=sarif`. Kept here rather
    than in `core/cli_args.py` because it answers a different question: that
    module splits argv, this one decides whether stdout must be a JSON document
    instead of a report — a decision every gate has to make identically or the
    merged output is corrupt.
    """
    for index, token in enumerate(argv):
        if token == '--sarif':
            return True
        if token == '--format' and index + 1 < len(argv):
            if str(argv[index + 1]).strip().lower() == 'sarif':
                return True
        if token.startswith('--format='):
            if token.split('=', 1)[1].strip().lower() == 'sarif':
                return True
    return False


def validate_sarif(document):
    """
    Structural validation against the SARIF 2.1.0 required shape.

    Deliberately not a full JSON-Schema validation: the schema is large, and the
    fields GitHub actually rejects a document for are the required top-level
    ones plus a well-formed run/tool/result chain. Returns a list of problems;
    empty means structurally sound.
    """
    problems = []
    if not isinstance(document, dict):
        return ['SARIF document must be an object']
    if document.get('version') != SARIF_VERSION:
        problems.append(f"version must be {SARIF_VERSION!r}")
    if not document.get('$schema'):
        problems.append('$schema is required')
    runs = document.get('runs')
    if not isinstance(runs, list) or not runs:
        return problems + ['runs must be a non-empty list']

    for index, run in enumerate(runs):
        driver = run.get('tool', {}).get('driver')
        if not isinstance(driver, dict):
            problems.append(f"runs[{index}].tool.driver is required")
            continue
        if not driver.get('name'):
            problems.append(f"runs[{index}].tool.driver.name is required")
        declared_rules = driver.get('rules', [])
        if not isinstance(declared_rules, list):
            problems.append(f"runs[{index}].tool.driver.rules must be a list")
            declared_rules = []
        declared_ids = {r.get('id') for r in declared_rules if isinstance(r, dict)}

        results = run.get('results')
        if not isinstance(results, list):
            problems.append(f"runs[{index}].results must be a list")
            continue
        for r_index, result in enumerate(results):
            where = f"runs[{index}].results[{r_index}]"
            rule_id = result.get('ruleId')
            if not rule_id:
                problems.append(f"{where}.ruleId is required")
            elif rule_id not in declared_ids:
                # GitHub silently drops a result whose rule is not declared. The
                # check must also fire when the driver declares *no* rules at all:
                # that document renders as a clean audit while hiding every result.
                problems.append(f"{where}.ruleId {rule_id!r} is not declared in driver.rules")
            if result.get('level') not in ('error', 'warning', 'note', 'none'):
                problems.append(f"{where}.level must be error/warning/note/none")
            message = result.get('message', {}).get('text')
            if not message:
                problems.append(f"{where}.message.text is required")
            locations = result.get('locations')
            if not isinstance(locations, list) or not locations:
                problems.append(f"{where}.locations must be non-empty")
                continue
            for l_index, location in enumerate(locations):
                artifact = location.get('physicalLocation', {}).get('artifactLocation', {})
                uri = artifact.get('uri')
                if not uri:
                    problems.append(f"{where}.locations[{l_index}].artifactLocation.uri is required")
                elif os.path.isabs(uri) or uri.startswith('/'):
                    # An absolute URI never resolves against the repository root.
                    problems.append(
                        f"{where}.locations[{l_index}].artifactLocation.uri must be relative")
                region = location.get('physicalLocation', {}).get('region', {})
                start = region.get('startLine')
                if not isinstance(start, int) or isinstance(start, bool) or start < 1:
                    problems.append(
                        f"{where}.locations[{l_index}].region.startLine must be an integer >= 1")
    return problems
