# Contributing to the clictl Toolbox

Thanks for contributing a tool spec. This guide covers the format, requirements, and process.

## Adding a Tool

### 1. Pick the right directory

All specs live under `{first-letter}/{tool-name}/` where `{first-letter}` is the first character of the tool name. For example, a tool named `open-meteo` goes in `o/open-meteo/open-meteo.yaml`.

### 2. Create the spec file

Name the file `<tool-name>.yaml` using kebab-case.

```yaml
spec: "1.0"
name: my-tool
description: Clear, one-line description of what it does
version: "1.0"
category: utilities
tags: [api, utility, example]

server:
  type: http
  url: https://api.example.com
  timeout: 15s

auth:
  env: MY_TOOL_API_KEY
  header: Authorization
  value: "Bearer ${MY_TOOL_API_KEY}"

instructions: |
  When to use this tool and what to watch out for.

actions:
  - name: get-data
    description: What this action does
    path: /data
    params:
      - name: query
        required: true
        example: "search term"
    response:
      example: |
        [{"id": 1, "name": "Example"}]
    assert:
      - type: status
        values: [200]
    transform:
      - type: json
        select: [id, name]
```

### 3. Add marketplace fields (optional but encouraged)

```yaml
pricing:
  model: free             # free, freemium, paid, contact
  url: https://example.com/pricing

privacy:
  local: true             # For CLI tools that don't send data externally
```

### 4. Submit a PR

- One tool per PR
- Test with `clictl info <name>` if possible
- Set `pricing.model` honestly
- If your spec uses transforms, test them: `clictl run <tool> <action> --raw | clictl transform --file your-transforms.yaml`

## Spec Types

### REST API

Uses `server.type: http` with actions that define `method`, `url`, and `path` directly on each action.

```yaml
server:
  type: http
  url: https://api.example.com

actions:
  - name: search
    description: Search for items
    path: /search
    params:
      - name: q
        required: true
    assert:
      - type: status
        values: [200]
    transform:
      - type: json
        select: [name, status]
```

### CLI Wrapper

Uses `server.type: command` with actions that have a `run` field.

```yaml
server:
  type: command
  shell: bash
  requires:
    - name: jq
      check: "jq --version"
      url: https://jqlang.github.io/jq/

actions:
  - name: filter
    description: Filter JSON with a jq expression
    output: json
    run: "echo '{{input}}' | jq '{{filter}}'"
    params:
      - name: input
        required: true
      - name: filter
        required: true
        example: ".[] | {name, id}"
```

### MCP Server

Uses `server.type: stdio` (or `http` for remote). Actions can be static, dynamic, or both.

```yaml
server:
  type: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/home"]

actions:
  discover: true
  static:
    - name: read_file
      description: Read file contents
      params:
        - name: path
          required: true

deny:
  - execute_command
  - delete_file

transforms:
  "*":
    - type: truncate
      max_length: 16000
```

### Skill

No `server` or `actions` blocks. Uses `source` to point to skill files. The file list and SHA256 hashes are auto-computed by `sync_registry` after merge, so you only need `repo` and `path`.

```yaml
name: my-skill
description: What this skill does
version: "1.0"
category: productivity
tags: [skill, example]

source:
  repo: myorg/my-repo
  path: skills/my-skill

sandbox:
  bash_allow: [python3]
  filesystem:
    read: ["**/*.py"]
```

For the full skill contribution workflow, see [Adding Skills](docs/ADDING_SKILLS.md). For the complete spec field reference, see [Spec Format](docs/SPEC_FORMAT.md).

## Requirements

- `name`: unique, kebab-case
- `description`: clear one-liner
- `version`: quoted string (e.g., `"1.0"`)
- `category`: one of the standard categories
- `tags`: at least 2-3 relevant search tags
- At least one action with a working endpoint (for API/CLI specs)
- No hardcoded credentials (use `auth.env` for vault references)
- Prefer public, stable APIs
- Actions that change state must set `mutable: true`
- Every action should have `assert` and `transform` blocks

## Auth

Use the template model. `env` names the vault key. `value` is what gets sent.

```yaml
# Bearer token
auth:
  env: GITHUB_TOKEN
  header: Authorization
  value: "Bearer ${GITHUB_TOKEN}"

# API key in custom header
auth:
  env: API_KEY
  header: x-api-key
  value: "${API_KEY}"

# No auth: omit the auth block entirely
```

Never hardcode secrets. The `${KEY}` syntax references vault keys that the user sets with `clictl vault set`.

## Transforms

Every action should transform raw API responses into clean, focused output.

```yaml
transform:
  # Extract nested data
  - type: json
    extract: "$.data.items"
    select: [name, status, url]
    rename: { stargazers_count: stars }

  # Limit output size
  - type: truncate
    max_items: 20
```

See [Spec Reference](docs/spec-reference.md) for the complete transform catalog.

## Questions?

Open an issue at [github.com/clictl/toolbox](https://github.com/clictl/toolbox/issues).

---

clictl is a [Soap Bucket LLC](https://www.soapbucket.org) project.
