import unittest
import subprocess
import os
import json

class TestCLIExpanded(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.cli_path = os.path.join(self.root_dir, 'bin', 'orthotect.js')

    def test_cli_doctor_command(self):
        """Verify 'orthotect doctor' runs diagnostics and reports HEALTHY."""
        res = subprocess.run(['node', self.cli_path, 'doctor'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Doctor failed with stderr: {res.stderr}")
        self.assertIn("HEALTHY", res.stdout)
        self.assertIn("Node.js Runtime", res.stdout)
        self.assertIn("Python Runtime", res.stdout)
        self.assertIn("22 skills installed", res.stdout)
        self.assertIn("UI/UX Knowledge Base", res.stdout)
        self.assertIn("Context & Token Engine: Operational", res.stdout)

    def test_cli_skills_list_command(self):
        """Verify 'orthotect skills' lists all 22 skills."""
        res = subprocess.run(['node', self.cli_path, 'skills'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("22 Modular Disciplines", res.stdout)
        expected_skills = [
            "orthotect-doctrine", "orthotect-bidi", "orthotect-dashboard",
            "orthotect-fsm", "orthotect-gates", "orthotect-tokens",
            "orthotect-visual-qa", "orthotect-uiux", "orthotect-design-systems",
            "orthotect-components", "orthotect-accessibility", "orthotect-responsive",
            "orthotect-motion", "orthotect-forms", "orthotect-data-viz", "orthotect-context",
            "orthotect-cro", "orthotect-schema", "orthotect-auto-fix", "orthotect-hooks",
            "orthotect-typography", "orthotect-security"
        ]
        for s in expected_skills:
            self.assertIn(s, res.stdout, f"Skill {s} missing from CLI output")

    def test_cli_skills_search_command(self):
        """Verify 'orthotect skills search <query>' filters skills by term."""
        res = subprocess.run(['node', self.cli_path, 'skills', 'search', 'fsm'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("orthotect-fsm", res.stdout)

    def test_cli_skills_show_command(self):
        """Verify 'orthotect skills show <name>' displays the full SKILL.md."""
        res = subprocess.run(['node', self.cli_path, 'skills', 'show', 'orthotect-doctrine'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("The 7 Non-Negotiable Laws of High-Integrity Interface Engineering", res.stdout)
        self.assertIn("Law 1: Verification Protocol", res.stdout)

    def test_cli_skills_validate_command(self):
        """Verify 'orthotect skills validate' verifies all 15 skills."""
        res = subprocess.run(['node', self.cli_path, 'skills', 'validate'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("100% PASSED", res.stdout)

    def test_cli_knowledge_validate_command(self):
        """Verify 'orthotect knowledge --validate' passes schema verification."""
        res = subprocess.run(['node', self.cli_path, 'knowledge', '--validate'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Successfully validated", res.stdout)

    def test_cli_knowledge_search_json_command(self):
        """Verify 'orthotect knowledge <query> --json' returns valid JSON array."""
        res = subprocess.run(['node', self.cli_path, 'knowledge', 'bidi', '--json'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn("id", data[0])
        self.assertIn("title", data[0])

    def test_cli_design_page_command(self):
        """Verify 'orthotect design page <recipe>' inspects recipe scaffolding."""
        res = subprocess.run(['node', self.cli_path, 'design', 'page', 'precision-analytical-console'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Scaffolding page using style recipe: precision-analytical-console", res.stdout)
        self.assertIn("Thesis:", res.stdout)
        self.assertIn("Certified HTML boilerplate ready", res.stdout)

    def test_cli_design_page_custom_out(self):
        """Verify 'orthotect design page <recipe> --out <path>' writes to custom destination."""
        out_path = '/tmp/temp_test_scaffold.html'
        if os.path.exists(out_path):
            os.remove(out_path)
        try:
            res = subprocess.run(['node', self.cli_path, 'design', 'page', 'contemporary-product-saas', '--out', out_path],
                                 capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(out_path))
            with open(out_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("Contemporary Product SaaS", content)
            self.assertIn("margin-block", content)
            self.assertIn("data-fsm", content)
            self.assertIn("initOrthotectFsm", content)
            self.assertIn("fsm-status-announcer", content)
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)

    def test_cli_design_page_stdout(self):
        """Verify 'orthotect design page <recipe> --stdout' streams boilerplate to stdout."""
        res = subprocess.run(['node', self.cli_path, 'design', 'page', 'contemporary-product-saas', '--stdout'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("<!DOCTYPE html>", res.stdout)
        self.assertIn("Contemporary Product SaaS", res.stdout)

    def test_cli_context_inspect_command(self):
        """Verify 'orthotect context inspect <path> --json' profiles token density."""
        pkg_path = os.path.join(self.root_dir, 'package.json')
        res = subprocess.run(['node', self.cli_path, 'context', 'inspect', pkg_path, '--json'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data['file'], 'package.json')
        self.assertGreater(data['estimated_tokens'], 0)
        self.assertIn("recommendation", data)

    def test_cli_context_skeleton_command(self):
        """Verify 'orthotect context skeleton <dir> --json' produces compressed symbol tree."""
        core_dir = os.path.join(self.root_dir, 'gates')
        res = subprocess.run(['node', self.cli_path, 'context', 'skeleton', core_dir, '--json'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertGreaterEqual(data['total_files'], 3)
        self.assertGreater(data['compression_ratio'], 0.5)

if __name__ == '__main__':
    unittest.main()


