#!/usr/bin/env python3
"""
Orthotect Configuration Engine
Zero-dependency configuration manager supporting orthotect.config.json.
Provides hierarchical configuration resolution, glob-based path exclusions,
and gate threshold customization.
"""
import os
import sys
import json
import fnmatch
from pathlib import Path
from copy import deepcopy

DEFAULT_CONFIG = {
    "version": "1.0",
    "exclude": [
        "**/node_modules/**",
        "**/.git/**",
        "**/dist/**",
        "**/build/**",
        "**/__pycache__/**",
        "**/.gemini/**",
        "**/.claude/**",
        "**/tmp/**"
    ],
    "bidi": {
        "allowCamelCase": False
    },
    "cwv": {
        "maxDomDepth": 32,
        "maxDomNodes": 1500
    },
    "contrast": {
        "level": "AA"
    }
}

CONFIG_FILENAME = "orthotect.config.json"

def find_config_file(start_path=None):
    """
    Searches for orthotect.config.json starting from start_path (or cwd)
    and traversing upwards towards the filesystem root.
    """
    if start_path is None:
        current = Path.cwd()
    else:
        p = Path(start_path).resolve()
        current = p if p.is_dir() else p.parent

    for parent in [current] + list(current.parents):
        candidate = parent / CONFIG_FILENAME
        if candidate.is_file():
            return str(candidate)

    return None

def deep_merge(base, override):
    """Recursively merges override dictionary into base dictionary."""
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result

def load_orthotect_config(project_path=None):
    """
    Loads and parses orthotect.config.json merged with default configuration.
    Returns (config_dict, config_filepath_or_none).
    """
    config_path = find_config_file(project_path)
    if not config_path:
        return deepcopy(DEFAULT_CONFIG), None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        merged = deep_merge(DEFAULT_CONFIG, user_config)
        return merged, config_path
    except Exception as e:
        print(f"⚠️  [Orthotect Config] Warning: Failed to parse {config_path}: {e}", file=sys.stderr)
        return deepcopy(DEFAULT_CONFIG), None

def is_path_excluded(path_str, config, base_dir=None):
    """
    Evaluates whether a file or directory path matches any pattern in config['exclude'].
    Normalizes path to forward slashes.
    """
    if not config or "exclude" not in config:
        return False

    norm_path = path_str.replace('\\', '/')
    if base_dir:
        base_norm = os.path.abspath(base_dir).replace('\\', '/')
        if norm_path.startswith(base_norm):
            norm_path = norm_path[len(base_norm):].lstrip('/')

    basename = os.path.basename(norm_path)

    for pattern in config.get("exclude", []):
        p_clean = pattern.replace('\\', '/')
        # Match against relative path
        if fnmatch.fnmatch(norm_path, p_clean):
            return True
        # Match against basename
        if fnmatch.fnmatch(basename, p_clean):
            return True
        # Handle **/pattern/** globs
        trimmed_pat = p_clean.strip('*').strip('/')
        if trimmed_pat and (f"/{trimmed_pat}/" in f"/{norm_path}/" or norm_path == trimmed_pat):
            return True

    return False

def get_bidi_config(config):
    """Retrieves BiDi gate configuration settings."""
    cfg = config.get("bidi", {}) if config else {}
    return {
        "allowCamelCase": cfg.get("allowCamelCase", False)
    }

def get_cwv_config(config):
    """Retrieves CWV budget gate configuration settings."""
    cfg = config.get("cwv", {}) if config else {}
    return {
        "maxDomDepth": cfg.get("maxDomDepth", 32),
        "maxDomNodes": cfg.get("maxDomNodes", 1500)
    }

def get_contrast_config(config):
    """Retrieves WCAG contrast gate configuration settings."""
    cfg = config.get("contrast", {}) if config else {}
    return {
        "level": cfg.get("level", "AA")
    }

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    cfg, cfg_file = load_orthotect_config(target)
    print(f"Orthotect Config Status:")
    print(f"  Source: {cfg_file or 'DEFAULT (Built-in)'}")
    print(json.dumps(cfg, indent=2))
