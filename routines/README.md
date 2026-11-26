# Routine prompts

Prompts for scheduled, unattended Claude runs. The same prompt works as a Claude Duet
routine or a Claude Code scheduled task. See [ways to run](../docs/ways-to-run.md).

Every routine here is **read-only** against the sheet. Nobody is watching an unattended run,
so it can't get a yes, and the toolkit's rule is no write without one. A routine reports and
proposes; a person (or an attended session) applies.

| Prompt | Cadence | What it does |
|---|---|---|
| [daily-review.md](daily-review.md) | daily, evening | Asks you about new blank / `Categorize Later` rows and odd paychecks |
| [weekly-sweep.md](weekly-sweep.md) | weekly | New recurring charges, fees and interest, unmatched payment legs, rule lint |
| [nightly-rules-snapshot.md](nightly-rules-snapshot.md) | nightly | Commits AutoCat and Categories tab changes to your private repo |

Copy a prompt into your private repo, fill in the `<placeholders>` (sheet name and ID,
where to post, your time zone), and keep the filled copy there as the source of truth.
If you edit the routine in Claude Duet or Claude Code, copy the change back.
