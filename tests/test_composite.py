"""Live integration tests for composite specs.

Discovers composite specs with a `test` block in their YAML, executes each
step against real APIs, and validates per-step and final output assertions.

Run:
    pytest tests/test_composite.py -v
    pytest tests/test_composite.py -v -k github
"""

from __future__ import annotations

import json
import os
import re
from collections import deque
from pathlib import Path
from typing import Any

import pytest
import requests

from conftest import REGISTRY_PATH, all_spec_files, load_spec, spec_id

TIMEOUT = 30


# ---------------------------------------------------------------------------
# Template resolution (mirrors Go CLI's resolveTemplate)
# ---------------------------------------------------------------------------

_TEMPLATE_RE = re.compile(r"\{\{([^}]+)\}\}")


def _extract_json_field(data: Any, field_path: str) -> Any:
    """Navigate a dotted/bracketed field path into parsed JSON data.

    Supports: "field", "field.nested", "[0].field", "field[0].nested"
    """
    parts: list[str] = []
    for segment in re.split(r"\.(?![^\[]*\])", field_path):
        # Split array indices: "output[0]" -> ["output", "0"]
        for sub in re.split(r"\[(\d+)\]", segment):
            if sub:
                parts.append(sub)

    current = data
    for part in parts:
        if current is None:
            return None
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (IndexError, ValueError):
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def resolve_template(
    tmpl: str,
    params: dict[str, str],
    step_results: dict[str, Any],
) -> str:
    """Replace {{...}} expressions in a template string."""

    def _replace(match: re.Match) -> str:
        expr = match.group(1).strip()

        # {{params.X}}
        if expr.startswith("params."):
            key = expr[len("params."):]
            return str(params.get(key, match.group(0)))

        # {{env.VAR}}
        if expr.startswith("env."):
            var = expr[len("env."):]
            return os.environ.get(var, match.group(0))

        # {{steps.X.output...}}
        if expr.startswith("steps."):
            rest = expr[len("steps."):]
            dot_idx = rest.find(".")
            if dot_idx == -1:
                return match.group(0)
            step_id = rest[:dot_idx]
            field_path = rest[dot_idx + 1:]

            if step_id not in step_results:
                return match.group(0)

            result = step_results[step_id]

            if field_path == "output":
                if isinstance(result, (dict, list)):
                    return json.dumps(result)
                return str(result)

            if field_path.startswith("output."):
                sub_path = field_path[len("output."):]
                value = _extract_json_field(result, sub_path)
                if value is None:
                    return match.group(0)
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                return str(value)

            if field_path.startswith("output["):
                sub_path = field_path[len("output"):]
                value = _extract_json_field(result, sub_path)
                if value is None:
                    return match.group(0)
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                return str(value)

        return match.group(0)

    return _TEMPLATE_RE.sub(_replace, tmpl)


# ---------------------------------------------------------------------------
# Spec resolution (for tool+action references)
# ---------------------------------------------------------------------------

_spec_cache: dict[str, dict[str, Any]] = {}


def _load_registry_spec(tool_name: str) -> dict[str, Any] | None:
    """Find and load a spec by name from the registry directory."""
    if tool_name in _spec_cache:
        return _spec_cache[tool_name]

    for yaml_path in REGISTRY_PATH.rglob("*.yaml"):
        if yaml_path.name.startswith(".") or yaml_path.name == "registry.yaml":
            continue
        # Quick check: filename often matches tool name
        if yaml_path.stem == tool_name:
            spec = load_spec(yaml_path)
            if spec.get("name") == tool_name:
                _spec_cache[tool_name] = spec
                return spec

    # Fallback: scan all specs
    for yaml_path in REGISTRY_PATH.rglob("*.yaml"):
        if yaml_path.name.startswith(".") or yaml_path.name == "registry.yaml":
            continue
        try:
            spec = load_spec(yaml_path)
            if spec.get("name") == tool_name:
                _spec_cache[tool_name] = spec
                return spec
        except Exception:
            continue

    return None


