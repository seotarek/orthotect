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
    'coverage', '.next', '.cache', 'vendor', '.github', 'tests', 'test',
    '.agents'
}

SCANNABLE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.vue', '.svelte', '.html', '.htm', '.php', '.sql', '.json'
}

def is_scannable_file(filename):
    """Detect if a file is eligible for SAST scanning, including dotfiles (.env, .env.local, .env.production)."""
    if filename in ('skills-lock.json',):
        return False
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

BASE_TRUSTED_SANITIZERS = (
    "DOMPurify.sanitize",
    "validator.escape",
    "he.encode",
    "sanitizeHtml",
)

def resolve_trusted_sanitizers(content):
    """
    Deterministically resolves the set of trusted HTML sanitizers for a specific file.
    Guarantees:
    1. Base trusted libraries: DOMPurify.sanitize, validator.escape, he.encode, sanitizeHtml.
    2. encodeURI and encodeURIComponent are EXCLUDED (URI encoders, not HTML sanitizers).
    3. Shadowing / Fake Definitions: If a file declares a local dummy definition (e.g.
       'const escapeHTML = value => value' or 'const DOMPurify = { sanitize: x => x }'),
       it is classified as UNTRUSTED and cannot neutralize taint.
    4. Custom Sanitizers: 'escapeHTML' or 'escapeHtml' are trusted ONLY if they are:
       - Explicitly imported from an external library, OR
       - Defined locally with verified HTML entity escaping logic (e.g. &amp;, &lt;, etc.).
    """
    trusted = set(BASE_TRUSTED_SANITIZERS)

    # 1. Check for imports of custom sanitizers (e.g. import { escapeHTML } from '...')
    import_re = re.compile(
        r'\bimport\s+[^;]*?\b(escapeHTML|escapeHtml)\b[^;]*?from\s*["\']|'
        r'const\s*\{[^}]*?\b(escapeHTML|escapeHtml)\b[^}]*?\}\s*=\s*require\('
    )
    for m in import_re.finditer(content):
        name = m.group(1) or m.group(2)
        if name:
            trusted.add(name)

    # 2. Check for local declarations/definitions
    decl_pattern = re.compile(
        r'(?:(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*([^;\n]+)|function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)\s*\{([^}]*)\})'
    )

    def has_entity_escaping(code_str):
        return bool(re.search(
            r'&(?:amp|lt|gt|quot|#39|#x27);|\b(?:replace|replaceAll)\s*\(\s*\/[^\/]*[<>&][^\/]*\/|\bcreateElement\s*\(\s*["\']div["\']\s*\)',
            code_str
        ))

    def is_dummy_func(code_str):
        m_arrow = re.search(r'(?:\(([a-zA-Z0-9_$]+)\)|([a-zA-Z0-9_$]+))\s*=>\s*(?:\{\s*return\s+(?:\1|\2)\s*;?\s*\}|(?:\1|\2)\b)', code_str)
        if m_arrow:
            return True
        m_func = re.search(r'function\s*\(\s*([a-zA-Z0-9_$]+)\s*\)\s*\{\s*return\s+\1\s*;?\s*\}', code_str)
        if m_func:
            return True
        return False

    for m in decl_pattern.finditer(content):
        var_name = m.group(1) or m.group(3)
        body = m.group(2) or m.group(5) or ""

        if var_name in ("escapeHTML", "escapeHtml"):
            if is_dummy_func(body) or not has_entity_escaping(body):
                trusted.discard(var_name)
            elif has_entity_escaping(body):
                trusted.add(var_name)

        if var_name == "DOMPurify":
            if is_dummy_func(body) or not has_entity_escaping(body):
                trusted.discard("DOMPurify.sanitize")

        if var_name == "validator":
            if is_dummy_func(body) or not has_entity_escaping(body):
                trusted.discard("validator.escape")

    return tuple(sorted(trusted))

