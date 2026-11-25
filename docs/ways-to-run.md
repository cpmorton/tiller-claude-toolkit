# Ways to run it: no AI, Claude Code, an assistant, or another LLM

The toolkit works at four levels of AI involvement. Pick one per job, not one for
everything. Whatever you pick, the same rule holds: **the sheet, the repos and your Drive
backups are the system of record.** A chat transcript or an assistant's memory is not.
If you lose access to an AI tomorrow, the categories, rules, tags and decisions are all
still in places you own.

## Rules first, AI for judgment

AI steps are slower, cost money, and can be wrong in new ways each day. Rules and scripts
are boring and repeatable. So:

1. **Deterministic first.** Tiller fills, AutoCat rules (Auto Run on Fill), the scripts
   here, the Apps Script backup. These run with no AI at all.
2. **AI for what's left:** the rows no rule could place, receipts and order histories,
   "which trip was this", "is this paycheck odd". That's judgment, and it's where an AI
   earns its keep.
3. **Promote repeated judgment into a rule.** When you answer the same question about the
   same merchant three times, it becomes a line in `rules/autocat.local.csv`. When an AI
   does the same multi-step job twice, its steps become a script or a runbook in `docs/`.
   The AI share should shrink over time, not grow.

The cost of skipping step 3 is lock-in: a workflow that only exists as an assistant's habit
can't be moved to another tool, audited, or run by someone else.

## Which jobs need what

| Job | No AI | What an AI adds |
|---|---|---|
| Categorize new rows | AutoCat rules + Auto Run on Fill | Nothing; rules do it |
| Rows no rule placed (blank, `Categorize Later`) | Weekly filter view, by hand | Asks you daily, proposes rule candidates ([daily review](../routines/daily-review.md)) |
| Card payment / transfer pairing | `scripts/pair_legs.py`, apply by hand | Runs the script, applies after your yes |
| Marketplace orders (Amazon etc.) | Read order history, type `AMZ:` notes | Matches an order export to charges, writes `AMZ:<item>` |
| Trip and gift tags | Type `TRIP:` / tag tokens | Finds trip date windows, proposes tags for review |
| Paycheck anomalies | A formula comparing to last paycheck | Flags odd amounts or timing and asks why |
| Backups | Apps Script nightly copy ([backups](backups.md)) | Makes a pre-change copy before every approved write |
| Rule history in git | Export the two tabs when you change them | [Nightly snapshot](../routines/nightly-rules-snapshot.md) |
| Quarterly cleanup | [Runbook](quarterly-sweep.md) by hand | Runs the runbook, you approve each change set |

Everything in the "No AI" column is the fallback for the column next to it.

## 1. No AI

Use Tiller, AutoCat, the Apps Script backup, filter views, and the scripts locally:

```bash
git clone https://github.com/cpmorton/tiller-claude-toolkit
cd tiller-claude-toolkit && git config core.hooksPath .githooks
python3 -I scripts/lint_autocat.py ../my-ops/rules/autocat.local.csv --categories ../my-ops/rules/categories.csv
python3 -I scripts/spend_analysis.py ~/budget-data/transactions.csv ~/budget-data/categories.csv --config ../my-ops/config.toml
python3 -I scripts/pair_legs.py ~/budget-data/transactions.csv --config ../my-ops/config.toml --out ~/budget-data/pairs.csv
```

Exports come from *File > Download > CSV* on the Transactions and Categories tabs, into a
folder outside any git checkout. Apply proposals in the sheet by hand (Values only), after a
backup. Use the [tags and notes](tags-and-notes.md) tokens so an AI can pick up later.

## 2. Claude Code (recommended for setup and bulk work)

Claude Code is the most portable AI option: the instructions are files in your repos, and
the same session works locally or in the cloud.

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

## 3. An always-on assistant (e.g. Claude Duet)

An assistant with channels, task threads, routines and memory can run the day-to-day: it
asks about new rows each evening, works a task in its own thread, and keeps you posted.
This is the most convenient mode and the least portable one, so set it up so it stays thin:

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
- **Routines:** create them by pasting a prompt from [`routines/`](../routines/) (filled in)
  and the schedule. Keep the filled prompt in your private repo too. Routines are read-only;
  answers come back in the channel and an attended thread applies them.
- **One writer per column.** When several task threads run at once, only one may write a
  given column (usually Note) at a time, and each re-reads a row's Note before appending.
- **Write decisions down where they last.** When you settle a convention in chat ("plan
  fees get their own category"), it goes into the private repo's `docs/decisions.md` or
  `CLAUDE.md`, not only the assistant's memory.

If the assistant changes or goes away, move to mode 2: the same prompts, the same repos.

## 4. Another LLM or MCP client

Tiller's connector is an MCP server, `https://ai-tools.tillermoney.com/mcp`. Tiller
documents setup only for Claude, reports that early ChatGPT tests were inconsistent and
inaccurate, and hasn't validated Gemini (checked 2026-11). It requires a Direct Fills sheet.

If you use another client anyway:

- Give it the toolkit's `CLAUDE.md` and your private one as its instructions. They're
  plain Markdown. Tools that look for `AGENTS.md` can get a copy with that name; Claude Code
  itself can read `AGENTS.md` too, but by default only when there's no `CLAUDE.md`.
- Check its writes harder at first: read back every batch with `query_transactions`.
- Scheduled runs: `cron` (or a CI schedule) calling that tool's non-interactive CLI with a
  prompt from [`routines/`](../routines/).

## What to document when you customize

Every customization should be cheap for the next person (or the next you) to bootstrap.
When you add one, record:

- **What and why** in your private `docs/decisions.md`, dated, with your own words.
- **Generic or personal?** If it names a merchant, account, person or place it stays
  private. If it's a pattern anyone could use (a new token key, a routine, a script), open a
  PR here with a default and a line in [getting-started](getting-started.md).
- **The no-AI fallback.** If a step only works with an AI, write down how a person does it
  by hand, even if it's tedious.
