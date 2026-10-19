# Public toolkit + private ops repo

| | `tiller-claude-toolkit` (public) | `<you>-mybudgetops` (private) |
|---|---|---|
| Scripts, docs, CLAUDE.md guardrails | ✓ | |
| Default categories and AutoCat rules | ✓ | |
| Your categories, AutoCat rules, account names | | ✓ |
| `config.toml` (accounts, payment patterns) | example only | ✓ |
| Decisions log, routine prompts, notes | | ✓ |
| Transaction data, statements, balances | ✗ | ✗ |

The test for which side something goes on: **does it name a merchant you visit, an
account, a person, or a place?** If so, it's private.

## Why not a fork

GitHub forks of a public repo are public, and their visibility can't be changed. So the
private repo is its own repo, and this one is tracked as a second remote:

```bash
git remote add upstream https://github.com/cpmorton/tiller-claude-toolkit
git fetch upstream
```

The private repo doesn't copy the scripts. It runs them from a sibling checkout and keeps
only overrides, so upstream changes never conflict:

```text
~/src/tiller-claude-toolkit/     # public, read-mostly
~/src/<you>-mybudgetops/
    CLAUDE.md                    # personal conventions on top of the toolkit's
    config.toml
    rules/autocat.local.csv      # your rules; merged ABOVE defaults
    rules/categories.csv         # your full category list
```

```bash
python3 -I ../tiller-claude-toolkit/scripts/merge_autocat.py \
    rules/autocat.local.csv ../tiller-claude-toolkit/defaults/autocat.csv > /root/budget-data/autocat.merged.csv
```

## Cloud sessions

Attach both repos to the Claude project (or environment). They clone side by side, so the
relative paths above work unchanged. A session with several repositories doesn't run repo
SessionStart hooks, so dependencies come from the environment's setup script. See
[cloud-environment](cloud-environment.md).
