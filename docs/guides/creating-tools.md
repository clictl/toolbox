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
name: my-tool
version: "1.0.0"
description: A short description of what this tool does
category: developer-tools
protocol: rest

connection:
  base_url: https://api.example.com

auth:
  type: api_key
  key_env: MY_TOOL_API_KEY
  inject:
    location: header
    param: Authorization
    prefix: "Bearer "

actions:
  - name: list-items
    description: List all items
    method: GET
    path: /items
    params:
      - name: limit
        type: int
        required: false
        description: Maximum number of items to return
        in: query
```

**Required fields:**

| Field | Description |
|-------|-------------|
| `name` | Unique tool identifier (lowercase, hyphens allowed) |
| `version` | Semantic version string |
| `description` | One-line summary of the tool |
| `category` | One of: ai, data, developer-tools, devops, security, communication, finance, productivity, commerce, media, science, location, health, monitoring, social, iot, other |
| `protocol` | `rest`, `mcp`, `cli`, or `skill` |

For the full spec format reference, see [Spec Format](https://github.com/clictl/toolbox/blob/main/SPEC_SCHEMA.md).

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
namespace: "@mycompany"
spec_paths:
  - "my-tool/"
```

Then add a GitHub Actions workflow or GitLab CI job to run `clictl toolbox sync` on push. See the [Toolbox Sync section](../../cli/README.md#toolbox-sync) in the CLI README for a complete CI example.

## Step 6: Verify the tool appears

After the sync completes, your tool should appear in My Toolbox:

```bash
clictl search my-tool
clictl info my-tool
clictl run my-tool list-items
```

In the web UI, navigate to Settings > My Toolbox to see your tool listed with a "Linked" badge.

## Next steps

- [Publishing Tools](publishing-tools.md) - Share your tool with the community
- [Securing Secrets](securing-secrets.md) - Use `vault://` for API keys instead of plaintext
- [Spec Format](https://github.com/clictl/toolbox/blob/main/SPEC_SCHEMA.md) - Full reference for all spec fields, transforms, and assertions
