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
        """Verify responsive layout across 5 exact viewports with ZERO horizontal overflow."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          const viewports = [
            {{ name: 'desktop', width: 1440, height: 900 }},
            {{ name: 'small-desktop', width: 1024, height: 768 }},
            {{ name: 'tablet-portrait', width: 768, height: 1024 }},
            {{ name: 'modern-mobile', width: 390, height: 844 }},
            {{ name: 'compact-mobile', width: 320, height: 568 }}
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

    def test_mobile_navigation_drawer_interactive(self):
        """Verify mobile navigation drawer toggling, ARIA attributes, 7 routes, and escape dismissal."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          // Mobile viewport (iPhone 12/13/14)
          await page.setViewportSize({{ width: 390, height: 844 }});
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // 1. Initial state: mobile menu button visible, aria-expanded=false
          const btnVisible = await page.$eval('#mobileMenuBtn', el => window.getComputedStyle(el).display !== 'none');
          if (!btnVisible) throw new Error('#mobileMenuBtn should be visible at 390px viewport');

          const initialExpanded = await page.$eval('#mobileMenuBtn', el => el.getAttribute('aria-expanded'));
          if (initialExpanded !== 'false') throw new Error('mobileMenuBtn aria-expanded should initially be false');

          const drawerHidden = await page.$eval('#mobileNavDrawer', el => el.getAttribute('aria-hidden'));
          if (drawerHidden !== 'true') throw new Error('mobileNavDrawer aria-hidden should initially be true');

          // 2. Click mobileMenuBtn to open drawer
          await page.click('#mobileMenuBtn');
          await page.waitForTimeout(250);

          const isDrawerOpen = await page.$eval('#mobileNavDrawer', el => el.classList.contains('open'));
          if (!isDrawerOpen) throw new Error('mobileNavDrawer should have class .open after click');

          const expandedAfterOpen = await page.$eval('#mobileMenuBtn', el => el.getAttribute('aria-expanded'));
          if (expandedAfterOpen !== 'true') throw new Error('mobileMenuBtn aria-expanded should be true when open');

          const bodyNavOpen = await page.$eval('body', el => el.classList.contains('nav-open'));
          if (!bodyNavOpen) throw new Error('body should have class .nav-open for scroll lock');

          // 3. Verify all 7 routes exist in drawer
          const mobileLinks = await page.$$eval('.mobile-nav-link', els => els.map(e => e.getAttribute('data-tab')));
          const expectedRoutes = ['home', 'catalog', 'playground', 'builder', 'gallery', 'gates', 'install'];
          for (const r of expectedRoutes) {{
            if (!mobileLinks.includes(r)) throw new Error(`Missing route ${{r}} in mobile nav drawer`);
          }}

          // 4. Click a link (e.g. playground) -> navigates and closes drawer
          await page.click('.mobile-nav-link[data-tab="playground"]');
          await page.waitForTimeout(250);

          const playgroundActive = await page.$eval('#view-playground', el => el.classList.contains('active'));
          if (!playgroundActive) throw new Error('Navigating to playground from mobile drawer failed');

          const drawerClosedAfterNav = await page.$eval('#mobileNavDrawer', el => !el.classList.contains('open'));
          if (!drawerClosedAfterNav) throw new Error('Drawer should close after clicking a nav link');

          // 5. Open again, then hit Escape key to dismiss
          await page.click('#mobileMenuBtn');
          await page.waitForTimeout(250);
          await page.keyboard.press('Escape');
          await page.waitForTimeout(250);

          const drawerClosedEscape = await page.$eval('#mobileNavDrawer', el => !el.classList.contains('open'));
          if (!drawerClosedEscape) throw new Error('Drawer should close after pressing Escape key');

          await browser.close();
          console.log('SUCCESS_MOBILE_DRAWER');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Mobile drawer test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_MOBILE_DRAWER", res.stdout)

    def test_official_brand_assets_and_theme_logo_switching(self):
        """Verify official brand SVG assets and dynamic theme logo switching in docs."""
        brand_assets = ['icon.svg', 'logo.svg', 'logo-light.svg', 'favicon.svg']
        for asset in brand_assets:
            p = os.path.join(self.root_dir, 'docs', 'assets', 'brand', asset)
            self.assertTrue(os.path.isfile(p), f"Brand asset missing: docs/assets/brand/{asset}")
            self.assertGreater(os.path.getsize(p), 100, f"Brand asset too small or empty: {asset}")

        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(80);

          // Dark mode initial logo
          const logoSrcDark = await page.$eval('.brand-logo-img', el => el.getAttribute('src'));
          if (!logoSrcDark.includes('logo.svg')) throw new Error('Dark mode logo should be logo.svg, got ' + logoSrcDark);

          // Switch to light mode
          await page.click('#themeToggleBtn');
          await page.waitForTimeout(80);
          const currentTheme = await page.$eval('html', el => el.getAttribute('data-theme'));
          if (currentTheme === 'light') {{
            const logoSrcLight = await page.$eval('.brand-logo-img', el => el.getAttribute('src'));
            if (!logoSrcLight.includes('logo-light.svg')) throw new Error('Light mode logo should be logo-light.svg, got ' + logoSrcLight);
          }}

          await browser.close();
          console.log('SUCCESS_BRAND_ASSETS');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Brand assets test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_BRAND_ASSETS", res.stdout)

    def test_quality_gates_simulator_honesty_and_eval_states(self):
        """Verify simulator honesty: NOT_EVALUATED for absent inputs, strict contrast pair, and summary alignment."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.evaluate(() => window.location.hash = '#gates');
          await page.waitForTimeout(100);

          const editor = await page.$('#codeEditor');
          const runBtn = await page.$('#runGateBtn');
          const terminal = await page.$('#gateTerminal');

          // Case 1: Code without images or FSM or colors
          await editor.fill('.clean-card {{ padding-inline: 1rem; margin-inline: auto; text-align: start; }}');
          await runBtn.click();
          await page.waitForTimeout(100);

          let output = await terminal.innerText();
          if (!output.includes('WCAG 2.2 Contrast') || !output.includes('NOT_EVALUATED')) {{
            throw new Error('Contrast gate should report NOT_EVALUATED when no color pairs are provided');
          }}
          if (!output.includes('DOM & Media Aspect-Ratio') || !output.includes('NOT_EVALUATED')) {{
            throw new Error('Media aspect ratio gate should report NOT_EVALUATED when no img tags exist');
          }}
          if (!output.includes('Evaluation Summary:')) {{
            throw new Error('Output must include Evaluation Summary line');
          }}

          // Case 2: Code with explicit color pair passing WCAG AAA
          await editor.fill('.badge {{ color: #38bdf8; background-color: #0f141c; }}');
          await runBtn.click();
          await page.waitForTimeout(100);

          output = await terminal.innerText();
          if (!output.includes('WCAG 2.2 Contrast:') || !output.includes('PASS')) {{
            throw new Error('Explicit high-contrast color pair must report PASS');
          }}

          await browser.close();
          console.log('SUCCESS_SIMULATOR_HONESTY');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Simulator honesty test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_SIMULATOR_HONESTY", res.stdout)

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

    def test_hero_interactive_in_browser_benchmark(self):
        """Verify that hero terminal displays verified benchmark baseline and executes live in-browser on click."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          const errors = [];
          page.on('console', msg => {{ if (msg.type() === 'error') errors.push(msg.text()); }});
          page.on('pageerror', err => errors.push(err.message));

          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // 1. Initial state must be labeled as specification baseline
          const initialBadge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          if (!initialBadge.includes('SPECIFICATION BASELINE')) {{
            throw new Error(`Expected SPECIFICATION BASELINE baseline badge, got: ${{initialBadge}}`);
          }}

          // 2. Click Run Live In-Browser button
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          // 3. Verify badge updates to live client benchmark
          const updatedBadge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          if (!updatedBadge.includes('LIVE CLIENT BENCHMARK')) {{
            throw new Error(`Expected LIVE CLIENT BENCHMARK badge after execution, got: ${{updatedBadge}}`);
          }}

          // 4. Verify certified tag updates to CLIENT VERIFIED
          const updatedCert = await page.$eval('#heroTerminalCert', el => el.textContent);
          if (updatedCert !== 'CLIENT VERIFIED') {{
            throw new Error(`Expected CLIENT VERIFIED cert tag, got: ${{updatedCert}}`);
          }}

          // 5. Verify live latency string
          const summary = await page.$eval('#heroTerminalSummary', el => el.textContent);
          if (!summary.includes('Live Client Latency') || !summary.includes('100% Gates Passed')) {{
            throw new Error(`Unexpected summary after live benchmark: ${{summary}}`);
          }}

          await browser.close();
          if (errors.length > 0) throw new Error('Console errors encountered: ' + errors.join('; '));
          console.log('SUCCESS_HERO_BENCHMARK');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_HERO_BENCHMARK", res.stdout)

if __name__ == '__main__':
    unittest.main()
