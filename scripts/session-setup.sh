#!/bin/bash
# Per-session bootstrap for the Tiller budget repos. Safe to run any number of times.
#   - Single-repo Claude Code sessions run it as a SessionStart hook (.claude/settings.json).
#   - Sessions with several repos attached (Claude Duet threads, Claude projects) skip repo
#     hooks, so run it by hand once: bash tiller-claude-toolkit/scripts/session-setup.sh
#   - On your own machine it only wires the git hooks; installs are cloud-only.
# Stdout becomes session context, so it stays quiet unless something is wrong.
set -u
toolkit=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# Turn on the pre-commit data guard here and in the private companion repo, if it sits
# next to this one. A hooksPath someone already set is left alone.
for repo in "$toolkit" "$toolkit/../tiller-claude-mybudgetops"; do
  [ -d "$repo/.githooks" ] || continue
  if [ -z "$(git -C "$repo" config --get core.hooksPath 2>/dev/null)" ]; then
    git -C "$repo" config core.hooksPath .githooks
  fi
done

# Package installs only in Claude Code cloud sessions.
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0

ready() {
  python3 -I -c 'import pandas, pyarrow, openpyxl, rapidfuzz, pytest' 2>/dev/null &&
    command -v mlr >/dev/null && command -v jq >/dev/null && [ -d /root/budget-data ]
}

# cloud-setup.sh is the one list of what gets installed (it's also the environment setup
# script). Skip when it's unchanged since its last good run and everything is still there.
# The stamp lives with the pip packages, so a fresh container without them reinstalls.
stamp="$(python3 -I -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/.tiller-session-setup.sha256"
if sha256sum --check --status "$stamp" 2>/dev/null && ready; then
  exit 0
fi
rm -f "$stamp"
bash "$toolkit/scripts/cloud-setup.sh"
if ready; then
  sha256sum "$toolkit/scripts/cloud-setup.sh" > "$stamp" 2>/dev/null || rm -f "$stamp"
else
  # cloud-setup.sh swallows failures so it can't block a session; say what's missing instead.
  echo "session-setup: some tools didn't install (see scripts/cloud-setup.sh); analysis scripts or tests may fail."
fi
exit 0
