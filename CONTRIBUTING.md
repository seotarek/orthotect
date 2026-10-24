# Contributing to Orthotect

Thank you for contributing to Orthotect! We maintain rigorous Google-caliber engineering standards to ensure autonomous AI agents and enterprise engineering teams can rely on deterministic interface guarantees.

## Development Workflow

### 1. Prerequisites
- **Node.js**: >= 20.19.0
- **Python**: >= 3.10.0

### 2. Running Tests
Before submitting any changes, you must run the full automated test suite:
```bash
npm test
```
All 296+ unit, browser, AST, and integration gate tests must pass.

### 3. Running Deterministic Quality Gates
Verify that the reference showcase satisfies all 5 objective gates:
```bash
npx orthotect verify examples/golden-showcase
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
