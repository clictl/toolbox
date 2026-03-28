# gstack - Tool Group

**Garry Tan's engineering skill stack for Claude Code, available as a clictl tool group.**

gstack is a collection of 29 AI agent skills created by [Garry Tan](https://x.com/garrytan) (Y Combinator CEO) that turns Claude Code into a virtual engineering team. Each skill enforces a specific role and workflow - from product strategy to code review to deployment.

Originally shared as [garrytan/gstack](https://github.com/garrytan/gstack) on GitHub, this tool group makes the entire stack installable with a single command through clictl.

## Install

```bash
clictl install group gstack
```

Or install individual skills:

```bash
clictl install gstack-review        # staff engineer code review
clictl install gstack-qa            # full QA in real browser
clictl install gstack-ship          # release automation
```

## What's Included

### Planning and Strategy
- **gstack-office-hours** - Product interrogation with 6 forcing questions
- **gstack-plan-ceo-review** - Strategic challenge in 4 scope modes
- **gstack-plan-eng-review** - Architecture lock with data flow diagrams and test matrices
- **gstack-plan-design-review** - Interactive design dimension ratings
- **gstack-plan-devex-review** - Developer experience planning audit
- **gstack-autoplan** - Chains CEO, design, eng, and DX reviews automatically

### Design
- **gstack-design-consultation** - Complete design system from scratch
- **gstack-design-shotgun** - Multiple visual variants with comparison board
- **gstack-design-html** - Production HTML with Pretext
- **gstack-design-review** - Live design audit with before/after screenshots

### Development and Review
- **gstack-review** - Staff engineer code review with auto-fixes
- **gstack-investigate** - Root-cause debugging with data flow tracing
- **gstack-ship** - Release automation (sync, test, coverage, PR)
- **gstack-land-and-deploy** - Merge, CI, deploy, verify
- **gstack-canary** - Post-deploy monitoring
- **gstack-benchmark** - Core Web Vitals and performance comparison

### Testing and QA
- **gstack-qa** - Full QA in real browser with regression tests
- **gstack-qa-only** - Pure bug reporting without code changes
- **gstack-devex-review** - Live developer experience audit

### Security and Documentation
- **gstack-cso** - OWASP Top 10 and STRIDE threat modeling
- **gstack-document-release** - Sync docs to shipped code
- **gstack-retro** - Weekly engineering retrospective

### Safety and Utilities
- **gstack-careful** - Warn before destructive commands
- **gstack-freeze** - Lock edits to one directory during debugging
- **gstack-guard** - Combined careful + freeze
- **gstack-browse** - Real Chromium browser via Bun + Playwright
- **gstack-checkpoint** - Development checkpoints
- **gstack-learn** - Persistent patterns and preferences
- **gstack-health** - System health diagnostics

## Requirements

- [Claude Code](https://claude.ai/code) or compatible AI coding tool
- [Bun](https://bun.sh) v1.0+ (for the browse skill)
- Git

## Credits

Created by [Garry Tan](https://github.com/garrytan). Licensed under MIT.
Packaged for clictl by the clictl community.

## Links

- [garrytan/gstack on GitHub](https://github.com/garrytan/gstack)
- [clictl](https://clictl.dev)
