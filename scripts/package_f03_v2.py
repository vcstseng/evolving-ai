"""Create a curated public solution bundle from the completed synthetic Gen 2 run.

Raw role JSON, event logs and chat are never copied. Frozen bundles are not overwritten.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import gen2_workflow as w

ACTION_LABELS = {'owner': '負責人', 'scope': '範圍', 'proposed_limit': '建議投入與期限（待確認）', 'minimum_evidence': '最低證據', 'stop': '停止條件', 'action': '行動', 'branch': '判斷分支', 'entry_gate': '進入條件', 'acceptance': '驗收與停止', 'non_gate': '不採用的判準'}

LABELS = {'units': '產量／產品組合', 'material_price': '材料價格', 'material_per_unit': '材料耗用',
          'hourly_rate': '工資率', 'hours_per_unit': '每單位工時', 'overhead_per_unit': '製造費用'}


def money(value):
    number = Decimal(str(value))
    return f'{number:,.0f}' if number == number.to_integral_value() else f'{number:,.2f}'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text_bytes(text):
    return text.replace('\r\n', '\n').encode('utf-8')


def json_bytes(value):
    return text_bytes(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(run_id):
    folder = w.directory(run_id)
    state = w.read(folder / 'state.json')
    w.verify(folder, state)
    if state['case']['kind'] != 'synthetic' or state['case']['id'] != 'f03-gen2-pilot' or len(state['completed']) != 6:
        raise ValueError('Only the completed synthetic F03 Gen 2 run is supported')
    proposal = w.read(folder / 'proposal.json')['content']
    calculation = w.read(folder / 'finance.json')['content']['calculation']
    evidence = w.read(folder / 'evidence.json')['content']
    diagnosis = w.read(folder / 'diagnosis.json')['content']
    if proposal['numeric_claims'] != w.numeric_template(calculation):
        raise ValueError('Proposal figures differ from the accepted calculation')
    events = [json.loads(line) for line in (folder / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
    totals = calculation['totals']
    summary = {'schema': 1, 'generation': 'gen2', 'proposal_version': 'v2', 'run_id': run_id,
               'source_commit': 'a2085d3', 'date': '2026-11-15', 'review_status': 'awaiting_claude_rereview',
               'mode': 'Shared-context model-assisted handoffs plus deterministic tools; not independent agents.',
               'completed_handoffs': 6, 'submissions': state['submissions'],
               'rejections': sum(e['event'] in ('submission_rejected', 'tool_failed') for e in events),
               'adjustment': diagnosis['decision'], 'new_capability': False,
               'model_tokens': None, 'model_cost': None, 'unseen_test': False, 'business_outcome': 'not_measured',
               'publication_scope': 'Curated final deliverable and checkable synthetic calculation, not raw role handoffs or chat.',
               'recommendation': proposal['recommendation'], 'alternatives': proposal['alternatives'],
               'limitations': proposal['limitations'], 'next_actions': proposal['next_actions'],
               'human_decisions': proposal['human_decisions'], 'disagreements': proposal['disagreements'],
               'evidence_gaps': evidence['gaps'], 'calculation': calculation}
    lines = ['# F03｜Gen 2 方案 v2', '',
             '狀態：六步半自動重跑完成，待 Claude 複審；未宣稱通過、優於 Gen 1 或企業有效。', '',
             f'日期：2026-11-15；run：{run_id}；方法來源提交：a2085d3。',
             '本文件是整合交付的整理版；原始角色 JSON、事件及聊天只留本機。', '',
             '## 問題與限制',
             state['case']['brief'],
             '沿用相同四列歷史合成 CSV，未補入日期、工單或其他資料。幣別沿用示範的合成 TWD。',
             '同一 Codex 對話協助各角色，A02/A06 使用程式；不是獨立 Agent、未見測試或等預算對照。', '',
             '## 建議與調查順序', proposal['recommendation'], '',
             '先核對可比期間、良品與工時定義；以下金額只是在提供的每單位成本模型下的條件式歸因。', '',
             f'- 原始基準 {money(totals["baseline"])}；實際 {money(totals["actual"])}；總差異 +{money(totals["variance"])}。',
             f'- 按各產品實際產量調整的基準 {money(totals["flex_baseline"])}；產量／組合效應 +{money(totals["volume_effect"])}。',
             f'- 剩餘非產量差異 +{money(totals["non_volume_variance"])}；這不是可節省額。', '',
             '| 順序 | 對象 | 依據 | 需要的證據／判斷 |', '|---|---|---|---|',
             '| 前置 | 期間與定義 | 尚未提供 metadata | 日期、良品單位、工時與成本範圍可比前，不判斷效率 |',
             f'| 先分離 | 產量／產品組合 | +{money(totals["volume_effect"])}，占總差異 {Decimal(totals["volume_effect"])/Decimal(totals["variance"])*100:.2f}% | 量變不是浪費；彈性基準假設仍待核對 |',
             '| 1 | 馬達工時 | 馬達非產量差異較大，工時在全部順序均為最大正向歸因 | 先查口徑，再查規格／批量與可比工單的必要及損失工時 |',
             '| 2 | 工資率 | 為另一項正向非產量差異 | 薪酬範圍、加班與人員組合，不直接建議降薪 |',
             '| 3 | 材料有利差異 | 價格與耗用為負向抵銷 | 核對品質、良品與定義；不把有利數字當改善已成立 |',
             '| 低優先 | 製造費用 | 本模型沒有差異 | 不代表其他期間或真實固定成本沒有問題 |', '',
             '## 分產品拆分',
             '| 產品 | 原始基準 | 實際 | 按實際產量基準 | 產量效應 | 非產量差異 |',
             '|---|---:|---:|---:|---:|---:|']
    for row in calculation['by_product']:
        lines.append('| ' + row['product'] + ' | ' + ' | '.join(money(row[k]) for k in ('baseline', 'actual', 'flex_baseline', 'volume_effect', 'non_volume_variance')) + ' |')
    lines += ['', '先限馬達做只讀調查，定位器仍保留監測；這是有條件的資源優先序，不是根因或效益結論。', '',
              '## 固定順序的成本橋接',
              '順序：產量／組合 → 材料價格 → 材料耗用 → 工資率 → 工時 → 製造費用。',
              '| 因素 | 貢獻 | 占原始總差異 | 解讀 |', '|---|---:|---:|---|']
    for field in calculation['fixed_order']:
        amount = Decimal(calculation['fixed_effects'][field])
        pct = amount / Decimal(totals['variance']) * 100
        note = '量變，先調整基準' if field == 'units' else ('負向抵銷，仍需口徑核對' if amount < 0 else '歸因，不是因果或節省額')
        lines.append(f'| {LABELS[field]} | {money(amount)} | {pct:.2f}% | {note} |')
    lines += ['', '百分比以原始總差異為分母，四捨五入可能不恰為百分之百；正向貢獻可超過非產量淨差異，因材料負向抵銷。不能再把產量效應從剩餘差異重複扣除。', '',
              '## 歸因順序敏感度',
              '已列舉六因素全部 720 種順序。範圍不是機率信賴區間；平均是 Shapley 分配，不能證明原因。',
              '| 因素 | 最小 | 最大 | 全順序平均（約） |', '|---|---:|---:|---:|']
    for field in calculation['fixed_order']:
        row = calculation['sensitivity']['effects'][field]
        lines.append(f'| {LABELS[field]} | {money(row["min"])} | {money(row["max"])} | {money(row["mean"])} |')
    lines += ['', '工時在全部順序均為最大正向歸因，因此「先查工時」在本資料下不因順序翻轉；它仍不代表工時損失或員工效率低落。平均的精確有理數與原始數值見 calculation.json，顯示四捨五入可能有尾差。', '',
              '## 選項與取捨']
    for item in proposal['alternatives']:
        lines += [f'- **{item["option"]}**：{item["tradeoff"]}']
    lines += ['', '## 有界調查、關卡與停止']
    for index, item in enumerate(proposal['next_actions'], 1):
        lines += ['', f'### {index}. {item["stage"]}']
        for key, value in item.items():
            if key != 'stage':
                lines.append(f'- {ACTION_LABELS[key]}：{value}')
    lines += ['', '以上調查範圍、五個工作日與人力上限都是待問題擁有者確認的提案，不是已核定的期限、費用或已量測投入；本 run 沒有執行現場調查。', '',
              '## 缺口與分歧',
              'CD 依實際 evidence、finance、proposal 及事件摘要，選擇補證據；沒有新增角色或能力。']
    for gap in evidence['gaps']:
        lines.append(f'- {gap["id"]}：{gap["detail"]}')
    lines += [''] + ['- ' + value for value in proposal['disagreements']]
    lines += ['', '## 邊界與尚未完成'] + ['- ' + value for value in proposal['limitations']]
    lines += ['- 尚無 Claude 對 v2 的實際回覆、未見重用、普通 Agent 對照或企業成效。',
              '- 模型 token／費用未知；12 次只是單一 run 的提交上限。不能宣稱等成本比較或改善幅度。',
              '- 24 項程式檢查是前輪程式驗證；這一輪另完成六步半自動交付，不能把兩者混成獨立品質評分。', '']
    review = '''# 請 Claude 複審 F03 方案 v2

本包是 Gen 2 六步半自動重跑後的整理交付，尚未送模型 API，也沒有外部通過結論。請先讀 brief.md、proposal.md；需要數字時用 f03-costs.csv 與 calculation.json。publication.json 提供與網頁一致的整理內容，manifest.json 記錄版本與檔案雜湊。

請檢查：
1. v2 是否回答調查優先序，並正確區分總差異、產量／組合與非產量差異？
2. 分產品與全順序分析是否一致？工時排序是否有足夠且適當的依據？
3. 方案是否把歸因誤當因果、浪費或可節省額？是否有未支持承諾？
4. 建議的只讀範圍、期限、人力上限、分支與停止條件是否合理？它們均未獲人類批准。
5. 對前次審查的回應有哪些仍不足？請分開列算術、方法、方案品質與研究設計。

方法程式與測試使用提交 a2085d3 的 src/gen2_workflow.py、src/gen2_analysis.py、tests/test_gen2.py。提供資料宣告不等於驗真；no_gap 只有在指定可用性缺口為空時才允許。本案實際仍有缺口，所以沒有走 no_gap。

同一模型對話協助履行角色，原始聊天、角色 JSON 與事件不公開；不能僅靠本包證明獨立 Agent、成本公平性或完整內部過程。已知 F03 答案，這是同案回歸，不是未見泛化或對照實驗。

請每項發現附位置、理由、嚴重度、修改要求與不確定性，並明列本次讀到／未讀到的資料。收到實際回覆前，網站維持待複審。
'''
    comparison = '''# Gen 1 → Gen 2｜本次已觀察與未觀察

- Gen 1 方案 v1 保留；Gen 2 形成 v2。這是同案、已知答案、受審查回饋影響的修訂，不能稱為獨立實驗勝出。
- v2 明列產量調整、分產品、全順序敏感度與調查排序；v1 缺這些主文內容。是否改善方案品質仍待 Claude 複審。
- 新程式具動態缺口、no_gap 與工具數值約束，已由前輪程式測試檢查；本案實際有缺口，所以 no_gap 沒被使用。
- 兩輪都選補證據；不能因 Gen 2 仍做相同決策就說無用，也不能因文字與工具較完整就宣稱企業效果更好。
- 本輪六次提交，無拒收。不同世代的模型 token／成本未計量，無等預算、重複、盲評、未見重用或普通 Agent 對照。
- 原始 run 留在本機。公開交付可以核對方案與算術，但不是原始過程的完整證明。
'''
    files = {
        'brief.md': (ROOT / 'web/evidence/f03/v1/brief.md').read_bytes().replace(b'\r\n', b'\n'),
        'f03-costs.csv': (ROOT / state['case']['source']).read_bytes().replace(b'\r\n', b'\n'),
        'proposal.md': text_bytes('\n'.join(lines)), 'review-brief.md': text_bytes(review),
        'comparison.md': text_bytes(comparison), 'calculation.json': json_bytes(calculation),
        'publication.json': json_bytes(summary)
    }
    manifest = {'case': 'f03', 'generation': 'gen2', 'proposal_version': 'v2', 'parent': 'v1',
                'run_id': run_id, 'date': '2026-11-15', 'source_commit': 'a2085d3',
                'review_status': 'awaiting_claude_rereview', 'change_reason': 'Respond to the user-relayed Claude review of c002556; retain v1.',
                'files': [{'path': name, 'sha256': sha(data)} for name, data in sorted(files.items())]}
    files['manifest.json'] = json_bytes(manifest)
    target = ROOT / 'web/evidence/f03/v2'
    target.mkdir(exist_ok=False)
    for name, data in files.items():
        (target / name).write_bytes(data)
    print('Created curated F03 v2 bundle; six handoffs complete, external re-review pending.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    build(parser.parse_args().run_id)
