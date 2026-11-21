# Contributing to Orthotect

Thank you for contributing to Orthotect! We maintain rigorous Google-caliber engineering standards to ensure autonomous AI agents and enterprise engineering teams can rely on deterministic interface guarantees.

## Development Workflow

### 1. Prerequisites
- **Node.js**: >= 20.19.0
- **Python**: >= 3.10.0

### 2. Running Tests
Install the declared dependencies first — `playwright-core` drives the browser tests and `parse5`
backs the DOM gate, so a bare clone reports failures that say nothing about your change:
```bash
npm ci
npm test
```
All 614 unit, browser, AST, and integration gate tests must pass.

Browser-backed tests need Chrome or Chromium installed. Without it they skip locally with a message
naming what is missing; in CI they fail, because silently shrinking coverage is not acceptable there.

### 3. Running Deterministic Quality Gates
Verify that the reference showcase satisfies all six objective gates:
```bash
npx orthotect verify examples/golden-showcase
npx orthotect verify .            # the same six gates against Orthotect's own source
```

### 4. Code Standards & Invariants
1. **Directional Neutrality**: Never use physical CSS direction properties (`margin-left`, `padding-right`, `float: left`). Always use CSS Logical Properties (`margin-inline-start`, `padding-inline-end`).
2. **Intent Tokens**: Hardcoded color hex/rgb codes in component files are strictly banned. Reference tokens via `var(--ot-...)`.
3. **Finite State Machines**: Every interactive component must define an FSM in `core/fsm/` with verified graph reachability and double-submission protection.
4. **No AI Slop**: Do not introduce raw emoji icons inside buttons/headings or generic indigo/purple gradients.
5. **Layout Shift Protection**: All media elements (`<img>`, `<video>`) must declare explicit `width` and `height` attributes or an inline CSS `aspect-ratio` property.

## Pull Request Guidelines
- PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat: ...`, `fix: ...`).
- All GitHub Actions CI checks must be green.
