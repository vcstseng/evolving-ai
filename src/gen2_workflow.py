"""Gen 2 candidate handoffs. Independent from preserved Gen 1; no autonomous LLM calls."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from time import perf_counter

from src.gen2_analysis import analyze, inspect_evidence

ROOT = Path(__file__).resolve().parents[1]
_TOOL_TOKEN = object()
DECISIONS = {
    'execution': {'retry', 'reassign'}, 'evidence': {'request_evidence', 'stop'},
    'method': {'change_method', 'stop'}, 'handoff': {'reassign', 'change_method'},
    'tool': {'add_tool', 'stop'}, 'expertise': {'recruit_existing', 'propose_role', 'stop'}
}


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def directory(run_id):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,70}', run_id):
        raise ValueError('Use a short lowercase run ID')
    return ROOT / 'runs' / run_id


@contextmanager
def locked(folder):
    lock = folder / '.lock'
    with lock.open('x'):
        pass
    try:
        yield
    finally:
        lock.unlink()


def event(folder, state, action, **fields):
    with (folder / 'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'time': now(), 'event': action, **fields}, ensure_ascii=False) + '\n')
    save(folder / 'state.json', state)


def verify(folder, state):
    if state.get('generation') != 'gen2':
        raise ValueError('This runner only handles Gen 2 runs')
    for source in state['sources']:
        if digest(ROOT / source['path']) != source['sha256']:
            raise ValueError('Source changed: start a new run')
    if digest(folder / 'contract.json') != state['contract_sha256']:
        raise ValueError('Run contract changed')
    for result in state['completed'].values():
        if digest(folder / result['file']) != result['sha256']:
            raise ValueError('Submitted artifact changed: do not overwrite history')


def start(run_id):
    folder = directory(run_id)
    case = read(ROOT / 'cases/active/f03-gen2.json')
    contract = read(ROOT / 'organization/roles/gen2.json')
    folder.mkdir(exist_ok=False)
    save(folder / 'contract.json', contract)
    state = {'id': run_id, 'generation': 'gen2', 'created': now(), 'case': case, 'completed': {}, 'submissions': 0,
             'external_review': 'pending', 'business_outcome': 'not_measured',
             'status': 'in_progress', 'contract_sha256': digest(folder / 'contract.json'),
             'sources': [{'path': path, 'sha256': digest(ROOT / path)} for path in
                         [case['source'], case['frozen_proposal'], 'cases/active/f03-gen2.json', 'src/gen2_analysis.py', 'src/gen2_workflow.py'] + ([case['evidence_metadata']] if case.get('evidence_metadata') else [])]}
    event(folder, state, 'started', mode='shared-context model-assisted handoffs; deterministic tools')
    return state


def packet(run_id, task_id):
    folder = directory(run_id)
    state = read(folder / 'state.json')
    verify(folder, state)
    contract = read(folder / 'contract.json')
    task = next((t for t in contract['tasks'] if t['id'] == task_id), None)
    if task is None:
        raise ValueError('Unknown task')
    missing = [d for d in task['depends'] if d not in state['completed']]
    if missing:
        raise ValueError('Dependencies incomplete: ' + ', '.join(missing))
    work = {'case': state['case'], 'task': task, 'role': contract['roles'][task['role']],
            'handoffs': {d: read(folder / state['completed'][d]['file'])['content'] for d in task['depends']}}
    if task_id == 'diagnosis':
        events = [json.loads(line) for line in (folder / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
        rejections = [e for e in events if e['event'] in ('submission_rejected', 'tool_failed')]
        work['event_summary'] = {'event_count': len(events), 'submissions': state['submissions'],
                                 'rejection_count': len(rejections),
                                 'rejections': [{'task': e.get('task'), 'reason': e.get('reason')} for e in rejections]}
    if task_id == 'proposal':
        work['numeric_claims_template'] = numeric_template(work['handoffs']['finance']['calculation'])
    return work


def numeric_template(calculation):
    return {key: calculation[key] for key in ('totals', 'fixed_effects', 'by_product', 'sensitivity')}


def tool_content(state, task_id):
    path = ROOT / state['case']['source']
    if task_id == 'evidence':
        metadata = state['case'].get('evidence_metadata')
        result = inspect_evidence(path, ROOT / metadata if metadata else None)
        result['source_refs'] = [state['case']['source']] + ([metadata] if metadata else [])
        return result
    if task_id == 'finance':
        result = analyze(path)
        return {'calculation': result, 'interpretation': 'Accounting attribution only; inspect comparability before causal conclusions.',
                'limitations': result['limitations']}
    raise ValueError('Only evidence/finance have a deterministic executor')


def check_proposal(content, work):
    if content['numeric_claims'] != work['numeric_claims_template']:
        raise ValueError('numeric_claims must match the finance tool template exactly')
    def check(value):
        if isinstance(value, str) and re.search(r'\d', value):
            raise ValueError('Put numeric literals in numeric_claims; use narrative wording in proposal prose')
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            raise ValueError('Put numeric values in numeric_claims')
        if isinstance(value, dict):
            for item in value.values(): check(item)
        if isinstance(value, list):
            for item in value: check(item)
    for key, value in content.items():
        if key not in ('numeric_claims', 'evidence_refs'): check(value)



def submit(run_id, task_id, content, actor, executor='model_assisted', usage=None, *, _tool_token=None):
    folder = directory(run_id)
    with locked(folder):
        state = read(folder / 'state.json')
        if state.get('generation') != 'gen2':
            raise ValueError('This runner only handles Gen 2 runs')
        if state['submissions'] >= state['case']['max_submissions']:
            state['status'] = 'stopped_submission_limit'
            event(folder, state, 'stopped', reason='submission_budget_exhausted')
            raise ValueError('External submission limit reached')
        state['submissions'] += 1
        try:
            work = packet(run_id, task_id)
            if task_id in state['completed']:
                raise ValueError('Task already submitted; start a new version/run')
            if not isinstance(content, dict) or any(k not in content for k in work['task']['fields']):
                raise ValueError('Missing handoff fields')
            for key in work['task']['fields']:
                if key in ('gaps', 'disagreements', 'required_evidence'):
                    if not isinstance(content[key], list):
                        raise ValueError(key + ' must be a list; an empty list is allowed')
                elif not content[key]:
                    raise ValueError('Empty handoff field: ' + key)
            if task_id in ('evidence', 'finance'):
                if _tool_token is not _TOOL_TOKEN or executor != 'deterministic':
                    raise ValueError('Evidence/finance must be produced by tool(), not submit()')
                if content != tool_content(state, task_id):
                    raise ValueError('Deterministic content does not match recomputation')
            if task_id == 'proposal':
                check_proposal(content, work)
            if not actor.strip() or executor not in ('model_assisted', 'deterministic', 'human'):
                raise ValueError('Record the actual executor and actor')
            if task_id in ('proposal', 'diagnosis'):
                refs = content['evidence_refs']
                if not isinstance(refs, list) or any(r not in work['task']['depends'] + (['event_summary'] if task_id == 'diagnosis' else []) for r in refs):
                    raise ValueError('Evidence references must name available handoffs')
            if task_id == 'diagnosis':
                if not isinstance(content['gaps'], list) or any(not isinstance(g, dict) or g.get('category') not in DECISIONS for g in content['gaps']):
                    raise ValueError('Unknown gap category')
                if not content['gaps']:
                    if content['decision'] != 'no_gap' or content['capability_status'] != 'no_new_capability':
                        raise ValueError('Empty gaps require no_gap and no_new_capability')
                    if work['handoffs']['evidence']['gaps']:
                        raise ValueError('no_gap contradicts unresolved availability gaps in evidence')
                elif content['decision'] == 'no_gap':
                    raise ValueError('no_gap requires an empty gap list')
                if any(content['decision'] not in DECISIONS[g['category']] for g in content['gaps']):
                    raise ValueError('Adjustment does not address every recorded gap; split diagnoses')
                if content['capability_status'] not in ('no_new_capability', 'candidate_unverified'):
                    raise ValueError('This handoff cannot certify a capability')
                if content['decision'] == 'propose_role' and content['capability_status'] != 'candidate_unverified':
                    raise ValueError('New roles must remain unverified candidates')
                if content['decision'] == 'propose_role':
                    spec = content.get('role_candidate', {})
                    if any(not spec.get(k) for k in ('purpose', 'inputs', 'outputs', 'boundaries', 'qualification_tests')):
                        raise ValueError('A role candidate requires a contract and qualification tests')
                if content['decision'] == 'recruit_existing' and content.get('recruit_role') not in read(folder / 'contract.json')['roles']:
                    raise ValueError('Recruit only an existing registered role')
            if usage is not None and (not isinstance(usage, dict) or any(not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 for v in usage.values())):
                raise ValueError('Usage must contain measured nonnegative values')
            result = {'task': task_id, 'role': work['task']['role'], 'actor': actor,
                      'executor': executor, 'submitted': now(), 'usage': usage,
                      'validation': 'schema_and_tool_numeric_consistency; not quality acceptance', 'content': content}
            filename = task_id + '.json'
            with (folder / filename).open('x', encoding='utf-8') as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
            state['completed'][task_id] = {'file': filename, 'sha256': digest(folder / filename),
                                           'role': work['task']['role'], 'executor': executor}
            if task_id == 'diagnosis':
                state['next_action'] = content['decision']
            if len(state['completed']) == len(read(folder / 'contract.json')['tasks']):
                state['status'] = 'handoffs_complete_awaiting_external_review'
            event(folder, state, 'handoff_submitted', task=task_id, executor=executor)
        except (ValueError, KeyError, TypeError) as error:
            event(folder, state, 'submission_rejected', task=task_id, reason=str(error))
            raise ValueError(str(error)) from None
    return state


def tool(run_id, task_id):
    folder = directory(run_id)
    with locked(folder):
        state = read(folder / 'state.json')
        if state.get('generation') != 'gen2':
            raise ValueError('This runner only handles Gen 2 runs')
        if state['submissions'] >= state['case']['max_submissions']:
            state['status'] = 'stopped_submission_limit'
            event(folder, state, 'stopped', reason='submission_budget_exhausted')
            raise ValueError('External submission limit reached')
        begin = perf_counter()
        try:
            packet(run_id, task_id)
            if task_id in state['completed']:
                raise ValueError('Task already submitted')
            content = tool_content(state, task_id)
        except (ValueError, OSError, KeyError, TypeError) as error:
            state['submissions'] += 1
            event(folder, state, 'tool_failed', task=task_id, reason=str(error))
            raise ValueError(str(error)) from None
    return submit(run_id, task_id, content, 'local Gen 2 Python tool', 'deterministic',
                  {'elapsed_seconds': perf_counter() - begin, 'model_calls': 0}, _tool_token=_TOOL_TOKEN)


def export_summary(run_id):
    """Explicit allowlist: no artifact text, prompts or raw event log is published."""
    folder = directory(run_id)
    state = read(folder / 'state.json')
    verify(folder, state)
    if state['case']['id'] != 'f03-gen2-pilot' or state['case']['kind'] != 'synthetic':
        raise ValueError('Public export is restricted to the synthetic F03 pilot')
    if state['status'] != 'handoffs_complete_awaiting_external_review':
        raise ValueError('Finish internal handoffs before publishing a summary')
    diagnosis = read(folder / 'diagnosis.json')['content']
    finance = read(folder / 'finance.json')['content']['calculation']
    out = {'schema': 2, 'generation': 'gen2', 'run_id': run_id, 'case_id': state['case']['id'], 'kind': 'synthetic',
           'created': state['created'], 'status': state['status'], 'external_review': 'pending',
           'independent_agents': False, 'unseen_test': False, 'business_outcome': 'not_measured',
           'mode': 'Shared-context model-assisted handoffs plus deterministic Python tools; no autonomous LLM runner.',
           'completed': [{'task': t, 'role': r['role'], 'executor': r['executor'], 'sha256': r['sha256']}
                         for t, r in state['completed'].items()],
           'objective_checks': {k: finance['totals'][k] for k in ('baseline', 'actual', 'variance')},
           'adjustment': diagnosis['decision'], 'gap_categories': sorted({g['category'] for g in diagnosis['gaps']}),
           'next_action_status': 'not_needed' if diagnosis['decision'] == 'no_gap' else 'pending',
           'capability_status': diagnosis['capability_status'], 'submissions': state['submissions'],
           'submission_limit': state['case']['max_submissions'], 'model_tokens': None, 'model_cost': None,
           'cost_note': 'Model usage for shared-chat tasks is not metered; no zero-cost claim.',
           'scope_note': 'Workflow execution only; schema acceptance is not proposal-quality acceptance. Frozen v1 unchanged.'}
    save(ROOT / 'web/evidence/f03-gen2-workflow.json', out)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['start', 'packet', 'submit', 'tool', 'status', 'export'])
    parser.add_argument('run')
    parser.add_argument('task', nargs='?')
    parser.add_argument('--file')
    parser.add_argument('--actor', default='')
    args = parser.parse_args()
    try:
        if args.command == 'start':
            out = start(args.run)
        elif args.command == 'packet':
            out = packet(args.run, args.task)
        elif args.command == 'submit':
            out = submit(args.run, args.task, read(args.file), args.actor)
        elif args.command == 'tool':
            out = tool(args.run, args.task)
        elif args.command == 'export':
            out = export_summary(args.run)
        else:
            folder = directory(args.run)
            out = read(folder / 'state.json')
            verify(folder, out)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
