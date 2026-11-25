# Tags and notes

Categories answer "what kind of spending is this". Tags and notes answer everything else:
which trip, which order, which debt, what still needs a person. This page is the convention
the toolkit's scripts and agents follow.

> **Status (2026-11):** tags live as tokens in the **Note** column. Moving the
> "what was it for" tokens to a Tiller **Tags** column is planned and not done yet. The
> scripts (`lint_autocat.py`, `merge_autocat.py`, `pair_legs.py`) and the default rules all
> assume Note tokens today. See [Moving to a Tags column](#moving-to-a-tags-column-pending).

## Token syntax

A token is `KEY:value`. Several tokens on one row are separated by `; ` (semicolon, space):

```text
PAIR:aB3dE9fG; SWEEP:2026-Q3
TRIP:Lisbon May 2026
FLAG:identify; TODO:find receipt
```

- **KEY** is upper case, no spaces. **value** may contain spaces, never `;`.
- **Append, never overwrite.** Read the row's current Note right before writing and add
  `; <token>` at the end. Two writers on the same rows at the same time lose each other's
  tokens, so one task owns a column's writes at a time.
- Free text is allowed before or between tokens. Agents leave it alone.
- Pick a value format and keep it: a tag is only as useful as its exact spelling.
  `TRIP:Lisbon May 2026` and `TRIP:Lisbon 2026-05` are two different trips to any filter.

## Default tokens

Two kinds. **Labels** say what the money was for, and are worth a total. **Workflow markers**
say what still needs doing, and go away (or stop mattering) once it's done.

| Token | Kind | Meaning | Written by |
|---|---|---|---|
| `TRIP:<name>` | label | Spending on one trip. Pick one format, e.g. `<place> <Mon yyyy>` | Agent or person, after review |
| `AMZ:<short item>` | label | What an Amazon (or other marketplace) charge bought, from your order history | Agent matching an order export |
| `AMZ:pending` | marker | Marketplace charge not yet matched to an order | AutoCat default rule |
| `PLAN:<purchase>` | label | A pay-over-time plan fee and the purchase it finances | Agent or person |
| `CARD:<debt>` | label | Which card or loan a payment pays, when the description doesn't say | Agent or person |
| `PAIR:<other Transaction ID>` | marker | The other leg of a transfer or card payment | `pair_legs.py` proposal, applied after review |
| `FLAG:identify` | marker | Nobody knows what this is yet | AutoCat default rules, sweeps |
| `FLAG:unmatched-leg` | marker | A payment or transfer whose other leg wasn't found | Sweeps |
| `REVIEW:<why>` | marker | Categorized, but a person should look | Rules, agents |
| `TODO:<what>` | marker | A specific follow-up | Anyone |
| `SWEEP:<yyyy>-Q<n>` | marker | Row was finalized in that quarter's sweep | [Quarterly sweep](quarterly-sweep.md) |

Add your own keys in your private repo's CLAUDE.md. A good new key is something you'd want
summed or filtered across categories. If you'd want it on every row of one category, it's
probably a category (or a subcategory) instead.

## Tag or category?

- **Category**: one per row, mutually exclusive, budgeted. "Restaurants".
- **Label token / tag**: cuts across categories. A trip has flights, hotels, restaurants and
  gifts; `TRIP:` lets you total all of it without changing any category.
- **Subcategory-style tags** work the same way: `GIFT:Xmas 2026` across Clothing, Toys and
  Books. Tiller has no subcategory column; a prefixed tag is the usual substitute.

## Finding tagged rows

Ask Claude, or have it run this through the Tiller connector (a filter on the `note` field):

```json
{ "filter": { "note": { "$regex": "TRIP:Lisbon May 2026" } },
  "aggregate": { "groupBy": "category", "functions": ["sum", "count"] } }
```

In the sheet itself: use a filter view on the Note column ("Text contains"), or a
`=SUMIFS(Transactions!E:E, Transactions!V:V, "*TRIP:Lisbon May 2026*")` formula
(adjust the column letters to your sheet). Don't add a "filter by condition" on Date in the
Transactions tab itself: Tiller's Direct Fills troubleshooting article lists it as a fill
blocker. Use a filter view or another tab.

## AutoCat and notes: the one big risk

AutoCat rules can write any column, including Note and Tags (add the column to the AutoCat
tab as an override column). Tiller's AutoCat article says **Run Rules on All** "will
overwrite existing categorizations where a rule matches". Treat override columns the same
way: one click can replace a row's whole hand-built Note with the rule's token.

- Normal **Run AutoCat** and **Auto Run on Fill** only touch rows that are still
  uncategorized, so they're safe.
- Before ever using Run Rules on All, back up ([backups](backups.md)) and remove the Note
  override from rules whose rows carry hand-written tokens.

## Moving to a Tags column (pending)

What Tiller supports today (checked 2026-11):

- A column titled exactly **Tags** is a supported, non-automated Transactions column. Tiller
  never fills it. The Tags Report in the Tiller Community Solutions add-on adds it at the far
  right of Transactions; you can also insert a column titled `Tags` yourself. Insert it to
  the right of existing columns, never between core columns.
- Multiple tags are comma-separated with **no space** between them; spaces inside a tag
  are fine (`Lisbon May 2026`). The Tags Report matches tags exactly.
- The Tags Report gives a total and count per tag over a date range, and a category
  breakdown for one tag.
- The Tiller connector already exposes a `tags` field on every transaction, so agents can
  filter on it once the column exists.

The likely split, once decided: **labels** (`TRIP`, `GIFT`, ...) move to Tags, where the Tags
Report can total them; **workflow markers** (`FLAG`, `TODO`, `SWEEP`, `PAIR`) stay in Note,
because a dollar total for "identify" tells you nothing. Until that lands in this repo, keep
everything in Note. The move needs script changes first: `lint_autocat.py` only accepts
Category, Description and Note as override columns.

Not to be confused with **Import Tag**: a Foundation Template column that marks rows that
came in through Tiller's CSV import. It isn't a tag and holds nothing of yours.

Sources:
- [Transactions sheet columns](https://help.tiller.com/en/articles/432681-transactions-sheet-columns) (updated 2026-10-15)
- [How to use AutoCat](https://help.tiller.com/en/articles/3792984-autocat-for-google-sheets) (updated 2026-08-25)
- [Docs: Tags Report for transaction tagging](https://community.tiller.com/t/docs-tags-report-for-transaction-tagging/375)
- [Direct Fills troubleshooting](https://help.tiller.com/en/articles/13177613-direct-fills-for-google-sheets)
