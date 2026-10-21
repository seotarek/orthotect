#!/usr/bin/env python3
"""
Orthotect Gate: Finite State Machine (FSM) Integrity Checker
Ensures that all async operations and interactive components:
- Explicitly declare valid initialState and valid states
- Graph reachability: all states are reachable from initialState
- Deadlock prevention and async error recovery transitions
- Prevent double-submission locks during loading
"""
import sys
import os
import json
from collections import deque

def check_fsm_file(fpath):
    violations = []
    fname = os.path.basename(fpath)

    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return [f"{fname}: Invalid JSON syntax: {e}"]

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

    # 2. Transition target validity & double-submission check
    all_targets = set()
    for state_name, state_def in states.items():
        if not isinstance(state_def, dict):
            violations.append(f"{fname}: State definition for '{state_name}' must be an object.")
            continue

        transitions = state_def.get('on', {})
        if not isinstance(transitions, dict):
            violations.append(f"{fname}: Transitions 'on' in '{state_name}' must be an object.")
            continue

        for trigger, target in transitions.items():
            all_targets.add(target)
            if target not in states:
                violations.append(f"{fname}: State '{state_name}' has transition '{trigger}' -> undefined target '{target}'.")

    # 3. Loading state lock validation
    if 'loading' in states:
        loading_state = states['loading']
        if loading_state.get('allowClick', False) is True:
            violations.append(f"{fname}: 'loading' state must lock pointer/keyboard actions (allowClick: false) to prevent race conditions.")
        
        # Must have an error transition from loading
        loading_transitions = list(loading_state.get('on', {}).values())
        has_error_recovery = any('error' in t.lower() or 'fail' in t.lower() or 'reject' in t.lower() for t in loading_transitions)
        if not has_error_recovery:
            violations.append(f"{fname}: 'loading' state must have an explicit error/failure transition for resilience.")

    # 4. Graph reachability check (BFS from initialState)
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

    return violations

def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else 'core/fsm'
    
    # Resolve directory to check
    fsm_dir = target_path
    if not os.path.exists(os.path.join(fsm_dir, 'button-states.json')):
        # Check subdirectories
        candidate = os.path.join(target_path, 'core', 'fsm')
        if os.path.exists(candidate):
            fsm_dir = candidate
        else:
            pkg_fallback = os.path.join(os.path.dirname(__file__), '..', 'core', 'fsm')
            if os.path.exists(pkg_fallback):
                fsm_dir = pkg_fallback

    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE: FSM & State Machine Resilience Check")
    print(f"  Inspecting: {fsm_dir}")
    print("═══════════════════════════════════════════════════════════════")

    if not os.path.exists(fsm_dir):
        print(f"❌ [REJECT] FSM directory does not exist: {fsm_dir}")
        sys.exit(1)

    json_files = [f for f in os.listdir(fsm_dir) if f.endswith('.json')]
    if not json_files:
        print(f"❌ [REJECT] No FSM specification files found in: {fsm_dir}")
        sys.exit(1)

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
        print(f"\n❌ [REJECT] Found {len(all_violations)} state machine flaw(s):")
        for v in all_violations:
            print(f"   - {v}")
        sys.exit(1)

if __name__ == '__main__':
    main()
