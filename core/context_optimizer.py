#!/usr/bin/env python3
"""
Orthotect Context Architecture & Token Optimizer Core
Zero-dependency, deterministic context analysis, AST-density profiling,
semantic chunking, and progressive skeleton generation for AI coding agents.
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
    This is a deterministic approximation for source code and structured text, not an
    exact tokenizer implementation for any vendor/model.
    """
    if not text:
        return 0

    # 1. Split on whitespace
    words = text.split()
    token_count = 0

    for word in words:
        w_len = len(word)
        if w_len <= 3:
            token_count += 1
        elif w_len <= 8:
            # Check for punctuation splits and case transitions
            splits = len(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+|\W+', word))
            token_count += max(1, splits)
        else:
            # Longer identifiers or strings: ~3.7 chars per token
            token_count += max(1, int(w_len / 3.7 + 0.5))

    # Add tokens for newlines and leading indentation (common in structured code)
    newline_count = text.count('\n')
    token_count += int(newline_count * 0.5)

    return max(1, token_count) if text.strip() else 0

def _js_is_regex_start(text: str, slash_idx: int) -> bool:
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


def _scan_js_line_for_brace_depth(line: str, full_text: str, absolute_index: int, state: dict) -> tuple[int, int]:
    """
    Scan one JS/TS line and return (open_braces, close_braces) in executable code.
    Ignores braces inside comments, strings, template literals, and regex literals.
    This is lexical (non-AST) parsing and intentionally best-effort.
    """
    open_braces = 0
    close_braces = 0
    i = 0
    n = len(line)

    while i < n:
        ch = line[i]
        abs_i = absolute_index + i

        if state['in_block_comment']:
            if ch == '*' and i + 1 < n and line[i + 1] == '/':
                state['in_block_comment'] = False
                i += 2
            else:
                i += 1
            continue

        if state['string_quote']:
            if ch == '\\' and i + 1 < n:
                i += 2
            elif ch == state['string_quote']:
                state['string_quote'] = None
                i += 1
            else:
                i += 1
            continue

        if state['in_template']:
            if ch == '\\' and i + 1 < n:
                i += 2
            elif ch == '`':
                state['in_template'] = False
                i += 1
            else:
                i += 1
            continue

        if state['in_regex']:
            if ch == '\\' and i + 1 < n:
                i += 2
            elif ch == '[' and not state['in_regex_char_class']:
                state['in_regex_char_class'] = True
                i += 1
            elif ch == ']' and state['in_regex_char_class']:
                state['in_regex_char_class'] = False
                i += 1
            elif ch == '/' and not state['in_regex_char_class']:
                state['in_regex'] = False
                i += 1
                while i < n and line[i].isalpha():
                    i += 1
            else:
                i += 1
            continue

        if ch == '/' and i + 1 < n and line[i + 1] == '/':
            break
        if ch == '/' and i + 1 < n and line[i + 1] == '*':
            state['in_block_comment'] = True
            i += 2
            continue
        if ch in ("'", '"'):
            state['string_quote'] = ch
            i += 1
            continue
        if ch == '`':
            state['in_template'] = True
            i += 1
            continue
        if ch == '/' and i + 1 < n and line[i + 1] not in ('/', '*') and _js_is_regex_start(full_text, abs_i):
            state['in_regex'] = True
            state['in_regex_char_class'] = False
            i += 1
            continue
        if ch == '{':
            open_braces += 1
        elif ch == '}':
            close_braces += 1
        i += 1

    return open_braces, close_braces


def _compute_python_indent(line: str) -> int:
    """Compute Python indentation depth with tabs normalized to 8-column stops."""
    expanded = line.expandtabs(8)
    return len(expanded) - len(expanded.lstrip(' '))


def _build_scope_path(symbol: dict, symbol_map: dict) -> list:
    path = []
    current = symbol
    visited = set()
    while current and current.get('name') and current['name'] not in visited:
        visited.add(current['name'])
        label = f"{current.get('type', 'scope')} {current['name']}"
        path.append(label)
        parent_name = current.get('parent')
        current = symbol_map.get(parent_name) if parent_name else None
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


def extract_symbols(content: str, ext: str):
    """
    Extract major architectural symbols (classes, functions, methods, components, selectors)
    with their starting line numbers, lexical nesting depth, and parent scopes.
    """
    symbols = []
    lines = content.splitlines()

    # JavaScript / TypeScript / JSX
    if ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs'):
        scope_stack = []
        brace_depth = 0
        scanner_state = {
            'in_block_comment': False,
            'string_quote': None,
            'in_template': False,
            'in_regex': False,
            'in_regex_char_class': False
        }
        full_text = content
        absolute_index = 0

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            cur_depth = brace_depth

            while scope_stack and scope_stack[-1]['open_brace_depth'] > cur_depth:
                scope_stack.pop()

            is_top = (cur_depth == 0)
            parent = scope_stack[-1]['name'] if scope_stack else None

            if stripped:
                class_pattern = r'(?<![\w$])(?:export\s+(?:default\s+)?)?class\s+([A-Za-z0-9_$]+)'
                func_pattern = r'(?<![\w$])(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\('
                arrow_pattern = r'(?<![\w$])(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_$]+)\s*=>'
                method_pattern = r'^(?:(?:async|get|set|static)\s+)*([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{?'

                for m_class in re.finditer(class_pattern, stripped):
                    c_name = m_class.group(1)
                    symbols.append({'line': idx, 'type': 'class', 'name': c_name, 'is_top_level': is_top, 'parent': parent, 'depth': cur_depth})
                    scope_stack.append({'open_brace_depth': cur_depth + 1, 'type': 'class', 'name': c_name})
                    parent = c_name
                    is_top = False

                for m_func in re.finditer(func_pattern, stripped):
                    f_name = m_func.group(1)
                    stype = 'function'
                    symbols.append({'line': idx, 'type': stype, 'name': f_name, 'is_top_level': (cur_depth == 0), 'parent': scope_stack[-1]['name'] if scope_stack else None, 'depth': cur_depth})
                    scope_stack.append({'open_brace_depth': cur_depth + 1, 'type': stype, 'name': f_name})

                for m_arrow in re.finditer(arrow_pattern, stripped):
                    a_name = m_arrow.group(1)
                    symbols.append({'line': idx, 'type': 'function', 'name': a_name, 'is_top_level': (cur_depth == 0), 'parent': scope_stack[-1]['name'] if scope_stack else None, 'depth': cur_depth})

                if scope_stack and scope_stack[-1]['type'] == 'class':
                    m_method = re.match(method_pattern, stripped)
                    if m_method and m_method.group(1) not in ('if', 'while', 'for', 'switch', 'catch'):
                        m_name = m_method.group(1)
                        symbols.append({'line': idx, 'type': 'method', 'name': m_name, 'is_top_level': False, 'parent': scope_stack[-1]['name'], 'depth': cur_depth})
                        scope_stack.append({'open_brace_depth': cur_depth + 1, 'type': 'method', 'name': m_name})

            opened, closed = _scan_js_line_for_brace_depth(line, full_text, absolute_index, scanner_state)
            brace_depth += opened
            brace_depth = max(0, brace_depth - closed)
            while scope_stack and scope_stack[-1]['open_brace_depth'] > brace_depth:
                scope_stack.pop()
            absolute_index += len(line) + 1

    # Python
    elif ext == '.py':
        scope_stack = []
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            indent = _compute_python_indent(line)
            while scope_stack and scope_stack[-1]['indent'] >= indent:
                scope_stack.pop()

            m_class = re.match(r'^class\s+([A-Za-z0-9_]+)', stripped)
            if m_class:
                c_name = m_class.group(1)
                is_top = len(scope_stack) == 0
                parent = scope_stack[-1]['name'] if scope_stack else None
                symbols.append({'line': idx, 'type': 'class', 'name': c_name, 'is_top_level': is_top, 'parent': parent, 'depth': len(scope_stack)})
                scope_stack.append({'type': 'class', 'name': c_name, 'indent': indent})
                continue

            m_func = re.match(r'^(?:async\s+)?def\s+([A-Za-z0-9_]+)\s*\(', stripped)
            if m_func:
                f_name = m_func.group(1)
                is_top = len(scope_stack) == 0
                parent = scope_stack[-1]['name'] if scope_stack else None
                stype = 'method' if (scope_stack and scope_stack[-1]['type'] == 'class') else 'function'
                symbols.append({'line': idx, 'type': stype, 'name': f_name, 'is_top_level': is_top, 'parent': parent, 'depth': len(scope_stack)})
                scope_stack.append({'type': stype, 'name': f_name, 'indent': indent})

    # CSS / SCSS
    elif ext in ('.css', '.scss', '.less'):
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            m = re.match(r'^(\.[A-Za-z0-9_-]+|#[A-Za-z0-9_-]+|:[a-zA-Z-]+)\s*\{', stripped)
            if m:
                symbols.append({'line': idx, 'type': 'selector', 'name': m.group(1), 'is_top_level': True, 'parent': None, 'depth': 0})

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

    # Derive reading recommendation based on token budget
    if tokens <= 350:
        recommendation = "SAFE_SINGLE_TURN_READ"
        rationale = "Small footprint; safe to read in full."
    elif tokens <= 1200:
        recommendation = "TARGETED_SLICES_PREFERRED"
        rationale = "Moderate size; reading specific 50-80 line ranges saves 60-80% tokens."
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
        'symbols': symbols[:15],  # top 15 symbols
        'recommendation': recommendation,
        'rationale': rationale
    }

