# Card payments, debt, and why your spending looks doubled

## The rule

Every credit-card purchase is already an expense on the card's side of the sheet. When you
pay the card from checking, that payment is money moving between your own accounts. If the
checking side is tagged as an expense, the same dollars count twice.

Tiller's own guidance offers two models:

- **Both legs are a Transfer-type category.** "This prevents the payment from being counted
  as spending twice." See [Understanding Transfers](https://help.tiller.com/en/articles/432687-understanding-transfers).
- **Checking side is an Expense-type "Debt Payment", card side a Transfer**, for getting out
  of debt. See [How to use Tiller to get out of Debt](https://help.tiller.com/en/articles/8900483-how-to-use-tiller-to-get-out-of-debt).

The second model is only honest when the card **isn't taking new purchases**. If it is, the
expense-typed payment covers purchases that were already counted.

## The convention in these defaults

| Leg | Category | Type |
|---|---|---|
| Card purchases | whatever they are | Expense |
| Payment, checking side, regular | `Debt / Revolving Payment` | Transfer |
| Payment, card side | `Debt / Revolving Payment` | Transfer |
| Minimum on a carried-balance card, sent as its **own** payment | `Debt Minimum Payment` | Expense |
| Extra paydown on the one snowball card, sent as its **own** payment | `Debt Snowball Fund` | Expense |
| Interest, plan fees, annual and late fees | `Credit Card Fees/Interest` | Expense |

Splitting the minimum or snowball into a separate payment is what makes this automatable.
The default rule tags any payment with Plaid hint `LOAN_PAYMENTS_CREDIT_CARD_PAYMENT` as a
transfer. A personal rule *above* it can bound the amount, for example
`Description Contains "Amex Epayment"`, `Amount Max 350`, giving `Debt Minimum Payment`.

## How to tell if you have the problem

`scripts/spend_analysis.py` prints a block called **Card payments filed as Expense**. If
you carry balances and pay them in large lump sums, that block can easily be bigger than
your mortgage. Every dollar in it is phantom spending in Tiller's reports.

## Other transfer-shaped things that hide spending

- **Transfers to family members' accounts** (kids' spending accounts, for example) look like
  `Transfer`. If the money gets spent, it's `Allowance` or `Kids Misc`.
- **P2P inflows tagged as wages.** Plaid often hints Venmo and PayPal receipts as
  `INCOME_WAGES`. The default Paycheck rule only fires on checking/savings for that reason.
- **Loan or line-of-credit draws** into checking are `Loan Disbursement/Advance` (a
  Transfer), not income. A month that "balances" because of a draw didn't balance.

## Finding the other leg

`scripts/pair_legs.py` does the matching from the [quarterly sweep](quarterly-sweep.md) step 7
for you. It reads the JSON that the Tiller connector's `query_transactions` returns (or a CSV of
the Transactions tab) and pairs an outflow with an inflow of the same amount in a different
account within 3 days, where at least one leg is uncategorized. For each blank leg it proposes:

1. the other leg's category, when that leg is already categorized and the account types
   below don't contradict it (a contradiction goes to a person);
2. `Debt / Revolving Payment` when one account is in `[accounts] cards`;
3. `Transfer` when both accounts are in `[accounts] cash`;
4. nothing, so a person decides (loans, P2P wallets, anything not in the config).

Pass `--categories` (a CSV of the Categories tab) so that only rows with a Transfer-type
category can be a partner. Without it, a purchase or refund that happens to share an amount
with a payment can pair. In a test on real data, family Venmo repayments paired with Amazon
orders that way. Ties are reported as ambiguous instead of guessed, and categorized rows are
never proposed for change. The proposal CSV goes to a scratch directory (`/root/budget-data`), and `--updates`
writes `update_transactions` payloads. The Note value **appends** `PAIR:<other Transaction ID>`
to the existing note. Nothing is written to the sheet until someone reviews the proposal,
backs up, and says yes. Then the payloads go through the Tiller connector, 100 per call.

```bash
python3 -I scripts/pair_legs.py /root/budget-data/tx.json --config ../my-ops/config.toml \
    --categories ../my-ops/rules/categories.csv --out /root/budget-data/pairs.csv --updates /root/budget-data/pair-updates.json
```

Legs it can't pair (one side on an account Tiller doesn't sync, for example) still need the
`FLAG:identify` treatment by hand.

## If the Category dropdown breaks

Per Tiller's [Troubleshooting the Category dropdown](https://help.tiller.com/en/articles/1550360)
(Google Sheets, checked 2026-11-25), the dropdown is a data-validation rule on the
Transactions Category column that reads its list from the Categories tab. It breaks when
someone inserts rows in Categories, pastes into Transactions without *Values only*, deletes
or reformats either Category column, or moves columns on either tab.

The fix is a direct sheet edit, so back up first and get a yes:

1. Find the Category column on both tabs (Foundation template: Transactions D, Categories A).
2. Select the Transactions Category column, then **Data > Data validation** and open the rule.
3. *Apply to range*: `Transactions!D2:D` (from row 2, so new rows inherit it).
4. *Criteria*: **Dropdown (from a range)**, `=Categories!$A$2:$A$201`. Adjust the letters if
   the columns moved, and the last row if Categories is longer.
5. Advanced: **Reject input**, arrow style (Tiller's recommendation).

Categories past the rule's last row don't show in the dropdown, so check that row before
adding many categories.
