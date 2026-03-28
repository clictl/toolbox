# MCP Tool Authoring Guide

How to write clictl specs for MCP (Model Context Protocol) servers. Covers static actions, dynamic discovery, filtering, transforms, packages, instructions, and complete examples.

All examples use spec 1.0 format.

---

## What Is MCP

MCP is a protocol for AI agents to interact with external tools and data sources. An MCP server exposes tools, prompts, and resources over a standardized JSON-RPC interface. The agent calls a tool by name, passes parameters, and gets structured results back.

clictl adds a spec layer on top of MCP servers that provides:

- **Curated descriptions** - better tool names and descriptions than the server defaults
- **Tool filtering** - expose only safe tools, deny dangerous ones
- **Output transforms** - truncate, extract, and format tool outputs before they reach the agent
- **Instructions** - system-level and per-tool guidance for the agent
- **Auth management** - vault-based credential resolution passed as env vars
- **Multi-client config** - one spec generates config for Claude Code, Cursor, VS Code, Windsurf

Without a clictl spec, you get the raw MCP server with all its tools and default descriptions. With a spec, you get a curated, safe, well-documented interface.

---

## Spec Structure

An MCP spec has a `server` block with `type: stdio` (or `type: http` for remote servers), an `actions` block, and optional `allow`/`deny` filters, `transforms`, and `instructions`.

```yaml
spec: "1.0"
name: my-mcp
namespace: my-org
description: What this MCP server does
version: "1.0"
category: data
tags: [mcp, database]

server:
  type: stdio
  command: npx
  args: ["-y", "@example/my-mcp-server"]
  env:
    API_KEY: "${MY_API_KEY}"

auth:
  env: MY_API_KEY

instructions: |
  Agent-facing guidance for this tool.

actions:
  # Static, dynamic, or both

allow:
  - "safe_*"

deny:
  - "drop_*"

transforms:
  "*":
    - type: truncate
      max_length: 16000
```

---

## Server Block

### stdio (local process)

Most MCP servers run as local processes communicating over stdin/stdout.

```yaml
server:
  type: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
  env:
    NODE_ENV: production
  requires:
    - name: node
      check: "node --version"
      url: https://nodejs.org
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | (required) | `stdio` |
| `command` | string | (required) | Binary to execute. |
| `args` | list | - | Command-line arguments. |
| `env` | map | - | Environment variables. Supports `${KEY}` vault references. |
| `requires` | list | - | System binary requirements with `name`, `check`, and `url`. |

### http (remote MCP server)

For MCP servers running as remote HTTP services.

```yaml
server:
  type: http
  url: https://mcp.example.com/v1
  headers:
    Authorization: "Bearer ${MCP_TOKEN}"
  timeout: 30s
```

---

## Static Actions

Static actions are defined in the spec. They provide curated descriptions, examples, and response shapes that the MCP server itself may not include.

```yaml
actions:
  - name: read_file
    description: Read the contents of a file at the given path
    output: text
    params:
      - name: path
        required: true
        description: Absolute or relative file path
        example: "./src/main.ts"
    response:
      example: |
        import express from 'express'
        const app = express()

  - name: write_file
    description: Write content to a file, creating it if it does not exist
    mutable: true
    params:
      - name: path
        required: true
        example: "./output.txt"
      - name: content
        required: true
```

Static actions map by name to MCP tool calls. No `request` block or `run` field is needed. clictl routes the call through the MCP protocol because the server block has `type: stdio` or `type: http`.

When an action name in the spec matches a tool name returned by the MCP server, the spec definition wins. This lets you override poor default descriptions with better ones.

---

## Tool Discovery

All stdio MCP servers automatically discover tools at runtime. clictl calls `tools/list` on the server to get the current set of available tools. No configuration needed.

Static `actions` in the spec are optional metadata for search indexing and `clictl info` output. They are not used for execution.

You can add static actions to provide better descriptions for search:

```yaml
# These are metadata for search and clictl info.
# Actual tools come from the MCP server at runtime.
actions:
  - name: query
    description: Execute a SQL query against the connected database
    instructions: "Always LIMIT results to 100 rows unless the user asks for more."
    params:
      - name: sql
        required: true
        example: "SELECT id, name FROM users LIMIT 10"

  - name: list_tables
    description: List all tables in the database
