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
            querySelector: (sel) => mockElement(sel.replace(/^[.#]/, '')),
            querySelectorAll: (sel) => [],
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

    def test_real_browser_playwright_modal_interaction(self):
        """Execute genuine headless browser interaction tests via Playwright and Chrome."""
        chrome_path = '/usr/bin/google-chrome'
        if not os.path.exists(chrome_path):
            self.skipTest("Google Chrome binary not found at /usr/bin/google-chrome")

        test_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.html_path}');
          
          // 1. Initial state closed
          const isClosed = await page.$eval('#modal-backdrop', el => el.getAttribute('aria-hidden') === 'true' && el.style.display === 'none');
          if (!isClosed) throw new Error('Initial state not closed');

          // 2. Open modal and check focus + inert
          await page.click('#btn-open-modal');
          await page.waitForTimeout(100);
          const isOpen = await page.$eval('#modal-backdrop', el => el.getAttribute('aria-hidden') === 'false' && el.classList.contains('is-open'));
          const focusedId = await page.evaluate(() => document.activeElement ? document.activeElement.id : null);
          const appShellInert = await page.$eval('.app-shell', el => el.hasAttribute('inert') && el.getAttribute('aria-hidden') === 'true');
          if (!isOpen || focusedId !== 'shard-name-input' || !appShellInert) {{
            throw new Error(`Open state failure: open=${{isOpen}}, focus=${{focusedId}}, inert=${{appShellInert}}`);
          }}

          // 3. Escape key handling and focus restoration
          await page.keyboard.press('Escape');
          await page.waitForTimeout(100);
          const closedAfterEsc = await page.$eval('#modal-backdrop', el => el.getAttribute('aria-hidden') === 'true' && el.style.display === 'none');
          const restoredId = await page.evaluate(() => document.activeElement ? document.activeElement.id : null);
          if (!closedAfterEsc || restoredId !== 'btn-open-modal') {{
            throw new Error(`Escape restore failure: closed=${{closedAfterEsc}}, restoredId=${{restoredId}}`);
          }}

          // 4. Open again and test submitting double-click lock
          await page.click('#btn-open-modal');
          await page.waitForTimeout(100);
          await page.fill('#shard-name-input', 'error');
          await page.click('#btn-submit-modal');
          const isLocked = await page.$eval('#btn-submit-modal', el => el.disabled);
          if (!isLocked) throw new Error('Submit lock failed to disable submit button');

          // 5. Error recovery transition
          await page.waitForTimeout(900);
          const hasError = await page.$eval('#modal-error-banner', el => el.style.display !== 'none' && el.textContent.includes('error'));
          const retryVisible = await page.$eval('#btn-retry-modal', el => el.style.display !== 'none');
          if (!hasError || !retryVisible) throw new Error('Error feedback state not reached');

          // 6. Retry and success path
          await page.fill('#shard-name-input', 'shard-prod-01');
          await page.click('#btn-retry-modal');
          await page.waitForTimeout(900);
          const successStatus = await page.$eval('#modal-status-text', el => el.textContent.includes('✓'));
          if (!successStatus) throw new Error('Success status feedback failed');

          // 7. Auto close
          await page.waitForTimeout(800);
          const finallyClosed = await page.$eval('#modal-backdrop', el => el.getAttribute('aria-hidden') === 'true');
          if (!finallyClosed) throw new Error('Modal failed to auto-close after success');

          await browser.close();
          console.log("REAL_BROWSER_E2E_PASSED");
        }}).catch(err => {{
          console.error("REAL_BROWSER_ERROR:", err);
          process.exit(1);
        }});
        """

        res = subprocess.run(['node', '--input-type=module', '-e', test_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Real browser test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("REAL_BROWSER_E2E_PASSED", res.stdout)

if __name__ == '__main__':
    unittest.main()

