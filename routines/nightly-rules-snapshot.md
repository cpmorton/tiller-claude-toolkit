# Nightly rules snapshot (template)

Keeps git history of the two hand-built tabs (AutoCat, Categories), so every rule edit,
including ones made by hand in the sheet, is reviewable and revertible. It reads the sheet
and never writes to it. It needs a runner with GitHub push access to your private repo and
the Google Drive connector. Transactions, balances and budget amounts never go to git.

> Nightly rules snapshot for <private repo>. Nobody is watching; don't ask questions. Never
> write to the spreadsheet, and never commit transactions, balances or budget amounts.
>
> 1. Check out <private repo> and the toolkit side by side; pull main. Read both CLAUDE.md files.
> 2. Export "<sheet name>" (id `<sheet id>`) as xlsx with the Drive connector to a scratch
>    directory outside any repo.
> 3. Write `rules/autocat.local.csv` and `rules/categories.csv` from the AutoCat and
>    Categories tabs (drop budget columns). Run `scripts/lint_autocat.py` and
>    `scripts/check_no_financial_data.sh --all`. Delete the export.
> 4. If `git status --porcelain rules/` is empty, stop: "No rule changes."
> 5. Otherwise commit only `rules/` with `Nightly snapshot <yyyy-mm-dd>: AutoCat +A -D ~C,
>    Categories +A -D` and push.
> 6. Post the counts, the commit link and the lint result to <where>. If anything failed,
>    say what and that nothing was committed.

Your private repo needs a small script to turn the xlsx into the two CSVs (openpyxl). The
toolkit doesn't ship one yet.
