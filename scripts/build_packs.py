#!/usr/bin/env python3
"""Build skill packs from toolbox YAML specs.

For each skill-protocol spec with a source.repo, fetches SKILL.md from GitHub
and creates a .tar.gz pack with SKILL.md, spec.yaml, and manifest.json.

Usage:
    python scripts/build_packs.py
    python scripts/build_packs.py --name "gstack-*"
    python scripts/build_packs.py --dry-run
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import tarfile
from io import BytesIO
from pathlib import Path

import httpx
import yaml


def fetch_skill_md(repo: str, path: str, ref: str = "main") -> str:
    """Fetch SKILL.md from GitHub."""
    repo = repo.replace("https://github.com/", "").rstrip("/")
    base_path = path.rstrip("/") if path else ""
    skill_path = f"{base_path}/SKILL.md" if base_path else "SKILL.md"
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{skill_path}"

    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"  Warning: failed to fetch {url}: {e}", file=sys.stderr)

    return ""


def build_pack(spec_path: Path, output_dir: Path, dry_run: bool = False) -> bool:
    """Build a pack from a YAML spec file."""
    try:
        raw = spec_path.read_text()
        spec = yaml.safe_load(raw)
    except Exception as e:
        print(f"  Skip {spec_path}: {e}", file=sys.stderr)
        return False

    if not isinstance(spec, dict) or "name" not in spec:
        return False

    name = spec["name"]
    protocol = spec.get("protocol", "")
    source = spec.get("source", {})

    if protocol != "skill" or not isinstance(source, dict) or not source.get("repo"):
        return False

    repo = source.get("repo", "")
    path = source.get("path", "")
    ref = source.get("ref", "main")

    if dry_run:
        print(f"  [DRY RUN] {name}")
        return True

    # Fetch SKILL.md
    skill_md = fetch_skill_md(repo, path, ref)
    if not skill_md:
        print(f"  Skip {name}: no SKILL.md at {repo}/{path}", file=sys.stderr)
        return False

    # Build pack
    pack_path = output_dir / f"{name}.tar.gz"
    with tarfile.open(str(pack_path), "w:gz") as tar:
        # SKILL.md
        data = skill_md.encode("utf-8")
        info = tarfile.TarInfo(name=f"{name}/SKILL.md")
        info.size = len(data)
        tar.addfile(info, BytesIO(data))

        # spec.yaml
        spec_data = raw.encode("utf-8")
        info = tarfile.TarInfo(name=f"{name}/spec.yaml")
        info.size = len(spec_data)
        tar.addfile(info, BytesIO(spec_data))

        # manifest.json
        manifest = {
            "name": name,
            "version": spec.get("version", "0.1.0"),
            "description": spec.get("description", ""),
            "protocol": "skill",
            "source": {"repo": repo, "path": path, "ref": ref},
            "files": [
                {
                    "path": "SKILL.md",
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            ],
            "content_sha256": hashlib.sha256(data).hexdigest(),
        }
        manifest_data = json.dumps(manifest, indent=2).encode("utf-8")
        info = tarfile.TarInfo(name=f"{name}/manifest.json")
        info.size = len(manifest_data)
        tar.addfile(info, BytesIO(manifest_data))

    print(f"  Built: {name} ({os.path.getsize(pack_path)} bytes)")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build skill packs from toolbox specs")
    parser.add_argument("--name", default="", help="Filter by name pattern")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be built")
    parser.add_argument("--output", default="packs/skills", help="Output directory")
    args = parser.parse_args()

    # Find toolbox root
    toolbox_root = Path(__file__).parent.parent
    output_dir = toolbox_root / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all YAML specs
    specs = sorted(toolbox_root.glob("*/*//*.yaml"))
    if not specs:
        # Try letter-prefix layout
        specs = []
        for letter_dir in sorted(toolbox_root.iterdir()):
            if not letter_dir.is_dir() or letter_dir.name.startswith(".") or letter_dir.name in ("scripts", "docs", "packs"):
                continue
            for tool_dir in sorted(letter_dir.iterdir()):
                if not tool_dir.is_dir():
                    continue
                for yaml_file in sorted(tool_dir.glob("*.yaml")):
                    specs.append(yaml_file)

    print(f"Found {len(specs)} specs")

    built = 0
    for spec_path in specs:
        if args.name:
            name_pattern = args.name.replace("*", "")
            spec_name = spec_path.stem
            if name_pattern not in spec_name:
                continue
        if build_pack(spec_path, output_dir, args.dry_run):
            built += 1

    # Write checksums file
    if not args.dry_run:
        checksums_path = toolbox_root / "packs" / "checksums.txt"
        with open(checksums_path, "w") as f:
            for pack_file in sorted(output_dir.glob("*.tar.gz")):
                pack_data = pack_file.read_bytes()
                sha = hashlib.sha256(pack_data).hexdigest()
                f.write(f"{sha}  {pack_file.name}\n")

    print(f"\nDone: {built} packs built")


if __name__ == "__main__":
    main()
