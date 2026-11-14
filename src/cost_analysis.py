"""Deterministic accounting attribution; no causal or savings inference."""
import csv
from decimal import Decimal, InvalidOperation

ORDER = ['units', 'material_price', 'material_per_unit', 'hourly_rate', 'hours_per_unit', 'overhead_per_unit']


def analyze(path):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not set(['product', 'period', *ORDER]).issubset(reader.fieldnames or []):
            raise ValueError('Missing required cost columns')
        pairs = {}
        for raw in reader:
            key = (raw['product'].strip(), raw['period'].strip())
            if not key[0] or key[1] not in ('baseline', 'actual') or key in pairs:
                raise ValueError('Invalid product/period or duplicate record')
            try:
                row = {field: Decimal(raw[field]) for field in ORDER}
            except (InvalidOperation, TypeError):
                raise ValueError('Missing or invalid numeric value') from None
            if any(not value.is_finite() or value < 0 for value in row.values()):
                raise ValueError('Numbers must be finite and nonnegative')
            if row['units'] != row['units'].to_integral_value():
                raise ValueError('Units must be whole numbers')
            pairs[key] = row
    products = sorted({product for product, _ in pairs})
    if not products or any((product, period) not in pairs for product in products for period in ('baseline', 'actual')):
        raise ValueError('Each product requires baseline and actual records')
    states = [pairs[p, 'baseline'].copy() for p in products]
    actual = [pairs[p, 'actual'] for p in products]

    def total():
        return sum((r['units'] * (r['material_per_unit'] * r['material_price'] + r['hours_per_unit'] * r['hourly_rate'] + r['overhead_per_unit']) for r in states), Decimal(0))

    baseline = previous = total()
    effects = []
    for field in ORDER:
        for row, target in zip(states, actual):
            row[field] = target[field]
        current = total()
        effects.append({'field': field, 'amount': str(current - previous)})
        previous = current
    assert sum(Decimal(e['amount']) for e in effects) == previous - baseline
    return {'baseline': str(baseline), 'actual': str(previous), 'variance': str(previous - baseline),
            'effects': effects, 'products': products, 'row_count': len(pairs),
            'limitations': ['Sequential attribution depends on substitution order.',
                            'No dates, period length or causal evidence are established by this calculation.',
                            'Variance is not achievable savings.']}
