# Claude Code cloud environment

Per [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments)
(checked 2026-10):

- The **setup script** runs as root on Ubuntu 24.04 before Claude starts. It must exit 0
  and finish in about 5 minutes. The resulting disk is snapshotted and reused for about
  7 days, or until the script changes.
- Python 3 with pip and uv is preinstalled. **Trusted** network access already allows PyPI.
- Environment variables and the setup script are readable by anyone who uses the
  environment. Don't put API keys there. Tiller, Google Sheets and Drive come in through
  claude.ai connectors and need no keys.
- Use the setup script for machine-level tools. Use a repo SessionStart hook for project
  deps, **except** in sessions with several repos, where repo hooks don't run (next section).

[`scripts/cloud-setup.sh`](../scripts/cloud-setup.sh) installs pandas, pyarrow, openpyxl,
rapidfuzz, pytest, miller and jq, and creates `/root/budget-data` (mode 700) for exports. It
takes about 15 seconds.

## Sessions outside that environment

The setup script runs only in an environment that has it. Every other session gets the same
bootstrap from [`scripts/session-setup.sh`](../scripts/session-setup.sh), which runs
`cloud-setup.sh` when something is missing (so that file stays the one list) and turns on the
`.githooks` data guard in both repos:

| Session | How it runs |
|---|---|
| One repo attached (Claude Code on the web) | SessionStart hook in `.claude/settings.json`, every start |
| Both repos attached (Claude Duet threads, Claude projects) | By hand: `bash tiller-claude-toolkit/scripts/session-setup.sh`, as CLAUDE.md says |
| Your own machine | Same hook; it only sets `core.hooksPath` and installs nothing |

Per [Claude Code settings](https://code.claude.com/docs/en/settings) (checked 2026-11-25), a
cloud session with several repositories reads only `enabledPlugins` and
`extraKnownMarketplaces` from each repo's `.claude/settings.json`, so no repo hook runs there.
Cloud sessions set `CLAUDE_CODE_REMOTE=true`
([hooks](https://code.claude.com/docs/en/hooks)); the script installs only when it's set.
After a good run it leaves a stamp next to the pip packages and skips the install until
`cloud-setup.sh` changes or a tool goes missing.

## What to automate

A scheduled routine running in this environment can be a weekly sweep: new uncategorized
rows, new recurring charges, new fees or interest, and payment legs without a match. It
posts a short report and changes nothing without a yes.
