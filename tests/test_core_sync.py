#!/usr/bin/env python3
"""
Unit tests for Orthotect Core Sync & Single Source of Truth
Validates that docs/core-models.js exactly mirrors core/fsm/*.json and core/tokens/*.json,
preventing client/server divergence.
"""
import json
import os
import re
import unittest
import tempfile
from gates.gate_fsm_integrity import check_fsm_file

class TestCoreSync(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.fsm_dir = os.path.join(self.root_dir, 'core', 'fsm')
        self.tokens_dir = os.path.join(self.root_dir, 'core', 'tokens')
        self.models_js = os.path.join(self.root_dir, 'docs', 'core-models.js')

    def test_core_models_js_exists_and_in_sync_with_source_files(self):
        """Verify docs/core-models.js exists and is 100% synchronized with core/ schemas."""
        self.assertTrue(os.path.exists(self.models_js), "docs/core-models.js must exist")

        with open(self.models_js, 'r', encoding='utf-8') as f:
            js_content = f.read()

        # Extract the JSON payload from window.ORTHOTECT_CORE = ...
        match = re.search(r'const coreData\s*=\s*(\{[\s\S]*?\});\s*if\s*\(typeof window', js_content)
        self.assertIsNotNone(match, "Failed to extract JSON object from docs/core-models.js")
        
        bundle = json.loads(match.group(1))
        self.assertIn('fsm', bundle)
        self.assertIn('tokens', bundle)

        # Check all FSM files
        for fname in ['data-table-loader.json', 'modal-dialog.json', 'button-states.json']:
            self.assertIn(fname, bundle['fsm'])
            source_path = os.path.join(self.fsm_dir, fname)
            with open(source_path, 'r', encoding='utf-8') as sf:
                expected = json.load(sf)
            self.assertEqual(bundle['fsm'][fname], expected, f"FSM {fname} in docs/core-models.js differs from {source_path}")

        # Check tokens
        prim_path = os.path.join(self.tokens_dir, 'primitives.json')
        sem_path = os.path.join(self.tokens_dir, 'semantics.json')
        with open(prim_path, 'r', encoding='utf-8') as pf:
            self.assertEqual(bundle['tokens']['primitives'], json.load(pf))
        with open(sem_path, 'r', encoding='utf-8') as sf:
            self.assertEqual(bundle['tokens']['semantics'], json.load(sf))

    def test_gate_fsm_integrity_rejects_missing_async_lock(self):
        """Unit test: check_fsm_file rejects an FSM when an async state lacks allowClick: false."""
        bad_fsm = {
            "name": "BrokenFSM",
            "initialState": "idle",
            "states": {
                "idle": { "on": { "START": "submitting" } },
                "submitting": {
                    "isAsync": True,
                    "allowClick": True,  # Violation!
                    "on": { "RESOLVE": "idle", "REJECT": "idle" }
                }
            }
        }
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as tf:
            json.dump(bad_fsm, tf)
            tf_path = tf.name

        try:
            violations = check_fsm_file(tf_path)
            self.assertTrue(len(violations) > 0, "check_fsm_file must flag missing interaction lock")
            self.assertTrue(any("allowClick: false" in v for v in violations))
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

if __name__ == '__main__':
    unittest.main()