```

**How it works:**

1. Static actions in the spec are indexed for search and shown by `clictl info`
2. At runtime, clictl starts the server and calls `tools/list`
3. Static actions override server descriptions for name matches (spec wins)
4. Server tools not in the spec pass through as-is
5. `deny` patterns filter the result
6. `allow` patterns whitelist (if present, only matching tools pass through)
7. The agent sees one unified list

---

## Allow and Deny Filters

Control which MCP tools are exposed to the agent. Both use glob patterns matched against tool names.

### Deny list

Block tools that match any pattern. Applied to both static and discovered tools.

```yaml
deny:
  - "drop_*"
  - "truncate_*"
  - "delete_*"
  - "exec_*"
```

### Allow list

If present, only tools matching an allow pattern are exposed. Everything else is blocked.

```yaml
allow:
  - "query"
  - "list_*"
  - "describe_*"
  - "read_*"
```

### Combined

When both are present, a tool must match an allow pattern AND not match any deny pattern.

```yaml
allow:
  - "query"
  - "list_*"
  - "describe_*"

deny:
  - "drop_*"
```

### Glob syntax

| Pattern | Matches |
|---------|---------|
| `read_*` | `read_file`, `read_dir`, `read_config` |
| `*_file` | `read_file`, `write_file`, `delete_file` |
| `query` | Exactly `query` |
| `*` | Everything |

---

## Per-Action Transforms

For MCP servers, transforms are keyed by action name in a top-level `transforms` block, not inside individual actions.

```yaml
transforms:
  read_file:
    - type: truncate
      max_length: 8000
  list_directory:
    - type: truncate
      max_items: 100
  query:
    - type: json
      select: [id, name, email]
    - type: truncate
      max_items: 50
  "*":
    - type: truncate
      max_length: 16000
```

The `"*"` key is a wildcard default applied to any action without a specific transform entry. Always include a wildcard truncate to bound output size.

All transform types from the [Transform Guide](transforms.md) work here: `json`, `truncate`, `format`, `template`, `filter`, `sort`, `redact`, and others.

---

## Instructions

### Tool-level instructions

Top-level `instructions` apply to the entire MCP server. The agent sees this guidance whenever it considers using any tool from this server.

```yaml
instructions: |
  Provides read/write access to a PostgreSQL database.
  Always run describe_table before writing queries to understand the schema.
  Never DROP or TRUNCATE tables without explicit user confirmation.
  Prefer SELECT queries with LIMIT clauses.
```

### Per-action instructions

Static actions can have their own `instructions` field for action-specific guidance.

```yaml
actions:
    - name: query
      description: Execute a SQL query
      instructions: "Always LIMIT results to 100 rows unless the user asks for more."

    - name: write_file
      description: Write content to a file
      instructions: "Always confirm the target path with the user before writing."
```

---

## Package Block

For MCP servers distributed as npm or PyPI packages, the `package` block declares the package manager and package name. clictl uses this for installation and updates.

### npm package

```yaml
server:
  type: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/home"]

package:
  manager: npm
  name: "@modelcontextprotocol/server-filesystem"
  version: ">=0.6.0"
```

### PyPI package

```yaml
server:
  type: stdio
  command: uvx
  args: ["mcp-server-sqlite", "--db-path", "./data.db"]

package:
  manager: pypi
  name: mcp-server-sqlite
  version: ">=0.5.0"
```

| Field | Type | Description |
|-------|------|-------------|
| `manager` | string | Package manager: `npm` or `pypi`. |
| `name` | string | Package name. |
| `version` | string | Version constraint. |

---

## Server Keep-Alive

By default, clictl starts the MCP server process when the first tool call arrives and stops it when the session ends. The `keep_alive` option keeps the server running between calls to avoid cold-start latency.

```yaml
server:
  type: stdio
  command: npx
  args: ["-y", "@example/slow-startup-mcp"]
  keep_alive: true
```

Use `keep_alive: true` for servers with slow startup times (database connections, model loading). For lightweight servers, the default behavior is fine.

---

## Prompts and Resources

MCP servers can expose prompts (reusable prompt templates) and resources (data sources) in addition to tools. clictl surfaces these in the spec.

### Prompts

```yaml
prompts:
  - name: summarize
    description: Summarize a document
    arguments:
      - name: content
        required: true
        description: The document text to summarize

  - name: translate
    description: Translate text to another language
    arguments:
      - name: text
        required: true
      - name: target_language
        required: true
        description: Target language code (e.g., "es", "de", "fr")
