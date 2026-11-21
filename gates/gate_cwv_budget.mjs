#!/usr/bin/env node
/**
 * Orthotect Gate: DOM Structure & Layout-Shift (CLS) Budget
 * Verifies that media elements reserve dimensions and DOM depth stays within bounds.
 */
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

let parse5 = null;
let parse5LoadError = null;
try {
  parse5 = await import('parse5');
} catch (err) {
  parse5LoadError = err;
}

/**
 * Thrown when an exported analysis function is called without the HTML parser
 * available. Without this, a missing dependency surfaces as a TypeError on
 * `null.parse` — a crash rather than the contract's exit 2.
 */
export class ParserUnavailableError extends Error {
  constructor(cause) {
    super('The DOM & Layout-Shift Budget gate cannot run: package "parse5" is not installed.');
    this.name = 'ParserUnavailableError';
    this.cause = cause;
  }
}

/**
 * Returns the loaded parse5 module or throws ParserUnavailableError.
 * Every analysis function funnels through this, so an absent parser can never
 * reach `parse5.parse` and masquerade as a code defect.
 */
function requireParse5() {
  if (!parse5) {
    throw new ParserUnavailableError(parse5LoadError);
  }
  return parse5;
}

import { loadOrthotectConfig } from '../core/config.mjs';

// Exit-code contract (see core/exit_codes.py and core/exit_codes.mjs):
//   0 = PASS, 1 = rule violation in the audited code, 2 = the gate could not run.
import { EXIT_PASS, EXIT_VIOLATION, EXIT_TOOL_ERROR } from '../core/exit_codes.mjs';

/**
 * The shared argument parser is loaded defensively, for the same reason `parse5`
 * is: a missing module means the gate cannot run, which is a tool error (exit 2),
 * never an uncaught import failure that Node reports as exit 1. A packaging fault
 * must not masquerade as a code violation in the audited project.
 */
let cliArgs = null;
let cliArgsLoadError = null;
try {
  cliArgs = await import('../core/cli_args.mjs');
} catch (err) {
  cliArgsLoadError = err;
}

// A second, private copy of the flag splitter is exactly the drift this milestone
// removed, so there is deliberately no fallback implementation here. A missing
// shared module is a broken installation and fails closed below as a tool error.
const cli = cliArgs;

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isMain && cliArgsLoadError) {
  console.error('');
  console.error('❌ [REJECT] DOM & Layout-Shift Budget gate cannot run: missing module "core/cli_args.mjs".');
  console.error(`   Cause: ${String(cliArgsLoadError.message || cliArgsLoadError).split('\n')[0]}`);
  console.error('   Fix: reinstall Orthotect so the core/ modules ship alongside gates/.');
  console.error('');
  process.exit(EXIT_TOOL_ERROR);
}

if (isMain && parse5LoadError) {
  // `parse5` is resolved from THIS file's location, i.e. from the orthotect package
  // itself — not from the project being verified and not from the current working
  // directory. Telling a user to `npm install parse5` in their own project therefore
  // does nothing. The only fix that actually works is to reinstall orthotect's own
  // dependencies, so the message names that and nothing else.
  console.error('');
  console.error('❌ [REJECT] DOM & Layout-Shift Budget gate cannot run: missing required package "parse5".');
  console.error('   The gate parses HTML through the WHATWG HTML5 AST (parse5) and fails closed without it.');
  console.error('');
  console.error('   Cause: Node resolved "parse5" from the Orthotect package itself and did not find it.');
  console.error('          Installing parse5 in the project you are verifying will NOT fix this, because the');
  console.error('          import is resolved relative to this gate file, not to your project or the cwd.');
  console.error('');
  console.error('   Fix: reinstall Orthotect\'s own dependencies, then re-run verification.');
  console.error('     npm install                       # inside the orthotect package directory');
  console.error('     npx orthotect verify .            # the published package ships parse5 as a dependency');
  console.error('');
  if (parse5LoadError && parse5LoadError.message) {
    console.error(`   Underlying resolver error: ${String(parse5LoadError.message).split('\n')[0]}`);
    console.error('');
  }
  process.exit(EXIT_TOOL_ERROR);
}

// Declared before the argument block below: a tool error there emits a SARIF
// document, and that document is built from these two lists.
// SARIF 2.1.0 constants. Declared before the argument block below because a tool
// error there emits a SARIF document, and these are read while building it.
const SARIF_VERSION = '2.1.0';
const SARIF_SCHEMA = 'https://json.schemastore.org/sarif-2.1.0.json';
const TOOL_NAME = 'orthotect';
const TOOL_URI = 'https://github.com/seotarek/orthotect';
const ERROR_LEVEL_SEVERITIES = new Set(['CRITICAL', 'HIGH']);

let checkedFiles = 0;
let errors = [];
let findings = [];

let targetDir = 'examples';
let asSarif = false;
if (isMain) {
  asSarif = sarifRequested(process.argv.slice(2));
  // The banner is human output; the target must be resolved either way. Gating
  // the parse on the output format would leave `--format sarif` auditing the
  // default `examples/` directory instead of the requested one.
  if (!asSarif) {
    console.log("═══════════════════════════════════════════════════════════════");
    console.log("  ORTHOTECT GATE: DOM Structure & Layout-Shift Budget");
    console.log("═══════════════════════════════════════════════════════════════");
  }
  // First non-flag token, so `gate_cwv_budget.mjs --json ./src` does not treat "--json"
  // as the directory to scan (which surfaced as a confusing "Target path not found").
  // Shared splitter: a value bound to a value-taking flag (`--format json`) must
  // never be mistaken for the target directory.
  targetDir = cli.positionals(process.argv.slice(2)).at(0) || 'examples';
  if (!fs.existsSync(targetDir)) {
    if (asSarif) {
      emitSarif(`Target path not found: ${targetDir}`);
    } else {
      console.error(`❌ [REJECT] Target path not found: ${targetDir}`);
    }
    process.exit(EXIT_TOOL_ERROR);
  }
}

/**
 * Structured mirror of `errors`, for machine-readable output.
 *
 * `errors` stays the console format people read; `findings` carries the same
 * entries with a registry rule id and a source line so SARIF can annotate them.
 * Both are appended together in `addFinding`, so the two reports can never
 * disagree about what fired.
 */

/**
 * Records one finding in both the console and the structured list.
 *
 * `body` is the message without the `file: ` prefix — SARIF carries the file in
 * `artifactLocation`, and repeating it there makes the annotation read as
 * "src/app.html: src/app.html: …".
 */
function addFinding(filePath, body, ruleId, line) {
  errors.push(`${filePath}: ${body}`);
  findings.push({
    file: filePath,
    line: Number.isInteger(line) && line > 0 ? line : 1,
    label: body,
    ruleId,
  });
}

/** 1-based line number for a character offset, or 1 when the offset is unknown. */
function lineAtOffset(content, offset) {
  if (typeof offset !== 'number' || offset <= 0 || typeof content !== 'string') return 1;
  return content.slice(0, offset).split('\n').length;
}

