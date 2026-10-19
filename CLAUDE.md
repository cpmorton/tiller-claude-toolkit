# Working on a Tiller budget sheet

These rules apply to any agent session that reads or writes a user's Tiller Google Sheet.
A private companion repo may add personal conventions on top. Its CLAUDE.md wins where they
differ.

## Never

- Commit financial data: transaction exports, statements, balances, account numbers.
  Exports go to a scratch directory outside every git checkout (e.g. `/root/budget-data`).
- Insert rows in the **Categories** tab. Append new categories at the bottom. The Category
  dropdown on Transactions is a data-validation rule that points at that range.
- Paste into **Transactions** or **AutoCat** except as *Paste special > Values only*.
  A normal paste overwrites the validation on those cells.
- Move, rename or reformat the Category column header on either tab.
- Run AutoCat "Run Rules on All" without saying so first. It overwrites existing
  categories wherever a rule matches.

## Always

- **Back up before any write**: make a Drive copy named
  `BACKUP <yyyy-mm-dd> pre-<step> - <sheet title>`.
- Default to read-only. Propose a change set, get a yes, back up, then write.
- Clear a cell only with explicit confirmation.
- Treat nothing as done until it's verified in the sheet. Plans discussed in chat aren't facts.
- Ground Tiller behavior in the current Help Center or Community, not memory. Cite the URL.

## Category conventions (defaults; the private repo may override)

- **Card payments are transfers on both legs** (`Debt / Revolving Payment`, Type Transfer).
  Card purchases are already expenses, so an expense-typed payment double-counts.
- To budget debt paydown, send the minimum or snowball as a **separate payment**. Then an
  amount-bounded rule can tag just that one `Debt Minimum Payment` / `Debt Snowball Fund`.
- `Transfer` is only for moves between your own checking/savings/investment accounts.
- Refunds go back to the original expense category, not to income.
- `Categorize Later` covers Amazon, superstores (Target, Costco, Walmart...), and P2P with
  no memo. They're reconciled later from order exports and receipts. Match by Transaction ID
  in the Note column.
- Note tokens: `FLAG:identify`, `AMZ:pending`, `REVIEW:<why>`, `TODO:<what>`, and
  `SWEEP:<yyyy>-Q<n>` on finalized rows. Append tokens; never overwrite a Note.

## Tools

- `scripts/lint_autocat.py rules.csv --categories categories.csv [--transactions tx.csv]`
  before proposing any rule change.
- `scripts/spend_analysis.py` for spending reviews. Report income vs. *real* spend
  (card payments excluded) first, and the uncategorized share before any totals.