def _resolve_tool_action_url(
    step: dict[str, Any],
    params: dict[str, str],
    step_results: dict[str, Any],
) -> tuple[str, str, dict[str, str]]:
    """Resolve a tool+action step to (method, url, headers).

    Looks up the referenced spec in the registry, finds the action,
    and builds the full URL from base_url + path.
    """
    tool_name = step["tool"]
    action_name = step["action"]

    spec = _load_registry_spec(tool_name)
    if not spec:
        raise ValueError(f"Cannot resolve tool '{tool_name}' from registry")

    base_url = (spec.get("connection") or {}).get("base_url", "")
    default_headers = (spec.get("connection") or {}).get("headers", {})

    action = None
    for a in spec.get("actions", []):
        if a.get("name") == action_name:
            action = a
            break

    if not action:
        raise ValueError(f"Action '{action_name}' not found in tool '{tool_name}'")

    method = action.get("method", "GET")
    path = action.get("path", "")

    # Resolve step params into the action's path params
    step_params = step.get("params", {})
    resolved_params: dict[str, str] = {}
    for key, val in step_params.items():
        resolved_params[key] = resolve_template(str(val), params, step_results)

    # Substitute path params and mustache conditionals
    resolved_path = path
    query_params: dict[str, str] = {}

    # Handle mustache-style conditionals: {{#param}}...{{/param}}
    def _resolve_mustache(m: re.Match) -> str:
        param_name = m.group(1)
        inner = m.group(2)
        val = resolved_params.get(param_name, "")
        if val:
            # Resolve any {{param}} refs inside the block
            return re.sub(r"\{\{" + re.escape(param_name) + r"\}\}", val, inner)
        return ""

    resolved_path = re.sub(
        r"\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}", _resolve_mustache, resolved_path
    )

    for param_def in action.get("params", []):
        pname = param_def.get("name", "")
        location = param_def.get("in", "query")
        val = resolved_params.get(pname, param_def.get("default", ""))
        if not val:
            continue
        if location == "path":
            resolved_path = resolved_path.replace(f"{{{{{pname}}}}}", str(val))
        else:
            query_params[pname] = str(val)

    url = f"{base_url}{resolved_path}"

    # Add any remaining params as query params (non-path params)
    for key, val in resolved_params.items():
        if f"{{{{{key}}}}}" not in path and key not in query_params:
            query_params[key] = val

    # Inject auth if configured via env var
    auth_config = spec.get("auth", {})
    if isinstance(auth_config, list):
        auth_config = auth_config[0] if auth_config else {}
    key_env = auth_config.get("key_env", "")
    if key_env:
        api_key = os.environ.get(key_env, "")
        if api_key:
            inject = auth_config.get("inject", {})
            location = inject.get("location", "header")
            key_name = inject.get("key", "Authorization")
            prefix = inject.get("prefix", "")
            if location == "header":
                default_headers[key_name] = f"{prefix}{api_key}"
            elif location == "query":
                query_params[key_name] = f"{prefix}{api_key}"

    return method, url, default_headers, query_params


# ---------------------------------------------------------------------------
# Topological sort
# ---------------------------------------------------------------------------


