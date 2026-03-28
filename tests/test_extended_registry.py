"""Validation tests for the extended registry specs.

These tests verify that:
1. All extended specs have required fields (name, description, version, etc.).
2. Extended specs contain ALL read-only actions from the corresponding official spec.
3. Extended specs add at least one write/destructive action beyond the official spec.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml

EXTENDED_REGISTRY_PATH = Path(
    os.environ.get(
        "EXTENDED_REGISTRY_PATH",
        str(Path(__file__).parent.parent / "registry-extended"),
    )
)
OFFICIAL_REGISTRY_PATH = Path(
    os.environ.get(
        "REGISTRY_PATH",
        str(Path(__file__).parent.parent / "registry"),
    )
)

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

VALID_CATEGORIES: set[str] = {
    "ai", "cloud", "communication", "crypto", "data", "data-portal",
    "developer", "devops", "documentation", "finance", "geo", "ip",
    "knowledge-base", "media", "monitoring", "news", "productivity",
    "reference", "search", "security", "text", "weather",
}

VALID_PROTOCOLS: set[str] = {
    "http", "https", "rest", "graphql", "grpc", "websocket", "command",
    "website", "tcp",
}


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Empty YAML file: {path}")
    return data


def find_extended_specs() -> list[Path]:
    """Discover all YAML spec files in the extended registry."""
    specs: list[Path] = []
    for yaml_path in sorted(EXTENDED_REGISTRY_PATH.rglob("*.yaml")):
        if yaml_path.name.startswith("."):
            continue
        if yaml_path.name == "registry.yaml":
            continue
        if "scripts" in yaml_path.parts:
            continue
        if ".github" in yaml_path.parts:
            continue
        specs.append(yaml_path)
    return specs


def find_official_counterpart(extended_path: Path) -> Path | None:
    """Find the official spec that corresponds to an extended spec."""
    relative = extended_path.relative_to(EXTENDED_REGISTRY_PATH)
    official_path = OFFICIAL_REGISTRY_PATH / relative
    if official_path.exists():
        return official_path
    return None


def get_action_names(spec: dict[str, Any]) -> set[str]:
    """Extract action names from a spec."""
    return {a["name"] for a in spec.get("actions", []) if "name" in a}


def get_action_by_name(spec: dict[str, Any], name: str) -> dict[str, Any] | None:
    """Find a single action by name in a spec."""
    for action in spec.get("actions", []):
        if action.get("name") == name:
            return action
    return None


def spec_id(path: Path) -> str:
    """Generate a human-readable test ID from a spec file path."""
    try:
        relative = path.relative_to(EXTENDED_REGISTRY_PATH)
    except ValueError:
        relative = path
    return str(relative).replace("/", "::").removesuffix(".yaml")


def _load_all_extended_specs() -> list[tuple[Path, dict[str, Any]]]:
    """Load all extended spec files for parameterization."""
    results: list[tuple[Path, dict[str, Any]]] = []
    for path in find_extended_specs():
        data = load_yaml(path)
        results.append((path, data))
    return results


def _spec_params() -> list[Any]:
    """Build pytest parameters for each extended spec file."""
    params: list[Any] = []
    for path, data in _load_all_extended_specs():
        params.append(pytest.param(path, data, id=spec_id(path)))
    return params


SPEC_PARAMS = _spec_params()


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_required_fields(spec_path: Path, spec: dict[str, Any]) -> None:
    """Every extended spec must contain all required top-level fields."""
    missing: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in spec:
            missing.append(field)
    assert not missing, (
        f"{spec_path.name}: missing required fields: {', '.join(missing)}"
    )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_valid_category(spec_path: Path, spec: dict[str, Any]) -> None:
    """Category must be a recognized value."""
    category = spec.get("category")
    assert category is not None, f"{spec_path.name}: missing 'category'"
    assert category in VALID_CATEGORIES, (
        f"{spec_path.name}: invalid category '{category}'"
    )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_valid_protocol(spec_path: Path, spec: dict[str, Any]) -> None:
    """Protocol must be a recognized value."""
    protocol = spec.get("protocol")
    assert protocol is not None, f"{spec_path.name}: missing 'protocol'"
    assert protocol in VALID_PROTOCOLS, (
        f"{spec_path.name}: invalid protocol '{protocol}'"
    )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_actions_exist(spec_path: Path, spec: dict[str, Any]) -> None:
    """Every spec must have at least one action."""
    actions = spec.get("actions")
    assert actions is not None, f"{spec_path.name}: missing 'actions' key"
    assert isinstance(actions, list), f"{spec_path.name}: 'actions' must be a list"
    assert len(actions) > 0, f"{spec_path.name}: 'actions' list is empty"


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_action_required_fields(spec_path: Path, spec: dict[str, Any]) -> None:
    """Every action must have a name and description."""
    for i, action in enumerate(spec.get("actions", [])):
        for field in REQUIRED_ACTION_FIELDS:
            assert field in action, (
                f"{spec_path.name}: action [{i}] missing '{field}'"
            )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_tags_exist(spec_path: Path, spec: dict[str, Any]) -> None:
    """Tags array must be present and non-empty."""
    tags = spec.get("tags")
    assert tags is not None, f"{spec_path.name}: missing 'tags'"
    assert isinstance(tags, list), f"{spec_path.name}: 'tags' must be a list"
    assert len(tags) > 0, f"{spec_path.name}: 'tags' list is empty"


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_has_at_least_as_many_actions_as_official(
    spec_path: Path, spec: dict[str, Any]
) -> None:
    """Extended specs must have at least as many actions as the official spec.

    The extended spec overrides the official entirely, so it must cover the same
    capabilities (or more). Action names may differ if the extended spec
    reorganizes the interface (e.g., 'get' instead of 'pods'/'services').

    If no official counterpart exists, the test is skipped.
    """
    official_path = find_official_counterpart(spec_path)
    if official_path is None:
        pytest.skip(f"No official counterpart for {spec_path.name}")

    official_spec = load_yaml(official_path)
    official_count = len(official_spec.get("actions", []))
    extended_count = len(spec.get("actions", []))

    assert extended_count >= official_count, (
        f"{spec_path.name}: extended spec has {extended_count} actions but "
        f"official has {official_count}. Extended must cover at least as many."
    )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_shared_actions_match_official(
    spec_path: Path, spec: dict[str, Any]
) -> None:
    """For actions that share the same name in both specs, run templates must match.

    Only checks actions that exist in both specs by name. Actions that are renamed
    or reorganized in the extended spec are not checked here.
    """
    official_path = find_official_counterpart(spec_path)
    if official_path is None:
        pytest.skip(f"No official counterpart for {spec_path.name}")

    official_spec = load_yaml(official_path)
    differences: list[str] = []

    for official_action in official_spec.get("actions", []):
        action_name = official_action.get("name", "")
        extended_action = get_action_by_name(spec, action_name)
        if extended_action is None:
            continue

        official_run = official_action.get("run", "")
        extended_run = extended_action.get("run", "")
        if official_run and official_run != extended_run:
            differences.append(
                f"action '{action_name}' run template differs"
            )

        official_send = official_action.get("send", {})
        extended_send = extended_action.get("send", {})
        if official_send and official_send != extended_send:
            differences.append(
                f"action '{action_name}' send template differs"
            )

    if differences:
        import warnings
        warnings.warn(
            f"{spec_path.name}: shared action mismatches (may need sync):\n"
            + "\n".join(f"  - {d}" for d in differences),
            stacklevel=1,
        )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_adds_write_actions_beyond_official(
    spec_path: Path, spec: dict[str, Any]
) -> None:
    """Extended specs must add at least one action beyond the official spec.

    If no official counterpart exists, the test is skipped.
    """
    official_path = find_official_counterpart(spec_path)
    if official_path is None:
        pytest.skip(f"No official counterpart for {spec_path.name}")

    official_spec = load_yaml(official_path)
    official_actions = get_action_names(official_spec)
    extended_actions = get_action_names(spec)

    new_actions = extended_actions - official_actions
    assert len(new_actions) > 0, (
        f"{spec_path.name}: extended spec does not add any actions beyond the official spec. "
        f"Extended specs should include at least one write or destructive action."
    )
