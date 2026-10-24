# OWASP Top 10 Enterprise Defense Reference

This guide provides deterministic vulnerability patterns, risk explanations, and production-tested remediations across Python, Node.js, and TypeScript.

---

## 1. Broken Access Control (A01:2021 / CWE-22, CWE-918, CWE-862)

### Server-Side Request Forgery (SSRF)
**Risk:** An attacker forces backend servers to make unauthorized HTTP requests to internal networks or cloud metadata APIs (`169.254.169.254`).

#### ❌ Vulnerable (Node.js)
```javascript
app.post('/api/fetch-url', async (req, res) => {
  const { url } = req.body;
  // Dangerous: Attacker can supply 'http://169.254.169.254/latest/meta-data/'
  const response = await fetch(url);
  const data = await response.text();
  res.send(data);
});
```

#### ✅ Secure (Node.js)
```javascript
import { URL } from 'url';
import dns from 'dns/promises';

const BLOCKED_IP_PREFIXES = ['127.', '10.', '192.168.', '172.16.', '169.254.', '0.'];

async function isSafeUrl(targetUrl) {
  const parsed = new URL(targetUrl);
  if (!['http:', 'https:'].includes(parsed.protocol)) return false;
  
  const addresses = await dns.resolve4(parsed.hostname);
  for (const ip of addresses) {
    if (BLOCKED_IP_PREFIXES.some(prefix => ip.startsWith(prefix))) {
      return false;
    }
  }
  return true;
}
```

---

## 2. Cryptographic Failures (A02:2021 / CWE-327, CWE-798)

### Hardcoded Secrets & Weak Hashing
**Risk:** Embedded credentials allow unauthorized repository viewers or scrapers to hijack production infrastructure.

#### ❌ Vulnerable (Python)
```python
import hashlib

API_KEY = "sk_live_93817498273498273498234"
def hash_password(password):
    # Broken: MD5 is vulnerable to collision attacks
    return hashlib.md5(password.encode()).hexdigest()
```

#### ✅ Secure (Python)
```python
import os
import bcrypt

API_KEY = os.environ.get("PRODUCTION_API_KEY")

def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt)
```

---

## 3. Injection (A03:2021 / CWE-89, CWE-78, CWE-79)

### SQL Injection
**Risk:** User input concatenated directly into SQL queries allows attackers to bypass authentication or extract the entire database.

#### ❌ Vulnerable (Python)
```python
cursor.execute(f"SELECT * FROM users WHERE email = '{email}' AND status = 1")
```

#### ✅ Secure (Python)
```python
cursor.execute("SELECT * FROM users WHERE email = %s AND status = %s", (email, 1))
```

### OS Command Injection
**Risk:** Spawning child processes with user input executes arbitrary host commands.

#### ❌ Vulnerable (Node.js)
```javascript
const { exec } = require('child_process');
exec(`convert image.png -resize ${size} out.png`);
```

#### ✅ Secure (Node.js)
```javascript
const { execFile } = require('child_process');
// Pass arguments as a discrete array without shell invocation
execFile('convert', ['image.png', '-resize', String(size), 'out.png']);
```

---

## 4. Insecure Design (A04:2021 / CWE-209, CWE-1059)
- Always validate and parse inputs using strict schemas (e.g. Zod or Pydantic).
- Implement rate limiting and exponential backoff on sensitive authentication endpoints.

---

## 5. Security Misconfiguration (A05:2021 / CWE-16, CWE-942)

### Insecure CORS
#### ❌ Vulnerable (Express)
```javascript
// Wildcard origin with credentials allows any website to read authenticated session data
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Credentials", "true");
  next();
});
```

#### ✅ Secure (Express)
```javascript
const ALLOWED_ORIGINS = new Set(['https://app.example.com', 'https://admin.example.com']);

app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (ALLOWED_ORIGINS.has(origin)) {
    res.header("Access-Control-Allow-Origin", origin);
    res.header("Access-Control-Allow-Credentials", "true");
  }
  next();
});
```
