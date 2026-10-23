import unittest
import os
import shutil
import subprocess

class TestScaffoldBrowserExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        cls.cli_path = os.path.join(cls.root_dir, 'bin', 'orthotect.js')
        cls.out_html = '/tmp/test_browser_scaffold_fsm.html'

        # Generate scaffolded page
        if os.path.exists(cls.out_html):
            os.remove(cls.out_html)
        res = subprocess.run(['node', cls.cli_path, 'design', 'page', 'contemporary-product-saas', '--out', cls.out_html],
                             capture_output=True, text=True)
        if res.returncode != 0 or not os.path.exists(cls.out_html):
            raise RuntimeError(f"Failed to scaffold page for browser test: {res.stderr}\n{res.stdout}")

        # Find Chrome / Chromium executable
        candidates = [
            os.environ.get('CHROME_BIN'),
            os.environ.get('BROWSER_PATH'),
            '/usr/bin/google-chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            shutil.which('google-chrome'),
            shutil.which('chromium'),
            shutil.which('chromium-browser')
        ]
        cls.chrome_path = None
        for c in candidates:
            if c and os.path.exists(c):
                cls.chrome_path = c
                break

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.out_html):
            try:
                os.remove(cls.out_html)
            except OSError:
                pass

    def setUp(self):
        is_ci = os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ
        if not self.chrome_path:
            if is_ci:
                self.fail("Mandatory Browser Execution Failed: No Chrome/Chromium binary found in CI. Silent skipping prohibited.")
            else:
                self.skipTest("Google Chrome / Chromium binary not found on local system")

    def test_scaffolded_fsm_success_lifecycle_and_race_lock(self):
        """Verify scaffolded page FSM idle -> loading -> success -> idle lifecycle and double-click race lock in real Chromium."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          const errors = [];
          page.on('pageerror', err => errors.push(err.message));

          await page.goto('file://{self.out_html}');

          // 1. Initial State assertions
          const initialState = await page.$eval('[data-fsm="button"]', el => el.getAttribute('data-state'));
          const initialText = await page.$eval('[data-fsm="button"]', el => el.textContent.trim());
          const initialDisabled = await page.$eval('[data-fsm="button"]', el => el.disabled);
          const initialAnnouncer = await page.$eval('#fsm-status-announcer', el => el.textContent.trim());

          if (initialState !== 'idle') throw new Error(`Expected state 'idle', got '${{initialState}}'`);
          if (initialText !== 'Execute Action') throw new Error(`Expected text 'Execute Action', got '${{initialText}}'`);
          if (initialDisabled !== false) throw new Error(`Expected button to be enabled in idle state`);
          if (initialAnnouncer !== 'Action ready.') throw new Error(`Expected announcer 'Action ready.', got '${{initialAnnouncer}}'`);

          // 2. Click button to initiate transition -> loading
          await page.click('[data-fsm="button"]');

          const loadingState = await page.$eval('[data-fsm="button"]', el => el.getAttribute('data-state'));
          const loadingBusy = await page.$eval('[data-fsm="button"]', el => el.getAttribute('aria-busy'));
          const loadingDisabled = await page.$eval('[data-fsm="button"]', el => el.disabled);
          const loadingText = await page.$eval('[data-fsm="button"]', el => el.textContent.trim());

          if (loadingState !== 'loading') throw new Error(`Expected state 'loading', got '${{loadingState}}'`);
          if (loadingBusy !== 'true') throw new Error(`Expected aria-busy='true', got '${{loadingBusy}}'`);
          if (loadingDisabled !== true) throw new Error(`Expected button to be disabled in loading state`);
          if (loadingText !== 'Processing...') throw new Error(`Expected text 'Processing...', got '${{loadingText}}'`);

          // 3. Race condition verification: attempt double-click while in loading state
          await page.evaluate(() => {{
            const btn = document.querySelector('[data-fsm="button"]');
            btn.click();
          }});

          const stateAfterLockAttempt = await page.$eval('[data-fsm="button"]', el => el.getAttribute('data-state'));
          if (stateAfterLockAttempt !== 'loading') {{
            throw new Error(`Race condition guard failed: state mutated to '${{stateAfterLockAttempt}}' during double-click`);
          }}

          // 4. Wait for automatic SUCCESS transition
          await page.waitForFunction(() => {{
            const btn = document.querySelector('[data-fsm="button"]');
            return btn && btn.getAttribute('data-state') === 'success';
          }}, {{ timeout: 3000 }});

          const successText = await page.$eval('[data-fsm="button"]', el => el.textContent.trim());
          const successDisabled = await page.$eval('[data-fsm="button"]', el => el.disabled);
          const successBusy = await page.$eval('[data-fsm="button"]', el => el.getAttribute('aria-busy'));

          if (successText !== 'Action Verified') throw new Error(`Expected text 'Action Verified', got '${{successText}}'`);
          if (successDisabled !== false) throw new Error(`Expected button to be re-enabled in success state`);
          if (successBusy !== null) throw new Error(`Expected aria-busy to be removed in success state`);

          // 5. Wait for automatic RESET transition back to idle
          await page.waitForFunction(() => {{
            const btn = document.querySelector('[data-fsm="button"]');
            return btn && btn.getAttribute('data-state') === 'idle';
          }}, {{ timeout: 3000 }});

          const resetText = await page.$eval('[data-fsm="button"]', el => el.textContent.trim());
          if (resetText !== 'Execute Action') throw new Error(`Expected reset text 'Execute Action', got '${{resetText}}'`);

          await browser.close();

          if (errors.length > 0) {{
            throw new Error('Uncaught browser exceptions: ' + errors.join('; '));
          }}

          console.log('SCAFFOLD_FSM_SUCCESS_LIFECYCLE_VERIFIED');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Scaffolded FSM browser lifecycle failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SCAFFOLD_FSM_SUCCESS_LIFECYCLE_VERIFIED", res.stdout)

    def test_scaffolded_fsm_error_simulation_and_retry_recovery(self):
        """Verify scaffolded page FSM error simulation, transition to error state, and retry recovery in Chromium."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          const errors = [];
          page.on('pageerror', err => errors.push(err.message));

          // Open page with error simulation query parameter
          await page.goto('file://{self.out_html}?simulate=error');

          // Initial state is idle
          const initialStatus = await page.$eval('[data-fsm="button"]', el => el.getAttribute('data-state'));
          if (initialStatus !== 'idle') throw new Error(`Expected initial 'idle', got '${{initialStatus}}'`);

          // Click button to start loading
          await page.click('[data-fsm="button"]');
          const loadingState = await page.$eval('[data-fsm="button"]', el => el.getAttribute('data-state'));
          if (loadingState !== 'loading') throw new Error(`Expected 'loading', got '${{loadingState}}'`);

          // Wait for ERROR transition
          await page.waitForFunction(() => {{
            const btn = document.querySelector('[data-fsm="button"]');
            return btn && btn.getAttribute('data-state') === 'error';
          }}, {{ timeout: 3000 }});

          const errorText = await page.$eval('[data-fsm="button"]', el => el.textContent.trim());
          const errorDisabled = await page.$eval('[data-fsm="button"]', el => el.disabled);
          const errorAnnouncer = await page.$eval('#fsm-status-announcer', el => el.textContent.trim());

          if (errorText !== 'Retry Action') throw new Error(`Expected text 'Retry Action', got '${{errorText}}'`);
          if (errorDisabled !== false) throw new Error(`Expected button to be enabled for retry in error state`);
          if (errorAnnouncer !== 'Action failed. Click to retry.') throw new Error(`Unexpected announcer text: '${{errorAnnouncer}}'`);

          // Verify window.__orthotectFsm is accessible and reports 'error'
          const fsmState = await page.evaluate(() => window.__orthotectFsm.getState());
          if (fsmState !== 'error') throw new Error(`window.__orthotectFsm state was '${{fsmState}}', expected 'error'`);

          // Click button in error state -> triggers RETRY event -> enters loading
          await page.click('[data-fsm="button"]');
          const retriedState = await page.$eval('[data-fsm="button"]', el => el.getAttribute('data-state'));
          if (retriedState !== 'loading') throw new Error(`Expected state 'loading' after RETRY, got '${{retriedState}}'`);

          await browser.close();

          if (errors.length > 0) {{
            throw new Error('Uncaught browser exceptions: ' + errors.join('; '));
          }}

          console.log('SCAFFOLD_FSM_ERROR_RECOVERY_VERIFIED');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Scaffolded FSM error recovery failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SCAFFOLD_FSM_ERROR_RECOVERY_VERIFIED", res.stdout)

if __name__ == '__main__':
    unittest.main()
