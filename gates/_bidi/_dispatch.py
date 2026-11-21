"""
Extension-to-scanner dispatch.

`scan_file` sits below both `gate` (which runs it) and `_fix` (which re-runs it
after rewriting a file to verify the fix). Keeping it in its own module is what
keeps the graph acyclic: `_fix` needs the scanner, and the CLI needs the fixer,
so the scanner cannot live in the CLI module.
"""
import os

from ._css import scan_css_content, scan_html_content
from ._js import scan_js_content
from ._paths import SUPPORTED_EXTENSIONS

def scan_file(filepath, allow_camel_case=False):
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported styling format for BiDi AST verification: {ext}")

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if ext in ('.html', '.htm', '.vue', '.svelte'):
        return scan_html_content(content)
    elif ext in ('.jsx', '.tsx', '.js', '.ts'):
        return scan_js_content(content, allow_camel_case=allow_camel_case)
    else:
        return scan_css_content(content)
