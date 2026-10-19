#!/usr/bin/env python3
"""Layer personal AutoCat rules over the toolkit defaults.

AutoCat is first-match-wins, so the merged sheet is: your local rules first, then every
default rule that isn't an exact duplicate of a local one. Columns are the union of both
files, in the defaults' order with any extra local columns appended.

  python3 -I scripts/merge_autocat.py local.csv defaults/autocat.csv > merged.csv

Paste the result into the AutoCat tab with Paste special > Values only, after backing up
the sheet. Never insert rows into the Categories tab to make room for new categories.
"""
import csv
import sys


def read(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        return r.fieldnames or [], list(r)


def key(row):
    return tuple(sorted((k, (v or '').strip().lower()) for k, v in row.items()
                        if k not in ('Description', 'Note') and (v or '').strip()))


def merge(local_rows, default_rows):
    seen = {key(r) for r in local_rows}
    return local_rows + [r for r in default_rows if key(r) not in seen]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    lh, local_rows = read(sys.argv[1])
    dh, default_rows = read(sys.argv[2])
    header = dh + [h for h in lh if h not in dh]
    w = csv.DictWriter(sys.stdout, fieldnames=header, extrasaction='ignore', lineterminator='\n')
    w.writeheader()
    w.writerows(merge(local_rows, default_rows))


if __name__ == '__main__':
    main()
