# Contributing to the clictl Toolbox

Thanks for contributing a tool spec. This guide covers the format, requirements, and process.

## Adding a Tool

### 1. Pick the right directory

All specs live under `{first-letter}/{tool-name}/` where `{first-letter}` is the first character of the tool name. For example, a tool named `open-meteo` goes in `o/open-meteo/open-meteo.yaml`.

### 2. Create the spec file

Name the file `<tool-name>.yaml` using kebab-case.

```yaml
name: my-tool
description: Clear, one-line description of what it does
version: "1.0"
category: utilities
tags: [api, utility, example]
protocol: http

connection:
  base_url: https://api.example.com
  timeout: 15s

actions:
  - name: get-data
    description: What this action does
    method: GET
    path: /data
    params:
      - name: query
        type: string
        required: true
        in: query
```

### 3. Add marketplace fields (optional but encouraged)

```yaml
owner_name: Your Company
website: https://example.com
support_url: https://example.com/docs
license: MIT
pricing_model: free       # free, freemium, paid, contact
```

### 4. Submit a PR

- One tool per PR
- Test with `clictl info <name>` if possible
- Include `owner_name` and `website` so users know who maintains the tool
- Set `pricing_model` honestly
- If your spec uses transforms, test them: `clictl run <tool> <action> --raw | clictl transform --file your-transforms.yaml`

## Requirements

- `name`: unique, kebab-case
- `description`: clear one-liner
- At least one action with a working endpoint
- No hardcoded credentials (use `key_env` for auth)
- Prefer public, stable APIs

## Questions?

Open an issue at [github.com/clictl/toolbox](https://github.com/clictl/toolbox/issues).

---

clictl is a [Soap Bucket LLC](https://www.soapbucket.org) project.
