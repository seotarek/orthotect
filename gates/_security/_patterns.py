"""
What the scanner looks for: severity levels, secret and sink patterns, and scope.

The two pattern tables are the rule *content*; keeping them in a module with no
logic means a reviewer can read every detection in one screen, and a new pattern
is added in one place rather than next to the code that consumes it.
"""
import os

CRITICAL = "CRITICAL"


HIGH = "HIGH"


MEDIUM = "MEDIUM"


LOW = "LOW"


SECRET_PATTERNS = [
    (r'(?i)\b(?:api_key|apikey|auth_token|client_secret|private_key|secret_key)\s*[:=]\s*["\']([a-zA-Z0-9_\-\.]{24,})["\']', "Hardcoded High-Entropy API Key or Secret", HIGH),
    (r'\bAKIA[0-9A-Z]{16}\b', "Hardcoded AWS Access Key ID", CRITICAL),
    (r'\bghp_[a-zA-Z0-9]{36}\b', "Hardcoded GitHub Personal Access Token", CRITICAL),
    (r'\bsk_live_[0-9a-zA-Z]{24,}\b', "Hardcoded Stripe Live Secret Key", CRITICAL),
    (r'\b(?:live|prod)_(?:secret|key)_[0-9a-zA-Z_]{20,}\b', "Hardcoded Production Secret Key", CRITICAL),
    (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Hardcoded Asymmetric Private Key", CRITICAL),
    (r'\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b', "Hardcoded JWT Token", HIGH)
]


INJECTION_PATTERNS = [
    # Command Injection
    (r'\b(?:child_process|cp)\.(?:exec|execSync)\s*\(\s*(?:`[^`]*\$\{[^}]+\}[^`]*`|["\'][^"\']*["\']\s*\+\s*[a-zA-Z0-9_]+|[a-zA-Z0-9_]+\s*\+)', "OS Command Injection: child_process.exec with dynamic un-sanitized string", CRITICAL),
    (r'\bos\.system\s*\(\s*(?:f["\'][^"\']*\{[^}]+\}[^"\']*["\']|["\'][^"\']*["\']\s*%\s*[a-zA-Z0-9_]+|["\'][^"\']*["\']\s*\+\s*[a-zA-Z0-9_]+)', "OS Command Injection: os.system with dynamic formatted string", CRITICAL),
    (r'\bsubprocess\.(?:Popen|call|run|check_call|check_output)\s*\([^)]*shell\s*=\s*True', "OS Command Injection: subprocess invocation with shell=True", HIGH),
    
    # Eval & Dynamic Code Sinks
    (r'\beval\s*\(\s*(?![a-zA-Z0-9_]+\s*==)[^)]*[\$\+\`]', "Unsafe Dynamic Code Execution (eval sink with dynamic input)", CRITICAL),
    (r'\bnew\s+Function\s*\([^)]*[\$\+\`]', "Unsafe Dynamic Function constructor execution with dynamic input", HIGH),
    
    # DOM XSS & Client-Side Sinks
    (r'\.(?:innerHTML|outerHTML|srcdoc)\s*=\s*[^;\n]*(?:location\.(?:search|hash|href|pathname)|document\.(?:URL|referrer)|window\.name|prompt\()', "DOM XSS: Direct assignment of un-sanitized URL/location source to DOM HTML sink", CRITICAL),
    (r'\.insertAdjacentHTML\s*\([^,]+,\s*[^)]*(?:location\.(?:search|hash|href|pathname)|document\.(?:URL|referrer)|window\.name|prompt\()', "DOM XSS: Direct un-sanitized source passed to insertAdjacentHTML()", CRITICAL),
    (r'\bcreateContextualFragment\s*\([^)]*(?:location\.(?:search|hash|href|pathname)|document\.(?:URL|referrer)|window\.name|prompt\()', "DOM XSS: Direct un-sanitized source passed to createContextualFragment()", CRITICAL),
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


BASE_TRUSTED_SANITIZERS = (
    "DOMPurify.sanitize",
    "validator.escape",
    "he.encode",
)
