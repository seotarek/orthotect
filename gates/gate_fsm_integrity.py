#!/usr/bin/env python3
"""
Orthotect Gate: FSM State Machine Integrity & Deadlock Detector
Validates that UI state machines:
  1. Have reachable states from initialState (Graph Reachability)
  2. All asynchronous in-flight states enforce interaction locks (allowClick: false / locksInteraction: true)
  3. Every asynchronous state provides an explicit error recovery transition
  4. Contain no deadlocks or broken transition targets
  5. Adhere to explicit structural contract with safe path discovery
"""

# Exit-code contract (see core/exit_codes.py):
#   0 = PASS, 1 = rule violation in the audited code, 2 = the gate could not run.
try:
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
except ImportError:
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
    from core.exit_codes import EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR
import json
import os
import sys
from collections import deque

try:
    from core.cli_args import positionals as cli_positionals
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from core.cli_args import positionals as cli_positionals

class FsmViolation(str):
    """
    A violation message that is still a plain string.

    Every existing caller treats these as text — the console report prints them,
    the tests assert substrings of them — so the message format is unchanged. The
    extra attributes carry what a machine-readable report needs: which registry
    rule fired and where in the file. Deriving either from the message text
    downstream would duplicate the detection logic, and the copy would rot.
    """

    def __new__(cls, message, rule=None, state=None, line=0):
        instance = super().__new__(cls, message)
        instance.rule = rule
        instance.state = state
        instance.line = line
        return instance


def _find_line(text, needle):
    """
    Best-effort 1-based line number of a JSON key or value.

    A state machine has no line numbers of its own — it is a graph in a JSON
    document — so an annotation needs to be pointed at the state's key. Returns
    0 when the needle is absent, which callers treat as "no location" rather
    than inventing line 1.
    """
    if not needle or not text:
        return 0
    for index, raw in enumerate(text.splitlines(), start=1):
        if needle in raw:
            return index
    return 0


