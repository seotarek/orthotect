import unittest
import sys
import os
import json
import tempfile
import subprocess
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gates')))
from gate_fsm_integrity import check_fsm_file

class TestFsmValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_fsm_passes(self):
        valid_fsm = {
            "name": "TestValid",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "GO": "loading" } },
                "loading": { "allowClick": False, "on": { "SUCCESS": "idle", "FAIL": "error" } },
                "error": { "on": { "RETRY": "loading" } }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "valid.json")
        with open(fpath, "w") as f:
            json.dump(valid_fsm, f)
        viols = check_fsm_file(fpath)
        self.assertEqual(len(viols), 0)

    def test_submitting_state_with_allow_click_true_fails(self):
        """Negative test: 'submitting' state with allowClick: true must be rejected."""
        fsm_submitting = {
            "name": "TestSubmittingFail",
            "initialState": "open",
            "states": {
                "open": { "on": { "SUBMIT": "submitting" } },
                "submitting": {
                    "allowClick": True, # VIOLATION: Must be false to lock interactions
                    "on": { "SUCCESS": "open", "ERROR": "open" }
                }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "submitting_true.json")
        with open(fpath, "w") as f:
            json.dump(fsm_submitting, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("must lock pointer/keyboard actions" in v for v in viols))

    def test_submitting_state_without_lock_fails(self):
        """Negative test: 'submitting' state omitting allowClick: false must be rejected."""
        fsm_submitting = {
            "name": "TestSubmittingMissingLock",
            "initialState": "open",
            "states": {
                "open": { "on": { "SUBMIT": "submitting" } },
                "submitting": {
                    "on": { "SUCCESS": "open", "ERROR": "open" }
                }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "submitting_missing.json")
        with open(fpath, "w") as f:
            json.dump(fsm_submitting, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("must explicitly declare 'allowClick: false'" in v for v in viols))

    def test_transition_state_omitting_allow_click_fails(self):
        """Negative test: transition state ('opening' / 'closing') omitting allowClick: false must be rejected."""
        fsm_transition = {
            "name": "TestTransitionLockMissing",
            "initialState": "closed",
            "states": {
                "closed": { "on": { "OPEN": "opening" } },
                "opening": {
                    # Missing allowClick: false!
                    "on": { "ANIMATION_END": "open" }
                },
                "open": { "on": { "CLOSE": "closed" } }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "opening_missing_lock.json")
        with open(fpath, "w") as f:
            json.dump(fsm_transition, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("must explicitly declare 'allowClick: false'" in v for v in viols))

    def test_async_state_lacking_error_recovery_fails(self):
        """Negative test: async state without error/failure recovery must be rejected."""
        fsm_no_error = {
            "name": "TestNoErrorRecovery",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "START": "submitting" } },
                "submitting": {
                    "allowClick": False,
                    "on": { "SUCCESS": "idle" } # VIOLATION: Missing error recovery transition
                }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "no_error.json")
        with open(fpath, "w") as f:
            json.dump(fsm_no_error, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("must have an explicit error/failure transition" in v for v in viols))

    def test_missing_initial_state_fails(self):
        broken = {
            "name": "Broken",
            "initialState": "nonexistent",
            "states": { "idle": {} }
        }
        fpath = os.path.join(self.temp_dir.name, "broken.json")
        with open(fpath, "w") as f:
            json.dump(broken, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("does not exist" in v for v in viols))

    def test_unreachable_orphaned_state_fails(self):
        orphaned = {
            "name": "Orphaned",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "NEXT": "loading" } },
                "loading": { "allowClick": False, "on": { "FAIL": "idle" } },
                "orphanState": { "on": { "LEAVE": "idle" } }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "orphan.json")
        with open(fpath, "w") as f:
            json.dump(orphaned, f)
        viols = check_fsm_file(fpath)
    def test_explicit_is_async_property_enforces_lock(self):
        """Schema test: explicit isAsync: true on arbitrary state name must enforce allowClick: false and recovery."""
        fsm = {
            "name": "CustomAsync",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "RUN": "customOperation" } },
                "customOperation": {
                    "isAsync": True,
                    "on": { "DONE": "idle", "FAIL": "errorState" }
                },
                "errorState": { "on": { "RESET": "idle" } }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "custom_async.json")
        with open(fpath, "w") as f:
            json.dump(fsm, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("must explicitly declare 'allowClick: false'" in v for v in viols))

    def test_deadlock_non_final_state_fails(self):
        """Negative test: non-final state with no outgoing transitions is a deadlock."""
        fsm = {
            "name": "DeadlockFSM",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "NEXT": "trapped" } },
                "trapped": {} # Deadlock: no transitions
            }
        }
        fpath = os.path.join(self.temp_dir.name, "deadlock.json")
        with open(fpath, "w") as f:
            json.dump(fsm, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("Deadlock detected in non-final state 'trapped'" in v for v in viols))

    def test_dead_end_error_state_fails(self):
        """Negative test: error state that has no transitions traps the user."""
        fsm = {
            "name": "DeadEndError",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "GO": "loading" } },
                "loading": {
                    "allowClick": False,
                    "on": { "SUCCESS": "idle", "REJECT_ERROR": "errorTrap" }
                },
                "errorTrap": {} # Dead-end error
            }
        }
        fpath = os.path.join(self.temp_dir.name, "dead_end_error.json")
        with open(fpath, "w") as f:
            json.dump(fsm, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("no recovery transitions" in v for v in viols))

    def test_malformed_transition_target_non_string(self):
        """Negative test: Non-string transition targets must produce diagnostics without crash."""
        fsm_bad_target = {
            "name": "BadTarget",
            "initialState": "idle",
            "states": {
                "idle": {
                    "on": {
                        "NEXT": 12345,  # Non-string integer target
                        "LIST": ["target"],  # Non-string list target
                        "EMPTY": ""  # Empty string target
                    }
                }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "bad_target.json")
        with open(fpath, "w") as f:
            json.dump(fsm_bad_target, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("invalid transition target" in v for v in viols))

    def test_malformed_states_structure_fails_gracefully(self):
        """Negative test: Malformed states structures must be rejected cleanly without unhandled exceptions."""
        cases = [
            {"initialState": "idle", "states": "string_not_dict"},
            {"initialState": "idle", "states": {"idle": "not_a_dict"}},
            {"initialState": "idle", "states": {"idle": {"on": [1, 2, 3]}}},
            ["array", "not", "dict"],
            {"initialState": 123, "states": {"idle": {}}}
        ]
        for i, case in enumerate(cases):
            fpath = os.path.join(self.temp_dir.name, f"malformed_{i}.json")
            with open(fpath, "w") as f:
                json.dump(case, f)
            viols = check_fsm_file(fpath)
            self.assertTrue(len(viols) > 0, f"Case {i} should fail")

    def test_valid_final_state_is_not_flagged_as_deadlock(self):
        """Positive test: States marked 'final: true' or 'type: final' without outgoing transitions are legitimate terminal states."""
        fsm_final = {
            "name": "FinalStateFlow",
            "initialState": "active",
            "states": {
                "active": { "on": { "TERMINATE": "completed" } },
                "completed": { "final": True }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "valid_final.json")
        with open(fpath, "w") as f:
            json.dump(fsm_final, f)
        viols = check_fsm_file(fpath)
        self.assertEqual(len(viols), 0)

    def test_valid_recoverable_error_flow_passes(self):
        """Positive test: Asynchronous state with proper allowClick lock and reversible error state."""
        fsm = {
            "name": "ResilientFlow",
            "initialState": "ready",
            "states": {
                "ready": { "on": { "EXECUTE": "fetching" } },
                "fetching": {
                    "isAsync": True,
                    "allowClick": False,
                    "on": { "SUCCESS": "ready", "ERROR": "errorRecovery" }
                },
                "errorRecovery": {
                    "on": { "RETRY": "fetching", "DISMISS": "ready" }
                }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "resilient_flow.json")
        with open(fpath, "w") as f:
            json.dump(fsm, f)
        viols = check_fsm_file(fpath)
        self.assertEqual(len(viols), 0)

    def test_explicit_is_async_contract_without_keyword_in_name(self):
        """Explicit contract test: A state without 'loading/submitting' in name but declaring 'isAsync: true' must satisfy lock and error transitions."""
        # 1. Non-async-named state with isAsync: true lacking allowClick: false
        fsm_missing_lock = {
            "name": "CustomWorkerFSM",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "START": "processBatch" } },
                "processBatch": {
                    "isAsync": True,
                    "on": { "RESOLVE": "idle", "REJECT": "idle" }
                }
            }
        }
        fpath1 = os.path.join(self.temp_dir.name, "worker1.json")
        with open(fpath1, "w") as f:
            json.dump(fsm_missing_lock, f)
        viols1 = check_fsm_file(fpath1)
        self.assertTrue(any("allowClick: false" in v for v in viols1))

        # 2. Non-async-named state with isAsync: true lacking error recovery
        fsm_missing_error = {
            "name": "CustomWorkerFSM",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "START": "processBatch" } },
                "processBatch": {
                    "isAsync": True,
                    "allowClick": False,
                    "on": { "RESOLVE": "idle" }
                }
            }
        }
        fpath2 = os.path.join(self.temp_dir.name, "worker2.json")
        with open(fpath2, "w") as f:
            json.dump(fsm_missing_error, f)
        viols2 = check_fsm_file(fpath2)
        self.assertTrue(any("explicit error/failure transition" in v for v in viols2))

        # 3. Non-async-named state with isAsync: true and full contract satisfies gate
        fsm_valid = {
            "name": "CustomWorkerFSM",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "START": "processBatch" } },
                "processBatch": {
                    "isAsync": True,
                    "allowClick": False,
                    "on": { "RESOLVE": "idle", "REJECT_ERROR": "errorState" }
                },
                "errorState": {
                    "on": { "RETRY": "processBatch" }
                }
            }
        }
        fpath3 = os.path.join(self.temp_dir.name, "worker3.json")
        with open(fpath3, "w") as f:
            json.dump(fsm_valid, f)
        viols3 = check_fsm_file(fpath3)
        self.assertEqual(len(viols3), 0)

    def test_undeclared_async_state_produces_strict_contract_diagnostic(self):
        """Strict contract test: An async-named state omitting explicit declarations must receive actionable contract diagnostic."""
        fsm_undeclared = {
            "name": "UndeclaredAsync",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "LOAD": "loading" } },
                "loading": {
                    "on": { "RESOLVE": "idle", "REJECT": "idle" }
                }
            }
        }
        fpath = os.path.join(self.temp_dir.name, "undeclared.json")
        with open(fpath, "w") as f:
            json.dump(fsm_undeclared, f)
        viols = check_fsm_file(fpath)
        self.assertTrue(any("must explicitly declare 'isAsync: true' or 'locksInteraction: true'" in v for v in viols))

