# Weekly sweep (template)

Read-only weekly report. Fill in the placeholders and keep the filled copy in your private repo.

> Using the Tiller connector, pull transactions added in the last 8 days from "<sheet
> name>" (id `<sheet id>`). Follow the toolkit's CLAUDE.md and your private repo's. Never
> write to the sheet. Report in under 15 lines to <where>:
> 1. New rows still blank or in `Categorize Later`: count, total, top 5 by amount.
> 2. New recurring charges (a merchant in 3+ distinct months at a similar amount) not in
>    last week's report, and recurring charges whose amount went up.
> 3. New interest, plan fees, late fees, NSF or courtesy-pay fees, by account.
> 4. Card payments from checking with no matching card-side leg (same amount, ±3 days).
>    Use `scripts/pair_legs.py` on the query result if the repo is checked out.
> 5. Lint status of `rules/autocat.local.csv` (`scripts/lint_autocat.py`).
> Propose rule changes as a diff to `rules/autocat.local.csv` on a branch, never in the sheet.
