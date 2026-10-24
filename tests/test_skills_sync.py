import unittest
import os
import re

class TestSkillsSync(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.skills_dir = os.path.join(self.root_dir, 'skills')
        self.docs_app_js = os.path.join(self.root_dir, 'docs', 'app.js')
        self.cli_js = os.path.join(self.root_dir, 'bin', 'orthotect.js')

    def test_all_skills_on_disk_have_valid_skill_md(self):
        """Verify that every directory in skills/ contains a valid, well-formed SKILL.md."""
        self.assertTrue(os.path.exists(self.skills_dir), "skills/ directory must exist")
        skill_folders = [f for f in os.listdir(self.skills_dir) if os.path.isdir(os.path.join(self.skills_dir, f))]
        self.assertGreaterEqual(len(skill_folders), 6, "Must have at least 6 core skills")

        for folder in skill_folders:
            skill_md_path = os.path.join(self.skills_dir, folder, 'SKILL.md')
            self.assertTrue(os.path.exists(skill_md_path), f"Missing SKILL.md in skills/{folder}")

            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Frontmatter check
            self.assertTrue(content.startswith('---'), f"skills/{folder}/SKILL.md must start with YAML frontmatter '---'")
            end_fm = content.find('---', 3)
            self.assertNotEqual(end_fm, -1, f"skills/{folder}/SKILL.md must have closing '---' for frontmatter")

            frontmatter = content[3:end_fm]
            name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
            self.assertIsNotNone(name_match, f"skills/{folder}/SKILL.md missing 'name:' in frontmatter")
            self.assertEqual(name_match.group(1).strip(), folder, f"Skill name in frontmatter must match folder name '{folder}'")

            desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
            self.assertIsNotNone(desc_match, f"skills/{folder}/SKILL.md missing 'description:' in frontmatter")
            desc_len = len(desc_match.group(1).strip())
            self.assertLessEqual(desc_len, 1024, f"Skill description in skills/{folder} exceeds 1024 character limit ({desc_len})")

    def test_skills_catalog_in_docs_app_matches_disk(self):
        """Verify that docs/app.js skillsData strictly matches actual disk skills."""
        skill_folders = set([f for f in os.listdir(self.skills_dir) if os.path.isdir(os.path.join(self.skills_dir, f))])

        with open(self.docs_app_js, 'r', encoding='utf-8') as f:
            app_js = f.read()

        # Extract skillsData array ids
        declared_skills = set(re.findall(r'id:\s*"(orthotect-[^"]+)"', app_js))
        self.assertEqual(declared_skills, skill_folders, f"docs/app.js declared skills do not match skills/ on disk: {declared_skills ^ skill_folders}")

    def test_cli_skills_command_lists_all_installed_skills(self):
        """Verify that bin/orthotect.js lists every skill installed in skills/."""
        skill_folders = [f for f in os.listdir(self.skills_dir) if os.path.isdir(os.path.join(self.skills_dir, f))]

        for s in skill_folders:
            with open(self.cli_js, 'r', encoding='utf-8') as f:
                cli_content = f.read()
            self.assertIn(s, cli_content, f"Skill '{s}' missing from bin/orthotect.js skills listing")

    def test_specification_validator_clean_run(self):
        """Verify that scripts/validate-skills.mjs executes and finds 0 errors across all skills."""
        import subprocess
        result = subprocess.run(
            ['node', os.path.join(self.root_dir, 'scripts', 'validate-skills.mjs')],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Specification validator failed: {result.stderr or result.stdout}")
        self.assertIn("18 passed", result.stdout)
        self.assertIn("0 errors", result.stdout)

    def test_validator_detects_broken_anchors_and_invalid_license(self):
        """Verify that scripts/validate-skills.mjs flags broken markdown anchors and invalid license identifiers."""
        import tempfile
        import shutil
        import subprocess

        temp_dir = tempfile.mkdtemp(prefix="orthotect_val_test_")
        try:
            mock_skill = os.path.join(temp_dir, "mock-broken-skill")
            os.makedirs(mock_skill)
            skill_content = (
                "---\n"
                "name: mock-broken-skill\n"
                "description: Use when testing validator error detection\n"
                "license: FakeLicense-9.9\n"
                "---\n\n"
                "# Mock Skill\n\n"
                "See [Missing Section](#nonexistent-heading) for details.\n"
            )
            with open(os.path.join(mock_skill, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(skill_content)

            env = os.environ.copy()
            env["SKILLS_DIR"] = temp_dir
            result = subprocess.run(
                ["node", os.path.join(self.root_dir, "scripts", "validate-skills.mjs")],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            output = (result.stdout or "") + (result.stderr or "")
            self.assertIn("Invalid license SPDX identifier", output)
            self.assertIn("Broken anchor link", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
