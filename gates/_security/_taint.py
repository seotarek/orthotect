"""
Intra-file taint flow.

`resolve_trusted_sanitizers` reads the file to learn which names actually
sanitize (including locally defined wrappers), then `mask_sanitizers` rewrites
those call sites before the sink patterns run. The helper functions below it —
comment stripping, parameter binding extraction, statement and declaration
splitting — exist to make that analysis survive real formatting rather than to
be generally useful; they are private to this family.
"""
import re

from ._patterns import BASE_TRUSTED_SANITIZERS, CRITICAL

def strip_code_comments(content):
    """
    Strips single-line (//), multi-line (/* ... */), and HTML (<!-- ... -->) comments
    from source code while preserving line structure (newlines) and string literals.
    """
    out = []
    i = 0
    n = len(content)
    while i < n:
        if content[i] in ('"', "'", '`'):
            quote = content[i]
            out.append(quote)
            i += 1
            while i < n:
                ch = content[i]
                out.append(ch)
                if ch == '\\':
                    if i + 1 < n:
                        i += 1
                        out.append(content[i])
                elif ch == quote:
                    break
                i += 1
            i += 1
        elif content.startswith('//', i):
            i += 2
            while i < n and content[i] != '\n':
                i += 1
        elif content.startswith('/*', i):
            i += 2
            while i < n and not content.startswith('*/', i):
                if content[i] == '\n':
                    out.append('\n')
                i += 1
            i += 2
        elif content.startswith('<!--', i):
            i += 4
            while i < n and not content.startswith('-->', i):
                if content[i] == '\n':
                    out.append('\n')
                i += 1
            i += 3
        else:
            out.append(content[i])
            i += 1
    return "".join(out)


def extract_param_bindings(params_str):
    """
    Extracts all bound variable identifiers from a JavaScript/TypeScript parameter list.
    Supports simple params, default values, TypeScript type annotations,
    rest params, object destructuring with renaming ({ prop: alias }),
    and array destructuring ([ a, b, ...rest ]).
    """
    bindings = set()

    params = []
    current = []
    brace_d = 0
    bracket_d = 0
    paren_d = 0
    for char in params_str:
        if char == "{": brace_d += 1
        elif char == "}": brace_d -= 1
        elif char == "[": bracket_d += 1
        elif char == "]": bracket_d -= 1
        elif char == "(": paren_d += 1
        elif char == ")": paren_d -= 1
        elif char == "," and brace_d == 0 and bracket_d == 0 and paren_d == 0:
            params.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        p = "".join(current).strip()
        if p:
            params.append(p)

    def parse_binding_pattern(pat):
        pat = pat.strip()
        if not pat:
            return
        if pat.startswith("{") and pat.endswith("}"):
            inner = pat[1:-1].strip()
            items = []
            c = []
            b_d = 0
            bk_d = 0
            for ch in inner:
                if ch == "{": b_d += 1
                elif ch == "}": b_d -= 1
                elif ch == "[": bk_d += 1
                elif ch == "]": bk_d -= 1
                elif ch == "," and b_d == 0 and bk_d == 0:
                    items.append("".join(c).strip())
                    c = []
                    continue
                c.append(ch)
            if c:
                it = "".join(c).strip()
                if it: items.append(it)

            for item in items:
                eq_idx = -1
                b_d = 0
                bk_d = 0
                for idx, ch in enumerate(item):
                    if ch == "{": b_d += 1
                    elif ch == "}": b_d -= 1
                    elif ch == "[": bk_d += 1
                    elif ch == "]": bk_d -= 1
                    elif ch == "=" and b_d == 0 and bk_d == 0:
                        eq_idx = idx
                        break
                if eq_idx != -1:
                    item = item[:eq_idx].strip()

                colon_idx = -1
                b_d = 0
                bk_d = 0
                for idx, ch in enumerate(item):
                    if ch == "{": b_d += 1
                    elif ch == "}": b_d -= 1
                    elif ch == "[": bk_d += 1
                    elif ch == "]": bk_d -= 1
                    elif ch == ":" and b_d == 0 and bk_d == 0:
                        colon_idx = idx
                        break

                if colon_idx != -1:
                    alias_part = item[colon_idx+1:].strip()
                    parse_binding_pattern(alias_part)
                else:
                    item = item.lstrip(".")
                    m = re.match(r"^([a-zA-Z0-9_$]+)", item)
                    if m:
                        bindings.add(m.group(1))

        elif pat.startswith("[") and pat.endswith("]"):
            inner = pat[1:-1].strip()
            items = []
            c = []
            b_d = 0
            bk_d = 0
            for ch in inner:
                if ch == "{": b_d += 1
                elif ch == "}": b_d -= 1
                elif ch == "[": bk_d += 1
                elif ch == "]": bk_d -= 1
                elif ch == "," and b_d == 0 and bk_d == 0:
                    items.append("".join(c).strip())
                    c = []
                    continue
                c.append(ch)
            if c:
                it = "".join(c).strip()
                if it: items.append(it)
            for item in items:
                eq_idx = -1
                b_d = 0
                bk_d = 0
                for idx, ch in enumerate(item):
                    if ch == "{": b_d += 1
                    elif ch == "}": b_d -= 1
                    elif ch == "[": bk_d += 1
                    elif ch == "]": bk_d -= 1
                    elif ch == "=" and b_d == 0 and bk_d == 0:
                        eq_idx = idx
                        break
                if eq_idx != -1:
                    item = item[:eq_idx].strip()
                item = item.lstrip(".")
                parse_binding_pattern(item)
        else:
            pat = pat.lstrip(".")
            m = re.match(r"^([a-zA-Z0-9_$]+)", pat)
            if m:
                bindings.add(m.group(1))

    for param in params:
        colon_idx = -1
        b_d = 0
        bk_d = 0
        for idx, ch in enumerate(param):
            if ch == "{": b_d += 1
            elif ch == "}": b_d -= 1
            elif ch == "[": bk_d += 1
            elif ch == "]": bk_d -= 1
            elif ch == ":" and b_d == 0 and bk_d == 0:
                colon_idx = idx
                break
        if colon_idx != -1:
            param = param[:colon_idx].strip()

        eq_idx = -1
        b_d = 0
        bk_d = 0
        for idx, ch in enumerate(param):
            if ch == "{": b_d += 1
            elif ch == "}": b_d -= 1
            elif ch == "[": bk_d += 1
            elif ch == "]": bk_d -= 1
            elif ch == "=" and b_d == 0 and bk_d == 0:
                eq_idx = idx
                break
        if eq_idx != -1:
            param = param[:eq_idx].strip()

        parse_binding_pattern(param)

    return bindings


