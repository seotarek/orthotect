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

    def test_hero_benchmark_rejects_physical_bidi_violation(self):
        """Negative test: Injecting physical margin-left into live DOM must trigger Gate 2 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject physical directional property
          await page.evaluate(() => {{
            const div = document.createElement('div');
            div.setAttribute('style', 'margin-left: 28px;');
            document.body.appendChild(div);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s2 = await page.$eval('#heroStatusGate2', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s2.includes('FAIL')) throw new Error(`Expected Gate 2 to FAIL, got: ${{s2}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);

          console.log('SUCCESS_REJECT_PHYSICAL_BIDI');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative bidi test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_PHYSICAL_BIDI", res.stdout)

    def test_hero_benchmark_rejects_unbudgeted_media_violation(self):
        """Negative test: Injecting unbudgeted media element must trigger Gate 5 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject unbudgeted image lacking width/height and aspect-ratio
          await page.evaluate(() => {{
            const img = document.createElement('img');
            img.setAttribute('src', 'unbudgeted_sample.png');
            document.body.appendChild(img);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s5 = await page.$eval('#heroStatusGate5', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s5.includes('FAIL')) throw new Error(`Expected Gate 5 to FAIL, got: ${{s5}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);

          console.log('SUCCESS_REJECT_UNBUDGETED_MEDIA');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative media test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_UNBUDGETED_MEDIA", res.stdout)

    def test_hero_benchmark_rejects_anti_slop_emoji_button_violation(self):
        """Negative test: Injecting button with raw emoji must trigger Gate 4 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject raw emoji button
          await page.evaluate(() => {{
            const btn = document.createElement('button');
            btn.textContent = '🚀 Instant AI Magic';
            document.body.appendChild(btn);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s4 = await page.$eval('#heroStatusGate4', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s4.includes('FAIL')) throw new Error(`Expected Gate 4 to FAIL, got: ${{s4}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);

          console.log('SUCCESS_REJECT_ANTI_SLOP');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative slop test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_ANTI_SLOP", res.stdout)

    def test_hero_benchmark_rejects_contrast_violation(self):
        """Negative test: Mutating --ortho-text-primary to low-contrast color must trigger Gate 1 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Mutate primary text token to low contrast value matching canvas
          await page.evaluate(() => {{
            document.documentElement.style.setProperty('--ortho-text-primary', '#090d18');
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s1 = await page.$eval('#heroStatusGate1', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);
          const detail = await page.$eval('#heroDetailGate1', el => el.textContent);

          await browser.close();

          if (!s1.includes('FAIL')) throw new Error(`Expected Gate 1 to FAIL, got: ${{s1}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);
          if (!detail.includes('Contrast Violation')) throw new Error(`Expected Contrast Violation detail, got: ${{detail}}`);

          console.log('SUCCESS_REJECT_CONTRAST');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative contrast test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_CONTRAST", res.stdout)

    def test_hero_benchmark_rejects_fsm_integrity_violation(self):
        """Negative test: Removing allowClick lock from canonical FSM transition state must trigger Gate 3 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Mutate canonical FSM transition state (opening) in window.ORTHOTECT_CORE to remove allowClick lock
          await page.evaluate(() => {{
            if (window.ORTHOTECT_CORE && window.ORTHOTECT_CORE.fsm && window.ORTHOTECT_CORE.fsm['modal-dialog.json']) {{
              delete window.ORTHOTECT_CORE.fsm['modal-dialog.json'].states.opening.allowClick;
            }}
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s3 = await page.$eval('#heroStatusGate3', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);
          const detail = await page.$eval('#heroDetailGate3', el => el.textContent);

          await browser.close();

          if (!s3.includes('FAIL')) throw new Error(`Expected Gate 3 to FAIL, got: ${{s3}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);
          if (!detail.includes('FSM Integrity Error')) throw new Error(`Expected FSM Integrity Error detail, got: ${{detail}}`);

          console.log('SUCCESS_REJECT_FSM_INTEGRITY');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative FSM test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_FSM_INTEGRITY", res.stdout)

    def test_hero_benchmark_rejects_calc_zero_media_violation(self):
        """Negative test: Injecting media with non-reserving calc(0px) must trigger Gate 5 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject media with non-reserving calc(0px) dimensions
          await page.evaluate(() => {{
            const img = document.createElement('img');
            img.setAttribute('src', 'zero_res.png');
            img.style.width = 'calc(0px)';
            img.style.height = 'calc(0px)';
            document.body.appendChild(img);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s5 = await page.$eval('#heroStatusGate5', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s5.includes('FAIL')) throw new Error(`Expected Gate 5 to FAIL, got: ${{s5}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);

          console.log('SUCCESS_REJECT_CALC_ZERO_MEDIA');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative calc(0px) media test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_CALC_ZERO_MEDIA", res.stdout)

    def test_hero_benchmark_rejects_calc_net_zero_media_violation(self):
        """Negative test: Injecting media with net-zero calc(100% - 100%) must trigger Gate 5 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject media with net-zero calc(100% - 100%) dimensions
          await page.evaluate(() => {{
            const img = document.createElement('img');
            img.setAttribute('src', 'net_zero_res.png');
            img.style.width = 'calc(100% - 100%)';
            img.style.height = 'calc(100% - 100%)';
            document.body.appendChild(img);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s5 = await page.$eval('#heroStatusGate5', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s5.includes('FAIL')) throw new Error(`Expected Gate 5 to FAIL, got: ${{s5}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);

          console.log('SUCCESS_REJECT_CALC_NET_ZERO_MEDIA');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative calc(100% - 100%) media test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_CALC_NET_ZERO_MEDIA", res.stdout)

    def test_hero_benchmark_rejects_calc_invalid_syntax_violation(self):
        """Negative test: Injecting media with invalid syntax/type calc((10px) must trigger Gate 5 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject media with unbalanced parenthesis and invalid length*length calc
          await page.evaluate(() => {{
            const img = document.createElement('img');
            img.setAttribute('src', 'syntax_err.png');
            img.style.width = 'calc((10px)';
            img.style.height = 'calc(10px * 20px)';
            document.body.appendChild(img);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s5 = await page.$eval('#heroStatusGate5', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s5.includes('FAIL')) throw new Error(`Expected Gate 5 to FAIL, got: ${{s5}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);

          console.log('SUCCESS_REJECT_CALC_INVALID_SYNTAX');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative calc syntax test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_CALC_INVALID_SYNTAX", res.stdout)

    def test_hero_benchmark_rejects_calc_missing_whitespace_and_malformed_number(self):
        """Negative test: Injecting media with calc(10px-5px) or calc(1.2.3px) must trigger Gate 5 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject media with missing operator whitespace and malformed number
          await page.evaluate(() => {{
            const img1 = document.createElement('img');
            img1.setAttribute('src', 'no_space.png');
            img1.style.width = 'calc(10px-5px)';
            img1.style.height = 'calc(10px-5px)';
            document.body.appendChild(img1);

            const img2 = document.createElement('img');
            img2.setAttribute('src', 'malformed_dot.png');
            img2.style.width = 'calc(1.2.3px)';
            img2.style.height = 'calc(1.2.3px)';
            document.body.appendChild(img2);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s5 = await page.$eval('#heroStatusGate5', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s5.includes('FAIL')) throw new Error(`Expected Gate 5 to FAIL, got: ${{s5}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);

          console.log('SUCCESS_REJECT_CALC_WHITESPACE_AND_MALFORMED');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative calc whitespace test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_CALC_WHITESPACE_AND_MALFORMED", res.stdout)

    def test_hero_benchmark_rejects_calc_whitespace_after_unary_minus(self):
        """Negative test: Injecting media with calc(- 10px + 20px) must trigger Gate 5 rejection."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject media with space after unary minus
          await page.evaluate(() => {{
            const img = document.createElement('img');
            img.setAttribute('src', 'unary_space.png');
            img.style.width = 'calc(- 10px + 20px)';
            img.style.height = 'calc(10px + - 5px)';
            document.body.appendChild(img);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s5 = await page.$eval('#heroStatusGate5', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s5.includes('FAIL')) throw new Error(`Expected Gate 5 to FAIL, got: ${{s5}}`);
          if (badge !== 'GATE VIOLATIONS DETECTED') throw new Error(`Expected GATE VIOLATIONS DETECTED badge, got: ${{badge}}`);
          if (cert !== 'REJECTED') throw new Error(`Expected REJECTED cert, got: ${{cert}}`);

          console.log('SUCCESS_REJECT_CALC_UNARY_SPACE');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark negative calc unary space test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_REJECT_CALC_UNARY_SPACE", res.stdout)

    def test_hero_benchmark_accepts_calc_em_and_ex_units(self):
        """Positive test: Injecting media with valid calc(10em + 2px) and calc(10ex + 2px) passes Gate 5."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject media with valid em and ex calc expressions
          await page.evaluate(() => {{
            const img1 = document.createElement('img');
            img1.setAttribute('src', 'valid_em.png');
            img1.style.width = 'calc(10em + 2px)';
            img1.style.height = 'calc(10ex + 2px)';
            document.body.appendChild(img1);

            const img2 = document.createElement('img');
            img2.setAttribute('src', 'valid_mixed.png');
            img2.style.width = 'calc(1e2px + 2em)';
            img2.style.height = 'calc(1.5e1rem - 5ex)';
            document.body.appendChild(img2);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s5 = await page.$eval('#heroStatusGate5', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s5.includes('PASS')) throw new Error(`Expected Gate 5 to PASS with em/ex calc, got: ${{s5}}`);
          if (!badge.includes('LIVE CLIENT BENCHMARK')) throw new Error(`Expected LIVE CLIENT BENCHMARK badge, got: ${{badge}}`);
          if (cert !== 'CLIENT VERIFIED') throw new Error(`Expected CLIENT VERIFIED cert, got: ${{cert}}`);

          console.log('SUCCESS_ACCEPT_CALC_EM_EX');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark positive calc em/ex test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_ACCEPT_CALC_EM_EX", res.stdout)

    def test_hero_benchmark_accepts_direct_decimal_dimensions(self):
        """Positive test: Injecting media with direct decimal dimensions below 1 (0.5px, .5em) passes Gate 5."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage();
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Inject media with valid decimal dimensions below 1
          await page.evaluate(() => {{
            const img1 = document.createElement('img');
            img1.setAttribute('src', 'valid_decimal.png');
            img1.style.width = '0.5px';
            img1.style.height = '0.5em';
            document.body.appendChild(img1);

            const img2 = document.createElement('img');
            img2.setAttribute('src', 'valid_decimal_dot.png');
            img2.style.width = '.5rem';
            img2.style.height = '.5ex';
            document.body.appendChild(img2);
          }});

          // Run benchmark
          await page.click('#btnRunHeroBenchmark');
          await page.waitForTimeout(300);

          const s5 = await page.$eval('#heroStatusGate5', el => el.textContent);
          const badge = await page.$eval('#heroTerminalBadge', el => el.textContent);
          const cert = await page.$eval('#heroTerminalCert', el => el.textContent);

          await browser.close();

          if (!s5.includes('PASS')) throw new Error(`Expected Gate 5 to PASS with decimal dimensions, got: ${{s5}}`);
          if (!badge.includes('LIVE CLIENT BENCHMARK')) throw new Error(`Expected LIVE CLIENT BENCHMARK badge, got: ${{badge}}`);
          if (cert !== 'CLIENT VERIFIED') throw new Error(`Expected CLIENT VERIFIED cert, got: ${{cert}}`);

          console.log('SUCCESS_ACCEPT_DIRECT_DECIMAL');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Hero benchmark positive decimal dimensions test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_ACCEPT_DIRECT_DECIMAL", res.stdout)

    def test_mobile_drawer_dialog_and_focus_trap(self):
        """Verify mobile navigation drawer role="dialog", aria-modal="true", keyboard focus trap, and Escape restoration."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage({{ viewport: {{ width: 375, height: 667 }} }});
          await page.goto('file://{self.docs_html}');

          // Verify accessibility attributes on drawer
          const role = await page.$eval('#mobileNavDrawer', el => el.getAttribute('role'));
          const modal = await page.$eval('#mobileNavDrawer', el => el.getAttribute('aria-modal'));
          if (role !== 'dialog') throw new Error(`Expected role="dialog", got ${{role}}`);
          if (modal !== 'true') throw new Error(`Expected aria-modal="true", got ${{modal}}`);

          // Open drawer via hamburger button
          await page.click('#mobileMenuBtn');
          await page.waitForTimeout(100);

          const isOpen = await page.$eval('#mobileNavDrawer', el => el.classList.contains('open'));
          const ariaHidden = await page.$eval('#mobileNavDrawer', el => el.getAttribute('aria-hidden'));
          if (!isOpen || ariaHidden !== 'false') throw new Error('Drawer failed to open properly');

          // Verify focus is inside drawer (mobileMenuCloseBtn)
          const focusedId = await page.evaluate(() => document.activeElement ? document.activeElement.id : null);
          if (focusedId !== 'mobileMenuCloseBtn') throw new Error(`Expected focus on mobileMenuCloseBtn, got: ${{focusedId}}`);

          // Press Escape to close
          await page.keyboard.press('Escape');
          await page.waitForTimeout(100);

          const isClosed = await page.$eval('#mobileNavDrawer', el => !el.classList.contains('open'));
          if (!isClosed) throw new Error('Drawer failed to close on Escape');

          // Verify focus restored to mobileMenuBtn
          const restoredId = await page.evaluate(() => document.activeElement ? document.activeElement.id : null);
          if (restoredId !== 'mobileMenuBtn') throw new Error(`Expected focus restored to mobileMenuBtn, got: ${{restoredId}}`);

          await browser.close();
          console.log('SUCCESS_MOBILE_DRAWER_FOCUS_TRAP');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Mobile drawer dialog & focus trap test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_MOBILE_DRAWER_FOCUS_TRAP", res.stdout)

    def test_light_mode_color_contrast_and_playground_synchronization(self):
        """Verify Light Mode logo switching, playground viewport synchronization, and toolbar toggling."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage({{ viewport: {{ width: 1440, height: 900 }} }});
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // 1. Toggle to Light theme
          const initialTheme = await page.$eval('html', el => el.getAttribute('data-theme'));
          if (initialTheme !== 'light') {{
            while (await page.$eval('html', el => el.getAttribute('data-theme')) !== 'light') {{
              await page.click('#themeToggleBtn');
              await page.waitForTimeout(50);
            }}
          }}

          // Verify logo switched to logo-light.svg
          const logoSrc = await page.$eval('.brand-logo-img', el => el.getAttribute('src'));
          if (!logoSrc.includes('logo-light.svg')) {{
            throw new Error(`Expected logo-light.svg in Light mode, got: ${{logoSrc}}`);
          }}

          // 2. Navigate to #playground
          await page.evaluate(() => window.location.hash = '#playground');
          await page.waitForTimeout(100);

          // Verify playground viewport synchronized with light mode
          const vpTheme = await page.$eval('#pgViewport', el => el.getAttribute('data-theme'));
          if (vpTheme !== 'light') {{
            throw new Error(`Expected #pgViewport to sync to 'light', got: ${{vpTheme}}`);
          }}

          // 3. Test #pgThemeBtn toggles viewport theme
          await page.click('#pgThemeBtn');
          await page.waitForTimeout(50);
          const vpThemeAfterToggle = await page.$eval('#pgViewport', el => el.getAttribute('data-theme'));
          if (vpThemeAfterToggle === 'light') {{
            throw new Error('Clicking #pgThemeBtn failed to toggle playground viewport theme');
          }}

          // 4. Test #pgBidiBtn toggles viewport direction
          await page.click('#pgBidiBtn');
          await page.waitForTimeout(50);
          const vpDir = await page.$eval('#pgViewport', el => el.getAttribute('dir'));
          if (vpDir !== 'rtl') {{
            throw new Error(`Expected dir="rtl" after #pgBidiBtn click, got: ${{vpDir}}`);
          }}

          // 5. Test #pgDensityBtn cycles density
          await page.click('#pgDensityBtn');
          await page.waitForTimeout(50);
          const vpDensity = await page.$eval('#pgViewport', el => el.classList.contains('density-comfortable'));
          if (!vpDensity) {{
            throw new Error('Expected .density-comfortable on #pgViewport after #pgDensityBtn click');
          }}

          await browser.close();
          console.log('SUCCESS_LIGHT_MODE_SYNC');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Light mode sync test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_LIGHT_MODE_SYNC", res.stdout)

    def test_cli_terminal_quickstart_contrast_and_interactivity(self):
        """Verify .cli-box high contrast tokens in Light mode, tab command switching, and copy action."""
        node_script = f"""
        import('playwright-core').then(async ({{ chromium }}) => {{
          const browser = await chromium.launch({{
            executablePath: '{self.chrome_path}',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
          }});
          const page = await browser.newPage({{ viewport: {{ width: 1440, height: 900 }} }});
          await page.goto('file://{self.docs_html}');
          await page.waitForTimeout(100);

          // Set Light theme
          while (await page.$eval('html', el => el.getAttribute('data-theme')) !== 'light') {{
            await page.click('#themeToggleBtn');
            await page.waitForTimeout(50);
          }}

          // 1. Verify contrast on CLI box in Light mode
          const cliColors = await page.evaluate(() => {{
            const box = document.querySelector('.cli-box');
            const cmd = document.getElementById('cliCommandText');
            const prompt = document.querySelector('.cli-prompt');
            const activeTab = document.querySelector('.cli-tab.active');
            const inactiveTab = document.querySelectorAll('.cli-tab')[1];
            const copyBtn = document.getElementById('cliCopyBtn');

            function getRgb(str) {{
              const m = str.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
              return m ? [parseInt(m[1]), parseInt(m[2]), parseInt(m[3])] : [0, 0, 0];
            }}

            function lum([r, g, b]) {{
              const a = [r, g, b].map(v => {{
                v /= 255;
                return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
              }});
              return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
            }}

            function contrast(c1, c2) {{
              const l1 = lum(getRgb(c1));
              const l2 = lum(getRgb(c2));
              return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
            }}

            const boxBg = window.getComputedStyle(box).backgroundColor;
            const cmdColor = window.getComputedStyle(cmd).color;
            const promptColor = window.getComputedStyle(prompt).color;
            const activeColor = window.getComputedStyle(activeTab).color;
            const inactiveColor = window.getComputedStyle(inactiveTab).color;
            const copyColor = window.getComputedStyle(copyBtn).color;

            return {{
              boxBg,
              cmdContrast: contrast(boxBg, cmdColor),
              promptContrast: contrast(boxBg, promptColor),
              activeContrast: contrast(boxBg, activeColor),
              inactiveContrast: contrast(boxBg, inactiveColor),
              copyContrast: contrast(boxBg, copyColor)
            }};
          }});

          if (cliColors.cmdContrast < 7.0) {{
            throw new Error(`CLI command text contrast too low: ${{cliColors.cmdContrast.toFixed(2)}}:1 (min 7.0:1)`);
          }}
          if (cliColors.inactiveContrast < 4.5) {{
            throw new Error(`CLI inactive tab contrast too low: ${{cliColors.inactiveContrast.toFixed(2)}}:1 (min 4.5:1)`);
          }}
          if (cliColors.promptContrast < 7.0) {{
            throw new Error(`CLI prompt contrast too low: ${{cliColors.promptContrast.toFixed(2)}}:1 (min 7.0:1)`);
          }}

          // 2. Test interactive tab switching
          await page.click('.cli-tab[data-cmd="verify"]');
          await page.waitForTimeout(50);
          const verifyText = await page.$eval('#cliCommandText', el => el.textContent);
          if (!verifyText.includes('npx orthotect verify')) {{
            throw new Error(`Expected 'npx orthotect verify' after clicking verify tab, got: ${{verifyText}}`);
          }}

          await page.click('.cli-tab[data-cmd="compile"]');
          await page.waitForTimeout(50);
          const compileText = await page.$eval('#cliCommandText', el => el.textContent);
          if (!compileText.includes('npx orthotect compile')) {{
            throw new Error(`Expected 'npx orthotect compile' after clicking compile tab, got: ${{compileText}}`);
          }}

          // 3. Test Copy button
          await page.click('#cliCopyBtn');
          await page.waitForTimeout(50);
          const copyLabel = await page.$eval('#cliCopyBtn', el => el.textContent);
          if (!copyLabel.includes('Copied')) {{
            throw new Error(`Expected '✓ Copied' label after click, got: ${{copyLabel}}`);
          }}

          await browser.close();
          console.log('SUCCESS_CLI_CONTRAST_INTERACTIVITY');
        }}).catch(err => {{
          console.error(err);
          process.exit(1);
        }});
        """
        res = subprocess.run(['node', '--input-type=module', '-e', node_script],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI terminal contrast & interactivity test failed: {res.stderr}\n{res.stdout}")
        self.assertIn("SUCCESS_CLI_CONTRAST_INTERACTIVITY", res.stdout)

if __name__ == '__main__':
    unittest.main()

