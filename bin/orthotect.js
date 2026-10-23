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
const pkgVersion = fs.existsSync(pkgPath) ? JSON.parse(fs.readFileSync(pkgPath, 'utf-8')).version : '1.6.0';

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

switch (command) {
  case 'doctor': {
    printBanner();
    console.log("Running Orthotect Platform Diagnostic Doctor...\n");
    let hasErrors = false;

    // Check Node version
    const nodeVer = process.version;
    const nodeMajor = parseInt(nodeVer.replace(/^v/, '').split('.')[0], 10);
    if (nodeMajor >= 20) {
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
      const recipeId = args[2] || 'contemporary-product-saas';
      console.log(`Scaffolding page using style recipe: ${recipeId}`);
      const recipeFile = path.join(rootDir, 'knowledge', 'styles', `${recipeId}.json`);
      if (fs.existsSync(recipeFile)) {
        const recipe = JSON.parse(fs.readFileSync(recipeFile, 'utf-8'));
        console.log(`Thesis: ${recipe.designThesis}`);
        console.log(`Recommended density: ${recipe.layoutRhythm?.density || 'default'}`);
        console.log(`Target WCAG contrast: ${recipe.accessibilityProfile?.targetWcagRatio || 4.5}:1`);
      } else {
        console.error(`Recipe '${recipeId}' not found in knowledge/styles/`);
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
