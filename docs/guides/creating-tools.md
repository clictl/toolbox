# Creating Tools

This guide walks through creating a tool spec, connecting it to clictl, and making it available in your workspace.

## Prerequisites

- clictl installed (`curl -fsSL https://download.clictl.dev/install.sh | bash`)
- A git repository (GitHub or GitLab) where you will store the spec
- A clictl account with an active workspace (for connecting the repo)

## Step 1: Scaffold the spec

Run `clictl init` in your repository to create a new tool spec interactively:

```bash
cd my-tools-repo
clictl init my-tool
```

This creates `my-tool/my-tool.yaml` with a template you can fill in. If you have an OpenAPI spec for the API you want to wrap, you can generate the tool spec from it:

```bash
clictl init --from https://api.example.com/openapi.json
```

## Step 2: Edit the YAML spec

Open the generated file and fill in the required fields:

```yaml
spec: "1.0"
name: my-tool
version: "1.0.0"
description: A short description of what this tool does
category: developer
tags: [api, data, example]

server:
  type: http
  url: https://api.example.com

auth:
  env: MY_TOOL_API_KEY
  header: Authorization
  value: "Bearer ${MY_TOOL_API_KEY}"

actions:
  - name: list-items
    description: List all items
    output: json
    path: /items
    params:
      - name: limit
        type: int
        description: Maximum number of items to return
        default: "25"
        example: "10"
    transform:
      - type: json
        extract: "$.data"
        select: [id, name, status]
      - type: truncate
        max_items: 20
```

**Required fields:**

| Field | Description |
|-------|-------------|
| `name` | Unique tool identifier (lowercase, hyphens allowed) |
| `version` | Version string (major.minor) |
| `description` | One-line summary of the tool |
| `category` | Category slug (developer, data, ai, devops, security, etc.) |
| `tags` | 3-8 search tags |
| `server` | How to connect (type: http, stdio, or command) |

For the full spec format reference, see [Spec Reference](../spec-reference.md).

## Step 3: Validate the spec

Before committing, test that the spec is valid and the API responds correctly:

```bash
clictl test my-tool
```

This sends a request using the spec's first action and checks that the response matches any configured assertions.

## Step 4: Commit and push

```bash
git add my-tool/my-tool.yaml
git commit -m "Add my-tool spec"
git push origin main
```

## Step 5: Connect your repo as a toolbox

There are two ways to connect your repository:

**Option A: Web UI**

1. Go to Settings > Toolboxes in your workspace
2. Click "Add Toolbox"
3. Paste your repository URL or browse connected GitHub/GitLab repos
4. Click "Add"

The system syncs automatically and imports your tool specs.

**Option B: CLI with CI sync**

For public repos, add `clictl toolbox sync` to your CI pipeline. Create a `.clictl.yaml` in the repo root:

```yaml
workspace: myworkspace
namespace: mycompany
spec_paths:
  - "my-tool/"
```

The `namespace` field sets the default publisher namespace for all specs in the toolbox. Individual specs can override it with their own `namespace` field. Namespace is a bare string (e.g., `mycompany`). Tools are referenced as `mycompany/my-tool` when qualified.

Then add a GitHub Actions workflow or GitLab CI job to run `clictl toolbox sync` on push.

## Step 6: Verify the tool appears

After the sync completes, your tool should appear in My Toolbox:

```bash
clictl search my-tool
clictl info my-tool
clictl run my-tool list-items
```

In the web UI, navigate to Settings > My Toolbox to see your tool listed with a "Linked" badge.

## Example Specs

### REST API (no auth)

```yaml
spec: "1.0"
name: open-meteo
description: Free weather forecast API
version: "1.0"
category: weather
tags: [weather, forecast, temperature]

server:
  type: http
  url: https://api.open-meteo.com/v1

actions:
  - name: current
    description: Get current weather for a location
    path: /forecast
    params:
      - name: latitude
        type: float
        required: true
        example: "51.5"
      - name: longitude
        type: float
        required: true
        example: "-0.12"
      - name: current
        default: "temperature_2m,wind_speed_10m"
```

### CLI wrapper

```yaml
spec: "1.0"
name: docker
description: Docker container management
version: "1.0"
category: devops
tags: [docker, containers]

server:
  type: command
  shell: bash
  requires:
    - name: docker
      check: "docker --version"
      url: https://docs.docker.com/get-docker/

actions:
  - name: ps
    description: List running containers
    run: "docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}'"
    output: text
```

### MCP server

```yaml
spec: "1.0"
name: filesystem-mcp
description: Local filesystem access via MCP
version: "1.0"
category: developer
tags: [filesystem, files, mcp]

server:
  type: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/home"]
  requires:
    - name: node
      check: "node --version"

actions:
  - name: read_file
    description: Read file contents
    output: text
    params:
      - name: path
        required: true
        example: "./README.md"
```

## Next Steps

- [Spec Reference](../spec-reference.md) - full field reference
- [Transforms Guide](../transforms.md) - transform pipeline recipes
- [Quick Reference](../quick-reference.md) - one-page cheat sheet
