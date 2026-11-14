"""Recompute published synthetic evidence independently of the website."""
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = root / 'web/evidence/f03-costs.csv'
manifest = json.loads((data.parent / 'f03-provenance.json').read_text(encoding='utf-8-sig'))
assert hashlib.sha256(data.read_bytes()).hexdigest() == manifest['csv_sha256']
with data.open(encoding='utf-8-sig', newline='') as stream:
    rows = list(csv.DictReader(stream))
fields = ['units', 'material_price', 'material_per_unit', 'hourly_rate', 'hours_per_unit', 'overhead_per_unit']
def cost(row):
    return row['units'] * (row['material_per_unit'] * row['material_price'] + row['hours_per_unit'] * row['hourly_rate'] + row['overhead_per_unit'])
products = sorted({row['product'] for row in rows})
states, actual = [], []
for product in products:
    for period, destination in [('baseline', states), ('actual', actual)]:
        matches = [row for row in rows if row['product'] == product and row['period'] == period]
        assert len(matches) == 1
        destination.append({key: Decimal(matches[0][key]) for key in fields})
baseline = sum(map(cost, states))
effects = []
previous = baseline
for field in fields:
    for state, target in zip(states, actual):
        state[field] = target[field]
    current = sum(map(cost, states))
    effects.append(current - previous)
    previous = current
assert baseline == 166000 and previous == 225300
assert effects == list(map(Decimal, [22000, -6000, -2700, 4000, 42000, 0]))
assert sum(effects) == previous - baseline == 59300
print('PASS: CSV hash, totals and all six sequential effects match published evidence.')
