"""Parameterized schema validation tests that run against every spec in the registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import (
    VALID_CATEGORIES,
    VALID_PROTOCOLS,
    all_spec_files,
    load_spec,
    spec_id,
    validate_action_safety,
    validate_composite_schema,
    validate_spec_schema,
)


def _load_all_specs() -> list[tuple[Path, dict[str, Any]]]:
    """Load all spec files and return (path, data) tuples for parameterization."""
    results: list[tuple[Path, dict[str, Any]]] = []
    for path in all_spec_files():
        try:
            data = load_spec(path)
            results.append((path, data))
        except Exception as exc:
            pytest.fail(f"Failed to load {path}: {exc}")
    return results


def _spec_params() -> list[pytest.param]:
    """Build pytest parameters with readable IDs for each spec file."""
    params: list[pytest.param] = []
    for path, data in _load_all_specs():
        params.append(pytest.param(path, data, id=spec_id(path)))
    return params


SPEC_PARAMS = _spec_params()


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_required_fields(spec_path: Path, spec: dict[str, Any]) -> None:
    """Every spec must contain name, description, version, category, and protocol."""
    errors = validate_spec_schema(spec)
    field_errors = [e for e in errors if e.startswith("Missing required field")]
    assert not field_errors, f"{spec_path.name}: {'; '.join(field_errors)}"


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_actions_exist(spec_path: Path, spec: dict[str, Any]) -> None:
    """Every non-MCP/skill spec must define at least one action."""
    protocol = spec.get("protocol")
    if protocol in ("mcp", "skill"):
        pytest.skip(f"MCP/skill specs don't require actions (protocol: {protocol})")
    actions = spec.get("actions")
    assert actions is not None, f"{spec_path.name}: 'actions' key is missing"
    assert isinstance(actions, list), f"{spec_path.name}: 'actions' must be a list"
    assert len(actions) > 0, f"{spec_path.name}: 'actions' list is empty"


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_action_fields(spec_path: Path, spec: dict[str, Any]) -> None:
    """Every action must have a name and description."""
    actions = spec.get("actions", [])
    for i, action in enumerate(actions):
        assert "name" in action, (
            f"{spec_path.name}: action [{i}] missing 'name'"
        )
        assert "description" in action, (
            f"{spec_path.name}: action [{i}] (name={action.get('name', '?')}) missing 'description'"
        )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_connection(spec_path: Path, spec: dict[str, Any]) -> None:
    """API and website specs must have a connection block with base_url or url."""
    protocol = spec.get("protocol", "")
    if protocol in ("cli", "command", "tcp"):
        pytest.skip("CLI/TCP specs use shell/host connection, not base_url")
    if protocol in ("mcp", "skill", "composite"):
        pytest.skip(f"{protocol} specs use transport/source instead of connection")

    connection = spec.get("connection")
    assert connection is not None, f"{spec_path.name}: missing 'connection' block"

    has_base_url = "base_url" in connection
    has_url = "url" in connection
    if protocol in ("http", "https", "rest", "grpc", "website"):
        assert has_base_url, (
            f"{spec_path.name}: connection block missing 'base_url'"
        )
    elif protocol in ("graphql", "websocket"):
        assert has_base_url or has_url, (
            f"{spec_path.name}: connection block missing 'base_url' or 'url'"
        )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_no_destructive_actions(spec_path: Path, spec: dict[str, Any]) -> None:
    """No DELETE methods allowed. POST must have safe: true in official registry."""
    violations = validate_action_safety(spec)
    assert not violations, (
        f"{spec_path.name}: safety violations found:\n" + "\n".join(f"  - {v}" for v in violations)
    )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_transform_or_assert(spec_path: Path, spec: dict[str, Any]) -> None:
    """Every action should have at least a transform or assert block."""
    protocol = spec.get("protocol", "")
    if protocol in ("cli", "command", "tcp", "mcp", "skill"):
        pytest.skip(f"{protocol} specs don't use action-level transform/assert")

    actions = spec.get("actions", [])
    missing: list[str] = []
    for action in actions:
        action_name = action.get("name", "<unnamed>")
        has_transform = "transform" in action
        has_assert = "assert" in action
        if not has_transform and not has_assert:
            missing.append(action_name)

    if missing:
        import warnings
        warnings.warn(
            f"{spec_path.name}: actions without transform or assert: {', '.join(missing)}",
            stacklevel=1,
        )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_valid_category(spec_path: Path, spec: dict[str, Any]) -> None:
    """Category must be from the known list of valid categories."""
    category = spec.get("category")
    assert category is not None, f"{spec_path.name}: missing 'category'"
    assert category in VALID_CATEGORIES, (
        f"{spec_path.name}: invalid category '{category}'. "
        f"Valid categories: {sorted(VALID_CATEGORIES)}"
    )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_valid_protocol(spec_path: Path, spec: dict[str, Any]) -> None:
    """Protocol must be one of the recognized protocol types."""
    protocol = spec.get("protocol")
    assert protocol is not None, f"{spec_path.name}: missing 'protocol'"
    assert protocol in VALID_PROTOCOLS, (
        f"{spec_path.name}: invalid protocol '{protocol}'. "
        f"Valid protocols: {sorted(VALID_PROTOCOLS)}"
    )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_tags_exist(spec_path: Path, spec: dict[str, Any]) -> None:
    """Tags array must be present and contain at least one tag."""
    tags = spec.get("tags")
    assert tags is not None, f"{spec_path.name}: missing 'tags'"
    assert isinstance(tags, list), f"{spec_path.name}: 'tags' must be a list"
    assert len(tags) > 0, f"{spec_path.name}: 'tags' list is empty"
    for tag in tags:
        assert isinstance(tag, str), (
            f"{spec_path.name}: all tags must be strings, got {type(tag).__name__}"
        )


@pytest.mark.parametrize("spec_path,spec", SPEC_PARAMS)
def test_composite_schema(spec_path: Path, spec: dict[str, Any]) -> None:
    """Composite specs must have valid step DAGs with no cycles or broken references."""
    if spec.get("protocol") != "composite":
        pytest.skip("Not a composite spec")
    errors = validate_composite_schema(spec)
    assert not errors, (
        f"{spec_path.name}: composite schema errors:\n" + "\n".join(f"  - {e}" for e in errors)
    )
