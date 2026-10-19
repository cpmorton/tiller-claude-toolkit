#!/usr/bin/env python3
"""Quick-wins spending review over Tiller exports.

Answers "where is the money actually going?" with card payments removed, so purchases
aren't counted twice when the checking-side payment is (mis)categorized as an expense.

Inputs (CSV downloads of the sheet tabs; keep them OUTSIDE any git checkout):
  transactions.csv  Transactions tab (needs Date, Description, Category, Amount, Account)
  categories.csv    Categories tab   (needs Category, Type)
  config.toml       your account names and payment patterns (see config.example.toml)

  python3 -I scripts/spend_analysis.py transactions.csv categories.csv --config config.toml \
      [--from 2025-10-01] [--to 2026-09-30]
"""
import argparse
import re
import sys
import tomllib  # stdlib since 3.11; no PyYAML dependency for config

import pandas as pd

DEFAULT_CONFIG = {
    'accounts': {'cash': []},
    'card_payments': {'patterns': [r'credit (card|crd)', r'card (payment|pmt)', r'\bepay', r'american express',
                                   r'autopay', r'citi card']},
    'income': {'categories': ['Paycheck']},
    'fees': {'categories': ['Credit Card Fees/Interest', 'Bank Fees']},
}


def load_config(path):
    cfg = {k: dict(v) for k, v in DEFAULT_CONFIG.items()}
    if path:
        with open(path, 'rb') as f:
            for k, v in tomllib.load(f).items():
                cfg.setdefault(k, {}).update(v)
    return cfg


def load(tx_csv, cats_csv, cfg):
    df = pd.read_csv(tx_csv, dtype=str).fillna('')
    need = {'Date', 'Description', 'Category', 'Amount', 'Account'}
    if not need <= set(df.columns):
        sys.exit(f'{tx_csv}: missing columns {sorted(need - set(df.columns))}')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amt'] = df['Amount'].str.replace(r'[$,]', '', regex=True).astype(float)
    cats = pd.read_csv(cats_csv, dtype=str).fillna('')
    tmap = dict(zip(cats['Category'].str.strip(), cats['Type'].str.strip()))
    # Uncategorized = blank (needs tagging); Unknown = name missing from Categories (sheet defect)
    df['Type'] = df['Category'].map(lambda c: 'Uncategorized' if c == '' else tmap.get(c, 'Unknown'))
    df['M'] = df['Date'].dt.to_period('M')
    rx = re.compile('|'.join(f'(?:{p})' for p in cfg['card_payments']['patterns']), re.I)
    cash = df['Account'].isin(cfg['accounts']['cash']) if cfg['accounts']['cash'] else True
    df['is_cardpay'] = df['Description'].map(lambda d: bool(rx.search(d))) & cash & (df['Amt'] < 0)
    df['spend'] = (df['Type'] == 'Expense') & ~df['is_cardpay']
    return df


def monthly_gap(x, cfg):
    m = pd.DataFrame({
        'income': x[x.Category.isin(cfg['income']['categories'])].groupby('M').Amt.sum(),
        'spend': x[x.spend].groupby('M').Amt.sum(),
        'fees_interest': x[x.Category.isin(cfg['fees']['categories'])].groupby('M').Amt.sum(),
    }).fillna(0)
    m['gap'] = m.income + m.spend
    return m.round(0)


def recurring(x, min_months=3):
    """Same merchant string at ~the same amount in >= min_months distinct months."""
    e = x[x.spend & (x.Amt < 0)].copy()
    e['amt'] = e.Amt.round(0)
    g = e.groupby(['Description', 'amt']).agg(months=('M', 'nunique'), total=('Amt', 'sum'),
                                               last=('Date', 'max'), account=('Account', 'first'))
    return g[g.months >= min_months].sort_values('total')


def by_category(x, months):
    g = x[x.spend].groupby('Category').Amt.agg(total='sum', n='size')
    g['per_month'] = g.total / months
    return g.sort_values('total').round(0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('transactions'); ap.add_argument('categories')
    ap.add_argument('--config')
    ap.add_argument('--from', dest='start'); ap.add_argument('--to', dest='end')
    a = ap.parse_args()
    cfg = load_config(a.config)
    pd.set_option('display.width', 200); pd.set_option('display.max_rows', 300)

    df = load(a.transactions, a.categories, cfg)
    x = df
    if a.start: x = x[x.Date >= a.start]
    if a.end: x = x[x.Date <= a.end]
    months = max(x.M.nunique(), 1)

    print('== Data quality ==')
    print(x.Type.value_counts().to_string())
    print('\n== Card payments filed as Expense (excluded from spend) ==')
    print(x[x.is_cardpay & (x.Type == 'Expense')].groupby('Category').Amt.agg(['sum', 'size']).round(0).to_string())
    print('\n== Monthly income vs real spend ==')
    gap = monthly_gap(x, cfg)
    print(gap.to_string()); print('avg/month:', (gap.sum() / months).round(0).to_dict())
    print('\n== Spend by category ==');      print(by_category(x, months).to_string())
    print('\n== Recurring charges (>=3 months) =='); print(recurring(x).head(60).to_string())


if __name__ == '__main__':
    main()
