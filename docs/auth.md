# Auth Patterns Guide

How authentication works in clictl specs. Covers every auth pattern, vault resolution, OAuth2 flows, MCP server auth, and common recipes for popular APIs.

All examples use spec 1.0 format.

---

## How Auth Works

The auth block is a template. You declare the vault key names, and clictl resolves them at runtime. No implicit behavior, no magic prefixes.

```
spec declares env keys -> clictl resolves from vault -> ${KEY} replaced in value -> header/param sent with request
```

Three pieces:

1. `env` - names the vault key(s) clictl needs
2. `header`/`param` - where the credential goes (request header or query string)
3. `value` - template with `${KEY}` placeholders, sent exactly as written

```yaml
auth:
  env: MY_TOKEN
  header: Authorization
  value: "Bearer ${MY_TOKEN}"
```

At runtime, `${MY_TOKEN}` is replaced with the resolved secret and sent as the `Authorization` header.

---

## Auth Patterns

### Bearer token

The most common pattern. Used by GitHub, OpenAI, Anthropic, Vercel, and most modern APIs.

```yaml
auth:
  env: GITHUB_TOKEN
  header: Authorization
  value: "Bearer ${GITHUB_TOKEN}"
```

The agent never sees the token. clictl injects it into the outgoing request.

### Custom header

Some APIs use a non-standard header name instead of `Authorization`.

```yaml
auth:
  env: ANTHROPIC_API_KEY
  header: x-api-key
  value: "${ANTHROPIC_API_KEY}"
```

The `value` template is sent as-is. No `Bearer` prefix unless you write one.

### Query parameter

Older APIs pass the key in the URL query string.

```yaml
auth:
  env: NASA_API_KEY
  param: api_key
  value: "${NASA_API_KEY}"
```

This appends `?api_key=<resolved>` to every request URL. Use `param` instead of `header`.

### Multiple headers

Some APIs require two or more credentials (e.g., an API key and an application key).

```yaml
auth:
  env: [DD_API_KEY, DD_APP_KEY]
  headers:
    DD-API-KEY: "${DD_API_KEY}"
    DD-APPLICATION-KEY: "${DD_APP_KEY}"
```

Use `headers` (plural, a map) instead of `header` (singular, a string). They are mutually exclusive.

### OAuth2

For APIs that use OAuth2 authorization flows (Slack, Google, Notion, etc.).

```yaml
auth:
  type: oauth2
  env: SLACK_TOKEN
  header: Authorization
  value: "Bearer ${SLACK_TOKEN}"
  scopes: [channels:read, chat:write, users:read]
```

The OAuth2 flow is user-initiated:

1. User runs `clictl connect slack`
2. clictl opens the browser to the authorization URL
3. User authorizes the app and grants the listed scopes
4. clictl receives the token and stores it in the vault
5. On subsequent runs, `${SLACK_TOKEN}` resolves from the vault automatically

The `scopes` field documents which permissions the tool needs. clictl requests exactly these scopes during the OAuth flow.

### No auth

Omit the `auth` block entirely. Do not add an empty block.

```yaml
# Correct: no auth block
spec: "1.0"
name: nominatim
server:
  type: http
  url: https://nominatim.openstreetmap.org
actions:
  # ...
```

---

## MCP Server Auth

MCP servers (type: stdio) do not use the `header`/`param` pattern. Instead, credentials are passed as environment variables to the subprocess.

```yaml
server:
  type: stdio
  command: npx
  args: ["-y", "@modelcontextprotocol/server-postgres"]
  env:
    POSTGRES_CONNECTION_STRING: "${POSTGRES_CONNECTION_STRING}"

auth:
  env: POSTGRES_CONNECTION_STRING
```

The `auth.env` field tells clictl which vault keys to resolve. The `server.env` block passes the resolved values as environment variables to the MCP process. The subprocess reads `POSTGRES_CONNECTION_STRING` from its environment at startup.

For MCP servers that need multiple credentials:

```yaml
server:
  type: stdio
  command: npx
  args: ["-y", "@example/multi-auth-mcp"]
  env:
    DB_HOST: "${DB_HOST}"
    DB_PASSWORD: "${DB_PASSWORD}"
    API_KEY: "${EXTERNAL_API_KEY}"

auth:
  env: [DB_HOST, DB_PASSWORD, EXTERNAL_API_KEY]
```

The key names in `server.env` are what the subprocess sees. The `${...}` values reference vault keys.

---

## Vault Resolution Order

When clictl encounters `${KEY}` in a value template, it resolves the key by checking these sources in order:

| Priority | Source | Scope | Set by |
|----------|--------|-------|--------|
| 1 | Project vault | Current project directory | `clictl vault set KEY --project` |
| 2 | User vault | All projects for this user | `clictl vault set KEY` |
| 3 | Workspace vault | All users in this workspace | Workspace admin |
| 4 | Environment variable | Shell environment | `export KEY=value` |

The first match wins. This means:

