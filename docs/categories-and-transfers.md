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
