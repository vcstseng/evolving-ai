# Gen 3｜範圍限定的證據閘門

2026-11-15。實作 src/gen3_policy.py、gen3_workflow.py、organization/roles/gen3.json、cases/active/f03-gen3.json。沿用固定 Gen 2 計算，沒有模型 API、獨立 Agent、企業寫入或跨案成效。方案 v3 仍是 Gen 2 計算的文字交付，不是這次 Gen 3 的新方案。

## 原題、主張與引用
- 由案件設定固定 brief、子問題 questions、所求 claims 與 required。decision 必須逐字等於 brief；每個子問題須有 required 主張對應，缺漏即 incomplete，不得 no_gap。
- 子問題分解由實驗設計者事前核對，不是程式能證明自然語言題目語意完整。CD 只能提交由工具重算的 evidence_gate_template；不可改寫問題、刪除主張或隱藏缺口。
- 比較項目由主張類別的固定依賴表決定；不依賴 CD 任意填 fields。任何非零固定歸因欄位不能用 not_applicable 排除；本版不以 not_applicable 放行所需欄位。
- metadata 的 evidence_sources 必須提供 owner／reference／description／text。baseline_definition 與 actual_definition 經大小寫／空白正規化後，須實際出現在所引輸入 text。只有名稱相符或造假引用 ID 不足以放行。
- 定義文本不同時，本版不支援語意同義或對帳換算，保守阻擋可比結論；明示的 hourly_rate_comparison 矛盾不可被另一份 yes 蓋掉。缺引用／欄位或只有 declared，不能到 L3。
- 來源內的 inspected／independently_verified 是輸入方聲明；程式只核對結構、引用與一致性，不證明來源真實。reported_verification 與 verification_by_this_tool 分開。

## 分層與聚合
| 層級 | 可交付內容 | 此實作的條件 |
|---|---|---|
| L0 | 停止，沒有分析 | 無固定原題／授權合成範圍，或輸入成本無效。CLI 拒收／拋錯；不產生 no_gap。 |
| L1 | 補資料與受限結論 | 因可比性或覆蓋缺口，原所求判斷未完成；保留需要什麼、為何及怎麼補。 |
| L2 | 條件式算術 | 成本可計算但比較依據不全；逐項標示 no／unknown，不宣稱真實效率、因果或節省。 |
| L3 | 所列主張範圍內 ready_for_review | 所需欄位 yes、引用／定義可解析、至少聲明 inspected、沒有相關未解問題。不是外部審查通過。 |

每個主張記 status、level、blockers。run_level 取所有列出主張最嚴層級；未涵蓋子問題使整體最多 L1。只有整體 L3、所求主張有回答且無相關問題，才可 no_gap。若原題受阻但仍能交條件式計算，整體可 conditional_delivery，同時 requested_decision_answered=false，不能用附帶算術宣稱原題已解。

因果、效率結論、試點及企業承諾本輪一律不由閘門授予；需外部證據及授權，這個版本不實作其驗收。補資料方案可在證據不全時交付，但不清空缺口。外部審查一直 pending，企業授權 not_granted，與 no_gap 分開。

## 操作與提交
入口與 Gen 2 相同，但使用獨立程式：

```powershell
python -X utf8 -m src.gen3_workflow start <new-run-id>
python -X utf8 -m src.gen3_workflow packet <run-id> scope
python -X utf8 -m src.gen3_workflow submit <run-id> scope --file <local-json> --actor <actual-actor>
python -X utf8 -m src.gen3_workflow tool <run-id> evidence
python -X utf8 -m src.gen3_workflow tool <run-id> finance
```

operations／proposal／diagnosis 仍需真實交付；packet 提供必要模板。proposal 的數值與 evidence_gate、diagnosis 的 gate／decision／gaps 都須與重算一致。原始 run 只存本機、拒收保留。單一 run 12 次上限不等於實驗總預算；未接自動模型。

## 證據與限制
tests/test_gen3.py 包含敵意案例、六步合成 fixture、乾淨 no_gap、條件式交付與數值邊界。fixture 不是完整模型角色實跑。web/evidence/gen3/development-results.json 是四個已知開發輸入的整理結果，沒有模型或 CD 新案件成果。

`python scripts/check_gen3.py` 重現整理結果及固定來源指紋；原版本檢查仍須通過。不得將已公開資料當未見測試。v3 複審已收到的設計意見不等於 Claude 審過本實作。
