---
name: orthotect-hooks
description: Install and configure fail-closed zero-dependency Git pre-commit hooks and CI/CD quality gate enforcement for repository integrity. Use when setting up pre-commit validation, configuring git hooks, or integrating Orthotect into automated GitHub Actions pipelines.
license: MIT
---

# Skill: Orthotect Git Hooks & CI/CD Enforcement

Use this skill when installing pre-commit hooks, configuring automated gate verification in Git, or establishing fail-closed CI/CD pipelines.

## Git Pre-Commit Hook Architecture
Orthotect ships a native, zero-dependency Git hook manager that inspects every staged file before `git commit` completes:
- Automatically backs up foreign hooks to `pre-commit.orthotect.bak`.
- Executes all 5 deterministic quality gates on staged changes.
- Blocks commits with `exit 1` if WCAG contrast, BiDi properties, or FSM models fail.
- Suggests immediate resolution via `npx orthotect verify --fix`.

## Installation & Management Commands
```bash
# Install pre-commit hook into current repository (.git/hooks/pre-commit)
npx orthotect hooks install

# Uninstall hook and restore previous hook backup
npx orthotect hooks uninstall
```

## CI/CD Pipeline Integration (GitHub Actions)
Add fail-closed gate verification to `.github/workflows/ci.yml`:
```yaml
- name: Run Deterministic Quality Gates
  run: |
    npm test
    npx orthotect verify .
```

## Anti-Patterns
- Using `git commit --no-verify` to bypass gate failures instead of running `--fix`.
- Allowing physical CSS properties into production branches.
