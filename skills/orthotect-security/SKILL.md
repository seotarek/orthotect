---
name: orthotect-security
description: Enterprise cybersecurity audit and vulnerability defense for full-stack projects. Scans and remediates OWASP Top 10, CWE Top 25, SQLi, Command Injection, DOM XSS, SSRF, prototype pollution, path traversal, and hardcoded secrets. Use when auditing backend or frontend code for security vulnerabilities, hardening APIs, preventing secret leakage, or running pre-deployment security gates.
metadata:
  version: 1.0.0
---

# Skill: Orthotect Full-Stack Cybersecurity & Threat Defense

Enforce deterministic, enterprise-grade cybersecurity standards across backend, frontend, and infrastructure codebases. Orthotect Gate 6 executes static analysis security testing (SAST) with zero external dependencies to detect and remediate vulnerabilities before deployment.

---

## Reference Routing

Load the matching reference guide before architecting, auditing, or refactoring:

| Topic | Reference File | Covers |
|---|---|---|
| Frontend Threat Defense | [frontend-security.md](references/frontend-security.md) | Client-side DOM XSS, prototype pollution, CSP directives, postMessage origin checks, token isolation |
| Backend & API Hardening | [backend-security.md](references/backend-security.md) | Parameterized SQL/NoSQL queries, SSRF IP filtering & DNS resolution, safe subprocesses, timing attacks |
| OWASP Top 10 Defenses | [owasp-top-10.md](references/owasp-top-10.md) | In-depth breakdown with vulnerable vs secure patterns across Node.js and Python |
| Injection Vectors | [injection-vectors.md](references/injection-vectors.md) | SQLi, NoSQLi, OS Command Injection, SSTI, Prototype Pollution, DOM XSS, SSRF |
| Production Checklist | [security-checklist.md](references/security-checklist.md) | Pre-deployment hardening checklist: Headers, Cookies, Secrets, CSP, HSTS |

---

## Deterministic Quality Gate 6 Execution

Run the security audit gate against any target file or directory:

```bash
# Run standalone Security Audit Gate
python3 gates/gate_security_audit.py <path>

# Run with JSON output (for automated CI/CD pipelines)
python3 gates/gate_security_audit.py <path> --json

# Run as part of the full 6-gate verification suite
node bin/orthotect.js verify <path>
```

---

## The 6 Pillars of Orthotect Threat Defense

### 1. Zero Hardcoded Secrets (CWE-798)
Never commit API tokens, private keys, or passwords.
- Always ingest configuration through `process.env` or `os.environ`.
- Ensure `.env` is declared in `.gitignore`.
- Immediately revoke and rotate any token that was ever committed or pushed to a remote repository.

### 2. Prepared Parameterized Queries (CWE-89)
Eliminate SQL injection at the compiler level:
- Never concatenate strings or format variables into SQL queries (`f"SELECT ... {id}"`).
- Pass dynamic values as tuples or parameterized arrays to database drivers (`cursor.execute("SELECT ... WHERE id = %s", (id,))`).

### 3. Safe Subprocess Execution (CWE-78)
Prevent arbitrary command execution on the host:
- Never use `shell=True` with dynamic user parameters in Python `subprocess`.
- Pass arguments as discrete arrays (`subprocess.run(["cmd", arg1, arg2])`).
- In Node.js, prefer `child_process.execFile` or `execFileSync` over `exec`.

### 4. Client-Side DOM XSS Immunity (CWE-79)
Block cross-site scripting in single-page apps and static templates:
- Use `element.textContent` instead of `element.innerHTML` for dynamic text.
- If HTML markup must be rendered dynamically, sanitize through DOMPurify with strict tag and attribute allowlists.
- Never bind raw `location.search`, `location.hash`, or `document.referrer` directly to execution sinks.

### 5. Server-Side Request Forgery Defense (CWE-918)
Protect internal services and cloud metadata endpoints:
- Validate and whitelist protocols (`http`, `https`).
- Resolve hostnames via DNS and reject private/reserved IP blocks (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`).

### 6. Prototype Pollution & Object Mutation Guards (CWE-1321)
Harden JavaScript object handling:
- Filter forbidden keys (`__proto__`, `constructor`, `prototype`) during deep merge operations.
- Prefer `Object.create(null)` for key-value hash dictionaries that do not inherit from `Object.prototype`.
