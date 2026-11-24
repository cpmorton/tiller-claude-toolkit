# Backups

Three layers, from cheapest to most deliberate. Only the first copies the whole sheet on
purpose. None of them puts transactions, balances or budget amounts in git.

| Layer | What it covers | Who runs it |
|---|---|---|
| Google Version History | Every edit, including Tiller's own fills and your hand edits | Google, automatically |
| Pre-change copy | The whole sheet, right before an approved change set | Whoever is about to write (you or Claude) |
| Rules snapshot (optional) | AutoCat and Categories tabs only, as CSV in your private repo | A scheduled job |

## 1. Version History (the undo)

Built into Google Sheets: **File → Version history → See version history**, pick a version,
**Restore this version**. Tiller's help center points here for restores:
[Reviewing version history](https://help.tiller.com/en/articles/432683-reviewing-version-history-restoring-a-google-sheet).
Name a version before a big change (**File → Version history → Name current version**) so it
is easy to find.

## 2. Pre-change copy (the rule)

Before any write to the sheet, make a Drive copy:

- **Name:** `BACKUP <yyyy-mm-dd> pre-<step> - <sheet title>`, e.g.
  `BACKUP 2026-11-24 pre-Q3-sweep - My Tiller Sheet`. The date sorts, and `<step>` says why.
- **Where:** a `Tiller Backups` folder in My Drive, not next to the live sheet. A copy is a
  full spreadsheet; keeping copies out of the way makes it hard to edit one by mistake.
- **When:** once per approved change set, after the yes and before the first write.
- **Sharing:** copies inherit nothing from the live sheet's sharing. Keep them private.

A copy is a snapshot, not a live sheet: Tiller never fills it, so don't connect it to Tiller
or run AutoCat in it.

## 3. Retention (opinionated default)

Copies are small (about 0.5 MB each for a two-year sheet), but they pile up. Default policy:

- keep every copy from the last **30 days**;
- keep the **earliest copy of each month** beyond that;
- delete the rest.

Deleting is a person's decision. A script or scheduled job may *list* what the policy would
remove; it deletes only after the owner has approved the policy, and it moves files to the
Drive Trash (recoverable for 30 days) rather than deleting them outright.

## 4. Rules snapshot (optional)

AutoCat rules and categories are the part of a Tiller sheet you build by hand, and they are
safe to keep in git because they contain no transactions. A nightly job can export the sheet,
write just those two tabs to CSV in your **private** repo, and commit only when they changed.
Git history then shows every rule edit, yours included. The pattern:

1. Export the sheet as xlsx (Google Drive export) to a scratch directory outside any repo.
2. Write `rules/autocat.local.csv` and `rules/categories.csv` from the AutoCat and Categories
   tabs (drop budget amount columns).
3. Run `scripts/lint_autocat.py` and `scripts/check_no_financial_data.sh --all`.
4. Commit `rules/` only if it changed. Delete the export.

The job reads the sheet and never writes to it. It is not a backup of your money data;
layers 1 and 2 are.