def mask_sanitizers(expr, trusted_sanitizers=None):
    """
    Replaces properly invoked trusted HTML sanitizer function calls with '__SANITIZED__'
    while correctly tracking balanced parentheses to support arbitrary nesting.
    Strictly checks boundaries so methods on untrusted objects (e.g. validator.sanitize)
    or bare custom functions are NOT falsely trusted.
    """
    if trusted_sanitizers is None:
        trusted_sanitizers = BASE_TRUSTED_SANITIZERS

    out = []
    i = 0
    n = len(expr)
    while i < n:
        matched_prefix = None
        for prefix in trusted_sanitizers:
            if expr.startswith(prefix, i):
                if i == 0 or not (expr[i - 1].isalnum() or expr[i - 1] in ("_", "$", ".")):
                    matched_prefix = prefix
                    break
        if matched_prefix:
            j = i + len(matched_prefix)
            while j < n and expr[j].isspace():
                j += 1
            if j < n and expr[j] == "(":
                depth = 1
                k = j + 1
                while k < n and depth > 0:
                    if expr[k] == "(":
                        depth += 1
                    elif expr[k] == ")":
                        depth -= 1
                    k += 1
                if depth == 0:
                    out.append("__SANITIZED__")
                    i = k
                    continue
        out.append(expr[i])
        i += 1
    return "".join(out)

def split_statements(line):
    """
    Splits a single source line into sequential statements separated by ';'
    while preserving semicolons inside string literals ('...', \"...\", `...`)
    and inside parentheses '()', brackets '[]', and braces '{}'.
    Specifically prevents splitting inside 'for (let i = 0; i < n; i++)'.
    """
    statements = []
    current = []
    in_quote = None
    escaped = False
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    for char in line:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if in_quote:
            current.append(char)
            if char == in_quote:
                in_quote = None
        elif char in ("\"", "'", "`"):
            in_quote = char
            current.append(char)
        elif char == "(":
            paren_depth += 1
            current.append(char)
        elif char == ")":
            paren_depth = max(0, paren_depth - 1)
            current.append(char)
        elif char == "[":
            bracket_depth += 1
            current.append(char)
        elif char == "]":
            bracket_depth = max(0, bracket_depth - 1)
            current.append(char)
        elif char == "{":
            brace_depth += 1
            current.append(char)
        elif char == "}":
            brace_depth = max(0, brace_depth - 1)
            current.append(char)
        elif char == ";":
            if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                stmt = "".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(char)
        else:
            current.append(char)

    stmt = "".join(current).strip()
    if stmt:
        statements.append(stmt)
    return statements

