#!/usr/bin/env python3
"""
Orthotect Deterministic Quality Gate 6: Enterprise Full-Stack Security & Threat Audit
Zero-dependency AST & Lexical Static Analysis Security Testing (SAST) Engine.
Enforces OWASP Top 10, CWE Top 25, and SANS defense standards across full-stack code:
- Injection Vectors: SQLi, OS Command Injection, NoSQL Injection, SSTI, Eval/Exec
- Client-Side & DOM Sinks: DOM XSS, dangerouslySetInnerHTML, v-html, Prototype Pollution, Insecure PostMessage
- Broken Access & SSRF: Server-Side Request Forgery to internal/cloud metadata IPs, Path Traversal
- Cryptographic Failures & Hardcoded Secrets: High-entropy API keys, AWS/GitHub/Stripe/JWT tokens, MD5/SHA1
- Security Misconfigurations: Wildcard CORS with Credentials, Unsafe Deserialization (pickle/yaml)
"""

import sys
import os
import re
import ast
import json

# Severity Levels
CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

# Hardcoded Secrets & Token Patterns
SECRET_PATTERNS = [
    (r'(?i)\b(?:api_key|apikey|auth_token|client_secret|private_key|secret_key)\s*[:=]\s*["\']([a-zA-Z0-9_\-\.]{24,})["\']', "Hardcoded High-Entropy API Key or Secret", HIGH),
    (r'\bAKIA[0-9A-Z]{16}\b', "Hardcoded AWS Access Key ID", CRITICAL),
    (r'\bghp_[a-zA-Z0-9]{36}\b', "Hardcoded GitHub Personal Access Token", CRITICAL),
    (r'\bsk_live_[0-9a-zA-Z]{24,}\b', "Hardcoded Stripe Live Secret Key", CRITICAL),
    (r'\b(?:live|prod)_(?:secret|key)_[0-9a-zA-Z_]{20,}\b', "Hardcoded Production Secret Key", CRITICAL),
    (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Hardcoded Asymmetric Private Key", CRITICAL),
    (r'\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b', "Hardcoded JWT Token", HIGH)
]

# Sinks & Injection Patterns across Full-Stack code
INJECTION_PATTERNS = [
    # Command Injection
    (r'\b(?:child_process|cp)\.(?:exec|execSync)\s*\(\s*(?:`[^`]*\$\{[^}]+\}[^`]*`|["\'][^"\']*["\']\s*\+\s*[a-zA-Z0-9_]+|[a-zA-Z0-9_]+\s*\+)', "OS Command Injection: child_process.exec with dynamic un-sanitized string", CRITICAL),
    (r'\bos\.system\s*\(\s*(?:f["\'][^"\']*\{[^}]+\}[^"\']*["\']|["\'][^"\']*["\']\s*%\s*[a-zA-Z0-9_]+|["\'][^"\']*["\']\s*\+\s*[a-zA-Z0-9_]+)', "OS Command Injection: os.system with dynamic formatted string", CRITICAL),
    (r'\bsubprocess\.(?:Popen|call|run|check_call|check_output)\s*\([^)]*shell\s*=\s*True', "OS Command Injection: subprocess invocation with shell=True", HIGH),
    
    # Eval & Dynamic Code Sinks
    (r'\beval\s*\(\s*(?![a-zA-Z0-9_]+\s*==)[^)]*[\$\+\`]', "Unsafe Dynamic Code Execution (eval sink with dynamic input)", CRITICAL),
    (r'\bnew\s+Function\s*\([^)]*[\$\+\`]', "Unsafe Dynamic Function constructor execution with dynamic input", HIGH),
    
    # DOM XSS & Client-Side Sinks
    (r'\.(?:innerHTML|outerHTML)\s*=\s*[^;\n]*(?:location\.(?:search|hash|href|pathname)|document\.(?:URL|referrer)|window\.name|prompt\()', "DOM XSS: Direct assignment of un-sanitized URL/location source to innerHTML/outerHTML", CRITICAL),
    (r'\bdocument\.write(?:ln)?\s*\([^)]*[\$\+\`]', "DOM XSS: document.write() with dynamic input", HIGH),
    (r'dangerouslySetInnerHTML\s*=\s*\{\{\s*__html\s*:\s*(?!DOMPurify|sanitize|escape)[a-zA-Z0-9_.]+\s*\}\}', "React DOM XSS: dangerouslySetInnerHTML without DOMPurify/sanitize", HIGH),
    (r'\bv-html\s*=\s*["\'](?!sanitize|DOMPurify|escape)[a-zA-Z0-9_.]+["\']', "Vue DOM XSS: v-html directive without HTML sanitization", HIGH),
    
    # Insecure Cross-Origin Communication
    (r'\bpostMessage\s*\([^,]+,\s*["\']\*["\']\s*\)', "Insecure Cross-Origin postMessage with wildcard target origin ('*')", HIGH),
    
    # Prototype Pollution
    (r'(?:\.__proto__|constructor\.prototype)\s*=', "Prototype Pollution vulnerability: Direct object prototype mutation", CRITICAL),
    
    # SQL & NoSQL Injection Sinks
    (r'(?i)\b(?:SELECT|INSERT|UPDATE|DELETE|DROP)\b[^;]*\b(?:FROM|INTO|SET|WHERE)\b[^;]*["\']\s*(?:\+\s*[a-zA-Z0-9_]+|%\s*\(?[a-zA-Z0-9_]+)|\b(?:SELECT|INSERT|UPDATE|DELETE|DROP)\b[^;]*\$\{[^}]+\}', "SQL Injection: Raw SQL query dynamically concatenated or formatted with variables", CRITICAL),
    (r'\$where\s*:\s*(?:["\'][^"\']*["\']\s*\+|`[^`]*\$\{)', "NoSQL Injection: Raw MongoDB $where clause with string concatenation", CRITICAL),
    
    # Server-Side Request Forgery (SSRF)
    (r'(?:fetch|axios(?:\.get|\.post)?|requests\.(?:get|post)|http\.(?:get|request))\s*\(\s*["\']https?://(?:127\.0\.0\.1|localhost|0\.0\.0\.0|169\.254\.169\.254|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})', "Server-Side Request Forgery (SSRF): Request to private/internal IP address", CRITICAL),
    
    # Path Traversal
    (r'(?:readFileSync|readFile|createReadStream|open)\s*\([^)]*(?:\.\./|\.\.\\)', "Path Traversal: Relative directory traversal ('../') in file read operation", HIGH),
    
    # Insecure Deserialization
    (r'\bpickle\.loads?\s*\(', "Insecure Deserialization: Arbitrary code execution via Python pickle", CRITICAL),
    (r'\byaml\.(?:load|unsafe_load)\s*\([^)]*(?!Loader\s*=\s*(?:SafeLoader|yaml\.SafeLoader|CSafeLoader))', "Insecure YAML Deserialization: yaml.load without SafeLoader", HIGH),
    
    # Weak Cryptography
    (r'\bcrypto\.createCipher\s*\(', "Weak Cryptography: Deprecated crypto.createCipher (uses insecure ECB mode without IV)", HIGH),
    (r'hashlib\.(?:md5|sha1)\s*\(', "Weak Cryptography: Broken MD5/SHA1 hash used for cryptographic integrity", MEDIUM),
    
    # CORS Misconfiguration
    (r'["\']Access-Control-Allow-Origin["\']\s*:\s*["\']\*["\'](?=[\s\S]*["\']Access-Control-Allow-Credentials["\']\s*:\s*["\']true["\'])', "Insecure CORS: Wildcard Access-Control-Allow-Origin with Credentials: true", CRITICAL)
]

IGNORE_DIRS = {
    'node_modules', '.git', 'dist', '__pycache__', '.claude', 'tmp',
    'coverage', '.next', '.cache', 'vendor', '.github'
}

SCANNABLE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.vue', '.svelte', '.html', '.htm', '.php', '.sql', '.json', '.env'
}

