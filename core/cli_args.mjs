/**
 * Orthotect CLI Argument Parser (ESM)
 * ===================================
 *
 * The JavaScript mirror of `core/cli_args.py`. Both must behave identically:
 * a flag that leaks its value into the positional list produces "target not
 * found: json" in one language and a correct scan in the other, which is the
 * exact defect this module exists to prevent.
 *
 * `tests/test_cli_args.py` pins the Python side against a shared table of cases
 * and runs the same table through this module via Node, so the two
 * implementations cannot drift apart silently.
 */

/** Flags that consume the following token as their value. */
export const VALUE_FLAGS = new Set([
  '--format', '--out', '--output', '--config', '-o', '--level', '--include', '--exclude',
]);

/** Output formats the gates understand. */
export const OUTPUT_FORMATS = ['console', 'json', 'md'];

export class ParsedArgs {
  constructor(positionals, flags) {
    this.positionals = positionals;
    this.flags = flags;
  }

  has(flag) {
    return this.flags.includes(flag);
  }

  /**
   * Value of a value-taking flag, supporting both `--flag value` and
   * `--flag=value`. Returns `fallback` when absent or given without a value.
   */
  value(flag, fallback = null) {
    for (let i = 0; i < this.flags.length; i++) {
      const token = this.flags[i];
      if (token === flag) {
        return i + 1 < this.flags.length ? this.flags[i + 1] : fallback;
      }
      if (token.startsWith(`${flag}=`)) {
        return token.slice(flag.length + 1);
      }
    }
    return fallback;
  }

  /** First positional argument, or `fallback` when there is none. */
  target(fallback = null) {
    return this.positionals.length ? this.positionals[0] : fallback;
  }
}

/**
 * Splits an argv vector (without the program name) into positionals and flags.
 *
 * The flags list preserves original token order, values included, so `value()`
 * can resolve `--flag value` pairs without a second pass.
 */
export function parseArgs(argv) {
  const positionals = [];
  const flags = [];
  let i = 0;
  while (i < argv.length) {
    const token = argv[i];
    if (token === '--') {
      positionals.push(...argv.slice(i + 1));
      break;
    }
    if (token.startsWith('-') && token !== '-') {
      flags.push(token);
      if (VALUE_FLAGS.has(token) && i + 1 < argv.length) {
        flags.push(argv[i + 1]);
        i += 2;
        continue;
      }
      i += 1;
      continue;
    }
    positionals.push(token);
    i += 1;
  }
  return new ParsedArgs(positionals, flags);
}

/**
 * Resolves the requested output format from `--json`, `--md`, `--format <fmt>`
 * or `--format=<fmt>`. Anything outside `allowed` resolves to null rather than
 * propagating an unknown format to the reporter.
 *
 * `bareToken: true` additionally accepts the legacy `script <dir> json` form,
 * where the format arrives as a trailing positional.
 */
export function resolveOutputFormat(argv, {
  // Mirrors the Python default exactly. A divergence here is silent — the
  // parity suite compares these two functions and nothing else would notice.
  allowed = ['json', 'md', 'sarif'],
  bareToken = false,
} = {}) {
  const parsed = parseArgs(argv);
  if (parsed.has('--json')) return 'json';
  if (parsed.has('--md')) return 'md';
  // Guarded by `allowed` for the same reason `--format sarif` is: a caller that
  // did not opt into machine output must not receive a SARIF document from a
  // bare flag it never advertised.
  if (allowed.includes('sarif') && parsed.has('--sarif')) return 'sarif';

  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (token === '--format') {
      if (i + 1 >= argv.length) return null;
      const value = String(argv[i + 1]).trim().toLowerCase();
      return allowed.includes(value) ? value : null;
    }
    if (token.startsWith('--format=')) {
      const value = token.slice('--format='.length).trim().toLowerCase();
      return allowed.includes(value) ? value : null;
    }
  }

  if (bareToken) {
    for (const token of parsed.positionals) {
      if (allowed.includes(token)) return token;
    }
  }
  return null;
}

/**
 * Non-flag arguments with value-flag leakage prevented.
 * `bareFormatTokens` removes legacy bare format tokens so they are never
 * mistaken for a path.
 */
export function positionals(argv, { bareFormatTokens = [] } = {}) {
  const parsed = parseArgs(argv);
  if (!bareFormatTokens.length) return [...parsed.positionals];
  return parsed.positionals.filter((p) => !bareFormatTokens.includes(p));
}

/** True when `flag` appears as its own token (never as a `--flag=value` prefix). */
export function hasFlag(argv, flag) {
  return parseArgs(argv).has(flag);
}