- A project vault key overrides the user vault key with the same name
- A user vault key overrides the workspace vault key
- Environment variables are the fallback of last resort

### Checking auth status

```bash
# See which keys are set and which are missing
clictl info github

# Output:
# Auth: GITHUB_TOKEN
#   Status: set (user vault)
```

```bash
# Set a key in the user vault
clictl vault set GITHUB_TOKEN

# Set a key scoped to the current project
clictl vault set GITHUB_TOKEN --project
```

### Environment variable fallback

If a key is not in any vault, clictl checks the shell environment. This is useful for CI/CD pipelines and ephemeral environments where vault setup is not practical.

```bash
export GITHUB_TOKEN=ghp_abc123
clictl run github search_repos --q "clictl"
# Works: GITHUB_TOKEN resolved from environment
```

---

## Common API Patterns

### GitHub

```yaml
auth:
  env: GITHUB_TOKEN
  header: Authorization
  value: "Bearer ${GITHUB_TOKEN}"
```

Token types: personal access token (classic), fine-grained PAT, GitHub App installation token. All use the same Bearer pattern. Rate limit: 5,000 req/hour with token, 60/hour without.

### Stripe

```yaml
auth:
  env: STRIPE_SECRET_KEY
  header: Authorization
  value: "Bearer ${STRIPE_SECRET_KEY}"
```

Stripe uses Bearer auth with `sk_live_` or `sk_test_` prefixed keys.

### Anthropic

```yaml
auth:
  env: ANTHROPIC_API_KEY
  header: x-api-key
  value: "${ANTHROPIC_API_KEY}"
```

Anthropic uses a custom `x-api-key` header. No `Bearer` prefix.

### OpenAI

```yaml
auth:
  env: OPENAI_API_KEY
  header: Authorization
  value: "Bearer ${OPENAI_API_KEY}"
```

For organization-scoped requests, add the org header in the server block:

```yaml
server:
  type: http
  url: https://api.openai.com
  headers:
    OpenAI-Organization: "${OPENAI_ORG_ID}"

auth:
  env: [OPENAI_API_KEY, OPENAI_ORG_ID]
  header: Authorization
  value: "Bearer ${OPENAI_API_KEY}"
```

### Datadog

```yaml
auth:
  env: [DD_API_KEY, DD_APP_KEY]
  headers:
    DD-API-KEY: "${DD_API_KEY}"
    DD-APPLICATION-KEY: "${DD_APP_KEY}"
```

Datadog requires both an API key and an application key on every request.

### Slack (OAuth2)

```yaml
auth:
  type: oauth2
  env: SLACK_TOKEN
  header: Authorization
  value: "Bearer ${SLACK_TOKEN}"
  scopes: [channels:read, chat:write, users:read]
```

Use `clictl connect slack` to start the OAuth flow. The token is stored in the vault.

### AWS S3

```yaml
auth:
  env: [AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]
```

For AWS services, clictl uses the standard AWS credential chain. The `env` field declares the expected keys. clictl handles SigV4 signing internally when the server URL matches `*.amazonaws.com`.

### Twilio

```yaml
auth:
  env: [TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]
  header: Authorization
  value: "Basic ${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}"
```

Twilio uses HTTP Basic auth. clictl base64-encodes the `user:password` pair when the value contains the `Basic` prefix with a colon separator.

---

## Auth Fields Reference

| Field | Type | Description |
|-------|------|-------------|
| `env` | string or list | Vault key name(s) that clictl needs to resolve. |
| `header` | string | Single header name to set. Mutually exclusive with `headers`. |
| `headers` | map | Multiple headers to set. Mutually exclusive with `header`. |
| `param` | string | Query parameter name (for query string auth). |
| `value` | string | Template with `${KEY}` placeholders. What you write is what gets sent. |
| `type` | string | `oauth2` for OAuth flows. Omit for simple key-based auth. |
| `scopes` | list | OAuth2 scopes (only with `type: oauth2`). |

---

## Tips

### Keep env key names conventional

Use the same key names that the API vendor documents. If Stripe calls it `STRIPE_SECRET_KEY`, use that. Users expect familiar names.

### Do not hardcode secrets

Never put actual tokens in the spec. Always use `${KEY}` placeholders.

```yaml
# Wrong
value: "Bearer ghp_abc123realtoken"

# Correct
value: "Bearer ${GITHUB_TOKEN}"
```

### Use clictl info to debug

If auth is not working, run `clictl info <tool>` to see which keys are resolved and from which source.

### One env key per credential

If the API needs one key, use a string. If it needs multiple, use a list. Do not combine unrelated credentials into one env key.

```yaml
# One key
auth:
  env: GITHUB_TOKEN

# Multiple keys
auth:
  env: [DD_API_KEY, DD_APP_KEY]
```

### Scopes are documentation

The `scopes` field on OAuth2 auth tells users exactly what permissions the tool requires. Always list the minimum scopes needed.
