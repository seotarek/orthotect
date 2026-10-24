# Enterprise Production Security Hardening Checklist

Use this checklist during architecture design, code review, and pre-deployment gates.

---

## 1. Secrets & Environment Isolation
- [ ] No API keys, credentials, or private keys are hardcoded in the codebase.
- [ ] `.env`, `.env.local`, and secrets files are listed in `.gitignore`.
- [ ] Production credentials are provided through secret managers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault).
- [ ] Sensitive tokens are rotated automatically every 90 days.

---

## 2. HTTP Headers & Transport Security
- [ ] Strict-Transport-Security (HSTS) header configured (`max-age=63072000; includeSubDomains; preload`).
- [ ] Content-Security-Policy (CSP) configured with nonce-based script execution and disabled `unsafe-inline`.
- [ ] X-Content-Type-Options set to `nosniff`.
- [ ] X-Frame-Options set to `DENY` or `SAMEORIGIN`.
- [ ] Referrer-Policy set to `strict-origin-when-cross-origin`.

---

## 3. Authentication & Session Management
- [ ] Session cookies use `Secure`, `HttpOnly`, and `SameSite=Lax` or `SameSite=Strict`.
- [ ] Passwords hashed using bcrypt (cost 12+), Argon2id, or PBKDF2.
- [ ] Token comparisons use constant-time algorithms (e.g. `crypto.timingSafeEqual`).
- [ ] Password reset flows invalidate previous active sessions.

---

## 4. Input & Data Handling
- [ ] All database queries use parameterized prepared statements.
- [ ] File uploads validate magic numbers/MIME types, restrict extensions, and store outside the webroot.
- [ ] File system operations use `path.resolve` and verify boundaries against root paths.
- [ ] SSRF guards block internal IP ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`).
