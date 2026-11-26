# Tags and notes

Categories answer "what kind of spending is this". Tags and notes answer everything else:
which trip, which order, which debt, what still needs a person. This page is the convention
the toolkit's scripts and agents follow.

> **Recommended setup (2026-11):** add a Tiller **Tags** column and put **labels** (what the
> money was for, like `TRIP:`) there, where the Tags Report can total them. **Workflow
> markers** (`FLAG:`, `TODO:`, `PAIR:`, `SWEEP:`) and free text stay in **Note**. The scripts
> (`lint_autocat.py`, `merge_autocat.py`, `pair_legs.py`) and the default rules still read and
> write Note only; Tags support in them is pending. See [Adding a Tags column](#adding-a-tags-column).

## Token syntax

Both columns use `KEY:value`, with no space after the colon. They differ in the separator:

```text
Tags:  TRIP:Lisbon May 2026,GIFT:Xmas 2026        (comma, no space)
Note:  PAIR:aB3dE9fG; SWEEP:2026-Q3              (semicolon, space)
Note:  FLAG:identify; TODO:find receipt
```

- **KEY** is upper case, no spaces. **value** may contain spaces, never `;` or `,`.
- **Tags** follow Tiller's rule: comma-separated, no space between tags, matched exactly by
  the Tags Report. A `KEY:` prefix still lets a filter like "starts with `TRIP:`" find every trip.
- **Append, never overwrite.** Read the row's current Note right before writing and add
  `; <token>` at the end. Two writers on the same rows at the same time lose each other's
  tokens, so one task owns a column's writes at a time.
- Free text is allowed before or between tokens. Agents leave it alone.
- Pick a value format and keep it: a tag is only as useful as its exact spelling.
  `TRIP:Lisbon May 2026` and `TRIP:Lisbon 2026-05` are two different trips to any filter.

## Default tokens

Two kinds. **Labels** say what the money was for, and are worth a total, so they go in Tags.
**Workflow markers** say what still needs doing, and go away (or stop mattering) once it's
done, so they stay in Note: a dollar total for "identify" tells you nothing.

| Token | Kind | Column | Meaning | Written by |
|---|---|---|---|---|
| `TRIP:<name>` | label | Tags | Spending on one trip. Pick one format, e.g. `<place> <Mon yyyy>` | Agent or person, after review |
| `PLAN:<purchase>` | label | Tags | A pay-over-time plan fee and the purchase it finances | Agent or person |
| `CARD:<debt>` | label | Tags | Which card or loan a payment pays, when the description doesn't say | Agent or person |
| `AMZ:<short item>` | detail | Note | What an Amazon (or other marketplace) charge bought, from your order history. Not a tag: the merchant already says Amazon | Agent matching an order export |
| `AMZ:pending` | marker | Note | Marketplace charge not yet matched to an order | AutoCat default rule |
| `PAIR:<other Transaction ID>` | marker | Note | The other leg of a transfer or card payment | `pair_legs.py` proposal, applied after review |
| `FLAG:identify` | marker | Note | Nobody knows what this is yet | AutoCat default rules, sweeps |
| `FLAG:unmatched-leg` | marker | Note | A payment or transfer whose other leg wasn't found | Sweeps |
| `REVIEW:<why>` | marker | Note | Categorized, but a person should look | Rules, agents |
| `TODO:<what>` | marker | Note | A specific follow-up | Anyone |
| `SWEEP:<yyyy>-Q<n>` | marker | Note | Row was finalized in that quarter's sweep | [Quarterly sweep](quarterly-sweep.md) |

Without a Tags column, labels go in Note as tokens like everything else.

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

Ask Claude, or have it run this through the Tiller connector. The connector exposes both
columns as the `tags` and `note` fields; use whichever holds the label:

```json
{ "filter": { "tags": { "$regex": "TRIP:Lisbon May 2026" } },
  "aggregate": { "groupBy": "category", "functions": ["sum", "count"] } }
```

In the sheet itself: the Tags Report (one total per tag, with a category breakdown), a filter
view ("Text contains"), or a `=SUMIFS(Transactions!E:E, Transactions!W:W, "*TRIP:Lisbon May 2026*")`
formula (adjust the column letters to your sheet). Don't add a "filter by condition" on Date in the
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

## Adding a Tags column

What Tiller supports today (checked 2026-11):

- A column titled exactly **Tags** is a supported, non-automated Transactions column. Tiller
  never fills it. The Tags Report in the Tiller Community Solutions add-on adds it at the far
  right of Transactions; you can also add a column titled `Tags` yourself, after a backup.
  Add it as the **last** column, never between existing columns. This is the one exception
  to the "never insert columns" rule in [CLAUDE.md](../CLAUDE.md).
- Multiple tags are comma-separated with **no space** between them; spaces inside a tag
  are fine (`Lisbon May 2026`). The Tags Report matches tags exactly.
- The Tags Report gives a total and count per tag over a date range, and a category
  breakdown for one tag.
- The Tiller connector already exposes a `tags` field on every transaction, so agents can
  filter on it once the column exists.

**Moving existing labels out of Note:** back up, then for each row move the label tokens
(`TRIP:`, `PLAN:`, `CARD:`, your own) into Tags and leave the markers in Note, in batches of
100 or fewer through the connector's `update_transactions`, with an undo list of old and new
values. Only one task writes either column while that runs.

**Not yet supported by the scripts:** `lint_autocat.py` accepts only Category, Description and
Note as AutoCat override columns, so a rule that writes Tags fails the lint, and `pair_legs.py`
reads Note only. Until those change, AutoCat rules shouldn't write tags.

Not to be confused with **Import Tag**: a Foundation Template column that marks rows that
came in through Tiller's CSV import. It isn't a tag and holds nothing of yours.

Sources:
- [Transactions sheet columns](https://help.tiller.com/en/articles/432681-transactions-sheet-columns) (updated 2026-10-15)
- [How to use AutoCat](https://help.tiller.com/en/articles/3792984-autocat-for-google-sheets) (updated 2026-08-25)
- [Docs: Tags Report for transaction tagging](https://community.tiller.com/t/docs-tags-report-for-transaction-tagging/375)
- [Direct Fills troubleshooting](https://help.tiller.com/en/articles/13177613-direct-fills-for-google-sheets)
