"""
Filesystem scope: which files this gate will look at, and which it will not.
"""

IGNORE_DIRS = {'node_modules', '.git', 'dist', '__pycache__', '.claude', '.gemini', 'tmp'}


SUPPORTED_EXTENSIONS = {'.css', '.scss', '.less', '.html', '.htm', '.vue', '.svelte', '.jsx', '.tsx', '.js', '.ts'}
