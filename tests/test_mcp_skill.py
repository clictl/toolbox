"""Tests specific to MCP and Skill protocol specs in the registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import (
    all_spec_files,
    load_spec,
    spec_id,
)


def _mcp_specs() -> list[pytest.param]:
    """Collect all MCP protocol specs."""
    params: list[pytest.param] = []
    for path in all_spec_files():
        try:
            data = load_spec(path)
            if data.get("protocol") == "mcp":
                params.append(pytest.param(path, data, id=spec_id(path)))
        except Exception:
            continue
    return params


def _skill_specs() -> list[pytest.param]:
    """Collect all skill protocol specs."""
    params: list[pytest.param] = []
    for path in all_spec_files():
        try:
            data = load_spec(path)
            if data.get("protocol") == "skill":
                params.append(pytest.param(path, data, id=spec_id(path)))
        except Exception:
            continue
    return params


MCP_PARAMS = _mcp_specs()
SKILL_PARAMS = _skill_specs()


# --- MCP Spec Tests ---


@pytest.mark.parametrize("spec_path,spec", MCP_PARAMS)
def test_mcp_has_transport_or_package(spec_path: Path, spec: dict[str, Any]) -> None:
    """MCP specs must have a transport block or a package block."""
    has_transport = "transport" in spec
    has_package = "package" in spec
    assert has_transport or has_package, (
        f"{spec_path.name}: MCP spec missing both 'transport' and 'package'"
    )
    if has_transport:
        transport = spec["transport"]
        assert "type" in transport, f"{spec_path.name}: transport missing 'type'"
        assert transport["type"] in ("stdio", "http", "sse"), (
            f"{spec_path.name}: transport type must be 'stdio', 'http', or 'sse', got '{transport['type']}'"
        )
    if has_package:
        package = spec["package"]
        assert "name" in package, f"{spec_path.name}: package missing 'name'"
        assert "registry" in package or "manager" in package, (
            f"{spec_path.name}: package must have 'registry' or 'manager'"
        )


@pytest.mark.parametrize("spec_path,spec", MCP_PARAMS)
def test_mcp_stdio_has_command(spec_path: Path, spec: dict[str, Any]) -> None:
    """stdio MCP specs must have a command field."""
    transport = spec.get("transport", {})
    if transport.get("type") != "stdio":
        pytest.skip("Not a stdio transport")
    assert "command" in transport, (
        f"{spec_path.name}: stdio transport missing 'command'"
    )


@pytest.mark.parametrize("spec_path,spec", MCP_PARAMS)
def test_mcp_http_has_url(spec_path: Path, spec: dict[str, Any]) -> None:
    """HTTP MCP specs must have a url field."""
    transport = spec.get("transport", {})
    if transport.get("type") not in ("http", "sse"):
        pytest.skip("Not an HTTP/SSE transport")
    assert "url" in transport, (
        f"{spec_path.name}: HTTP transport missing 'url'"
    )


@pytest.mark.parametrize("spec_path,spec", MCP_PARAMS)
def test_mcp_tools_config(spec_path: Path, spec: dict[str, Any]) -> None:
    """MCP specs with a tools block must have valid expose config."""
    tools = spec.get("tools")
    if tools is None:
        pytest.skip("No tools block (defaults to expose: all)")
    expose = tools.get("expose")
    if expose is not None:
        if isinstance(expose, str):
            assert expose == "all", (
                f"{spec_path.name}: tools.expose string must be 'all', got '{expose}'"
            )
        elif isinstance(expose, list):
            for i, entry in enumerate(expose):
                assert "name" in entry, (
                    f"{spec_path.name}: tools.expose[{i}] missing 'name'"
                )
        else:
            pytest.fail(
                f"{spec_path.name}: tools.expose must be 'all' or a list, got {type(expose).__name__}"
            )


@pytest.mark.parametrize("spec_path,spec", MCP_PARAMS)
def test_mcp_deny_list(spec_path: Path, spec: dict[str, Any]) -> None:
    """MCP tools deny list entries must have names."""
    tools = spec.get("tools")
    if tools is None:
        pytest.skip("No tools block")
    deny = tools.get("deny", [])
    for i, entry in enumerate(deny):
        assert "name" in entry, (
            f"{spec_path.name}: tools.deny[{i}] missing 'name'"
        )


@pytest.mark.parametrize("spec_path,spec", MCP_PARAMS)
def test_mcp_destructive_tools_marked(spec_path: Path, spec: dict[str, Any]) -> None:
    """MCP tools that are destructive should be explicitly marked."""
    tools = spec.get("tools")
    if tools is None:
        pytest.skip("No tools block")
    expose = tools.get("expose")
    if not isinstance(expose, list):
        pytest.skip("expose: all, no individual tool config")
    # Just verify structure; we can't validate destructive marking automatically
    for entry in expose:
        if entry.get("destructive"):
            assert "name" in entry, "Destructive tool entry must have a name"


# --- Skill Spec Tests ---


@pytest.mark.parametrize("spec_path,spec", SKILL_PARAMS)
def test_skill_has_source(spec_path: Path, spec: dict[str, Any]) -> None:
    """Skill specs must have a source block."""
    assert "source" in spec, f"{spec_path.name}: skill spec missing 'source'"
    source = spec["source"]
    assert "type" in source, f"{spec_path.name}: source missing 'type'"
    assert source["type"] in ("github", "npm", "inline"), (
        f"{spec_path.name}: source type must be 'github', 'npm', or 'inline', got '{source['type']}'"
    )


@pytest.mark.parametrize("spec_path,spec", SKILL_PARAMS)
def test_skill_github_source(spec_path: Path, spec: dict[str, Any]) -> None:
    """GitHub-sourced skills must have repo and path fields."""
    source = spec.get("source", {})
    if source.get("type") != "github":
        pytest.skip("Not a GitHub source")
    assert "repo" in source, f"{spec_path.name}: GitHub source missing 'repo'"
    assert "path" in source, f"{spec_path.name}: GitHub source missing 'path'"


@pytest.mark.parametrize("spec_path,spec", SKILL_PARAMS)
def test_skill_has_platforms(spec_path: Path, spec: dict[str, Any]) -> None:
    """Skill specs must declare platform compatibility."""
    platforms = spec.get("platforms")
    assert platforms is not None, f"{spec_path.name}: skill spec missing 'platforms'"
    assert isinstance(platforms, list), f"{spec_path.name}: 'platforms' must be a list"
    assert len(platforms) > 0, f"{spec_path.name}: 'platforms' list is empty"
    for i, p in enumerate(platforms):
        assert "name" in p, f"{spec_path.name}: platforms[{i}] missing 'name'"


@pytest.mark.parametrize("spec_path,spec", SKILL_PARAMS)
def test_skill_valid_platforms(spec_path: Path, spec: dict[str, Any]) -> None:
    """Platform names should be from the known set."""
    valid_platforms = {"claude-code", "cursor", "vscode", "codex", "windsurf", "gemini"}
    platforms = spec.get("platforms", [])
    for p in platforms:
        name = p.get("name", "")
        assert name in valid_platforms, (
            f"{spec_path.name}: unknown platform '{name}'. "
            f"Valid: {sorted(valid_platforms)}"
        )