class TestFsmGateE2E(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.gate_script = os.path.join(self.root_dir, 'gates', 'gate_fsm_integrity.py')
        self.temp_dir = tempfile.mkdtemp(prefix='fsm_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_gate(self, target):
        return subprocess.run(['python3', self.gate_script, target],
                              capture_output=True, text=True)

    def test_gate_cli_rejects_empty_directory(self):
        """Negative test: Gate must REJECT directory without FSM specifications."""
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required FSM specifications in target", res.stdout)

    def test_gate_cli_rejects_unrelated_json_manifests_beside_html(self):
        """Negative test: Directory containing manifest.json, package.json, settings.json beside HTML must be rejected, not certified."""
        with open(os.path.join(self.temp_dir, 'index.html'), 'w') as f:
            f.write("<!DOCTYPE html><html><body><h1>Test</h1></body></html>")
        with open(os.path.join(self.temp_dir, 'manifest.json'), 'w') as f:
            json.dump({"name": "My App", "version": "1.0.0"}, f)
        with open(os.path.join(self.temp_dir, 'settings.json'), 'w') as f:
            json.dump({"theme": "dark", "locale": "en"}, f)

        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required FSM specifications in target", res.stdout)

    def test_gate_cli_rejects_submitting_state_with_allow_click_true(self):
        """Negative test: Gate must REJECT FSM where submitting state has allowClick: true."""
        fsm_dir = os.path.join(self.temp_dir, 'core', 'fsm')
        os.makedirs(fsm_dir, exist_ok=True)
        bad_fsm = {
            "name": "ButtonRaceFlaw",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "SUBMIT": "submitting" } },
                "submitting": {
                    "allowClick": True, # VIOLATION: Must lock click actions
                    "on": { "SUCCESS": "idle", "FAIL": "idle" }
                }
            }
        }
        with open(os.path.join(fsm_dir, 'button.json'), 'w') as f:
            json.dump(bad_fsm, f)
        res = self.run_gate(self.temp_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("FSM integrity violation", res.stdout)
        self.assertIn("must lock pointer/keyboard actions", res.stdout)

    def test_gate_cli_accepts_valid_fsm(self):
        """Positive verification: Gate PASSES compliant FSM state definitions."""
        fsm_dir = os.path.join(self.temp_dir, 'core', 'fsm')
        os.makedirs(fsm_dir, exist_ok=True)
        valid_fsm = {
            "name": "CompliantDialog",
            "initialState": "closed",
            "states": {
                "closed": { "on": { "OPEN": "open" } },
                "open": { "on": { "SUBMIT": "submitting", "CLOSE": "closed" } },
                "submitting": {
                    "allowClick": False,
                    "on": { "SUCCESS": "closed", "ERROR": "error" }
                },
                "error": { "on": { "RETRY": "submitting", "DISMISS": "closed" } }
            }
        }
        with open(os.path.join(fsm_dir, 'dialog.json'), 'w') as f:
            json.dump(valid_fsm, f)
        res = self.run_gate(self.temp_dir)
        self.assertEqual(res.returncode, 0)
        self.assertIn("FSM state models verified successfully", res.stdout)

    def test_empty_subdirectory_in_repo_fails_without_fsm(self):
        """Negative test: A subdirectory located inside the repository tree without its own FSM must NOT borrow root FSM."""
        bin_dir = os.path.join(self.root_dir, 'bin')
        res = self.run_gate(bin_dir)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Missing required FSM specifications in target", res.stdout)

    def test_nested_project_paths_isolated(self):
        """Negative test: Proj1 with valid FSM and Proj2 with broken FSM must remain strictly isolated."""
        proj1 = os.path.join(self.temp_dir, 'proj1')
        proj2 = os.path.join(self.temp_dir, 'proj2')
        os.makedirs(os.path.join(proj1, 'fsm'), exist_ok=True)
        os.makedirs(os.path.join(proj2, 'fsm'), exist_ok=True)

        with open(os.path.join(proj1, 'fsm', 's.json'), 'w') as f:
            json.dump({"initialState": "a", "states": {"a": {"on": {"NEXT": "b"}}, "b": {"final": True}}}, f)
        with open(os.path.join(proj2, 'fsm', 's.json'), 'w') as f:
            json.dump({"initialState": "a", "states": {"a": {"on": {"NEXT": "nonexistent"}}}}, f)

        res1 = self.run_gate(proj1)
        self.assertEqual(res1.returncode, 0)

        res2 = self.run_gate(proj2)
        self.assertNotEqual(res2.returncode, 0)
        self.assertIn("undefined target 'nonexistent'", res2.stdout)

if __name__ == '__main__':
    unittest.main()



