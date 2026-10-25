# Backend & API Security Threat Defense Reference

Comprehensive architectural guide for hardening backend runtimes, database layers, REST/GraphQL APIs, and background services against enterprise-level attacks.

---

## 1. SQL Injection & Database Boundary Defense (CWE-89)

### ❌ Dangerous: String Interpolation into Queries
```python
# Python DB-API / psycopg2 / sqlite3
cursor.execute(f"SELECT * FROM accounts WHERE tenant_id = '{tenant_id}' AND status = 'active'")
```
```javascript
// Node.js pg / mysql2
db.query("SELECT * FROM users WHERE email = '" + req.body.email + "'");
```

### ✅ Secure: Parameterized Prepared Statements
```python
# Values are passed separately as parameters; DB driver guarantees no query re-parsing
cursor.execute(
    "SELECT * FROM accounts WHERE tenant_id = %s AND status = %s",
    (tenant_id, "active")
)
```
```javascript
// Node.js parameterized query
db.query(
    "SELECT * FROM users WHERE email = $1",
    [req.body.email]
);
```

---

## 2. Server-Side Request Forgery (SSRF) Defense (CWE-918)

### Attack Vector
Attackers provide URLs targeting AWS metadata (`http://169.254.169.254/latest/meta-data/`) or internal Kubernetes pods (`http://10.244.0.5/admin`).

### ✅ Deterministic SSRF Guard (Node.js)
```javascript
import { URL } from 'url';
import dns from 'dns/promises';

const BLOCKED_RANGES = [
  /^127\./,           // Loopback
  /^10\./,            // Private RFC 1918
  /^172\.(1[6-9]|2[0-9]|3[0-1])\./, // Private RFC 1918
  /^192\.168\./,      // Private RFC 1918
  /^169\.254\./,      // Link-local / Cloud Metadata
  /^0\./,             // Current network
  /^::1$/,            // IPv6 loopback
  /^fc00:/i,          // IPv6 private
  /^fe80:/i           // IPv6 link-local
];

export async function validateOutgoingUrl(rawUrl) {
  const parsed = new URL(rawUrl);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('Unsupported protocol');
  }

  // Resolve DNS to verify the actual IP address
  const addresses = await dns.resolve4(parsed.hostname);
  for (const ip of addresses) {
    if (BLOCKED_RANGES.some(regex => regex.test(ip))) {
      throw new Error(`SSRF Blocked: ${parsed.hostname} resolves to private IP ${ip}`);
    }
  }
  return parsed.toString();
}
```

---

## 3. OS Command Injection (CWE-78)

### ❌ Dangerous: Spawning Subprocesses via Shell
```python
# Shell=True invokes /bin/sh which parses shell metacharacters (; && | ` $)
subprocess.Popen(f"tar -czf archive.tar.gz {user_path}", shell=True)
```
```javascript
// child_process.exec spawns a shell
cp.exec(`convert ${imageName} output.png`);
```

### ✅ Secure: Direct Executable Arrays
```python
# Pass arguments as a discrete array without shell invocation
subprocess.run(["tar", "-czf", "archive.tar.gz", user_path], shell=False, check=True)
```
```javascript
// execFile executes binary directly without shell parsing
cp.execFile('convert', [imageName, 'output.png'], (err, stdout) => { ... });
```

---

## 4. Path Traversal & Arbitrary File Reads (CWE-22)

### ❌ Dangerous: Unbounded Path Joins
```javascript
const filePath = path.join('/var/app/uploads', req.query.filename);
// If filename is '../../etc/passwd', resolves to /var/etc/passwd or /etc/passwd
fs.readFile(filePath, ...);
```

### ✅ Secure: Boundary Resolution Guard
```javascript
const BASE_DIRECTORY = path.resolve('/var/app/uploads');
const safeTarget = path.resolve(BASE_DIRECTORY, req.query.filename);

// Verify canonical path starts with the base directory
if (!safeTarget.startsWith(BASE_DIRECTORY + path.sep)) {
  throw new Error('Access denied: Path traversal attempt detected');
}
const content = await fs.promises.readFile(safeTarget);
```

---

## 5. Insecure Deserialization (CWE-502)

### ❌ Dangerous
```python
import pickle
data = pickle.loads(untrusted_bytes)  # Arbitrary code execution

import yaml
data = yaml.load(yaml_string)  # yaml.load without SafeLoader executes arbitrary Python objects
```

### ✅ Secure
```python
import json
data = json.loads(untrusted_json)  # Standard data-only serialization

import yaml
data = yaml.safe_load(yaml_string)  # Strictly parses standard types only
```

---

## 6. Timing Attack Immunity on Hash & Token Comparisons (CWE-208)

### ❌ Dangerous: Standard String Equality
```javascript
// Vulnerable to side-channel timing analysis (short-circuits on first mismatched character)
if (userToken === secretHmac) { ... }
```

### ✅ Secure: Constant-Time Comparison
```javascript
import crypto from 'crypto';

function verifyHmac(userHmac, expectedHmac) {
  const bufA = Buffer.from(userHmac, 'utf8');
  const bufB = Buffer.from(expectedHmac, 'utf8');
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}
```
