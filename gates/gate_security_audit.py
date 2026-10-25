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
    (r'(?i)["\']\s*(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|DROP\s+TABLE)\b[^"\';\n]*\b(?:FROM|INTO|SET|WHERE)\b[^"\';\n]*["\']\s*(?:\+\s*[a-zA-Z0-9_]+|%\s*\(?[a-zA-Z0-9_]+)|["\']\s*(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|DROP\s+TABLE)\b[^"\';\n]*\$\{[^}]+\}', "SQL Injection: Raw SQL query dynamically concatenated or formatted with variables", CRITICAL),
    (r'\$where\s*:\s*(?:["\'][^"\']*["\']\s*\+|`[^`]*\$\{)', "NoSQL Injection: Raw MongoDB $where clause with string concatenation", CRITICAL),
    
    # Server-Side Request Forgery (SSRF)
    (r'(?:fetch|axios(?:\.get|\.post)?|requests\.(?:get|post)|http\.(?:get|request))\s*\(\s*["\']https?://(?:127\.0.0\.1|localhost|0\.0\.0\.0|169\.254\.169\.254|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})', "Server-Side Request Forgery (SSRF): Request to private/internal IP address", CRITICAL),
    
    # Path Traversal (dynamic variable with relative path traversal)
    (r'(?:readFileSync|readFile|createReadStream|open)\s*\([^)]*(?:\+\s*["\'][^"\']*\.\./|["\'][^"\']*\.\./[^"\']*["\']\s*\+|`[^`]*\.\./[^`]*\$\{)', "Path Traversal: Relative directory traversal ('../') with dynamic concatenation in file read", HIGH),
    
    # Insecure Deserialization
    (r'\bpickle\.loads?\s*\(', "Insecure Deserialization: Arbitrary code execution via Python pickle", CRITICAL),
    (r'\byaml\.unsafe_load\s*\(', "Insecure Deserialization: yaml.unsafe_load allows arbitrary code execution", CRITICAL),
    (r'\byaml\.load\s*\([^)]*Loader\s*=\s*(?:yaml\.)?(?:Loader|FullLoader|UnsafeLoader)', "Insecure YAML Deserialization: yaml.load with unsafe Loader", HIGH),
    
    # Weak Cryptography
    (r'\bcrypto\.createCipher\s*\(', "Weak Cryptography: Deprecated crypto.createCipher (uses insecure ECB mode without IV)", HIGH),
    (r'hashlib\.(?:md5|sha1)\s*\(', "Weak Cryptography: Broken MD5/SHA1 hash used for cryptographic integrity", MEDIUM),
    
    # CORS Misconfiguration
    (r'["\']Access-Control-Allow-Origin["\']\s*:\s*["\']\*["\'](?=[\s\S]*["\']Access-Control-Allow-Credentials["\']\s*:\s*["\']true["\'])', "Insecure CORS: Wildcard Access-Control-Allow-Origin with Credentials: true", CRITICAL)
]

IGNORE_DIRS = {
    'node_modules', '.git', 'dist', '__pycache__', '.claude', 'tmp',
    'coverage', '.next', '.cache', 'vendor', '.github', 'tests', 'test'
}

SCANNABLE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.vue', '.svelte', '.html', '.htm', '.php', '.sql', '.json'
}

def is_scannable_file(filename):
    """Detect if a file is eligible for SAST scanning, including dotfiles (.env, .env.local, .env.production)."""
    lower = filename.lower()
    if lower == '.env' or lower.startswith('.env.'):
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in SCANNABLE_EXTENSIONS

def is_safe_context(snippet, filepath):
    """Filter out non-exploitable contexts: comments, self-inspection, test assertions, educational knowledge files."""
    lower_path = filepath.lower().replace('\\', '/')
    lower_snip = snippet.lower().strip()
    
    # Safe if inside the security gate itself or test files
    if 'gate_security_audit' in lower_path or '/tests/' in lower_path or '/test/' in lower_path or lower_path.startswith('tests/'):
        return True
        
    # Safe if inside knowledge base or references (educational/anti-pattern definitions)
    if '/knowledge/' in lower_path or '/references/' in lower_path or lower_path.startswith('knowledge/') or lower_path.startswith('references/'):
        return True

    # Safe if line is pure comment or markdown quote
    if lower_snip.startswith(('//', '#', '/*', '*', '<!--', '"""', "'''", '>')):
        return True
        
    return False

