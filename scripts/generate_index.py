#!/usr/bin/env python3
"""Generate toolbox-index.json from the toolbox directory.

Scans toolbox/{letter}/{tool}/{tool}.yaml and produces a JSON manifest
of all community tools. This file is the source of truth for identifying
which tools are promoted to the community toolbox.

Usage:
    python3 scripts/generate_index.py          # writes toolbox-index.json
    python3 scripts/generate_index.py --check   # exits 1 if index is stale
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

TOOLBOX_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = TOOLBOX_ROOT / "toolbox-index.json"

# Single-letter directories only (skip docs/, scripts/, etc.)
LETTER_DIRS = sorted(
    d for d in TOOLBOX_ROOT.iterdir()
    if d.is_dir() and len(d.name) == 1 and d.name.isalpha()
)


def scan_toolbox() -> list[dict[str, str]]:
    """Scan toolbox and return sorted list of tool entries."""
    tools: list[dict[str, str]] = []
    for letter_dir in LETTER_DIRS:
        for tool_dir in sorted(letter_dir.iterdir()):
            if not tool_dir.is_dir():
                continue
            spec_path = tool_dir / f"{tool_dir.name}.yaml"
            if not spec_path.exists():
                continue
            try:
                data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
            except (yaml.YAMLError, OSError):
                continue
            if not isinstance(data, dict):
                continue
            name = data.get("name", tool_dir.name)
            tools.append({
                "name": name,
                "version": str(data.get("version", "0.0.0")),
                "category": data.get("category", ""),
                "etag": hashlib.sha256(
                    spec_path.read_bytes()
                ).hexdigest()[:16],
            })
    tools.sort(key=lambda t: t["name"])
    return tools


def main() -> None:
    tools = scan_toolbox()
    index = {
        "version": 1,
        "count": len(tools),
        "tools": tools,
    }
    new_content = json.dumps(index, indent=2, ensure_ascii=False) + "\n"

    if "--check" in sys.argv:
        if not OUTPUT.exists():
            print(f"ERROR: {OUTPUT.name} does not exist. Run: make index")
            sys.exit(1)
        existing = OUTPUT.read_text(encoding="utf-8")
        if existing != new_content:
            print(f"ERROR: {OUTPUT.name} is stale. Run: make index")
            sys.exit(1)
        print(f"OK: {OUTPUT.name} is up to date ({len(tools)} tools)")
        sys.exit(0)

    OUTPUT.write_text(new_content, encoding="utf-8")
    print(f"Wrote {OUTPUT.name} with {len(tools)} tools")


if __name__ == "__main__":
    main()
