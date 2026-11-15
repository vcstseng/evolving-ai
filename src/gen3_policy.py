"""Scoped, deterministic evidence gate. Checks structured declarations, not their truth."""
import json
from pathlib import Path

from src.gen2_analysis import ORDER, analyze, inspect_evidence

FIELDS = ['periods', *ORDER]
REQUIRED = {
    'conditional_arithmetic': set(FIELDS),
    'rate_change': {'periods', 'units', 'hourly_rate'},
    'efficiency': {'periods', 'units', 'hours_per_unit'},
    'comparable_attribution': set(FIELDS),
    'evidence_plan': set(FIELDS),
    'causal': set(FIELDS),
    'pilot': set(FIELDS),
}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def normalized(value):
    return ' '.join(value.casefold().split())


def assess(path, metadata_path, request, *, brief):
    if not text(brief) or not isinstance(request, dict) or request.get('decision') != brief:
        raise ValueError('A pinned requested decision is required')
    questions = request.get('questions')
    if not isinstance(questions, list) or not questions or any(not isinstance(q, dict) or not text(q.get('id')) or not text(q.get('text')) for q in questions):
        raise ValueError('Pinned brief questions are required')
    question_ids = {q['id'] for q in questions}
    if len(question_ids) != len(questions):
        raise ValueError('Question IDs must be unique')
    claims = request.get('claims')
    if not isinstance(claims, list) or not claims:
        raise ValueError('Declare the requested claims before execution')
    ids = set()
    for claim in claims:
        if not isinstance(claim, dict) or not text(claim.get('id')) or claim['id'] in ids:
            raise ValueError('Claim IDs must be unique nonempty strings')
        if claim.get('kind') not in REQUIRED or type(claim.get('required')) is not bool:
            raise ValueError('Unsupported claim kind or missing required flag')
        answers = claim.get('answers')
        if not isinstance(answers, list) or not answers or any(not isinstance(q, str) or q not in question_ids for q in answers):
            raise ValueError('Claims must map to pinned brief question IDs')
        ids.add(claim['id'])
    if not any(c['required'] for c in claims):
        raise ValueError('At least one original requested claim must be required')

    uncovered = sorted(question_ids - {q for c in claims if c['required'] for q in c['answers']})
    calculation = analyze(path)
    availability = inspect_evidence(path, metadata_path)
    metadata = json.loads(Path(metadata_path).read_text(encoding='utf-8-sig')) if metadata_path else {}
    registry = metadata.get('evidence_sources', {})
    if not isinstance(registry, dict):
        registry = {}
    declared = metadata.get('comparability', {})
    if not isinstance(declared, dict):
        declared = {}
    comparisons = []
    issues = [{'id': 'availability.' + item['id'], 'category': 'evidence', 'detail': item['detail'],
               'affected_claim_ids': [c['id'] for c in claims], 'blocking': False}
              for item in availability['gaps']]
    for field in FIELDS:
        item = declared.get(field, {})
        if not isinstance(item, dict):
            item = {}
        refs = item.get('source_refs', [])
        refs_valid = isinstance(refs, list) and bool(refs) and all(
            isinstance(ref, str) and isinstance(registry.get(ref), dict) and
            all(text(registry[ref].get(k)) for k in ('owner', 'reference', 'description', 'text')) for ref in refs)
        complete = (all(text(item.get(k)) for k in ('baseline_definition', 'actual_definition', 'reason', 'resolution'))
                    and item.get('verification') in ('declared', 'inspected', 'independently_verified') and refs_valid)
        status = 'unknown'
        reason = 'Missing, malformed or unsupported comparability declaration.'
        if item.get('status') == 'no':
            status, reason = 'no', 'Declared incomparable; missing citations cannot erase the warning.'
        elif complete:
            quotes_found = all(any(normalized(item[k]) in normalized(registry[r]['text']) for r in refs)
                               for k in ('baseline_definition', 'actual_definition'))
            if normalized(item['baseline_definition']) != normalized(item['actual_definition']):
                status, reason = 'no', 'Definition texts differ; no normalization is implemented.'
            elif any(registry[ref].get('conflict') is True for ref in refs):
                status, reason = 'no', 'A referenced source declares a conflict.'
            elif not quotes_found:
                reason = 'Definition quote cannot be located in the referenced input text.'
            elif item.get('verification') == 'declared':
                reason = 'A declaration alone is insufficient for scoped no-gap; inspected references are required.'
            elif item.get('status') == 'yes':
                status, reason = 'yes', 'Consistent structured declaration with identifiable references; truth is unverified.'
            # unknown / not_applicable cannot skip a field required by a claim.
        legacy = metadata.get('hourly_rate_comparison', {}) if field == 'hourly_rate' else {}
        if isinstance(legacy, dict) and (legacy.get('comparable') is False or
                all(text(legacy.get(k)) for k in ('baseline_definition', 'actual_definition')) and
                normalized(legacy['baseline_definition']) != normalized(legacy['actual_definition'])):
            status, reason = 'no', 'Explicit hourly-rate comparison conflicts; positive declarations cannot override it.'
        if field == 'periods' and availability['quality_checks']['periods']['status'] == 'missing_or_invalid':
            status, reason = 'unknown', 'Missing or invalid period dates.'
        elif field == 'periods' and any(g['id'] == 'period_comparability' for g in availability['gaps']):
            status, reason = 'no', 'Period durations differ; normalization is not implemented.'
        affected = [c['id'] for c in claims if field in REQUIRED[c['kind']]]
        if item.get('status') == 'not_applicable' and field in ORDER and any(p['effects'][field] != '0' for p in calculation['by_product']):
            status, reason = 'unknown', 'Not-applicable cannot exclude a nonzero attributed effect.'
            affected = [c['id'] for c in claims]
        comparisons.append({'field': field, 'status': status, 'reason': reason,
                            'baseline_definition': item.get('baseline_definition') if text(item.get('baseline_definition')) else None,
                            'actual_definition': item.get('actual_definition') if text(item.get('actual_definition')) else None,
                            'source_refs': refs if refs_valid else [],
                            'source_owner_or_unknown': [registry[r]['owner'] for r in refs] if refs_valid else ['unknown'],
                            'reported_verification': item.get('verification') if complete else 'unknown',
                            'verification_by_this_tool': 'structure_and_consistency_only',
                            'affected_claim_ids': affected,
                            'resolution': item.get('resolution') if text(item.get('resolution')) else 'Obtain comparable definitions and traceable evidence.'})
        if status != 'yes':
            issues.append({'id': 'comparability.' + field, 'category': 'evidence', 'detail': reason,
                           'affected_claim_ids': affected, 'blocking': bool(affected)})

    statuses = {c['field']: c['status'] for c in comparisons}
    permitted, blocked, decisions = [], [], []
    for claim in claims:
        kind = claim['kind']
        blockers = [f for f in FIELDS if f in REQUIRED[kind] and statuses[f] != 'yes']
        if kind in ('causal', 'pilot', 'efficiency'):
            blockers.append('causal_evidence_and_human_authorization_not_supported')
        level = 1 if blockers else 3
        if kind in ('conditional_arithmetic', 'evidence_plan'):
            level = (2 if blockers or availability['gaps'] else 3) if kind == 'conditional_arithmetic' else (1 if blockers or availability['gaps'] else 3)
            blockers = []  # These remain explicitly limited and do not answer stronger claims.
        (blocked if blockers else permitted).append(claim['id'])
        decisions.append({**claim, 'status': 'blocked' if blockers else 'permitted', 'blockers': blockers,
                          'level': level,
                          'qualification': 'Supplied-number arithmetic / evidence planning only.' if kind in ('conditional_arithmetic', 'evidence_plan') else
                          'Conditional on supplied declarations, not source truth or business validity.'})
        for blocker in blockers:
            if blocker not in FIELDS:
                issues.append({'id': 'claim.' + claim['id'], 'category': 'evidence', 'detail': blocker,
                               'affected_claim_ids': [claim['id']], 'blocking': True})
    if uncovered:
        issues.append({'id': 'coverage.incomplete', 'category': 'evidence', 'detail': 'Brief questions lack required claim coverage.',
                       'affected_claim_ids': [c['id'] for c in claims], 'blocking': True})
    required_answered = not uncovered and all(c['id'] in permitted for c in claims if c['required'])
    run_level = min(c['level'] for c in decisions)
    if uncovered:
        run_level = min(run_level, 1)
    relevant_issues = [i for i in issues if i['affected_claim_ids']]
    decision = 'no_gap' if required_answered and run_level == 3 and not relevant_issues else 'conditional_delivery' if permitted else 'request_evidence'
    return {'schema': 1, 'generation': 'gen3', 'requested_decision': request['decision'],
            'questions': questions, 'uncovered_questions': uncovered, 'run_level': run_level,
            'claim_ids': [c['id'] for c in claims], 'claims': decisions, 'comparability': comparisons,
            'availability': availability, 'supporting_refs': sorted({r for c in comparisons for r in c['source_refs']}),
            'unresolved_issues': issues, 'permitted_claims': permitted, 'blocked_claims': blocked,
            'requested_decision_answered': required_answered,
            'decision': decision, 'release_status': {'no_gap': 'ready_for_review', 'conditional_delivery': 'conditional_delivery', 'request_evidence': 'withheld'}[decision],
            'review_status': 'pending', 'business_authorization': 'not_granted',
            'scope_note': 'No-gap is scoped to the pinned requested claims. This tool checks structured declarations, not source truth, free-text causal claims or enterprise outcomes.'}
