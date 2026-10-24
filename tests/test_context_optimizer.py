#!/usr/bin/env python3
"""
Unit and Integration Tests for Orthotect Context Architecture & Token Optimizer
"""

import unittest
from unittest.mock import patch
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

    def test_extract_symbols_nesting_and_parent_scopes_js(self):
        js_code = """
        export class Controller {
            constructor() {
                this.ready = true;
            }
            dispatch(action) {
                const helper = () => action.type;
                return helper();
            }
        }
        export function standalone() { return false; }
        """
        symbols = extract_symbols(js_code, '.js')
        sym_map = {s['name']: s for s in symbols}

        self.assertTrue(sym_map['Controller']['is_top_level'])
        self.assertIsNone(sym_map['Controller']['parent'])

        self.assertFalse(sym_map['constructor']['is_top_level'])
        self.assertEqual(sym_map['constructor']['parent'], 'Controller')
        self.assertEqual(sym_map['constructor']['type'], 'method')

        self.assertFalse(sym_map['dispatch']['is_top_level'])
        self.assertEqual(sym_map['dispatch']['parent'], 'Controller')
        self.assertEqual(sym_map['dispatch']['type'], 'method')

        self.assertFalse(sym_map['helper']['is_top_level'])
        self.assertEqual(sym_map['helper']['parent'], 'dispatch')

        self.assertTrue(sym_map['standalone']['is_top_level'])
        self.assertIsNone(sym_map['standalone']['parent'])

    def test_extract_symbols_nesting_and_parent_scopes_py(self):
        py_code = """
        def top_level_fn():
            def inner_closure():
                return 42
            return inner_closure()

        class BaseService:
            def execute(self):
                pass
        """
        symbols = extract_symbols(py_code, '.py')
        sym_map = {s['name']: s for s in symbols}

        self.assertTrue(sym_map['top_level_fn']['is_top_level'])
        self.assertIsNone(sym_map['top_level_fn']['parent'])

        self.assertFalse(sym_map['inner_closure']['is_top_level'])
        self.assertEqual(sym_map['inner_closure']['parent'], 'top_level_fn')

        self.assertTrue(sym_map['BaseService']['is_top_level'])
        self.assertIsNone(sym_map['BaseService']['parent'])

        self.assertFalse(sym_map['execute']['is_top_level'])
        self.assertEqual(sym_map['execute']['parent'], 'BaseService')
        self.assertEqual(sym_map['execute']['type'], 'method')

    def test_semantic_chunking_preserves_class_nesting_and_continuation_breadcrumbs(self):
        # Create a large class with methods that exceed max_tokens
        js_code = """
        export class HeavyProcessor {
            phaseOne() {
                const payload1 = "heavy workload step one with multiple tokens";
                const payload2 = "continuing payload line for phase one";
                return payload1 + payload2;
            }

            phaseTwo() {
                const payload3 = "heavy workload step two with multiple tokens";
                const payload4 = "continuing payload line for phase two";
                return payload3 + payload4;
            }
        }
        export function finalize() {
            return "done";
        }
        """
        chunks = semantic_chunk(js_code, max_tokens=25, is_content=True, ext='.js')
        self.assertGreaterEqual(len(chunks), 2)

        # Subsequent chunk inside HeavyProcessor must have continuation breadcrumbs
        continuation_chunks = [c for c in chunks if c.get('continuation_of')]
        self.assertTrue(len(continuation_chunks) >= 1)
        for c in continuation_chunks:
            self.assertEqual(c['continuation_of'], 'class HeavyProcessor')
            self.assertIn("// [Context Continuation: class HeavyProcessor", c['content'])

    def test_generate_context_skeleton_depth_pruning(self):
        # Create d1/d2/d3/d4 directory structure
        deep_dir = os.path.join(self.temp_dir, 'lvl1', 'lvl2', 'lvl3', 'lvl4')
        os.makedirs(deep_dir)
        with open(os.path.join(deep_dir, 'Deep.js'), 'w') as f:
            f.write("export const deep = true;\n")

        with open(os.path.join(self.temp_dir, 'lvl1', 'Top.js'), 'w') as f:
            f.write("export const top = true;\n")

        # Depth 1: should include Top.js in lvl1, but NOT recurse into lvl2, lvl3, lvl4
        skel = generate_context_skeleton(self.temp_dir, max_depth=1)
        files = [f['path'] for f in skel['files']]
        self.assertIn(os.path.join('lvl1', 'Top.js'), files)
        self.assertNotIn(os.path.join('lvl1', 'lvl2', 'lvl3', 'lvl4', 'Deep.js'), files)
    def test_semantic_chunking_large_top_level_function_preserves_scope_metadata(self):
        js_lines = ["export function giantPipeline(input) {"]
        js_lines.append("  const stages = [];")
        for i in range(120):
            js_lines.append(f"  function nested_{i}(value) {{")
            js_lines.append(f"    const local_{i} = `segment {i} with braces {{not-scope}} and // slash`;")
            js_lines.append("    const regex = /https?:\\/\\/[a-z/]+/i;")
            js_lines.append(f"    return (() => value + {i})() + (regex.test('https://a') ? 1 : 0);")
            js_lines.append("  }")
            js_lines.append(f"  stages.push(nested_{i}(input));")
        js_lines.append("  return stages.join(',');")
        js_lines.append("}")
        js_lines.append("export function tail() { return 'done'; }")
        js_code = "\n".join(js_lines)

        chunks = semantic_chunk(js_code, max_tokens=180, is_content=True, ext='.js')
        self.assertGreater(len(chunks), 2)
        self.assertEqual(chunks[0]['start_line'], 1)
        self.assertIn("export function giantPipeline", chunks[0]['content'])
        continuation_chunks = [c for c in chunks if c.get('continuation_of') == 'function giantPipeline']
        self.assertGreaterEqual(len(continuation_chunks), 1)
        for c in continuation_chunks:
            self.assertEqual(c['context_path'], ['function giantPipeline'])
            self.assertIn('oversized_scope', c)
            self.assertEqual(c['oversized_scope']['name'], 'giantPipeline')
            self.assertEqual(c['split_strategy'] in ('nested_boundary', 'line_window'), True)

    def test_semantic_chunking_python_nested_functions_with_tabs(self):
        py_code = (
            "def outer(value):\n"
            "\ttotal = value\n"
            "\tdef inner_a(v):\n"
            "\t\tdef inner_b(x):\n"
            "\t\t\treturn x + 1\n"
            "\t\treturn inner_b(v)\n"
            "\tfor i in range(180):\n"
            "\t\ttotal += inner_a(i)\n"
            "\tlog_message = 'this is a deliberately long line to force token expansion in semantic chunking for python tabs'\n"
            "\tlog_message2 = 'another deliberately long line to keep the declaration above the max token threshold'\n"
            "\tlog_message3 = 'chunking should keep explicit continuation metadata for oversized declarations'\n"
            "\treturn total\n\n"
            "def sibling():\n"
            "\treturn 'ok'\n"
        )
        symbols = extract_symbols(py_code, '.py')
        names = [s['name'] for s in symbols]
        self.assertIn('outer', names)
        self.assertIn('inner_a', names)
        self.assertIn('inner_b', names)
        inner_b = [s for s in symbols if s['name'] == 'inner_b'][0]
        self.assertEqual(inner_b['parent'], 'inner_a')

        chunks = semantic_chunk(py_code, max_tokens=40, is_content=True, ext='.py')
        self.assertGreaterEqual(len(chunks), 2)
        continuation_chunks = [c for c in chunks if c.get('continuation_of') == 'function outer']
        self.assertTrue(continuation_chunks)
        for c in continuation_chunks:
            self.assertIn('function outer', " > ".join(c['context_path']))

    def test_extract_symbols_multiple_declarations_same_line(self):
        js_code = "export function a() { return 1; } export function b() { return 2; } const c = () => 3;"
        symbols = extract_symbols(js_code, '.js')
        names = [s['name'] for s in symbols]
        self.assertIn('a', names)
        self.assertIn('b', names)
        self.assertIn('c', names)

    def test_generate_context_skeleton_depth_pruning_stops_traversal(self):
        root = os.path.join(self.temp_dir, 'repo')
        os.makedirs(root)
        os.makedirs(os.path.join(root, 'lvl1', 'lvl2', 'lvl3'))
        with open(os.path.join(root, 'lvl1', 'Top.js'), 'w') as f:
            f.write("export const top = true;\n")
        with open(os.path.join(root, 'lvl1', 'lvl2', 'Deep.js'), 'w') as f:
            f.write("export const deep = true;\n")

        visited = []
        subdirs = {
            root: ['lvl1'],
            os.path.join(root, 'lvl1'): ['lvl2'],
            os.path.join(root, 'lvl1', 'lvl2'): ['lvl3'],
            os.path.join(root, 'lvl1', 'lvl2', 'lvl3'): []
        }
        files_map = {
            root: [],
            os.path.join(root, 'lvl1'): ['Top.js'],
            os.path.join(root, 'lvl1', 'lvl2'): ['Deep.js'],
            os.path.join(root, 'lvl1', 'lvl2', 'lvl3'): []
        }

        def instrumented_walk(_root_path):
            queue = [root]
            while queue:
                current = queue.pop(0)
                dirs = list(subdirs[current])
                files = list(files_map[current])
                visited.append(current)
                yield current, dirs, files
                for d in dirs:
                    queue.append(os.path.join(current, d))

        with patch('core.context_optimizer.os.walk', side_effect=instrumented_walk):
            skel = generate_context_skeleton(root, max_depth=1)

        self.assertIn(os.path.join(root, 'lvl1'), visited)
        self.assertNotIn(os.path.join(root, 'lvl1', 'lvl2'), visited)
        files = [f['path'] for f in skel['files']]
        self.assertIn(os.path.join('lvl1', 'Top.js'), files)
        self.assertNotIn(os.path.join('lvl1', 'lvl2', 'Deep.js'), files)

    def test_extract_symbols_ignores_declarations_in_comments_strings_templates_and_regex(self):
        js_code = '''
        // function ghostSingleLine() {}
        /* export class GhostMultiLine {} */
        const singleStr = 'function fakeInSingle() {}';
        const doubleStr = "export class FakeInDouble {}";
        const tpl = `
            function fakeInTpl() {}
            ${function realInExpression() { return 100; }}
            /* comment inside template */
        `;
        const regex1 = /function fakeInRegex() {}/g;
        const regex2 = /[a-z/\\-\\[\\]]+/i;
        const division = (a + b) / 2;
        export function realTopLevel() {
            return true;
        }
        '''
        symbols = extract_symbols(js_code, '.js')
        names = [s['name'] for s in symbols]
        self.assertNotIn('ghostSingleLine', names)
        self.assertNotIn('GhostMultiLine', names)
        self.assertNotIn('fakeInSingle', names)
        self.assertNotIn('FakeInDouble', names)
        self.assertNotIn('fakeInTpl', names)
        self.assertNotIn('fakeInRegex', names)

        self.assertIn('realInExpression', names)
        self.assertIn('realTopLevel', names)

    def test_extract_symbols_same_named_methods_and_nested_functions(self):
        js_code = '''
        export class ViewA {
            constructor() {}
            render() { return "A"; }
        }
        export class ViewB {
            constructor() {}
            render() { return "B"; }
        }
        export function outerA() {
            function helper() { return 1; }
            return helper();
        }
        export function outerB() {
            function helper() { return 2; }
            return helper();
        }
        '''
        symbols = extract_symbols(js_code, '.js')
        renders = [s for s in symbols if s['name'] == 'render']
        self.assertEqual(len(renders), 2)
        parents = {r['parent'] for r in renders}
        self.assertEqual(parents, {'ViewA', 'ViewB'})
        self.assertNotEqual(renders[0]['id'], renders[1]['id'])

        helpers = [s for s in symbols if s['name'] == 'helper']
        self.assertEqual(len(helpers), 2)
        h_parents = {h['parent'] for h in helpers}
        self.assertEqual(h_parents, {'outerA', 'outerB'})
        self.assertNotEqual(helpers[0]['id'], helpers[1]['id'])

    def test_extract_symbols_python_decorators_and_tab_indentation(self):
        py_code = (
            "@dataclass\n"
            "class Configuration:\n"
            "\tname: str\n\n"
            "@router.get('/endpoint')\n"
            "@authenticate(\n"
            "\tscope='admin',\n"
            "\tstrict=True\n"
            ")\n"
            "def handle_get():\n"
            "\t@memoize\n"
            "\tdef cached_helper():\n"
            "\t\treturn 42\n"
            "\treturn cached_helper()\n\n"
            "@router.post('/endpoint')\n"
            "def handle_post():\n"
            "\treturn True\n"
        )
        symbols = extract_symbols(py_code, '.py')
        names = [s['name'] for s in symbols]
        self.assertIn('Configuration', names)
        self.assertIn('handle_get', names)
        self.assertIn('cached_helper', names)
        self.assertIn('handle_post', names)

        cfg = [s for s in symbols if s['name'] == 'Configuration'][0]
        self.assertEqual(cfg['line'], 1)
        self.assertEqual(cfg['def_line'], 2)
        self.assertIn('@dataclass', cfg['decorators'])

        h_get = [s for s in symbols if s['name'] == 'handle_get'][0]
        self.assertEqual(h_get['line'], 5)
        self.assertEqual(h_get['def_line'], 10)
        self.assertEqual(len(h_get['decorators']), 5)

        cached = [s for s in symbols if s['name'] == 'cached_helper'][0]
        self.assertEqual(cached['parent'], 'handle_get')
        self.assertEqual(cached['line'], 11)

    def test_generate_context_skeleton_boundary_depths(self):
        root = os.path.join(self.temp_dir, 'depth_test')
        os.makedirs(os.path.join(root, 'd1', 'd2', 'd3'))
        with open(os.path.join(root, 'Root.js'), 'w') as f:
            f.write("export const root = true;\n")
        with open(os.path.join(root, 'd1', 'D1.js'), 'w') as f:
            f.write("export const d1 = true;\n")
        with open(os.path.join(root, 'd1', 'd2', 'D2.js'), 'w') as f:
            f.write("export const d2 = true;\n")

        # Depth 0: only root directory files
        skel0 = generate_context_skeleton(root, max_depth=0)
        files0 = [f['path'] for f in skel0['files']]
        self.assertIn('Root.js', files0)
        self.assertNotIn(os.path.join('d1', 'D1.js'), files0)

        # Depth 1: root and direct children
        skel1 = generate_context_skeleton(root, max_depth=1)
        files1 = [f['path'] for f in skel1['files']]
        self.assertIn('Root.js', files1)
        self.assertIn(os.path.join('d1', 'D1.js'), files1)
        self.assertNotIn(os.path.join('d1', 'd2', 'D2.js'), files1)

        # Depth 2: down to d2
        skel2 = generate_context_skeleton(root, max_depth=2)
        files2 = [f['path'] for f in skel2['files']]
        self.assertIn('Root.js', files2)
        self.assertIn(os.path.join('d1', 'D1.js'), files2)
        self.assertIn(os.path.join('d1', 'd2', 'D2.js'), files2)

    def test_semantic_chunking_oversized_nested_declaration(self):
        js_lines = ["export function masterController() {"]
        for i in range(120):
            js_lines.append(f"  function worker_{i}(data) {{ return data + {i}; }}")
        js_lines.append("  return worker_0('start');")
        js_lines.append("}")
        js_code = "\n".join(js_lines)

        chunks = semantic_chunk(js_code, max_tokens=100, is_content=True, ext='.js')
        self.assertGreaterEqual(len(chunks), 2)
        worker_chunks = [c for c in chunks if c.get('continuation_of') == 'function masterController']
        self.assertTrue(worker_chunks)
        for c in worker_chunks:
            self.assertEqual(c['context_path'], ['function masterController'])
            self.assertIn('oversized_scope', c)
            self.assertEqual(c['oversized_scope']['name'], 'masterController')

if __name__ == '__main__':
    unittest.main()