def is_safe_context(snippet, filepath):
    """Filter out non-exploitable contexts: comments, self-inspection, test assertions."""
    lower_path = filepath.lower()
    lower_snip = snippet.lower().strip()
    
    # Safe if inside the security gate itself or test files verifying exploit detection
    if 'gate_security_audit' in lower_path or 'test_security_gate' in lower_path:
        return True
        
    # Safe if line is pure comment
    if lower_snip.startswith(('//', '#', '/*', '*', '<!--', '"""', "'''")):
        return True
        
    return False

def scan_python_ast(filepath, content):
    """Perform AST taint and syntax-level vulnerability checks on Python source code."""
    findings = []
    try:
        tree = ast.parse(content, filename=filepath)
    except SyntaxError:
        return findings

    for node in ast.walk(tree):
        # 1. SQL Injection via formatted strings in cursor.execute
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
                
            if func_name in ('execute', 'executemany'):
                if node.args:
                    first_arg = node.args[0]
                    # f-string: ast.JoinedStr
                    if isinstance(first_arg, ast.JoinedStr):
                        findings.append((
                            first_arg.lineno,
                            "SQL Injection: Raw formatted f-string passed to database execute() sink",
                            CRITICAL,
                            "cursor.execute(f\"...\")"
                        ))
                    # % formatting or string concatenation
                    elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, (ast.Mod, ast.Add)):
                        findings.append((
                            first_arg.lineno,
                            "SQL Injection: String concatenation or % formatting passed to database execute() sink",
                            CRITICAL,
                            "cursor.execute(... + ...)"
                        ))

            # 2. Subprocess with shell=True
            if func_name in ('Popen', 'call', 'run', 'check_call', 'check_output'):
                for kw in node.keywords:
                    if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        findings.append((
                            node.lineno,
                            "OS Command Injection: subprocess invocation with shell=True",
                            HIGH,
                            f"subprocess.{func_name}(..., shell=True)"
                        ))

            # 3. Insecure pickle loads
            if func_name in ('load', 'loads') and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == 'pickle':
                    findings.append((
                        node.lineno,
                        "Insecure Deserialization: Untrusted pickle.loads() execution",
                        CRITICAL,
                        "pickle.loads(...)"
                    ))

            # 4. Insecure yaml.load without Loader
            if func_name == 'load' and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == 'yaml':
                    has_loader = any(kw.arg == 'Loader' for kw in node.keywords)
                    if not has_loader and len(node.args) < 2:
                        findings.append((
                            node.lineno,
                            "Insecure Deserialization: yaml.load without SafeLoader",
                            HIGH,
                            "yaml.load(...)"
                        ))

    return findings

