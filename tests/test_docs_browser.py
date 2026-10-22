import unittest
import os
import shutil
import subprocess

class TestDocsBrowserPlatform(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.docs_html = os.path.join(self.root_dir, 'docs', 'index.html')

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
        self.chrome_path = None
        for c in candidates:
            if c and os.path.exists(c):
                self.chrome_path = c
                break

        is_ci = os.environ.get('CI') == 'true' or 'GITHUB_ACTIONS' in os.environ
        if not self.chrome_path:
            if is_ci:
                self.fail("Mandatory Browser Execution Failed: No Chrome/Chromium binary found in CI. Silent skipping prohibited.")
            else:
                self.skipTest("Google Chrome / Chromium binary not found on local system")

    def test_docs_7_views_navigation_and_zero_console_errors(self):
        """Verify navigation across all 7 views in docs/ without any JS errors."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          const errors = [];
          page.on('console', msg => {{
            if (msg.type() === 'error') errors.push(msg.text());
          }});
          page.on('pageerror', err => errors.push(err.message));

          await page.goto('file://{self.docs_html}');

          // Verify default route (view-home is active)
          const homeActive = await page.$eval('#view-home', el => el.classList.contains('active'));
          if (!homeActive) throw new Error('Home view not active initially');

          // Navigate to all routes
          const routes = ['catalog', 'playground', 'builder', 'gallery', 'gates', 'install', 'home'];
          for (const r of routes) {{
            await page.evaluate(route => window.location.hash = '#' + route, r);
            await page.waitForTimeout(60);
            const isActive = await page.$eval('#view-' + r, el => el.classList.contains('active'));
            if (!isActive) throw new Error(`View #${{r}} failed to become active`);
          }}

          await browser.close();
          if (errors.length > 0) {{
            throw new Error('Console errors encountered: ' + errors.join('; '));
          }}
          console.log('SUCCESS_ALL_VIEWS');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Docs views navigation failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_ALL_VIEWS", res.stdout)

    def test_theme_and_bidi_controls_in_real_browser(self):
        """Verify theme switching, BiDi toggle, and localStorage persistence in real Chromium."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');

          // 1. Theme Toggle
          const initialTheme = await page.$eval('html', el => el.getAttribute('data-theme'));
          await page.click('#themeToggleBtn');
          const secondTheme = await page.$eval('html', el => el.getAttribute('data-theme'));
          if (initialTheme === secondTheme) throw new Error('Theme toggle failed to change data-theme');

          // 2. BiDi Toggle
          const initialDir = await page.$eval('html', el => el.getAttribute('dir'));
          await page.click('#bidiToggleBtn');
          const rtlDir = await page.$eval('html', el => el.getAttribute('dir'));
          if (rtlDir !== 'rtl') throw new Error(`Expected dir=rtl after click, got ${{rtlDir}}`);

          // Verify Arabic text updated
          const navHomeText = await page.$eval('#navHome', el => el.textContent);
          if (!navHomeText.includes('الرئيسية')) throw new Error(`Expected Arabic text in navHome, got: ${{navHomeText}}`);

          // 3. Reload and verify localStorage persistence
          await page.reload();
          const persistedDir = await page.$eval('html', el => el.getAttribute('dir'));
          if (persistedDir !== 'rtl') throw new Error(`Expected persisted rtl, got ${{persistedDir}}`);

          await browser.close();
          console.log('SUCCESS_THEME_BIDI');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Theme/BiDi controls failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_THEME_BIDI", res.stdout)

    def test_playground_component_tabs_and_data_states(self):
        """Verify interactive playground component switching and data table state machine."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}#playground');
          await page.waitForTimeout(100);

          // 1. Switch to datatable component
          await page.click('.pg-btn[data-comp="datatable"]');
          await page.waitForTimeout(80);
          const badge = await page.$eval('#pgSkillBadge', el => el.textContent);
          if (!badge.includes('orthotect-fsm')) throw new Error('Expected orthotect-fsm badge for datatable');

          // 2. Click state buttons in data table
          await page.click('#dtBtnSkeleton');
          await page.waitForTimeout(50);
          const hasSkeleton = await page.$eval('#dtDynamicArea', el => el.innerHTML.includes('skeleton'));
          if (!hasSkeleton) throw new Error('Skeleton loading state failed to render');

          await page.click('#dtBtnEmpty');
          await page.waitForTimeout(50);
          const hasEmpty = await page.$eval('#dtDynamicArea', el => el.innerHTML.includes('No matching records'));
          if (!hasEmpty) throw new Error('Empty state failed to render');

          await page.click('#dtBtnError');
          await page.waitForTimeout(50);
          const hasError = await page.$eval('#dtDynamicArea', el => el.innerHTML.includes('Data Pipeline Failure'));
          if (!hasError) throw new Error('Error state failed to render');

          await page.click('#dtBtnActive');
          await page.waitForTimeout(50);
          const hasActive = await page.$eval('#dtDynamicArea', el => el.innerHTML.includes('<table'));
          if (!hasActive) throw new Error('Active table failed to render');

          // 3. Switch to CRM and E-commerce
          await page.click('.pg-btn[data-comp="crm"]');
          await page.waitForTimeout(60);
          await page.click('.pg-btn[data-comp="ecommerce"]');
          await page.waitForTimeout(60);

          await browser.close();
          console.log('SUCCESS_PLAYGROUND');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Playground interaction failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_PLAYGROUND", res.stdout)

    def test_skill_builder_live_markdown_generation(self):
        """Verify skill builder dynamic markdown generation and field updating."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}#builder');
          await page.waitForTimeout(100);

          // Change skill name
          await page.fill('#sbName', 'autonomous-k8s-agent');
          await page.waitForTimeout(100);

          const preview = await page.$eval('#sbMarkdownPreview', el => el.textContent);
          if (!preview.includes('name: autonomous-k8s-agent')) {{
            throw new Error('Markdown preview did not update with new skill name');
          }}

          // Toggle off a gate and verify preview updates
          await page.click('#gateSlop');
          await page.waitForTimeout(100);
          const updatedPreview = await page.$eval('#sbMarkdownPreview', el => el.textContent);
          if (updatedPreview.includes('Anti-Slop Pattern Inspector')) {{
            throw new Error('Unchecked gate still appeared in preview');
          }}

          await browser.close();
          console.log('SUCCESS_BUILDER');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Skill builder test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_BUILDER", res.stdout)

    def test_docs_modal_dialog_focus_trap_and_lifecycle(self):
        """Verify accessible modal dialog inside docs/ with focus trapping, escape, and double-submit lock."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}#playground');
          await page.waitForTimeout(100);

          // Switch to modal demo component
          await page.click('.pg-btn[data-comp="modal"]');
          await page.waitForTimeout(80);

          // Click open modal button
          await page.click('#pgTriggerModalBtn');
          await page.waitForTimeout(100);

          const isVisible = await page.$eval('#docsModalBackdrop', el => el.style.display !== 'none');
          if (!isVisible) throw new Error('Modal backdrop is not visible after trigger');

          // Check focus trap
          await page.keyboard.press('Tab');
          await page.keyboard.press('Tab');
          const isContained = await page.evaluate(() => {{
            const active = document.activeElement;
            const modal = document.getElementById('docsModalBackdrop');
            return modal && modal.contains(active);
          }});
          if (!isContained) throw new Error('Focus escaped modal dialog');

          // Press escape
          await page.keyboard.press('Escape');
          await page.waitForTimeout(100);
          const isClosed = await page.$eval('#docsModalBackdrop', el => el.style.display === 'none');
          if (!isClosed) throw new Error('Modal did not close on Escape');

          await browser.close();
          console.log('SUCCESS_DOCS_MODAL');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Docs modal dialog test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_DOCS_MODAL", res.stdout)

    def test_responsive_viewports_no_horizontal_overflow(self):
        """Verify responsive layout across Mobile, Tablet, and Desktop with ZERO horizontal overflow."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          const viewports = [
            {{ name: 'mobile', width: 375, height: 667 }},
            {{ name: 'tablet', width: 768, height: 1024 }},
            {{ name: 'desktop', width: 1440, height: 900 }}
          ];

          for (const vp of viewports) {{
            await page.setViewportSize({{ width: vp.width, height: vp.height }});
            await page.goto('file://{self.docs_html}');
            await page.waitForTimeout(100);

            const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
            if (scrollWidth > vp.width + 1) {{
              throw new Error(`Horizontal overflow detected in ${{vp.name}}: scrollWidth=${{scrollWidth}} > windowWidth=${{vp.width}}`);
            }}
          }}

          await browser.close();
          console.log('SUCCESS_RESPONSIVE_OVERFLOW');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Responsive overflow test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_RESPONSIVE_OVERFLOW", res.stdout)

    def test_skill_builder_empty_form_rejection(self):
        """Skill Builder must reject Download and show field errors when required fields are empty."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');

          // Navigate to builder view
          await page.evaluate(() => window.location.hash = '#builder');
          await page.waitForTimeout(80);

          // Clear the name field
          const nameInput = await page.$('#sbName');
          if (!nameInput) throw new Error('sbName input not found');
          await nameInput.fill('');

          // Also clear description
          const descInput = await page.$('#sbDesc');
          if (descInput) {{ await descInput.fill(''); }}

          // Also clear steps
          const stepsInput = await page.$('#sbSteps');
          if (stepsInput) {{ await stepsInput.fill(''); }}

          // Badge should now say Incomplete
          await page.waitForTimeout(100);
          const badge = await page.$eval('#previewStatusBadge', el => el.textContent);
          if (!badge.includes('Incomplete')) throw new Error('Badge should say Incomplete when fields empty, got: ' + badge);

          // Click Download — should be BLOCKED (no file download, error shown)
          let downloadFired = false;
          page.on('download', () => {{ downloadFired = true; }});
          await page.click('#btnDownloadSkill');
          await page.waitForTimeout(200);

          if (downloadFired) throw new Error('Download must be BLOCKED when required fields are empty');

          // Check that a field error element was injected for sbName
          const errorExists = await page.$('#sbNameError');
          if (!errorExists) throw new Error('Field error #sbNameError must appear after blocked download attempt');

          // Now fill in valid data and verify download is ALLOWED
          await nameInput.fill('my-valid-skill');
          if (descInput) await descInput.fill('A valid skill description.');
          if (stepsInput) await stepsInput.fill('1. Do the thing');
          await page.waitForTimeout(100);

          const badge2 = await page.$eval('#previewStatusBadge', el => el.textContent);
          if (!badge2.includes('Valid')) throw new Error('Badge should say Valid when all required fields filled, got: ' + badge2);

          await browser.close();
          console.log('SUCCESS_BUILDER_VALIDATION');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Skill builder validation test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_BUILDER_VALIDATION", res.stdout)

if __name__ == '__main__':
    unittest.main()
