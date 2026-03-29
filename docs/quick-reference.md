# Spec 1.0 Quick Reference

One-page cheat sheet for clictl tool specs. See [spec-reference.md](spec-reference.md) for full details.

## Minimal Spec (REST API, no auth)

```yaml
spec: "1.0"
name: my-api
description: What this API does
version: "1.0"
category: utilities
tags: [api, example]

server:
  type: http
  url: https://api.example.com

actions:
  - name: search
    description: Search for items
    request:
      method: GET
      path: /search
    params:
      - name: q
        required: true
        example: "search term"
```

## Four Tool Types

### REST API

```yaml
server:
  type: http
  url: https://api.example.com
  headers:
    Accept: application/json
  timeout: 15s

auth:
  env: API_KEY
  header: Authorization
  value: "Bearer ${API_KEY}"

actions:
  - name: get_item
    description: Fetch an item by ID
    request:
      method: GET
      path: /items/{id}
    params:
      - name: id
        required: true
        example: "123"
    assert:
      - type: status
        values: [200]
    transform:
      - type: json
        select: [name, status, url]
```

### CLI Wrapper

```yaml
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
    output: text
    run: "docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}'"

  - name: stop
    description: Stop a container
    mutable: true
    run: "docker stop {{name}}"
    params:
      - name: name
        required: true
```

### MCP Server

```yaml
server:
  type: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-postgres"]
  env:
    POSTGRES_URL: "${POSTGRES_URL}"

auth:
  env: POSTGRES_URL

actions:
  discover: true
  static:
    - name: query
      description: Execute a SQL query
      params:
        - name: sql
          required: true

deny:
  - "drop_*"

transforms:
  "*":
    - type: truncate
      max_items: 100
```

### Skill

```yaml
name: pdf
description: Extract and analyze PDF content
version: "1.0"
category: productivity
tags: [pdf, document]

source:
  repo: anthropics/claude-code
  path: skills/pdf
  ref: main
  files:
    - path: SKILL.md
      sha256: a1b2c3d4e5f6...

sandbox:
  bash_allow: [uv, python3, pdftotext]
  filesystem:
    read: ["**/*.pdf"]
    write: ["**/*.md"]
```

## Auth Patterns

```yaml
# Bearer token
auth:
  env: TOKEN
  header: Authorization
  value: "Bearer ${TOKEN}"

# Custom header
auth:
  env: API_KEY
  header: x-api-key
  value: "${API_KEY}"

# Query string
auth:
  env: API_KEY
  param: api_key
  value: "${API_KEY}"

# Multiple headers
auth:
  env: [KEY_A, KEY_B]
  headers:
    X-Key-A: "${KEY_A}"
    X-Key-B: "${KEY_B}"

# OAuth2
auth:
  type: oauth2
  env: SLACK_TOKEN
  header: Authorization
  value: "Bearer ${SLACK_TOKEN}"
  scopes: [channels:read, chat:write]

# No auth: omit the auth block
```

## Common Transforms

```yaml
# Extract and shape JSON
- type: json
  extract: "$.data.items"
  select: [name, status, url]
  rename: { stargazers_count: stars }

# Limit output size
- type: truncate
  max_items: 20
  max_length: 8000

# Convert HTML to markdown
- type: html_to_markdown
  remove_images: true

# Sort results
- type: sort
  field: stars
  order: desc

# Filter items
- type: filter
  jq: ".stars > 100"

# Simple text format
- type: format
  template: "- {name} ({language}, {stars} stars)"

# Pipe through another tool
- type: pipe
  run: "jq filter --filter '[.[] | {name, stars}]'"
```

## Common Asserts

```yaml
# HTTP status
- type: status
  values: [200, 201]

# JSON field exists and is not empty
- type: json
  exists: "$.data"
  not_empty: "$.data.results"

# jq expression
- type: jq
  filter: ".data | length > 0"
```

## Param Types

```yaml
params:
  - name: query        # type defaults to string
    required: true
    example: "search term"

  - name: limit
    type: int
    default: "10"

  - name: lat
    type: float
    required: true

  - name: verbose
    type: bool

  - name: tags
    type: array

  - name: sort
    values: [stars, forks, updated]    # enum
    default: "stars"
```

## Defaults Table

| Field | Default |
|-------|---------|
| `spec` | `"1.0"` |
| `server.timeout` | `30s` |
| `params[].type` | `string` |
| `params[].required` | `false` |
| `params[].in` (GET) | `query` |
| `params[].in` (POST/PUT/PATCH) | `body` |
| `params[].in` (path) | `path` (auto) |
| `output` | `json` |
| `mutable` | `false` |
| `discover` | `false` |
| `pricing.model` | `free` |
| `retry.on` | `[429, 500, 502, 503]` |
| `retry.max_attempts` | `3` |
| `retry.backoff` | `exponential` |
| `retry.delay` | `1s` |
| `stream_timeout` | `30s` |

## Param Location Rules

- GET params go to query string (no `in` needed)
- POST/PUT/PATCH params go to body (no `in` needed)
- `{name}` in path auto-detects to path (no `in` needed)
- Only specify `in` when it deviates from the default

## File Location

All specs live at: `{first-letter}/{tool-name}/{tool-name}.yaml`

Examples:
- `g/github/github.yaml`
- `o/open-meteo/open-meteo.yaml`
- `s/slack/slack.yaml`

## Retry

```yaml
retry:
  on: [429, 500, 502, 503]
  max_attempts: 3
  backoff: exponential    # exponential, linear, fixed
  delay: 1s
```

Omit the block entirely to disable retry.

## Pagination

```yaml
# Page-based
pagination:
  type: page
  param: page
  per_page_param: per_page
  per_page_default: 30
  max_pages: 10

# Cursor-based
pagination:
  type: cursor
  param: starting_after
  cursor_path: "$.data[-1].id"
  has_more_path: "$.has_more"
  max_pages: 10
```

## Streaming

```yaml
actions:
  - name: tail_logs
    stream: true
    stream_timeout: 30s
    run: "docker logs -f {{name}}"
```

## Pricing

```yaml
# Free: omit the block
# Paid:
pricing:
  model: paid          # free, freemium, paid, contact
  url: https://example.com/pricing
```

## Deprecation

```yaml
deprecated: true
deprecated_message: "Use new-tool instead"
deprecated_by: new-tool
```
