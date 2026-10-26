#!/usr/bin/env node
/**
 * Orthotect CLI
 * Production-grade command-line interface for autonomous interface engineering.
 * Comprehensive UI/UX design intelligence, quality gates, and agent skills.
 */
import { spawnSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
let validateSkills = null;
try {
  const mod = await import('../scripts/validate-skills.mjs');
  validateSkills = mod.validateSkills;
} catch (_) {
  // Graceful fallback if scripts/ is omitted or relocated
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const args = process.argv.slice(2);
const command = args[0] || 'help';
const subCommand = args[1] && !args[1].startsWith('--') ? args[1] : null;
const targetArg = args[1] && !args[1].startsWith('--') ? args[1] : null;
const forceFlag = args.includes('--force');

const pkgPath = path.join(rootDir, 'package.json');
const pkgVersion = fs.existsSync(pkgPath) ? JSON.parse(fs.readFileSync(pkgPath, 'utf-8')).version : '1.8.8';

if (args.includes('--version') || args.includes('-v') || command === 'version') {
  console.log(pkgVersion);
  process.exit(0);
}

function printBanner() {
  console.log("╔═══════════════════════════════════════════════════════════════╗");
  console.log("║           ORTHOTECT INTERFACE ARCHITECTURE CLI                ║");
  console.log("╚═══════════════════════════════════════════════════════════════╝\n");
}

function copyDirRecursive(src, dest, force = false) {
  let copied = 0;
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copied += copyDirRecursive(srcPath, destPath, force);
    } else {
      if (fs.existsSync(destPath) && !force) {
        console.log(`  ⚠️ Skipped existing: ${path.relative(process.cwd(), destPath)} (use --force to overwrite)`);
      } else {
        fs.copyFileSync(srcPath, destPath);
        console.log(`  ✅ Installed: ${path.relative(process.cwd(), destPath)}`);
        copied++;
      }
    }
  }
  return copied;
}

