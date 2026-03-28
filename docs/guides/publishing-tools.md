# Publishing Tools

Publishing makes your tools available to other workspaces and users on the clictl platform. This guide covers the end-to-end flow from having a tool in your workspace to making it publicly discoverable.

## Prerequisites

- A publisher profile with a claimed namespace (Settings > Publishing > Publisher Profile)
- At least one tool in My Toolbox (connected via a toolbox source)
- For public tools: an approved publisher profile (`VerifiedPublisher.status == APPROVED`)
- Workspace-only tools are exempt from publisher verification

## Step 1: Set up your publisher profile

If you have not already done so:

1. Go to Settings > Publishing > Publisher Profile
2. Click "Enable Publishing"
3. Claim a namespace (e.g., `mycompany`). This is how users will reference your tools (`clictl install mycompany/my-tool`)

Namespaces share a global pool with usernames and workspace slugs. Choose a name that represents your brand or organization.

## Step 2: Go to Published Tools

Navigate to Settings > Publishing > Published Tools. You will see two sections:

- **Published tools** - Tools currently visible on your publisher page
- **Available to publish** - Tools from My Toolbox that can be published

## Step 3: Toggle tools to publish

Click the publish toggle next to any tool in the "Available to publish" section. The tool moves to the "Published" section and becomes visible on your publisher page.

If a tool is in a private repository and you are on the free plan, the toggle will be disabled with a warning. Private repo tools require a paid plan because clictl needs to proxy the spec content for downstream users who cannot access the private repo directly.

## Step 4: Reorder published tools

Drag and drop tools in the "Published" section to control their display order on your publisher page. The first few tools are the most prominent, so put your best work at the top.

## Step 5: Preview your publisher page

Click "Preview Page" to see your public publisher profile at `/your-namespace`. This page shows your publisher info, featured tools, and a searchable list of all published tools.

## How other workspaces consume your tools

Once published, other users can add your tools in two ways:

**Install a specific tool:**

```bash
clictl install mycompany/my-tool
```

**Add your publisher as a toolbox source:**

```bash
clictl toolbox add mycompany
```

This adds your publisher registry endpoint as a source. All your published tools become available for search and install. It works the same way as adding a git-based toolbox, but the source is your publisher's API endpoint.

## Private repository considerations

| Plan | Private repo tools |
|------|--------------------|
| Free | Cannot publish. The toggle shows "Make the repo public to publish" |
| Pro | Can publish. clictl proxies the spec through the API |
| Team | Can publish. Spec proxying included |
| Enterprise | Can publish. All features |

When a tool is in a private repo and you publish it on a paid plan, clictl fetches the spec from your private repo using stored credentials and serves it to downstream users through the API. Downstream users never access your private repo directly.

If you downgrade to a lower plan, the proxy stops working and downstream consumers will see errors when trying to install the affected tools. The web UI warns about this before a downgrade.

## Unpublishing

Toggle a tool off in the Published Tools page to unpublish it. Existing installations by other workspaces continue to work (they already have the spec cached), but new installations will fail. No confirmation is required because unpublishing is reversible.

## Next steps

- [Creating Tools](creating-tools.md) - How to author tool specs
- [Customizing Tools](customizing-tools.md) - How others can fork and customize your tools
