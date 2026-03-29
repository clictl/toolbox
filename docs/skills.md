# Skill Authoring Guide

How to write clictl specs for skills. Covers the source block, file hashing, sandbox constraints, runtime dependencies, the trust model, and a complete example.

All examples use spec 1.0 format.

---

## What Is a Skill

A skill is an instruction file, not a service. It is a markdown document (SKILL.md) that teaches an agent how to perform a task, like writing commits, reviewing PRs, or extracting PDF content. Skills may include helper scripts that the agent can execute.

Skills differ from MCP tools and API specs:

| | Skills | MCP / API tools |
|---|---|---|
| **Type** | Prompt-based (markdown instructions) | Function-based (tool calls) |
| **Execution** | Agent reads instructions and follows them | Agent calls function, gets result |
| **Infrastructure** | None (just files) | Client-server protocol or HTTP |
| **Best for** | Workflows, conventions, best practices | Data access, APIs, system operations |

A skill spec has no `server` or `actions` blocks. Instead, it has a `source` block that tells clictl where to fetch the skill files and a `sandbox` block that constrains runtime behavior.

---

## Spec Structure

```yaml
spec: "1.0"
name: my-skill
namespace: my-org
description: What this skill teaches the agent to do
version: "1.0"
category: developer
tags: [skill, workflow]

source:
  repo: owner/repo
  path: skills/my-skill
  ref: main
  files:
    - path: SKILL.md
      sha256: abc123...
    - path: helpers/run.py
      sha256: def456...

depends:
  - some-tool

sandbox:
  bash_allow: [python3, uv]
  filesystem:
    read: ["**/*.py", "**/*.md"]
    write: ["**/*.md"]
```

---

## Source Block

The `source` block tells clictl where to fetch skill files from a Git repository.

```yaml
source:
  repo: anthropics/claude-code
  path: skills/pdf
  ref: main
  files:
    - path: SKILL.md
      sha256: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
    - path: helpers/extract.py
      sha256: f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5
```

| Field | Type | Description |
|-------|------|-------------|
| `repo` | string | GitHub `owner/repo`. |
| `path` | string | Directory path within the repo containing the skill files. |
| `ref` | string | Git ref: branch name, tag, or commit SHA. Use a tag or commit for reproducibility. |
| `files` | list | Every file the skill needs. Each entry has `path` (relative to `source.path`) and `sha256` hash. |

### File listing rules

Every file must be listed individually. Directory entries are not valid.

```yaml
# Wrong: directory entry
files:
  - path: helpers/

# Correct: individual files
files:
  - path: helpers/extract.py
    sha256: abc123...
  - path: helpers/format.py
    sha256: def456...
```

Every file must have a `sha256` hash. To compute the hash:

```bash
shasum -a 256 SKILL.md
# a1b2c3d4e5f6...  SKILL.md
```

Or fetch the file from GitHub and hash it:

```bash
curl -sL https://raw.githubusercontent.com/owner/repo/ref/skills/my-skill/SKILL.md | shasum -a 256
```

### Using refs for stability

| Ref type | Example | When to use |
|----------|---------|-------------|
| Branch | `main` | Development, testing. Content may change. |
| Tag | `v1.2.0` | Published releases. Content is stable. |
| Commit SHA | `a1b2c3d` | Maximum reproducibility. Content is immutable. |

For published skills, prefer tags or commit SHAs. Branch refs are convenient but the content can change, which will cause hash mismatches.

---

## Sandbox Block

The sandbox constrains what the skill's helper scripts can do at runtime. It restricts shell commands, file access, network access, and environment variables.

```yaml
sandbox:
  bash_allow: [uv, python3, pdftotext]
  filesystem:
    read: ["**/*.pdf", "**/*.md", "**/*.txt"]
    write: ["**/*.md", "**/*.txt"]
  network:
    allow: []
  env:
    deny: [AWS_*, GITHUB_TOKEN, ANTHROPIC_API_KEY]
```

### bash_allow

Whitelist of shell commands the skill is allowed to run. Any command not on this list is blocked.

```yaml
sandbox:
  bash_allow: [uv, python3, pdftotext, jq]
```

This is a strict allowlist. If the skill's SKILL.md instructs the agent to run `curl`, but `curl` is not in `bash_allow`, the command is rejected.

### filesystem

Glob patterns controlling which files the skill can read and write.

```yaml
sandbox:
  filesystem:
    read: ["**/*.pdf", "**/*.md", "**/*.py", "**/*.json"]
    write: ["**/*.md", "**/*.txt", "output/**"]
```

| Field | Type | Description |
|-------|------|-------------|
| `read` | list | Glob patterns for allowed reads. |
| `write` | list | Glob patterns for allowed writes. |

Patterns are relative to the project root. `**/*.pdf` matches PDF files at any depth.

### network

Controls outbound network access from helper scripts.

```yaml
sandbox:
  network:
    allow: ["api.example.com", "pypi.org"]
```

An empty allow list (`allow: []`) blocks all outbound network access. Omitting the `network` block entirely allows all network access.

### env

Controls which environment variables are visible to the skill's subprocess.

```yaml
sandbox:
  env:
    deny: [AWS_*, GITHUB_TOKEN, ANTHROPIC_API_KEY, *_SECRET_*]
```