def topo_sort(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort steps by dependency order using Kahn's algorithm."""
    step_map = {s["id"]: s for s in steps}
    in_degree: dict[str, int] = {s["id"]: 0 for s in steps}
    adj: dict[str, list[str]] = {s["id"]: [] for s in steps}

    for step in steps:
        for dep in step.get("depends_on", []):
            adj[dep].append(step["id"])
            in_degree[step["id"]] += 1

    queue: deque[str] = deque(sid for sid, deg in in_degree.items() if deg == 0)
    result: list[dict[str, Any]] = []

    while queue:
        sid = queue.popleft()
        result.append(step_map[sid])
        for neighbor in adj[sid]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(steps):
        raise ValueError("Cycle detected in step dependencies")

    return result


# ---------------------------------------------------------------------------
# Step execution
# ---------------------------------------------------------------------------


def execute_step(
    step: dict[str, Any],
    params: dict[str, str],
    step_results: dict[str, Any],
    session: requests.Session,
    timeout: int = TIMEOUT,
) -> tuple[int, Any]:
    """Execute a single composite step. Returns (status_code, parsed_output)."""
    if "method" in step and "url" in step:
        # Direct HTTP step
        method = step["method"]
        raw_url = resolve_template(step["url"], params, step_results)

        headers = {}
        for key, val in step.get("headers", {}).items():
            headers[key] = resolve_template(str(val), params, step_results)

        # Resolve params as query params
        query_params: dict[str, str] = {}
        for key, val in step.get("params", {}).items():
            query_params[key] = resolve_template(str(val), params, step_results)

        resp = session.request(
            method, raw_url, headers=headers, params=query_params or None, timeout=timeout
        )
        try:
            body = resp.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            body = resp.text
        return resp.status_code, body

    elif "tool" in step and "action" in step:
        # Cross-tool reference - resolve from registry
        method, url, default_headers, query_params = _resolve_tool_action_url(
            step, params, step_results
        )
        headers = dict(default_headers)
        # Step-level headers override
        for key, val in step.get("headers", {}).items():
            headers[key] = resolve_template(str(val), params, step_results)

        resp = session.request(
            method, url, headers=headers, params=query_params or None, timeout=timeout
        )
        try:
            body = resp.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            body = resp.text
        return resp.status_code, body

    elif "action" in step:
        # Same-tool action reference - not supported in test runner
        pytest.skip(f"Step '{step.get('id')}' uses same-tool action reference (not yet supported)")

    else:
        raise ValueError(f"Step '{step.get('id')}' has no method+url or tool+action")


# ---------------------------------------------------------------------------
# Test discovery and execution
# ---------------------------------------------------------------------------


def _discover_composite_tests() -> list[pytest.param]:
    """Find all composite specs with test blocks and build pytest params."""
    params: list[pytest.param] = []

    for spec_path in all_spec_files():
        try:
            spec = load_spec(spec_path)
        except Exception:
            continue

        if spec.get("protocol") != "composite":
            continue

        test_block = spec.get("test")
        if not test_block:
            continue

        for test_case in test_block.get("actions", []):
            action_name = test_case.get("action", "unknown")
            test_id = f"{spec_id(spec_path)}::{action_name}"
            params.append(pytest.param(spec_path, spec, test_case, id=test_id))

    return params


COMPOSITE_TEST_PARAMS = _discover_composite_tests()


@pytest.fixture(scope="module")
def http_session() -> requests.Session:
    """Reusable HTTP session for composite tests."""
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


@pytest.mark.parametrize("spec_path,spec,test_case", COMPOSITE_TEST_PARAMS)
def test_composite_action(
    spec_path: Path,
    spec: dict[str, Any],
    test_case: dict[str, Any],
    http_session: requests.Session,
) -> None:
    """Execute a composite action's test case against live APIs."""
    action_name = test_case["action"]
    test_params = test_case.get("params", {})
    test_timeout = test_case.get("timeout", TIMEOUT)
    step_expectations = {s["id"]: s for s in test_case.get("steps", [])}
    expect = test_case.get("expect", {})

    # Check for required env vars
    skip_env = test_case.get("skip_unless_env")
    if skip_env and not os.environ.get(skip_env):
        pytest.skip(f"Skipping: {skip_env} not set")

    # Find the action
    action = None
    for a in spec.get("actions", []):
        if a.get("name") == action_name:
            action = a
            break
    assert action is not None, f"Action '{action_name}' not found in {spec_path.name}"
    assert action.get("composite"), f"Action '{action_name}' is not composite"

    steps = action.get("steps", [])
    sorted_steps = topo_sort(steps)

    # Execute steps
    step_results: dict[str, Any] = {}
    step_statuses: dict[str, int] = {}

    for step in sorted_steps:
        sid = step.get("id", "")
        on_error = step.get("on_error", "fail")

        try:
            status_code, output = execute_step(
                step, test_params, step_results, http_session, test_timeout
            )
            step_statuses[sid] = status_code
            step_results[sid] = output
        except Exception as exc:
            if on_error == "skip":
                continue
            elif on_error == "continue":
                step_results[sid] = {}
                continue
            else:
                raise AssertionError(f"Step '{sid}' failed: {exc}") from exc

    # Validate per-step expectations
    for sid, exp in step_expectations.items():
        if sid not in step_statuses:
            if exp.get("optional"):
                continue
            pytest.fail(f"Step '{sid}' was not executed")

        if "expect_status" in exp:
            assert step_statuses[sid] == exp["expect_status"], (
                f"Step '{sid}': expected status {exp['expect_status']}, got {step_statuses[sid]}"
            )

        if "expect_fields" in exp:
            output = step_results.get(sid, {})
            if isinstance(output, list) and len(output) > 0:
                output = output[0]
            for field in exp["expect_fields"]:
                assert field in output, (
                    f"Step '{sid}': missing expected field '{field}' in output. "
                    f"Keys: {list(output.keys()) if isinstance(output, dict) else 'not a dict'}"
                )

    # Validate final output expectations
    if expect.get("output_contains"):
        # Build final output by applying action transform template
        action_transform = action.get("transform", [])
        final_output = ""
        for t in action_transform:
            if "template" in t:
                final_output = resolve_template(
                    t["template"], test_params, step_results
                )

        for expected_str in expect["output_contains"]:
            assert expected_str in final_output, (
                f"Expected '{expected_str}' in final output but not found.\n"
                f"Output preview: {final_output[:500]}"
            )

    if expect.get("output_fields"):
        # Check that terminal step output has expected fields
        terminal_step = sorted_steps[-1]
        terminal_output = step_results.get(terminal_step["id"], {})
        for field in expect["output_fields"]:
            assert field in terminal_output, (
                f"Missing expected field '{field}' in terminal step output"
            )
