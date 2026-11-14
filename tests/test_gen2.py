import copy
import csv
from fractions import Fraction
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.gen2_analysis import analyze, inspect_evidence
from src import gen2_workflow as w

REAL_ROOT = w.ROOT
COMPLETE_METADATA = {
    'periods': {'baseline': {'start': '2025-01-01', 'end': '2025-01-31'},
                'actual': {'start': '2025-03-01', 'end': '2025-03-31'}},
    'definitions': {'units': 'Synthetic good units produced in the stated period',
                    'hours_per_unit': 'Synthetic direct hours per good unit, same definition in both periods'},
    'operational_records': [{'reference': 'synthetic-fixture-only', 'description': 'Declared test fixture; not business evidence'}]
}


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'data.csv'
        self.meta = Path(self.temp.name) / 'metadata.json'
        with self.path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['product', 'period', 'units', 'material_per_unit', 'material_price', 'hours_per_unit', 'hourly_rate', 'overhead_per_unit'])
            writer.writerows([['p', 'baseline', 10, 2, 3, 1, 4, 1], ['p', 'actual', 12, 3, 5, 2, 6, 2]])

    def test_volume_product_and_exact_shapley_reconciliation(self):
        result = analyze(self.path)
        self.assertEqual(result['totals'], {'baseline': '110', 'actual': '348', 'variance': '238',
                                           'flex_baseline': '132', 'volume_effect': '22', 'non_volume_variance': '216'})
        self.assertEqual(sum(Fraction(v['mean_fraction']) for v in result['sensitivity']['effects'].values()), 238)
        self.assertEqual(result['sensitivity']['orders'], 720)
        self.assertEqual(sum(Fraction(p['non_volume_variance']) for p in result['by_product']), 216)

    def test_f03_regression_arithmetic_not_unseen_test(self):
        result = analyze(REAL_ROOT / 'web/evidence/f03/v1/f03-costs.csv')
        self.assertEqual(result['totals']['flex_baseline'], '188000')
        self.assertEqual(result['totals']['volume_effect'], '22000')
        self.assertEqual(result['totals']['non_volume_variance'], '37300')
        self.assertEqual(sorted(p['non_volume_variance'] for p in result['by_product']), ['32100', '5200'])
        hours = result['sensitivity']['effects']['hours_per_unit']
        self.assertEqual((hours['min'], hours['max'], hours['mean']), ('34000', '42000', '37950'))
        self.assertTrue(result['sensitivity']['hours_largest_in_every_order'])

    def test_unchanged_data_does_not_claim_labor_problem(self):
        lines = self.path.read_text().splitlines()
        lines[2] = lines[1].replace('baseline', 'actual')
        self.path.write_text('\n'.join(lines) + '\n')
        result = analyze(self.path)
        self.assertEqual(result['totals']['variance'], '0')
        self.assertEqual(result['sensitivity']['adverse_drivers_by_mean'], [])
        self.assertFalse(result['sensitivity']['hours_largest_in_every_order'])

    def test_evidence_changes_with_supplied_metadata(self):
        missing = inspect_evidence(self.path)
        self.assertEqual({g['id'] for g in missing['gaps']}, {'periods', 'units_definition', 'hours_per_unit_definition', 'operational_records'})
        self.meta.write_text(json.dumps(COMPLETE_METADATA))
        supplied = inspect_evidence(self.path, self.meta)
        self.assertEqual(supplied['gaps'], [])
        self.assertEqual(supplied['quality_checks']['hours_per_unit_definition'], 'provided_unverified')
        partial = copy.deepcopy(COMPLETE_METADATA)
        partial['definitions'].pop('hours_per_unit')
        self.meta.write_text(json.dumps(partial))
        self.assertEqual([g['id'] for g in inspect_evidence(self.path, self.meta)['gaps']], ['hours_per_unit_definition'])

    def test_malformed_periods_do_not_pass_availability_check(self):
        for periods in ([], {'baseline': {}}, {'baseline': {'start': 'bad'}}):
            self.meta.write_text(json.dumps({**COMPLETE_METADATA, 'periods': periods}))
            self.assertIn('periods', [g['id'] for g in inspect_evidence(self.path, self.meta)['gaps']])

    def test_different_period_lengths_raise_comparability_gap(self):
        meta = copy.deepcopy(COMPLETE_METADATA)
        meta['periods']['actual']['end'] = '2025-03-20'
        self.meta.write_text(json.dumps(meta))
        self.assertEqual([g['id'] for g in inspect_evidence(self.path, self.meta)['gaps']], ['period_comparability'])


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in ['organization/roles/gen2.json', 'cases/active/f03-gen2.json',
                     'web/evidence/f03/v1/f03-costs.csv', 'web/evidence/f03/v1/proposal.md',
                     'src/gen2_analysis.py', 'src/gen2_workflow.py']:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REAL_ROOT / path, target)
        (self.root / 'runs').mkdir()
        self.patcher = patch.object(w, 'ROOT', self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def begin(self, complete=False):
        if complete:
            w.save(self.root / 'metadata.json', COMPLETE_METADATA)
            path = self.root / 'cases/active/f03-gen2.json'
            case = w.read(path)
            case['evidence_metadata'] = 'metadata.json'
            w.save(path, case)
        w.start('test')
        self.complete('scope')

    def content(self, task):
        work = w.packet('test', task)
        content = {key: ['Synthetic test fixture'] for key in work['task']['fields']}
        if 'evidence_refs' in content:
            content['evidence_refs'] = work['task']['depends']
        if task == 'proposal':
            content['numeric_claims'] = work['numeric_claims_template']
            content['disagreements'] = []
        return content

    def complete(self, task):
        return w.submit('test', task, self.content(task), 'test fixture')

    def ready(self, complete=False):
        self.begin(complete)
        w.tool('test', 'evidence')
        w.tool('test', 'finance')
        self.complete('operations')

    def diagnosis(self):
        return {'gaps': [], 'decision': 'no_gap', 'reason': 'No further availability gaps within this test scope; declarations remain unverified.',
                'evidence_refs': ['evidence', 'finance', 'proposal', 'event_summary'],
                'capability_status': 'no_new_capability', 'next_check': 'External review is still required.'}

    def test_tool_tasks_cannot_be_submitted_or_spoofed(self):
        self.begin()
        for executor in ('model_assisted', 'deterministic'):
            with self.assertRaisesRegex(ValueError, 'produced by tool'):
                w.submit('test', 'evidence', w.tool_content(w.read(w.directory('test') / 'state.json'), 'evidence'), 'fixture', executor)
        w.tool('test', 'evidence')
        with self.assertRaisesRegex(ValueError, 'produced by tool'):
            w.submit('test', 'finance', {'calculation': {'actual': '1'}, 'interpretation': 'fake', 'limitations': ['fake']}, 'fixture')

    def test_full_no_gap_path_is_allowed_without_certification(self):
        self.ready(complete=True)
        self.complete('proposal')
        w.submit('test', 'diagnosis', self.diagnosis(), 'fixture')
        summary = w.export_summary('test')
        self.assertEqual(summary['next_action_status'], 'not_needed')
        self.assertEqual(summary['external_review'], 'pending')
        self.assertEqual(summary['generation'], 'gen2')

    def test_no_gap_cannot_hide_missing_evidence(self):
        self.ready()
        self.complete('proposal')
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            w.submit('test', 'diagnosis', self.diagnosis(), 'fixture')

    def test_cd_receives_evidence_finance_and_rejections(self):
        self.ready()
        with self.assertRaises(ValueError):
            w.submit('test', 'proposal', {}, 'fixture')
        self.complete('proposal')
        work = w.packet('test', 'diagnosis')
        self.assertEqual(set(work['handoffs']), {'evidence', 'finance', 'proposal'})
        self.assertEqual(work['event_summary']['rejection_count'], 1)

    def test_bad_structured_figures_are_rejected(self):
        self.ready()
        content = self.content('proposal')
        content['numeric_claims']['totals']['variance'] = '99999'
        with self.assertRaisesRegex(ValueError, 'match the finance'):
            w.submit('test', 'proposal', content, 'fixture')
        self.complete('proposal')

    def test_prose_cannot_bypass_numeric_claims(self):
        self.ready()
        content = self.content('proposal')
        content['recommendation'] = 'Save 99999 immediately'
        with self.assertRaisesRegex(ValueError, 'numeric literals'):
            w.submit('test', 'proposal', content, 'fixture')

    def test_missing_dependency_tool_failure_is_recorded(self):
        w.start('test')
        with self.assertRaises(ValueError):
            w.tool('test', 'evidence')
        state = w.read(w.directory('test') / 'state.json')
        self.assertEqual(state['submissions'], 1)
        self.assertIn('tool_failed', (w.directory('test') / 'events.jsonl').read_text())

    def test_changed_source_tool_failure_is_recorded(self):
        self.begin()
        (self.root / 'web/evidence/f03/v1/f03-costs.csv').write_text('changed')
        with self.assertRaises(ValueError):
            w.tool('test', 'evidence')
        self.assertIn('tool_failed', (w.directory('test') / 'events.jsonl').read_text())


if __name__ == '__main__':
    unittest.main()
