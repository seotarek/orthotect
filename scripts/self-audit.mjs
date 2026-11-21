#!/usr/bin/env node
/**
 * Orthotect Self-Audit
 * ====================
 *
 * Runs all six deterministic gates against Orthotect's OWN source tree.
 *
 * Why this exists
 * ---------------
 * Every critical defect found in REVIEW_2026-11.md — a bypassable `!important`
 * flag, a `/tests/` path-trust shortcut, three configuration keys that were
 * parsed and then ignored — was the same kind of bug: the gates were written to
 * check other people's code and were never turned on themselves. A tool whose
 * entire premise is "evidence before assertions" should be the first thing it
 * verifies.
 *
 * Scope
 * -----
 * The audit target is the repository root, not the individual source
 * directories. The contrast, FSM and DOM gates resolve their required
 * `core/tokens/`, `core/fsm/` and markup inputs relative to the audit root, so
 * auditing `gates/` in isolation correctly fails closed with exit 2 (tool
 * error) — that is the contract working, not a finding. Auditing the root
 * evaluates the whole project the way a real user's project would be evaluated.
 *
 * Exit codes (see core/exit_codes.py):
 *   0 = every gate passed
 *   1 = at least one gate found a real violation in Orthotect's own code
 *   2 = a gate could not run, or the audit could not be executed
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ORCHESTRATOR = path.join(ROOT, 'gates', 'run_all_gates.py');

// Mirrors core/exit_codes.mjs and core/exit_codes.py.
const EXIT_PASS = 0;
const EXIT_VIOLATION = 1;
const EXIT_TOOL_ERROR = 2;

function fail(message, hint) {
  console.error('');
  console.error(`❌ [REJECT] Self-audit cannot run: ${message}`);
  if (hint) console.error(`   ${hint}`);
  console.error('');
  process.exit(EXIT_TOOL_ERROR);
}

/**
 * Resolves a working Python interpreter. The gates are pure standard library,
 * so any Python 3 is sufficient; `python3` is the documented entry point.
 */
function resolvePython() {
  return process.platform === 'win32' ? 'python' : 'python3';
}

function main() {
  if (!fs.existsSync(ORCHESTRATOR)) {
    fail(`gate orchestrator not found at ${ORCHESTRATOR}`,
         'Run this script from an intact Orthotect checkout.');
  }

  // The DOM gate needs parse5. Report that as an environment problem up front
  // with an actionable message, rather than letting it surface mid-run as if it
  // were a finding about Orthotect's code.
  if (!fs.existsSync(path.join(ROOT, 'node_modules', 'parse5'))) {
    fail('the HTML parser "parse5" is not installed, so the DOM & Layout-Shift gate cannot evaluate anything.',
         'Run `npm ci` inside the repository root, then re-run `npm run audit:self`.');
  }

  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  ORTHOTECT SELF-AUDIT — all six gates vs. Orthotect itself');
  console.log(`  Target: ${ROOT}`);
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('');

  const python = resolvePython();
  const child = spawn(python, [ORCHESTRATOR, ROOT], {
    cwd: ROOT,
    stdio: 'inherit',
  });

  child.on('error', (err) => {
    fail(`could not start "${python}" (${err.message}).`,
         'Ensure Python 3 is on PATH, or invoke `python3 gates/run_all_gates.py .` directly.');
  });

  child.on('close', (code, signal) => {
    if (signal) {
      // A killed gate makes no claim about the code.
      fail(`the gate orchestrator was terminated by signal ${signal}.`);
    }
    if (code === null) {
      fail('the gate orchestrator exited without a status.');
    }
    if (code === EXIT_PASS) {
      console.log('');
      console.log('✅ Self-audit passed: Orthotect satisfies its own six gates.');
      process.exit(EXIT_PASS);
    }
    if (code === EXIT_VIOLATION) {
      console.log('');
      console.log('❌ Self-audit failed: Orthotect violates one of its own rules.');
      console.log('   This is a defect in this repository, not in a user project.');
      process.exit(EXIT_VIOLATION);
    }
    // Anything else (including 2) is an environment/tooling problem.
    fail(`the gate orchestrator reported status ${code}.`,
         'One or more gates could not evaluate the tree; see the gate details above.');
  });
}

main();
