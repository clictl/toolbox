# Adding a Skill to the Community Toolbox

Step-by-step guide for contributing a skill spec.

## Prerequisites

You need:

1. A **public GitHub repository** containing your skill files.
2. A **SKILL.md** file in that repo. This is the instruction document the agent reads at runtime.
3. (Optional) Helper scripts alongside SKILL.md if the skill needs to run code.

## Step 1: Write SKILL.md

Your SKILL.md should teach the agent how to perform one specific task. Keep it focused. Include:

- When to use the skill
- Step-by-step instructions
- Expected inputs and outputs
- Error handling guidance

Place it in a dedicated directory within your repo, e.g., `skills/my-skill/SKILL.md`.

## Step 2: Write the Spec YAML

Create a minimal spec file:

```yaml
spec: "1.0"
name: my-skill
description: What this skill teaches the agent to do
version: "1.0"
category: developer
tags: [skill, workflow]

source:
  repo: your-org/your-repo
  path: skills/my-skill
```

That is all you need for a basic submission. You do not need to list individual files or compute SHA256 hashes. The `sync_registry` pipeline handles that automatically after merge.

### Optional fields worth adding

```yaml
# Pin to a stable release
source:
  ref: v1.0.0

# Constrain what the skill can do at runtime
sandbox:
  bash_allow: [python3]
  filesystem:
    read: ["**/*.py"]

# Declare dependencies on other clictl tools
depends:
  - some-tool

# Specify runtime packages
runtime:
  manager: uvx
  dependencies:
    - some-package>=1.0
```

See [SPEC_FORMAT.md](SPEC_FORMAT.md) for the full field reference.

## Step 3: Place the File

Specs live at `toolbox/{first-letter}/{name}/{name}.yaml`.

Examples:
- `my-skill` goes in `m/my-skill/my-skill.yaml`
- `pdf-extract` goes in `p/pdf-extract/pdf-extract.yaml`
- `code-review` goes in `c/code-review/code-review.yaml`

The name must be kebab-case, unique, and match across the directory name and filename.

## Step 4: Validate Locally

If you have clictl installed:

```bash
clictl toolbox validate toolbox/m/my-skill/my-skill.yaml
```

This checks required fields, YAML syntax, and naming conventions.

## Step 5: Submit a PR

- One skill per PR
- Include a brief description of what the skill does and why it is useful
- Make sure your source repo is public so the pipeline can fetch files
- Set `category` and `tags` accurately for discoverability

## What Happens After Merge

1. The `sync_registry` pipeline runs automatically.
2. It reads your spec, fetches files from `source.repo`, and computes SHA256 hashes.
3. The skill is added to the registry index with verified file hashes.
4. CLI users get the skill on their next `clictl toolbox update`.

Users install your skill with:

```bash
clictl install my-skill
```

If your publisher account is not verified, users will need the `--trust` flag on first install. See the [skills guide](skills.md) for details on the trust model.

## Checklist

- [ ] SKILL.md exists in the source repo and is well-written
- [ ] Spec YAML has `name`, `description`, `version`, `category`, and `source`
- [ ] File is placed at `toolbox/{letter}/{name}/{name}.yaml`
- [ ] Name is kebab-case and unique
- [ ] Source repo is public
- [ ] Sandbox block is present if the skill runs helper scripts
- [ ] `clictl toolbox validate` passes (if available)