def semantic_chunk(filepath_or_content: str, max_tokens: int = 500, is_content: bool = False, ext: str = '.js') -> list:
    """
    Semantically partition content into deterministic chunks.

    Guarantees:
    - For JS/TS/Python inputs, prefers boundaries at top-level declarations and then nested
      declarations before any line-window fallback.
    - A single oversized declaration is never silently split without metadata: every fallback
      chunk includes explicit enclosing-scope breadcrumbs and `split_strategy` metadata.

    Limits:
    - JS/TS parsing is lexical (non-AST). It is resilient to comments, strings, template
      literals, and regex literals for brace counting, but does not claim full grammar coverage.
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
    symbol_map = {s['name']: s for s in symbols_sorted if s.get('name')}

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
                context_path=_build_scope_path(symbol, symbol_map) if symbol else []
            )
            continue

        if not symbol:
            for sub_start, sub_end, strategy in _split_oversized_range_by_lines(lines, r_start, r_end, max_tokens):
                append_chunk(sub_start, sub_end, continuation_of='file scope', split_strategy=strategy, context_path=[])
            continue

        symbol_name = f"{symbol['type']} {symbol['name']}"
        context_path = _build_scope_path(symbol, symbol_map)
        child_symbols = [
            s for s in symbols_sorted
            if r_start < s['line'] <= r_end and (s.get('parent') == symbol.get('name'))
        ]
        child_starts = sorted({s['line'] for s in child_symbols})

        sub_ranges = []
        if child_starts:
            cursor = r_start
            for child_start in child_starts:
                if child_start > cursor:
                    sub_ranges.append((cursor, child_start - 1, 'nested_boundary'))
                cursor = child_start
            if cursor <= r_end:
                sub_ranges.append((cursor, r_end, 'nested_boundary'))
        else:
            sub_ranges = _split_oversized_range_by_lines(lines, r_start, r_end, max_tokens)

        oversized_meta = {
            'name': symbol.get('name'),
            'type': symbol.get('type'),
            'start_line': r_start,
            'end_line': r_end
        }

        for idx_sub, (sub_start, sub_end, strategy) in enumerate(sub_ranges):
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
    Generate an ultra-compact architectural skeleton of files and their major symbols.
    Compresses codebase context by >85% compared to raw file reading.

    Depth semantics:
    - root directory depth is 0
    - direct children are depth 1
    - when current directory depth >= max_depth, traversal is pruned by clearing `dirs[:]`
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
        # Exclude ignored directories in-place
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

                    # Add compact line to skeleton buffer
                    sym_repr = f" [{', '.join(file_summary['symbols'][:5])}]" if file_summary['symbols'] else ""
                    full_text_buffer.append(f"{rel_path} ({file_summary['lines']} lines, ~{file_tokens} tokens){sym_repr}")
                except Exception:
                    continue

    skeleton_text = "\n".join(full_text_buffer)
    skeleton['skeleton_tokens'] = estimate_tokens(skeleton_text)
    skeleton['compression_ratio'] = (
        round(1.0 - (skeleton['skeleton_tokens'] / skeleton['total_estimated_tokens']), 3)
        if skeleton['total_estimated_tokens'] > 0 else 0.0
    )
    skeleton['formatted_view'] = skeleton_text

    return skeleton

def main():
    parser = argparse.ArgumentParser(description="Orthotect Context Architecture & Token Optimizer")
    subparsers = parser.add_subparsers(dest="subcommand", help="Context optimization subcommands")

    # Inspect
    inspect_parser = subparsers.add_parser("inspect", help="Profile token density and recommendation for a file")
    inspect_parser.add_argument("path", help="Path to file")
    inspect_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Chunk
    chunk_parser = subparsers.add_parser("chunk", help="Semantically chunk a file at symbol boundaries")
    chunk_parser.add_argument("path", help="Path to file")
    chunk_parser.add_argument("--max-tokens", type=int, default=500, help="Max tokens per chunk (default: 500)")
    chunk_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Skeleton
    skeleton_parser = subparsers.add_parser("skeleton", help="Generate progressive architectural skeleton of a directory")
    skeleton_parser.add_argument("directory", help="Root directory path")
    skeleton_parser.add_argument("--depth", type=int, default=3, help="Max directory depth (default: 3)")
    skeleton_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    if args.subcommand == "inspect":
        res = analyze_file_density(args.path)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("═══════════════════════════════════════════════════════════════")
            print(f"  ORTHOTECT CONTEXT INSPECTOR: {res['file']}")
            print("═══════════════════════════════════════════════════════════════")
            print(f"  Lines:             {res['lines']}")
            print(f"  Characters:        {res['characters']}")
            print(f"  Estimated Tokens:  ~{res['estimated_tokens']}")
            print(f"  Density:           {res['tokens_per_line']} tokens/line ({res['chars_per_token']} chars/token)")
            print(f"  Symbols Extracted: {res['symbol_count']}")
            print(f"  Recommendation:    [{res['recommendation']}]")
            print(f"  Rationale:         {res['rationale']}")
            if res['symbols']:
                print("\n  Top Architectural Symbols:")
                for s in res['symbols'][:8]:
                    print(f"    - L{s['line']}: {s['type']} {s['name']}")
            print("═══════════════════════════════════════════════════════════════")

    elif args.subcommand == "chunk":
        chunks = semantic_chunk(args.path, max_tokens=args.max_tokens)
        if args.json:
            print(json.dumps(chunks, indent=2))
        else:
            print(f"📦 Semantically partitioned into {len(chunks)} coherent chunk(s):")
            for c in chunks:
                symbols_desc = f" ({', '.join(c['symbols'])})" if c['symbols'] else ""
                cont_desc = f" [Continuation: {c['continuation_of']}]" if c.get('continuation_of') else ""
                print(f"  • Chunk #{c['chunk_index']}: Lines {c['start_line']}–{c['end_line']} (~{c['estimated_tokens']} tokens){symbols_desc}{cont_desc}")

    elif args.subcommand == "skeleton":
        res = generate_context_skeleton(args.directory, max_depth=args.depth)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("═══════════════════════════════════════════════════════════════")
            print(f"  ORTHOTECT ARCHITECTURAL CONTEXT SKELETON: {res['root']}")
            print(f"  Files: {res['total_files']} | Total Raw Tokens: ~{res['total_estimated_tokens']}")
            print(f"  Skeleton Tokens: ~{res['skeleton_tokens']} | Compression: {round(res['compression_ratio'] * 100, 1)}%")
            print("═══════════════════════════════════════════════════════════════")
            print(res['formatted_view'])
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
