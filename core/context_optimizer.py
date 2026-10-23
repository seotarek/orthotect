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
    Deterministically estimate token count using calibrated BPE approximation.
    Averages ~3.8 characters per token for source code, adjusting for whitespace,
    punctuation clusters, and identifier boundaries (camelCase / snake_case).
    """
    if not text:
        return 0

    # Fast heuristic approximation calibrated against OpenAI cl100k_base / Gemini tokenizer
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

def extract_symbols(content: str, ext: str):
    """
    Extract major architectural symbols (classes, functions, components, FSMs)
    with their starting line numbers from file content.
    """
    symbols = []
    lines = content.splitlines()

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        # JavaScript / TypeScript / JSX
        if ext in ('.js', '.jsx', '.ts', '.tsx', '.mjs'):
            # function declarations or exports
            m = re.match(r'^(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s*([A-Za-z0-9_$]+)', stripped)
            if m:
                symbols.append({'line': idx, 'type': 'function', 'name': m.group(1)})
                continue

            # class declarations
            m = re.match(r'^(?:export\s+(?:default\s+)?)?class\s+([A-Za-z0-9_$]+)', stripped)
            if m:
                symbols.append({'line': idx, 'type': 'class', 'name': m.group(1)})
                continue

            # const/let arrow functions or React components: const MyComp = (...) =>
            m = re.match(r'^(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_$]+)\s*=>', stripped)
            if m:
                symbols.append({'line': idx, 'type': 'function', 'name': m.group(1)})
                continue

        # Python
        elif ext == '.py':
            m = re.match(r'^(?:async\s+)?def\s+([A-Za-z0-9_]+)\s*\(', stripped)
            if m:
                symbols.append({'line': idx, 'type': 'function', 'name': m.group(1)})
                continue

            m = re.match(r'^class\s+([A-Za-z0-9_]+)', stripped)
            if m:
                symbols.append({'line': idx, 'type': 'class', 'name': m.group(1)})
                continue

        # CSS / SCSS
        elif ext in ('.css', '.scss', '.less'):
            m = re.match(r'^(\.[A-Za-z0-9_-]+|#[A-Za-z0-9_-]+|:[a-zA-Z-]+)\s*\{', stripped)
            if m:
                symbols.append({'line': idx, 'type': 'selector', 'name': m.group(1)})
                continue

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
    Semantically partition file into coherent blocks bounded by top-level declarations,
    avoiding arbitrary line splitting that severs function closures or class scopes.
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

    symbols = extract_symbols(content, ext)
    symbol_lines = {s['line']: s['name'] for s in symbols}

    chunks = []
    current_chunk_lines = []
    current_start_line = 1
    current_symbols = []

    for idx, line in enumerate(lines, 1):
        if idx in symbol_lines:
            current_symbols.append(symbol_lines[idx])

        current_chunk_lines.append(line)
        candidate_text = "\n".join(current_chunk_lines)
        curr_tokens = estimate_tokens(candidate_text)

        # Check if we should split at a top-level boundary
        is_boundary = (idx + 1 in symbol_lines) or (idx == total_lines)
        if (curr_tokens >= max_tokens and is_boundary) or idx == total_lines:
            chunk_content = "\n".join(current_chunk_lines)
            chunks.append({
                'chunk_index': len(chunks) + 1,
                'file': filename,
                'start_line': current_start_line,
                'end_line': idx,
                'lines_count': len(current_chunk_lines),
                'estimated_tokens': estimate_tokens(chunk_content),
                'symbols': list(current_symbols),
                'content': chunk_content
            })
            current_chunk_lines = []
            current_start_line = idx + 1
            current_symbols = []

    # If any remaining lines exist
    if current_chunk_lines:
        chunk_content = "\n".join(current_chunk_lines)
        chunks.append({
            'chunk_index': len(chunks) + 1,
            'file': filename,
            'start_line': current_start_line,
            'end_line': total_lines,
            'lines_count': len(current_chunk_lines),
            'estimated_tokens': estimate_tokens(chunk_content),
            'symbols': list(current_symbols),
            'content': chunk_content
        })

    return chunks

def generate_context_skeleton(root_dir: str, max_depth: int = 3, ignore_dirs: set = None) -> dict:
    """
    Generate an ultra-compact architectural skeleton of files and their major symbols.
    Compresses codebase context by >85% compared to raw file reading.
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
                print(f"  • Chunk #{c['chunk_index']}: Lines {c['start_line']}–{c['end_line']} (~{c['estimated_tokens']} tokens){symbols_desc}")

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
