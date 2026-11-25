# Getting started

Two paths: a **new** Tiller sheet, or an **existing** one you already use. Both end in the
same place: the toolkit's categories and rules in your sheet, a backup habit, and Claude
connected to do the bookkeeping (see [ways to run](ways-to-run.md)).

Allow about an hour for the new path and an afternoon for the existing one, most of it
reviewing categories.

## Prerequisites (both paths)

- A Tiller subscription and a Google Sheet on **[Direct Fills](https://help.tiller.com/en/articles/13177613-direct-fills-for-google-sheets)**.
  Data arrives without pressing a button, and AutoCat's AI Suggest and Tiller's Claude
  connector (MCP) work only on Direct Fills sheets. Older Sidebar sheets can be upgraded
  from the Tiller Console.
- Two Direct Fills gotchas from that article: vertically merged cells break fills, and so
  do duplicate Transaction IDs.
- A Claude account (Tiller's connector is documented for Claude) and a GitHub account for
  the public/private repo pattern ([public-private-pattern](public-private-pattern.md)).

## Connect Claude

Do this first, so Claude can do the work in either path. The Tiller connector lets Claude
read and edit Transactions and Categories: add it from Claude's connector directory
(claude.ai or the desktop app) and sign in with your Tiller login. Tiller calls it
experimental. Per Tiller's
[MCP article](https://help.tiller.com/en/articles/14999828-connecting-ai-tools-to-tiller-via-mcp)
(checked 2026-11):

- reads all Transactions, Balance History, Holdings and Categories columns; at most 500
  transactions per call, paged;
- edits any Transactions column and adds, renames or deletes categories; budget amounts
  are read-only;
- `delete_transactions` exists in Claude Code only;
- `refresh_accounts` shares the Console's daily refresh limit;
- it reads your linked sheets only, not Tiller's database.

The AutoCat tab, backups and any other tab need the Google Sheets and Drive connectors.
Give Claude [CLAUDE.md](../CLAUDE.md) as its rules, plus your private repo's CLAUDE.md.
Then choose where it runs, Claude Code or Claude Duet: [ways to run](ways-to-run.md).

## Path A: new Tiller sheet

1. **Sheet.** Start from Tiller's [Foundation template](https://help.tiller.com/en/articles/3250724-what-is-the-tiller-foundation-template).
   Before the first fill, add a column titled **Note** at the right edge of Transactions:
   columns added later don't back-fill existing rows. (A **Tags** column is optional and not
   used by the scripts yet; see [tags and notes](tags-and-notes.md).)
2. **Categories.** Load [`defaults/categories.csv`](../defaults/categories.csv) into the
   Categories tab before AutoCat ever runs. Have Claude add them with the connector's
   `add_category`, or type or *Paste special > Values only* into blank rows under the last
   category. Never insert rows. Delete the template's categories you
   don't want before any transaction uses them.
3. **AutoCat.** Paste [`defaults/autocat.csv`](../defaults/autocat.csv) into the AutoCat tab
   with *Paste special > Values only*. Read the [AutoCat playbook](autocat-playbook.md) first:
   order matters. Turn on **Auto Run on Fill** in the Console so new rows are categorized
   as they arrive.
4. **Backups.** Set up the nightly copy in [backups](backups.md) (ten minutes, your own
   Google account). From now on every bulk change starts with a copy.
5. **Connect accounts** in the Tiller Console and let the first fill land.
6. **First review.** Look at what's blank or `Categorize Later`, and write rules for any
   merchant with 3 or more rows. Ask Claude to do this.

## Path B: existing Tiller sheet

Your sheet already has categories, rules and history you care about. The goal is to adopt
the conventions without a big-bang rewrite.

1. **Back up first.** A Drive copy named `BACKUP <yyyy-mm-dd> pre-toolkit - <sheet title>`
   (see [backups](backups.md)), and a named version in Version History.
2. **Check the sheet is Direct Fills** in the Tiller Console. Upgrade if not.
3. **Inventory.** Export the Categories and AutoCat tabs (they contain no transactions) and
   run the linter on your rules:
   ```bash
   python3 -I scripts/lint_autocat.py my-autocat.csv --categories my-categories.csv
   ```
   Fix broken quotes and shadowed rules before adding anything.
4. **Merge categories, don't replace them.** Compare your list with
   [`defaults/categories.csv`](../defaults/categories.csv) and add only what you're missing,
   at the bottom (or with `add_category`). Renaming a category you already use is a
   `rename_category` call (or a careful find-and-replace) so old rows follow it. A
   category that disappears shows up as "Unknown" in reports.
5. **Layer the rules.** Put your existing rules in your private repo as
   `rules/autocat.local.csv` and merge them **above** the defaults:
   ```bash
   python3 -I scripts/merge_autocat.py rules/autocat.local.csv defaults/autocat.csv > /root/budget-data/autocat.merged.csv
   ```
   Paste the result into the AutoCat tab with *Values only*. Your rules keep winning
   because first match wins.
6. **Don't touch history yet.** Normal Run AutoCat only fills blank rows, so it's safe.
   **Run Rules on All** overwrites every row a rule matches, Note overrides included; use
   it only after reading [tags and notes](tags-and-notes.md#autocat-and-notes-the-one-big-risk).
7. **Add a Note column** if you don't have one (insert at the right edge, titled `Note`).
   Existing free-text notes can stay; tokens get appended after them.
8. **Card payments.** Run `spend_analysis.py` (below) and read the "card payments filed as
   Expense" block. It's the most common reason an existing sheet's reports look wrong. See
   [categories and transfers](categories-and-transfers.md).
9. **Clean up a quarter at a time** with the [quarterly sweep](quarterly-sweep.md), newest
   first, instead of re-categorizing years at once.

## First spending review

Download Transactions and Categories as CSV into a folder **outside** any git checkout,
then:

```bash
python3 -I scripts/spend_analysis.py ~/budget-data/transactions.csv ~/budget-data/categories.csv \
    --config ../my-private-repo/config.toml --from 2025-10-01 --to 2026-09-30
```

Read the "card payments filed as Expense" block first. If it isn't empty, your reports are
double-counting. See [categories-and-transfers](categories-and-transfers.md).
