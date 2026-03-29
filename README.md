# clictl Official Toolbox

[![Tool Count](https://img.shields.io/badge/tools-223%2B-blue)](https://github.com/clictl/toolbox)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Spec Tests](https://github.com/clictl/toolbox/actions/workflows/validate.yaml/badge.svg)](https://github.com/clictl/toolbox/actions/workflows/validate.yaml)

The official tool registry for [clictl](https://clictl.dev) - the package manager for AI agents. 223+ curated specs for APIs, CLIs, MCP servers, and skills.

This toolbox is included by default when you install clictl:

```bash
curl -fsSL https://clictl.dev/install.sh | sh
clictl search github
```

## Documentation

- **[Spec Reference](docs/spec-reference.md)** - Complete field reference (spec 1.0)
- **[Transform Guide](docs/transforms.md)** - Cookbook for response transforms, DAG pipelines, and recipes
- **[DAG Transform Guide](docs/dag.md)** - Deep dive into parallel branches, fan-out, merge strategies, and testing
- **[Auth Patterns](docs/auth.md)** - Bearer tokens, API keys, OAuth2, MCP auth, vault resolution
- **[MCP Tool Guide](docs/mcp.md)** - Authoring specs for MCP servers, discovery, filtering, and transforms
- **[Skill Authoring Guide](docs/skills.md)** - Source blocks, sandbox constraints, trust model, and file hashing
- **[Quick Reference](docs/quick-reference.md)** - One-page cheat sheet
- **[Creating Tools](docs/guides/creating-tools.md)** - Step-by-step guide
- **[Customizing Tools](docs/guides/customizing-tools.md)** - Forks and overrides
- **[Publishing Tools](docs/guides/publishing-tools.md)** - Publishing to the registry

## For AI Agents

If you are an AI agent creating specs, read these:
- **[Spec Reference](docs/spec-reference.md)** - complete schema reference with examples
- **[Quick Reference](docs/quick-reference.md)** - defaults and common patterns
- **[llms.txt](llms.txt)** - machine-readable summary

## What's Inside

Curated tools across five spec types:

**APIs:** GitHub, GitLab, OpenAI, Anthropic, Slack, Discord, Stripe, npm, PyPI, crates.io, Homebrew, Docker Hub, Hugging Face, Twilio, SendGrid, Datadog, PagerDuty, Sentry, Shodan, VirusTotal, NASA, and more.

**CLIs:** git, gh, docker, kubectl, terraform, homebrew, npm, jq, and more.

**Websites:** React, Python, Go, TypeScript, Node.js docs, MDN, Stack Overflow, Wikipedia, and more.

**MCP Servers:** filesystem-server, github-mcp, git-mcp, fetch-server, brave-search-mcp, slack-mcp, postgres-mcp, sqlite-mcp, memory-mcp, puppeteer-mcp, sequential-thinking-mcp, everart-mcp, and more.

**Skills:** skill-commit, skill-pr-review, skill-test-writer, skill-refactor, skill-docs-writer, skill-debug, skill-api-design, skill-security-audit, and more.

## Structure

Specs are organized by first-character prefix (a-z, 0-9):

```
a/    anthropic, aws-s3, airtable, az, azure-ai, ...
b/    bing-search, brave-search-mcp, brainstorming, bun, ...
c/    cloudflare, confluence-mcp, context7-mcp, ...
g/    github, gitlab, gcloud, google-search, google-trends, ...
m/    mongodb-mcp, memory-mcp, ...
p/    perplexity, postman-mcp, postgres-mcp, ...
r/    reddit, recraft, rg, remotion, ...
s/    slack, stripe, shadcn, stability-ai, ...
...
tests/
  test_schema_all.py   # Schema validation for all specs
```

Each spec YAML includes its `category` and `protocol` fields. The directory prefix is purely for filesystem scalability.

## Spec Types

### API / CLI / Website Specs

Traditional tool specs that define connection details, auth, actions, assertions, and response transforms. These are the core of the registry.

### MCP Servers

MCP (Model Context Protocol) server specs define how to connect to servers that expose tools, prompts, and resources to agents. The registry adds value on top of raw MCP servers:

- **Tool filtering** -- expose only whitelisted tools, deny dangerous ones
- **Prompt injection** -- system prompts and per-tool instructions guide agent behavior
- **Output transforms** -- truncate, extract, and format tool outputs
- **Safety rules** -- destructive tools require ACL approval, deny lists block tools entirely
- **Multi-client config** -- one spec generates config for Claude Desktop, Claude Code, Cursor, VS Code, Windsurf

See [Spec Reference](docs/spec-reference.md) for the MCP spec schema.

### Skills

Skills follow the [agentskills.io](https://agentskills.io) standard (SKILL.md files). They are prompt-based agent capabilities -- markdown instructions that teach agents how to perform tasks like writing commits, reviewing PRs, or debugging code. Skills work across Claude Code, Cursor, VS Code, Codex CLI, and Windsurf.

| | Skills | MCP Tools |
|---|---|---|
| **Type** | Prompt-based (markdown instructions) | Function-based (tool calls) |
| **Execution** | Agent reads instructions, follows them | Agent calls function, gets result |
| **Infrastructure** | None (just a file) | Client-server protocol |
| **Best for** | Workflows, conventions, best practices | Data access, APIs, system operations |

See [Spec Reference](docs/spec-reference.md) for the skill spec schema.

## CLI Usage

```bash
# Install specific tools
clictl install open-meteo github stripe

# Install MCP servers (generates config for your client)
clictl install github-mcp --target claude-code
clictl install filesystem-server --target cursor

# Install skills (copies SKILL.md to the right place)
clictl install skill-commit --target claude-code

# Search the registry
clictl search --protocol mcp --tag database
clictl search --protocol skill --tag commit

# Inspect a spec
clictl info postgres-mcp
```

## Destructive Actions

Some tools include destructive or write actions (DELETE, rm, apply, exec). These are tagged with `destructive` in their tags list.

Workspace admins can block destructive actions using ACL rules:

```
DENY tag:destructive group:null    # Block all destructive actions for everyone
ALLOW tag:destructive group:devops  # Allow devops team to use them
```

Tools tagged `destructive`: docker, git, homebrew, kubectl, redis, terraform-cli.

## Create Your Own Toolbox

Use the [toolbox-example](https://github.com/clictl/toolbox-example) repo as a starting point. It includes sample specs, a `.clictl.yaml` config, and a GitHub Action that syncs your tools automatically on push.

```bash
# Use the example as a template on GitHub, then:
clictl toolbox add https://github.com/youruser/my-toolbox
```

See the [Spec Reference](docs/spec-reference.md) for the full spec format reference.

## Transforms

Specs include transforms that clean up raw API responses before your Agent sees them.

```yaml
# Raw API returns 50+ fields. Your Agent gets 3 clean lines.
actions:
  - name: current
    description: Get current weather for a location
    request:
      method: GET
      path: /data/2.5/weather
    assert:
      - type: status
        values: [200]
    transform:
      - type: json
        extract: "$.main"
      - type: template
        template: |
          Temperature: {{.temp}}C (feels like {{.feels_like}}C)
          Humidity: {{.humidity}}%
          Pressure: {{.pressure}} hPa
```

**Response transforms:** `json` (extract, select, rename), `template`, `truncate`, `format`, `html_to_markdown`, `sort`, `filter`, `unique`, `group`, `jq`, `js`, `pipe`

**Pre-request transforms:** `default_params`, `rename_params`, `template_body` (use `on: request`)

**Assertions:** `status`, `json`, `jq`, `js`, `cel`, `contains`

## Contributing

1. Fork this repo
2. Add your spec under `{first-letter}/{tool-name}/` (e.g., `s/my-tool/my-tool.yaml`)
3. Required fields: `name`, `description`, `version`, `category`, `tags`
4. For API/CLI specs: every action must have `assert` and `transform`
5. For MCP specs: must have `server` (type stdio or http) and `actions` blocks
6. For skill specs: must have `source` and `sandbox` blocks
7. Actions that change state must include `mutable: true`
8. Destructive actions must be tagged with `destructive`
9. Submit a PR

See [Spec Reference](docs/spec-reference.md) for the complete schema reference with examples.

## Links

- [clictl.dev](https://clictl.dev) - Website
- [github.com/clictl/cli](https://github.com/clictl/cli) - CLI source code
- [github.com/clictl/toolbox](https://github.com/clictl/toolbox) - This toolbox
- [github.com/clictl/toolbox-example](https://github.com/clictl/toolbox-example) - Example toolbox template
- [Contributing](CONTRIBUTING.md) - How to add a tool spec

A [Soap Bucket LLC](https://www.soapbucket.org) project.
