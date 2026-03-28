# Spec Schema Reference

Complete reference for writing clictl tool specs. This document is designed for AI agents to read and use when creating new specs.

## Agent Instructions

To create a new spec for the clictl registry:

1. Determine the tool type (API, CLI, or website) and pick the correct category
2. Copy the appropriate template from this document
3. Fill in all required fields
4. Add actions with params, assert, and transform
5. Save as `specs/{first-letter}/<tool-name>/<tool-name>.yaml` where `{first-letter}` is the first character of the tool name
6. Run `uv run pytest tests/test_schema_all.py -k <tool-name>` to validate

## File Location

```
registry/
  specs/{first-char}/{tool-name}/{tool-name}.yaml   # Latest version
  specs/{first-char}/{tool-name}/{tool-name}@1.0.yaml  # Pinned version (optional)
  # {first-char} is the first character of the tool name (letter or number)
```

The `{first-letter}` is the first character of the tool name. Each tool gets its own folder. For example, `open-meteo` goes in `specs/o/open-meteo/open-meteo.yaml` and `github` goes in `specs/g/github/github.yaml`.

## Spec Format Version

The `spec` field declares which version of the spec format this file uses. It is optional and defaults to `"1.0"` if omitted. clictl uses this to determine how to parse and validate the spec. Only set it explicitly when a future format version requires it.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `spec` | string | No | `"1.0"` | Spec format version (major.minor). Current version: `"1.0"`. |

## Required Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier, kebab-case (e.g., `open-meteo`, `npm-registry`) |
| `description` | string | Yes | One-line description of what the tool does. Written for agent discovery. |
| `version` | string | Yes | Spec version in major.minor format (e.g., `"1.0"`, `"2.1"`). Not semver. |
| `category` | string | Yes | Category slug from the valid list below |
| `tags` | list[string] | Yes | 3-8 relevant tags for search (e.g., `[weather, forecast, climate]`) |
| `protocol` | string | Yes | One of: `rest`, `graphql`, `grpc`, `websocket`, `website`, `cli`, `mcp`, `skill` |
| `owner_name` | string | Yes | Official company or organization name |
| `website` | string | Yes | Official URL |
| `support_url` | string | Yes | Documentation or support page URL |
| `pricing_model` | string | Yes | One of: `free`, `freemium`, `paid`, `contact` |
| `connection` | object | Yes* | Connection settings (see below). *Not required for `mcp` or `skill` protocols. |
| `auth` | list[object] | No | Authentication config array (see below). Omit if no auth required (default: none). |
| `actions` | list[object] | Yes* | At least one action. *Not required for `mcp` protocol (tools come from the server) or `skill` protocol. |
| `transport` | object | MCP only | Transport config for MCP servers (see MCP section below) |
| `tools` | object | MCP only | Tool exposure and filtering config (see MCP section below) |
| `prompts` | object | No | Prompt injection and templates for MCP servers |
| `resources` | object | No | Resource exposure config for MCP servers |
| `install_mode` | object | No | Controls how the MCP server is installed (skill, mcp, or both) |
| `source` | object | Skill only | Where to fetch the SKILL.md file (see Skill section below) |
| `platforms` | list[object] | Skill only | Platform compatibility and install paths (see Skill section below) |
| `skill_metadata` | object | No | Additional skill metadata (author, version, license) |
| `requires_tools` | list[string] | No | Tools the skill depends on (e.g., `[bash, read, write, git]`) |
| `requires_mcp` | list[string] | No | MCP servers the skill depends on (e.g., `[filesystem-server]`) |

## Optional Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `license` | string | License identifier (e.g., `MIT`, `Apache-2.0`) |
| `pricing_url` | string | Link to pricing page |
| `docs.api_reference` | string | URL to API reference docs |
| `docs.getting_started` | string | URL to quickstart guide |
| `docs.changelog` | string | URL to changelog |
| `docs.openapi` | string | URL to OpenAPI/Swagger spec |
| `rate_limit.requests_per_minute` | int | Rate limit per minute |
| `rate_limit.requests_per_day` | int | Rate limit per day |
| `rate_limit.note` | string | Human-readable rate limit description |
| `data_freshness` | string | One of: `real-time`, `hourly`, `daily`, `static` |

## Valid Categories