```

### Resources

```yaml
resources:
  - name: schema
    uri: "postgres://localhost/mydb/schema"
    description: Database schema for the connected PostgreSQL instance
    mime_type: application/json
```

---

## Complete Examples

### Filesystem MCP

```yaml
spec: "1.0"
name: filesystem-mcp
namespace: modelcontextprotocol
description: Secure file system access through MCP
version: "1.0"
category: developer
tags: [filesystem, files, mcp]

server:
  type: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
  requires:
    - name: node
      check: "node --version"
      url: https://nodejs.org

package:
  manager: npm
  name: "@modelcontextprotocol/server-filesystem"

instructions: |
  Provides read and write access to files within the allowed directory.
  The server is restricted to the directory passed as the last argument.
  Always confirm with the user before writing or deleting files.

actions:
    - name: read_file
      description: Read the full contents of a file
      output: text
      params:
        - name: path
          required: true
          example: "./src/main.ts"

    - name: write_file
      description: Write content to a file, creating it if needed
      mutable: true
      instructions: "Confirm the path with the user before writing."
      params:
        - name: path
          required: true
        - name: content
          required: true

    - name: list_directory
      description: List files and directories at a path
      params:
        - name: path
          required: true
          example: "./src"

deny:
  - "delete_*"

transforms:
  read_file:
    - type: truncate
      max_length: 8000
  list_directory:
    - type: truncate
      max_items: 200
  "*":
    - type: truncate
      max_length: 16000
```

### PostgreSQL MCP

```yaml
spec: "1.0"
name: postgres-mcp
namespace: modelcontextprotocol
description: PostgreSQL database access via MCP
version: "1.0"
category: data
tags: [postgres, sql, database, query, mcp]

privacy:
  pii: true

server:
  type: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-postgres"]
  env:
    POSTGRES_CONNECTION_STRING: "${POSTGRES_CONNECTION_STRING}"

auth:
  env: POSTGRES_CONNECTION_STRING

package:
  manager: npm
  name: "@modelcontextprotocol/server-postgres"

instructions: |
  Provides read/write access to a PostgreSQL database.
  Always run describe_table before writing queries to understand the schema.
  Never DROP or TRUNCATE tables without explicit user confirmation.
  Prefer SELECT queries with LIMIT clauses.

actions:
    - name: query
      description: Execute a SQL query against the connected database
      output: json
      instructions: "Always LIMIT results to 100 rows unless the user asks for more."
      params:
        - name: sql
          required: true
          example: "SELECT id, name FROM users LIMIT 10"
      response:
        example: |
          [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    - name: list_tables
      description: List all tables in the database
      output: json
      response:
        example: |
          ["users", "orders", "products"]

    - name: describe_table
      description: Show column names and types for a table
      instructions: "Run this before writing queries to understand the schema."
      params:
        - name: table_name
          required: true
          example: "users"

deny:
  - "drop_*"
  - "truncate_*"

transforms:
  query:
    - type: truncate
      max_items: 100
  "*":
    - type: truncate
      max_length: 16000
```

---

## Tips

### Always add a wildcard truncate

MCP servers can return unbounded output. A `"*"` transform with `truncate` prevents large responses from flooding the agent context window.

```yaml
transforms:
  "*":
    - type: truncate
      max_length: 16000
```

### Write static overrides for key tools

Write static action definitions for the tools the agent will use most. These serve as search metadata and override server descriptions with better ones. Better descriptions, examples, and instructions make the agent more effective.

### Use deny to block destructive tools

If the MCP server exposes tools like `drop_table`, `delete_file`, or `exec_command`, add them to the deny list. It is easier to deny dangerous tools than to allow-list safe ones.

### Pass credentials through env, not args

Do not put secrets in `server.args`. Use `server.env` with vault references.

```yaml
# Wrong: secret in args
server:
  args: ["-y", "@example/mcp", "--token", "sk-abc123"]

# Correct: secret in env
server:
  env:
    API_TOKEN: "${MY_TOKEN}"
```

### Test with clictl info

Run `clictl info <mcp-tool>` to see the resolved actions, auth status, and any missing dependencies before running the tool.
