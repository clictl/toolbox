# clictl toolbox

[![clictl](https://api.clictl.dev/api/v1/badge/clictl/toolbox/)](https://clictl.dev)
[![clictl tools](https://api.clictl.dev/api/v1/badge/clictl/toolbox/tools/)](https://clictl.dev/browse)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Spec Tests](https://github.com/clictl/toolbox/actions/workflows/validate.yaml/badge.svg)](https://github.com/clictl/toolbox/actions/workflows/validate.yaml)

The default tool registry for [clictl](https://clictl.dev). 220+ curated specs for APIs, MCP servers, and skills that work out of the box with your AI agents.

One install gives you tools for GitHub, Slack, Stripe, OpenAI, Anthropic, Postgres, filesystem access, code review, and much more. [Browse all tools](https://clictl.dev/browse).

## Install

```bash
curl -fsSL https://download.clictl.dev/install.sh | sh
```

This toolbox is included automatically. Start using tools right away:

```bash
clictl install github stripe open-meteo
clictl install github-mcp
clictl search --protocol mcp --tag database
```

## What's inside

Every spec uses the [clictl Tool Spec 1.0](https://clictl.dev/spec) format. Five protocol types:

- **http** - REST APIs with auth, transforms, and assertions
- **mcp** - MCP servers with tool filtering, output transforms, and sandbox isolation
- **skill** - Agent skills (instructions + code) fetched from git repos
- **website** - Web pages converted to agent-readable markdown
- **command** - CLI tools wrapped for agent use

## Spec format

Four required fields:

```yaml
spec: "1.0"
name: my-tool
protocol: http
description: What this tool does
```

See the [full spec reference](https://clictl.dev/spec) and the [JSON Schema](https://clictl.dev/spec/1.0/schema.json) for validation.

## Create your own toolbox

Use the [toolbox-example](https://github.com/clictl/toolbox-example) template to create a private or public toolbox:

```bash
clictl toolbox add https://github.com/youruser/my-toolbox
```

## Documentation

- [Spec 1.0 Reference](https://clictl.dev/spec) - Complete spec format and field reference
- [Auth Patterns](docs/auth.md) - Bearer tokens, API keys, vault resolution
- [Transform Guide](docs/transforms.md) - Response transforms and DAG pipelines
- [Skill Authoring Guide](docs/skills.md) - Source blocks, sandbox constraints
- [Adding a Skill](docs/adding-skills.md) - Step-by-step guide for contributing skills

## Contributing

Contributions are welcome. Please open an issue to discuss your idea before submitting a pull request.

1. Fork this repo
2. Add your spec under `toolbox/{first-letter}/{tool-name}/{tool-name}.yaml`
3. Include required fields: `spec`, `name`, `protocol`, `description`
4. Run `clictl toolbox validate` before submitting
5. Submit a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide with examples for each protocol type.

## For AI agents

If you are an AI agent creating specs, read [CONTRIBUTING.md](CONTRIBUTING.md) and [llms.txt](llms.txt).

## Links

- [clictl.dev](https://clictl.dev)
- [CLI source](https://github.com/clictl/cli)
- [Toolbox template](https://github.com/clictl/toolbox-example)

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

clictl is a [Soap Bucket LLC](https://www.soapbucket.org) project. SOAPBUCKET and clictl are trademarks of Soap Bucket LLC.
