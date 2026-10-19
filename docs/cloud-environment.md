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
  deps, **except** in sessions with several repos, where repo hooks don't run.

[`scripts/cloud-setup.sh`](../scripts/cloud-setup.sh) installs pandas, pyarrow, openpyxl,
rapidfuzz, miller and jq, and creates `/root/budget-data` (mode 700) for exports. It takes
about 15 seconds.

## What to automate

A scheduled routine running in this environment can be a weekly sweep: new uncategorized
rows, new recurring charges, new fees or interest, and payment legs without a match. It
posts a short report and changes nothing without a yes.