def scan_python_ast(filepath, content):
    """Perform AST taint and syntax-level vulnerability checks on Python source code."""
    findings = []
    try:
        tree = ast.parse(content, filename=filepath)
    except SyntaxError:
        return findings

    # Import tracking for YAML modules, direct function imports, and custom aliases
    yaml_modules = {'yaml'}
    direct_unsafe_calls = {'unsafe_load'}
    direct_load_calls = {'load'}
    safe_loader_names = {'SafeLoader', 'CSafeLoader'}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'yaml' and alias.asname:
                    yaml_modules.add(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module == 'yaml':
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    if alias.name == 'unsafe_load':
                        direct_unsafe_calls.add(local_name)
                    elif alias.name == 'load':
                        direct_load_calls.add(local_name)
                    elif alias.name in ('SafeLoader', 'CSafeLoader'):
                        safe_loader_names.add(local_name)

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

            # 4. Insecure yaml.load / yaml.unsafe_load (with full alias & direct import support)
            is_yaml_call = False
            is_unsafe_call = False
            is_load_call = False

            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id in yaml_modules:
                    if node.func.attr == 'unsafe_load':
                        is_yaml_call = True
                        is_unsafe_call = True
                    elif node.func.attr == 'load':
                        is_yaml_call = True
                        is_load_call = True
            elif isinstance(node.func, ast.Name):
                if node.func.id in direct_unsafe_calls:
                    is_yaml_call = True
                    is_unsafe_call = True
                elif node.func.id in direct_load_calls:
                    is_yaml_call = True
                    is_load_call = True

            if is_yaml_call:
                if is_unsafe_call:
                    findings.append((
                        node.lineno,
                        "Insecure Deserialization: yaml.unsafe_load allows arbitrary code execution",
                        CRITICAL,
                        "unsafe_load(...)"
                    ))
                elif is_load_call:
                    loader_kw = next((kw for kw in node.keywords if kw.arg == 'Loader'), None)
                    loader_safe = False
                    if loader_kw:
                        val = loader_kw.value
                        if isinstance(val, ast.Name) and val.id in safe_loader_names:
                            loader_safe = True
                        elif isinstance(val, ast.Attribute):
                            if (isinstance(val.value, ast.Name) and 
                                val.value.id in yaml_modules and 
                                val.attr in safe_loader_names):
                                loader_safe = True

                    if not loader_safe:
                        findings.append((
                            node.lineno,
                            "Insecure Deserialization: yaml.load without SafeLoader",
                            HIGH,
                            "yaml.load(...)"
                        ))

    return findings

def scan_intrafile_taint(filepath, content):
    """
    Intra-file lexical & pattern taint tracking:
    Identifies untrusted sources assigned to local variables and traces their propagation
    through variable assignments, method chains (e.g. raw.trim()), string concatenation,
    and compound expressions into dangerous sinks (e.g. innerHTML, outerHTML, document.write).
    """
    findings = []
    lines = content.splitlines()

    assign_pattern = re.compile(
        r'(?:(?:const|let|var)\s+)?([a-zA-Z0-9_]+)\s*=\s*([^;\n]+)'
    )
    untrusted_source_re = re.compile(
        r'\b(?:location\.(?:search|hash|href|pathname)|document\.(?:URL|referrer|cookie)|window\.name|new\s+URLSearchParams\()'
    )
    sanitizer_pattern = re.compile(
        r'\b(?:DOMPurify\.sanitize|sanitize|escapeHTML|encodeURIComponent)\s*\('
    )
    sink_pattern = re.compile(
        r'(?:\.innerHTML|\.outerHTML)\s*=\s*([^;\n]+)|document\.write(?:ln)?\s*\(\s*([^;\n]+)\s*\)'
    )

    tainted_vars = {}

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith(('//', '/*', '*', '#', '<!--')):
            continue

        # 1. Check for dangerous sink usage
        m_sink = sink_pattern.search(line)
        if m_sink:
            sink_expr = (m_sink.group(1) or m_sink.group(2)).strip()

            # Check if sink directly consumes untrusted source (direct DOM XSS)
            if untrusted_source_re.search(sink_expr):
                if not sanitizer_pattern.search(sink_expr):
                    findings.append((
                        idx,
                        "DOM XSS (Direct Sink): Direct untrusted source assigned to dangerous DOM sink without sanitization",
                        CRITICAL,
                        line.strip()[:80]
                    ))
            else:
                # Check if sink consumes any tainted variable
                for tvar, sline in tainted_vars.items():
                    if re.search(r'\b' + re.escape(tvar) + r'\b', sink_expr):
                        # Verify whether this specific variable is wrapped in a sanitizer in the sink expression
                        sanitized_usage = re.search(
                            r'\b(?:DOMPurify\.sanitize|sanitize|escapeHTML|encodeURIComponent)\s*\([^)]*\b' + re.escape(tvar) + r'\b[^)]*\)',
                            sink_expr
                        )
                        if not sanitized_usage:
                            findings.append((
                                idx,
                                f"DOM XSS (Taint Flow): Variable '{tvar}' (tainted from line {sline}) passed to dangerous DOM sink",
                                CRITICAL,
                                line.strip()[:80]
                            ))
                            break

        # 2. Check for variable declarations and taint propagation
        m_assign = assign_pattern.search(line)
        if m_assign:
            var_name = m_assign.group(1)
            rhs = m_assign.group(2).strip()

            # Case A: Assigned directly from an untrusted source
            if untrusted_source_re.search(rhs):
                if not sanitizer_pattern.search(rhs):
                    tainted_vars[var_name] = idx
            else:
                # Case B: Propagation through method chains, string concatenation, or compound expressions
                for tvar, sline in list(tainted_vars.items()):
                    if re.search(r'\b' + re.escape(tvar) + r'\b', rhs):
                        sanitized_usage = re.search(
                            r'\b(?:DOMPurify\.sanitize|sanitize|escapeHTML|encodeURIComponent)\s*\([^)]*\b' + re.escape(tvar) + r'\b[^)]*\)',
                            rhs
                        )
                        if not sanitized_usage:
                            tainted_vars[var_name] = sline
                            break

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

    # 4. Intra-file Taint Flow Analysis
    if any(filepath.endswith(ext) for ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte', '.html')):
        taint_findings = scan_intrafile_taint(filepath, content)
        for line_no, label, severity, snippet in taint_findings:
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
                if is_scannable_file(file):
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
            "scope": {
                "included": "Application frontend & backend source files (.py, .js, .ts, .html, .json, .env*)",
                "excluded": "tests/, .github/, node_modules/, dist/"
            },
            "notice": "Deterministic SAST verification passed (AST & intra-file taint analysis). Verifies static syntax, dangerous sinks, and secrets; does not replace runtime penetration testing.",
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
        print(f"**Target:** `{target_dir}` | **Status:** {'✅ PASSED (Deterministic SAST)' if passed else '❌ VULNERABILITIES DETECTED'} | **Files Scanned:** {len(files_to_scan)}")
        print(f"**Scope:** Application source files (.py, .js, .ts, .html, .json, .env*). Excluded: tests/, .github/, node_modules/, dist/.\n")
        if not passed:
            print("| File | Line | Severity | Vulnerability | Snippet |")
            print("| :--- | :---: | :---: | :--- | :--- |")
            for fpath, vulns in file_reports.items():
                rel = os.path.relpath(fpath, target_dir)
                for line, label, sev, snip in vulns:
                    print(f"| `{rel}` | {line} | **{sev}** | {label} | `{snip}` |")
        else:
            print("> **Scope Notice:** Deterministic SAST verification passed (AST & intra-file taint analysis). Verifies static syntax, dangerous sinks, and secrets. Does not replace dynamic runtime penetration testing, DAST, or manual security review.\n")
        sys.exit(0 if passed else 1)

    # Standard Console ASCII Banner
    print("═══════════════════════════════════════════════════════════════")
    print("  ORTHOTECT GATE 6: Deterministic SAST Security & Threat Audit")
    print("  Deterministic SAST & Dangerous Sink Inspection (OWASP / CWE)")
    print("═══════════════════════════════════════════════════════════════")
    print(f" Target Path: {target_dir}")
    print(f" Scanned Scope: {len(files_to_scan)} application source files (.py, .js, .ts, .html, .json, .env*)")
    print(f" Excluded Scope: Tests (tests/), CI (.github/), Vendor (node_modules/), Build (dist/)\n")

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
        print("   Scope: Syntactic AST patterns, dangerous sink detection, and intra-file taint tracking.")
        print("   Notice: Verifies static patterns & secrets. Does not replace dynamic runtime penetration testing or load audits.")
        sys.exit(0)

if __name__ == '__main__':
    main()
