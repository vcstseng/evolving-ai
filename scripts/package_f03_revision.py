"""Create supplemental review evidence and an editorial v3; never rewrite frozen v2/probes."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.cost_analysis import analyze as old_analyze
from src.gen2_analysis import analyze


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lf_sha(data):
    return hashlib.sha256(data.decode('utf-8').replace('\r\n', '\n').encode()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def probe_revision():
    base = ROOT / 'web/evidence/method-probe'
    rows = []
    for name in ('volume', 'order', 'definition'):
        old, new = old_analyze(base / (name + '.csv')), analyze(base / (name + '.csv'))
        effects = {r['field']: r['amount'] for r in old['effects']}
        normalized = {'baseline': str(Fraction(old['baseline'])), 'actual': str(Fraction(old['actual'])),
                      'variance': str(Fraction(old['variance'])),
                      'volume_effect': str(Fraction(effects['units'])),
                      'non_volume_variance': str(Fraction(old['variance']) - Fraction(effects['units']))}
        normalized_new = {k: str(Fraction(new['totals'][k])) for k in normalized}
        checks = {
            'equivalent_totals_match': normalized == normalized_new,
            'fixed_bridges_match': all(Fraction(effects[k]) == Fraction(v) for k, v in new['fixed_effects'].items()),
            'gen1_bridge_sums_to_variance': sum(map(Fraction, effects.values())) == Fraction(old['variance']),
            'gen2_bridge_sums_to_variance': sum(map(Fraction, new['fixed_effects'].values())) == Fraction(new['totals']['variance']),
            'exact_order_means_sum_to_variance': sum(Fraction(r['mean_fraction']) for r in new['sensitivity']['effects'].values()) == Fraction(new['totals']['variance']),
            'baseline_plus_volume_equals_flex': Fraction(new['totals']['baseline']) + Fraction(new['totals']['volume_effect']) == Fraction(new['totals']['flex_baseline']),
            'flex_plus_residual_equals_actual': Fraction(new['totals']['flex_baseline']) + Fraction(new['totals']['non_volume_variance']) == Fraction(new['totals']['actual']),
            'fixed_and_mean_within_ranges': all(Fraction(r['min']) <= Fraction(new['fixed_effects'][k]) <= Fraction(r['max']) and Fraction(r['min']) <= Fraction(r['mean_fraction']) <= Fraction(r['max']) for k, r in new['sensitivity']['effects'].items()),
        }
        assert all(checks.values()), name
        rows.append({'id': name, 'gen1_equivalent': normalized, 'gen2_equivalent': normalized_new,
                     'invariants': checks,
                     'coverage_only': {'gen1': 'fixed-order bridge; volume is present; residual is derived',
                                       'gen2': 'explicit flexible baseline, product split and order sensitivity'},
                     'semantic_comparability_fixed': False})
    return {'schema': 1, 'date': '2026-11-15', 'kind': 'corrected development coverage report, not a generation ranking',
            'supersedes_interpretation_of': 'results.json', 'original_results_sha256': sha(base / 'results.json'),
            'mapping': {'volume_effect': 'Gen 1 effects[field=units].amount',
                        'non_volume_variance': 'Gen 1 variance minus units amount'},
            'cases': rows, 'models_called': 0, 'unseen_test': False,
            'note': 'The definition mismatch remains unhandled. Properties verify arithmetic consistency, not comparability or proposal acceptance.'}


def main():
    f03 = ROOT / 'web/evidence/f03'
    probe = json.loads((ROOT / 'web/evidence/method-probe/results.json').read_text(encoding='utf-8'))
    commits = {c: subprocess.check_output(['git', 'rev-parse', c], cwd=ROOT, text=True).strip()
               for c in ('a2085d3', '5fe2987', '532359e')}
    # Only curated code fingerprints leave the ignored run. No role content or events are copied.
    state = json.loads((ROOT / 'runs/f03-gen2-20261115-01/state.json').read_text(encoding='utf-8-sig'))
    recorded = {r['path']: r['sha256'] for r in state['sources']}
    methods = []
    for path in ('src/gen2_analysis.py', 'src/gen2_workflow.py'):
        historical = {}
        for label in ('a2085d3', '5fe2987'):
            blob = subprocess.check_output(['git', 'show', f'{commits[label]}:{path}'], cwd=ROOT)
            historical[label] = lf_sha(blob)
        current = lf_sha((ROOT / path).read_bytes())
        assert len(set([current, *historical.values()])) == 1
        assert sha(ROOT / path) == recorded[path]
        if path in probe['source_sha256_lf']:
            assert current == probe['source_sha256_lf'][path]
        methods.append({'path': path, 'sha256_lf': current, 'commit_blob_sha256_lf': historical,
                        'author_checked_local_run_source_sha256': recorded[path],
                        'source_url': f'https://github.com/vcstseng/evolving-ai/blob/{commits["a2085d3"]}/{path}'})
    write(f03 / 'source-attribution.json', {'schema': 1, 'date': '2026-11-15', 'commits': commits,
          'methods': methods, 'calculation_sha256': sha(f03 / 'v2/calculation.json'),
          'input_sha256': sha(f03 / 'v2/f03-costs.csv'),
          'scope': 'Retrospective source continuity check. Git blobs and figures can be checked publicly; original execution cannot be independently attested by this author statement.',
          'raw_run_published': False, 'v2_changed': False})
    write(ROOT / 'web/evidence/method-probe/revision-1.json', probe_revision())
    sections = [
        {'title': ['先核對需求與可比性', 'Confirm demand and comparability'], 'paragraphs': [
            ['日期、良品／重工、成本範圍與需求／庫存尚待核對。增加產量若沒有需求支持，也可能形成不必要庫存；不預設量變合理。', 'Dates, good-unit/rework definitions, cost scope and demand/inventory remain unverified. Increased output may create unnecessary inventory; volume is not assumed justified.'],
            ['先查馬達 BOM／規格／製程／批量是否同時影響工時與材料，再核對工資率口徑。這些是假設，不是已確認的共同原因。', 'Investigate whether motor BOM, specifications, process or batch changes affect both hours and materials, then reconcile wage-rate scope. These are hypotheses, not established causes.']]},
        {'title': ['保留 37,300，分開說明不同假設', 'Keep 37,300 and distinguish assumptions'], 'paragraphs': [
            ['原始成本 166,000 → 225,300，差異 59,300。以基準每單位成本按實際產量計算，基準為 188,000、產量效應 22,000、剩餘 37,300；不是節省額。', 'Costs are 166,000 → 225,300, a difference of 59,300. At baseline unit costs and actual volume, the flexible baseline is 188,000, volume effect 22,000 and residual 37,300; none establishes savings.'],
            ['更換歸因順序時，相應剩餘為 30,500–38,750，這是交互項分配敏感度，不是信賴區間。若 X 製造費用為固定總額，另一模型下剩餘為 39,300；此假設未經資料確認。', 'Across attribution orders the corresponding residual is 30,500–38,750: an allocation sensitivity, not a confidence interval. Assuming fixed total overhead for X produces a separate model residual of 39,300; this assumption is unverified.']]},
        {'title': ['調查優先序', 'Investigation priorities'], 'paragraphs': [
            ['前置核對需求及定義 → 馬達的材料／工時共同變動假設 → 工資率口徑與人員組合。指定模型下馬達剩餘 32,100、定位器 5,200，後者先保留監測。', 'Demand and definitions first → joint motor material/hour hypotheses → wage-rate scope and staffing. Under the specified model, residuals are 32,100 for the motor and 5,200 for the positioner, which remains monitored.'],
            ['工時在 720 順序皆為最大正向歸因，值得優先取得證據；不代表效率差或可控制損失，新增證據可改變方向。', 'Hours are the largest positive attribution in all 720 orders, supporting priority evidence collection, not a conclusion of inefficiency or controllable loss. New evidence may change the direction.']]},
        {'title': ['所有調查步驟共用上限', 'A shared limit across all investigation steps'], 'paragraphs': [
            ['待人類確認：單一馬達、一組可比工單，五個工作日內；財務四小時、營運四小時、品質一小時，共九人時，含協調、取資料、分析及記錄。不是每步重置，也不保證足夠。', 'Subject to human approval: one motor, one comparable work-order group, within five business days; finance four hours, operations four, quality one, totaling nine person-hours including coordination, data, analysis and recording. Limits do not reset per step and may be insufficient.'],
            ['第 1–2 日核對能否開始；第 3–4 日查共同假設；第 5 日核對率差並整合。任一上限先到、無授權或資料矛盾即停止相關判斷並交受限結論；延長須重新批准。詳完整方案的逐步投入分配。', 'Days 1–2 check readiness; days 3–4 examine joint hypotheses; day 5 reconcile rates and close. Stop affected judgments at any limit, missing authorization or conflicting data, and report limitations. Extensions need new approval; step allocations are in the full proposal.'],
            ['現場試點屬後續另案。原因可控制、量測、完整預算、期限、負責人、品質安全與交期、回復條件及人工授權全部具備前，不啟動；不以任意歸因百分比放行。', 'An operational pilot is a separate future decision. It requires a controllable cause, measurement, full budget, duration, owner, quality/safety/delivery criteria, rollback and human approval; an arbitrary attribution percentage cannot authorize it.']]},
    ]
    write(f03 / 'v3/publication.json', {'schema': 1, 'proposal_version': 'v3', 'parent': 'v2',
          'date': '2026-11-15', 'kind': 'editorial_revision_from_external_review',
          'method_generation': 'gen2', 'new_run': False, 'gen3_implemented': False,
          'review_status': 'awaiting_v3_review', 'model_cost': None, 'unseen_test': False,
          'sections': sections})
    files = ['proposal.md', 'publication.json', 'changes.md', 'review-brief.md']
    write(f03 / 'v3/manifest.json', {'schema': 1, 'proposal_version': 'v3', 'parent': 'v2',
          'kind': 'editorial_revision_not_a_new_run', 'method_generation': 'gen2',
          'review_status': 'awaiting_v3_review',
          'parent_manifest_sha256': sha(f03 / 'v2/manifest.json'),
          'calculation_ref': '../v2/calculation.json', 'source_attribution_ref': '../source-attribution.json',
          'review_ref': '../review-v2/review.md',
          'files': [{'path': p, 'sha256': sha(f03 / 'v3' / p)} for p in files]})
    print('Created supplemental attribution, corrected probe interpretation and editorial v3. Gen 2 unchanged; Gen 3 design only.')


if __name__ == '__main__':
    main()