The deny list uses glob patterns. `AWS_*` blocks all environment variables starting with `AWS_`. This prevents the skill from accessing credentials it does not need.

---

## Runtime Block

For skills that need a specific runtime or package manager to execute helper scripts.

```yaml
runtime:
  manager: uvx
  dependencies:
    - pymupdf>=1.24.0
    - pillow>=10.0.0
```

| Field | Type | Description |
|-------|------|-------------|
| `manager` | string | Runtime manager: `uvx` (Python) or `npx` (Node.js). |
| `dependencies` | list | Packages to install. Version constraints are supported. |

When the skill is installed, clictl ensures the runtime dependencies are available. The `manager` field determines how dependencies are installed and scripts are executed.

---

## Dependencies

Skills can depend on other clictl tools (any type: API, CLI, MCP, or other skills).

```yaml
depends:
  - poppler      # CLI tool needed for pdftotext
  - github       # API tool used in the workflow
```

Dependencies are clictl tool names, not system binaries. System binary requirements go in `server.requires` (but skills do not have a server block, so dependencies on system binaries should be expressed as depends on CLI wrapper specs).

On `clictl install`, clictl checks `depends` and warns about missing dependencies.

---

## Trust Model

Skills execute as agent instructions and can run helper scripts. The trust model has four layers:

### 1. SHA256 file hashes

Every file in the `source.files` list has a `sha256` hash. When clictl fetches the file, it computes the hash and compares it to the spec. If they do not match, the install aborts.

```
Fetch file -> Compute SHA256 -> Compare to spec -> Match: install / Mismatch: abort
```

This ensures the skill content has not been tampered with since the spec was published.

### 2. Toolbox trust

Users explicitly add toolbox sources with `clictl toolbox add`. Only tools from trusted toolbox sources are available. This is the top-level gate: if the toolbox is not trusted, none of its tools are visible.

```bash
# Trust the official toolbox (added by default)
clictl toolbox add https://github.com/clictl/toolbox

# Trust a team toolbox
clictl toolbox add https://github.com/myteam/internal-tools
```

### 3. Sandbox constraints

Even after a skill is installed, its runtime behavior is constrained by the sandbox. The skill can only run commands in `bash_allow`, access files matching `filesystem` patterns, and reach hosts in `network.allow`.

### 4. Unverified publisher gate

Skills from publishers that are not verified require the `--trust` flag on first install.

```bash
# Verified publisher: installs without prompt
clictl install pdf

# Unverified publisher: requires explicit trust
clictl install community-skill --trust
```

After the first `--trust` install, the publisher is remembered and subsequent installs do not prompt.

### Trust flow summary

```
Toolbox trusted? -> Publisher verified? -> Hashes match? -> Sandbox enforced at runtime
       |                   |                    |                      |
       No: invisible       No: --trust gate     No: abort              Yes: constrained execution
```

---

## Complete Example: PDF Skill

```yaml
spec: "1.0"
name: pdf
namespace: anthropic
description: Extract and analyze PDF content
version: "1.0"
category: productivity
tags: [pdf, document, extract, skill]

instructions: |
  Use this skill when the user asks you to read, extract, or analyze PDF files.
  The skill includes a helper script that converts PDF pages to text.
  Always summarize the extracted content rather than dumping raw text.

source:
  repo: anthropics/claude-code
  path: skills/pdf
  ref: v1.0.0
  files:
    - path: SKILL.md
      sha256: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
    - path: helpers/extract.py
      sha256: f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5

depends:
  - poppler

runtime:
  manager: uvx
  dependencies:
    - pymupdf>=1.24.0

sandbox:
  bash_allow: [uv, python3, pdftotext]
  filesystem:
    read: ["**/*.pdf", "**/*.md"]
    write: ["**/*.md", "**/*.txt"]
  network:
    allow: []
  env:
    deny: [AWS_*, GITHUB_TOKEN, ANTHROPIC_API_KEY]
```

**What happens at install time:**

1. clictl fetches `SKILL.md` and `helpers/extract.py` from `anthropics/claude-code` at ref `v1.0.0`
2. Each file's SHA256 hash is verified against the spec
3. The `poppler` dependency is checked (warns if missing)
4. The `pymupdf` Python package is ensured available via `uvx`
5. The SKILL.md is copied to the appropriate location for the target client

**What happens at runtime:**

1. The agent reads SKILL.md and follows its instructions
2. If the instructions call for running `helpers/extract.py`, clictl checks `bash_allow`
3. File reads are restricted to `**/*.pdf` and `**/*.md` patterns
4. File writes are restricted to `**/*.md` and `**/*.txt` patterns
5. No outbound network access is allowed
6. Sensitive environment variables are hidden

---

## Tips

### Keep SKILL.md focused

A skill should teach one thing well. If you need multiple workflows, create multiple skills.

### Use tags or commit SHAs for published skills

Branch refs like `main` can change, causing hash mismatches. Use a tag (`v1.0.0`) or commit SHA for stability.

### Minimize bash_allow

Only allow the commands the skill actually needs. A smaller allowlist means a smaller attack surface.

### Test the sandbox locally

```bash
clictl install my-skill
clictl info my-skill
# Shows: sandbox constraints, resolved dependencies, file hashes
```

### List every file individually

Never use directory entries in `source.files`. Every file must be listed with its own `sha256` hash. Use the GitHub API to enumerate files if the skill has many.
