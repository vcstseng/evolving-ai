"""Reproduce a shared-context exploration's numbers and gates, not its author's judgments."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.gen2_analysis import analyze
from src.gen3_policy import assess


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    os.chdir(ROOT)
    folder = Path('web/evidence/exploration-01')
    for path, digest in read(folder / 'before-gate.json')['sha256'].items():
        assert hashlib.sha256((folder / path).read_bytes()).hexdigest() == digest, path
    for path, digest in read(Path('web/evidence/gen3/development-results.json'))['source_sha256_lf'].items():
        assert hashlib.sha256(Path(path).read_text(encoding='utf-8').encode()).hexdigest() == digest, path
    request = read(folder / 'request.json')
    ordinary = read(folder / 'ordinary-proposals.json')
    gated = read(folder / 'gated-proposals.json')
    for name in ('E01', 'E02', 'E03'):
        calc = analyze(folder / (name + '.csv'))
        assert read(folder / (name + '-calculation.json')) == calc
        gate = assess(folder / (name + '.csv'), folder / (name + '-metadata.json'), request, brief=request['decision'])
        assert read(folder / (name + '-gate.json')) == gate
        for item in ordinary + gated:
            if item['case_id'] == name:
                assert item['numbers'] == {k: calc['totals'][k] for k in ('baseline', 'actual', 'variance')}
        item = next(p for p in gated if p['case_id'] == name)
        assert item['gate_decision'] == gate['decision']
        assert item['original_question_fully_answered'] == gate['requested_decision_answered']
        assert item['rate_conclusion_supported'] == ('rate_conclusion' in gate['permitted_claims'])
    comparison = read(folder / 'comparison.json')
    assert comparison['independent_contexts'] is False and comparison['unseen_test'] is False
    assert comparison['per_arm_tokens'] is None and comparison['per_arm_cost'] is None
    print('PASS: three inputs, unchanged method, figures and gates reproduce. Shared-context proposals and author judgments are not independently verified.')


if __name__ == '__main__':
    main()
