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
import json
import os
import sys
from collections import deque

def check_fsm_file(file_path):
    violations = []
    fname = os.path.basename(file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return [f"{fname}: Failed to parse JSON ({e})"]

    # 1. Structural schema integrity
    if not isinstance(data, dict):
        return [f"{fname}: Root FSM specification must be a JSON object."]

    initial_state = data.get('initialState')
    if not initial_state or not isinstance(initial_state, str):
        violations.append(f"{fname}: Missing required 'initialState' declaration (must be a non-empty string).")

    states = data.get('states')
    if not states or not isinstance(states, dict):
        violations.append(f"{fname}: Missing or empty 'states' object.")
        return violations

    if initial_state and isinstance(initial_state, str) and initial_state not in states:
        violations.append(f"{fname}: initialState '{initial_state}' does not exist in declared states.")

    # 2. State definitions and transition target validity
    has_structural_error = False
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            violations.append(f"{fname}: State definition for '{state_name}' must be an object.")
            has_structural_error = True
            continue

        transitions = state_def.get('on')
        if transitions is not None:
            if not isinstance(transitions, dict):
                violations.append(f"{fname}: Transitions 'on' in '{state_name}' must be an object.")
                has_structural_error = True
                continue

            for trigger, target in transitions.items():
                if not isinstance(trigger, str) or not trigger.strip():
                    violations.append(f"{fname}: State '{state_name}' has invalid transition trigger '{trigger}' (must be a non-empty string).")
                if not isinstance(target, str) or not target.strip():
                    violations.append(f"{fname}: State '{state_name}' has invalid transition target for trigger '{trigger}' (must be a non-empty string).")
                    has_structural_error = True
                elif target not in states:
                    violations.append(f"{fname}: State '{state_name}' has transition '{trigger}' -> undefined target '{target}'.")

    # If basic structure is broken, stop before behavioral/reachability analysis
    if has_structural_error:
        return violations

    # 3. Explicit Asynchronous execution & transition lock validation
    # Orthotect FSM contract strictly requires explicit declarations:
    #   - 'isAsync: true' (or type: 'async') for in-flight async operations
    #   - 'allowClick: false' (or locksInteraction: true) for pointer/keyboard locks
    # Substring name guessing is deprecated and rejected with actionable diagnostics.
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

        # Explicit Contract Enforcement: undeclared async-sounding states must be declared
        if (is_async_by_name or is_transition_by_name) and not has_explicit_contract:
            violations.append(
                f"{fname}: State '{state_name}' must explicitly declare 'isAsync: true' or 'locksInteraction: true' "
                f"(must explicitly declare 'allowClick: false') under the Orthotect FSM contract to prevent interaction race conditions."
            )

        # Race condition lock check: MUST lock pointer/keyboard actions (allowClick: false)
        if state_def.get('allowClick') is True:
            violations.append(f"{fname}: '{state_name}' state must lock pointer/keyboard actions (allowClick: false) to prevent race conditions.")
        elif (is_explicitly_async or is_async_by_name or is_transition_by_name) and not is_explicitly_locked:
            violations.append(f"{fname}: '{state_name}' state must explicitly declare 'allowClick: false' (or locksInteraction: true) to prevent interaction race conditions.")

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
                violations.append(f"{fname}: '{state_name}' state must have an explicit error/failure transition for resilience.")

    # 4. Deadlock detection: Ensure every non-terminal state has transitions
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            continue
        is_final = state_def.get('final') is True or state_def.get('type') == 'final' or state_def.get('isFinal') is True
        transitions = state_def.get('on', {})
        if not is_final and not transitions:
            violations.append(f"{fname}: Deadlock detected in non-final state '{state_name}' (no outgoing transitions).")

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
            violations.append(f"{fname}: Unreachable orphaned state(s) detected: {', '.join(unreachable)}.")

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
                                    violations.append(f"{fname}: Error state '{target}' has no recovery transitions (dead-end error trap).")

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

def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else 'core/fsm'
    fsm_dir, json_files = find_target_fsm_dir(target_path)

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: FSM & State Machine Resilience Check")
    print("═══════════════════════════════════════════════════════════════")

    if not fsm_dir or not json_files:
        print(f"❌ [REJECT] Missing required FSM specifications in target: {target_path}")
        print("   Orthotect requires explicit FSM state definitions (.json) in core/fsm/.")
        print("   (Run 'npx orthotect init <path>' to scaffold standard state models).")
        sys.exit(1)

    print(f"  Inspecting: {fsm_dir}")
    all_violations = []
    for f in json_files:
        viols = check_fsm_file(os.path.join(fsm_dir, f))
        if viols:
            all_violations.extend(viols)
        else:
            print(f"  ✅ {f:<30}: Verified (Deterministic & Reachable)")

    if not all_violations:
        print(f"\n✅ [PASS] All {len(json_files)} FSM state models verified successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ [REJECT] Found {len(all_violations)} FSM integrity violation(s):")
        for v in all_violations:
            print(f"   - {v}")
        sys.exit(1)
if __name__ == '__main__':
    main()

