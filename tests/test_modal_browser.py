import unittest
import os
import subprocess

class TestModalBrowserExecution(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.html_path = os.path.join(self.root_dir, 'examples', 'golden-showcase', 'index.html')

    def test_modal_elements_exist_before_script(self):
        with open(self.html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Modal elements must exist before the script to prevent null element reference crashes
        modal_idx = html.find('id="modal-backdrop"')
        script_idx = html.find('<script>')
        self.assertNotEqual(modal_idx, -1, "modal-backdrop element must exist")
        self.assertNotEqual(script_idx, -1, "<script> element must exist")
        self.assertLess(modal_idx, script_idx, "modal-backdrop must be defined BEFORE <script> in HTML order")

        # Elements required by the FSM controller
        required_ids = [
            'btn-open-modal',
            'modal-backdrop',
            'btn-close-modal',
            'btn-cancel-modal',
            'btn-submit-modal',
            'shard-name-input',
            'modal-status-text'
        ]
        for el_id in required_ids:
            self.assertIn(f'id="{el_id}"', html, f"Required element #{el_id} missing in markup")

    def test_modal_javascript_executes_without_null_errors(self):
        """Simulate browser DOM loading and event wiring in Node.js to verify zero null TypeError exceptions."""
        node_script = """
        const fs = require('fs');
        const html = fs.readFileSync(process.argv[1], 'utf-8');

        // Extract script content
        const scriptMatch = html.match(/<script>([\\s\\S]*?)<\\/script>/i);
        if (!scriptMatch) process.exit(1);

        const scriptContent = scriptMatch[1];

        // Mock Minimal DOM Environment
        const elements = {};
        const listeners = {};

        function mockElement(id, tag = 'div') {
            return {
                id,
                tagName: tag.toUpperCase(),
                classList: {
                    add: (cls) => {},
                    remove: (cls) => {},
                    contains: (cls) => false
                },
                setAttribute: (k, v) => {},
                getAttribute: (k) => 'light',
                addEventListener: (evt, cb) => {
                    if (!listeners[id]) listeners[id] = {};
                    listeners[id][evt] = cb;
                },
                querySelector: () => mockElement('inner'),
                querySelectorAll: () => [mockElement('btn1', 'button'), mockElement('inp1', 'input')],
                focus: () => {},
                disabled: false,
                value: 'shard-01',
                textContent: ''
            };
        }

        const requiredIds = [
            'toggle-theme', 'toggle-bidi', 'bidi-target', 'btn-deploy',
            'btn-open-modal', 'modal-backdrop', 'btn-close-modal',
            'btn-cancel-modal', 'btn-submit-modal', 'shard-name-input',
            'modal-status-text'
        ];
        requiredIds.forEach(id => { elements[id] = mockElement(id); });

        global.document = {
            getElementById: (id) => elements[id] || null,
            documentElement: mockElement('html'),
            addEventListener: (evt, cb) => {
                if (evt === 'DOMContentLoaded') cb();
            }
        };
        global.window = {
            addEventListener: (evt, cb) => {}
        };

        // Execute script - MUST NOT THROW ANY TypeError
        try {
            eval(scriptContent);
            console.log("SUCCESS_EVAL");
        } catch (e) {
            console.error("SCRIPT_ERROR:", e);
            process.exit(2);
        }
        """

        res = subprocess.run(['node', '-e', node_script, self.html_path],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Script threw error on execution: {res.stderr}")
        self.assertIn("SUCCESS_EVAL", res.stdout)

if __name__ == '__main__':
    unittest.main()