// ---------------------------------------------------------------------------
// SARIF 2.1.0 emission
//
// The schema is emitted from this file rather than by shelling out to Python:
// this gate is the only one that runs on Node, and a cross-runtime hop would add
// a failure mode (a missing interpreter) to a gate whose whole contract is that
// it either reports or exits 2. The shape matches core/sarif.py exactly, and
// `tests/test_sarif.py` asserts the two agree field for field.
// ---------------------------------------------------------------------------

/** True when the caller asked for SARIF, in any of its three spellings. */
function sarifRequested(argv) {
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === '--sarif') return true;
    if (token === '--format' && i + 1 < argv.length) {
      if (String(argv[i + 1]).trim().toLowerCase() === 'sarif') return true;
    }
    if (token.startsWith('--format=')) {
      if (token.split('=').slice(1).join('=').trim().toLowerCase() === 'sarif') return true;
    }
  }
  return false;
}

/** The package version, or '0.0.0' when the manifest is unreachable. */
function toolVersion() {
  try {
    const manifest = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'package.json');
    return String(JSON.parse(fs.readFileSync(manifest, 'utf-8')).version || '0.0.0');
  } catch (_) {
    return '0.0.0';
  }
}

/**
 * Registry severities for the `dom.*` rules, read from `core/rule_registry.py`.
 *
 * The registry is the single source of truth for a rule's severity, and reading
 * it rather than hardcoding a copy here is what keeps a SARIF annotation level
 * from contradicting what `orthotect explain` prints. Failure is tolerated — a
 * missing registry degrades the level, it does not stop the gate.
 */
function loadRuleSeverities() {
  const cache = new Map();
  try {
    const registryPath = path.resolve(
      path.dirname(fileURLToPath(import.meta.url)), '..', 'core', 'rule_registry.py');
    const source = fs.readFileSync(registryPath, 'utf-8');
    // Each entry is a dict literal: '<id>': { ... 'severity': '<LEVEL>', ... }
    const entryPattern = /'([a-z]+\.[a-z0-9-]+)'\s*:\s*\{([\s\S]*?)\n    \}/g;
    let match;
    while ((match = entryPattern.exec(source)) !== null) {
      const severity = /'severity'\s*:\s*'([A-Z]+)'/.exec(match[2]);
      if (severity) cache.set(match[1], severity[1]);
    }
  } catch (_) {
    /* A missing registry only costs us the level mapping. */
  }
  return cache;
}

let ruleSeverities = null;

/** Registry severity for a rule id, or null. Never throws. */
function registrySeverity(ruleId) {
  if (ruleSeverities === null) ruleSeverities = loadRuleSeverities();
  const severity = ruleSeverities.get(ruleId);
  return severity ? severity.toUpperCase() : null;
}

/**
 * The rule-set version block, read from `core/rule_registry.py`.
 *
 * Emitted in the SARIF driver's `properties` so this gate's document carries the
 * same rule-set identity as the Python gates. Absent rather than invented when
 * the registry cannot be read — a made-up version looks pinnable and is not.
 */
function ruleSetMetadata() {
  try {
    const registryPath = path.resolve(
      path.dirname(fileURLToPath(import.meta.url)), '..', 'core', 'rule_registry.py');
    const source = fs.readFileSync(registryPath, 'utf-8');
    const version = /^RULES_VERSION\s*=\s*'([^']+)'/m.exec(source);
    if (!version) return {};

    // Each rule entry is a flat block: the id as a key, then `gate` and
    // `severity` as string fields before the prose fields. Parsing exactly those
    // three is what makes the digest reproducible in this language; the full
    // Python structure is not.
    const entries = [];
    const entryPattern = /^    '([a-z]+\.[a-z0-9-]+)':\s*\{([\s\S]*?)^    \},?$/gm;
    let match;
    while ((match = entryPattern.exec(source)) !== null) {
      const gate = /'gate'\s*:\s*'([^']+)'/.exec(match[2]);
      const severity = /'severity'\s*:\s*'([^']+)'/.exec(match[2]);
      if (gate && severity) {
        entries.push(`${match[1]}|${gate[1]}|${severity[1]}`);
      }
    }
    if (entries.length === 0) return {};
    entries.sort();

    const digest = crypto.createHash('sha256')
      .update(entries.join('\n'), 'utf-8')
      .digest('hex')
      .slice(0, 16);
    return { rulesVersion: version[1], rulesDigest: digest, ruleCount: entries.length };
  } catch (_) {
    return {};
  }
}

/** SARIF has three levels; Orthotect has four. Map conservatively. */
function sarifLevel(severity) {
  return ERROR_LEVEL_SEVERITIES.has(String(severity || '').toUpperCase()) ? 'error' : 'warning';
}

/** Repo-relative, forward-slashed URI. An absolute path never attaches in GitHub. */
function relativize(target, baseDir) {
  try {
    const rel = path.relative(path.resolve(baseDir || '.'), path.resolve(target));
    return rel.split(path.sep).join('/');
  } catch (_) {
    return String(target).split(path.sep).join('/');
  }
}

/** Builds the SARIF document for this gate's findings. */
function buildSarifDocument(toolError) {
  const rules = new Map();
  const results = [];

  for (const finding of findings) {
    const severity = registrySeverity(finding.ruleId) || 'MEDIUM';
    const ruleId = finding.ruleId || 'dom-cwv-budget.finding';
    if (!rules.has(ruleId)) {
      rules.set(ruleId, {
        id: ruleId,
        name: ruleId.replace(/[.\-]/g, ' ').split(' ').filter(Boolean)
          .map(p => p.charAt(0).toUpperCase() + p.slice(1)).join('') || 'Finding',
        shortDescription: { text: String(finding.label) },
        defaultConfiguration: { level: sarifLevel(severity) },
        helpUri: `${TOOL_URI}#${ruleId}`,
      });
    }
    results.push({
      ruleId,
      level: sarifLevel(severity),
      message: { text: String(finding.label) },
      locations: [{
        physicalLocation: {
          artifactLocation: { uri: relativize(finding.file, targetDir) },
          region: { startLine: Math.max(Number(finding.line) || 1, 1) },
        },
      }],
      properties: { severity, gate: 'gate_cwv_budget' },
    });
  }

  const notifications = toolError
    ? [{ level: 'error', message: { text: String(toolError) } }]
    : [];

  const driver = {
    name: TOOL_NAME,
    informationUri: TOOL_URI,
    version: toolVersion(),
    rules: Array.from(rules.keys()).sort().map(k => rules.get(k)),
  };
  const ruleMetadata = ruleSetMetadata();
  if (Object.keys(ruleMetadata).length > 0) {
    driver.properties = ruleMetadata;
  }

  return {
    $schema: SARIF_SCHEMA,
    version: SARIF_VERSION,
    runs: [{
      tool: { driver },
      results,
      columnKind: 'utf16CodeUnits',
      invocations: [{
        executionSuccessful: notifications.length === 0,
        toolExecutionNotifications: notifications,
      }],
    }],
  };
}

