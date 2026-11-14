import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.cost_analysis import analyze
from src import workflow as w

REAL_ROOT = w.ROOT


class CostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'costs.csv'
        self.rows = [
            ['p', 'baseline', 10, 2, 3, 1, 4, 1],
            ['p', 'actual', 12, 3, 5, 2, 6, 2]]

    def write(self):
        with self.path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['product', 'period', 'units', 'material_per_unit', 'material_price', 'hours_per_unit', 'hourly_rate', 'overhead_per_unit'])
            writer.writerows(self.rows)

    def test_independent_numbers(self):
        self.write()
        result = analyze(self.path)
        self.assertEqual((result['baseline'], result['actual'], result['variance']), ('110', '348', '238'))
        self.assertEqual([e['amount'] for e in result['effects']], ['22', '48', '60', '24', '72', '12'])

    def test_invalid_inputs(self):
        for value in ('NaN', 'Infinity', '', '-1'):
            with self.subTest(value=value):
                self.rows[0][3] = value
                self.write()
                with self.assertRaises(ValueError):
                    analyze(self.path)

    def test_missing_pair_and_duplicate(self):
        self.rows.pop()
        self.write()
        with self.assertRaises(ValueError):
            analyze(self.path)
        self.rows.append(self.rows[0])
        self.write()
        with self.assertRaises(ValueError):
            analyze(self.path)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        for path in ['organization/roles/pilot.json', 'cases/active/f03-pilot.json',
                     'web/evidence/f03/v1/f03-costs.csv', 'web/evidence/f03/v1/proposal.md']:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REAL_ROOT / path, target)
        (root / 'runs').mkdir()
        self.patcher = patch.object(w, 'ROOT', root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        w.start('test')

    def complete(self, task):
        packet = w.packet('test', task)
        content = {key: ['test-only placeholder'] for key in packet['task']['fields']}
        if 'evidence_refs' in content:
            content['evidence_refs'] = packet['task']['depends']
        w.submit('test', task, content, 'test fixture')

    def ready_for_diagnosis(self):
        self.complete('scope')
        w.tool('test', 'evidence')
        w.tool('test', 'finance')
        self.complete('operations')
        self.complete('proposal')

    def diagnosis(self, decision='request_evidence'):
        return {'gaps': [{'category': 'evidence', 'detail': 'Missing dates'}],
                'decision': decision, 'reason': 'Need comparable periods', 'evidence_refs': ['proposal'],
                'capability_status': 'no_new_capability', 'next_check': 'Obtain approved dates'}

    def test_dependency_and_rejection_are_recorded(self):
        with self.assertRaises(ValueError):
            w.submit('test', 'proposal', {}, 'fixture')
        state = w.read(w.directory('test') / 'state.json')
        self.assertEqual(state['submissions'], 1)
        self.assertIn('submission_rejected', (w.directory('test') / 'events.jsonl').read_text())

    def test_no_duplicate_or_mutated_artifact(self):
        self.complete('scope')
        with self.assertRaises(ValueError):
            self.complete('scope')
        (w.directory('test') / 'scope.json').write_text('{}')
        with self.assertRaises(ValueError):
            w.packet('test', 'evidence')

    def test_no_role_creation_for_missing_data(self):
        self.ready_for_diagnosis()
        with self.assertRaises(ValueError):
            w.submit('test', 'diagnosis', self.diagnosis('propose_role'), 'fixture')
        w.submit('test', 'diagnosis', self.diagnosis(), 'fixture')
        summary = w.export_summary('test')
        self.assertEqual(summary['external_review'], 'pending')
        self.assertIsNone(summary['model_cost'])
        self.assertFalse(summary['independent_agents'])
        self.assertNotIn('content', json.dumps(summary))
        self.assertEqual(summary['next_action_status'], 'pending')

    def test_source_changes_block_handoff(self):
        (w.ROOT / 'web/evidence/f03/v1/f03-costs.csv').write_text('changed')
        with self.assertRaises(ValueError):
            w.packet('test', 'scope')

    def test_budget_is_enforced(self):
        for _ in range(12):
            with self.assertRaises(ValueError):
                w.submit('test', 'proposal', {}, 'fixture')
        with self.assertRaisesRegex(ValueError, 'limit'):
            w.submit('test', 'scope', {}, 'fixture')
        self.assertEqual(w.read(w.directory('test') / 'state.json')['status'], 'stopped_submission_limit')

    def test_role_candidate_requires_contract_and_cannot_be_validated(self):
        self.ready_for_diagnosis()
        diagnosis = self.diagnosis('propose_role')
        diagnosis['gaps'] = [{'category': 'expertise', 'detail': 'Test fixture expertise gap'}]
        diagnosis['capability_status'] = 'candidate_unverified'
        with self.assertRaises(ValueError):
            w.submit('test', 'diagnosis', diagnosis, 'fixture')
        diagnosis['role_candidate'] = {k: ['test fixture'] for k in ('purpose', 'inputs', 'outputs', 'boundaries', 'qualification_tests')}
        w.submit('test', 'diagnosis', diagnosis, 'fixture')
        self.assertEqual(w.export_summary('test')['capability_status'], 'candidate_unverified')

    def test_export_cannot_publish_private_case(self):
        self.ready_for_diagnosis()
        w.submit('test', 'diagnosis', self.diagnosis(), 'fixture')
        state = w.read(w.directory('test') / 'state.json')
        state['case']['kind'] = 'private'
        w.save(w.directory('test') / 'state.json', state)
        with self.assertRaisesRegex(ValueError, 'synthetic'):
            w.export_summary('test')


if __name__ == '__main__':
    unittest.main()
