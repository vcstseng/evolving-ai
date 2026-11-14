"""Reproduce a public development probe; expected blind spots are observations, not test passes."""
import argparse
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.cost_analysis import analyze as gen1
from src.gen2_analysis import analyze as gen2, inspect_evidence

BASE = ROOT / 'web/evidence/method-probe'
METHODS = {
    'src/cost_analysis.py': 'b2d4f3565235ff96af98b41d53b24c0dd307a19949dbe2a57e556414e62334cf',
    'src/gen2_analysis.py': '9700bbaaee869297bf178c58fb7d966914bfb0fa3f4eae3abb9aef502952e702',
}


def fingerprint(path):
    # Text files normalize CRLF to LF for Windows/Linux reproducibility.
    return hashlib.sha256(path.read_text(encoding='utf-8').encode('utf-8')).hexdigest()


def get(data, dotted):
    for key in dotted.split('.'):
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def observe(expected, actual):
    if actual is None:
        status = 'not_reported'
    elif isinstance(expected, bool):
        status = 'matched' if actual is expected else 'mismatch'
    else:
        status = 'matched' if Decimal(str(actual)) == Decimal(str(expected)) else 'mismatch'
    return {'expected': expected, 'actual': actual, 'status': status}


def run():
    for name, digest in METHODS.items():
        if fingerprint(ROOT / name) != digest:
            raise ValueError(f'Frozen method changed: {name}; preserve this probe and create a new version')
    cases = []
    for spec in json.loads((BASE / 'expectations.json').read_text(encoding='utf-8')):
        path = BASE / (spec['id'] + '.csv')
        old, new = gen1(path), gen2(path)
        evidence = inspect_evidence(path, BASE / spec['metadata'])
        common = {key: {'gen1': observe(value, old.get(key)),
                        'gen2': observe(value, new['totals'].get(key))}
                  for key, value in spec['costs'].items()}
        if any(c['status'] != 'matched' for row in common.values() for c in row.values()):
            raise ValueError(f'Cost mismatch in {spec["id"]}')
        extra = {key: {'gen1': observe(value, get(old, key)), 'gen2': observe(value, get(new, key))}
                 for key, value in spec.get('extra', {}).items()}
        if any(row['gen2']['status'] != 'matched' for row in extra.values()):
            raise ValueError(f'Gen 2 analysis mismatch in {spec["id"]}')
        gap = None
        if spec.get('required_gap'):
            found = spec['required_gap'] in [item['id'] for item in evidence['gaps']]
            gap = {'required_gap': spec['required_gap'], 'gen1': 'not_reported',
                   'gen2': 'detected' if found else 'not_detected',
                   'scope': 'Requested semantic comparison is outside the implemented evidence checks.'}
        cases.append({'id': spec['id'], 'common_cost_checks': common, 'additional_checks': extra,
                      'semantic_gap_check': gap,
                      'gen2_availability_gap_ids': [item['id'] for item in evidence['gaps']]})
    files = sorted(p for p in BASE.iterdir() if p.name in {
        'protocol.md', 'expectations.json', 'volume.csv', 'order.csv', 'definition.csv',
        'metadata.json', 'definition-metadata.json'})
    return {'schema': 1, 'protocol': 'method-probe-v1', 'date': '2026-11-15',
            'method_commit': '5fe298720eefccc9b5e282b6a305b0d18cbb8d51',
            'scope': 'public synthetic deterministic development probe; not unseen agent evaluation',
            'repetitions_per_method_per_case': 1, 'model_calls': 0,
            'claude_v2_review': 'pending', 'unseen_test': False,
            'source_sha256_lf': METHODS,
            'input_sha256_lf': {p.name: fingerprint(p) for p in files}, 'cases': cases,
            'limitations': ['No agent handoffs, proposal review, token-budget comparison or business outcome.',
                            'Missing outputs are not arithmetic errors; no aggregate win rate is assigned.',
                            'Authors know the fixtures and expectations; this is not an independent evaluation.',
                            'Empty availability gaps do not establish semantic comparability.',
                            'The methods remain unchanged after observing the boundary failure.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Create the first curated result; never overwrite')
    args = parser.parse_args()
    result = run()
    output = BASE / 'results.json'
    if args.write:
        with output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    elif json.loads(output.read_text(encoding='utf-8')) != result:
        raise ValueError('Published probe differs from reproduction')
    print('Three method probes reproduced; cost checks matched. Semantic blind spots remain observations, not acceptance.')
