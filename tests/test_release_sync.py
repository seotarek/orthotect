#!/usr/bin/env python3
"""
Unit test for Release Synchronization & Version Parity Checker
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class TestReleaseSync(unittest.TestCase):
    def test_check_release_sync_script(self):
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "check-release-sync.mjs")],
            cwd=str(ROOT),
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"check-release-sync failed:\n{result.stderr}\n{result.stdout}")
        self.assertIn("100% Version Parity Enforced", result.stdout)

if __name__ == "__main__":
    unittest.main()
