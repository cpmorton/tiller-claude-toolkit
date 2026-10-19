"""Shared AutoCat sheet model: parse rules exported from the AutoCat tab and evaluate them.

Semantics mirror Tiller's AutoCat as documented in
https://help.tiller.com/en/articles/3792984-how-to-use-autocat-for-automatic-categorization :
rules run top-down and the first match wins; "Contains" matching is case-insensitive;
Amount Min/Max are absolute values; Amount Polarity is an optional extra column.

Two details are inferred, not documented, and kept in one place so they're easy to fix:
  * a "Contains" cell with double quotes is a comma-separated list of quoted terms;
    without quotes it is one literal term (commas included).
  * Regex columns are evaluated with Python `re`; Tiller runs JavaScript regex, which
    agrees for the simple patterns rules normally use.
"""
import csv
import io
import re

# Rule columns that filter a transaction. Headers outside this set are carried through
# untouched (Description, Note, and Tiller's override columns).
CONTAINS_COLS = ['Description Contains', 'Full Description Contains', 'Account Contains',
                 'Institution Contains']
REGEX_COLS = {'Description Regex': 'Description', 'Category Hint Regex': 'Category Hint',
              'Full Description Regex': 'Full Description'}
AMOUNT_COLS = ['Amount Min', 'Amount Max']
FILTER_COLS = CONTAINS_COLS + list(REGEX_COLS) + AMOUNT_COLS + ['Amount Polarity']


def parse_terms(cell):
    """Return (terms, problems) for a Contains cell."""
    cell = (cell or '').strip()
    if not cell:
        return [], []
    if '"' not in cell:
        return [cell.lower()], []
    problems = []
    if cell.count('"') % 2:
        problems.append('unbalanced double quotes')
    row = next(csv.reader(io.StringIO(cell), skipinitialspace=True), [])
    terms = [t.strip() for t in row]
    if any(t == '' for t in terms):
        problems.append('empty term (stray comma)')
    return [t.lower() for t in terms if t], problems


def parse_amount(cell):
    """Return (value or None, problem or None). Accepts '50', '50.00'; flags '$50'."""
    cell = (cell or '').strip()
    if not cell:
        return None, None
    try:
        return abs(float(cell)), None
    except ValueError:
        try:
            return abs(float(cell.replace('$', '').replace(',', ''))), f'non-numeric amount {cell!r}'
        except ValueError:
            return None, f'unparseable amount {cell!r}'


class Rule:
    def __init__(self, row, index):
        self.row = row
        self.index = index  # 1-based sheet row, header = 1
        self.category = (row.get('Category') or '').strip()
        self.problems = []
        self.terms = {}
        for col in CONTAINS_COLS:
            terms, probs = parse_terms(row.get(col))
            self.terms[col] = terms
            self.problems += [f'{col}: {p}' for p in probs]
        self.regex = {}
        for col in REGEX_COLS:
            pat = (row.get(col) or '').strip()
            if pat:
                try:
                    self.regex[col] = re.compile(pat, re.I)
                except re.error as e:
                    self.problems.append(f'{col}: invalid regex ({e})')
        self.amin, p1 = parse_amount(row.get('Amount Min'))
        self.amax, p2 = parse_amount(row.get('Amount Max'))
        self.problems += [p for p in (p1, p2) if p]
        self.polarity = (row.get('Amount Polarity') or '').strip().lower()
        if self.polarity not in ('', 'positive', 'negative'):
            self.problems.append(f'Amount Polarity must be Positive/Negative, got {self.polarity!r}')

    @property
    def has_criteria(self):
        return any(self.terms.values()) or bool(self.regex) or self.amin is not None \
            or self.amax is not None or bool(self.polarity)

    def matches(self, tx):
        """tx: dict with Transactions-sheet headers; Amount as float."""
        field_for = {'Description Contains': 'Description',
                     'Full Description Contains': 'Full Description',
                     'Account Contains': 'Account', 'Institution Contains': 'Institution'}
        for col, terms in self.terms.items():
            if terms:
                hay = str(tx.get(field_for[col], '')).lower()
                if not any(t in hay for t in terms):
                    return False
        for col, rx in self.regex.items():
            if not rx.search(str(tx.get(REGEX_COLS[col], ''))):
                return False
        amt = float(tx.get('Amount', 0) or 0)
        if self.amin is not None and abs(amt) < self.amin:
            return False
        if self.amax is not None and abs(amt) > self.amax:
            return False
        if self.polarity == 'positive' and amt <= 0:
            return False
        if self.polarity == 'negative' and amt >= 0:
            return False
        return self.has_criteria


def load_rules(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rules = [Rule(r, i + 2) for i, r in enumerate(reader)]
        return reader.fieldnames or [], rules


def first_match(rules, tx):
    for r in rules:
        if r.category and r.matches(tx):
            return r
    return None
