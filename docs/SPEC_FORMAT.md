# Spec YAML Reference

Reference for the tool spec format used in the clictl community toolbox.

## Schema Version

Specs use `schema_version: "1"` as the version field. The legacy `spec: "1.0"` format is still accepted during migration but new specs should use `schema_version`.

## Minimal Skill Spec

The smallest valid skill spec:

```yaml
schema_version: "1"
name: my-skill
description: What this skill teaches the agent to do
version: "1.0"
category: developer

source:
  repo: owner/repo
  path: skills/my-skill
```

That is all you need. The `source.files` list is auto-computed by `sync_registry` during the build pipeline. You do not need to hand-maintain file paths or SHA256 hashes.

## Full Spec (All Optional Fields)

```yaml
schema_version: "1"
name: my-skill
namespace: my-org
description: What this skill teaches the agent to do
version: "1.2"
category: developer
tags: [skill, workflow, example]
license: MIT
homepage: https://github.com/my-org/my-skill

instructions: |
  When to use this skill and constraints the agent should follow.

source:
  repo: owner/repo
  path: skills/my-skill
  ref: v1.2.0
  files:
    - path: SKILL.md
      sha256: a1b2c3...
    - path: helpers/run.py
      sha256: d4e5f6...

depends:
  - poppler
  - github

targets:
  - type: claude-code
    min_version: 1.0.0
  - type: cursor
  - type: codex

runtime:
  manager: uvx
  dependencies:
    - pymupdf>=1.24.0

sandbox:
  bash_allow: [python3, uv]
  filesystem:
    read: ["**/*.pdf", "**/*.md"]
    write: ["**/*.md"]
  network:
    allow: []
  env:
    deny: [AWS_*, GITHUB_TOKEN]

pricing:
  model: free
  url: https://example.com/pricing

privacy:
  local: true
```

## Field Reference

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Schema version. Always `"1"`. Legacy `spec: "1.0"` also accepted. |
| `name` | string | yes | Unique tool name in kebab-case. |
| `namespace` | string | no | Publisher or org name. Metadata only. |
| `description` | string | yes | One-line summary of what the tool does. |
| `version` | string | yes | Quoted version string (e.g., `"1.0"`). |
| `category` | string | yes | One of the standard categories. |
| `tags` | list | no | Search tags. 2-3 recommended. |
| `license` | string | no | SPDX license identifier (e.g., `MIT`, `Apache-2.0`). |
| `homepage` | string | no | URL to the tool's homepage or documentation. |
| `instructions` | string | no | Usage guidance for the agent. Strongly recommended. |
| `depends` | list | no | Other clictl tool names this tool requires. |
| `targets` | list | no | Agent targets this tool supports (claude-code, cursor, codex). Informational. |

### Source Block (Skills Only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source.repo` | string | yes | GitHub `owner/repo` containing the skill files. |
| `source.path` | string | yes | Directory path within the repo. |
| `source.ref` | string | no | Git ref (branch, tag, SHA). Defaults to `main`. |
| `source.files` | list | no | Auto-computed by sync_registry. Each entry has `path` and `sha256`. |

### Sandbox Block

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sandbox.bash_allow` | list | no | Allowlist of shell commands the skill can run. |
| `sandbox.filesystem.read` | list | no | Glob patterns for allowed file reads. |
| `sandbox.filesystem.write` | list | no | Glob patterns for allowed file writes. |
| `sandbox.network.allow` | list | no | Hostnames the skill can reach. Empty list blocks all. |
| `sandbox.env.deny` | list | no | Glob patterns for env vars to hide from the skill. |

### Targets Block

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `targets[].type` | string | yes | Agent target: `claude-code`, `cursor`, `codex`, `windsurf`, `gemini`. |
| `targets[].min_version` | string | no | Minimum agent version required. |

### Runtime Block

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `runtime.manager` | string | no | Package manager: `uvx` (Python) or `npx` (Node.js). |
| `runtime.dependencies` | list | no | Packages to install. Supports version constraints. |

### Pricing Block

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pricing.model` | string | no | Pricing model: `free`, `freemium`, `paid`. |
| `pricing.url` | string | no | Link to pricing page. |

