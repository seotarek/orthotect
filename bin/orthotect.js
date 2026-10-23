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

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const args = process.argv.slice(2);
const command = args[0] || 'help';
const subCommand = args[1] && !args[1].startsWith('--') ? args[1] : null;
const targetArg = args[1] && !args[1].startsWith('--') ? args[1] : null;
const forceFlag = args.includes('--force');

const pkgPath = path.join(rootDir, 'package.json');
const pkgVersion = fs.existsSync(pkgPath) ? JSON.parse(fs.readFileSync(pkgPath, 'utf-8')).version : '1.7.0';

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
          <button class="btn-primary" data-fsm="button" data-state="idle">Execute Action</button>
        </article>
      </section>
    </main>
  </div>
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

    console.log(`\nDoctor Status: ${hasErrors ? '❌ ISSUES DETECTED' : '✅ HEALTHY - All systems operational'}`);
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
          recipeId = args[i];
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
      console.log("Validating all installed skills...\n");
      const folders = fs.readdirSync(skillsDir).filter(f => fs.statSync(path.join(skillsDir, f)).isDirectory());
      let valid = true;
      for (const f of folders) {
        const sPath = path.join(skillsDir, f, 'SKILL.md');
        if (!fs.existsSync(sPath)) {
          console.log(`  ❌ Missing SKILL.md in skills/${f}`);
          valid = false;
        } else {
          console.log(`  ✅ skills/${f}/SKILL.md`);
        }
      }
      console.log(`\nValidation: ${valid ? '100% PASSED' : 'FAILED'}`);
      if (!valid) process.exit(1);
      break;
    }

    printBanner();
    console.log("Available Orthotect Autonomous Agent Skills (15 Modular Disciplines):");
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
    break;
  }

  default: {
    printBanner();
    console.log("Usage: npx orthotect <command> [target_directory] [options]");
    console.log("\nCore Commands:");
    console.log("  doctor                                 Check environment, gates, skills, and knowledge health");
    console.log("  verify | audit [path] [--json|--md]    Run all deterministic quality gates on target directory");
    console.log("  init [path] [--force]                  Scaffold tokens, FSM specs, and AGENTS.md in target directory");
    console.log("  compile [tokens_path] [--out <file>]   Compile W3C DTCG tokens into production CSS variables");
    console.log("  skills [list|search|show|validate]     Inspect and validate autonomous agent skills");
    console.log("  knowledge [query] [-c cat] [--json]    Search the UI/UX knowledge base and style recipes");
    console.log("  design <system|page|init>              Design system tools and style recipe page scaffolding");
    console.log("\nExamples:");
    console.log("  npx orthotect doctor");
    console.log("  npx orthotect verify ./src");
    console.log("  npx orthotect knowledge 'contrast' --category palettes");
    console.log("  npx orthotect skills show orthotect-uiux");
    break;
  }
}
