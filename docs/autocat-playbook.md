# AutoCat playbook

Facts from [How to use AutoCat](https://help.tiller.com/en/articles/3792984-how-to-use-autocat-for-automatic-categorization)
(checked 2026-10):

- **Rules run top-down, first match wins.** "Once a transaction matches on one rule, it
  won't match on other rules." Specific rules go above broad ones.
- **Amount Min/Max are absolute values.** Sign comes from an optional `Amount Polarity`
  column (`Positive` = inflow, `Negative` = outflow).
- **Filter headers must start with an existing Transactions column name** and are
  case-sensitive, e.g. `Description Contains`, `Account Contains`, `Category Hint Regex`.
- **Description Match** (learns from your past categorizations) runs before **AI Suggest**.
  Both are toggles in AutoCat settings and both work only on still-uncategorized rows.
- **Run Rules on All** re-runs only your rules across every row and **overwrites**
  existing categories wherever a rule matches. Description Match and AI Suggest don't run
  during it.

## How the defaults are ordered

1. **Structural**: card payments, fees, interest, payroll, tax, loans, transfers. These must
   win over anything merchant-based.
2. **Specific merchants**, most specific first: `Costco Gas` before `Costco`, `Uber Eats`
   before `Uber`, `Harris Teeter Fuel` before `Harris Teeter`.
3. **Superstores and P2P go to `Categorize Later`.** A Target receipt is groceries, clothes
   and a birthday gift. A guess is worse than a flag.
4. **Plaid `Category Hint` fallbacks** catch anything left. Hints look like
   `FOOD_AND_DRINK: FOOD_AND_DRINK_GROCERIES`, and the detailed codes come from Plaid's
   [personal finance category taxonomy](https://plaid.com/documents/transactions-personal-finance-category-taxonomy.csv).

Your personal rules go **above all of this**. `scripts/merge_autocat.py` does that layering.

## Writing "Contains" cells

- One term needs no quotes: `Publix`.
- Several terms: `"Whole Foods","Wholefds"`, double-quoted and comma-separated.
- Matching is case-insensitive and substring-based, so `"travel"` also matches
  "Travelers Insurance". Add a space or a store-number marker (`"REI #"`) to tighten it.
- Amounts are plain numbers: `50`, not `$50`.

`scripts/lint_autocat.py` flags unbalanced quotes, stray commas, `$` amounts, invalid regex,
categories that don't exist, duplicates, and rules **shadowed** by an earlier broader rule.
A shadowed rule can never fire. With `--transactions` it replays the rules and lists the
top unmatched descriptions, which are your next rule candidates.

## Safe re-run (cleanup mode)

1. Back up the sheet.
2. Turn **off** Description Match and AI Suggest. They learn from, and amplify, whatever
   is already wrong.
3. Clear Category and Categorized By only on the rows you want re-run. Log their
   Transaction IDs and old categories to a tab first, so the change can be undone.
4. Run AutoCat normally from the Console (**not** "Run Rules on All").
5. Review what's still blank, write rules for merchants with 3+ rows, and hand-pick the
   one-offs.
