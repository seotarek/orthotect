import unittest
import sys
import os
import json
import tempfile

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
        self.assertTrue(any("orphanState" in v for v in viols))

if __name__ == '__main__':
    unittest.main()
