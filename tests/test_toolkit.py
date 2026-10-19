import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

from autocat import Rule, first_match, load_rules, parse_terms  # noqa: E402
from lint_autocat import lint  # noqa: E402
from merge_autocat import merge  # noqa: E402
import spend_analysis  # noqa: E402

FIX = os.path.join(ROOT, 'tests', 'fixtures')


def rule(**kw):
    return Rule({k.replace('_', ' '): v for k, v in kw.items()}, index=2)


def test_parse_terms_quoted_and_broken():
    assert parse_terms('"Whole Foods","Wholefds"') == (['whole foods', 'wholefds'], [])
    assert parse_terms('Publix') == (['publix'], [])
    _, probs = parse_terms('"thrift","goodwill",')
    assert 'empty term (stray comma)' in probs
    _, probs = parse_terms('"dsw","thrift\\",goodwill"')
    assert probs  # unbalanced quotes


def test_first_match_wins_and_specific_first():
    rules = [rule(Category='Fuel/Gas', Description_Contains='"Costco Gas"'),
             rule(Category='Categorize Later', Description_Contains='Costco')]
    rules[1].index = 3
    gas = {'Description': 'Costco Gas #9', 'Amount': -45.0}
    whse = {'Description': 'Costco Whse #9', 'Amount': -210.0}
    assert first_match(rules, gas).category == 'Fuel/Gas'
    assert first_match(rules, whse).category == 'Categorize Later'


def test_polarity_and_amount_bounds():
    r = rule(Category='Debt Minimum Payment', Description_Contains='Amex Epayment',
             Amount_Max='350', Amount_Polarity='Negative')
    assert r.matches({'Description': 'Amex Epayment', 'Amount': -300})
    assert not r.matches({'Description': 'Amex Epayment', 'Amount': -2000})
    assert not r.matches({'Description': 'Amex Epayment', 'Amount': 300})


def test_lint_flags_shadowed_unknown_and_dollar_amounts():
    a = rule(Category='Groceries - Food/Household', Description_Contains='Harris Teeter')
    b = rule(Category='Fuel/Gas', Description_Contains='harris teeter fuel')
    c = rule(Category='Nails/Makeup/Spa', Description_Contains='glossy nails', Amount_Min='$50')
    b.index, c.index = 3, 4
    msgs = [m for _, _, m in lint([a, b, c], categories={'Groceries - Food/Household', 'Fuel/Gas'})]
    assert any('shadowed by row 2' in m for m in msgs)
    assert any("not in Categories sheet" in m for m in msgs)
    assert any('non-numeric amount' in m for m in msgs)


def test_defaults_lint_clean():
    _, rules = load_rules(os.path.join(ROOT, 'defaults', 'autocat.csv'))
    with open(os.path.join(ROOT, 'defaults', 'categories.csv'), newline='') as f:
        cats = {r['Category'] for r in csv.DictReader(f)}
    errors = [f for f in lint(rules, cats) if f[0] == 'ERROR']
    assert errors == []


def test_defaults_on_fixture():
    _, rules = load_rules(os.path.join(ROOT, 'defaults', 'autocat.csv'))
    with open(os.path.join(FIX, 'transactions.csv'), newline='') as f:
        rows = list(csv.DictReader(f))
    got = {}
    for tx in rows:
        tx['Amount'] = float(tx['Amount'].replace('$', '').replace(',', ''))
        m = first_match(rules, tx)
        got[(tx['Description'], tx['Account'])] = m.category if m else None
    assert got[('Chase Credit Crd', 'Sample Checking')] == 'Debt / Revolving Payment'
    assert got[('Payment Thank You - Web', 'Sample Visa')] == 'Debt / Revolving Payment'
    assert got[('Costco Gas #9', 'Sample Visa')] == 'Fuel/Gas'
    assert got[('Costco Whse #9', 'Sample Visa')] == 'Categorize Later'
    assert got[('Acme Payroll', 'Sample Checking')] == 'Paycheck'
    # P2P inflow hinted as wages must NOT become Paycheck
    assert got[('Venmo', 'Sample Venmo')] == 'Categorize Later'


def test_merge_puts_local_first_and_dedupes():
    local = [{'Category': 'Gym/Fitness', 'Description Contains': 'Acme Dojo'}]
    defaults = [{'Category': 'Gym/Fitness', 'Description Contains': 'acme dojo', 'Note': 'x'},
                {'Category': 'Fuel/Gas', 'Description Contains': 'Shell'}]
    out = merge(local, defaults)
    assert [r['Description Contains'] for r in out] == ['Acme Dojo', 'Shell']


def test_spend_analysis_excludes_card_payments(tmp_path):
    cats = tmp_path / 'categories.csv'
    cats.write_text(open(os.path.join(ROOT, 'defaults', 'categories.csv')).read())
    cfg = spend_analysis.load_config(None)
    cfg['accounts']['cash'] = ['Sample Checking']
    df = spend_analysis.load(os.path.join(FIX, 'transactions.csv'), str(cats), cfg)
    pay = df[df.Description == 'Chase Credit Crd'].iloc[0]
    assert pay.is_cardpay and not pay.spend
    rec = spend_analysis.recurring(df)
    assert 'Streamco Monthly' in rec.index.get_level_values(0)


def test_cli_lint_exit_codes(tmp_path):
    bad = tmp_path / 'bad.csv'
    with open(bad, 'w', newline='') as f:  # csv.writer so the cell content survives CSV quoting
        csv.writer(f).writerows([['Category', 'Description Contains'],
                                 ['Fuel/Gas', '"shell",'], ['Technology/Computer/Electronics', '']])
    p = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'scripts', 'lint_autocat.py'), str(bad)],
                       capture_output=True, text=True)
    assert p.returncode == 1 and 'has no criteria' in p.stdout
