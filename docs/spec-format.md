# Spec Format Reference

This document has moved to the clictl Tool Spec 1.0 paper.

See: [cli/docs/spec.md](../../cli/docs/spec.md)

Or online at: [clictl.dev/spec](https://clictl.dev/spec)

## Quick Reference

Four required fields:

```yaml
spec: "1.0"
name: my-tool
protocol: http
description: What this tool does
```

Five protocols: `http`, `mcp`, `skill`, `website`, `command`.

Auth uses header templates:

```yaml
auth:
  env: API_KEY
  header: "Authorization: Bearer ${API_KEY}"
```

For MCP servers, use a `package` block:

```yaml
package:
  registry: npm
  name: "@org/mcp-server"
  version: 1.0.0
```

For full field reference, see the spec paper.
