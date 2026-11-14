"""Gen 2 accounting tools. Exact rational attribution, not causal inference."""
import csv
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from itertools import permutations
import json

from src.cost_analysis import ORDER


def decimal_text(value, places=None):
    with localcontext() as context:
        context.prec = 60
        number = Decimal(value.numerator) / Decimal(value.denominator)
        text = format(number, 'f' if places is None else f'.{places}f')
        return text.rstrip('0').rstrip('.') if '.' in text else text


def load(path):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)) or not {'product', 'period', *ORDER}.issubset(columns):
            raise ValueError('Missing or duplicate cost columns')
        pairs = {}
        for raw in reader:
            key = ((raw.get('product') or '').strip(), (raw.get('period') or '').strip())
            if not key[0] or key[1] not in ('baseline', 'actual') or key in pairs:
                raise ValueError('Invalid or duplicate product/period')
            row = {}
            for field in ORDER:
                try:
                    value = Decimal(raw[field])
                except (InvalidOperation, TypeError):
                    raise ValueError(f'Invalid numeric field: {field}') from None
                if not value.is_finite() or value < 0:
                    raise ValueError(f'Nonfinite or negative field: {field}')
                if field == 'units' and value != value.to_integral_value():
                    raise ValueError('Units must be whole numbers')
                row[field] = Fraction(value)
            pairs[key] = row
    products = sorted({product for product, _ in pairs})
    if not products or any((product, period) not in pairs for product in products for period in ('baseline', 'actual')):
        raise ValueError('Each product requires baseline and actual records')
    return columns, products, pairs


def cost(row):
    return row['units'] * (row['material_per_unit'] * row['material_price'] + row['hours_per_unit'] * row['hourly_rate'] + row['overhead_per_unit'])


def bridge(baseline, actual, order):
    state = baseline.copy()
    previous = cost(state)
    effects = {}
    for field in order:
        state[field] = actual[field]
        current = cost(state)
        effects[field] = current - previous
        previous = current
    return effects


def analyze(path):
    _, products, pairs = load(path)
    by_product, effects = [], {field: Fraction(0) for field in ORDER}
    baseline = actual = flex = Fraction(0)
    for product in products:
        b, a = pairs[product, 'baseline'], pairs[product, 'actual']
        bcost, acost, fcost = cost(b), cost(a), cost({**b, 'units': a['units']})
        product_effects = bridge(b, a, ORDER)
        baseline += bcost
        actual += acost
        flex += fcost
        for field in ORDER:
            effects[field] += product_effects[field]
        by_product.append({'product': product, 'baseline': decimal_text(bcost), 'actual': decimal_text(acost),
                           'flex_baseline': decimal_text(fcost), 'volume_effect': decimal_text(fcost - bcost),
                           'non_volume_variance': decimal_text(acost - fcost),
                           'effects': {k: decimal_text(v) for k, v in product_effects.items()}})
    samples = {field: [] for field in ORDER}
    hours_largest = True
    for order in permutations(ORDER):
        totals = {field: Fraction(0) for field in ORDER}
        for product in products:
            values = bridge(pairs[product, 'baseline'], pairs[product, 'actual'], order)
            for field in ORDER:
                totals[field] += values[field]
        hours_largest &= totals['hours_per_unit'] > 0 and totals['hours_per_unit'] >= max(totals.values())
        for field in ORDER:
            samples[field].append(totals[field])
    sensitivity = {}
    means = {}
    for field, values in samples.items():
        mean = sum(values) / len(values)
        means[field] = mean
        sensitivity[field] = {'min': decimal_text(min(values)), 'max': decimal_text(max(values)),
                              'mean': decimal_text(mean, 12), 'mean_fraction': str(mean)}
    assert sum(effects.values()) == actual - baseline == sum(means.values())
    return {'totals': {'baseline': decimal_text(baseline), 'actual': decimal_text(actual),
                       'variance': decimal_text(actual - baseline), 'flex_baseline': decimal_text(flex),
                       'volume_effect': decimal_text(flex - baseline), 'non_volume_variance': decimal_text(actual - flex)},
            'fixed_order': ORDER, 'fixed_effects': {k: decimal_text(v) for k, v in effects.items()},
            'by_product': by_product,
            'sensitivity': {'orders': len(samples[ORDER[0]]), 'effects': sensitivity,
                            'hours_largest_in_every_order': hours_largest,
                            'adverse_drivers_by_mean': sorted((k for k in ORDER if means[k] > 0), key=lambda k: means[k], reverse=True)},
            'limitations': ['Flexible baseline assumes the supplied per-unit cost model; it does not distinguish true fixed costs.',
                            'Order means are rounded to 12 decimal places; mean_fraction retains the exact rational value.',
                            'Accounting attribution and priority signals do not establish causes, avoidable waste or savings.']}


def inspect_evidence(path, metadata_path=None):
    columns, products, pairs = load(path)
    metadata = {}
    if metadata_path is not None:
        with open(metadata_path, encoding='utf-8-sig') as stream:
            metadata = json.load(stream)
        if not isinstance(metadata, dict):
            raise ValueError('Evidence metadata must be an object')
    checks = {'cost_columns_checked': sorted(set(columns) & set(ORDER)), 'rows_checked': len(pairs),
              'paired_products': products, 'numeric_fields_checked': len(pairs) * len(ORDER)}
    gaps = []
    periods = metadata.get('periods', {})
    try:
        if not isinstance(periods, dict):
            raise ValueError('Invalid periods')
        durations = []
        for period in ('baseline', 'actual'):
            value = periods.get(period, {})
            begin, end = date.fromisoformat(value['start']), date.fromisoformat(value['end'])
            if end < begin:
                raise ValueError('Invalid date range')
            durations.append((end - begin).days + 1)
        checks['periods'] = {'status': 'format_checked_not_independently_verified', 'days': durations}
        if durations[0] != durations[1]:
            gaps.append({'id': 'period_comparability', 'category': 'evidence', 'detail': 'Declared period lengths differ; comparability needs explanation.'})
    except (KeyError, ValueError, TypeError):
        checks['periods'] = {'status': 'missing_or_invalid'}
        gaps.append({'id': 'periods', 'category': 'evidence', 'detail': 'Valid baseline/actual dates were not supplied in the evidence metadata.'})
    definitions = metadata.get('definitions', {})
    for field in ('units', 'hours_per_unit'):
        value = definitions.get(field) if isinstance(definitions, dict) else None
        supplied = isinstance(value, str) and bool(value.strip())
        checks[field + '_definition'] = 'provided_unverified' if supplied else 'missing'
        if not supplied:
            gaps.append({'id': field + '_definition', 'category': 'evidence', 'detail': f'No supplied definition for {field}.'})
    records = metadata.get('operational_records', [])
    supplied = isinstance(records, list) and bool(records) and all(isinstance(r, dict) and all(isinstance(r.get(k), str) and r[k].strip() for k in ('reference', 'description')) for r in records)
    checks['operational_records'] = 'referenced_not_verified' if supplied else 'not_referenced'
    if not supplied:
        gaps.append({'id': 'operational_records', 'category': 'evidence', 'detail': 'No operational evidence reference was supplied; causal claims remain unsupported.'})
    return {'source_refs': [str(path)] + ([str(metadata_path)] if metadata_path else []),
            'quality_checks': checks, 'gaps': gaps,
            'permitted_uses': ['Validated cost-field arithmetic; supplied metadata is not independently verified.'],
            'limitations': ['An empty availability-gap list means required declarations were supplied, not that their content is true or business outcomes are verified.']}
