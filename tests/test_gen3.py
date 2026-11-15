import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.gen3_policy import assess
from src import gen3_workflow as w

ROOT = w.ROOT
DATA = ROOT / 'web/evidence/method-probe/definition.csv'
CLEAN = json.loads((ROOT / 'web/evidence/gen3/metadata-clean.json').read_text(encoding='utf-8'))


def request(kind='rate_change', mixed=False):
    claims = [{'id': 'requested', 'kind': kind, 'required': True, 'answers': ['question']}]
    if mixed:
        claims.append({'id': 'calculation', 'kind': 'conditional_arithmetic', 'required': False, 'answers': ['question']})
    return {'decision': 'Determine whether the supplied rate difference is comparable.', 'questions': [{'id': 'question', 'text': 'Determine comparable rate change'}], 'claims': claims}


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.meta_path = Path(self.tmp.name) / 'metadata.json'
        self.meta = copy.deepcopy(CLEAN)

    def run_gate(self, req=None):
        self.meta_path.write_text(json.dumps(self.meta), encoding='utf-8')
        return assess(DATA, self.meta_path, req or request(), brief=request()['decision'])

    def test_clean_scoped_no_gap_is_not_source_truth_or_authorization(self):
        gate = self.run_gate()
        self.assertEqual(gate['decision'], 'no_gap')
        self.assertTrue(gate['requested_decision_answered'])
        self.assertEqual(gate['review_status'], 'pending')
        self.assertEqual(gate['business_authorization'], 'not_granted')
        self.assertTrue(all(c['verification_by_this_tool'] == 'structure_and_consistency_only' for c in gate['comparability']))

    def test_original_probe_conflict_is_detected_despite_complete_availability(self):
        self.meta = json.loads((ROOT / 'web/evidence/method-probe/definition-metadata.json').read_text())
        gate = self.run_gate()
        self.assertEqual(gate['availability']['gaps'], [])
        self.assertEqual(next(c['status'] for c in gate['comparability'] if c['field'] == 'hourly_rate'), 'no')
        self.assertEqual(gate['decision'], 'request_evidence')

    def test_positive_declaration_cannot_override_legacy_conflict(self):
        self.meta['hourly_rate_comparison'] = {'comparable': False}
        self.assertEqual(self.run_gate()['blocked_claims'], ['requested'])

    def test_unknown_does_not_answer_original_question_but_allows_conditional_calculation(self):
        self.meta['comparability'].pop('hourly_rate')
        gate = self.run_gate(request(mixed=True))
        self.assertEqual(gate['decision'], 'conditional_delivery')
        self.assertEqual(gate['permitted_claims'], ['calculation'])
        self.assertEqual(gate['blocked_claims'], ['requested'])
        self.assertFalse(gate['requested_decision_answered'])

    def test_missing_reference_downgrades_yes(self):
        self.meta['comparability']['hourly_rate']['source_refs'] = ['does-not-exist']
        self.assertEqual(self.run_gate()['decision'], 'request_evidence')

    def test_existing_reference_with_fabricated_definition_quote_is_rejected(self):
        self.meta['evidence_sources']['fixture']['text'] = 'Unrelated input content'
        self.assertEqual(self.run_gate()['decision'], 'request_evidence')

    def test_declared_only_cannot_reach_level_three(self):
        self.meta['comparability']['hourly_rate']['verification'] = 'declared'
        gate = self.run_gate()
        self.assertLess(gate['run_level'], 3)
        self.assertNotEqual(gate['decision'], 'no_gap')

    def test_uncovered_question_cannot_be_hidden_by_easy_claim(self):
        req = request('conditional_arithmetic')
        req['questions'].append({'id': 'unanswered', 'text': 'What caused the increase?'})
        gate = self.run_gate(req)
        self.assertEqual(gate['uncovered_questions'], ['unanswered'])
        self.assertFalse(gate['requested_decision_answered'])
        self.assertNotEqual(gate['decision'], 'no_gap')

    def test_mixed_required_claims_aggregate_to_strictest_level(self):
        req = request('conditional_arithmetic')
        req['claims'].append({'id': 'cause', 'kind': 'causal', 'required': True, 'answers': ['question']})
        gate = self.run_gate(req)
        self.assertEqual(gate['run_level'], min(c['level'] for c in gate['claims']))
        self.assertEqual(gate['blocked_claims'], ['cause'])
        self.assertNotEqual(gate['decision'], 'no_gap')

    def test_nonzero_not_applicable_cannot_be_ignored(self):
        self.meta['comparability']['hourly_rate']['status'] = 'not_applicable'
        gate = self.run_gate(request('conditional_arithmetic'))
        self.assertNotEqual(gate['decision'], 'no_gap')
        self.assertTrue(any('nonzero' in c['reason'] for c in gate['comparability']))

    def test_empty_comparability_table_only_allows_conditional_arithmetic(self):
        self.meta['comparability'] = {}
        gate = self.run_gate(request('conditional_arithmetic'))
        self.assertEqual(gate['run_level'], 2)
        self.assertEqual(gate['decision'], 'conditional_delivery')

    def test_clean_arithmetic_is_not_blocked(self):
        gate = self.run_gate(request('conditional_arithmetic'))
        self.assertEqual((gate['run_level'], gate['decision']), (3, 'no_gap'))

    def test_requested_decision_cannot_shrink_pinned_brief(self):
        req = request('conditional_arithmetic')
        req['decision'] = 'Only add the supplied numbers'
        with self.assertRaisesRegex(ValueError, 'pinned'):
            self.run_gate(req)

    def test_different_definition_texts_cannot_be_yes(self):
        self.meta['comparability']['hourly_rate']['actual_definition'] = 'Loaded cost including benefits'
        gate = self.run_gate()
        self.assertEqual(next(c['status'] for c in gate['comparability'] if c['field'] == 'hourly_rate'), 'no')

    def test_source_conflict_blocks_positive_declarations(self):
        self.meta['evidence_sources']['fixture']['conflict'] = True
        self.assertEqual(self.run_gate()['permitted_claims'], [])

    def test_reported_verification_does_not_become_tool_verification(self):
        self.meta['comparability']['hourly_rate']['verification'] = 'independently_verified'
        item = next(c for c in self.run_gate()['comparability'] if c['field'] == 'hourly_rate')
        self.assertEqual(item['reported_verification'], 'independently_verified')
        self.assertEqual(item['verification_by_this_tool'], 'structure_and_consistency_only')

    def test_not_applicable_cannot_skip_required_factor(self):
        self.meta['comparability']['hourly_rate']['status'] = 'not_applicable'
        self.assertEqual(self.run_gate()['decision'], 'request_evidence')

    def test_period_duration_warning_cannot_be_overridden(self):
        self.meta['periods']['actual']['end'] = '2026-10-29'
        self.assertEqual(self.run_gate()['decision'], 'request_evidence')

    def test_irrelevant_unknowns_are_retained_without_blocking_scoped_claim(self):
        self.meta['comparability'].pop('material_price')
        gate = self.run_gate()
        self.assertEqual(gate['decision'], 'no_gap')
        issue = next(i for i in gate['unresolved_issues'] if i['id'] == 'comparability.material_price')
        self.assertEqual(issue['affected_claim_ids'], [])

    def test_arithmetic_and_evidence_plan_remain_qualified_when_evidence_missing(self):
        self.meta = {}
        for kind in ('conditional_arithmetic', 'evidence_plan'):
            with self.subTest(kind=kind):
                gate = self.run_gate(request(kind))
                self.assertEqual(gate['decision'], 'conditional_delivery')
                self.assertTrue(gate['unresolved_issues'])

    def test_metadata_cannot_authorize_causal_or_pilot_claim(self):
        self.meta['human_approved'] = True
        for kind in ('causal', 'pilot', 'efficiency'):
            with self.subTest(kind=kind):
                self.assertEqual(self.run_gate(request(kind))['decision'], 'request_evidence')

    def test_request_schema_cannot_remove_original_obligation(self):
        for req in ({'decision': 'x', 'claims': []}, {'decision': 'x', 'claims': [{'id': 'a', 'kind': 'unknown', 'required': True}]},
                    {'decision': 'x', 'claims': [{'id': 'a', 'kind': 'rate_change', 'required': False}]}):
            with self.subTest(request=req), self.assertRaises(ValueError):
                self.run_gate(req)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for path in ('organization/roles/gen3.json', 'cases/active/f03-gen3.json',
                     'web/evidence/f03/v1/f03-costs.csv', 'web/evidence/f03/v1/proposal.md',
                     'src/gen2_analysis.py', 'src/cost_analysis.py', 'src/gen3_policy.py', 'src/gen3_workflow.py'):
            dest = self.root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, dest)
        (self.root / 'runs').mkdir()
        (self.root / 'web/evidence').mkdir(exist_ok=True)
        self.patcher = patch.object(w, 'ROOT', self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def begin(self, conflict=False):
        meta = copy.deepcopy(CLEAN)
        if conflict:
            meta['hourly_rate_comparison'] = {'comparable': False}
        w.save(self.root / 'metadata.json', meta)
        path = self.root / 'cases/active/f03-gen3.json'
        case = w.read(path)
        case['evidence_metadata'] = 'metadata.json'
        case['requested_decision'] = request(mixed=conflict)
        case['brief'] = case['requested_decision']['decision']
        w.save(path, case)
        w.start('test')
        self.complete('scope')
        w.tool('test', 'evidence')
        w.tool('test', 'finance')
        self.complete('operations')

    def content(self, task):
        work = w.packet('test', task)
        value = {key: ['Synthetic development fixture'] for key in work['task']['fields']}
        if task in ('proposal', 'diagnosis'):
            value['evidence_refs'] = work['task']['depends']
            value['evidence_gate'] = work['evidence_gate_template']
        if task == 'proposal':
            value['numeric_claims'] = work['numeric_claims_template']
            value['disagreements'] = []
        if task == 'diagnosis':
            gate = value['evidence_gate']
            value.update(gaps=gate['unresolved_issues'], decision=gate['decision'], capability_status='no_new_capability')
        return value

    def complete(self, task):
        return w.submit('test', task, self.content(task), 'synthetic fixture')

    def test_clean_full_handoff_path_keeps_external_review_pending(self):
        self.begin()
        self.complete('proposal')
        self.complete('diagnosis')
        summary = w.export_summary('test')
        self.assertEqual(summary['adjustment'], 'no_gap')
        self.assertEqual(summary['external_review'], 'pending')
        self.assertEqual(summary['next_action_status'], 'scoped_review_required')
        self.assertFalse(summary['source_truth_verified'])

    def test_conditional_path_retains_blocked_required_claim(self):
        self.begin(conflict=True)
        self.complete('proposal')
        self.complete('diagnosis')
        summary = w.export_summary('test')
        self.assertEqual(summary['adjustment'], 'conditional_delivery')
        self.assertEqual(summary['blocked_claims'], ['requested'])
        self.assertFalse(summary['requested_decision_answered'])

    def test_cd_cannot_force_no_gap_or_erase_issues_and_rejections_are_recorded(self):
        self.begin(conflict=True)
        self.complete('proposal')
        value = self.content('diagnosis')
        value['decision'] = 'no_gap'
        value['gaps'] = []
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            w.submit('test', 'diagnosis', value, 'fixture')
        self.assertEqual(w.packet('test', 'diagnosis')['event_summary']['rejection_count'], 1)

    def test_proposal_cannot_shrink_requested_question_or_forge_gate(self):
        self.begin(conflict=True)
        value = self.content('proposal')
        value['evidence_gate']['requested_decision'] = 'Only arithmetic, please'
        with self.assertRaisesRegex(ValueError, 'pinned'):
            w.submit('test', 'proposal', value, 'fixture')

    def test_source_change_and_tool_bypass_are_rejected(self):
        self.begin()
        w.start('bypass')
        w.submit('bypass', 'scope', self.content('scope'), 'fixture')
        with self.assertRaisesRegex(ValueError, 'produced by tool'):
            w.submit('bypass', 'evidence', w.tool_content(w.read(w.directory('bypass') / 'state.json'), 'evidence'), 'fixture')
        w.save(self.root / 'metadata.json', {})
        with self.assertRaisesRegex(ValueError, 'Source changed'):
            w.tool('test', 'finance')


class NumericBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'data.csv'
        self.header = 'product,period,units,material_per_unit,material_price,hours_per_unit,hourly_rate,overhead_per_unit\n'

    def calculate(self, rows):
        from src.gen2_analysis import analyze
        self.path.write_text(self.header + '\n'.join(rows) + '\n', encoding='utf-8')
        return analyze(self.path)

    def test_zero_variance_and_one_product(self):
        result = self.calculate(['p,baseline,10,1,2,1,3,4', 'p,actual,10,1,2,1,3,4'])
        self.assertEqual(result['totals']['variance'], '0')
        self.assertEqual(len(result['by_product']), 1)
        self.assertFalse(result['sensitivity']['hours_largest_in_every_order'])

    def test_negative_variance(self):
        result = self.calculate(['p,baseline,10,1,2,1,3,4', 'p,actual,5,1,2,1,3,4'])
        self.assertEqual(result['totals']['variance'], '-45')
        self.assertEqual(result['totals']['non_volume_variance'], '0')

    def test_zero_production(self):
        result = self.calculate(['p,baseline,10,1,2,1,3,4', 'p,actual,0,1,2,1,3,4'])
        self.assertEqual(result['totals']['actual'], '0')
        self.assertEqual(result['totals']['flex_baseline'], '0')

    def test_product_in_only_one_period_is_rejected(self):
        with self.assertRaises(ValueError):
            self.calculate(['p,baseline,10,1,2,1,3,4'])

    def test_invalid_numeric_input_stops_before_gate(self):
        self.path.write_text(self.header + 'p,baseline,10,1,2,1,3,4\np,actual,NaN,1,2,1,3,4\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            assess(self.path, None, request(), brief=request()['decision'])


if __name__ == '__main__':
    unittest.main()
