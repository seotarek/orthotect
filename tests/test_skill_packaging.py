import unittest
import os
import json
import tempfile
import zipfile
import shutil
from pathlib import Path
from scripts.package_skills import build_packages, sha256_bytes

class TestSkillPackaging(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.temp_dir = tempfile.mkdtemp(prefix="orthotect_pack_test_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_skill_package_and_manifest(self):
        """Test building a package for a single skill (orthotect-cro)."""
        output_dir = Path(self.temp_dir) / "output"
        manifest = build_packages(
            repo_dir=self.root_dir,
            output_dir=output_dir,
            skills=["orthotect-cro"],
        )

        self.assertEqual(manifest["bundle_count"], 1)
        self.assertEqual(len(manifest["bundles"]), 1)
        bundle = manifest["bundles"][0]
        self.assertEqual(bundle["skill"], "orthotect-cro")
        self.assertEqual(bundle["archive"], "orthotect-cro.zip")

        zip_path = output_dir / "orthotect-cro.zip"
        self.assertTrue(zip_path.is_file())
        self.assertEqual(bundle["sha256"], sha256_bytes(zip_path.read_bytes()))

        # Verify ZIP contents
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            self.assertIn("orthotect-cro/SKILL.md", namelist)
            self.assertIn("orthotect-cro/LICENSE", namelist)
            self.assertIn("orthotect-cro/references/form-cro.md", namelist)
            self.assertIn("orthotect-cro/references/cta-hierarchy.md", namelist)
            # Ensure excluded parts are NOT present
            for name in namelist:
                self.assertNotIn("evals", name)
                self.assertNotIn("__pycache__", name)

        manifest_file = output_dir / "manifest.json"
        self.assertTrue(manifest_file.is_file())
        saved_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(saved_manifest["bundle_count"], 1)

    def test_reproducible_deterministic_output(self):
        """Test that two packaging runs produce byte-for-byte identical archives and hashes."""
        out1 = Path(self.temp_dir) / "run1"
        out2 = Path(self.temp_dir) / "run2"

        m1 = build_packages(repo_dir=self.root_dir, output_dir=out1, skills=["orthotect-schema"])
        m2 = build_packages(repo_dir=self.root_dir, output_dir=out2, skills=["orthotect-schema"])

        zip1 = (out1 / "orthotect-schema.zip").read_bytes()
        zip2 = (out2 / "orthotect-schema.zip").read_bytes()

        self.assertEqual(zip1, zip2, "ZIP archives must be byte-for-byte deterministic across runs")
        self.assertEqual(m1["bundles"][0]["sha256"], m2["bundles"][0]["sha256"])

if __name__ == '__main__':
    unittest.main()
