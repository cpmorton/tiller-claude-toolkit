# Routine prompts

Prompts for scheduled, unattended agent runs. They are plain Markdown so any runner can use
them: a Claude Code scheduled task, an always-on assistant's routine (e.g. Claude Duet), or
`cron` calling an agent CLI. See [ways to run](../docs/ways-to-run.md).

Every routine here is **read-only** against the sheet. Nobody is watching an unattended run,
so it can't get a yes, and the toolkit's rule is no write without one. A routine reports and
proposes; a person (or an attended session) applies.

| Prompt | Cadence | What it does | No-AI fallback |
|---|---|---|---|
| [daily-review.md](daily-review.md) | daily, evening | Asks you about new blank / `Categorize Later` rows and odd paychecks | Filter view on Category, weekly |
| [weekly-sweep.md](weekly-sweep.md) | weekly | New recurring charges, fees and interest, unmatched payment legs, rule lint | `spend_analysis.py` + `pair_legs.py` by hand |
| [nightly-rules-snapshot.md](nightly-rules-snapshot.md) | nightly | Commits AutoCat and Categories tab changes to your private repo | Export the two tabs when you change them |

Copy a prompt into your private repo, fill in the `<placeholders>` (sheet name and ID,
where to post, your time zone), and keep the filled copy there as the source of truth.
If you edit the routine in the runner's UI, copy the change back.
