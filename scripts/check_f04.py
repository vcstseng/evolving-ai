"""Check synthetic F04 arithmetic and frozen Gen 2 reuse; not proposal-quality approval."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.gen2_analysis import analyze, inspect_evidence

folder = ROOT / 'web/evidence/f04/v1'
read = lambda name: json.loads((folder / name).read_text(encoding='utf-8'))
calc = read('calculation.json')
assert calc == analyze(folder / 'costs.csv')
assert calc['totals'] == {'baseline': '75000', 'actual': '70700', 'variance': '-4300',
                          'flex_baseline': '66000', 'volume_effect': '-9000', 'non_volume_variance': '4700'}
assert calc['fixed_effects']['material_price'] == '7900'
assert calc['fixed_effects']['hours_per_unit'] == '-3200'
assert calc['sensitivity']['adverse_drivers_by_mean'] == ['material_price']
assert not calc['sensitivity']['hours_largest_in_every_order']
assert (calc['sensitivity']['effects']['material_price']['min'], calc['sensitivity']['effects']['material_price']['max']) == ('7900', '9500')
totals = {'baseline': Decimal(0), 'actual': Decimal(0)}
unit_costs = {}
with (folder / 'costs.csv').open(encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f):
        unit = (Decimal(row['material_per_unit']) * Decimal(row['material_price']) +
                Decimal(row['hours_per_unit']) * Decimal(row['hourly_rate']) + Decimal(row['overhead_per_unit']))
        unit_costs[(row['product'], row['period'])] = unit
        totals[row['period']] += Decimal(row['units']) * unit
assert totals == {'baseline': Decimal(75000), 'actual': Decimal(70700)}
assert unit_costs == {('標準接頭', 'baseline'): Decimal(45), ('標準接頭', 'actual'): Decimal(49),
                      ('高壓接頭', 'baseline'): Decimal(60), ('高壓接頭', 'actual'): Decimal(63)}
pub = read('publication.json')
for name, digest in pub['method_sha256_lf'].items():
    assert hashlib.sha256((ROOT / name).read_text(encoding='utf-8').encode()).hexdigest() == digest
original = json.loads((ROOT / 'web/evidence/f03/source-attribution.json').read_text(encoding='utf-8'))
for method in original['methods']:
    assert pub['method_sha256_lf'][method['path']] == method['sha256_lf']
assert pub['method_generation'] == 'gen2' and pub['new_capability'] is False
assert pub['completed_handoffs'] == pub['submissions'] == 6 and pub['rejections'] == 0
assert pub['unseen_test'] is False and pub['external_review'] == 'pending' and pub['model_cost'] is None
assert pub['adjustment'] == 'request_evidence'
assert read('evidence-check.json')['gaps'] == inspect_evidence(folder / 'costs.csv', folder / 'metadata.json')['gaps'] == []
print('PASS: F04 figures, unit costs, material priority and unchanged Gen 2 sources. Handoff counts are author-reported; proposal review pending.')
