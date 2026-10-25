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
        # Exit code must be 0 (100% verified) or 2 (valid local parity, unverified remote in offline/test environment)
        # It must NEVER be 1 (parity violation)
        self.assertIn(result.returncode, (0, 2), f"check-release-sync failed with violation (code {result.returncode}):\n{result.stderr}\n{result.stdout}")
        self.assertTrue(
            "100% Version Parity Enforced" in result.stdout or "Partial Version Parity Enforced" in result.stdout,
            f"Unexpected output:\n{result.stdout}"
        )

if __name__ == "__main__":
    unittest.main()