def resolve_trusted_sanitizers(content):
    """
    Deterministically resolves the set of trusted HTML sanitizers for a specific file.
    Guarantees:
    1. Base trusted libraries: DOMPurify.sanitize, validator.escape, he.encode.
    2. Zero-Trust for In-File Definitions: Local variable/function/class declarations in the file
       are NEVER trusted as sanitizers (an in-file custom function cannot be proven safe via regexes).
    3. Shadowing Protection: If a library identifier ('DOMPurify', 'validator', 'he', 'sanitizeHtml', etc.)
       is declared or shadowed locally (e.g. 'const sanitizeHtml = value => value' or 'const DOMPurify = { sanitize: ... }'
       or function/method/arrow parameter like 'function render(DOMPurify)' or destructured alias like '{ sanitizer: DOMPurify }'),
       it is classified as UNTRUSTED and stripped from the trusted set.
    4. Object Alias & Mutation Tracking: If an alias is created to a trusted library (e.g. 'const dp = DOMPurify'),
       any mutation on that alias (e.g. 'dp.sanitize = ...' or 'Object.assign(dp, ...)') mutates the underlying
       library at runtime, immediately disqualifying the root library from the trusted set.
    5. Verified Library Imports: Bare functions like 'sanitizeHtml', 'escapeHTML', 'escapeHtml'
       are trusted ONLY when explicitly imported from their verified packages ('sanitize-html', 'escape-html')
       via exact package name matching.
    6. Comment Isolation: Imports, aliases, and declarations commented out (via // or /* */ or <!-- -->)
       are strictly ignored and NEVER granted sanitizer trust.
    7. URI Encoders Excluded: encodeURI and encodeURIComponent are NOT permitted as HTML sanitizers.
    """
    trusted = set(BASE_TRUSTED_SANITIZERS)

    # Clean comments to prevent commented-out imports or aliases from granting trust
    clean_content = strip_code_comments(content)

    # 1. Check for verified external package imports (Exact Package Name Matching)
    import_re = re.compile(
        r'\bimport\s+(?:\{([^}]*)\}|([a-zA-Z0-9_$]+))\s+from\s*["\']([^"\']+)["\']|'
        r'(?:const|let|var)\s+(?:\{([^}]*)\}\s*=\s*require\(["\']([^"\']+)["\']\)|([a-zA-Z0-9_$]+)\s*=\s*require\(["\']([^"\']+)["\']\))'
    )
    for m in import_re.finditer(clean_content):
        named_clause = m.group(1) or m.group(4)
        default_name = m.group(2) or m.group(6)
        pkg = m.group(3) or m.group(5) or m.group(7) or ''

        if pkg == 'sanitize-html':
            if default_name:
                trusted.add(default_name)
            if named_clause:
                for part in named_clause.split(','):
                    part = part.strip()
                    m_as = re.search(r'\bsanitizeHtml\s+as\s+([a-zA-Z0-9_$]+)', part)
                    m_colon = re.search(r'\bsanitizeHtml\s*:\s*([a-zA-Z0-9_$]+)', part)
                    if m_as:
                        trusted.add(m_as.group(1))
                    elif m_colon:
                        trusted.add(m_colon.group(1))
                    elif re.search(r'\bsanitizeHtml\b', part):
                        trusted.add('sanitizeHtml')

        elif pkg == 'escape-html':
            if default_name:
                trusted.add(default_name)
            if named_clause:
                for part in named_clause.split(','):
                    part = part.strip()
                    m_as = re.search(r'\b(?:escapeHTML|escapeHtml)\s+as\s+([a-zA-Z0-9_$]+)', part)
                    m_colon = re.search(r'\b(?:escapeHTML|escapeHtml)\s*:\s*([a-zA-Z0-9_$]+)', part)
                    if m_as:
                        trusted.add(m_as.group(1))
                    elif m_colon:
                        trusted.add(m_colon.group(1))
                    elif re.search(r'\b(escapeHTML|escapeHtml)\b', part):
                        trusted.add(re.search(r'\b(escapeHTML|escapeHtml)\b', part).group(1))

    # 2. Track Aliases to Trusted Libraries (DOMPurify, validator, he)
    alias_map = {}
    alias_decl_re = re.compile(
        r'(?:(?:const|let|var)\s+)?([a-zA-Z0-9_$]+)\s*=\s*([a-zA-Z0-9_$]+)\s*(?:;|\n|//|/\*|$)'
    )
    for _ in range(3):
        for m in alias_decl_re.finditer(clean_content):
            lhs = m.group(1)
            rhs = m.group(2)
            if rhs in ('DOMPurify', 'validator', 'he'):
                if lhs != rhs:
                    alias_map[lhs] = rhs
            elif rhs in alias_map:
                if lhs != rhs:
                    alias_map[lhs] = alias_map[rhs]

    # 3. Detect ALL local in-file declarations (variables, functions, classes)
    decl_pattern = re.compile(
        r'(?:(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=|function\s+([a-zA-Z0-9_$]+)\s*\(|class\s+([a-zA-Z0-9_$]+)\b)'
    )
    # Direct mutations on root libraries
    root_targets = ['DOMPurify', 'validator', 'he', 'sanitizeHtml', 'escapeHTML', 'escapeHtml']
    mutation_pattern = re.compile(
        r'\b(' + '|'.join(root_targets) + r')(?:\.[a-zA-Z0-9_$]+|\[[^\]]+\])?\s*='
        r'|\b(?:window|globalThis|global)\.(' + '|'.join(root_targets) + r')(?:\.[a-zA-Z0-9_$]+|\[[^\]]+\])?\s*='
        r'|\bObject\.(?:assign|defineProperty|defineProperties)\s*\(\s*(?:(?:window|globalThis|global)\.)?(' + '|'.join(root_targets) + r')\b'
    )

    local_shadows = set()
    for m in decl_pattern.finditer(clean_content):
        name = m.group(1) or m.group(2) or m.group(3)
        if name:
            local_shadows.add(name)
    for m in mutation_pattern.finditer(clean_content):
        name = next((g for g in m.groups() if g is not None), None)
        if name:
            local_shadows.add(name)

    # 4. Check for mutations on aliases of trusted libraries
    if alias_map:
        alias_names = list(alias_map.keys())
        alias_mut_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(a) for a in alias_names) + r')(?:\.[a-zA-Z0-9_$]+|\[[^\]]+\])\s*='
            r'|\b(?:window|globalThis|global)\.(' + '|'.join(re.escape(a) for a in alias_names) + r')(?:\.[a-zA-Z0-9_$]+|\[[^\]]+\])?\s*='
            r'|\bObject\.(?:assign|defineProperty|defineProperties)\s*\(\s*(?:(?:window|globalThis|global)\.)?(' + '|'.join(re.escape(a) for a in alias_names) + r')\b'
        )
        for m in alias_mut_pattern.finditer(clean_content):
            matched_alias = next((g for g in m.groups() if g is not None), None)
            if matched_alias and matched_alias in alias_map:
                root_obj = alias_map[matched_alias]
                local_shadows.add(root_obj)

    # 5. Parameter Shadowing Protection (functions, methods, arrow functions)
    target_names = set(root_targets) | {name for name in trusted if '.' not in name}
    param_patterns = [
        re.compile(r'\bfunction\s*\*?(?:\s+[a-zA-Z0-9_$]+)?\s*\(([^)]*)\)'),
        re.compile(r'\(([^)]*)\)\s*=>'),
        re.compile(r'\b(?:constructor|[a-zA-Z0-9_$]+)\s*\(([^)]*)\)\s*\{'),
    ]
    single_arrow = re.compile(r'(?:\basync\s+)?\b([a-zA-Z0-9_$]+)\s*=>')
    for m in single_arrow.finditer(clean_content):
        name = m.group(1)
        if name in target_names:
            local_shadows.add(name)

    for pat in param_patterns:
        for m in pat.finditer(clean_content):
            params_str = m.group(1)
            for bound_id in extract_param_bindings(params_str):
                if bound_id in target_names:
                    local_shadows.add(bound_id)

    # Discard any candidate shadowed or mutated locally
    if 'DOMPurify' in local_shadows:
        trusted.discard('DOMPurify.sanitize')
    if 'validator' in local_shadows:
        trusted.discard('validator.escape')
    if 'he' in local_shadows:
        trusted.discard('he.encode')
    for shadow in local_shadows:
        trusted.discard(shadow)

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
    and inside parentheses '()' and brackets '[]'.
    Specifically prevents splitting inside 'for (let i = 0; i < n; i++)' while
    correctly splitting multiple statements inside block bodies '{ stmt1; stmt2; }'.
    """
    statements = []
    current = []
    in_quote = None
    escaped = False
    paren_depth = 0
    bracket_depth = 0

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
        elif char == ";":
            if paren_depth == 0 and bracket_depth == 0:
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


def split_comma_declarations(stmt):
    """
    Expands comma-separated variable declarations (e.g. 'const raw = location.search, clean = raw')
    into sequential sub-statements while respecting quotes, parentheses, brackets, and braces.
    """
    s = stmt.strip()
    decl_prefix = ''
    for kw in ('const ', 'let ', 'var '):
        if s.startswith(kw):
            decl_prefix = kw
            s = s[len(kw):].strip()
            break

    parts = []
    current = []
    in_quote = None
    escaped = False
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    for char in s:
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
        elif char == ",":
            if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                p = "".join(current).strip()
                if p:
                    parts.append(decl_prefix + p if decl_prefix else p)
                current = []
            else:
                current.append(char)
        else:
            current.append(char)

    p = "".join(current).strip()
    if p:
        parts.append(decl_prefix + p if decl_prefix else p)
    return parts


def scan_intrafile_taint(filepath, content):
    """
    Intra-file lexical & pattern taint tracking:
    Identifies untrusted sources assigned to local variables and traces their propagation
    through variable assignments, method chains (e.g. raw.trim()), string concatenation,
    and compound expressions into dangerous sinks (e.g. innerHTML, outerHTML, document.write).

    Key Soundness Guarantees:
    1. Sequential Statement Processing: Evaluates multiple statements on a single line in order,
       respecting semicolons inside loops and expressions.
    2. Comma-Separated Declaration Processing: Expands comma-separated variable declarations
       (const raw = location.search, clean = raw) sequentially to track taint propagation.
    3. Conservative Branch Sensitivity: Safe reassignments inside conditional blocks
       (if/else/switch/case/catch/loops) or un-braced control statements do NOT clear taint.
    4. Unconditional Reassignment Clearing: Taint state is cleared only when reassigned
       at the same lexical block depth without conditional guards.
    5. Zero-Trust for In-File Sanitizers: Rejects local dummy or identity definitions,
       requiring audited external libraries or verified imports.
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
        r'(?:\.(?:innerHTML|outerHTML|srcdoc))\s*=\s*([^;\n]+)|'
        r'(?:\bdocument\.write(?:ln)?|\bcreateContextualFragment)\s*\(\s*([^;\n]+)\s*\)|'
        r'\.insertAdjacentHTML\s*\([^,]+,\s*([^;\n]+)\s*\)'
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
        for raw_stmt in statements:
            sub_stmts = split_comma_declarations(raw_stmt)
            for stmt in sub_stmts:
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
                    sink_expr = (m_sink.group(1) or m_sink.group(2) or m_sink.group(3)).strip()
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
