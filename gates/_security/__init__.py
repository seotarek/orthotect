#!/usr/bin/env python3
"""
Orthotect Deterministic Quality Gate 6: Enterprise Full-Stack Security & Threat Audit.

Zero-dependency AST & Lexical Static Analysis Security Testing (SAST) engine.
Enforces OWASP Top 10, CWE Top 25, and SANS defense standards across full-stack code:

- Injection Vectors: SQLi, OS Command Injection, NoSQL Injection, SSTI, Eval/Exec
- Client-Side & DOM Sinks: DOM XSS, dangerouslySetInnerHTML, v-html, Prototype
  Pollution, Insecure PostMessage
- Broken Access & SSRF: Server-Side Request Forgery to internal/cloud metadata
  IPs, Path Traversal
- Cryptographic Failures & Hardcoded Secrets: High-entropy API keys,
  AWS/GitHub/Stripe/JWT tokens, MD5/SHA1
- Security Misconfigurations: Wildcard CORS with Credentials, Unsafe
  Deserialization (pickle/yaml)

This package replaces the single-module gate of the same name and keeps its
public surface unchanged: `from gates.gate_security_audit import scan_file,
main` and `from gates.gate_security_audit import is_safe_context` both still
work, and `gates/gate_security_audit.py` remains the CLI entry point.

Layout — one module per rule family, dependencies pointing one way:

    _runtime    exit codes, the shared argument parser
    _patterns   severities, secret/sink patterns, sanitizer allowlist, scope
    _ast        Python AST analysis
    _taint      intra-file taint flow and its text helpers
    _scanner    file scope, safe contexts, per-file scan and deduplication
    _cli        format/target resolution, SARIF, rule-set metadata, main
"""

from ._ast import scan_python_ast
from ._cli import classify_label, main
from ._patterns import (
    BASE_TRUSTED_SANITIZERS,
    CRITICAL,
    HIGH,
    IGNORE_DIRS,
    INJECTION_PATTERNS,
    LOW,
    MEDIUM,
    SCANNABLE_EXTENSIONS,
    SECRET_PATTERNS,
)
from ._scanner import is_engine_file, is_safe_context, is_scannable_file, scan_file
from ._taint import (
    extract_param_bindings,
    mask_sanitizers,
    resolve_trusted_sanitizers,
    scan_intrafile_taint,
    split_comma_declarations,
    split_statements,
    strip_code_comments,
)

__all__ = [
    'BASE_TRUSTED_SANITIZERS', 'CRITICAL', 'HIGH', 'IGNORE_DIRS',
    'INJECTION_PATTERNS', 'LOW', 'MEDIUM', 'SCANNABLE_EXTENSIONS',
    'SECRET_PATTERNS', 'classify_label', 'extract_param_bindings', 'is_engine_file', 'is_safe_context',
    'is_scannable_file', 'main', 'mask_sanitizers', 'resolve_trusted_sanitizers',
    'scan_file', 'scan_intrafile_taint', 'scan_python_ast', 'split_comma_declarations',
    'split_statements', 'strip_code_comments',
]
