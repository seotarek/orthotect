import unittest
import subprocess
import tempfile
import os
import json
import shutil
from core.compiler import compile_tokens, calculate_contrast

class TestTokenCompiler(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.cli_path = os.path.join(self.root_dir, 'bin', 'orthotect.js')
        self.tokens_dir = os.path.join(self.root_dir, 'core', 'tokens')
        self.temp_dir = tempfile.mkdtemp(prefix='compiler_test_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_contrast_math_calculation(self):
        # White vs Black should be 21.0:1
        cr = calculate_contrast('#ffffff', '#000000')
        self.assertAlmostEqual(cr, 21.0, places=1)

        # Low contrast pair #4b5563 vs #0d1117 should fail WCAG AA (around 2.3:1)
        cr_low = calculate_contrast('#4b5563', '#0d1117')
        self.assertLess(cr_low, 3.0)

    def test_compile_tokens_python_api_includes_verified_contrast(self):
        css = compile_tokens(self.tokens_dir)
        self.assertIn(":root {", css)
        self.assertIn('--ot-surface-canvas:', css)
        self.assertIn('--ot-action-primary:', css)
        self.assertIn('[data-theme="dark"] {', css)
        self.assertIn('@media (prefers-color-scheme: dark)', css)
        
        # Verify that compiler calculates and logs exact WCAG contrast in header comment
        self.assertIn("Semantic Contrast Verification (WCAG 2.2 Math):", css)
        self.assertIn("surface.canvas vs content.primary", css)
        self.assertIn("WCAG AAA", css)
        self.assertIn("gates/gate_contrast_wcag.py", css)

    def test_compile_tokens_with_low_contrast_fails(self):
        """Negative test: Token compilation must FAIL with ValueError if any semantic pair violates WCAG AA (4.5:1)."""
        bad_dir = os.path.join(self.temp_dir, 'bad_contrast_tokens')
        os.makedirs(bad_dir, exist_ok=True)
        
        prims = {
            "color": {
                "gray": {
                    "500": { "$value": "#777777" },
                    "600": { "$value": "#666666" }
                }
            }
        }
        sems = {
            "theme": {
                "light": {
                    "surface": {
                        "canvas": { "$value": "{color.gray.600}" },
                        "panel": { "$value": "{color.gray.600}" }
                    },
                    "action": {
                        "primary": { "$value": "{color.gray.600}" }
                    },
                    "content": {
                        # #777777 on #666666 gives approx 1.3:1 contrast (severe failure)
                        "primary": { "$value": "{color.gray.500}" },
                        "inverse": { "$value": "{color.gray.500}" }
                    }
                }
            }
        }
        with open(os.path.join(bad_dir, 'primitives.json'), 'w') as f:
            json.dump(prims, f)
        with open(os.path.join(bad_dir, 'semantics.json'), 'w') as f:
            json.dump(sems, f)

        with self.assertRaises(ValueError) as ctx:
            compile_tokens(bad_dir)
        self.assertIn("WCAG 2.2 Contrast Failure", str(ctx.exception))

    def test_circular_reference_raises(self):
        """Negative test: Circular references between tokens must raise ValueError."""
        dir_path = os.path.join(self.temp_dir, 'cycle_tokens')
        os.makedirs(dir_path, exist_ok=True)
        prims = {
            "color": {
                "a": { "$value": "{color.b}" },
                "b": { "$value": "{color.a}" }
            }
        }
        sems = {
            "theme": {
                "light": {
                    "surface": {
                        "canvas": { "$value": "{color.a}" },
                        "panel": { "$value": "{color.a}" }
                    },
                    "action": {
                        "primary": { "$value": "{color.a}" }
                    },
                    "content": {
                        "primary": { "$value": "{color.b}" },
                        "inverse": { "$value": "{color.b}" }
                    }
                }
            }
        }
        with open(os.path.join(dir_path, 'primitives.json'), 'w') as f:
            json.dump(prims, f)
        with open(os.path.join(dir_path, 'semantics.json'), 'w') as f:
            json.dump(sems, f)

        with self.assertRaises(ValueError) as ctx:
            compile_tokens(dir_path)
        self.assertIn("Circular reference detected", str(ctx.exception))

    def test_unresolved_reference_raises(self):
        """Negative test: Token reference to non-existent key must raise ValueError."""
        dir_path = os.path.join(self.temp_dir, 'missing_ref_tokens')
        os.makedirs(dir_path, exist_ok=True)
        prims = {
            "color": {
                "valid": { "$value": "#ffffff" }
            }
        }
        sems = {
            "theme": {
                "light": {
                    "surface": {
                        "canvas": { "$value": "{color.does_not_exist}" },
                        "panel": { "$value": "{color.valid}" }
                    },
                    "action": {
                        "primary": { "$value": "{color.valid}" }
                    },
                    "content": {
                        "primary": { "$value": "{color.valid}" },
                        "inverse": { "$value": "{color.valid}" }
                    }
                }
            }
        }
        with open(os.path.join(dir_path, 'primitives.json'), 'w') as f:
            json.dump(prims, f)
        with open(os.path.join(dir_path, 'semantics.json'), 'w') as f:
            json.dump(sems, f)

        with self.assertRaises(ValueError) as ctx:
            compile_tokens(dir_path)
        self.assertIn("Unresolved token reference", str(ctx.exception))

    def test_missing_required_semantic_token_raises(self):
        """Negative test: Theme missing mandatory semantic tokens (e.g. surface.panel) must raise ValueError."""
        dir_path = os.path.join(self.temp_dir, 'missing_sem_tokens')
        os.makedirs(dir_path, exist_ok=True)
        prims = {
            "color": {
                "white": { "$value": "#ffffff" },
                "black": { "$value": "#000000" }
            }
        }
        sems = {
            "theme": {
                "light": {
                    "surface": {
                        "canvas": { "$value": "{color.white}" }
                        # Missing surface.panel
                    },
                    "action": {
                        "primary": { "$value": "{color.black}" }
                    },
                    "content": {
                        "primary": { "$value": "{color.black}" },
                        "inverse": { "$value": "{color.white}" }
                    }
                }
            }
        }
        with open(os.path.join(dir_path, 'primitives.json'), 'w') as f:
            json.dump(prims, f)
        with open(os.path.join(dir_path, 'semantics.json'), 'w') as f:
            json.dump(sems, f)

        with self.assertRaises(ValueError) as ctx:
            compile_tokens(dir_path)
        self.assertIn("Missing required semantic token", str(ctx.exception))

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
        self.assertIn('Semantic Contrast Verification', content)

if __name__ == '__main__':
    unittest.main()
