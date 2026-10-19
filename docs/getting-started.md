# Getting started

## 1. Sheet

Start from Tiller's [Foundation template](https://help.tiller.com/en/articles/3250724-what-is-the-tiller-foundation-template)
on a [Direct Fills](https://help.tiller.com/en/articles/13177613-direct-fills-for-google-sheets)
Google Sheet. Direct Fills is Tiller's newer fill service. Data arrives without pressing a
button, and AutoCat's AI Suggest is only available on it. Sheets started before Feb 2026 can
be upgraded from the Tiller Console.

Two Direct Fills gotchas from the help article: vertically merged cells in a column break
fills, and duplicate Transaction IDs block them.

## 2. Categories

Load [`defaults/categories.csv`](../defaults/categories.csv) into the Categories tab *before*
your first AutoCat run. If the tab already has categories, **append** the ones you want at
the bottom. Don't insert rows (see [CLAUDE.md](../CLAUDE.md)).

The list is opinionated in a few ways:

- **Debt is its own group.** `Debt / Revolving Payment` is a Transfer. Minimums, snowball
  payments, interest and fees are Expenses, so the cost of debt shows up as spending.
- **Discretionary groups carry a `-Discretionary` suffix**, so a pivot on Group splits
  needs from wants with no extra column.
- **`Categorize Later`** is a real category, not a blank. Blank means "AutoCat hasn't seen
  it". Categorize Later means "a human or agent needs a receipt".

## 3. AutoCat

Paste [`defaults/autocat.csv`](../defaults/autocat.csv) into the AutoCat tab with *Paste
special > Values only*. Then read the [AutoCat playbook](autocat-playbook.md) before your
first run. Rule order matters and the defaults are ordered on purpose.

## 4. Connect Claude

The Tiller connector for Claude lets an agent query and update transactions. The Google
Sheets connector covers the other tabs. Give the agent [CLAUDE.md](../CLAUDE.md) as its
rules. In a Claude project, put the private repo's CLAUDE.md in the project instructions or
in the repo itself.

## 5. First review

Download the Transactions and Categories tabs as CSV into a folder **outside** any git
checkout, then run:

```bash
python3 -I scripts/spend_analysis.py ~/budget-data/transactions.csv ~/budget-data/categories.csv \
    --config ../my-private-repo/config.toml --from 2025-10-01 --to 2026-09-30
```

Read the "card payments filed as Expense" block first. If it isn't empty, your reports are
double-counting. See [categories-and-transfers](categories-and-transfers.md).