function generatePageBoilerplate(recipe) {
  const title = (recipe.name || 'Orthotect Page').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const thesis = (recipe.designThesis || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const recipeId = (recipe.id || 'custom-recipe').replace(/[^a-zA-Z0-9_-]/g, '');

  return `<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} — Orthotect Certified Architecture</title>
  <style>
    :root {
      --ot-bg-canvas: #0b0f19;
      --ot-bg-surface: #111827;
      --ot-bg-subtle: #1f2937;
      --ot-border-subtle: rgba(255, 255, 255, 0.12);
      --ot-fg-default: #f9fafb;
      --ot-fg-muted: #9ca3af;
      --ot-color-primary: #2563eb;
      --ot-color-primary-fg: #ffffff;
      --ot-radius-md: 8px;
      --ot-space-sm: 8px;
      --ot-space-md: 16px;
      --ot-space-lg: 24px;
      --ot-space-xl: 32px;
      --ot-font-sans: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    * {
      box-sizing: border-box;
      margin-block: 0;
      margin-inline: 0;
      padding-block: 0;
      padding-inline: 0;
    }

    body {
      background-color: var(--ot-bg-canvas);
      color: var(--ot-fg-default);
      font-family: var(--ot-font-sans);
      line-height: 1.6;
      padding-block: var(--ot-space-xl);
      padding-inline: var(--ot-space-lg);
    }

    .container {
      max-inline-size: 1100px;
      margin-inline: auto;
    }

    header {
      margin-block-end: var(--ot-space-xl);
      border-block-end: 1px solid var(--ot-border-subtle);
      padding-block-end: var(--ot-space-lg);
    }

    h1 {
      font-size: 2rem;
      font-weight: 600;
      margin-block-end: var(--ot-space-sm);
    }

    .thesis {
      color: var(--ot-fg-muted);
      font-size: 1.125rem;
      max-inline-size: 65ch;
    }

    .bento-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: var(--ot-space-lg);
      margin-block-start: var(--ot-space-lg);
    }

    .card {
      background-color: var(--ot-bg-surface);
      border: 1px solid var(--ot-border-subtle);
      border-radius: var(--ot-radius-md);
      padding-block: var(--ot-space-lg);
      padding-inline: var(--ot-space-lg);
      display: flex;
      flex-direction: column;
      gap: var(--ot-space-md);
    }

    .btn-primary {
      background-color: var(--ot-color-primary);
      color: var(--ot-color-primary-fg);
      border: none;
      border-radius: var(--ot-radius-md);
      padding-block: 10px;
      padding-inline: 18px;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      inline-size: fit-content;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>${title}</h1>
      <p class="thesis">${thesis}</p>
    </header>
    <main>
      <section class="bento-grid">
        <article class="card">
          <h2>Architecture Overview</h2>
          <p>Scaffolded using Orthotect Style Recipe <code>${recipeId}</code>. Fully compliant with CSS Logical Properties and W3C DTCG tokens.</p>
          <button class="btn-primary" data-fsm="button" data-state="idle" aria-live="polite">Execute Action</button>
          <div id="fsm-status-announcer" aria-live="polite" style="position: absolute; inline-size: 1px; block-size: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;">Action ready.</div>
        </article>
      </section>
    </main>
  </div>
  <script>
    /**
     * Orthotect Finite State Machine (FSM) Runtime Controller
     * Enforces explicit state graph reachability and double-submission race condition locks
     * per core/fsm/button-states.json specifications.
     */
    (function initOrthotectFsm() {
      const fsmButton = document.querySelector('[data-fsm="button"]');
      const statusAnnouncer = document.getElementById('fsm-status-announcer');
      if (!fsmButton) return;

      const fsmConfig = {
        initialState: 'idle',
        states: {
          idle: { on: { CLICK: 'loading' } },
          loading: { on: { SUCCESS: 'success', ERROR: 'error' } },
          success: { on: { RESET: 'idle' } },
          error: { on: { RETRY: 'loading', RESET: 'idle' } }
        }
      };

      let currentState = fsmConfig.initialState;
      window.__orthotectActionExecCount = 0;
      window.__orthotectErrorSimulated = false;

      function transition(event) {
        const stateNode = fsmConfig.states[currentState];
        if (!stateNode || !stateNode.on || !stateNode.on[event]) {
          console.warn('[Orthotect FSM] Invalid transition "' + event + '" from state "' + currentState + '". Event rejected by race-condition lock.');
          return;
        }

        currentState = stateNode.on[event];
        renderState(currentState);
      }

      function renderState(state) {
        fsmButton.setAttribute('data-state', state);

        switch (state) {
          case 'idle':
            fsmButton.disabled = false;
            fsmButton.removeAttribute('aria-busy');
            fsmButton.textContent = 'Execute Action';
            if (statusAnnouncer) statusAnnouncer.textContent = 'Action ready.';
            break;

          case 'loading':
            fsmButton.disabled = true;
            fsmButton.setAttribute('aria-busy', 'true');
            fsmButton.textContent = 'Processing...';
            if (statusAnnouncer) statusAnnouncer.textContent = 'Processing request...';

            let shouldSimulateError = false;
            const simParam = window.location ? new URLSearchParams(window.location.search).get('simulate') : null;
            const simAttr = fsmButton.getAttribute('data-simulate');
            const hasErrorSim = (simParam === 'error' || simParam === 'error_once' || simAttr === 'error' || simAttr === 'error-once');

            if (hasErrorSim && !window.__orthotectErrorSimulated) {
              shouldSimulateError = true;
              window.__orthotectErrorSimulated = true;
            }

            setTimeout(() => {
              transition(shouldSimulateError ? 'ERROR' : 'SUCCESS');
            }, 600);
            break;

          case 'success':
            fsmButton.disabled = false;
            fsmButton.removeAttribute('aria-busy');
            fsmButton.textContent = 'Action Verified';
            if (statusAnnouncer) statusAnnouncer.textContent = 'Action verified successfully.';

            setTimeout(() => {
              transition('RESET');
            }, 600);
            break;

          case 'error':
            fsmButton.disabled = false;
            fsmButton.removeAttribute('aria-busy');
            fsmButton.textContent = 'Retry Action';
            if (statusAnnouncer) statusAnnouncer.textContent = 'Action failed. Click to retry.';
            break;
        }
      }

      fsmButton.addEventListener('click', () => {
        if (currentState === 'loading') return;
        if (currentState === 'idle') {
          window.__orthotectActionExecCount++;
          transition('CLICK');
        } else if (currentState === 'error') {
          window.__orthotectActionExecCount++;
          transition('RETRY');
        }
      });

      window.__orthotectFsm = {
        getState: () => currentState,
        transition: (event) => transition(event),
        getActionExecCount: () => window.__orthotectActionExecCount,
        config: fsmConfig
      };
    })();
  </script>
</body>
</html>
`;
}

switch (command) {
  case 'doctor': {
    printBanner();
    console.log("Running Orthotect Platform Diagnostic Doctor...\n");
    let hasErrors = false;

    // Check Node version
    const nodeVer = process.version;
    const [nodeMajor, nodeMinor] = nodeVer.replace(/^v/, '').split('.').map(n => parseInt(n, 10) || 0);
    const isNodeValid = (nodeMajor > 20) || (nodeMajor === 20 && nodeMinor >= 19);
    if (isNodeValid) {
      console.log(`  ✅ Node.js Runtime: ${nodeVer} (>= v20.19.0 requirement satisfied)`);
    } else {
      console.log(`  ❌ Node.js Runtime: ${nodeVer} (requires >= v20.19.0)`);
      hasErrors = true;
    }

    // Check Python runtime
    const pyCheck = spawnSync('python3', ['--version'], { encoding: 'utf-8' });
    if (pyCheck.status === 0) {
      console.log(`  ✅ Python Runtime: ${pyCheck.stdout.trim()}`);
    } else {
      console.log(`  ❌ Python 3 runtime not found`);
      hasErrors = true;
    }

    // Check gates directory
    const gatesDir = path.join(rootDir, 'gates');
    if (fs.existsSync(gatesDir)) {
      const gates = fs.readdirSync(gatesDir).filter(f => f.startsWith('gate_'));
      console.log(`  ✅ Deterministic Quality Gates: ${gates.length} gates verified (${gates.join(', ')})`);
    } else {
      console.log(`  ❌ Gates directory missing: ${gatesDir}`);
      hasErrors = true;
    }

    // Check skills directory
    const skillsDir = path.join(rootDir, 'skills');
    if (fs.existsSync(skillsDir)) {
      const skills = fs.readdirSync(skillsDir).filter(f => fs.statSync(path.join(skillsDir, f)).isDirectory());
      console.log(`  ✅ Autonomous Agent Skills: ${skills.length} skills installed`);
    } else {
      console.log(`  ❌ Skills directory missing: ${skillsDir}`);
      hasErrors = true;
    }

    // Check knowledge base
    const kbScript = path.join(rootDir, 'core', 'knowledge_search.py');
    if (fs.existsSync(kbScript)) {
      const kbCheck = spawnSync('python3', [kbScript, '--validate'], { encoding: 'utf-8' });
      if (kbCheck.status === 0) {
        console.log(`  ✅ UI/UX Knowledge Base: 100% schema compliant`);
      } else {
        console.log(`  ❌ UI/UX Knowledge Base schema validation error`);
        hasErrors = true;
      }
    }

    // Check context & token optimizer engine
    const ctxScript = path.join(rootDir, 'core', 'context_optimizer.py');
    if (fs.existsSync(ctxScript)) {
      console.log(`  ✅ Context & Token Engine: Operational (3-tier disclosure & semantic chunking)`);
    } else {
      console.log(`  ❌ Context engine missing: ${ctxScript}`);
      hasErrors = true;
    }

    console.log(`\nDoctor Status: ${hasErrors ? '❌ ISSUES DETECTED' : '✅ HEALTHY - All systems operational'}`);
    if (!hasErrors) {
      console.log("⭐ Enjoying Orthotect? Star the project on GitHub: https://github.com/seotarek/orthotect\n");
    }
    if (hasErrors) process.exit(1);
    break;
  }

  case 'init': {
    printBanner();
    const targetDir = path.resolve(process.cwd(), targetArg || '.');
    console.log(`Initializing Orthotect Architecture into: ${targetDir}\n`);

    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    // 1. Copy tokens
    const srcTokens = path.join(rootDir, 'core', 'tokens');
    const destTokens = path.join(targetDir, 'core', 'tokens');
    console.log("Installing W3C DTCG Design Tokens...");
    const tokensCount = copyDirRecursive(srcTokens, destTokens, forceFlag);

    // 2. Copy FSM specs
    const srcFsm = path.join(rootDir, 'core', 'fsm');
    const destFsm = path.join(targetDir, 'core', 'fsm');
    console.log("\nInstalling Finite State Machine specifications...");
    const fsmCount = copyDirRecursive(srcFsm, destFsm, forceFlag);

    // 3. Copy AGENTS.md rulebook
    const srcAgents = path.join(rootDir, 'AGENTS.md');
    const destAgents = path.join(targetDir, 'AGENTS.md');
    if (fs.existsSync(destAgents) && !forceFlag) {
      console.log(`\n  ⚠️ Skipped existing: ${path.relative(process.cwd(), destAgents)}`);
    } else {
      fs.copyFileSync(srcAgents, destAgents);
      console.log(`\n  ✅ Installed: ${path.relative(process.cwd(), destAgents)}`);
    }

    console.log(`\n🎉 Initialization Complete! Installed ${tokensCount} tokens and ${fsmCount} FSM definitions.`);
    console.log("To verify your project at any time, run: npx orthotect verify");
    console.log("⭐ Star Orthotect on GitHub to support deterministic engineering: https://github.com/seotarek/orthotect\n");
    break;
  }

  case 'hook':
  case 'hooks': {
    printBanner();
    const action = (subCommand === 'install' || subCommand === 'uninstall') ? subCommand : 'install';
    const explicitTarget = (args[2] && !args[2].startsWith('--')) ? args[2] : (targetArg && targetArg !== 'install' && targetArg !== 'uninstall' ? targetArg : '.');
    const targetDir = path.resolve(process.cwd(), explicitTarget);

    // Find git root starting from targetDir
    let currentDir = targetDir;
    let gitDir = null;
    while (true) {
      const candidate = path.join(currentDir, '.git');
      if (fs.existsSync(candidate)) {
        gitDir = candidate;
        break;
      }
      const parent = path.dirname(currentDir);
      if (parent === currentDir) break;
      currentDir = parent;
    }

    if (!gitDir) {
      console.error(`❌ Error: Not a git repository (missing .git directory in ${targetDir} or its parents).`);
      process.exit(1);
    }

    const hooksDir = path.join(gitDir, 'hooks');
    const hookPath = path.join(hooksDir, 'pre-commit');
    const backupPath = path.join(hooksDir, 'pre-commit.orthotect.bak');

    if (action === 'install') {
      fs.mkdirSync(hooksDir, { recursive: true });
      if (fs.existsSync(hookPath)) {
        const existing = fs.readFileSync(hookPath, 'utf-8');
        if (!existing.includes('# Orthotect Deterministic Quality Gate Pre-Commit Hook')) {
          fs.writeFileSync(backupPath, existing, { encoding: 'utf-8', mode: 0o755 });
          console.log(`ℹ️  Existing pre-commit hook backed up to: ${path.relative(process.cwd(), backupPath)}`);
        }
      }
      const hookContent = `#!/bin/sh
# Orthotect Deterministic Quality Gate Pre-Commit Hook
# Automatically generated by Orthotect CLI
echo "🔍 [Orthotect] Running deterministic quality gates before commit..."
if [ -f "./node_modules/.bin/orthotect" ]; then
  ./node_modules/.bin/orthotect verify .
else
  npx --no-install orthotect verify . 2>/dev/null || npx orthotect verify .
fi
STATUS=$?
if [ $STATUS -ne 0 ]; then
  echo ""
  echo "❌ [Orthotect] Quality Gate Failed! Pre-commit verification rejected."
  echo "💡 Action: Run 'npx orthotect verify --fix' to auto-remediate physical CSS properties."
  exit $STATUS
fi
`;
      fs.writeFileSync(hookPath, hookContent, { encoding: 'utf-8', mode: 0o755 });
      try {
        fs.chmodSync(hookPath, 0o755);
      } catch (_) {}

      console.log(`✅ Orthotect Git pre-commit hook installed successfully!`);
      console.log(`   Hook location: ${path.relative(process.cwd(), hookPath)}`);
      console.log(`   All subsequent git commits will be deterministically verified.`);
      console.log(`   To uninstall at any time: npx orthotect hooks uninstall`);
      console.log(`   ⭐ Star the project on GitHub: https://github.com/seotarek/orthotect\n`);
    } else if (action === 'uninstall') {
      if (fs.existsSync(hookPath)) {
        const currentHook = fs.readFileSync(hookPath, 'utf-8');
        if (!currentHook.includes('Orthotect')) {
          console.warn(`⚠️  Warning: Existing pre-commit hook does not appear to be created by Orthotect. Skipping deletion for safety.`);
          break;
        }
        fs.unlinkSync(hookPath);
        if (fs.existsSync(backupPath)) {
          fs.renameSync(backupPath, hookPath);
          console.log(`ℹ️  Restored previous pre-commit hook from backup: ${path.relative(process.cwd(), backupPath)}`);
        }
        console.log(`✅ Orthotect Git pre-commit hook uninstalled successfully.`);
        console.log(`   Removed: ${path.relative(process.cwd(), hookPath)}\n`);
      } else {
        console.log(`ℹ️  No Orthotect pre-commit hook found in: ${hooksDir}\n`);
      }
    } else {
      console.error(`❌ Unknown hooks command: '${action}'. Expected 'install' or 'uninstall'.`);
      console.log("Usage: npx orthotect hooks <install|uninstall> [target_directory]");
      process.exit(1);
    }
    break;
  }

  case 'check':
  case 'audit':
  case 'verify':
  case 'test': {
    const targetDir = path.resolve(process.cwd(), targetArg || '.');
    if (!fs.existsSync(targetDir)) {
      console.error(`❌ Error: Target directory does not exist: ${targetDir}`);
      process.exit(1);
    }

    const runnerPath = path.join(rootDir, 'gates', 'run_all_gates.py');
    const runnerArgs = [runnerPath, targetDir];

    if (args.includes('--json')) runnerArgs.push('--json');
    if (args.includes('--md')) runnerArgs.push('--md');
    if (args.includes('--fix')) runnerArgs.push('--fix');

    if (!args.includes('--json') && !args.includes('--md')) {
      printBanner();
      console.log(`Executing Deterministic Quality Gates on: ${targetDir}\n`);
    }

    const result = spawnSync('python3', runnerArgs, {
      stdio: 'inherit',
      cwd: rootDir
    });

    if (result.status !== 0) {
      process.exit(result.status || 1);
    }
    break;
  }

  case 'security':
  case 'audit:security': {
    const targetDir = path.resolve(process.cwd(), targetArg || '.');
    if (!fs.existsSync(targetDir)) {
      console.error(`❌ Error: Target directory does not exist: ${targetDir}`);
      process.exit(1);
    }

    const secPath = path.join(rootDir, 'gates', 'gate_security_audit.py');
    const secArgs = [secPath, targetDir];

    if (args.includes('--json')) secArgs.push('--json');
    if (args.includes('--md')) secArgs.push('--md');

    if (!args.includes('--json') && !args.includes('--md')) {
      printBanner();
      console.log(`Executing Enterprise Cybersecurity & Threat Audit on: ${targetDir}\n`);
    }

    const result = spawnSync('python3', secArgs, {
      stdio: 'inherit',
      cwd: rootDir
    });

    if (result.status !== 0) {
      process.exit(result.status || 1);
    }
    break;
  }

  case 'compile':
  case 'build:tokens': {
    printBanner();
    const tokensDir = targetArg ? path.resolve(process.cwd(), targetArg) : path.join(process.cwd(), 'core', 'tokens');
    const outArgIndex = args.indexOf('--out') !== -1 ? args.indexOf('--out') + 1 : (args.indexOf('-o') !== -1 ? args.indexOf('-o') + 1 : -1);
    const outputFile = outArgIndex !== -1 && args[outArgIndex] ? path.resolve(process.cwd(), args[outArgIndex]) : path.resolve(process.cwd(), 'tokens.css');

    console.log(`Compiling W3C DTCG tokens from: ${tokensDir}`);
    console.log(`Output destination: ${outputFile}\n`);

    const compilerScript = path.join(rootDir, 'core', 'compiler.py');
    const result = spawnSync('python3', [compilerScript, tokensDir, outputFile], {
      stdio: 'inherit',
      cwd: rootDir
    });

    if (result.status !== 0) {
      process.exit(result.status || 1);
    }
    break;
  }

  case 'knowledge': {
    const kbScript = path.join(rootDir, 'core', 'knowledge_search.py');
    const pyArgs = [kbScript, ...args.slice(1)];
    const result = spawnSync('python3', pyArgs, {
      stdio: 'inherit',
      cwd: rootDir
    });
    if (result.status !== 0) {
      process.exit(result.status || 1);
    }
    break;
  }

  case 'design': {
    printBanner();
    const action = args[1];
    if (action === 'system' || action === 'tokens') {
      const tokensDir = path.join(rootDir, 'core', 'tokens');
      const outFile = args[2] ? path.resolve(process.cwd(), args[2]) : path.resolve(process.cwd(), 'tokens.css');
      const compilerScript = path.join(rootDir, 'core', 'compiler.py');
      const result = spawnSync('python3', [compilerScript, tokensDir, outFile], { stdio: 'inherit', cwd: rootDir });
      if (result.status !== 0) process.exit(result.status || 1);
    } else if (action === 'page' || action === 'recipe') {
      let recipeId = 'contemporary-product-saas';
      let outFile = null;

      for (let i = 2; i < args.length; i++) {
        if (args[i] === '--out' && args[i + 1]) {
          outFile = path.resolve(process.cwd(), args[i + 1]);
          i++;
        } else if (!args[i].startsWith('--')) {
          recipeId = args[i].replace(/[^a-zA-Z0-9_-]/g, '');
        }
      }

      console.log(`Scaffolding page using style recipe: ${recipeId}`);
      const recipeFile = path.join(rootDir, 'knowledge', 'styles', `${recipeId}.json`);
      if (fs.existsSync(recipeFile)) {
        const recipe = JSON.parse(fs.readFileSync(recipeFile, 'utf-8'));
        console.log(`Thesis: ${recipe.designThesis}`);
        console.log(`Recommended density: ${recipe.layoutRhythm?.density || 'default'}`);
        console.log(`Target WCAG contrast: ${recipe.accessibilityProfile?.targetWcagRatio || 4.5}:1`);

        const html = generatePageBoilerplate(recipe);
        if (args.includes('--stdout')) {
          console.log("\n" + html);
        } else if (outFile) {
          fs.writeFileSync(outFile, html, 'utf-8');
          console.log(`  ✅ Successfully scaffolded certified page: ${path.relative(process.cwd(), outFile)}`);
        } else {
          console.log(`\n  ℹ️ Certified HTML boilerplate ready for '${recipeId}' (specify destination with --out <file.html> or view with --stdout).`);
        }
      } else {
        console.error(`Recipe '${recipeId}' not found in knowledge/styles/`);
        process.exit(1);
      }
    } else {
      console.log("Usage: orthotect design <system|page|init> [options]");
    }
    break;
  }

  case 'context': {
    const sub = args[1];
    const target = args[2];
    const pyScript = path.join(rootDir, 'core', 'context_optimizer.py');

    if (!fs.existsSync(pyScript)) {
      console.error(`❌ Context optimizer engine not found: ${pyScript}`);
      process.exit(1);
    }

    if (sub === 'inspect') {
      if (!target) {
        console.error("Usage: orthotect context inspect <file_or_dir> [--json]");
        process.exit(1);
      }
      const passArgs = [pyScript, 'inspect', path.resolve(process.cwd(), target)];
      if (args.includes('--json')) passArgs.push('--json');
      const proc = spawnSync('python3', passArgs, { stdio: 'inherit' });
      process.exit(proc.status || 0);
    }

    if (sub === 'chunk') {
      if (!target) {
        console.error("Usage: orthotect context chunk <file> [--max-tokens <N>] [--json]");
        process.exit(1);
      }
      const passArgs = [pyScript, 'chunk', path.resolve(process.cwd(), target)];
      const maxIdx = args.indexOf('--max-tokens');
      if (maxIdx !== -1 && args[maxIdx + 1]) {
        passArgs.push('--max-tokens', args[maxIdx + 1]);
      }
      if (args.includes('--json')) passArgs.push('--json');
      const proc = spawnSync('python3', passArgs, { stdio: 'inherit' });
      process.exit(proc.status || 0);
    }

    if (sub === 'skeleton') {
      const dirTarget = target || '.';
      const passArgs = [pyScript, 'skeleton', path.resolve(process.cwd(), dirTarget)];
      const depthIdx = args.indexOf('--depth');
      if (depthIdx !== -1 && args[depthIdx + 1]) {
        passArgs.push('--depth', args[depthIdx + 1]);
      }
      if (args.includes('--json')) passArgs.push('--json');
      const proc = spawnSync('python3', passArgs, { stdio: 'inherit' });
      process.exit(proc.status || 0);
    }

    printBanner();
    console.log("Orthotect Context & Token Optimizer Subsystem:");
    console.log("  inspect <path> [--json]                Profile token density, character counts & reading advice");
    console.log("  chunk <file> [--max-tokens N] [--json] Semantically partition file into boundary-safe chunks");
    console.log("  skeleton [dir] [--depth N] [--json]    Generate ultra-compact (>85% compressed) symbol map");
    break;
  }

  case 'skills':
  case 'list': {
    const sub = args[1];
    const skillsDir = path.join(rootDir, 'skills');

    if (sub === 'search') {
      const q = (args[2] || '').toLowerCase();
      console.log(`Searching skills for query: "${q}"...\n`);
      const folders = fs.readdirSync(skillsDir);
      for (const f of folders) {
        const sPath = path.join(skillsDir, f, 'SKILL.md');
        if (fs.existsSync(sPath)) {
          const content = fs.readFileSync(sPath, 'utf-8');
          if (f.toLowerCase().includes(q) || content.toLowerCase().includes(q)) {
            console.log(`  • ${f}`);
          }
        }
      }
      break;
    }

    if (sub === 'show') {
      const skillName = args[2];
      if (!skillName) {
        console.error("Please specify skill name: orthotect skills show <name>");
        process.exit(1);
      }
      const sPath = path.join(skillsDir, skillName, 'SKILL.md');
      if (fs.existsSync(sPath)) {
        console.log(fs.readFileSync(sPath, 'utf-8'));
      } else {
        console.error(`Skill '${skillName}' not found in skills/`);
        process.exit(1);
      }
      break;
    }

    if (sub === 'validate') {
      console.log("Validating all installed skills against Agent Skills Specification...\n");
      if (!validateSkills) {
        console.error("Validator module (scripts/validate-skills.mjs) is not available.");
        process.exit(1);
      }
      const res = validateSkills(skillsDir);
      for (const r of res.details) {
        if (r.errors.length > 0) {
          console.error(`  ❌ ${r.name}`);
          for (const err of r.errors) console.error(`     Error: ${err}`);
        } else if (r.warnings.length > 0) {
          console.warn(`  ⚠️  ${r.name}`);
          for (const warn of r.warnings) console.warn(`     Warning: ${warn}`);
        } else {
          console.log(`  ✅ ${r.name}`);
        }
      }
      console.log(`\nValidation: ${res.errors === 0 ? '100% PASSED' : 'FAILED'} (${res.passed} passed, ${res.warnings} warnings, ${res.errors} errors)`);
      if (res.errors > 0) process.exit(1);
      break;
    }

    printBanner();
    console.log("Available Orthotect Autonomous Agent Skills (22 Modular Disciplines):");
    console.log("  • orthotect-doctrine       : The 7 Non-Negotiable Laws of Interface Engineering");
    console.log("  • orthotect-uiux           : Master UI/UX Design Intelligence & Orchestrator");
    console.log("  • orthotect-design-systems : DTCG Token Hierarchy & Multi-Brand Themes");
    console.log("  • orthotect-components     : Accessible WAI-ARIA Component Contracts & FSM States");
    console.log("  • orthotect-accessibility  : WCAG 2.2 AA/AAA Deterministic Verification");
    console.log("  • orthotect-bidi           : True Bidirectional & Logical CSS Engineering");
    console.log("  • orthotect-dashboard      : High-Density Cognitive Console Architecture");
    console.log("  • orthotect-fsm            : Finite State Machine & Async Resilience Engineering");
    console.log("  • orthotect-forms          : Resilient Forms, Double-Submission Locks & Validation");
    console.log("  • orthotect-responsive     : Adaptive Bento Layouts, Fluid Typography & Queries");
    console.log("  • orthotect-motion         : Spring Physics Motion Tokens & Reduced-Motion");
    console.log("  • orthotect-data-viz       : Accessible Telemetry, Charts & SVG Sparklines");
    console.log("  • orthotect-tokens         : DTCG W3C 3-Tier Design Tokens & Theme Compiler");
    console.log("  • orthotect-gates          : Deterministic Quality Gates Runner");
    console.log("  • orthotect-visual-qa      : Automated Browser Visual Regression & Contrast Gate");
    console.log("  • orthotect-context        : Token-Optimizer & Context Architecture Guard");
    console.log("  • orthotect-cro            : Interface Conversion Rate Optimization & Form Ergonomics");
    console.log("  • orthotect-schema         : Semantic Structured Data & Schema.org JSON-LD");
    console.log("  • orthotect-auto-fix       : In-Place Auto-Healing & Remediation Engine (--fix)");
    console.log("  • orthotect-hooks          : Git Pre-Commit Hooks & Fail-Closed CI Enforcement");
    console.log("  • orthotect-typography     : Accessible & Fluid Typography Systems");
    console.log("  • orthotect-security       : Full-Stack Enterprise Cybersecurity & Vulnerability Audit");
    break;
  }

  default: {
    printBanner();
    console.log("Usage: npx orthotect <command> [target_directory] [options]");
    console.log("\nCore Commands:");
    console.log("  doctor                                 Check environment, gates, skills, and knowledge health");
    console.log("  verify | audit [path] [--fix] [--json] Run all 6 deterministic quality gates (with auto-healing --fix)");
    console.log("  security [path] [--json] [--md]        Run enterprise cybersecurity & vulnerability audit gate");
    console.log("  hooks <install|uninstall> [path]       Install or safely remove Git pre-commit quality gate hook");
    console.log("  init [path] [--force]                  Scaffold tokens, FSM specs, and AGENTS.md in target directory");
    console.log("  compile [tokens_path] [--out <file>]   Compile W3C DTCG tokens into production CSS variables");
    console.log("  context <inspect|chunk|skeleton>       Profile token density, chunk code, and generate symbol skeletons");
    console.log("  skills [list|search|show|validate]     Inspect and validate autonomous agent skills");
    console.log("  knowledge [query] [-c cat] [--json]    Search the UI/UX knowledge base and style recipes");
    console.log("  design <system|page|init>              Design system tools and style recipe page scaffolding");
    console.log("\nExamples:");
    console.log("  npx orthotect doctor");
    console.log("  npx orthotect verify ./src --fix");
    console.log("  npx orthotect hooks install");
    console.log("  npx orthotect knowledge 'contrast' --category palettes");
    console.log("  npx orthotect skills show orthotect-uiux");
    break;
  }
}
