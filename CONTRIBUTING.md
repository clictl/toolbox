# Contributing to the clictl Toolbox

Thanks for contributing a tool spec. This guide covers the format, requirements, and process.

## Which protocol should I use?

```
Wrapping a REST API?              -> protocol: http
Registering an MCP server?        -> protocol: mcp
Adding agent skills/instructions? -> protocol: skill
Scraping a website for agents?    -> protocol: website
Wrapping a CLI tool?              -> protocol: command
```

## Adding a Tool

### 1. Pick the right directory

Specs live under `toolbox/{first-letter}/{tool-name}/{tool-name}.yaml`. For example, `open-meteo` goes in `toolbox/o/open-meteo/open-meteo.yaml`.

### 2. Create the spec file

**HTTP API:**

```yaml
spec: "1.0"
name: my-api
protocol: http
description: What this API does
version: "1.0"
category: utilities
tags: [api, utility]

server:
  url: https://api.example.com

auth:
  env: MY_API_KEY
  header: "Authorization: Bearer ${MY_API_KEY}"

actions:
  - name: get-data
    description: What this action does
    path: /data
    params:
      - name: query
        type: string
        required: true
    transform:
      - type: json
        select: [id, name]
      - type: truncate
        max_items: 20
```

**MCP server (npm package):**

```yaml
spec: "1.0"
name: my-mcp
protocol: mcp
description: What this MCP server does
version: "1.0"
category: developer
tags: [mcp]

package:
  registry: npm
  name: "@org/mcp-server"
  version: 1.0.0

auth:
  env: MY_TOKEN

actions:
  - name: search
    description: Search for items
    params:
      - name: query
        type: string
        required: true
```

**MCP server (pypi package):**

```yaml
spec: "1.0"
name: my-mcp
protocol: mcp
description: What this MCP server does
version: "1.0"
category: data

package:
  registry: pypi
  name: mcp-server-example
  version: 1.0.0
```

**Skill:**

```yaml
spec: "1.0"
name: my-skill
protocol: skill
description: What this skill does
version: "1.0"
category: productivity
tags: [skill]

source:
  repo: myorg/my-repo
  path: skills/my-skill
  files:
    - path: SKILL.md
```

**Website scraper:**

```yaml
spec: "1.0"
name: my-scraper
protocol: website
description: Scrape a website as markdown
version: "1.0"
category: news

server:
  url: https://example.com

actions:
  - name: get-page
    description: Get the front page
    path: /
    transform:
      - type: html_to_markdown
```

**CLI wrapper:**

```yaml
spec: "1.0"
name: my-cli
protocol: command
description: Wrap a CLI tool
version: "1.0"
category: developer

actions:
  - name: status
    description: Show status
    run: my-tool status
```

### 3. Submit a PR

- One tool per PR
- Test with `clictl info <name>` and `clictl run <name> <action>`
- Run `clictl toolbox validate` before submitting

## Auth

Use the header template format. `env` names the vault key. `header` is the full header string with `${VAR}` substitution.

```yaml
# Bearer token
auth:
  env: GITHUB_TOKEN
  header: "Authorization: Bearer ${GITHUB_TOKEN}"

# API key in custom header
auth:
  env: API_KEY
  header: "X-Api-Key: ${API_KEY}"

# Query parameter
auth:
  env: API_KEY
  param: key

# MCP env passthrough (no header needed)
auth:
  env: GITHUB_TOKEN

# No auth: omit the auth block entirely
```

Never hardcode secrets. The `${KEY}` syntax references vault keys that the user sets with `clictl vault set`.

## MCP Server Specs

For MCP specs, `actions` are metadata for search and `clictl info`. Tools are discovered from the server at runtime. You don't need to list every tool - just the important ones with good descriptions so search can find them.

Use `deny` to block dangerous tools, `allow` to whitelist specific ones, and `transforms` (keyed by tool name) to shape output.

```yaml
deny:
  - "drop_*"
  - "delete_*"

transforms:
  search_results:
    - type: truncate
      max_items: 20
```

## Transforms

Every action SHOULD transform raw API responses into clean, focused output.

```yaml
transform:
  - extract: "$.data.items"
  - type: json
    select: [name, status, url]
  - type: truncate
    max_items: 20
```

See the [Spec Reference](../cli/docs/spec.md) for the full transform catalog.

## Requirements

- `spec`: must be `"1.0"`
- `name`: unique, kebab-case
- `protocol`: one of http, mcp, skill, website, command
- `description`: clear one-liner
- `version`: quoted string (e.g., `"1.0"`)
- `category`: one of the standard categories
- `tags`: at least 2-3 relevant search tags
- No hardcoded credentials (use `auth.env` for vault references)
- Prefer public, stable APIs
- Actions that change state must set `mutable: true`

## Questions?

Open an issue at [github.com/clictl/toolbox](https://github.com/clictl/toolbox/issues).

---

clictl is a [Soap Bucket LLC](https://www.soapbucket.org) project.