```
ai, cloud, communication, crypto, data, data-portal, developer, devops,
documentation, finance, geo, ip, knowledge-base, media, monitoring, news,
productivity, reference, search, security, text, weather
```

## MCP Server Specs

MCP (Model Context Protocol) specs define servers that expose tools, prompts, and resources to agents. Unlike API/CLI/website specs where actions are defined in the registry, MCP specs describe *how to connect* to a server that dynamically provides its own capabilities.

The registry adds value on top of raw MCP servers through **tool filtering**, **prompt injection**, **output transforms**, and **safety rules**.

### Transport Block (required for MCP)

Replaces `connection` for MCP specs. Supports `stdio` (local process) and `http` (remote server with streamable HTTP/SSE).

#### stdio transport (local binary)

```yaml
transport:
  type: stdio
  command: npx                            # Binary to execute
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/home"]
  env:                                    # Optional env vars passed to the process
    NODE_ENV: production
  requires:                               # Binary prerequisites (same as CLI specs)
    - name: node
      url: https://nodejs.org
      check: "node --version"
```

#### HTTP transport (remote server)

```yaml
transport:
  type: http
  url: https://mcp.example.com/sse        # Server URL (streamable HTTP or SSE)
  headers:                                # Optional default headers
    Accept: text/event-stream
  timeout: 30s
```

### Tools Block

Controls which MCP tools are exposed to agents. This is the registry's core value-add -- agents see only curated, filtered tools rather than the full server surface.

#### Expose all tools

```yaml
tools:
  expose: all
```

#### Whitelist specific tools

```yaml
tools:
  expose:
    - name: read_file
      description: "Read contents of a file"    # Override server description
    - name: list_directory
      description: "List files and folders"
    - name: write_file
      destructive: true                          # Marks tool for ACL enforcement
```

#### Expose all except denied tools

```yaml
tools:
  expose: all
  deny:
    - name: delete_file
    - name: execute_command
```

#### Tool-level output transforms

Apply transforms to individual tool outputs. Uses the same transform syntax as API actions.

```yaml
tools:
  expose: all
  tool_transforms:
    read_file:
      - truncate: { max_length: 8000 }
    search_files:
      - truncate: { max_items: 50 }
    list_directory:
      - truncate: { max_items: 100 }
```

### Prompts Block

Config-driven prompts that guide agent behavior when using this MCP server.

```yaml
prompts:
  # System-level instruction injected when this server is active
  system: |
    When using filesystem tools, always confirm with the user before
    writing or deleting files. Prefer reading over executing commands.

  # Tool-specific instructions appended to tool descriptions
  tool_instructions:
    read_file: "Prefer this over shell cat/head commands."
    write_file: "Always create a backup before overwriting existing files."

  # Prompt templates the server exposes (discoverable via MCP)
  templates:
    - name: code_review
      description: "Review code in a directory"
      arguments:
        - name: directory
          description: "Directory to review"
          required: true
```

### Resources Block

Declares what MCP resources the server exposes and how to filter them.

```yaml
resources:
  # Expose all resources from the server
  expose: all

  # Or whitelist by URI pattern
  expose:
    - uri_pattern: "file:///**/*.md"
      description: "Markdown documentation files"
    - uri_pattern: "db://users/**"
      description: "User database records"
      read_only: true

  # Resource-level transforms
  resource_transforms:
    "file://**":
      - truncate: { max_length: 10000 }
```

### Install Mode

Controls how `clictl install` exposes the MCP server.

```yaml
install_mode:
  default: skill                # skill | mcp | both
  allow_mcp: true               # Can be installed as native MCP server
  allow_skill: true             # Can be installed as proxied clictl skill
  keep_alive: 300s              # How long to keep stdio server alive between calls
```

- **skill mode**: Each MCP tool becomes a `clictl run <server> <tool>` skill. clictl proxies calls through the transform/safety pipeline.
- **mcp mode**: clictl generates native MCP client config for the target (Claude Desktop, Cursor, VS Code, etc.). Direct connection, no proxy.
- **both**: Registers native MCP and also exposes filtered skills through clictl.

### Auth for MCP

Reuses the existing auth array. For stdio, tokens are injected as env vars. For HTTP, tokens are injected as headers.