### Privacy Block

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `privacy.local` | bool | no | Whether the tool runs entirely locally (no external API calls). |

## How source.repo and source.path Work

The `source.repo` field is a GitHub `owner/repo` string. The `source.path` field is a directory path within that repo. Together they identify where the skill files live.

For example, `repo: anthropics/claude-code` and `path: skills/pdf` resolves to files under `https://github.com/anthropics/claude-code/tree/main/skills/pdf`.

At install time, clictl fetches each file from `raw.githubusercontent.com` using the `ref` (defaulting to `main`) and verifies its SHA256 hash against the spec.

## How the CLI Resolves Specs

1. The CLI scans all configured toolbox sources (local directories or remote repos).
2. It walks `toolbox/` recursively looking for `*.yaml` files matching `{letter}/{name}/{name}.yaml`.
3. Specs are indexed by name. If duplicates exist across toolboxes, workspace sources take priority, then local config, then default.
4. `clictl search`, `clictl info`, and `clictl install` all resolve against this merged index.

## File List Auto-Computation

You do not need to list `source.files` by hand. When you submit a spec to the community toolbox, the `sync_registry` pipeline:

1. Reads `source.repo` and `source.path` from your spec.
2. Uses the GitHub API to enumerate all files in that directory.
3. Fetches each file and computes its SHA256 hash.
4. Writes the `files` list into the registry index.

This means your submitted spec only needs `repo`, `path`, and optionally `ref`. The hashes are computed and verified server-side.

## Pack Manifest Format

When a skill is published through the platform, it is packaged as a signed `.tar.gz` archive containing a `manifest.yaml`. The manifest is an extension of the spec format with additional fields for signing and provenance.

```yaml
schema_version: "1"
name: my-skill
version: 1.0.0
type: skill
description: "What this skill does."

publisher:
  name: my-org
  identity: github:my-org

content_sha256: a1b2c3d4e5f6...

provenance:
  builder: clictl.dev/registry
  source_repo: github.com/my-org/my-skill
  source_ref: v1.0.0
  source_commit: abc123def456789...
  source_tree_hash: fedcba987654321...
  built_at: "2026-03-30T12:00:00Z"
  git_tag_signed: true

sandbox:
  network: host
  credentials:
    - ssh
    - git-config
  filesystem:
    read_write:
      - "."
    read_only:
      - "~/.gitconfig"
  timeout: 120s
```

### Pack Manifest Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Pack type: `skill`, `mcp`, `http`, `website`, `composite`, `group`. |
| `publisher.name` | string | Publisher's namespace. |
| `publisher.identity` | string | Publisher's verified identity (e.g., `github:username`). |
| `content_sha256` | string | Merkle hash of the content directory tree. |
| `provenance.builder` | string | Build system that created the pack. |
| `provenance.source_repo` | string | Full URL of the source repository. |
| `provenance.source_ref` | string | Git tag the pack was built from. |
| `provenance.source_commit` | string | Full commit SHA. |
| `provenance.source_tree_hash` | string | Git tree hash for independent verification. |
| `provenance.built_at` | string | ISO 8601 timestamp of the build. |
| `provenance.git_tag_signed` | bool | Whether the source git tag was signed. |
| `sigstore_bundle` | object | (optional) Transparency log bundle containing a certificate-based signature and public log entry. Present when the pack was built in the automated pipeline. Used by the CLI for independent verification against the public audit log. When this field is present, `clictl verify` checks both the registry signature and the transparency log entry. |
| `sandbox.network` | string | Network access: `none`, `host`. |
| `sandbox.credentials` | list | Credential types the tool needs at runtime. |
| `sandbox.filesystem.read_write` | list | Paths with read-write access. |
| `sandbox.filesystem.read_only` | list | Paths with read-only access. |
| `sandbox.timeout` | string | Maximum execution time (e.g., `120s`). |

Publishers do not create pack manifests directly. The platform generates them during the build process. Use `clictl pack` to build local test packs.
