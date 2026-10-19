# tiller-claude-toolkit

Opinionated defaults, how-tos, and Claude agent workflows for running a household budget on a
[Tiller](https://tiller.com) Google Sheet (Direct Fills).

> Not affiliated with or endorsed by Tiller. "Tiller" is used only to describe compatibility.

## Who this is for

Someone who just connected their bank accounts to a Tiller sheet and wants:

1. A category list and an AutoCat rule set that work out of the box. The defaults here
   match about 87% of transactions on a real two-year household dataset before you add a
   single personal rule.
2. Conventions that keep reports honest: card payments that don't double-count, debt
   tracked separately from spending, and mixed-basket stores parked for review instead of
   guessed.
3. A way to let an AI agent (Claude) do the tedious parts, like sweeps, rule tuning and
   finding leaks, without it ever breaking the sheet.

## Layout

| Path | What |
|---|---|
| [`docs/`](docs/) | How-tos, from first setup to quarterly sweeps. Start with [getting-started](docs/getting-started.md) |
| [`defaults/categories.csv`](defaults/categories.csv) | Opinionated category list (Category, Group, Type) |
| [`defaults/autocat.csv`](defaults/autocat.csv) | Generic AutoCat rules in four tiers: structural, merchants, superstores, Plaid-hint fallbacks |
| [`scripts/lint_autocat.py`](scripts/lint_autocat.py) | Catches broken quotes, unknown categories, and rules that can never fire. Replays rules against your transactions |
| [`scripts/merge_autocat.py`](scripts/merge_autocat.py) | Layers your personal rules over the defaults (yours first, since first match wins) |
| [`scripts/spend_analysis.py`](scripts/spend_analysis.py) | "Where is the money actually going" review, with card payments removed |
| [`scripts/cloud-setup.sh`](scripts/cloud-setup.sh) | Setup script for a Claude Code cloud environment |
| [`CLAUDE.md`](CLAUDE.md) | Guardrails any agent working on a Tiller sheet should follow |
| [`config.example.toml`](config.example.toml) | Shape of the private config the scripts read |

## Public toolkit, private ops repo

Keep this repo generic and put everything personal in a **private** companion repo. That
means your account names, your local merchants, your rules and your notes. GitHub won't let
you make a private fork of a public repo, so the companion is a separate repo that uses this
one as upstream. See [docs/public-private-pattern.md](docs/public-private-pattern.md).

Financial data goes in **neither** repo. `.gitignore`, a pre-commit hook and CI all block it.

## Quick start

```bash
git clone https://github.com/cpmorton/tiller-claude-toolkit
cd tiller-claude-toolkit
git config core.hooksPath .githooks          # blocks commits of CSV/XLSX exports
python3 -I scripts/lint_autocat.py defaults/autocat.csv --categories defaults/categories.csv
```

Requires Python 3.11+ (for stdlib `tomllib`) and `pandas` for the analysis script.

## License

MIT. See [LICENSE](LICENSE).
