import unittest
import os
import sys
import tempfile
import subprocess
import shutil

class TestHooksCli(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = self.temp_dir.name
        self.orthotect_cli = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin', 'orthotect.js'))

        # Initialize a real git repo
        subprocess.run(['git', 'init', self.repo_dir], capture_output=True, check=True)
        # Configure local git user to allow test commits
        subprocess.run(['git', '-C', self.repo_dir, 'config', 'user.name', 'Orthotect Test'], capture_output=True, check=True)
        subprocess.run(['git', '-C', self.repo_dir, 'config', 'user.email', 'test@orthotect.dev'], capture_output=True, check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_hooks_install_and_uninstall(self):
        """Verify orthotect hooks install writes pre-commit and uninstall safely removes it."""
        hook_path = os.path.join(self.repo_dir, '.git', 'hooks', 'pre-commit')
        self.assertFalse(os.path.exists(hook_path))

        # 1. Install hook
        res = subprocess.run(['node', self.orthotect_cli, 'hooks', 'install', self.repo_dir], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Error: {res.stderr}\n{res.stdout}")
        self.assertTrue(os.path.exists(hook_path))
        self.assertTrue(os.access(hook_path, os.X_OK))

        with open(hook_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("npx orthotect verify", content)
        self.assertIn("pre-commit", content.lower())

        # 2. Uninstall hook
        res_un = subprocess.run(['node', self.orthotect_cli, 'hooks', 'uninstall', self.repo_dir], capture_output=True, text=True)
        self.assertEqual(res_un.returncode, 0, f"Error: {res_un.stderr}\n{res_un.stdout}")
        self.assertFalse(os.path.exists(hook_path))

    def test_non_git_repo_rejected(self):
        """orthotect hooks install in non-git directory should fail gracefully with clear error."""
        non_git = os.path.join(self.repo_dir, 'plain_folder')
        os.makedirs(non_git, exist_ok=True)
        # Delete .git from repo_dir to ensure no git ancestor
        shutil.rmtree(os.path.join(self.repo_dir, '.git'))

        res = subprocess.run(['node', self.orthotect_cli, 'hooks', 'install', non_git], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("missing .git directory", res.stderr)

if __name__ == '__main__':
    unittest.main()