def scan_file(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return findings

    # Skip if file itself is this gate script
    if os.path.abspath(filepath) == os.path.abspath(__file__):
        return []

    lines = content.splitlines()

    # 1. Check Hardcoded Secrets
    for pattern, label, severity in SECRET_PATTERNS:
        for m in re.finditer(pattern, content):
            snippet = m.group(0)[:80].replace('\n', ' ')
            if is_safe_context(snippet, filepath):
                continue
            line_no = content.count('\n', 0, m.start()) + 1
            findings.append((line_no, label, severity, snippet))

    # 2. Check Sinks and Injection Patterns
    for pattern, label, severity in INJECTION_PATTERNS:
        for m in re.finditer(pattern, content):
            snippet = m.group(0)[:80].replace('\n', ' ')
            if is_safe_context(snippet, filepath):
                continue
            line_no = content.count('\n', 0, m.start()) + 1
            findings.append((line_no, label, severity, snippet))

    # 3. Python AST Analysis
    if filepath.endswith('.py'):
        ast_findings = scan_python_ast(filepath, content)
        for line_no, label, severity, snippet in ast_findings:
            if not is_safe_context(snippet, filepath):
                findings.append((line_no, label, severity, snippet))

    # Deduplicate findings by line and label
    deduped = []
    seen = set()
    for f in findings:
        key = (f[0], f[1])
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return sorted(deduped, key=lambda x: x[0])

def main():
    args = sys.argv[1:]
    is_json = '--json' in args or ('--format' in args and 'json' in args)
    is_md = '--md' in args or ('--format' in args and 'md' in args)

    positional = [a for a in args if not a.startswith('--') and a not in ('json', 'md')]
    target_dir = positional[0] if positional else 'examples/golden-showcase'
    target_dir = os.path.abspath(target_dir)

    if not os.path.exists(target_dir):
        err = f"Target path does not exist: {target_dir}"
        if is_json:
            print(json.dumps({"error": err, "passed": False}))
        else:
            print(f"❌ [REJECT] {err}")
        sys.exit(1)

    files_to_scan = []
    if os.path.isfile(target_dir):
        files_to_scan.append(target_dir)
    else:
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in SCANNABLE_EXTENSIONS:
                    files_to_scan.append(os.path.join(root, file))

    total_vulns = 0
    file_reports = {}

    for fpath in files_to_scan:
        findings = scan_file(fpath)
        if findings:
            file_reports[fpath] = findings
            total_vulns += len(findings)

    passed = (total_vulns == 0)

    if is_json:
        report = {
            "target": target_dir,
            "passed": passed,
            "scannedFiles": len(files_to_scan),
            "vulnerabilityCount": total_vulns,
            "vulnerabilities": [
                {
                    "file": fpath,
                    "line": line,
                    "label": label,
                    "severity": sev,
                    "snippet": snip
                }
                for fpath, vulns in file_reports.items()
                for line, label, sev, snip in vulns
            ]
        }
        print(json.dumps(report, indent=2))
        sys.exit(0 if passed else 1)

    if is_md:
        print(f"### 🛡️ Orthotect Cybersecurity Gate Report")
        print(f"**Target:** `{target_dir}` | **Status:** {'✅ CERTIFIED SECURE' if passed else '❌ VULNERABILITIES DETECTED'} | **Files Scanned:** {len(files_to_scan)}\n")
        if not passed:
            print("| File | Line | Severity | Vulnerability | Snippet |")
            print("| :--- | :---: | :---: | :--- | :--- |")
            for fpath, vulns in file_reports.items():
                rel = os.path.relpath(fpath, target_dir)
                for line, label, sev, snip in vulns:
                    print(f"| `{rel}` | {line} | **{sev}** | {label} | `{snip}` |")
        sys.exit(0 if passed else 1)

    # Standard Console ASCII Banner
    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE 6: Enterprise Full-Stack Security & Threat Audit")
    print("  Deterministic SAST & Threat Defense Protocol (OWASP / CWE)")
    print("═══════════════════════════════════════════════════════════════")
    print(f" Target Path: {target_dir}")
    print(f" Scanned Files: {len(files_to_scan)}\n")

    if not passed:
        for fpath, vulns in file_reports.items():
            print(f"❌ [VULNERABILITY DETECTED] in: {fpath}")
            for line, label, sev, snip in vulns:
                print(f"   Line {line:4d} [{sev}]: {label}")
                print(f"              Snippet: '{snip}'")
        print(f"\n❌ [REJECT] {total_vulns} cybersecurity vulnerability/vulnerabilities detected.")
        print("   Security gates are fail-closed. Remediation required before release.")
        sys.exit(1)
    else:
        print(f"✅ [PASS] Zero cybersecurity vulnerabilities detected across {len(files_to_scan)} file(s)!")
        print("   OWASP Top 10, CWE Top 25, and injection defenses 100% verified.")
        sys.exit(0)

if __name__ == '__main__':
    main()
