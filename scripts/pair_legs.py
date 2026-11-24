#!/usr/bin/env python3
"""Propose matching legs for transfers, card payments and loan payments. Never writes the sheet.

A payment from checking to a card, or a move between two of your own accounts, shows up
twice: once as an outflow, once as an inflow of the same amount a day or two apart. This
script finds those pairs where at least one leg is still uncategorized and proposes a
category and a `PAIR:<other Transaction ID>` note token for each blank leg. Applying the
proposal is a separate, approved step through the Tiller connector (update_transactions).

Input (keep it OUTSIDE any git checkout, e.g. /root/budget-data):
  * the JSON that the Tiller connector's query_transactions returns ({"transactions": [...]}), or
  * a CSV download of the Transactions tab (Date, Description, Amount, Account, Category,
    Transaction ID, Note).

  python3 -I scripts/pair_legs.py /root/budget-data/tx.json --config config.toml \
      --out /root/budget-data/pairs.csv [--updates /root/budget-data/pair-updates.json] [--days 3]

Matching rules (all inferred conventions, see docs/categories-and-transfers.md):
  * a categorized row can be a partner only if its category is a transfer-type one: Type
    "Transfer" in the --categories CSV (Category,Group,Type,...), plus any listed in
    [pairing] partner_categories. Purchases and refunds that happen to share an amount
    with a payment are never paired. Without either, every category counts (with a warning);
  * opposite signs, identical absolute amount (to the cent), different accounts,
    dates within --days of each other;
  * each transaction is used at most once; the closest date wins;
  * a tie (two equally close candidates) is reported as `ambiguous`, never guessed.

Proposed category for a blank leg, strongest signal first:
  1. the other leg's category, if it is already categorized (it was a human or a rule)
     and doesn't contradict rules 2 and 3 (a contradiction goes to a person);
  2. `card_payment_category` when either account is listed in [accounts] cards;
  3. `transfer_category` when both accounts are listed in [accounts] cash;
  4. blank, so a person decides (loans, P2P apps, anything not in the config).
"""
import argparse
import csv
import json
import sys
import tomllib
from datetime import date

DEFAULTS = {'days': 3, 'transfer_category': 'Transfer',
            'card_payment_category': 'Debt / Revolving Payment'}

# Transactions-tab header for each normalized field, and the connector's JSON key.
FIELDS = {'id': ('Transaction ID', 'transactionId'), 'date': ('Date', 'date'),
          'desc': ('Description', 'description'), 'amount': ('Amount', 'amount'),
          'account': ('Account', 'account'), 'category': ('Category', 'category'),
          'note': ('Note', 'note')}


def parse_date(s):
    s = str(s).strip()
    if '/' in s:  # sheet display format, M/D/YYYY or M/D/YY
        m, d, y = (int(p) for p in s.split('/'))
        return date(y + 2000 if y < 100 else y, m, d)
    return date.fromisoformat(s[:10])


def parse_amount(v):
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    s = str(v).replace('$', '').replace(',', '').strip()
    neg = s.startswith('(') and s.endswith(')')
    val = float(s.strip('()') or 0)
    return round(-val if neg else val, 2)


