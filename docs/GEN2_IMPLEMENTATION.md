# Gen 2 方法實作｜待完整案件重跑

已實作 C01–C04，並通過 24 項程式測試（Gen 1 十項、Gen 2 十四項）。測試中的完整流程使用明示的合成 fixture／佔位交付，不是模型重新解決 F03。沒有方案 v2、外部複審、未見重用或改善結論。

## 保留與入口

- Gen 1：src/workflow.py、src/cost_analysis.py、organization/roles/pilot.json 與原 run 均保留。
- Gen 2：src/gen2_workflow.py、src/gen2_analysis.py、organization/roles/gen2.json。
- 案件設定：cases/active/f03-gen2.json。尚未取得日期／定義／工單資料，evidence_metadata 是 null，不自行補造。
- Python 3.10+，無第三方依賴，於專案根目錄執行。

```powershell
python -X utf8 -m src.gen2_workflow start f03-gen2-01
python -X utf8 -m src.gen2_workflow packet f03-gen2-01 scope
python -X utf8 -m src.gen2_workflow submit f03-gen2-01 scope --file runs/f03-gen2-01/scope-input.json --actor "actual author"
python -X utf8 -m src.gen2_workflow tool f03-gen2-01 evidence
python -X utf8 -m src.gen2_workflow tool f03-gen2-01 finance
python -X utf8 -m src.gen2_workflow packet f03-gen2-01 operations
```

依任務包交付 operations → proposal → diagnosis；仍是半自動，沒有自動模型呼叫。所有原始交付留在 Git 忽略的 runs/。Gen 2 禁止讀取／更改 Gen 1 run。

## C01：以資料產生可用性缺口

CSV 驗證欄位、數值、配對與重複；日期、units／hours_per_unit 定義與營運證據引用從選用 JSON metadata 檢查。缺什麼才記錄什麼，格式錯誤或期間長度不同另列缺口。

metadata 格式見 tests/test_gen2.py 的 COMPLETE_METADATA；它只作合成測試，不是 F03 真實資料，也不是未見研究案例。可在新的案件設定指定 evidence_metadata 相對路徑，該檔案會在 run 起點留存雜湊。

提供資料宣告只代表 provided_unverified／referenced_not_verified，不代表獨立核實。空缺口只表示指定的可用性要求滿足，不代表根因或成效成立。

## C02：完整依據與 no_gap

CD 取得 evidence、finance、proposal 與 event_summary（提交數、拒收數、拒收原因）。gaps 可為空；若沒有未解的可用性缺口，可選 no_gap 與 no_new_capability，表示無須額外調整，而非通過外部審查。有未解 evidence gaps 時不能直接 no_gap。其他缺口仍可補資料、改方法／工具／分工，專業缺口才提出角色候選。

## C03：財務方法

- 先以實際產量、基準每單位成本重算彈性基準；此模型仍假設提供的是每單位成本，不宣稱已拆出真實固定成本。
- 分產品輸出成本、產量影響、非產量差異與固定順序歸因。
- 六因素全列 720 種順序，輸出 min／max、Shapley 平均及精確有理數；平均小數顯示到十二位。
- 排序是會計差異的調查訊號，不是因果或節省額；零差異時不宣稱工時是問題。

F03 工具回歸結果：基準 166000、實際 225300、按實際產量基準 188000；產量效應 22000，剩餘 37300（馬達 32100、定位器 5200）。全順序工時效應 34000–42000，平均 37950，皆為最大正向歸因。這只是原已知資料的工具核對。

## C04：數值與工具一致

evidence／finance 只接受 tool 路徑提交，且內部重算核對內容；一般 submit 即使聲稱 deterministic 也不接受。這是本機 CLI 交付約束，不是對可任意改寫 Python 程式的敵對程式碼的安全邊界。

proposal 的 packet 提供 numeric_claims_template（totals、fixed_effects、by_product、sensitivity），交付的 numeric_claims 必須完全一致。這個 pilot 約定：數字放結構化欄位，其他敘述不放阿拉伯數字或數值型欄位，避免相互矛盾。這也會限制日期／角色編號等文字；不是通用自然語言數字查核器。中文數詞、因果、ROI 等語意仍須模型／人工審查。

空 disagreements 與 required_evidence 可以交付，不強迫編造分歧或資料需求。缺依賴、來源變更等 tool 拒收現在會留存。

## 證據與尚未完成

web/evidence/gen2-checks.json 是程式測試結果摘要；f03-gen2-calculation.json 是已知 F03 的工具回歸輸出。都不含原始模型交付。

尚未完成：實際角色解題重跑與方案 v2、Claude 複審、跨案／基準比較、案件層級預算、token 計量、公開可核對的整合交付包。12 次仍只是單一 run 的提交上限，接自動模型前需另外限制實驗總預算。
