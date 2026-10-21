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