def load(path):
    if path.endswith('.json'):
        with open(path) as f:
            raw = json.load(f)
        rows = raw['transactions'] if isinstance(raw, dict) else raw
        key = 1
    else:
        with open(path, newline='', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
        key = 0
    out = []
    for r in rows:
        tx = {k: r.get(cols[key], '') for k, cols in FIELDS.items()}
        if not tx['id']:
            continue  # a row with no Transaction ID can't be updated through the connector
        tx['date'] = parse_date(tx['date'])
        tx['amount'] = parse_amount(tx['amount'])
        tx['category'] = (tx['category'] or '').strip()
        tx['note'] = tx['note'] or ''
        out.append(tx)
    return out


def load_config(path):
    cfg = {'accounts': {'cash': [], 'cards': []}, 'pairing': dict(DEFAULTS)}
    if path:
        with open(path, 'rb') as f:
            for k, v in tomllib.load(f).items():
                cfg.setdefault(k, {}).update(v)
    return cfg


def partner_categories(cfg, categories_csv):
    """Categories a categorized leg may carry and still be a partner, or None for any."""
    allowed = set(cfg['pairing'].get('partner_categories', []))
    if categories_csv:
        with open(categories_csv, newline='', encoding='utf-8-sig') as f:
            allowed |= {r['Category'].strip() for r in csv.DictReader(f)
                        if (r.get('Type') or '').strip() == 'Transfer'}
    return allowed or None


def propose_category(a, b, cfg):
    """Category for the blank leg `a`, given its partner `b`.

    When the partner's category and the account rule disagree, propose nothing: one of the
    two is wrong and a person should say which.
    """
    cash, cards = set(cfg['accounts'].get('cash', [])), set(cfg['accounts'].get('cards', []))
    accts = {a['account'], b['account']}
    p = cfg['pairing']
    rule = why = ''
    if accts & cards:
        rule, why = p['card_payment_category'], 'card account on one side'
    elif accts <= cash and cash:
        rule, why = p['transfer_category'], 'both legs are cash accounts'
    if b['category']:
        if rule and b['category'] != rule:
            return '', f"other leg is {b['category']} but accounts say {rule}; decide by hand"
        return b['category'], 'other leg already categorized'
    return (rule, why) if rule else ('', 'account types not in config; decide by hand')


def pair(txs, days):
    """Return (pairs, ambiguous). Each pair is (outflow, inflow, gap_days)."""
    by_amt = {}
    for t in txs:
        if t['amount']:
            by_amt.setdefault(abs(t['amount']), []).append(t)
    candidates = []
    for group in by_amt.values():
        outs = [t for t in group if t['amount'] < 0]
        ins = [t for t in group if t['amount'] > 0]
        for o in outs:
            for i in ins:
                gap = abs((o['date'] - i['date']).days)
                if o['account'] != i['account'] and gap <= days and (not o['category'] or not i['category']):
                    candidates.append((gap, o, i))
    candidates.sort(key=lambda c: (c[0], c[1]['date'], c[1]['id'], c[2]['id']))
    used, pairs, ambiguous = set(), [], []
    for gap, o, i in candidates:
        if o['id'] in used or i['id'] in used:
            continue
        rivals = [c for c in candidates if c[0] == gap and (c[1] is o) != (c[2] is i)
                  and (c[1] is o or c[2] is i) and c[1]['id'] not in used and c[2]['id'] not in used]
        if rivals:
            ambiguous.append((o, i, gap, len(rivals) + 1))
            used.update({o['id'], i['id']} | {r[1]['id'] for r in rivals} | {r[2]['id'] for r in rivals})
            continue
        used.update({o['id'], i['id']})
        pairs.append((o, i, gap))
    return pairs, ambiguous


def append_token(note, token):
    note = note.strip()
    if token in note.split():
        return note
    return f'{note} {token}'.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('transactions', help='connector JSON or Transactions CSV')
    ap.add_argument('--config')
    ap.add_argument('--days', type=int)
    ap.add_argument('--categories', help='Categories tab CSV; Type=Transfer rows may be partners')
    ap.add_argument('--out', required=True, help='proposal CSV (one row per leg to change)')
    ap.add_argument('--updates', help='also write update_transactions payloads (JSON list)')
    a = ap.parse_args()

    cfg = load_config(a.config)
    days = a.days if a.days is not None else int(cfg['pairing'].get('days', DEFAULTS['days']))
    txs = load(a.transactions)
    allowed = partner_categories(cfg, a.categories)
    if allowed is None:
        print('warning: no --categories or partner_categories; any categorized row may pair', file=sys.stderr)
    else:
        txs = [t for t in txs if not t['category'] or t['category'] in allowed]
    pairs, ambiguous = pair(txs, days)

    rows, updates = [], []
    for o, i, gap in pairs:
        for leg, other in ((o, i), (i, o)):
            if leg['category']:
                continue
            cat, why = propose_category(leg, other, cfg)
            note = append_token(leg['note'], f"PAIR:{other['id']}")
            rows.append({'status': 'proposed' if cat else 'needs_category',
                         'transaction_id': leg['id'], 'date': leg['date'].isoformat(),
                         'account': leg['account'], 'description': leg['desc'],
                         'amount': f"{leg['amount']:.2f}", 'proposed_category': cat,
                         'reason': why, 'new_note': note, 'other_id': other['id'],
                         'other_account': other['account'], 'other_category': other['category'],
                         'gap_days': gap})
            if cat:
                updates.append({'transactionId': leg['id'], 'values': {'Category': cat, 'Note': note}})
    for o, i, gap, n in ambiguous:
        for leg, other in ((o, i), (i, o)):
            if not leg['category']:
                rows.append({'status': f'ambiguous ({n} candidates)', 'transaction_id': leg['id'],
                             'date': leg['date'].isoformat(), 'account': leg['account'],
                             'description': leg['desc'], 'amount': f"{leg['amount']:.2f}",
                             'proposed_category': '', 'reason': 'tie on amount and date gap',
                             'new_note': leg['note'], 'other_id': other['id'],
                             'other_account': other['account'], 'other_category': other['category'],
                             'gap_days': gap})

    cols = ['status', 'transaction_id', 'date', 'account', 'description', 'amount',
            'proposed_category', 'reason', 'new_note', 'other_id', 'other_account',
            'other_category', 'gap_days']
    with open(a.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r['status'] != 'proposed', r['date'])))
    if a.updates:
        with open(a.updates, 'w') as f:
            json.dump(updates, f, indent=1)

    blank = sum(1 for t in txs if not t['category'])
    print(f'{len(txs)} transactions, {blank} uncategorized, window ±{days} days')
    print(f'{len(pairs)} pairs; {len(updates)} legs with a proposed category, '
          f'{sum(r["status"] == "needs_category" for r in rows)} paired but need a category, '
          f'{len(ambiguous)} ambiguous')
    print(f'proposal: {a.out}' + (f'; update payloads: {a.updates}' if a.updates else ''))
    print('Nothing was written to the sheet. Apply only after review, a backup, and a yes.')


if __name__ == '__main__':
    sys.exit(main())
