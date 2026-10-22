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

if __name__ == '__main__':
    unittest.main()


