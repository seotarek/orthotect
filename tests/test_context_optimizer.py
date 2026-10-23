#!/usr/bin/env python3
"""
Unit and Integration Tests for Orthotect Context Architecture & Token Optimizer
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
import subprocess

from core.context_optimizer import (
    estimate_tokens,
    extract_symbols,
    analyze_file_density,
    semantic_chunk,
    generate_context_skeleton
)

class TestContextOptimizer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="orthotect_ctx_test_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_estimate_tokens_empty_and_short(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("   \n\t  "), 0)
        self.assertGreaterEqual(estimate_tokens("hello world"), 2)

    def test_estimate_tokens_code_calibration(self):
        sample_code = """
        function calculateLayout(containerWidth, paddingInline) {
            const innerWidth = containerWidth - (paddingInline * 2);
            return Math.max(0, innerWidth);
        }
        """
        tokens = estimate_tokens(sample_code)
        # Should be reasonable ~30-50 tokens
        self.assertGreaterEqual(tokens, 20)
        self.assertLessEqual(tokens, 75)

    def test_extract_symbols_js_and_ts(self):
        js_code = """
        export function initTheme(mode) { return mode; }
        export class LayoutEngine { constructor() {} }
        const renderHeader = () => <div>Header</div>;
        """
        symbols = extract_symbols(js_code, '.js')
        names = [s['name'] for s in symbols]
        self.assertIn('initTheme', names)
        self.assertIn('LayoutEngine', names)
        self.assertIn('renderHeader', names)

    def test_extract_symbols_python(self):
        py_code = """
        def compute_metrics(data):
            pass

        class AuditRunner:
            def run(self):
                pass
        """
        symbols = extract_symbols(py_code, '.py')
        names = [s['name'] for s in symbols]
        self.assertIn('compute_metrics', names)
        self.assertIn('AuditRunner', names)

    def test_analyze_file_density_recommendations(self):
        # Small content -> SAFE_SINGLE_TURN_READ
        small_code = "export const PI = 3.14159;\nexport const TAU = 6.28318;"
        res_small = analyze_file_density(small_code, is_content=True, ext='.js')
        self.assertEqual(res_small['recommendation'], "SAFE_SINGLE_TURN_READ")

        # Large content -> CHUNK_OR_SKELETON_REQUIRED
        large_code = "\n".join([f"function fn_{i}() {{ return {i} * 2; }}" for i in range(150)])
        res_large = analyze_file_density(large_code, is_content=True, ext='.js')
        self.assertIn(res_large['recommendation'], ("TARGETED_SLICES_PREFERRED", "CHUNK_OR_SKELETON_REQUIRED"))
        self.assertGreaterEqual(res_large['estimated_tokens'], 400)

    def test_semantic_chunking_boundaries(self):
        code_lines = []
        for i in range(10):
            code_lines.append(f"export function processStep_{i}() {{")
            for j in range(8):
                code_lines.append(f"  const step_{j} = computeValue({i}, {j});")
            code_lines.append("  return step_0;\n}")

        full_code = "\n".join(code_lines)
        chunks = semantic_chunk(full_code, max_tokens=150, is_content=True, ext='.js')
        self.assertGreater(len(chunks), 1, "Should partition into multiple chunks")

        # Ensure chunks start and end at logical lines
        for idx, c in enumerate(chunks, 1):
            self.assertEqual(c['chunk_index'], idx)
            self.assertGreater(c['lines_count'], 0)
            self.assertGreater(c['estimated_tokens'], 0)

    def test_generate_context_skeleton_compression(self):
        # Create mock file structure
        sub_dir = os.path.join(self.temp_dir, 'components')
        os.makedirs(sub_dir)

        f1 = os.path.join(sub_dir, 'Button.js')
        with open(f1, 'w') as f:
            f.write("""
            export function Button(props) {
                const { label, onClick, variant = 'primary' } = props;
                console.log('Rendering button with variant:', variant);
                const className = `btn btn-${variant}`;
                return `<button class="${className}" onclick="${onClick}">${label}</button>`;
            }
            export function IconButton(props) {
                return `<button class="btn-icon">${props.icon}</button>`;
            }
            """)

        f2 = os.path.join(sub_dir, 'Modal.py')
        with open(f2, 'w') as f:
            f.write("""
            class ModalDialog:
                def __init__(self, title, content):
                    self.title = title
                    self.content = content
                    self.is_open = False

                def open(self):
                    self.is_open = True
                    return {"status": "opened", "title": self.title}

                def close(self):
                    self.is_open = False
                    return {"status": "closed"}
            """)

        skeleton = generate_context_skeleton(self.temp_dir)
        self.assertEqual(skeleton['total_files'], 2)
        self.assertGreater(skeleton['total_estimated_tokens'], 0)
        self.assertGreater(skeleton['skeleton_tokens'], 0)
        self.assertGreater(skeleton['compression_ratio'], 0.0)
        self.assertIn("Button.js", skeleton['formatted_view'])
        self.assertIn("Modal.py", skeleton['formatted_view'])

    def test_cli_execution_inspect_and_skeleton(self):
        sample_file = os.path.join(self.temp_dir, 'test.py')
        with open(sample_file, 'w') as f:
            f.write("def hello():\n    return 'world'\n")

        # CLI inspect
        res = subprocess.run([sys.executable, 'core/context_optimizer.py', 'inspect', sample_file, '--json'],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data['file'], 'test.py')
        self.assertEqual(data['symbol_count'], 1)

        # CLI skeleton
        res_skel = subprocess.run([sys.executable, 'core/context_optimizer.py', 'skeleton', self.temp_dir, '--json'],
                                  capture_output=True, text=True)
        self.assertEqual(res_skel.returncode, 0)
        data_skel = json.loads(res_skel.stdout)
        self.assertEqual(data_skel['total_files'], 1)

if __name__ == '__main__':
    unittest.main()
