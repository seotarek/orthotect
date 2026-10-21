#!/usr/bin/env node
/**
 * Orthotect CLI
 * Production-grade command-line interface for autonomous interface engineering.
 */
import { spawnSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const args = process.argv.slice(2);
const command = args[0] || 'help';
const targetArg = args[1] && !args[1].startsWith('--') ? args[1] : null;
const forceFlag = args.includes('--force');

console.log("╔═══════════════════════════════════════════════════════════════╗");
console.log("║           ORTHOTECT INTERFACE ARCHITECTURE CLI                ║");
console.log("╚═══════════════════════════════════════════════════════════════╝\n");

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
  case 'init': {
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
      console.log(`Executing Deterministic Quality Gates on: ${targetDir}\n`);
    }

    // Safe execution without shell string interpolation
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

  case 'skills':
  case 'list': {
    console.log("Available Orthotect Autonomous Agent Skills:");
    console.log("  • orthotect-doctrine   : The 7 Non-Negotiable Laws of Interface Engineering");
    console.log("  • orthotect-fsm        : Finite State Machine & Async Resilience Engineering");
    console.log("  • orthotect-tokens     : DTCG W3C 3-Tier Design Tokens & Theme Compiler");
    console.log("  • orthotect-gates      : Deterministic Quality Gates Runner");
    console.log("  • orthotect-bidi       : True Bidirectional & Logical CSS Engineering");
    console.log("  • orthotect-dashboard  : High-Density Cognitive Console Architecture");
    break;
  }

  default: {
    console.log("Usage: npx orthotect <command> [target_directory] [options]");
    console.log("\nCommands:");
    console.log("  init [path] [--force]                  Scaffold tokens, FSM specs, and AGENTS.md in target directory");
    console.log("  verify [path]                          Run all deterministic quality gates on target directory");
    console.log("  compile [tokens_path] [--out <file>]   Compile W3C DTCG tokens into production CSS variables");
    console.log("  skills | list                          List all installed agent skills");
    console.log("\nExamples:");
    console.log("  npx orthotect init .");
    console.log("  npx orthotect verify ./src");
    console.log("  npx orthotect compile core/tokens --out styles/tokens.css");
    break;
  }
}
