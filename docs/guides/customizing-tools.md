# Customizing Tools

clictl does not provide in-platform forking or editing of tool specs. All customization happens at the git level using standard fork workflows. This guide explains when and how to customize an existing tool.

## When to customize

You might want to customize a tool when you need:

- Different default parameters (e.g., always use metric units, different base URL)
- Different authentication (e.g., your own OAuth app instead of a shared one)
- Modified behavior (e.g., extra transforms, additional actions, removed actions)
- A fix for a bug the publisher has not addressed yet

## Step 1: Find the tool's source repository

Every tool in clictl points to a git repository. You can find the source in two places:

**Web UI:** Open the tool detail page in My Toolbox. The source repository and file path are shown in the tool metadata.

**CLI:**

```bash
clictl info my-tool
```

The output includes the source repo URL, path, and ref (branch or tag).

## Step 2: Fork the repository

Go to the tool's source repository on GitHub, GitLab, or whichever provider hosts it. Use the provider's fork button to create a copy under your account or organization.

```
Original:  github.com/publisher/tools
Your fork: github.com/yourorg/tools
```

## Step 3: Make changes in your fork

Clone your fork and edit the spec file:

```bash
git clone https://github.com/yourorg/tools.git
cd tools

# Edit the spec
# e.g., change default units, add a new action, modify transforms
vim toolbox/my-tool/my-tool.yaml

git add .
git commit -m "Customize my-tool for our use case"
git push origin main
```

You can make any changes you want: add actions, remove actions, change parameters, update transforms, modify auth config, or adjust connection settings.

## Step 4: Connect your fork as a toolbox source

**Web UI:**

1. Go to Settings > Toolboxes
2. Click "Add Toolbox"
3. Paste your fork's URL or browse your GitHub repos
4. Click "Add"

**CLI (CI sync):**

Add a `.clictl.yaml` to your fork's root:

```yaml
workspace: myworkspace
namespace: "@yourorg"
spec_paths:
  - "toolbox/"
```

Then run `clictl toolbox sync` in CI or manually.

## Step 5: Your customized version appears in My Toolbox

After syncing, your modified tool appears in My Toolbox with a "Linked" badge. It is namespaced under your workspace, so it does not conflict with the original:

- `@publisher/my-tool` - the original
- `@yourorg/my-tool` - your customized version

You can install and use your version:

```bash
clictl install @yourorg/my-tool
clictl run @yourorg/my-tool action-name
```

## Namespacing prevents conflicts

Each toolbox source is associated with a namespace. If two sources provide a tool with the same base name, the namespace differentiates them. You can have both the original and your fork installed in the same workspace without conflicts.

## Staying in sync with upstream

Since your customization is a standard git fork, you can use git's built-in tools to stay up to date with the original repository:

```bash
git remote add upstream https://github.com/publisher/tools.git
git fetch upstream
git merge upstream/main
```

Resolve any conflicts in the spec files, push, and your toolbox source will pick up the changes on the next sync.

## Contributing changes back

If your customization is a bug fix or improvement that benefits everyone, open a pull request against the original repository. The publisher can merge your change, and it becomes available to all users on the next sync.

## Next steps

- [Creating Tools](creating-tools.md) - Author your own tool specs from scratch
- [Publishing Tools](publishing-tools.md) - Publish your customized tools for your team or the community
