"""Shared fixtures and validation helpers for clictl registry tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml


REGISTRY_PATH: Path = Path(os.environ.get("REGISTRY_PATH", str(Path(__file__).parent.parent)))

VALID_CATEGORIES: set[str] = {
    "ai",
    "cloud",
    "communication",
    "crypto",
    "data",
    "data-portal",
    "design",
    "developer",
    "devops",
    "documentation",
    "finance",
    "geo",
    "ip",
    "knowledge-base",
    "media",
    "monitoring",
    "news",
    "productivity",
    "reference",
    "search",
    "security",
    "text",
    "weather",
}

VALID_PROTOCOLS: set[str] = {
    "http",
    "https",
    "rest",
    "graphql",
    "grpc",
    "websocket",
    "cli",
    "command",
    "website",
    "tcp",
    "composite",
    "mcp",
    "skill",
}

REQUIRED_TOP_LEVEL_FIELDS: list[str] = [
    "name",
    "description",
    "version",
    "category",
    "protocol",
]

REQUIRED_ACTION_FIELDS: list[str] = [
    "name",
    "description",
]

DESTRUCTIVE_METHODS: set[str] = {"DELETE", "PUT", "PATCH"}


def load_spec(spec_path: Path) -> dict[str, Any]:
    """Load and parse a YAML spec file, returning its contents as a dictionary."""
    with open(spec_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Empty spec file: {spec_path}")
    return data


def validate_spec_schema(spec: dict[str, Any]) -> list[str]:
    """Validate that a spec contains all required top-level fields.

    Returns a list of error messages. An empty list means the spec is valid.
    """
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in spec:
            errors.append(f"Missing required field: {field}")

    protocol = spec.get("protocol")

    # MCP specs require transport, not actions
    if protocol == "mcp":
        if "transport" not in spec:
            errors.append("MCP spec missing required 'transport' field")
        else:
            transport = spec["transport"]
            if transport.get("type") not in ("stdio", "http"):
                errors.append(f"MCP transport type must be 'stdio' or 'http', got '{transport.get('type')}'")
    # Skill specs require source, not actions
    elif protocol == "skill":
        if "source" not in spec:
            errors.append("Skill spec missing required 'source' field")
        if "platforms" not in spec or not isinstance(spec.get("platforms"), list):
            errors.append("Skill spec missing or invalid 'platforms' field (must be a list)")
    # All other protocols require actions
    elif "actions" not in spec or not isinstance(spec.get("actions"), list):
        errors.append("Missing or invalid 'actions' field (must be a list)")
    else:
        for i, action in enumerate(spec["actions"]):
            for action_field in REQUIRED_ACTION_FIELDS:
                if action_field not in action:
                    errors.append(f"Action [{i}] missing required field: {action_field}")

    category = spec.get("category")
    if category and category not in VALID_CATEGORIES:
        errors.append(f"Invalid category: {category}")

    protocol = spec.get("protocol")
    if protocol and protocol not in VALID_PROTOCOLS:
        errors.append(f"Invalid protocol: {protocol}")

    tags = spec.get("tags")
    if tags is None:
        errors.append("Missing 'tags' field")
    elif not isinstance(tags, list) or len(tags) == 0:
        errors.append("'tags' must be a non-empty list")

    return errors


def validate_action_safety(spec: dict[str, Any]) -> list[str]:
    """Check actions for destructive HTTP methods.

    In the official registry:
    - DELETE is always rejected.
    - POST without safe: true is allowed IF the spec requires auth (key-gated writes).
    - POST without safe: true and without auth is rejected.

    Returns a list of safety violation messages.
    """
    violations: list[str] = []
    # MCP and skill specs don't have actions to validate
    if spec.get("protocol") in ("mcp", "skill"):
        return violations
    actions = spec.get("actions", [])
    has_auth = _spec_requires_auth(spec)

    for action in actions:
        method = str(action.get("method", "")).upper()
        action_name = action.get("name", "<unnamed>")

        if method == "DELETE":
            violations.append(
                f"Action '{action_name}' uses DELETE method (use extended registry)"
            )

        if method == "POST" and not action.get("safe", False) and not has_auth:
            violations.append(
                f"Action '{action_name}' uses POST without safe: true and without auth"
            )

    return violations


def _spec_requires_auth(spec: dict[str, Any]) -> bool:
    """Check if the spec requires authentication (API key, bearer, oauth2)."""
    auth = spec.get("auth")
    if auth is None:
        return False
    if isinstance(auth, list):
        return any(a.get("type") not in (None, "none") for a in auth)
    return auth.get("type") not in (None, "none")


MAX_COMPOSITE_STEPS = 20
MAX_COMPOSITE_DEPTH = 3


def validate_composite_schema(spec: dict[str, Any]) -> list[str]:
    """Validate composite-specific constraints on a spec.

    Returns a list of error messages. An empty list means the spec is valid.
    Only runs on specs with protocol: composite.
    """
    errors: list[str] = []
    if spec.get("protocol") != "composite":
        return errors

    actions = spec.get("actions", [])
    for action in actions:
        if not action.get("composite"):
            continue

        action_name = action.get("name", "<unnamed>")
        steps = action.get("steps", [])

        if not steps:
            errors.append(f"Composite action '{action_name}' has no steps")
            continue

        if len(steps) > MAX_COMPOSITE_STEPS:
            errors.append(
                f"Composite action '{action_name}' has {len(steps)} steps (max {MAX_COMPOSITE_STEPS})"
            )

        # Check unique step IDs
        step_ids: set[str] = set()
        for step in steps:
            sid = step.get("id", "")
            if not sid:
                errors.append(f"Action '{action_name}': step missing 'id'")
            elif sid in step_ids:
                errors.append(f"Action '{action_name}': duplicate step ID '{sid}'")
            step_ids.add(sid)

        # Check depends_on references exist
        for step in steps:
            for dep in step.get("depends_on", []):
                if dep not in step_ids:
                    errors.append(
                        f"Action '{action_name}': step '{step.get('id')}' depends on "
                        f"unknown step '{dep}'"
                    )

        # Check for cycles (Kahn's algorithm)
        in_degree: dict[str, int] = {s.get("id", ""): 0 for s in steps}
        for step in steps:
            for dep in step.get("depends_on", []):
                sid = step.get("id", "")
                if sid in in_degree:
                    in_degree[sid] += 1

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        visited = 0
        adj: dict[str, list[str]] = {s.get("id", ""): [] for s in steps}
        for step in steps:
            for dep in step.get("depends_on", []):
                if dep in adj:
                    adj[dep].append(step.get("id", ""))

        # BFS
        processed: list[str] = []
        q = list(queue)
        temp_in = dict(in_degree)
        while q:
            node = q.pop(0)
            processed.append(node)
            for neighbor in adj.get(node, []):
                temp_in[neighbor] -= 1
                if temp_in[neighbor] == 0:
                    q.append(neighbor)

        if len(processed) != len(step_ids):
            errors.append(f"Action '{action_name}': cycle detected in step dependencies")

        # Check max depth
        def _depth(sid: str, memo: dict[str, int]) -> int:
            if sid in memo:
                return memo[sid]
            step_map = {s.get("id", ""): s for s in steps}
            step = step_map.get(sid)
            if not step or not step.get("depends_on"):
                memo[sid] = 1
                return 1
            d = 1 + max(_depth(dep, memo) for dep in step.get("depends_on", []) if dep in step_map)
            memo[sid] = d
            return d

        memo: dict[str, int] = {}
        for sid in step_ids:
            if sid and _depth(sid, memo) > MAX_COMPOSITE_DEPTH:
                errors.append(
                    f"Action '{action_name}': step '{sid}' exceeds max depth of {MAX_COMPOSITE_DEPTH}"
                )

        # Check each step has method+url or tool+action
        for step in steps:
            sid = step.get("id", "<unnamed>")
            has_method = "method" in step and "url" in step
            has_tool_action = "tool" in step and "action" in step
            has_action_only = "action" in step and "tool" not in step
            if not has_method and not has_tool_action and not has_action_only:
                errors.append(
                    f"Action '{action_name}': step '{sid}' needs method+url or tool+action or action"
                )

    return errors


def all_spec_files() -> list[Path]:
    """Discover all YAML spec files in the registry directory."""
    spec_files: list[Path] = []
    for yaml_path in sorted(REGISTRY_PATH.rglob("*.yaml")):
        if yaml_path.name.startswith("."):
            continue
        if yaml_path.name == "registry.yaml":
            continue
        # Skip non-spec files (workflows, configs, etc.)
        relative = str(yaml_path.relative_to(REGISTRY_PATH))
        if relative.startswith(".github") or relative.startswith("tests"):
            continue
        spec_files.append(yaml_path)
    return spec_files


def spec_id(spec_path: Path) -> str:
    """Generate a human-readable test ID from a spec file path."""
    try:
        relative = spec_path.relative_to(REGISTRY_PATH)
    except ValueError:
        relative = spec_path
    return str(relative).replace("/", "::").removesuffix(".yaml")


@pytest.fixture(scope="session")
def registry_path() -> Path:
    """Return the resolved registry path."""
    return REGISTRY_PATH


@pytest.fixture(scope="session")
def spec_files() -> list[Path]:
    """Return all discovered spec files in the registry."""
    files = all_spec_files()
    if not files:
        pytest.skip("No spec files found in registry")
    return files