def check_fsm_file(file_path):
    violations = []
    fname = os.path.basename(file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        data = json.loads(text)
    except Exception as e:
        return [FsmViolation(f"{fname}: Failed to parse JSON ({e})", rule='fsm.invalid-structure')]

    def add(message, rule, state=None):
        """Appends a violation, tagging it with the state's line when there is one."""
        line = _find_line(text, f'"{state}"') if state else 0
        violations.append(FsmViolation(message, rule=rule, state=state, line=line))

    # 1. Structural schema integrity
    if not isinstance(data, dict):
        return [FsmViolation(f"{fname}: Root FSM specification must be a JSON object.",
                             rule='fsm.invalid-structure')]

    initial_state = data.get('initialState')
    if not initial_state or not isinstance(initial_state, str):
        add(f"{fname}: Missing required 'initialState' declaration (must be a non-empty string).",
            'fsm.missing-initial-state', state='initialState')

    states = data.get('states')
    if not states or not isinstance(states, dict):
        add(f"{fname}: Missing or empty 'states' object.", 'fsm.invalid-structure', state='states')
        return violations

    if initial_state and isinstance(initial_state, str) and initial_state not in states:
        add(f"{fname}: initialState '{initial_state}' does not exist in declared states.",
            'fsm.undefined-transition-target', state='initialState')

    # 2. State definitions and transition target validity
    has_structural_error = False
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            add(f"{fname}: State definition for '{state_name}' must be an object.",
                'fsm.invalid-structure', state=state_name)
            has_structural_error = True
            continue

        transitions = state_def.get('on')
        if transitions is not None:
            if not isinstance(transitions, dict):
                add(f"{fname}: Transitions 'on' in '{state_name}' must be an object.",
                    'fsm.invalid-structure', state=state_name)
                has_structural_error = True
                continue

            for trigger, target in transitions.items():
                if not isinstance(trigger, str) or not trigger.strip():
                    add(f"{fname}: State '{state_name}' has invalid transition trigger '{trigger}' (must be a non-empty string).",
                        'fsm.invalid-structure', state=state_name)
                if not isinstance(target, str) or not target.strip():
                    add(f"{fname}: State '{state_name}' has invalid transition target for trigger '{trigger}' (must be a non-empty string).",
                        'fsm.undefined-transition-target', state=state_name)
                    has_structural_error = True
                elif target not in states:
                    add(f"{fname}: State '{state_name}' has transition '{trigger}' -> undefined target '{target}'.",
                        'fsm.undefined-transition-target', state=state_name)

    # If basic structure is broken, stop before behavioral/reachability analysis
    if has_structural_error:
        return violations

    # 3. Explicit Asynchronous execution & interaction lock validation
    # Under the Orthotect FSM specification:
    #   - Asynchronous states MUST declare 'isAsync: true' (or 'type': 'async')
    #   - Asynchronous states MUST declare 'allowClick: false' (or 'locksInteraction: true')
    #   - Asynchronous states MUST declare explicit error recovery transitions
    # State name guessing is completely eliminated from enforcement; explicit contracts govern all states.
    # A diagnostic guard flags any state exhibiting async characteristics that omits explicit declaration.
    async_keywords = {'loading', 'submitting', 'pending', 'processing', 'fetching', 'skeletonloading', 'syncing'}
    transition_keywords = {'opening', 'closing', 'transitioning'}

    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            continue

        name_lower = state_name.lower()
        is_async_by_name = any(kw in name_lower for kw in async_keywords)
        is_transition_by_name = any(kw in name_lower for kw in transition_keywords)

        is_explicitly_async = (
            state_def.get('isAsync') is True or
            state_def.get('async') is True or
            state_def.get('type') == 'async'
        )
        is_explicitly_locked = (
            state_def.get('allowClick') is False or
            state_def.get('locksInteraction') is True or
            state_def.get('isLocked') is True or
            state_def.get('locked') is True
        )
        has_explicit_contract = is_explicitly_async or is_explicitly_locked

        # Explicit Contract Enforcement: undeclared async-sounding states must declare the contract
        if (is_async_by_name or is_transition_by_name) and not has_explicit_contract:
            add(
                f"{fname}: State '{state_name}' must explicitly declare 'isAsync: true' or 'locksInteraction: true' "
                f"(must explicitly declare 'allowClick: false') under the Orthotect FSM contract to prevent interaction race conditions.",
                'fsm.missing-loading-lock', state=state_name
            )

        # Race condition lock check: MUST lock pointer/keyboard actions (allowClick: false)
        if state_def.get('allowClick') is True:
            if is_explicitly_async or is_async_by_name or is_transition_by_name:
                add(f"{fname}: '{state_name}' state must lock pointer/keyboard actions (allowClick: false) to prevent race conditions.",
                    'fsm.missing-loading-lock', state=state_name)
        elif (is_explicitly_async or is_async_by_name or is_transition_by_name) and not is_explicitly_locked:
            add(f"{fname}: '{state_name}' state must explicitly declare 'allowClick: false' (or locksInteraction: true) to prevent interaction race conditions.",
                'fsm.missing-loading-lock', state=state_name)

        # Resilience check: Asynchronous operations (data/network) MUST have explicit error/failure transition
        if is_explicitly_async or is_async_by_name:
            transitions = state_def.get('on', {})
            has_error_recovery = False
            if isinstance(transitions, dict):
                for trig, tgt in transitions.items():
                    if isinstance(trig, str) and any(term in trig.lower() for term in ('error', 'fail', 'reject', 'catch')):
                        has_error_recovery = True
                        break
                    if isinstance(tgt, str) and any(term in tgt.lower() for term in ('error', 'fail', 'reject')):
                        has_error_recovery = True
                        break
            if state_def.get('onError'):
                has_error_recovery = True

            if not has_error_recovery:
                add(f"{fname}: '{state_name}' state must have an explicit error/failure transition for resilience.",
                    'fsm.missing-error-transition', state=state_name)

    # 4. Deadlock detection: Ensure every non-terminal state has transitions
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            continue
        is_final = state_def.get('final') is True or state_def.get('type') == 'final' or state_def.get('isFinal') is True
        transitions = state_def.get('on', {})
        if not is_final and not transitions:
            add(f"{fname}: Deadlock detected in non-final state '{state_name}' (no outgoing transitions).",
                'fsm.deadlock', state=state_name)

    # 5. Graph reachability check (BFS from initialState)
    if initial_state and isinstance(initial_state, str) and initial_state in states:
        visited = set()
        queue = deque([initial_state])
        while queue:
            curr = queue.popleft()
            if curr in visited or curr not in states:
                continue
            visited.add(curr)
            transitions = states[curr].get('on', {})
            if isinstance(transitions, dict):
                for target in transitions.values():
                    if isinstance(target, str) and target in states and target not in visited:
                        queue.append(target)

        unreachable = sorted(list(set(states.keys()) - visited))
        if unreachable:
            add(f"{fname}: Unreachable orphaned state(s) detected: {', '.join(unreachable)}.",
                'fsm.unreachable-state', state=unreachable[0])

    # 6. Error recovery reversibility: Ensure error recovery states do not trap the user
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            continue
        transitions = state_def.get('on', {})
        if isinstance(transitions, dict):
            for trigger, target in transitions.items():
                if isinstance(trigger, str) and isinstance(target, str):
                    if any(term in trigger.lower() or term in target.lower() for term in ('error', 'fail', 'reject')):
                        if target in states:
                            tgt_def = states[target]
                            is_target_final = tgt_def.get('final') is True or tgt_def.get('type') == 'final' or tgt_def.get('isFinal') is True
                            if not is_target_final:
                                target_transitions = tgt_def.get('on', {})
                                if not target_transitions:
                                    add(f"{fname}: Error state '{target}' has no recovery transitions (dead-end error trap).",
                                        'fsm.missing-error-transition', state=target)

    return violations

def find_target_fsm_dir(target_path):
    target_abs = os.path.abspath(target_path)
    root_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Direct target file
    if os.path.isfile(target_abs) and target_abs.endswith('.json'):
        return os.path.dirname(target_abs), [os.path.basename(target_abs)]

    if not os.path.exists(target_abs) or not os.path.isdir(target_abs):
        return None, []

    # 1. Approved dedicated FSM subdirectories within target
    for sub in [('core', 'fsm'), ('fsm',), ('.orthotect', 'fsm')]:
        candidate = os.path.join(target_abs, *sub)
        if os.path.exists(candidate) and os.path.isdir(candidate):
            json_files = [f for f in os.listdir(candidate) if f.endswith('.json')]
            if json_files:
                return candidate, sorted(json_files)

    # 2. Target itself is an approved dedicated FSM directory
    if os.path.basename(target_abs) in ('fsm', 'state_machines', 'states'):
        json_files = [f for f in os.listdir(target_abs) if f.endswith('.json')]
        if json_files:
            return target_abs, sorted(json_files)

    # 3. Explicit fallback ONLY for repository root or documentation project
    is_root_or_docs = (target_abs == root_pkg or target_abs == os.path.join(root_pkg, 'docs'))
    if is_root_or_docs:
        root_fsm = os.path.join(root_pkg, 'core', 'fsm')
        if os.path.exists(root_fsm) and os.path.isdir(root_fsm):
            json_files = [f for f in os.listdir(root_fsm) if f.endswith('.json')]
            if json_files:
                return root_fsm, sorted(json_files)

    return None, []

def _load_sarif_module():
    """Loads `core/sarif.py`, anchored to the package so cwd cannot change it."""
    try:
        from core import sarif
        return sarif
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from core import sarif
        return sarif


def main():
    # Skip flag tokens so `gate_fsm_integrity.py --md ./src` audits ./src rather than "--md".
    args = sys.argv[1:]
    positional = cli_positionals(args)
    target_path = positional[0] if positional else 'core/fsm'
    fsm_dir, json_files = find_target_fsm_dir(target_path)

    sarif = _load_sarif_module()
    as_sarif = sarif.sarif_requested(args)

    def fail_tool_error(message):
        """
        Exits 2, emitting a SARIF document that records the gate did not run.

        An empty result set would be indistinguishable from a clean audit in the
        code-scanning UI, which is the one reading a security-adjacent gate must
        never allow.
        """
        if as_sarif:
            sarif.print_gate_sarif('gate_fsm_integrity', [], os.path.abspath(target_path),
                                   tool_error=message)
        else:
            print(f"❌ [REJECT] {message}")
            print("   Orthotect requires explicit FSM state definitions (.json) in core/fsm/.")
            print("   (Run 'npx orthotect init <path>' to scaffold standard state models).")
        sys.exit(EXIT_TOOL_ERROR)

    if not as_sarif:
        print("═══════════════════════════════════════════════════════════════")
        print("  ORTHOTECT GATE: FSM & State Machine Resilience Check")
        print("═══════════════════════════════════════════════════════════════")

    if not fsm_dir or not json_files:
        fail_tool_error(f"Missing required FSM specifications in target: {target_path}")

    if not as_sarif:
        print(f"  Inspecting: {fsm_dir}")

    all_violations = []
    findings = []
    for f in json_files:
        fpath = os.path.join(fsm_dir, f)
        viols = check_fsm_file(fpath)
        if viols:
            all_violations.extend(viols)
            for v in viols:
                findings.append({
                    'file': fpath,
                    'line': getattr(v, 'line', 0) or 1,
                    'label': str(v),
                    'ruleId': getattr(v, 'rule', None),
                })
        elif not as_sarif:
            print(f"  ✅ {f:<30}: Verified (Deterministic & Reachable)")

    if as_sarif:
        sarif.print_gate_sarif('gate_fsm_integrity', findings, os.path.abspath(target_path))
        sys.exit(EXIT_PASS if not all_violations else EXIT_VIOLATION)

    if not all_violations:
        print(f"\n✅ [PASS] All {len(json_files)} FSM state models verified successfully!")
        sys.exit(EXIT_PASS)
    else:
        print(f"\n❌ [REJECT] Found {len(all_violations)} FSM integrity violation(s):")
        for v in all_violations:
            print(f"   - {v}")
        sys.exit(EXIT_VIOLATION)
if __name__ == '__main__':
    main()

