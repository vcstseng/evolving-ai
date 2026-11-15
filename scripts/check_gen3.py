"""Reproduce known public development cases for Gen 3; no agent or unseen-case claims."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.gen3_policy import assess
from src.gen2_analysis import inspect_evidence


def digest(path):
    return hashlib.sha256(path.read_text(encoding='utf-8').encode('utf-8')).hexdigest()


def request(kind, mixed=False):
    brief = 'Assess the requested rate difference without claiming source truth.'
    claims = [{'id': 'requested', 'kind': kind, 'required': True, 'answers': ['q']}]
    if mixed:
        claims.append({'id': 'calculation', 'kind': 'conditional_arithmetic', 'required': False, 'answers': ['q']})
    return {'decision': brief, 'questions': [{'id': 'q', 'text': brief}], 'claims': claims}


def compute():
    source = Path('web/evidence/method-probe/definition.csv')
    clean = Path('web/evidence/gen3/metadata-clean.json')
    unknown = Path('web/evidence/method-probe/metadata.json')
    conflict = Path('web/evidence/method-probe/definition-metadata.json')
    scenarios = [('definition_conflict', conflict, request('rate_change'), 'request_evidence'),
                 ('unknown', unknown, request('rate_change', mixed=True), 'conditional_delivery'),
                 ('clean', clean, request('conditional_arithmetic'), 'no_gap'),
                 ('unresolved_cause', clean, request('causal', mixed=True), 'conditional_delivery')]
    results = []
    for name, metadata, req, expected in scenarios:
        gate = assess(source, metadata, req, brief=req['decision'])
        assert gate['decision'] == expected, name
        results.append({'id': name, 'input': source.as_posix(), 'metadata': metadata.as_posix(),
                        'requested_claims': req, 'gen2_availability_gap_ids': [g['id'] for g in inspect_evidence(source, metadata)['gaps']],
                        'gen3_decision': gate['decision'], 'run_level': gate['run_level'],
                        'requested_decision_answered': gate['requested_decision_answered'],
                        'permitted_claims': gate['permitted_claims'], 'blocked_claims': gate['blocked_claims'],
                        'comparability': [{'field': c['field'], 'status': c['status'], 'reason': c['reason']} for c in gate['comparability']],
                        'review_status': gate['review_status']})
    attribution = json.loads((ROOT / 'web/evidence/f03/source-attribution.json').read_text(encoding='utf-8'))
    method = next(m for m in attribution['methods'] if m['path'] == 'src/gen2_workflow.py')
    lf = (ROOT / method['path']).read_text(encoding='utf-8').encode('utf-8')
    crlf = hashlib.sha256(lf.replace(b'\n', b'\r\n')).hexdigest()
    assert hashlib.sha256(lf).hexdigest() == method['sha256_lf']
    assert crlf == method['author_checked_local_run_source_sha256']
    files = ['src/gen3_policy.py', 'src/gen3_workflow.py', 'src/gen2_analysis.py', 'src/cost_analysis.py',
             'organization/roles/gen3.json', 'cases/active/f03-gen3.json', 'tests/test_gen3.py',
             source.as_posix(), clean.as_posix(), unknown.as_posix(), conflict.as_posix()]
    return {'schema': 1, 'date': '2026-11-15', 'generation': 'gen3',
            'scope': 'Deterministic development gate examples, not complete model-assisted case reruns or unseen transfer.',
            'model_calls': 0, 'external_review': 'not_reviewed_as_implementation', 'unseen_test': False,
            'cases': results, 'source_sha256_lf': {p: digest(ROOT / p) for p in files},
            'gen2_workflow_line_endings': {'sha256_lf': method['sha256_lf'], 'sha256_lf_converted_to_crlf': crlf,
                                          'matches_author_recorded_run_hash': True,
                                          'note': 'Reproducible byte-format explanation, not independent attestation of the historical execution.'},
            'limitations': ['The brief-question mapping is authored before the run, not automatically proven complete by NLP.',
                            'Quoted definitions and structured reference text are checked; source truth is not.',
                            'Inspected is a supplied provenance claim, not independent verification by this program.',
                            'Causal, efficiency and pilot claims remain unsupported by this bounded gate.',
                            'Gen 2 availability output is shown as context, not its CD decision or a fair agent comparison.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = compute()
    output = ROOT / 'web/evidence/gen3/development-results.json'
    if args.write:
        with output.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write('\n')
    else:
        assert json.loads(output.read_text(encoding='utf-8')) == result, 'Published Gen 3 examples or frozen source fingerprints changed'
    print('PASS: four development gate examples and the LF/CRLF explanation reproduce; no unseen or business outcome claim.')