/** Prints this gate's SARIF document. */
function emitSarif(toolError) {
  process.stdout.write(JSON.stringify(buildSarifDocument(toolError), null, 2) + '\n');
}

/**
 * Exits 2 in the requested format.
 *
 * A SARIF document is still emitted on a tool error, recording that the analysis
 * did not run: an empty result set would be indistinguishable from a clean audit
 * in the code-scanning UI.
 */
function emitToolError(message) {
  if (asSarif) {
    emitSarif(message);
  } else {
    console.log(`\n❌ [REJECT] ${message}`);
  }
  process.exit(EXIT_TOOL_ERROR);
}

/**
 * Parses raw HTML tag attribute string into an object dictionary.
 * Prevents confusion between 'width' and 'data-width'.
 * Preserves quotes containing '<' or '>'.
 */
export function parseHtmlAttributes(attrsStr) {
  if (!attrsStr || typeof attrsStr !== 'string') return {};
  const attrs = {};
  const regex = /([a-zA-Z0-9_:-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;
  let match;
  while ((match = regex.exec(attrsStr)) !== null) {
    const attrName = match[1].toLowerCase();
    const val = match[2] !== undefined ? match[2] : (match[3] !== undefined ? match[3] : (match[4] !== undefined ? match[4] : ""));
    attrs[attrName] = val;
  }
  return attrs;
}

/**
 * Validates whether an HTML width/height attribute value is a valid positive integer.
 * Per HTML5 specification (§ 4.8.4.1.3 Dimension attributes), width/height on <img>
 * must be valid non-negative integers (ASCII digits only, no 'px', no decimals, no signs).
 * Accepts "200", "800".
 * Rejects "200px", "0", "-100", "", "invalid", "auto", "100%", "150.5".
 */
export function isPositiveDimension(val) {
  if (val === undefined || val === null || typeof val !== 'string') return false;
  const clean = val.trim();
  if (!clean) return false;
  if (!/^[1-9]\d*$/.test(clean)) return false;
  const num = parseInt(clean, 10);
  return !isNaN(num) && num > 0;
}

/**
 * Parses a CSS style string into an object of declared properties.
 * Handles quoted strings, strips CSS comments, and handles repeated declarations.
 */
export function parseStyleDeclarations(styleStr) {
  if (!styleStr || typeof styleStr !== 'string') return {};
  const stripped = styleStr.replace(/\/\*[\s\S]*?\*\//g, '');
  const decls = {};
  let current = '';
  let inQuote = null;

  for (let i = 0; i < stripped.length; i++) {
    const ch = stripped[i];
    if (inQuote) {
      if (ch === inQuote) inQuote = null;
      current += ch;
    } else if (ch === '"' || ch === "'") {
      inQuote = ch;
      current += ch;
    } else if (ch === ';') {
      const colonIdx = current.indexOf(':');
      if (colonIdx > 0) {
        const prop = current.slice(0, colonIdx).trim().toLowerCase();
        const val = current.slice(colonIdx + 1).trim();
        if (prop) decls[prop] = val;
      }
      current = '';
    } else {
      current += ch;
    }
  }
  if (current.trim()) {
    const colonIdx = current.indexOf(':');
    if (colonIdx > 0) {
      const prop = current.slice(0, colonIdx).trim().toLowerCase();
      const val = current.slice(colonIdx + 1).trim();
      if (prop) decls[prop] = val;
    }
  }
  return decls;
}

/**
 * Validates CSS aspect-ratio property value against W3C CSS Box Sizing Level 4.
 * Syntax: auto || <ratio>
 * where <ratio> = <positive-number> [ / <positive-number> ]?
 */
export function isValidAspectRatioValue(rawVal) {
  if (!rawVal || typeof rawVal !== 'string') return false;

  let val = rawVal.replace(/^\bauto\b\s*/i, '').replace(/\s*\bauto\b$/i, '').trim();
  val = val.replace(/\s*!important\s*$/i, '').trim();
  if (!val) {
    // 'auto' alone does not provide a fixed aspect-ratio to prevent layout shift
    return false;
  }

  const ratioMatch = val.match(/^([0-9]*\.?[0-9]+)\s*(?:\/\s*([0-9]*\.?[0-9]+))?$/);
  if (!ratioMatch) return false;

  const w = parseFloat(ratioMatch[1]);
  const h = ratioMatch[2] !== undefined ? parseFloat(ratioMatch[2]) : 1.0;

  return !isNaN(w) && !isNaN(h) && w > 0 && h > 0;
}

/**
 * Parses, type-checks per W3C CSS Values and Units Level 4 (§ 8.1.1),
 * validates parenthesis matching, and mathematically evaluates CSS calc() expressions.
 * Enforces:
 * - Balanced parentheses (rejects unbalanced ( or ))
 * - Multiplication requires at least one unitless <number> operand (rejects length * length)
 * - Addition/subtraction operands must match types (rejects length + number)
 * - Division right operand must be a non-zero unitless <number> (rejects length / length, length / 0)
 * - Dimension expression must resolve to <length> (rejects unitless numbers)
 * - All evaluated reference models (mobile, desktop, neutral) must be strictly positive (> 0)
 */
export function parseAndValidateCssCalc(innerStr) {
  if (!innerStr || typeof innerStr !== 'string') return false;
  const str = innerStr.trim();
  if (!str) return false;

  const validUnits = new Set(['px', 'rem', 'em', 'vw', 'vh', '%', 'cqi', 'cqw', 'pt', 'cm', 'mm', 'in', 'vmin', 'vmax', 'ch', 'ex']);
  const numberRegex = /^[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/;

  // 1. Lexical Tokenization
  const tokens = [];
  let i = 0;
  const len = str.length;
  while (i < len) {
    const ch = str[i];
    if (/\s/.test(ch)) {
      i++;
      continue;
    }
    if (ch === '(' || ch === ')' || ch === '*' || ch === '/') {
      tokens.push({ type: ch, raw: ch });
      i++;
      continue;
    }
    if (ch === '+' || ch === '-') {
      const prev = tokens.length > 0 ? tokens[tokens.length - 1].type : null;
      const isUnary = !prev || prev === '(' || prev === '+' || prev === '-' || prev === '*' || prev === '/';
      if (isUnary) {
        // In CSS Syntax Level 3, a unary sign must be followed immediately by a number (or opening parenthesis)
        // with ZERO whitespace! (e.g. "-10px", not "- 10px")
        const nextChar = str[i + 1];
        if (!nextChar || /\s/.test(nextChar)) {
          return false; // Space after unary sign is INVALID in CSS
        }

        if (nextChar === '(') {
          tokens.push({ type: 'unary', sign: ch === '-' ? -1 : 1 });
          i++;
          continue;
        }

        if (/[0-9.]/.test(nextChar)) {
          const sign = ch === '-' ? -1 : 1;
          i++; // consume sign
          const numStart = i;
          while (i < len && /[0-9.]/.test(str[i])) i++;
          // W3C CSS Syntax Module Level 3 (§ 4.3.12 Consume a number):
          // An exponent indicator 'e' or 'E' is only part of the number if followed by an optional sign and at least one digit!
          // This strictly avoids colliding with valid CSS units such as 'em' and 'ex' (e.g. "10em", "10ex").
          if (i < len && (str[i] === 'e' || str[i] === 'E')) {
            const rem = str.slice(i);
            const expMatch = rem.match(/^[eE][+-]?[0-9]+/);
            if (expMatch) {
              i += expMatch[0].length;
            }
          }
          const rawNum = str.slice(numStart, i);
          if (!numberRegex.test(rawNum)) {
            return false;
          }
          const numVal = parseFloat(rawNum);
          if (isNaN(numVal)) return false;

          const unitStart = i;
          while (i < len && /[a-zA-Z%]/.test(str[i])) i++;
          const unit = str.slice(unitStart, i).toLowerCase();
          if (unit && !validUnits.has(unit)) return false;

          tokens.push({
            type: 'val',
            num: sign * numVal,
            unit: unit || null,
            dimType: unit ? 'length' : 'number'
          });
          continue;
        }
        return false;
      } else {
        // Binary infix operator "+" or "-": W3C CSS Values and Units Level 4 (§ 8.1.1) requires whitespace on BOTH sides!
        const hasPrecedingSpace = i > 0 && /\s/.test(str[i - 1]);
        const hasFollowingSpace = (i + 1 < len) && /\s/.test(str[i + 1]);
        if (!hasPrecedingSpace || !hasFollowingSpace) {
          return false;
        }
        tokens.push({ type: ch, raw: ch });
        i++;
        continue;
      }
    }
    if (/[0-9.]/.test(ch)) {
      const numStart = i;
      while (i < len && /[0-9.]/.test(str[i])) i++;
      // W3C CSS Syntax Module Level 3 (§ 4.3.12 Consume a number):
      // An exponent indicator 'e' or 'E' is only part of the number if followed by an optional sign and at least one digit!
      // This strictly avoids colliding with valid CSS units such as 'em' and 'ex' (e.g. "10em", "10ex").
      if (i < len && (str[i] === 'e' || str[i] === 'E')) {
        const rem = str.slice(i);
        const expMatch = rem.match(/^[eE][+-]?[0-9]+/);
        if (expMatch) {
          i += expMatch[0].length;
        }
      }
      const rawNum = str.slice(numStart, i);
      if (!numberRegex.test(rawNum)) {
        return false;
      }
      const numVal = parseFloat(rawNum);
      if (isNaN(numVal)) return false;
      const unitStart = i;
      while (i < len && /[a-zA-Z%]/.test(str[i])) i++;
      const unit = str.slice(unitStart, i).toLowerCase();
      if (unit && !validUnits.has(unit)) return false;
      tokens.push({
        type: 'val',
        num: numVal,
        unit: unit || null,
        dimType: unit ? 'length' : 'number'
      });
      continue;
    }
    // Unrecognized character
    return false;
  }

  if (tokens.length === 0) return false;

  // 2. Recursive-Descent Parser with W3C CSS Values and Units Level 4 (§ 8.1.1) Type Checking
  let pos = 0;

  function parseFactor() {
    if (pos >= tokens.length) return null;
    let sign = 1;
    if (tokens[pos].type === 'unary') {
      sign = tokens[pos].sign;
      pos++;
      if (pos >= tokens.length) return null;
    } else if (tokens[pos].type === '+' || tokens[pos].type === '-') {
      if (tokens[pos].type === '-') sign = -1;
      pos++;
      if (pos >= tokens.length) return null;
    }

    const t = tokens[pos];
    if (t.type === '(') {
      pos++; // consume (
      const expr = parseExpression();
      if (!expr) return null;
      if (pos >= tokens.length || tokens[pos].type !== ')') {
        // Unbalanced opening parenthesis: missing closing ')'
        return null;
      }
      pos++; // consume )
      return {
        dimType: expr.dimType,
        evalNode: (map) => sign * expr.evalNode(map)
      };
    }

    if (t.type === 'val') {
      pos++; // consume val
      const valToken = t;
      return {
        dimType: valToken.dimType,
        evalNode: (map) => {
          const factor = valToken.unit ? (map[valToken.unit] !== undefined ? map[valToken.unit] : 1) : 1;
          return sign * valToken.num * factor;
        }
      };
    }

    return null;
  }

  function parseTerm() {
    let left = parseFactor();
    if (!left) return null;

    while (pos < tokens.length && (tokens[pos].type === '*' || tokens[pos].type === '/')) {
      const op = tokens[pos].type;
      pos++;
      const right = parseFactor();
      if (!right) return null;

      if (op === '*') {
        // W3C Rule: At least one operand must be a <number>
        if (left.dimType === 'length' && right.dimType === 'length') {
          return null; // Cannot multiply length by length
        }
        const resDimType = (left.dimType === 'length' || right.dimType === 'length') ? 'length' : 'number';
        const prevLeft = left;
        left = {
          dimType: resDimType,
          evalNode: (map) => prevLeft.evalNode(map) * right.evalNode(map)
        };
      } else {
        // Division: Right operand MUST be a unitless <number>
        if (right.dimType !== 'number') {
          return null; // Cannot divide by length or dimension
        }
        const prevLeft = left;
        left = {
          dimType: prevLeft.dimType, // preserves left type
          evalNode: (map) => {
            const rVal = right.evalNode(map);
            if (rVal === 0) return NaN;
            return prevLeft.evalNode(map) / rVal;
          }
        };
      }
    }
    return left;
  }

  function parseExpression() {
    let left = parseTerm();
    if (!left) return null;

    while (pos < tokens.length && (tokens[pos].type === '+' || tokens[pos].type === '-')) {
      const op = tokens[pos].type;
      pos++;
      const right = parseTerm();
      if (!right) return null;

      // W3C Rule: Both operands must have matching types (length + length, or number + number)
      if (left.dimType !== right.dimType) {
        return null; // Cannot add/subtract length and unitless number
      }

      const prevLeft = left;
      left = {
        dimType: prevLeft.dimType,
        evalNode: (map) => {
          const lVal = prevLeft.evalNode(map);
          const rVal = right.evalNode(map);
          return op === '+' ? lVal + rVal : lVal - rVal;
        }
      };
    }
    return left;
  }

  const ast = parseExpression();
  if (!ast) return false;

  // Unconsumed tokens (e.g. extra closing parenthesis or invalid trailing token)
  if (pos < tokens.length) return false;

  // A CSS dimension (width/height) MUST resolve to <length> (or percentage), NOT a unitless number
  if (ast.dimType !== 'length') return false;

  // 3. Dimensional Evaluation across mobile, desktop, and neutral models
  const mobileMap = { px: 1, rem: 16, em: 16, vw: 3.6, vh: 6.4, '%': 3.6, cqi: 3.6, cqw: 3.6, pt: 1.333, cm: 37.795, mm: 3.7795, in: 96, vmin: 3.6, vmax: 6.4, ch: 8, ex: 8 };
  const desktopMap = { px: 1, rem: 16, em: 16, vw: 14.4, vh: 9.0, '%': 14.4, cqi: 14.4, cqw: 14.4, pt: 1.333, cm: 37.795, mm: 3.7795, in: 96, vmin: 9.0, vmax: 14.4, ch: 8, ex: 8 };
  const neutralMap = { px: 1, rem: 1, em: 1, vw: 1, vh: 1, '%': 1, cqi: 1, cqw: 1, pt: 1, cm: 1, mm: 1, in: 1, vmin: 1, vmax: 1, ch: 1, ex: 1 };

  const mVal = ast.evalNode(mobileMap);
  const dVal = ast.evalNode(desktopMap);
  const nVal = ast.evalNode(neutralMap);

  if (isNaN(mVal) || isNaN(dVal) || isNaN(nVal)) return false;
  return mVal > 0 && dVal > 0 && nVal > 0;
}

/**
 * Validates CSS dimension property value (width/height).
 * Rejects 'auto', 'none', 'initial', 'inherit', 'unset', '0', '0px', and any invalid or non-positive calc().
 * Accepts positive dimensions with length/percentage units or mathematically positive valid calc().
 */
export function isValidCssDimensionValue(val) {
  if (!val || typeof val !== 'string') return false;
  const clean = val.trim().toLowerCase().replace(/\s*!important\s*$/i, '').trim();
  if (['auto', 'none', 'initial', 'inherit', 'unset', '0', '0px', ''].includes(clean)) return false;

  // Single length/percentage dimension check: e.g. "200px", "0.5px", ".5em", "50%", "10rem", "10ex"
  // Strictly validates positive numeric value (> 0) supporting decimals below 1 and leading decimal dots per W3C CSS Values 4
  const directMatch = clean.match(/^((?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)(px|rem|em|vw|vh|%|cqi|cqw|pt|cm|mm|in|vmin|vmax|ch|ex)$/i);
  if (directMatch) {
    const num = parseFloat(directMatch[1]);
    if (!isNaN(num) && num > 0) return true;
    return false;
  }

  // Calc expression evaluation
  const calcMatch = clean.match(/^calc\((.+)\)$/i);
  if (!calcMatch) return false;

  const inner = calcMatch[1].trim();
  if (!inner) return false;

  return parseAndValidateCssCalc(inner);
}

/**
 * Returns the maximum element nesting depth of an HTML document.
 * Delegates to analyzeDomStructure so depth and node-count budgets share one AST pass.
 */
export function calculateMaxDomDepth(htmlContent, filePath = 'snippet') {
  return analyzeDomStructure(htmlContent, filePath).maxDepth;
}

export function analyzeDomStructure(htmlContent, filePath = 'snippet') {
  const voidTags = new Set([
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr'
  ]);
  const optionalClosing = new Set([
    'html', 'body', 'p', 'li', 'td', 'tr', 'dt', 'dd', 'option', 'thead', 'tbody', 'tfoot'
  ]);

  const parser = requireParse5();
  const parseErrors = [];
  const doc = parser.parse(htmlContent, {
    sourceCodeLocationInfo: true,
    onParseError: (err) => parseErrors.push(err)
  });

  for (const pe of parseErrors) {
    const at = lineAtOffset(htmlContent, pe.startOffset);
    if (pe.code === 'eof-in-tag' || pe.code === 'eof-before-tag-name' || pe.code === 'eof-in-attribute-value') {
      addFinding(filePath, `Malformed HTML - unclosed tag opening or attribute syntax '<' at position ${pe.startOffset || 0}.`, 'dom.unbalanced-markup', at);
    } else if (pe.code === 'non-void-html-element-start-tag-with-trailing-solidus') {
      addFinding(filePath, 'Malformed HTML - non-void HTML element start tag with trailing solidus (<div/> is not self-closing in HTML5).', 'dom.unbalanced-markup', at);
    } else if (pe.code === 'end-tag-without-matching-open-element') {
      addFinding(filePath, 'Malformed HTML - stray or mismatched closing tag without matching open element.', 'dom.unbalanced-markup', at);
    } else if (pe.code === 'duplicate-attribute') {
      addFinding(filePath, 'Malformed HTML - duplicate attribute on element.', 'dom.unbalanced-markup', at);
    }
  }

  const stack = [];
  const tokenizer = new parser.Tokenizer({}, {
    onNullCharacter: () => {},
    onWhitespaceCharacter: () => {},
    onCharacter: () => {},
    onComment: () => {},
    onDoctype: () => {},
    onStartTag: (t) => {
      if (!voidTags.has(t.tagName) && !t.selfClosing) {
        stack.push(t.tagName);
      }
    },
    onEndTag: (t) => {
      if (voidTags.has(t.tagName)) return;
      const at = lineAtOffset(htmlContent, t.location && t.location.startOffset);
      if (stack.length === 0) {
        addFinding(filePath, `Malformed HTML - stray closing tag </${t.tagName}> without open tag.`, 'dom.unbalanced-markup', at);
        return;
      }
      const top = stack[stack.length - 1];
      if (top === t.tagName) {
        stack.pop();
      } else {
        while (stack.length > 0 && optionalClosing.has(stack[stack.length - 1]) && stack[stack.length - 1] !== t.tagName) {
          stack.pop();
        }
        if (stack.length > 0 && stack[stack.length - 1] === t.tagName) {
          stack.pop();
        } else {
          addFinding(filePath, `Malformed HTML - mismatched closing tag </${t.tagName}>, expected </${top}>.`, 'dom.unbalanced-markup', at);
          const idx = stack.lastIndexOf(t.tagName);
          if (idx !== -1) stack.splice(idx);
        }
      }
    },
    onEof: () => {}
  });

  tokenizer.write(htmlContent, true);

  const unclosed = stack.filter(t => !optionalClosing.has(t));
  if (unclosed.length > 0) {
    addFinding(filePath, `Malformed HTML - unclosed tag(s) remaining at end of file: <${unclosed.join('>, <')}>.`, 'dom.unbalanced-markup', 1);
  }

  // Iterative Tree Traversal from the parsed HTML5 AST using an explicit stack
  let maxTreeDepth = 0;
  let elementCount = 0;
  let nodesVisited = 0;
  const MAX_NODE_VISIT_LIMIT = 200000;
  const traversalStack = [{ node: doc, depth: 0 }];

  while (traversalStack.length > 0) {
    const { node, depth } = traversalStack.pop();
    nodesVisited++;

    if (nodesVisited > MAX_NODE_VISIT_LIMIT) {
      addFinding(filePath, `Resource limit exceeded during AST traversal (> ${MAX_NODE_VISIT_LIMIT} nodes visited). Adversarial DOM structure rejected.`, 'dom.resource-limit', 1);
      break;
    }

    const isElem = node.nodeName && !node.nodeName.startsWith('#');
    const currentDepth = isElem ? depth + 1 : depth;
    if (isElem) elementCount++;

    if (currentDepth > maxTreeDepth) {
      maxTreeDepth = currentDepth;
    }

    if (node.childNodes && node.childNodes.length > 0) {
      for (let i = node.childNodes.length - 1; i >= 0; i--) {
        const child = node.childNodes[i];
        if (child.nodeName && !child.nodeName.startsWith('#')) {
          traversalStack.push({ node: child, depth: currentDepth });
        }
      }
    }
  }

  return { maxDepth: maxTreeDepth, elementCount };
}

function findElements(rootNode, tagName) {
  const results = [];
  const stack = [rootNode];
  while (stack.length > 0) {
    const node = stack.pop();
    if (node.nodeName === tagName) results.push(node);
    if (node.childNodes && node.childNodes.length > 0) {
      for (let i = node.childNodes.length - 1; i >= 0; i--) {
        stack.push(node.childNodes[i]);
      }
    }
  }
  return results;
}

export function extractCssRulesFromHtmlAndLinkedSheets(htmlContent, htmlFilePath) {
  const cssTexts = [];
  const styleRegex = /<style\b[^>]*>([\s\S]*?)<\/style>/gi;
  let match;
  while ((match = styleRegex.exec(htmlContent)) !== null) {
    cssTexts.push(match[1]);
  }
  // Robust link tag extraction using parseHtmlAttributes (order-agnostic)
  const linkTagRegex = /<link\b([^>]*)\/?>/gi;
  const dir = path.dirname(htmlFilePath);
  while ((match = linkTagRegex.exec(htmlContent)) !== null) {
    const attrs = parseHtmlAttributes(match[1]);
    if (attrs['rel'] && attrs['rel'].toLowerCase() === 'stylesheet' && attrs['href']) {
      const href = attrs['href'].split('?')[0].split('#')[0];
      if (path.isAbsolute(href) || href.startsWith('//') || href.includes('://')) continue;
      const fullPath = path.resolve(dir, href);
      if (fullPath.endsWith('.css') && fs.existsSync(fullPath)) {
        try {
          const stat = fs.statSync(fullPath);
          if (stat.isFile()) {
            cssTexts.push(fs.readFileSync(fullPath, 'utf-8'));
          }
        } catch (_) {}
      }
    }
  }
  return cssTexts.join('\n');
}

export function calculateSelectorSpecificity(selectorStr) {
  let a = 0, b = 0, c = 0;
  if (!selectorStr || typeof selectorStr !== 'string') return [0, 0, 0];
  const normalized = selectorStr.replace(/\s*>\s*/g, ' > ').trim();
  const compounds = normalized.split(/\s+/).filter(t => t !== '>');
  for (const comp of compounds) {
    if (comp === '*' || !comp) continue;
    const ids = comp.match(/#[a-zA-Z0-9_-]+/g);
    if (ids) a += ids.length;
    const classes = comp.match(/\.[a-zA-Z0-9_-]+/g);
    if (classes) b += classes.length;
    const attrs = comp.match(/\[[^\]]+\]/g);
    if (attrs) b += attrs.length;
    const tagMatch = comp.match(/^([a-zA-Z0-9_-]+)/);
    if (tagMatch && tagMatch[1] !== '*') {
      c += 1;
    }
  }
  return [a, b, c];
}

export function compareSpecificity(specA, specB) {
  if (specA[0] !== specB[0]) return specA[0] - specB[0];
  if (specA[1] !== specB[1]) return specA[1] - specB[1];
  return specA[2] - specB[2];
}

export function parseCssOrderedRules(cssText) {
  const rules = [];
  if (!cssText) return rules;
  const stripped = cssText.replace(/\/\*[\s\S]*?\*\//g, '');
  const ruleRegex = /([^{}]+)\{([^{}]+)\}/g;
  let match;
  let order = 0;
  while ((match = ruleRegex.exec(stripped)) !== null) {
    const selectors = match[1].split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
    const decls = parseStyleDeclarations(match[2]);
    for (const sel of selectors) {
      rules.push({
        selector: sel,
        decls,
        specificity: calculateSelectorSpecificity(sel),
        order: order++
      });
    }
  }
  return rules;
}

export function parseCssSelectorRules(cssText) {
  const selectorMap = {};
  if (!cssText) return selectorMap;
  const stripped = cssText.replace(/\/\*[\s\S]*?\*\//g, '');
  const ruleRegex = /([^{}]+)\{([^{}]+)\}/g;
  let match;
  while ((match = ruleRegex.exec(stripped)) !== null) {
    const selectors = match[1].split(',').map(s => s.trim().toLowerCase());
    const decls = parseStyleDeclarations(match[2]);
    for (const sel of selectors) {
      if (!selectorMap[sel]) selectorMap[sel] = {};
      Object.assign(selectorMap[sel], decls);
    }
  }
  return selectorMap;
}


export function elementMatchesCompound(node, compound) {
  if (!node || !node.nodeName || node.nodeName.startsWith('#')) return false;
  const attrs = {};
  for (const a of (node.attrs || [])) {
    attrs[a.name.toLowerCase()] = a.value;
  }
  const classes = new Set((attrs['class'] || '').toLowerCase().split(/\s+/).filter(Boolean));
  const id = (attrs['id'] || '').toLowerCase();
  const tag = node.nodeName.toLowerCase();

  const parts = compound.match(/^([a-zA-Z0-9_-]+|\*)?((?:\.[a-zA-Z0-9_-]+|#[a-zA-Z0-9_-]+)*)$/);
  if (!parts) return false;
  const [_, tagPart, rest] = parts;
  if (tagPart && tagPart !== '*' && tagPart.toLowerCase() !== tag) return false;

  if (rest) {
    const tokens = rest.match(/([.#][a-zA-Z0-9_-]+)/g) || [];
    for (const tok of tokens) {
      if (tok.startsWith('.')) {
        if (!classes.has(tok.slice(1).toLowerCase())) return false;
      } else if (tok.startsWith('#')) {
        if (id !== tok.slice(1).toLowerCase()) return false;
      }
    }
  }
  return true;
}

export function matchesSelectorChain(node, ancestors, selectorStr) {
  const normalized = selectorStr.replace(/\s*>\s*/g, ' > ').trim().toLowerCase();
  const tokens = normalized.split(/\s+/);
  let currIdx = tokens.length - 1;
  const targetCompound = tokens[currIdx];
  if (!elementMatchesCompound(node, targetCompound)) return false;
  if (tokens.length === 1) return true;

  currIdx--;
  let ancestorIdx = ancestors.length - 1;
  while (currIdx >= 0) {
    if (tokens[currIdx] === '>') {
      currIdx--;
      if (currIdx < 0 || ancestorIdx < 0) return false;
      const parentCompound = tokens[currIdx];
      if (!elementMatchesCompound(ancestors[ancestorIdx], parentCompound)) return false;
      ancestorIdx--;
      currIdx--;
    } else {
      const ancestorCompound = tokens[currIdx];
      let matched = false;
      while (ancestorIdx >= 0) {
        if (elementMatchesCompound(ancestors[ancestorIdx], ancestorCompound)) {
          matched = true;
          ancestorIdx--;
          break;
        }
        ancestorIdx--;
      }
      if (!matched) return false;
      currIdx--;
    }
  }
  return true;
}

export function findElementsWithAncestors(rootNode, tagNames) {
  const targetTags = new Set(tagNames.map(t => t.toLowerCase()));
  const results = [];
  const stack = [{ node: rootNode, ancestors: [] }];
  while (stack.length > 0) {
    const { node, ancestors } = stack.pop();
    if (node.nodeName && targetTags.has(node.nodeName.toLowerCase())) {
      results.push({ node, ancestors });
    }
    if (node.childNodes && node.childNodes.length > 0) {
      const isElem = node.nodeName && !node.nodeName.startsWith('#');
      const nextAncestors = isElem ? [...ancestors, node] : ancestors;
      for (let i = node.childNodes.length - 1; i >= 0; i--) {
        stack.push({ node: node.childNodes[i], ancestors: nextAncestors });
      }
    }
  }
  return results;
}

function checkHtmlFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  checkedFiles++;

  if (!content || !content.trim() || !content.replace(/<!--[\s\S]*?-->/g, '').trim()) {
    addFinding(filePath, 'Empty or non-scannable HTML file (empty, whitespace-only, or comment-only). Orthotect requires valid markup to verify DOM and layout budgets.', 'dom.empty-document', 1);
    return;
  }

  // `sourceCodeLocationInfo` costs a little memory but is what lets a finding
  // name the line of the offending element instead of defaulting to line 1.
  const doc = requireParse5().parse(content, { sourceCodeLocationInfo: true });
  const combinedCss = extractCssRulesFromHtmlAndLinkedSheets(content, filePath);
  const orderedCssRules = parseCssOrderedRules(combinedCss);

  // 1. Strict media dimension check on parsed AST:
  // Inspects <img>, <video>, and <iframe> elements to prevent CLS layout shift.
  // Resolves full CSS cascade: HTML presentation attributes -> stylesheet rules (specificity + source order) -> inline styles.
  const mediaElements = findElementsWithAncestors(doc, ['img', 'video', 'iframe']);
  for (const { node: el, ancestors } of mediaElements) {
    const tag = el.nodeName.toLowerCase();
    const attrs = {};
    for (const a of (el.attrs || [])) {
      attrs[a.name.toLowerCase()] = a.value;
    }

    // Base presentation attributes
    let cascadedWidth = Object.prototype.hasOwnProperty.call(attrs, 'width') ? { val: attrs['width'], isHtmlAttr: true, isImportant: false } : null;
    let cascadedHeight = Object.prototype.hasOwnProperty.call(attrs, 'height') ? { val: attrs['height'], isHtmlAttr: true, isImportant: false } : null;
    let cascadedAspect = null;

    // Matching CSS stylesheet rules sorted by specificity ascending, then source order ascending
    const matchingRules = [];
    for (const rule of orderedCssRules) {
      if (matchesSelectorChain(el, ancestors, rule.selector)) {
        matchingRules.push(rule);
      }
    }
    matchingRules.sort((r1, r2) => {
      const cmp = compareSpecificity(r1.specificity, r2.specificity);
      if (cmp !== 0) return cmp;
      return r1.order - r2.order;
    });

    for (const rule of matchingRules) {
      if (rule.decls['width']) {
        const isImp = /!important\s*$/i.test(rule.decls['width']);
        if (!cascadedWidth || !cascadedWidth.isImportant || isImp) {
          cascadedWidth = { val: rule.decls['width'], isHtmlAttr: false, isImportant: isImp };
        }
      }
      if (rule.decls['height']) {
        const isImp = /!important\s*$/i.test(rule.decls['height']);
        if (!cascadedHeight || !cascadedHeight.isImportant || isImp) {
          cascadedHeight = { val: rule.decls['height'], isHtmlAttr: false, isImportant: isImp };
        }
      }
      if (rule.decls['aspect-ratio']) {
        const isImp = /!important\s*$/i.test(rule.decls['aspect-ratio']);
        if (!cascadedAspect || !cascadedAspect.isImportant || isImp) {
          cascadedAspect = { val: rule.decls['aspect-ratio'], isHtmlAttr: false, isImportant: isImp };
        }
      }
    }

    // Inline style attribute declarations (specificity (1, 0, 0, 0))
    const styleDecls = parseStyleDeclarations(attrs['style'] || '');
    if (Object.prototype.hasOwnProperty.call(styleDecls, 'width')) {
      const isImp = /!important\s*$/i.test(styleDecls['width']);
      if (!cascadedWidth || !cascadedWidth.isImportant || isImp) {
        cascadedWidth = { val: styleDecls['width'], isHtmlAttr: false, isImportant: isImp, isInline: true };
      }
    }
    if (Object.prototype.hasOwnProperty.call(styleDecls, 'height')) {
      const isImp = /!important\s*$/i.test(styleDecls['height']);
      if (!cascadedHeight || !cascadedHeight.isImportant || isImp) {
        cascadedHeight = { val: styleDecls['height'], isHtmlAttr: false, isImportant: isImp, isInline: true };
      }
    }
    if (Object.prototype.hasOwnProperty.call(styleDecls, 'aspect-ratio')) {
      const isImp = /!important\s*$/i.test(styleDecls['aspect-ratio']);
      if (!cascadedAspect || !cascadedAspect.isImportant || isImp) {
        cascadedAspect = { val: styleDecls['aspect-ratio'], isHtmlAttr: false, isImportant: isImp, isInline: true };
      }
    }

    // Now evaluate winning cascaded values
    const elLine = lineAtOffset(content, el.sourceCodeLocation && el.sourceCodeLocation.startOffset);
    let hasValidAspect = false;
    if (cascadedAspect) {
      hasValidAspect = isValidAspectRatioValue(cascadedAspect.val);
      if (!hasValidAspect && cascadedAspect.isInline) {
        addFinding(filePath, `<${tag}> has invalid CSS aspect-ratio value in style attribute ("${cascadedAspect.val}"). Must be a positive ratio (e.g. "16/9" or "1").`, 'dom.invalid-dimension', elLine);
      }
    }

    let hasValidWidth = false;
    if (cascadedWidth) {
      hasValidWidth = cascadedWidth.isHtmlAttr ? isPositiveDimension(cascadedWidth.val) : isValidCssDimensionValue(cascadedWidth.val);
    }
    let hasValidHeight = false;
    if (cascadedHeight) {
      hasValidHeight = cascadedHeight.isHtmlAttr ? isPositiveDimension(cascadedHeight.val) : isValidCssDimensionValue(cascadedHeight.val);
    }

    const hasBothDimensions = hasValidWidth && hasValidHeight;

    if (!hasBothDimensions && !hasValidAspect) {
      if (cascadedWidth && cascadedHeight && (cascadedWidth.isInline || cascadedHeight.isInline)) {
        addFinding(filePath, `<${tag}> has invalid non-reserving CSS dimensions in style ("width: ${cascadedWidth.val}; height: ${cascadedHeight.val}"). Must be positive dimensions with valid units.`, 'dom.invalid-dimension', elLine);
      } else if (attrs['data-width'] || attrs['data-height']) {
        addFinding(filePath, `<${tag}> uses data-width/data-height instead of native HTML width/height attributes or CSS aspect-ratio.`, 'dom.layout-shift-risk', elLine);
      } else if ('width' in attrs && !hasValidWidth && cascadedWidth && cascadedWidth.isHtmlAttr) {
        addFinding(filePath, `<${tag}> has invalid width attribute value ("${attrs['width']}"). Must be a positive integer.`, 'dom.invalid-dimension', elLine);
      } else if ('height' in attrs && !hasValidHeight && cascadedHeight && cascadedHeight.isHtmlAttr) {
        addFinding(filePath, `<${tag}> has invalid height attribute value ("${attrs['height']}"). Must be a positive integer.`, 'dom.invalid-dimension', elLine);
      } else {
        addFinding(filePath, `<${tag}> tag lacks complete dimensions (requires BOTH width and height attributes, valid CSS width/height, or a valid CSS aspect-ratio property to prevent CLS layout shift).`, 'dom.layout-shift-risk', elLine);
      }
    }
  }


  // 2. Blocking synchronous <script> tags in <head>
  const headNodes = findElements(doc, 'head');
  if (headNodes.length > 0) {
    const scriptNodes = findElements(headNodes[0], 'script');
    for (const sNode of scriptNodes) {
      const sAttrs = {};
      for (const a of (sNode.attrs || [])) {
        sAttrs[a.name.toLowerCase()] = a.value;
      }
      const isAsync = 'async' in sAttrs;
      const isDefer = 'defer' in sAttrs;
      const isModule = sAttrs['type'] === 'module';
      const isInline = !('src' in sAttrs);
      if (!isInline && !isAsync && !isDefer && !isModule) {
        addFinding(filePath, 'Synchronous blocking <script> in <head> without defer/async.', 'dom.blocking-script', lineAtOffset(content, sNode.sourceCodeLocation && sNode.sourceCodeLocation.startOffset));
      }
    }
  }

  // 3. DOM nesting depth AND node-count budgets using a single parse5 AST pass
  const { config: cwvConfig } = loadOrthotectConfig(filePath);
  const maxAllowedDomDepth = cwvConfig?.cwv?.maxDomDepth ?? 32;
  const maxAllowedDomNodes = cwvConfig?.cwv?.maxDomNodes ?? 1500;
  const { maxDepth, elementCount } = analyzeDomStructure(content, filePath);
  if (maxDepth > maxAllowedDomDepth) {
    addFinding(filePath, `Excessive DOM depth of ${maxDepth} levels (Budget max is ${maxAllowedDomDepth}).`, 'dom.excessive-depth', 1);
  }
  if (maxAllowedDomNodes > 0 && elementCount > maxAllowedDomNodes) {
    addFinding(filePath, `Excessive DOM size of ${elementCount} elements (Budget max is ${maxAllowedDomNodes}). Large DOMs inflate style, layout, and memory cost.`, 'dom.excessive-nodes', 1);
  }
}

/**
 * Runs the gate body, translating a missing parser into the contract's exit 2.
 * Without this, a ParserUnavailableError raised from any analysis call would
 * surface as an unhandled rejection (Node exits 1), contradicting the contract:
 * a gate that could not run must never look like a rule violation.
 */
function runMain() {
  try {
    runMainBody();
  } catch (err) {
    if (err instanceof ParserUnavailableError || (err && err.name === 'ParserUnavailableError')) {
      console.error('');
      console.error('❌ [REJECT] DOM & Layout-Shift Budget gate cannot run: missing required package "parse5".');
      console.error('   Cause: Node resolved "parse5" from the Orthotect package itself and did not find it.');
      console.error('          Installing parse5 in the project you are verifying will NOT fix this.');
      console.error('   Fix: run `npm install` inside the orthotect package directory, then re-run verification.');
      console.error('');
      process.exit(EXIT_TOOL_ERROR);
    }
    throw err;
  }
}

function runMainBody() {
  if (cliArgsLoadError) {
    // A missing shared module is a broken installation, not a finding about the
    // audited project. Exit 2 with the cause, rather than letting an uncaught
    // import error surface as Node's exit 1.
    console.error('');
    console.error('❌ [REJECT] DOM & Layout-Shift Budget gate cannot run: missing module "core/cli_args.mjs".');
    console.error(`   Cause: ${String(cliArgsLoadError.message || cliArgsLoadError).split('\n')[0]}`);
    console.error('   Fix: reinstall Orthotect so the core/ modules ship alongside gates/.');
    console.error('');
    process.exit(EXIT_TOOL_ERROR);
  }
  const resolvedTarget = path.resolve(targetDir);
  const targetStat = fs.statSync(targetDir);
  if (targetStat.isFile() && targetDir.endsWith('.html')) {
    checkHtmlFile(targetDir);
  } else {
    const visitedRealDirs = new Set();
    const scan = (dir) => {
      let realDir;
      try {
        realDir = fs.realpathSync(dir);
      } catch (_) {
        return;
      }
      if (visitedRealDirs.has(realDir)) return;
      visitedRealDirs.add(realDir);

      let entries;
      try {
        entries = fs.readdirSync(dir);
      } catch (_) {
        return;
      }

      for (const f of entries) {
        const full = path.join(dir, f);
        try {
          const lstat = fs.lstatSync(full);
          if (lstat.isSymbolicLink()) {
            const realTarget = fs.realpathSync(full);
            // Check if symlink points outside the target tree
            const rel = path.relative(resolvedTarget, realTarget);
            if (rel.startsWith('..') || path.isAbsolute(rel)) {
              // External symlink - do not traverse outside targetDir
              continue;
            }
            const realStat = fs.statSync(realTarget);
            if (realStat.isDirectory()) {
              if (!['node_modules', '.git', 'dist'].includes(f)) scan(full);
            } else if (f.endsWith('.html')) {
              checkHtmlFile(full);
            }
          } else if (lstat.isDirectory()) {
            if (!['node_modules', '.git', 'dist'].includes(f)) scan(full);
          } else if (f.endsWith('.html')) {
            checkHtmlFile(full);
          }
        } catch (_) {}
      }
    };
    scan(targetDir);
  }

  if (checkedFiles === 0) {
    emitToolError('No markup (.html) files found to inspect in: ' + targetDir
      + '. Orthotect requires markup files to verify DOM budgets and CLS avoidance.');
  }

  if (asSarif) {
    emitSarif();
    process.exit(errors.length === 0 ? EXIT_PASS : EXIT_VIOLATION);
  }

  if (errors.length === 0) {
    console.log(`\n✅ [PASS] Layout-Shift & DOM budgets passed across ${checkedFiles} file(s)!`);
    process.exit(EXIT_PASS);
  } else {
    console.log(`\n❌ [REJECT] Found ${errors.length} structural budget violation(s):`);
    errors.forEach(e => console.log(`   - ${e}`));
    process.exit(EXIT_VIOLATION);
  }
}

if (isMain) {
  runMain();
}
