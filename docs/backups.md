# Backups

Three layers, from cheapest to most deliberate. Only the first copies the whole sheet on
purpose. None of them puts transactions, balances or budget amounts in git.

| Layer | What it covers | Who runs it |
|---|---|---|
| Google Version History | Every edit, including Tiller's own fills and your hand edits | Google, automatically |
| Pre-change copy | The whole sheet, right before an approved change set | Whoever is about to write (you or Claude) |
| Nightly copy (optional) | The whole sheet, once a day, with retention | An Apps Script trigger in your own Google account |
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

## 4. Nightly copy with Apps Script (optional)

[`apps-script/nightly-backup.gs`](../apps-script/nightly-backup.gs) copies the live sheet into
the backup folder every night as `BACKUP <yyyy-mm-dd> nightly - <sheet title>` and applies the
retention policy above to **its own** copies only. It runs in your Google account, so only you
can install and authorize it.

What it will and won't touch:

- It reads the live sheet and never writes to it.
- It trashes (never permanently deletes) only files in the backup folder that it tagged
  itself, that you own, and that are named like a nightly copy. Hand-made `pre-<step>` copies
  and anything else in the folder or elsewhere in Drive are left alone.
- It stops without trashing anything if a run would trash more than 5 copies.
- A copy has a new file ID. Direct Fills fill only the sheets linked to your Tiller account, so
  a copy gets no new transactions unless someone links it. Tiller's help center describes a
  copy the same way: "a historical copy of your Tiller spreadsheet with the data that's in it
  today" ([Accessing Tiller Google Sheets on your Google Drive](https://help.tiller.com/en/articles/432698-accessing-tiller-google-sheets-on-your-google-drive)).
  Never link a backup to Tiller.

Setup (about ten minutes):

1. Open [script.google.com](https://script.google.com), choose **New project**, and name it
   `Tiller nightly backup`.
2. Replace everything in `Code.gs` with the contents of `apps-script/nightly-backup.gs`, then save.
3. **Project Settings** (gear icon): set **Time zone** to yours. Under **Script properties**, add
   `SOURCE_SHEET_ID` (the long ID in your Tiller sheet's URL, between `/d/` and `/edit`). If you
   already have a backup folder, also add `BACKUP_FOLDER_ID` (the ID at the end of the folder's
   URL). Otherwise the script uses or creates a single `Tiller Backups` folder in My Drive.
4. In the editor, choose `nightlyBackup` and **Run**. Approve the access prompt. Google warns
   that the app isn't verified because it's your own script: **Advanced → Go to Tiller nightly
   backup**. Check that today's copy is in the folder.
5. Check the Tiller Console: the copy should not appear among your linked sheets.
6. Run `dryRunPrune`. It logs what it would trash (nothing, at first).
7. Run `installTrigger` once. The **Triggers** page (clock icon) should now show `nightlyBackup`
   daily between 2 and 3 AM.

To stop it, run `removeTrigger` or delete the trigger on the Triggers page. Copies already made
stay where they are.

## 5. Rules snapshot (optional)

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
