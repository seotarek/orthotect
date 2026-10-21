import unittest
import subprocess
import tempfile
import os
import shutil
from core.compiler import compile_tokens

class TestTokenCompiler(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.cli_path = os.path.join(self.root_dir, 'bin', 'orthotect.js')
        self.tokens_dir = os.path.join(self.root_dir, 'core', 'tokens')
        self.temp_dir = tempfile.mkdtemp(prefix='compiler_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compile_tokens_python_api(self):
        css = compile_tokens(self.tokens_dir)
        self.assertIn(":root {", css)
        self.assertIn('--ot-surface-canvas:', css)
        self.assertIn('--ot-action-primary:', css)
        self.assertIn('[data-theme="dark"] {', css)
        self.assertIn('@media (prefers-color-scheme: dark)', css)

    def test_compile_missing_tokens_raises(self):
        empty_dir = os.path.join(self.temp_dir, 'empty')
        os.makedirs(empty_dir, exist_ok=True)
        with self.assertRaises(FileNotFoundError):
            compile_tokens(empty_dir)

    def test_compile_via_cli(self):
        out_file = os.path.join(self.temp_dir, 'output.css')
        res = subprocess.run(['node', self.cli_path, 'compile', self.tokens_dir, '--out', out_file],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('--ot-surface-canvas:', content)
        self.assertIn('--ot-action-danger:', content)

if __name__ == '__main__':
    unittest.main()
