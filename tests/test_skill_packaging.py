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

    def test_sensitive_files_and_dotfiles_are_strictly_excluded(self):
        """Test that sensitive files, credentials, dotfiles, and disallowed extensions are never packaged."""
        mock_repo = Path(self.temp_dir) / "mock_repo"
        mock_repo.mkdir(parents=True)
        (mock_repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")

        mock_skill_dir = mock_repo / "skills" / "mock-secure-skill"
        (mock_skill_dir / "references").mkdir(parents=True)
        (mock_skill_dir / "scripts").mkdir(parents=True)

        # Valid files
        (mock_skill_dir / "SKILL.md").write_text(
            "---\nname: mock-secure-skill\ndescription: Mock skill for security testing\n---\n# Mock\n",
            encoding="utf-8"
        )
        (mock_skill_dir / "references" / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (mock_skill_dir / "scripts" / "tool.mjs").write_text("console.log('ok');\n", encoding="utf-8")

        # Sensitive files and dotfiles planted intentionally
        (mock_skill_dir / ".env").write_text("SECRET=123\n", encoding="utf-8")
        (mock_skill_dir / ".env.local").write_text("DB_PASS=xyz\n", encoding="utf-8")
        (mock_skill_dir / "references" / ".token").write_text("ghp_secret\n", encoding="utf-8")
        (mock_skill_dir / "references" / "private.key").write_text("PRIVATE KEY\n", encoding="utf-8")
        (mock_skill_dir / "references" / "id_rsa").write_text("SSH KEY\n", encoding="utf-8")
        (mock_skill_dir / "references" / "user_credentials.txt").write_text("admin:pass\n", encoding="utf-8")
        (mock_skill_dir / "references" / "api_secret.json").write_text('{"token": "abc"}\n', encoding="utf-8")
        (mock_skill_dir / "references" / "binary.bin").write_bytes(b"\x00\x01\x02\x03")
        (mock_skill_dir / "scripts" / "exploit.exe").write_bytes(b"\x4d\x5a")

        out = Path(self.temp_dir) / "security_out"
        manifest = build_packages(repo_dir=mock_repo, output_dir=out, skills=["mock-secure-skill"])
        self.assertEqual(manifest["bundle_count"], 1)

        zip_path = out / "mock-secure-skill.zip"
        self.assertTrue(zip_path.is_file())

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            # Allowed files must be packaged
            self.assertIn("mock-secure-skill/SKILL.md", names)
            self.assertIn("mock-secure-skill/LICENSE", names)
            self.assertIn("mock-secure-skill/references/guide.md", names)
            self.assertIn("mock-secure-skill/scripts/tool.mjs", names)

            # Sensitive files, dotfiles, and disallowed extensions must be completely absent
            for forbidden in [
                ".env",
                ".env.local",
                ".token",
                "private.key",
                "id_rsa",
                "user_credentials.txt",
                "api_secret.json",
                "binary.bin",
                "exploit.exe",
            ]:
                self.assertFalse(
                    any(forbidden in n for n in names),
                    f"Forbidden file '{forbidden}' leaked into packaged ZIP bundle: {names}"
                )

    def test_symlink_escape_is_strictly_rejected(self):
        """Test that symlinks pointing outside the skill directory are rejected as security violations."""
        mock_repo = Path(self.temp_dir) / "symlink_repo"
        mock_repo.mkdir(parents=True)
        (mock_repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")

        mock_skill_dir = mock_repo / "skills" / "mock-symlink-skill"
        (mock_skill_dir / "references").mkdir(parents=True)
        (mock_skill_dir / "SKILL.md").write_text(
            "---\nname: mock-symlink-skill\ndescription: Symlink security test\n---\n# Mock\n",
            encoding="utf-8"
        )
        (mock_skill_dir / "references" / "valid.md").write_text("# Valid\n", encoding="utf-8")

        outside_secret = Path(self.temp_dir) / "outside_secret.txt"
        outside_secret.write_text("SUPER_SECRET_HOST_DATA\n", encoding="utf-8")

        symlink_target = mock_skill_dir / "references" / "escaped_link.md"
        symlink_target.symlink_to(outside_secret)

        out = Path(self.temp_dir) / "symlink_out"
        with self.assertRaises(ValueError) as ctx:
            build_packages(repo_dir=mock_repo, output_dir=out, skills=["mock-symlink-skill"])
        self.assertIn("Security violation", str(ctx.exception))
        self.assertIn("points outside skill directory", str(ctx.exception))

    def test_sensitive_content_is_strictly_rejected(self):
        """Test that sensitive credentials or private keys in allowed files trigger a security violation."""
        mock_repo = Path(self.temp_dir) / "content_sec_repo"
        mock_repo.mkdir(parents=True)
        (mock_repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")

        mock_skill_dir = mock_repo / "skills" / "mock-leak-skill"
        (mock_skill_dir / "references").mkdir(parents=True)
        (mock_skill_dir / "SKILL.md").write_text(
            "---\nname: mock-leak-skill\ndescription: Secret leak test\n---\n# Mock\n",
            encoding="utf-8"
        )

        # Plant a private key inside an allowed markdown file
        (mock_skill_dir / "references" / "leaked.md").write_text(
            "Here is the key:\n-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----\n",
            encoding="utf-8"
        )

        out = Path(self.temp_dir) / "leak_out"
        with self.assertRaises(ValueError) as ctx:
            build_packages(repo_dir=mock_repo, output_dir=out, skills=["mock-leak-skill"])
        self.assertIn("Security violation", str(ctx.exception))
        self.assertIn("Sensitive credential pattern detected", str(ctx.exception))

    def test_design_tokens_file_is_allowed(self):
        """Test that design-tokens.md is not falsely flagged by token filtering."""
        mock_repo = Path(self.temp_dir) / "tokens_repo"
        mock_repo.mkdir(parents=True)
        (mock_repo / "LICENSE").write_text("MIT License\n", encoding="utf-8")

        mock_skill_dir = mock_repo / "skills" / "mock-tokens-skill"
        (mock_skill_dir / "references").mkdir(parents=True)
        (mock_skill_dir / "SKILL.md").write_text(
            "---\nname: mock-tokens-skill\ndescription: Design tokens test\n---\n# Mock\n",
            encoding="utf-8"
        )
        (mock_skill_dir / "references" / "design-tokens.md").write_text(
            "# Design Tokens\n--color-primary: #0070f3;\n",
            encoding="utf-8"
        )

        out = Path(self.temp_dir) / "tokens_out"
        manifest = build_packages(repo_dir=mock_repo, output_dir=out, skills=["mock-tokens-skill"])
        self.assertEqual(manifest["bundle_count"], 1)

        zip_path = out / "mock-tokens-skill.zip"
        self.assertTrue(zip_path.is_file())
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            self.assertIn("mock-tokens-skill/references/design-tokens.md", names)


if __name__ == '__main__':
    unittest.main()

