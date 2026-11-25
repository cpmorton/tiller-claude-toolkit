# Ways to run it: Claude Code or Claude Duet

The toolkit is built for Claude, working through Tiller's connector. It runs in two places:
**Claude Code** for setup and bulk work, and **Claude Duet** (an always-on assistant with
channels, task threads and routines) for the day to day. Whichever you use, the same rule
holds: **the sheet, the repos and your Drive backups are the system of record.** A chat transcript or an assistant's memory is not.
If you move between Claude Duet and Claude Code, the categories, rules, tags and decisions
all come with you.

## Rules first, Claude for judgment

Claude steps are slower, cost money, and can be wrong in new ways each day. Rules and scripts
are boring and repeatable. So:

1. **Deterministic first.** Tiller fills, AutoCat rules (Auto Run on Fill), the scripts
   here, the Apps Script backup. These run without Claude.
2. **Claude for what's left:** the rows no rule could place, receipts and order histories,
   "which trip was this", "is this paycheck odd". That's judgment, and it's where Claude
   earns its keep.
3. **Promote repeated judgment into a rule.** When you answer the same question about the
   same merchant three times, it becomes a line in `rules/autocat.local.csv`. When Claude
   does the same multi-step job twice, its steps become a script or a runbook in `docs/`.
   Claude's share should shrink over time, not grow.

The cost of skipping step 3 is lock-in: a workflow that only exists as an assistant's habit
can't be moved from Claude Duet to Claude Code, audited, or set up by someone else.

## Which jobs need Claude

| Job | Rules and scripts | What Claude adds |
|---|---|---|
| Categorize new rows | AutoCat rules + Auto Run on Fill | Nothing; rules do it |
| Rows no rule placed (blank, `Categorize Later`) | `Categorize Later` rules park them | Asks you daily, proposes rule candidates ([daily review](../routines/daily-review.md)) |
| Card payment / transfer pairing | `scripts/pair_legs.py` proposes pairs | Runs the script, applies after your yes |
| Marketplace orders (Amazon etc.) | `AMZ:pending` rule marks them | Matches an order export to charges, writes `AMZ:<item>` |
| Trip and gift tags | None | Finds trip date windows, proposes tags for review |
| Paycheck anomalies | None | Flags odd amounts or timing and asks why |
| Backups | Apps Script nightly copy ([backups](backups.md)) | Makes a pre-change copy before every approved write |
| Rule history in git | `lint_autocat.py` checks each snapshot | [Nightly snapshot](../routines/nightly-rules-snapshot.md) |
| Quarterly cleanup | [Runbook](quarterly-sweep.md) | Runs the runbook, you approve each change set |

## Claude Code (setup and bulk work)

The instructions are files in your repos, and the same session works locally or in the
cloud. Run the scripts here too:

```bash
T=../tiller-claude-toolkit
python3 -I $T/scripts/lint_autocat.py rules/autocat.local.csv --categories rules/categories.csv
python3 -I $T/scripts/spend_analysis.py /root/budget-data/transactions.csv /root/budget-data/categories.csv --config config.toml
```

- **Setup:** attach both repos (toolkit + private) to a session, or clone them side by side
  locally. Claude Code reads each repo's `CLAUDE.md`. Connect Tiller, Google Sheets and
  Google Drive as claude.ai connectors so cloud sessions can use them.
- **Cloud environment:** [cloud-environment](cloud-environment.md) covers the setup script.
- **Use it for:** first-time setup, rule reviews, quarterly sweeps, anything that ends in a
  PR. `delete_transactions` is available only here (Tiller's MCP article).
- **Scheduled runs:** Claude Code's **scheduled tasks** (formerly "routines"; research
  preview, Pro/Max/Team/Enterprise) run a saved prompt against your repos in the cloud on a
  schedule, with your claude.ai connectors. Create one at claude.ai/code/routines or with
  `/schedule` in the CLI. Paste a prompt from [`routines/`](../routines/). Cron is UTC unless
  it starts with `CRON_TZ=`, and nothing more often than hourly. Per
  [the docs](https://code.claude.com/docs/en/routines) (checked 2026-11).
- **Local, unattended:** `claude -p "<prompt>"` runs non-interactively
  ([headless docs](https://code.claude.com/docs/en/headless)); `--mcp-config` loads MCP
  servers and `--allowedTools` limits what it may do. Whether your claude.ai connectors load
  in a local `-p` run isn't documented, so test it before relying on cron.

## Claude Duet (day to day)

Claude Duet, with its channels, task threads, routines and memory, runs the day to day: it
asks about new rows each evening, works a task in its own thread, and keeps you posted.
It's the most convenient place and the least portable one, so keep it thin:

- **One channel (or project) for the budget.** Its instructions should only point at the
  repos, like this, so rules live in one place:
  ```text
  Bookkeeping for my Tiller sheet (Direct Fills), "<sheet name>".
  The rules live in GitHub: <you>/<private repo> (CLAUDE.md, config, rules, decisions,
  routines) and cpmorton/tiller-claude-toolkit (scripts, how-tos). Read both CLAUDE.md
  files before any work. Where anything here disagrees with them, the repos win.
  Use the Tiller connector first; edit the sheet directly only where it can't reach, and
  only as current Tiller docs allow. Nothing is written to the sheet without a proposal,
  my yes and a Drive backup first.
  ```
- **Connectors:** Tiller, Google Sheets, Google Drive, and GitHub for the repos. Mail is
  optional (receipts, order confirmations).
- **Routines:** create them in the channel by pasting a prompt from [`routines/`](../routines/) (filled in)
  and the schedule. Keep the filled prompt in your private repo too. Routines are read-only;
  answers come back in the channel and an attended thread applies them.
- **One writer per column.** When several task threads run at once, only one may write a
  given column (usually Note) at a time, and each re-reads a row's Note before appending.
- **Write decisions down where they last.** When you settle a convention in chat ("plan
  fees get their own category"), it goes into the private repo's `docs/decisions.md` or
  `CLAUDE.md`, not only Claude Duet's memory.

If Claude Duet isn't available, use Claude Code: the same prompts, the same repos, and
its scheduled tasks for the routines.

## What to document when you customize

Every customization should be cheap for the next person (or the next you) to bootstrap.
When you add one, record:

- **What and why** in your private `docs/decisions.md`, dated, with your own words.
- **Generic or personal?** If it names a merchant, account, person or place it stays
  private. If it's a pattern anyone could use (a new token key, a routine, a script), open a
  PR here with a default and a line in [getting-started](getting-started.md).
- **Where it runs.** If it's a Claude Duet routine, keep its prompt in the private repo so a
  Claude Code scheduled task can run it too.