```yaml
# HTTP transport: injected as header
auth:
  - type: api_key
    key_env: MCP_SERVER_TOKEN
    inject:
      location: header
      param: Authorization
      prefix: "Bearer"

# stdio transport: injected as env var to child process
auth:
  - type: api_key
    key_env: GITHUB_TOKEN
    inject:
      location: env                        # Passes as env var to the process
      param: GITHUB_TOKEN
```

### Safety Rules for MCP

MCP specs follow the same safety model as other specs:

1. **Tools without `destructive: true`** -- always allowed
2. **Tools with `destructive: true`** -- controlled by workspace ACL rules
3. **Specs tagged `destructive`** -- all tools in the spec require ACL approval
4. **Tool deny lists** -- blocked tools are never exposed regardless of ACL

### Config Generation Targets

`clictl install <mcp-server>` generates config for the target client:

```bash
clictl install filesystem-server --target claude-desktop   # Claude Desktop
clictl install filesystem-server --target claude-code      # Claude Code
clictl install filesystem-server --target cursor           # Cursor
clictl install filesystem-server --target vscode           # VS Code
clictl install filesystem-server --target windsurf         # Windsurf
clictl install filesystem-server --target generic          # Generic JSON to stdout
```

## Skill Specs

Skill specs define SKILL.md files -- prompt-based agent capabilities following the [agentskills.io](https://agentskills.io) standard. Where MCP tools are function-based (call a function, get a result), skills are instruction-based (agent reads instructions, follows them).

Skills are markdown files with YAML frontmatter that teach agents how to perform tasks like writing commits, reviewing PRs, debugging, or designing APIs. They work across Claude Code, Cursor, VS Code, Codex CLI, Windsurf, and other platforms.

The registry adds **discovery**, **categorization**, **platform compatibility info**, and **install automation** for skills.

### Source Block (required for skill)

Defines where to fetch the SKILL.md file.

#### GitHub source

```yaml
source:
  type: github
  repo: anthropics/skills                    # GitHub org/repo
  path: skills/commit/SKILL.md              # Path within repo
  ref: main                                  # Branch or tag (optional, defaults to main)
```

#### npm source

```yaml
source:
  type: npm
  package: "@anthropic/skill-commit"         # npm package name
  path: SKILL.md                             # Path within package
```

#### Inline source (for simple skills)

```yaml
source:
  type: inline
  content: |
    ---
    name: my-skill
    description: What this skill does
    ---
    # Instructions
    When the user asks you to do X, follow these steps...
```

### Platforms Block

Declares which platforms support this skill and how to install it.

```yaml
platforms:
  - name: claude-code
    install_method: skill                    # How clictl installs it
    config_path: .claude/skills/             # Where the SKILL.md is placed
  - name: cursor
    install_method: skill
    config_path: .cursor/skills/
  - name: vscode
    install_method: copy
    config_path: .github/skills/
  - name: codex
    install_method: copy
    config_path: .codex/skills/
  - name: windsurf
    install_method: copy
    config_path: .windsurf/skills/
```

### Skill Metadata

Additional metadata that mirrors SKILL.md frontmatter for index discovery.

```yaml
skill_metadata:
  author: anthropic
  version: "1.0"
  license: Apache-2.0
```

### Dependencies

Skills can declare tool and MCP server dependencies.

```yaml
requires_tools: [bash, read, write, git]     # Agent tools the skill expects
requires_mcp: [filesystem-server]            # MCP servers the skill needs
```

### Auth for Skills

Most skills don't need auth. If a skill references an external API:

```yaml
auth:
  - type: none

# OR for skills that need API access
auth:
  - type: api_key
    key_env: GITHUB_TOKEN
    inject:
      location: env
      param: GITHUB_TOKEN
```

### Install Targets

`clictl install <skill>` copies the SKILL.md to the right platform directory:

```bash
clictl install skill-commit                          # Auto-detect platform
clictl install skill-commit --target claude-code     # ~/.claude/skills/
clictl install skill-commit --target cursor          # .cursor/skills/
clictl install skill-commit --target vscode          # .github/skills/
clictl install skill-commit --target codex           # .codex/skills/

# Install all skills in a category
clictl install --category developer --protocol skill

# Search for skills
clictl search --protocol skill --tag commit
```

## Connection Block

### API specs (protocol: rest, graphql, grpc)

```yaml
connection:
  base_url: https://api.example.com    # Required. Root URL for all actions.
  timeout: 15s                          # Optional. Request timeout (default: 30s).
  headers:                              # Optional. Default headers for every request.
    Accept: application/json
    User-Agent: clictl/1.0
```

### CLI specs (protocol: cli)

```yaml
connection:
  shell: /bin/sh
  requires:                             # Optional. clictl verifies before execution.
    - name: docker                      # Binary name to check on PATH
      url: https://docs.docker.com/get-docker/  # Install URL shown if missing
      check: "docker --version"         # Command to verify installation
```

If `requires` is omitted, clictl infers the binary from the first action's `run` field (e.g., `run: "git status"` checks for `git`).

### Website specs (protocol: website)

```yaml
connection:
  base_url: https://developer.mozilla.org
  headers:
    Accept: application/json

site:
  url: https://developer.mozilla.org
  sitemap: https://developer.mozilla.org/sitemap.xml
  content_type: documentation           # documentation, knowledge-base, data-portal
  preferred_format: markdown

access:
  method: fetch
  robots_txt: respected
```

## Authentication

Auth is an **array**. The CLI tries each entry in order and uses the first one that resolves.

### API Key (most common)

```yaml
auth:
  - type: api_key
    key_env: EXAMPLE_API_KEY               # Environment variable name
    inject:
      location: query                   # query or header
      param: appid                      # Parameter name or header name
```

### Bearer Token

```yaml
auth:
  - type: api_key
    key_env: GITHUB_TOKEN
    inject:
      location: header
      param: Authorization
      prefix: "Bearer"                  # Prefix added before the token value
```

### Custom Header

```yaml
auth:
  - type: api_key
    key_env: VT_API_KEY
    inject:
      location: header
      param: x-apikey                   # Custom header name, no prefix
```

### No Auth

```yaml
auth:
  - type: none
```

### Dual Auth (API key + OAuth fallback)

```yaml
auth:
  - type: api_key                       # Standalone users use personal token
    key_env: GITHUB_TOKEN
    inject:
      location: header
      param: Authorization
      prefix: "Bearer"
  - type: oauth2                        # Platform users get full OAuth flow
    authorization_url: https://github.com/login/oauth/authorize
    token_url: https://github.com/login/oauth/access_token
    scopes: [repo, read:user]
```

## Actions

Each action maps to one API endpoint or CLI command.

### API Action

```yaml
actions:
  - name: search                        # kebab-case identifier
    description: Search packages by keyword  # One line, for agent discovery
    method: GET                         # GET, POST, PUT, PATCH, DELETE
    path: /search                       # URL path appended to base_url
    params:                             # Input parameters
      - name: q
        type: string                    # string, integer, number, boolean, array, object
        required: true
        description: Search query
        in: query                       # query, header, path, body
      - name: limit
        type: integer
        default: "20"
        description: Max results to return
        in: query
    assert:                             # Response validation
      - status: [200]
      - exists: "$.data"
    transform:                          # Response processing
      - extract: "$.data.results"
      - select: ["name", "version", "description"]
      - truncate:
          max_items: 20
```

### CLI Action

```yaml
actions:
  - name: status
    description: Show working tree status
    run: "git status"                   # Shell command template
    params: []

  - name: log
    description: Show recent commit history
    run: "git log --oneline -n {{count}}"
    params:
      - name: count
        type: int
        default: "10"
        description: Number of commits to show
```

### POST Action (safe query)

POST actions that are semantically read-only MUST include `safe: true`:

```yaml
actions:
  - name: chat
    description: Create a chat completion
    method: POST
    safe: true                          # Required for read-only POST actions
    path: /chat/completions
    params:
      - name: model
        type: string
        required: true
        in: body
      - name: message
        type: string
        required: true
        in: body
    assert:
      - status: [200]
    transform:
      - extract: "$.choices[0].message.content"
```

## Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Parameter name |
| `type` | string | Yes | `string`, `integer`, `number`, `boolean`, `array`, `object` |
| `required` | bool | No | Whether the parameter is required (default: false) |
| `default` | string | No | Default value if not provided |
| `description` | string | Yes | What this parameter does |
| `in` | string | Yes | Where to place it: `query`, `header`, `path`, `body` |

Path parameters use `{name}` syntax:

```yaml
path: /repos/{owner}/{repo}/issues
params:
  - name: owner
    type: string
    required: true
    in: path
```

## Assertions

Validate the response before processing. Every action should have at least `status`.

```yaml
assert:
  - status: [200]                       # Accept these HTTP status codes
  - status: [200, 201]                  # Multiple accepted codes
  - exists: "$.data"                    # JSONPath field must exist
  - not_empty: "$.data.results"         # Field must not be empty/null
  - equals:                             # Field equals value
      path: "$.status"
      value: "success"
  - contains: "results"                 # Response body contains string
```

## Transforms

Process the response into agent-friendly output. Applied in order.

```yaml
transform:
  - extract: "$.data.items"             # JSONPath extraction
  - select: ["name", "status", "url"]   # Keep only these fields
  - truncate:
      max_items: 20                     # Limit array length
      max_length: 8000                  # Limit string length
  - rename:
      old_name: new_name               # Rename fields
  - template: |                         # Go template formatting
      {{range .}}
      - {{.name}}: {{.status}}
      {{end}}
  - html_to_markdown: {}               # Convert HTML to markdown
  - js: |                              # JavaScript transform (sandboxed)
      function transform(data) {
        return data.filter(function(r) { return r.score > 0.5; });
      }
```

## Pre-Request Transforms

Modify parameters before the request is sent.

```yaml
pre_transform:
  - default_params:                     # Inject default values
      format: json
      per_page: 10
  - rename_params:                      # Rename parameters
      q: query
  - template_body: |                    # Build request body from template
      {"query": "{ search(q: \"{{.q}}\") { id title } }"}
```

## Safety Rules

The registry enforces these rules:

1. **GET/HEAD/OPTIONS** - always allowed
2. **POST with `safe: true`** - allowed (for queries, inference, search)
3. **POST without `safe: true`** - allowed only if spec has auth (key-gated writes)
4. **POST without `safe: true` and without auth** - rejected
5. **DELETE and other destructive actions** - allowed, but the spec must include `destructive` in its tags
6. **CLI commands that modify state** - allowed, but the spec must include `destructive` in its tags
7. **MCP tools without `destructive: true`** - always allowed
8. **MCP tools with `destructive: true`** - controlled by workspace ACL rules
9. **MCP tools in the deny list** - never exposed regardless of ACL

Destructive actions are controlled by workspace ACL rules. Workspace security policies determine which users and agents can execute specs tagged with `destructive`.

## Complete API Template

```yaml
spec: "1.0"
name: my-api
description: One-line description of what this API does
version: "1.0"
category: developer
tags: [tag1, tag2, tag3]
protocol: rest
owner_name: Company Name
website: https://example.com
support_url: https://docs.example.com
pricing_model: freemium

docs:
  api_reference: https://docs.example.com/api

rate_limit:
  requests_per_minute: 60
  note: "Free tier limits"

connection:
  base_url: https://api.example.com
  timeout: 15s
  headers:
    Accept: application/json

auth:
  - type: api_key
    key_env: EXAMPLE_API_KEY
    inject:
      location: header
      param: Authorization
      prefix: "Bearer"

actions:
  - name: list-items
    description: List items with pagination
    method: GET
    path: /items
    params:
      - name: q
        type: string
        description: Search query
        in: query
      - name: limit
        type: integer
        default: "20"
        description: Max results
        in: query
    assert:
      - status: [200]
    transform:
      - extract: "$.data"
      - select: ["id", "name", "status"]
      - truncate:
          max_items: 20

  - name: get-item
    description: Get a specific item by ID
    method: GET
    path: /items/{id}
    params:
      - name: id
        type: string
        required: true
        description: Item ID
        in: path
    assert:
      - status: [200]
      - exists: "$.id"
    transform:
      - select: ["id", "name", "description", "status", "created_at"]
```

## Complete CLI Template

```yaml
spec: "1.0"
name: my-cli
description: What this CLI tool does
version: "1.0"
category: developer
tags: [tag1, tag2, tag3]
protocol: cli
owner_name: Tool Author
website: https://example.com
support_url: https://docs.example.com

connection:
  shell: /bin/sh
  requires:
    - name: mytool
      url: https://example.com/install
      check: "mytool --version"

auth:
  - type: none

actions:
  - name: list
    description: List all items
    run: "mytool list --format table"
    params: []

  - name: show
    description: Show details for a specific item
    run: "mytool show {{name}}"
    params:
      - name: name
        type: string
        required: true
        description: Item name
```

## Complete Website Template

```yaml
spec: "1.0"
name: my-docs
description: Documentation for X technology
version: "1.0"
category: documentation
tags: [docs, reference, tag1]
protocol: website
owner_name: Organization Name
website: https://docs.example.com
support_url: https://github.com/org/docs/issues
pricing_model: free

site:
  url: https://docs.example.com
  sitemap: https://docs.example.com/sitemap.xml
  content_type: documentation
  preferred_format: markdown

access:
  method: fetch
  robots_txt: respected

connection:
  base_url: https://docs.example.com
  headers:
    Accept: application/json

auth:
  - type: none

actions:
  - name: search
    description: Search documentation
    method: GET
    path: /api/search
    params:
      - name: q
        type: string
        required: true
        description: Search query
        in: query
    assert:
      - status: [200]
    transform:
      - extract: "$.results"
      - select: ["title", "url", "excerpt"]
      - truncate:
          max_items: 20
```

## Complete MCP Template (stdio)

```yaml
spec: "1.0"
name: my-mcp-server
description: What this MCP server does
version: "1.0"
category: developer
tags: [mcp, tag1, tag2]
protocol: mcp
owner_name: Author Name
website: https://example.com
support_url: https://github.com/org/repo/issues
pricing_model: free
license: MIT

transport:
  type: stdio
  command: npx
  args: ["-y", "@scope/mcp-server"]
  requires:
    - name: node
      url: https://nodejs.org
      check: "node --version"

auth:
  - type: none

tools:
  expose:
    - name: tool_one
      description: "What tool_one does"
    - name: tool_two
      description: "What tool_two does"
      destructive: true
  tool_transforms:
    tool_one:
      - truncate: { max_length: 8000 }

prompts:
  system: |
    Instructions for the agent when using this server.
  tool_instructions:
    tool_one: "Additional context for using tool_one."

resources:
  expose: all

install_mode:
  default: both
  allow_mcp: true
  allow_skill: true
```

## Complete MCP Template (HTTP)

```yaml
spec: "1.0"
name: my-remote-mcp
description: What this remote MCP server does
version: "1.0"
category: developer
tags: [mcp, tag1, tag2]
protocol: mcp
owner_name: Company Name
website: https://example.com
support_url: https://docs.example.com
pricing_model: freemium

transport:
  type: http
  url: https://mcp.example.com/sse
  headers:
    Accept: text/event-stream
  timeout: 30s

auth:
  - type: api_key
    key_env: MCP_SERVER_TOKEN
    inject:
      location: header
      param: Authorization
      prefix: "Bearer"

tools:
  expose: all
  deny:
    - name: dangerous_tool
  tool_transforms:
    search:
      - truncate: { max_items: 50 }

prompts:
  system: |
    Instructions for the agent when using this server.

resources:
  expose: all

install_mode:
  default: mcp
  allow_mcp: true
  allow_skill: true
```

## Complete Skill Template

```yaml
spec: "1.0"
name: my-skill
description: What this skill teaches the agent to do
version: "1.0"
category: developer
tags: [skill, tag1, tag2]
protocol: skill
owner_name: Author Name
website: https://github.com/org/repo
support_url: https://github.com/org/repo/issues
pricing_model: free
license: Apache-2.0

source:
  type: github
  repo: org/skills-repo
  path: skills/my-skill/SKILL.md
  ref: main

platforms:
  - name: claude-code
    install_method: skill
    config_path: .claude/skills/
  - name: cursor
    install_method: skill
    config_path: .cursor/skills/
  - name: vscode
    install_method: copy
    config_path: .github/skills/

skill_metadata:
  author: org-name
  version: "1.0"

auth:
  - type: none

requires_tools: [bash, read, write]
```

## Validation

After creating a spec, validate it:

```bash
# Schema validation
uv run pytest tests/test_schema_all.py -k "<tool-name>" -v

# Full test suite
uv run pytest tests/ -q
```

Common validation errors:
- Missing required fields (name, description, version, category, protocol)
- Invalid category (must be from the valid list)
- POST without `safe: true` and without auth
- DELETE method without `destructive` tag
- Missing `assert` or `transform` on actions (not required for MCP or skill specs)
- Invalid protocol
- MCP spec missing `transport` block
- MCP spec missing `tools` block
- Skill spec missing `source` block
- Skill spec missing `platforms` block
