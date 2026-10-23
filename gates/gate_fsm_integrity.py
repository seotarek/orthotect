#!/usr/bin/env python3
"""
Orthotect Gate: FSM State Machine Integrity & Deadlock Detector
Validates that UI state machines:
  1. Have reachable states from initialState (Graph Reachability)
  2. All asynchronous in-flight states (loading, submitting, fetching, etc.) enforce interaction locks (allowClick: false)
  3. Every asynchronous state provides an explicit error recovery transition
  4. Contain no deadlocks or broken transition targets
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

    # 1. Schema integrity
    if not isinstance(data, dict):
        return [f"{fname}: Root FSM specification must be a JSON object."]

    states = data.get('states')
    if not states or not isinstance(states, dict):
        return [f"{fname}: Missing or empty 'states' object."]

    initial_state = data.get('initialState')
    if not initial_state:
        violations.append(f"{fname}: Missing required 'initialState' declaration.")
    elif initial_state not in states:
        violations.append(f"{fname}: initialState '{initial_state}' does not exist in declared states.")

    # 2. Transition target validity
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            violations.append(f"{fname}: State definition for '{state_name}' must be an object.")
            continue

        transitions = state_def.get('on', {})
        if not isinstance(transitions, dict):
            violations.append(f"{fname}: Transitions 'on' in '{state_name}' must be an object.")
            continue

        for trigger, target in transitions.items():
            if target not in states:
                violations.append(f"{fname}: State '{state_name}' has transition '{trigger}' -> undefined target '{target}'.")

    # 3. Asynchronous execution & transition lock validation
    # Supports explicit schema properties ('isAsync', 'type: "async"', 'locksInteraction') as well as documented conventions
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
        requires_lock = (
            is_async_by_name or
            is_explicitly_async or
            is_transition_by_name or
            state_def.get('locksInteraction') is True or
            state_def.get('isLocked') is True or
            state_def.get('locked') is True or
            ('allowClick' in state_def and state_def.get('allowClick') is False)
        )

        if requires_lock:
            # Race condition lock check: MUST lock pointer/keyboard actions (allowClick: false)
            is_locked = (
                state_def.get('allowClick') is False or
                state_def.get('locksInteraction') is True or
                state_def.get('isLocked') is True or
                state_def.get('locked') is True
            )
            if state_def.get('allowClick', False) is True:
                violations.append(f"{fname}: '{state_name}' state must lock pointer/keyboard actions (allowClick: false) to prevent race conditions.")
            elif not is_locked:
                violations.append(f"{fname}: '{state_name}' state must explicitly declare 'allowClick: false' (or locksInteraction: true) to prevent interaction race conditions.")

            # Resilience check: Asynchronous operations (data/network) MUST have explicit error/failure transition
            if is_async_by_name or is_explicitly_async:
                transitions = list(state_def.get('on', {}).values())
                has_error_recovery = any('error' in t.lower() or 'fail' in t.lower() or 'reject' in t.lower() for t in transitions)
                if not has_error_recovery:
                    violations.append(f"{fname}: '{state_name}' state must have an explicit error/failure transition for resilience.")

    # 4. Deadlock detection: Ensure every non-terminal state has transitions
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            continue
        is_final = state_def.get('final') is True or state_def.get('type') == 'final'
        transitions = state_def.get('on', {})
        if not is_final and not transitions:
            violations.append(f"{fname}: Deadlock detected in non-final state '{state_name}' (no outgoing transitions).")

    # 5. Graph reachability check (BFS from initialState)
    if initial_state and initial_state in states:
        visited = set()
        queue = deque([initial_state])
        while queue:
            curr = queue.popleft()
            if curr in visited:
                continue
            visited.add(curr)
            for target in states.get(curr, {}).get('on', {}).values():
                if target in states and target not in visited:
                    queue.append(target)

        unreachable = set(states.keys()) - visited
        if unreachable:
            violations.append(f"{fname}: Unreachable orphaned state(s) detected: {', '.join(unreachable)}.")

    # 6. Error recovery reversibility: Ensure error recovery states do not trap the user
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            continue
        transitions = state_def.get('on', {})
        for trigger, target in transitions.items():
            if any(term in trigger.lower() or term in target.lower() for term in ('error', 'fail', 'reject')):
                if target in states:
                    target_transitions = states[target].get('on', {})
                    if not target_transitions:
                        violations.append(f"{fname}: Error state '{target}' has no recovery transitions (dead-end error trap).")

    return violations

def find_target_fsm_dir(target_path):
    target_abs = os.path.abspath(target_path)
    root_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    is_root_or_docs = (target_abs == root_pkg or target_abs == os.path.join(root_pkg, 'docs'))
    # Dedicated FSM directories take priority over raw target root
    candidates = [
        os.path.join(target_abs, 'core', 'fsm'),
        os.path.join(target_abs, 'fsm'),
        os.path.join(target_abs, '.orthotect', 'fsm')
    ]
    if is_root_or_docs:
        candidates.append(os.path.join(root_pkg, 'core', 'fsm'))
    candidates.append(target_abs)

    ignored_jsons = {
        'package.json', 'package-lock.json', 'tsconfig.json',
        'gallery-data.json', 'manifest.json', 'sitemap.json', 'skills.sh.json'
    }

    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            json_files = [f for f in os.listdir(c) if f.endswith('.json') and f not in ignored_jsons]
            if json_files:
                return c, json_files
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
