/**
 * Orthotect Exit-Code Contract (JavaScript mirror of core/exit_codes.py)
 * ======================================================================
 *
 *    0  PASS       Every enforced rule was evaluated and satisfied.
 *    1  VIOLATION  At least one gate evaluated the code and found a breach.
 *    2  TOOL ERROR The gate could not evaluate the code: missing runtime
 *                  dependency, absent/invalid configuration, unreadable file,
 *                  or a target path that does not exist.
 *
 * Kept in sync with core/exit_codes.py by tests/test_exit_codes.py, which
 * fails if the two files disagree.
 */

export const EXIT_PASS = 0;
export const EXIT_VIOLATION = 1;
export const EXIT_TOOL_ERROR = 2;

export const EXIT_NAMES = {
  [EXIT_PASS]: 'PASS',
  [EXIT_VIOLATION]: 'VIOLATION',
  [EXIT_TOOL_ERROR]: 'TOOL_ERROR',
};

/**
 * Collapse a list of gate exit codes into the worst outcome, so an
 * environment failure is never masked by an ordinary violation.
 * TOOL_ERROR (2) outranks VIOLATION (1) outranks PASS (0).
 */
export function worstExitCode(codes) {
  let worst = EXIT_PASS;
  for (const code of codes) {
    if (code === EXIT_TOOL_ERROR) return EXIT_TOOL_ERROR;
    if (code !== EXIT_PASS) worst = EXIT_VIOLATION;
  }
  return worst;
}
