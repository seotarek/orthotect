#!/usr/bin/env python3
"""
Orthotect Context Architecture & Token Optimizer Core
Zero-dependency, deterministic context analysis, density profiling,
semantic chunking, and progressive skeleton generation for AI coding agents.

LIMITATIONS NOTICE:
Lexical scanning and structural fallbacks in this module are lightweight heuristic
approximations designed to run deterministically with zero runtime dependencies.
They do not implement a full AST parser for ECMAScript/TypeScript or Python grammar.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

# Common directories to exclude from scanning and skeleton generation
DEFAULT_IGNORE_DIRS = {
    'node_modules', '.git', 'dist', 'build', '__pycache__', '.claude',
    'tmp', '.venv', 'venv', 'coverage', '.tempmediaStorage', '.system_generated'
}

DEFAULT_SUPPORTED_EXTENSIONS = {
    '.js', '.jsx', '.ts', '.tsx', '.py', '.html', '.htm',
    '.css', '.scss', '.less', '.json', '.md'
}

def estimate_tokens(text: str) -> int:
    """
    Zero-dependency heuristic token estimator.
    Provides a deterministic, lightweight approximation for source code and structured text (~3.7-3.8 chars/token).
    NOTE: This is a heuristic estimate, not an exact vendor tokenizer (e.g. OpenAI tiktoken / Google Gemini).
    """
    if not text:
        return 0

    words = text.split()
    token_count = 0

    for word in words:
        w_len = len(word)
        if w_len <= 3:
            token_count += 1
        elif w_len <= 8:
            splits = len(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+|\W+', word))
            token_count += max(1, splits)
        else:
            token_count += max(1, int(w_len / 3.7 + 0.5))

    newline_count = text.count('\n')
    token_count += int(newline_count * 0.5)

    return max(1, token_count) if text.strip() else 0


def _is_regex_start(text: str, slash_idx: int) -> bool:
    """
    Best-effort lexical disambiguation for JS/TS `/` token:
    returns True when `/` is likely a regex literal start and False for division.
    """
    j = slash_idx - 1
    while j >= 0 and text[j] in ' \t\r\n':
        j -= 1
    if j < 0:
        return True

    prev_ch = text[j]
    if prev_ch in '=(,{[;:!&|?~^+-*<>%':
        return True
    if prev_ch == ')':
        depth = 1
        k = j - 1
        while k >= 0 and depth > 0:
            if text[k] == ')':
                depth += 1
            elif text[k] == '(':
                depth -= 1
            k -= 1
        if depth == 0:
            w = k
            while w >= 0 and text[w] in ' \t\r\n':
                w -= 1
            word_end = w
            while w >= 0 and (text[w].isalnum() or text[w] in '_$'):
                w -= 1
            kw = text[w + 1:word_end + 1]
            return kw in ('if', 'while', 'for', 'with', 'catch')
        return False

    k = j
    while k >= 0 and (text[k].isalnum() or text[k] in '_$'):
        k -= 1
    word = text[k + 1:j + 1]
    return word in ('return', 'case', 'typeof', 'delete', 'void', 'throw', 'yield', 'await', 'default')


def mask_js_code(text: str) -> str:
    """
    Mask non-code regions in JavaScript / TypeScript source code:
    replaces comments (// and /* */), single/double-quoted strings, regex literals,
    and template literal text (outside of ${...}) with space characters,
    preserving exact newline characters and character offsets.
    Expressions inside ${...} remain unmasked executable code.
    """
    result = []
    i = 0
    n = len(text)
    stack = []
    in_regex_class = False

    while i < n:
        ch = text[i]
        top = stack[-1] if stack else None

        if top == 'LINE_COMMENT':
            if ch == '\n':
                stack.pop()
                result.append('\n')
            else:
                result.append(' ')
            i += 1
            continue

        if top == 'BLOCK_COMMENT':
            if ch == '*' and i + 1 < n and text[i + 1] == '/':
                stack.pop()
                result.append('  ')
                i += 2
            elif ch == '\n':
                result.append('\n')
                i += 1
            else:
                result.append(' ')
                i += 1
            continue

        if top in ('SINGLE_QUOTE', 'DOUBLE_QUOTE'):
            quote = "'" if top == 'SINGLE_QUOTE' else '"'
            if ch == '\\' and i + 1 < n:
                result.append('  ' if text[i + 1] != '\n' else ' \n')
                i += 2
            elif ch == quote:
                stack.pop()
                result.append(' ')
                i += 1
            elif ch == '\n':
                result.append('\n')
                i += 1
            else:
                result.append(' ')
                i += 1
            continue

        if top == 'TEMPLATE':
            if ch == '\\' and i + 1 < n:
                result.append('  ' if text[i + 1] != '\n' else ' \n')
                i += 2
            elif ch == '$' and i + 1 < n and text[i + 1] == '{':
                stack.append(['TEMPLATE_EXPR', 1])
                result.append('  ')
                i += 2
            elif ch == '`':
                stack.pop()
                result.append(' ')
                i += 1
            elif ch == '\n':
                result.append('\n')
                i += 1
            else:
                result.append(' ')
                i += 1
            continue

        if top == 'REGEX':
            if ch == '\\' and i + 1 < n:
                result.append('  ' if text[i + 1] != '\n' else ' \n')
                i += 2
            elif ch == '[' and not in_regex_class:
                in_regex_class = True
                result.append(' ')
                i += 1
            elif ch == ']' and in_regex_class:
                in_regex_class = False
                result.append(' ')
                i += 1
            elif ch == '/' and not in_regex_class:
                stack.pop()
                result.append(' ')
                i += 1
                while i < n and text[i].isalpha():
                    result.append(' ')
                    i += 1
            elif ch == '\n':
                stack.pop()
                result.append('\n')
                i += 1
            else:
                result.append(' ')
                i += 1
            continue

        # In executable code (either root or inside TEMPLATE_EXPR)
        in_expr = bool(top and isinstance(top, list) and top[0] == 'TEMPLATE_EXPR')

        if ch == '/' and i + 1 < n and text[i + 1] == '/':
            stack.append('LINE_COMMENT')
            result.append('  ')
            i += 2
            continue
        if ch == '/' and i + 1 < n and text[i + 1] == '*':
            stack.append('BLOCK_COMMENT')
            result.append('  ')
            i += 2
            continue
        if ch == "'":
            stack.append('SINGLE_QUOTE')
            result.append(' ')
            i += 1
            continue
        if ch == '"':
            stack.append('DOUBLE_QUOTE')
            result.append(' ')
            i += 1
            continue
        if ch == '`':
            stack.append('TEMPLATE')
            result.append(' ')
            i += 1
            continue
        if ch == '/' and i + 1 < n and text[i + 1] not in ('/', '*') and _is_regex_start(text, i):
            stack.append('REGEX')
            in_regex_class = False
            result.append(' ')
            i += 1
            continue

        if in_expr:
            if ch == '{':
                top[1] += 1
            elif ch == '}':
                top[1] -= 1
                if top[1] == 0:
                    stack.pop()
                    result.append(' ')
                    i += 1
                    continue

        result.append(ch)
        i += 1

    return ''.join(result)


def _compute_python_indent(line: str) -> int:
    """Compute Python indentation depth with tabs normalized to 8-column stops."""
    expanded = line.expandtabs(8)
    return len(expanded) - len(expanded.lstrip(' '))


def _build_scope_path(symbol: dict, symbol_by_id: dict) -> list:
    """Construct hierarchical scope path (e.g. ['class Controller', 'method render'])."""
    path = []
    current = symbol
    visited = set()
    while current and current.get('id') not in visited:
        visited.add(current['id'])
        label = f"{current.get('type', 'scope')} {current['name']}"
        path.append(label)
        parent_id = current.get('parent_id')
        current = symbol_by_id.get(parent_id) if parent_id else None
    return list(reversed(path))


def _split_oversized_range_by_lines(lines: list, range_start: int, range_end: int, max_tokens: int) -> list:
    """
    Deterministic structural fallback for a single oversized declaration range.
    Splits by line windows sized by local token density.
    """
    text = "\n".join(lines[range_start - 1:range_end])
    tokens = estimate_tokens(text)
    total_lines = max(1, range_end - range_start + 1)
    tokens_per_line = max(1.0, tokens / total_lines)
    window_lines = max(20, int(max_tokens / tokens_per_line))

    spans = []
    cursor = range_start
    while cursor <= range_end:
        end_line = min(range_end, cursor + window_lines - 1)
        spans.append((cursor, end_line, 'line_window'))
        cursor = end_line + 1
    return spans


def extract_symbols(content: str, ext: str) -> list:
    """
    Extract major architectural symbols (classes, functions, methods, components, selectors)
    with their starting line numbers, lexical nesting depth, and parent scopes.
    Uses reliable unique IDs and scope references to prevent name collisions.
    """
    symbols = []
    lines = content.splitlines()

    # JavaScript / TypeScript / JSX
    if ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs'):
        masked = mask_js_code(content)
        lines_masked = masked.splitlines()
        scope_stack = []
        brace_depth = 0

        class_pat = re.compile(r'(?<![\w$])(?:export\s+(?:default\s+)?)?class\s+([A-Za-z0-9_$]+)')
        func_pat = re.compile(r'(?<![\w$])(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(')
        arrow_pat = re.compile(r'(?<![\w$])(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_$]+)\s*=>')
        method_pat = re.compile(r'^(?:(?:async|get|set|static)\s+)*([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{?')

        for idx, (l_orig, l_mask) in enumerate(zip(lines, lines_masked), 1):
            cur_depth = brace_depth

            while scope_stack and scope_stack[-1]['open_brace_depth'] > cur_depth:
                scope_stack.pop()

            decls = []
            for m in class_pat.finditer(l_mask):
                decls.append((m.start(), 'class', m.group(1)))
            for m in func_pat.finditer(l_mask):
                decls.append((m.start(), 'function', m.group(1)))
            for m in arrow_pat.finditer(l_mask):
                decls.append((m.start(), 'function', m.group(1)))

            if scope_stack and scope_stack[-1]['type'] == 'class':
                stripped_mask = l_mask.strip()
                m_meth = method_pat.match(stripped_mask)
                if m_meth and m_meth.group(1) not in ('if', 'while', 'for', 'switch', 'catch'):
                    meth_name = m_meth.group(1)
                    m_start = l_mask.find(meth_name)
                    decls.append((m_start, 'method', meth_name))

            decls.sort(key=lambda d: d[0])

            for char_pos, ch in enumerate(l_mask):
                for d_pos, d_type, d_name in decls:
                    if d_pos == char_pos:
                        parent_sym = scope_stack[-1] if scope_stack else None
                        sym_id = f"{d_type}_{d_name}_L{idx}_C{char_pos + 1}"
                        sym_dict = {
                            'id': sym_id,
                            'line': idx,
                            'col': char_pos + 1,
                            'type': d_type,
                            'name': d_name,
                            'is_top_level': (cur_depth == 0),
                            'parent': parent_sym['name'] if parent_sym else None,
                            'parent_id': parent_sym['id'] if parent_sym else None,
                            'depth': cur_depth
                        }
                        symbols.append(sym_dict)
                        if d_type in ('class', 'function', 'method'):
                            scope_stack.append({
                                'id': sym_id,
                                'name': d_name,
                                'type': d_type,
                                'open_brace_depth': cur_depth + 1
                            })

                if ch == '{':
                    brace_depth += 1
                    cur_depth += 1
                elif ch == '}':
                    brace_depth = max(0, brace_depth - 1)
                    cur_depth = max(0, cur_depth - 1)
                    while scope_stack and scope_stack[-1]['open_brace_depth'] > brace_depth:
                        scope_stack.pop()

    # Python
    elif ext == '.py':
        scope_stack = []
        pending_decorators = []
        decorator_start_line = None
        in_multiline_decorator = False
        paren_depth = 0

        class_pat = re.compile(r'^class\s+([A-Za-z0-9_]+)')
        func_pat = re.compile(r'^(?:async\s+)?def\s+([A-Za-z0-9_]+)\s*\(')

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            indent = _compute_python_indent(line)

            if in_multiline_decorator:
                paren_depth += line.count('(') - line.count(')')
                pending_decorators.append(stripped)
                if paren_depth <= 0:
                    in_multiline_decorator = False
                continue

            if stripped.startswith('@'):
                if not pending_decorators:
                    decorator_start_line = idx
                pending_decorators.append(stripped)
                paren_depth = line.count('(') - line.count(')')
                if paren_depth > 0:
                    in_multiline_decorator = True
                continue

            while scope_stack and scope_stack[-1]['indent'] >= indent:
                scope_stack.pop()

            m_class = class_pat.match(stripped)
            if m_class:
                c_name = m_class.group(1)
                parent = scope_stack[-1] if scope_stack else None
                start_l = decorator_start_line if pending_decorators else idx
                sym_id = f"class_{c_name}_L{start_l}"
                symbols.append({
                    'id': sym_id,
                    'line': start_l,
                    'def_line': idx,
                    'type': 'class',
                    'name': c_name,
                    'is_top_level': (len(scope_stack) == 0),
                    'parent': parent['name'] if parent else None,
                    'parent_id': parent['id'] if parent else None,
                    'depth': len(scope_stack),
                    'indent': indent,
                    'decorators': list(pending_decorators)
                })
                scope_stack.append({'id': sym_id, 'type': 'class', 'name': c_name, 'indent': indent})
                pending_decorators = []
                decorator_start_line = None
                continue

            m_func = func_pat.match(stripped)
            if m_func:
                f_name = m_func.group(1)
                parent = scope_stack[-1] if scope_stack else None
                stype = 'method' if (parent and parent['type'] == 'class') else 'function'
                start_l = decorator_start_line if pending_decorators else idx
                sym_id = f"{stype}_{f_name}_L{start_l}"
                symbols.append({
                    'id': sym_id,
                    'line': start_l,
                    'def_line': idx,
                    'type': stype,
                    'name': f_name,
                    'is_top_level': (len(scope_stack) == 0),
                    'parent': parent['name'] if parent else None,
                    'parent_id': parent['id'] if parent else None,
                    'depth': len(scope_stack),
                    'indent': indent,
                    'decorators': list(pending_decorators)
                })
                scope_stack.append({'id': sym_id, 'type': stype, 'name': f_name, 'indent': indent})
                pending_decorators = []
                decorator_start_line = None
                continue

            pending_decorators = []
            decorator_start_line = None

    # CSS / SCSS
    elif ext in ('.css', '.scss', '.less'):
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            m = re.match(r'^(\.[A-Za-z0-9_-]+|#[A-Za-z0-9_-]+|:[a-zA-Z-]+)\s*\{', stripped)
            if m:
                s_name = m.group(1)
                sym_id = f"selector_{s_name}_L{idx}"
                symbols.append({
                    'id': sym_id,
                    'line': idx,
                    'type': 'selector',
                    'name': s_name,
                    'is_top_level': True,
                    'parent': None,
                    'parent_id': None,
                    'depth': 0
                })

    return symbols


def analyze_file_density(filepath_or_content: str, is_content: bool = False, ext: str = '.js') -> dict:
    """
    Profile file size, token density, symbol distribution, and surgical read recommendations.
    """
    if is_content:
        content = filepath_or_content
        filename = f"inline{ext}"
    else:
        path = Path(filepath_or_content)
        filename = path.name
        ext = path.suffix.lower()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath_or_content}")
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

    lines = content.splitlines()
    total_lines = len(lines)
    total_chars = len(content)
    tokens = estimate_tokens(content)
    symbols = extract_symbols(content, ext)

    tokens_per_line = round(tokens / total_lines, 2) if total_lines > 0 else 0
    chars_per_token = round(total_chars / tokens, 2) if tokens > 0 else 0

    if tokens <= 350:
        recommendation = "SAFE_SINGLE_TURN_READ"
        rationale = "Small footprint; safe to read in full."
    elif tokens <= 1200:
        recommendation = "TARGETED_SLICES_PREFERRED"
        rationale = "Moderate size; reading specific 50-80 line ranges saves tokens."
    else:
        recommendation = "CHUNK_OR_SKELETON_REQUIRED"
        rationale = "Large file; full read risks context pollution. Use semantic chunking or symbol skeleton."

    return {
        'file': filename,
        'extension': ext,
        'lines': total_lines,
        'characters': total_chars,
        'estimated_tokens': tokens,
        'tokens_per_line': tokens_per_line,
        'chars_per_token': chars_per_token,
        'symbol_count': len(symbols),
        'symbols': symbols[:15],
        'recommendation': recommendation,
        'rationale': rationale
    }


def semantic_chunk(filepath_or_content: str, max_tokens: int = 500, is_content: bool = False, ext: str = '.js') -> list:
    """
    Semantically partition content into deterministic chunks.

    Guarantees:
    - Preambles, top-level declarations, and compound structures are kept intact whenever possible.
    - Preserves scope context via reliable parent IDs, context paths, and continuation breadcrumbs.
    - When declarations exceed token budgets, partitions cleanly along nested declaration boundaries
      or line windows, tagging oversized declarations with explicit metadata.

    Limitations:
    - JavaScript/TypeScript parsing is lexical and best-effort rather than full grammar AST.
    """
    if is_content:
        content = filepath_or_content
        filename = f"inline{ext}"
    else:
        path = Path(filepath_or_content)
        filename = path.name
        ext = path.suffix.lower()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath_or_content}")
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return []

    comment_prefix = '#' if ext == '.py' else '//'
    chunks = []
    symbols = extract_symbols(content, ext)
    symbols_sorted = sorted(symbols, key=lambda s: (s.get('line', 0), s.get('depth', 0)))
    symbol_by_id = {s['id']: s for s in symbols_sorted if s.get('id')}

    top_level_symbols = [s for s in symbols_sorted if s.get('is_top_level')]
    top_level_symbols.sort(key=lambda s: s['line'])

    ranges = []
    if top_level_symbols:
        first_start = top_level_symbols[0]['line']
        if first_start > 1:
            ranges.append({'start': 1, 'end': first_start - 1, 'symbol': None, 'strategy': 'preamble'})

        for i, sym in enumerate(top_level_symbols):
            start = sym['line']
            end = (top_level_symbols[i + 1]['line'] - 1) if i + 1 < len(top_level_symbols) else total_lines
            ranges.append({'start': start, 'end': end, 'symbol': sym, 'strategy': 'top_level'})
    else:
        ranges.append({'start': 1, 'end': total_lines, 'symbol': None, 'strategy': 'file_window'})

    def collect_chunk_symbols(start_line, end_line):
        return [s['name'] for s in symbols_sorted if start_line <= s['line'] <= end_line]

    def append_chunk(start_line, end_line, continuation_of=None, split_strategy='top_level', context_path=None, oversized_scope=None):
        chunk_idx = len(chunks) + 1
        raw_content = "\n".join(lines[start_line - 1:end_line])
        final_content = raw_content
        if continuation_of:
            breadcrumb = f"{comment_prefix} [Context Continuation: {continuation_of} | chunk #{chunk_idx}]\n"
            final_content = breadcrumb + raw_content
        chunk = {
            'chunk_index': chunk_idx,
            'file': filename,
            'start_line': start_line,
            'end_line': end_line,
            'lines_count': (end_line - start_line + 1),
            'estimated_tokens': estimate_tokens(final_content),
            'continuation_of': continuation_of,
            'split_strategy': split_strategy,
            'context_path': context_path or [],
            'symbols': collect_chunk_symbols(start_line, end_line),
            'content': final_content
        }
        if oversized_scope:
            chunk['oversized_scope'] = oversized_scope
        chunks.append(chunk)

    for r in ranges:
        r_start = r['start']
        r_end = r['end']
        if r_end < r_start:
            continue

        r_text = "\n".join(lines[r_start - 1:r_end])
        r_tokens = estimate_tokens(r_text)
        symbol = r['symbol']

        if r_tokens <= max_tokens:
            append_chunk(
                r_start,
                r_end,
                continuation_of=None,
                split_strategy=r['strategy'],
                context_path=_build_scope_path(symbol, symbol_by_id) if symbol else []
            )
            continue

        if not symbol:
            for sub_start, sub_end, strategy in _split_oversized_range_by_lines(lines, r_start, r_end, max_tokens):
                append_chunk(sub_start, sub_end, continuation_of='file scope', split_strategy=strategy, context_path=[])
            continue

        symbol_name = f"{symbol['type']} {symbol['name']}"
        context_path = _build_scope_path(symbol, symbol_by_id)
        child_symbols = [
            s for s in symbols_sorted
            if r_start < s['line'] <= r_end and (s.get('parent_id') == symbol.get('id') or s.get('parent') == symbol.get('name'))
        ]
        child_starts = sorted({s['line'] for s in child_symbols})

        sub_ranges = []
        if child_starts:
            cursor = r_start
            current_sym = None
            for child_start in child_starts:
                if child_start > cursor:
                    sub_ranges.append((cursor, child_start - 1, 'nested_boundary', current_sym))
                c_matches = [cs for cs in child_symbols if cs['line'] == child_start]
                current_sym = c_matches[0] if c_matches else None
                cursor = child_start
            if cursor <= r_end:
                sub_ranges.append((cursor, r_end, 'nested_boundary', current_sym))
        else:
            for s_start, s_end, s_strat in _split_oversized_range_by_lines(lines, r_start, r_end, max_tokens):
                sub_ranges.append((s_start, s_end, s_strat, None))

        oversized_meta = {
            'name': symbol.get('name'),
            'type': symbol.get('type'),
            'start_line': r_start,
            'end_line': r_end
        }

        for idx_sub, (sub_start, sub_end, strategy, sub_sym) in enumerate(sub_ranges):
            sub_text = "\n".join(lines[sub_start - 1:sub_end])
            sub_tokens = estimate_tokens(sub_text)

            if sub_tokens > max_tokens and strategy != 'line_window':
                finer = _split_oversized_range_by_lines(lines, sub_start, sub_end, max_tokens)
                for j, (f_start, f_end, f_strategy) in enumerate(finer):
                    continuation = None if (idx_sub == 0 and j == 0 and f_start == r_start) else symbol_name
                    append_chunk(
                        f_start, f_end,
                        continuation_of=continuation,
                        split_strategy=f_strategy,
                        context_path=context_path,
                        oversized_scope=oversized_meta
                    )
            else:
                continuation = None if (idx_sub == 0 and sub_start == r_start) else symbol_name
                append_chunk(
                    sub_start, sub_end,
                    continuation_of=continuation,
                    split_strategy=strategy,
                    context_path=context_path,
                    oversized_scope=oversized_meta
                )

    return chunks


def generate_context_skeleton(root_dir: str, max_depth: int = 3, ignore_dirs: set = None) -> dict:
    """
    Generate an architectural skeleton of files and their major symbols.

    Depth semantics:
    - Root directory depth is 0
    - Direct children are depth 1
    - When current directory depth >= max_depth, traversal is pruned by clearing `dirs[:]` in-place
      before `os.walk` descends further.
    """
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS

    root_path = Path(root_dir).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")

    skeleton = {
        'root': str(root_path),
        'files': [],
        'total_files': 0,
        'total_estimated_tokens': 0,
        'skeleton_tokens': 0
    }

    full_text_buffer = []

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]

        rel_dir = os.path.relpath(root, root_path)
        depth = 0 if rel_dir == '.' else len(rel_dir.split(os.sep))
        if depth >= max_depth:
            dirs[:] = []
            if depth > max_depth:
                continue

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in DEFAULT_SUPPORTED_EXTENSIONS:
                file_path = Path(root) / f
                rel_path = str(file_path.relative_to(root_path))
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                        content = fp.read()
                    file_tokens = estimate_tokens(content)
                    symbols = extract_symbols(content, ext)

                    file_summary = {
                        'path': rel_path,
                        'lines': len(content.splitlines()),
                        'tokens': file_tokens,
                        'symbols': [f"{s['type']} {s['name']} (L{s['line']})" for s in symbols]
                    }
                    skeleton['files'].append(file_summary)
                    skeleton['total_files'] += 1
                    skeleton['total_estimated_tokens'] += file_tokens

                    sym_repr = f" [{', '.join(file_summary['symbols'][:5])}]" if file_summary['symbols'] else ""
                    full_text_buffer.append(f"{rel_path} ({file_summary['lines']} lines, ~{file_tokens} tokens){sym_repr}")
                except Exception:
                    continue

    skeleton_text = "\n".join(full_text_buffer)
    skeleton['formatted_view'] = skeleton_text
    skeleton['skeleton_tokens'] = estimate_tokens(skeleton_text)
    skeleton['compression_ratio'] = (
        round(1.0 - (skeleton['skeleton_tokens'] / max(1, skeleton['total_estimated_tokens'])), 4)
        if skeleton['total_estimated_tokens'] > 0 else 0.0
    )

    return skeleton


def main():
    parser = argparse.ArgumentParser(description="Orthotect Context Architecture & Token Optimizer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available context commands")

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Profile file density and token consumption")
    inspect_parser.add_argument("path", help="Target file path")
    inspect_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Chunk command
    chunk_parser = subparsers.add_parser("chunk", help="Semantically chunk a file for AI agent consumption")
    chunk_parser.add_argument("path", help="Target file path")
    chunk_parser.add_argument("--max-tokens", type=int, default=500, help="Max tokens per semantic chunk (default: 500)")
    chunk_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Skeleton command
    skel_parser = subparsers.add_parser("skeleton", help="Generate progressive codebase skeleton")
    skel_parser.add_argument("path", nargs="?", default=".", help="Root directory (default: .)")
    skel_parser.add_argument("--depth", type=int, default=3, help="Max directory depth (default: 3)")
    skel_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if args.command == "inspect":
        res = analyze_file_density(args.path)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"File: {res['file']} ({res['lines']} lines, {res['characters']} chars)")
            print(f"Estimated Tokens: {res['estimated_tokens']} (~{res['tokens_per_line']} tokens/line)")
            print(f"Recommendation: [{res['recommendation']}] - {res['rationale']}")
            print(f"Identified Symbols ({res['symbol_count']}):")
            for s in res['symbols']:
                parent_info = f" (in {s['parent']})" if s['parent'] else ""
                print(f"  - {s['type']} {s['name']} (L{s['line']}){parent_info}")

    elif args.command == "chunk":
        chunks = semantic_chunk(args.path, max_tokens=args.max_tokens)
        if args.json:
            print(json.dumps(chunks, indent=2))
        else:
            print(f"Semantic Chunking Summary: {len(chunks)} chunks produced for {args.path}")
            for c in chunks:
                cont = f" [Continuation of {c['continuation_of']}]" if c.get('continuation_of') else ""
                print(f"  Chunk #{c['chunk_index']}: Lines {c['start_line']}..{c['end_line']} ({c['estimated_tokens']} tokens){cont}")

    elif args.command == "skeleton":
        skel = generate_context_skeleton(args.path, max_depth=args.depth)
        if args.json:
            print(json.dumps(skel, indent=2))
        else:
            print(f"Progressive Architecture Skeleton ({skel['total_files']} files, ~{skel['total_estimated_tokens']} total tokens):")
            print(f"Skeleton Token Footprint: ~{skel['skeleton_tokens']} tokens")
            for f in skel['files']:
                sym_str = f" [{', '.join(f['symbols'][:4])}]" if f['symbols'] else ""
                print(f"  {f['path']} ({f['lines']} lines, ~{f['tokens']} tokens){sym_str}")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
