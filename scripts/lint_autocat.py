#!/usr/bin/env python3
"""Lint an AutoCat rules CSV (File > Download > CSV of the AutoCat tab).

Catches the mistakes that silently break categorization:
  * unbalanced quotes / stray commas in Contains cells (a term that never matches)
  * categories missing from the Categories sheet (rows land as "Unknown" in reports)
  * rules with a category but no criteria
  * "$50"-style amounts, bad Amount Polarity, invalid regex
  * exact duplicate rules, and rules shadowed by an earlier, broader one
    (first match wins, so a shadowed rule can never fire)

With --transactions it also replays the rules against a Transactions CSV export and
reports coverage and rules that never fire.

  python3 -I scripts/lint_autocat.py rules.csv [--categories categories.csv] [--transactions tx.csv]
Exit status: 1 if any ERROR, else 0.
"""
import argparse
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autocat import CONTAINS_COLS, FILTER_COLS, first_match, load_rules  # noqa: E402


def shadowed_by(later, earlier):
    """True if `earlier` matches every transaction `later` can match.

    Conservative: only reasons about rules whose sole criterion is Description Contains
    on the earlier side. Any extra criterion on `later` only narrows it, so still shadowed.
    """
    if not earlier.category or not earlier.terms['Description Contains']:
        return False
    other = [c for c in FILTER_COLS if c != 'Description Contains' and (earlier.row.get(c) or '').strip()]
    if other:
        return False
    a_terms = earlier.terms['Description Contains']
    b_terms = later.terms['Description Contains']
    return bool(b_terms) and all(any(a in b for a in a_terms) for b in b_terms)


def lint(rules, categories=None):
    findings = []  # (level, row, message)
    seen = {}
    for r in rules:
        if not r.category and r.has_criteria:
            findings.append(('ERROR', r.index, 'criteria but no Category'))
        if r.category and not r.has_criteria:
            findings.append(('ERROR', r.index, f'{r.category!r} has no criteria'))
        if categories is not None and r.category and r.category not in categories:
            findings.append(('ERROR', r.index, f'category {r.category!r} not in Categories sheet'))
        for p in r.problems:
            level = 'WARN' if p.startswith('non-numeric amount') else 'ERROR'
            findings.append((level, r.index, p))
        key = tuple((r.row.get(c) or '').strip().lower() for c in ['Category'] + FILTER_COLS)
        if r.category and key in seen:
            findings.append(('WARN', r.index, f'duplicate of row {seen[key]}'))
        else:
            seen.setdefault(key, r.index)
    for i, b in enumerate(rules):
        for a in rules[:i]:
            if a.category != b.category and shadowed_by(b, a):
                findings.append(('WARN', b.index,
                                 f'shadowed by row {a.index} ({a.category!r}); first match wins'))
                break
    return sorted(findings, key=lambda f: (f[1], f[0]))


def replay(rules, tx_path):
    hits, total, uncovered = Counter(), 0, Counter()
    with open(tx_path, newline='', encoding='utf-8-sig') as f:
        for tx in csv.DictReader(f):
            total += 1
            tx['Amount'] = float(str(tx.get('Amount', '0')).replace('$', '').replace(',', '') or 0)
            r = first_match(rules, tx)
            if r:
                hits[r.index] += 1
            else:
                uncovered[tx.get('Description', '')[:40]] += 1
    return total, hits, uncovered


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('rules')
    ap.add_argument('--categories', help='Categories CSV export (needs a Category column)')
    ap.add_argument('--transactions', help='Transactions CSV export to replay rules against')
    a = ap.parse_args()

    header, rules = load_rules(a.rules)
    missing = [c for c in ['Category', 'Description Contains'] if c not in header]
    if missing:
        sys.exit(f'{a.rules}: missing required columns {missing}')
    unknown = [h for h in header if h and h not in FILTER_COLS + ['Category', 'Description', 'Note']]
    cats = None
    if a.categories:
        with open(a.categories, newline='', encoding='utf-8-sig') as f:
            cats = {r['Category'].strip() for r in csv.DictReader(f) if r.get('Category')}

    findings = lint(rules, cats)
    for h in unknown:
        print(f'INFO  header {h!r} is not a filter this linter knows; passed through')
    for level, row, msg in findings:
        print(f'{level:5} row {row}: {msg}')
    n_err = sum(1 for f in findings if f[0] == 'ERROR')
    print(f'\n{len(rules)} rules, {n_err} errors, {len(findings) - n_err} warnings')

    if a.transactions:
        total, hits, uncovered = replay(rules, a.transactions)
        covered = sum(hits.values())
        print(f'\nReplay: {covered}/{total} transactions matched a rule ({covered / max(total, 1):.0%})')
        dead = [r.index for r in rules if r.category and r.has_criteria and r.index not in hits]
        print(f'Rules that never fired: {len(dead)} (rows {", ".join(map(str, dead[:40]))}{" ..." if len(dead) > 40 else ""})')
        print('Top unmatched descriptions (rule candidates):')
        for desc, n in uncovered.most_common(15):
            print(f'  {n:4}  {desc}')
    sys.exit(1 if n_err else 0)


if __name__ == '__main__':
    main()
