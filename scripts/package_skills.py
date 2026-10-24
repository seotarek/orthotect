#!/usr/bin/env python3
"""
Orthotect Skill Packager
Builds deterministic, single-skill ZIP bundles with SHA-256 manifests
for cross-agent portability (Claude Code, Cursor, Codex, Antigravity, OpenCode).

Adapted from Marketingskills packager under MIT License (Copyright 2025 Corey Haines).
"""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXCLUDED_PARTS = {"evals", "__pycache__", "node_modules", ".cache", ".DS_Store", ".git", ".env", ".github"}

SENSITIVE_FILENAME_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.I),
    re.compile(r".*\.(pem|key|pkcs12|p12|p8|crt|cer|der)$", re.I),
    re.compile(r"^id_rsa.*", re.I),
    re.compile(r"^id_ed25519.*", re.I),
    re.compile(r".*(?:api[_-]?(?:key|secret|token)|access[_-]?token|auth[_-]?token|secret[_-]?key|credentials?).*", re.I),
    re.compile(r"^(token|secret|credentials|passwd|shadow)(\.[a-z0-9]+)?$", re.I),
]

SENSITIVE_CONTENT_PATTERNS = [
    re.compile(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    re.compile(rb"-----BEGIN OPENSSH PRIVATE KEY-----"),
    re.compile(rb"ghp_[A-Za-z0-9_]{36}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{82}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"sk-[A-Za-z0-9]{32,}"),
]

ALLOWED_EXTENSIONS_BY_DIR = {
    "references": {".md", ".txt", ".json", ".yaml", ".yml"},
    "scripts": {".mjs", ".js", ".py", ".sh"},
    "assets": {".svg", ".png", ".jpg", ".jpeg", ".webp", ".json"},
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_metadata(data: bytes) -> dict:
    text = data.decode("utf-8")
    front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not front:
        raise ValueError("SKILL.md is missing YAML frontmatter delimiters '---'")
    fields = {}
    for key in ("name", "description"):
        matches = list(re.finditer(r"^" + key + r":[ \t]*(.*)$", front[1], re.M))
        if len(matches) != 1:
            raise ValueError(f"SKILL.md requires exactly one '{key}' declaration")
        val = matches[0][1].rstrip("\r").strip()
        if val.startswith('"') and val.endswith('"'):
            val = json.loads(val)
        elif val.startswith("'") and val.endswith("'"):
            val = val[1:-1].replace("''", "'")
        elif not val or val.startswith(("|", ">")):
            raise ValueError(f"Unsupported {key} scalar; use a single-line value")
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"SKILL.md '{key}' must be non-empty text")
        fields[key] = val
    return fields


def get_repo_revision(repo_dir: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            stderr=subprocess.PIPE,
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "unversioned"


def collect_skill_files_from_disk(repo_dir: Path, skill_name: str) -> dict:
    skill_dir = (repo_dir / "skills" / skill_name).resolve()
    if not skill_dir.is_dir():
        raise ValueError(f"Skill directory not found: {skill_dir}")

    files = {}
    for root, dirs, filenames in os.walk(skill_dir):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_PARTS and not d.startswith(".")]
        for fname in filenames:
            # Exclude dotfiles, excluded parts, and sensitive file patterns
            if fname in EXCLUDED_PARTS or fname.startswith("."):
                continue
            if any(pat.search(fname) for pat in SENSITIVE_FILENAME_PATTERNS):
                continue

            full_path = Path(root) / fname
            rel_path = full_path.relative_to(skill_dir).as_posix()
            parts = PurePosixPath(rel_path).parts

            if any(p in EXCLUDED_PARTS or p.startswith(".") for p in parts):
                continue

            # Symlink defense: verify target resolves strictly within skill_dir
            if full_path.is_symlink():
                try:
                    resolved = full_path.resolve(strict=True)
                    if not resolved.is_relative_to(skill_dir):
                        raise ValueError(f"Security violation: Symlink '{rel_path}' points outside skill directory ({resolved})")
                except Exception as e:
                    raise ValueError(f"Security violation: Unresolvable symlink '{rel_path}' ({e})")

            # SKILL.md is mandatory at the root
            if rel_path == "SKILL.md":
                data = full_path.read_bytes()
                for cpat in SENSITIVE_CONTENT_PATTERNS:
                    if cpat.search(data):
                        raise ValueError(f"Security violation: Sensitive credential pattern detected in '{rel_path}'")
                files[rel_path] = (data, "100644", f"skills/{skill_name}/{rel_path}")
                continue

            # Other allowed subdirectories with strict file extensions
            top_dir = parts[0]
            if top_dir not in ALLOWED_EXTENSIONS_BY_DIR:
                continue

            ext = full_path.suffix.lower()
            if ext not in ALLOWED_EXTENSIONS_BY_DIR[top_dir]:
                continue

            data = full_path.read_bytes()
            for cpat in SENSITIVE_CONTENT_PATTERNS:
                if cpat.search(data):
                    raise ValueError(f"Security violation: Sensitive credential pattern detected in '{rel_path}'")
            files[rel_path] = (data, "100644", f"skills/{skill_name}/{rel_path}")

    return files


def build_packages(
    repo_dir: Path,
    output_dir: Path,
    skills: list = None,
    max_bytes: int = 30_000_000,
) -> dict:
    repo_dir = repo_dir.resolve()
    output_dir = output_dir.resolve()

    skills_root = repo_dir / "skills"
    if not skills_root.is_dir():
        raise ValueError(f"Skills directory not found: {skills_root}")

    available_skills = sorted(
        [
            d.name
            for d in skills_root.iterdir()
            if d.is_dir() and (d / "SKILL.md").is_file()
        ]
    )

    selected = sorted(set(skills) if skills else available_skills)
    if not selected:
        raise ValueError("No skills selected for packaging")

    for name in selected:
        if not SKILL_NAME_RE.fullmatch(name) or len(name) > 64 or name not in available_skills:
            raise ValueError(f"Unknown or invalid skill name: {name}")

    license_file = repo_dir / "LICENSE"
    if not license_file.is_file():
        raise ValueError(f"Required LICENSE file not found in {repo_dir}")
    license_data = license_file.read_bytes()

    commit = get_repo_revision(repo_dir)
    bundles = []
    artifacts = {}

    for name in selected:
        resources = collect_skill_files_from_disk(repo_dir, name)
        if "SKILL.md" not in resources:
            raise ValueError(f"Missing SKILL.md in skill {name}")

        original_skill_md = resources["SKILL.md"][0]
        meta = extract_metadata(original_skill_md)
        if meta["name"] != name:
            raise ValueError(f"SKILL.md declared name '{meta['name']}' does not match directory '{name}'")

        resources["LICENSE"] = (license_data, "100644", "LICENSE")

        uncompressed_bytes = sum(len(item[0]) for item in resources.values())
        if uncompressed_bytes > max_bytes:
            raise ValueError(f"Skill bundle '{name}' exceeds size bound ({uncompressed_bytes} > {max_bytes})")

        stream = io.BytesIO()
        inventory = []

        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative, (data, mode, source_path) in sorted(resources.items()):
                # Fixed deterministic epoch for reproducible ZIP hashes
                entry = zipfile.ZipInfo(f"{name}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, data, compresslevel=9)
                inventory.append({
                    "path": entry.filename,
                    "source_path": source_path,
                    "sha256": sha256_bytes(data),
                    "size_bytes": len(data),
                })

        filename = f"{name}.zip"
        zip_bytes = stream.getvalue()
        artifacts[filename] = zip_bytes

        bundles.append({
            "skill": name,
            "archive": filename,
            "sha256": sha256_bytes(zip_bytes),
            "uncompressed_bytes": uncompressed_bytes,
            "file_count": len(resources),
            "files": inventory,
        })

    manifest = {
        "format_version": "orthotect-skill-pack.v1",
        "source_commit": commit,
        "bundle_count": len(bundles),
        "bundles": bundles,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, data in artifacts.items():
        (output_dir / filename).write_bytes(data)

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root path (default: parent of scripts/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory where packaged ZIP bundles and manifest.json will be saved",
    )
    parser.add_argument(
        "--skill",
        action="append",
        help="Select specific skill to package (repeatable, default: all skills)",
    )
    parser.add_argument(
        "--max-uncompressed-bytes",
        type=int,
        default=30_000_000,
        help="Per-bundle uncompressed size limit in bytes",
    )

    args = parser.parse_args()
    try:
        manifest = build_packages(
            repo_dir=args.repo,
            output_dir=args.output,
            skills=args.skill,
            max_bytes=args.max_uncompressed_bytes,
        )
        print(f"✅ Successfully built {manifest['bundle_count']} skill bundles in {args.output}")
        for b in manifest["bundles"]:
            print(f"   • {b['archive']} ({b['sha256'][:12]}... - {b['file_count']} files, {b['uncompressed_bytes']} bytes)")
    except Exception as e:
        sys.stderr.write(f"❌ Packaging failed: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
