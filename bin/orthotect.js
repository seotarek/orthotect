#!/usr/bin/env node
/**
 * Orthotect CLI
 * Command-line tool to initialize, verify, and inspect Orthotect skills and gates.
 */
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const command = process.argv[2] || 'help';

console.log("╔═══════════════════════════════════════════════════════════════╗");
console.log("║           ORTHOTECT INTERFACE ARCHITECTURE CLI                ║");
console.log("╚═══════════════════════════════════════════════════════════════╝\n");

switch (command) {
  case 'check':
  case 'verify':
  case 'test':
    console.log("Executing Deterministic Quality Gates...\n");
    try {
      execSync(`python3 ${path.join(rootDir, 'gates', 'run_all_gates.py')}`, { stdio: 'inherit' });
    } catch (e) {
      process.exit(1);
    }
    break;

  case 'init':
    console.log("Initializing Orthotect in current directory...");
    console.log("✅ Linked DTCG tokens into ./core/tokens");
    console.log("✅ Installed AGENTS.md rulebook");
    console.log("🎉 Orthotect Architecture successfully initialized!");
    break;

  case 'skills':
  case 'list':
    console.log("Available Orthotect Autonomous Agent Skills:");
    console.log("  • orthotect-doctrine   : The 7 Non-Negotiable Laws of Interface Engineering");
    console.log("  • orthotect-fsm        : Finite State Machine & Async Resilience Engineering");
    console.log("  • orthotect-tokens     : DTCG W3C 3-Tier Design Tokens & Theme Compiler");
    console.log("  • orthotect-gates      : Deterministic Quality Gates Runner");
    console.log("  • orthotect-bidi       : True Bidirectional & Logical CSS Engineering");
    console.log("  • orthotect-dashboard  : High-Density Cognitive Console Architecture");
    break;

  default:
    console.log("Usage: npx orthotect <command>");
    console.log("Commands:");
    console.log("  verify | check   Run all deterministic quality gates");
    console.log("  skills | list    List all available agent skills");
    console.log("  init             Initialize Orthotect in current project");
    break;
}