def scan_intrafile_taint(filepath, content):
    """
    Intra-file lexical & pattern taint tracking:
    Identifies untrusted sources assigned to local variables and traces their propagation
    through variable assignments, method chains (e.g. raw.trim()), string concatenation,
    and compound expressions into dangerous sinks (e.g. innerHTML, outerHTML, document.write).

    Key Soundness Guarantees:
    1. Sequential Statement Processing: Evaluates multiple statements on a single line in order,
       respecting semicolons inside loops and expressions.
    2. Conservative Branch Sensitivity: Safe reassignments inside conditional blocks
       (if/else/switch/case/catch/loops) or un-braced control statements do NOT clear taint.
    3. Unconditional Reassignment Clearing: Taint state is cleared only when reassigned
       at the same lexical block depth without conditional guards.
    4. Anti-Shadowing Sanitizer Resolution: Rejects dummy/fake sanitizers (e.g. escapeHTML = x => x)
       and enforces verified implementations.
    """
    findings = []
    lines = content.splitlines()

    assign_pattern = re.compile(
        r'(?:(?:const|let|var)\s+)?([a-zA-Z0-9_]+)\s*=\s*([^;\n]+)'
    )
    untrusted_source_re = re.compile(
        r'\b(?:location\.(?:search|hash|href|pathname)|document\.(?:URL|referrer|cookie)|window\.name|new\s+URLSearchParams\()'
    )
    sink_pattern = re.compile(
        r'(?:\.innerHTML|\.outerHTML)\s*=\s*([^;\n]+)|document\.write(?:ln)?\s*\(\s*([^;\n]+)\s*\)'
    )
    conditional_keyword_re = re.compile(
        r'\b(?:if|else|switch|case|catch|while|for)\b'
    )
    header_re = re.compile(
        r'^(?:for|if|while)\s*\([^)]*\)\s*$|^else\s*$'
    )

    trusted_sanitizers = resolve_trusted_sanitizers(content)
    tainted_vars = {}
    brace_depth = 0
    pending_conditional = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith(('//', '/*', '*', '#', '<!--')):
            continue

        statements = split_statements(line)
        for stmt in statements:
            open_braces = 0
            close_braces = 0
            in_q = None
            esc = False
            for ch in stmt:
                if esc:
                    esc = False
                    continue
                if ch == "\\":
                    esc = True
                    continue
                if in_q:
                    if ch == in_q:
                        in_q = None
                elif ch in ("\"", "'", "`"):
                    in_q = ch
                elif ch == "{":
                    open_braces += 1
                elif ch == "}":
                    close_braces += 1

            net_brace = open_braces - close_braces
            is_conditional = bool(conditional_keyword_re.search(stmt)) or pending_conditional
            if pending_conditional:
                pending_conditional = False

            if header_re.search(stmt):
                pending_conditional = True

            # 1. Check for dangerous sink usage
            m_sink = sink_pattern.search(stmt)
            if m_sink:
                sink_expr = (m_sink.group(1) or m_sink.group(2)).strip()
                masked_sink = mask_sanitizers(sink_expr, trusted_sanitizers)

                # Check if sink directly consumes untrusted source (direct DOM XSS)
                if untrusted_source_re.search(masked_sink):
                    findings.append((
                        idx,
                        "DOM XSS (Direct Sink): Direct untrusted source assigned to dangerous DOM sink without sanitization",
                        CRITICAL,
                        stmt.strip()[:80]
                    ))
                else:
                    # Check if sink consumes any tainted variable without sanitization
                    for tvar, meta in list(tainted_vars.items()):
                        if re.search(r'\b' + re.escape(tvar) + r'\b', masked_sink):
                            findings.append((
                                idx,
                                f"DOM XSS (Taint Flow): Variable '{tvar}' (tainted from line {meta['line']}) passed to dangerous DOM sink",
                                CRITICAL,
                                stmt.strip()[:80]
                            ))
                            break

            # 2. Check for variable declarations, taint propagation, or taint clearing
            m_assign = assign_pattern.search(stmt)
            if m_assign:
                var_name = m_assign.group(1)
                rhs = m_assign.group(2).strip()
                masked_rhs = mask_sanitizers(rhs, trusted_sanitizers)

                # Case A: Assigned directly from an untrusted source without full sanitization
                if untrusted_source_re.search(masked_rhs):
                    tainted_vars[var_name] = {"line": idx, "depth": brace_depth}
                else:
                    # Case B: Propagation through method chains, string concatenation, or compound expressions
                    propagated_source_line = None
                    for tvar, meta in list(tainted_vars.items()):
                        if re.search(r'\b' + re.escape(tvar) + r'\b', masked_rhs):
                            propagated_source_line = meta["line"]
                            break

                    if propagated_source_line is not None:
                        tainted_vars[var_name] = {"line": propagated_source_line, "depth": brace_depth}
                    elif var_name in tainted_vars:
                        # Taint is cleared ONLY on unconditional reassignments at the same or outer lexical scope
                        if brace_depth <= tainted_vars[var_name]["depth"] and not is_conditional:
                            del tainted_vars[var_name]

            brace_depth = max(0, brace_depth + net_brace)

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
