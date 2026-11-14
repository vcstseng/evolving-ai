# 本機案件流程｜pilot-1

這是可執行的半自動交接器。程式依依賴順序提供任務包、檢查交付格式、重算數字、保存不可覆寫的交付與雜湊。方案及診斷仍由同一模型／人類協助履行角色；沒有自主 LLM 調度，也不是獨立多 Agent 實驗。

## 三層責任

| 層 | 本輪角色 | 執行方式 |
|---|---|---|
| 案件整合 | A01：範圍、派工、整合 | 本模型協助，手動交付 |
| 專業執行 | A02 資料、A06 財務、A08 營運 | A02/A06 本機 Python；A08 本模型協助 |
| 能力發展 | CD：缺口、調整與下一步 | 本模型協助；不具外部驗收權 |

角色契約改編自原 Consulting Agent Framework，只實作這個成本案例切片，沒有匯入全部 16 個角色。建立契約不等於驗證專業能力。

## 執行

在 repo 根目錄，Python 3.10+，無額外依賴：

```powershell
python -X utf8 -m src.workflow start my-run-01
python -X utf8 -m src.workflow packet my-run-01 scope
python -X utf8 -m src.workflow submit my-run-01 scope --file runs/my-run-01/scope-input.json --actor "actual author"
python -X utf8 -m src.workflow tool my-run-01 evidence
python -X utf8 -m src.workflow tool my-run-01 finance
python -X utf8 -m src.workflow packet my-run-01 operations
```

依 packet 的 fields 提供 JSON，再以 submit 交付 operations → proposal → diagnosis。每項任務附角色契約與已完成依賴，不自動呼叫模型；不要把 CLI 執行稱為自主思考。一般題目可只交方案，本案例因有數字才用 CSV 工具。

```powershell
python -X utf8 -m src.workflow status my-run-01
python -X utf8 -m src.workflow export my-run-01
python -m unittest discover -s tests -v
python scripts/check_versions.py
```

start 使用 cases/active/f03-pilot.json。新的 run ID 才可重跑，舊任務不能覆寫。packet 列出必要欄位；缺欄、缺依賴、來源或已交付檔案被改寫都會拒收。提交失敗記入 events.jsonl；最多 12 次嘗試，由程式強制停止。原始執行資料只在被 Git 忽略的 runs/，不得提交。

模型 token／成本若無計量就保留未知，不能填零。此 runner 不發模型請求，所以沒有模型 token 預算執行器；12 次是交付嘗試上限，不是模型費用上限。另有程式工具耗時紀錄。

## 缺口與調整

執行問題可重試／重派，證據缺口可補資料／停止，方法缺口可改方法，交接缺口可重派／改方法，工具缺口可補工具；專業缺口才可招募既有角色或提出新角色。混合缺口需分開診斷。本輪只記錄調整決策，不自行取得資料、安裝工具或執行模型；下一步狀態仍為 pending。

新角色提案須附目的、輸入、輸出、邊界與資格測試，存在 diagnosis 交付內，狀態只准 candidate_unverified。不得直接註冊成已驗證能力。招募既有角色需在本輪 contract 登錄。

## 首輪實際狀態

f03-20261115-01：六步交付已記錄；本輪計算 166000 → 225300、差異 59300。CD 依交付指出缺期間與根因資料，選 request_evidence，未新增 Agent／能力。這是內部缺口判斷，不是品質驗收或外部審查。

整合方案是新的工作草稿，留在本機 run，與已固定的網頁方案 v1 分開；沒有把草稿替換成 v2。歷史答案已知，不是未見測試。Claude 回覆與真實成效均不存在。

export 只輸出欄位白名單到 web/evidence/f03-workflow.json：角色／步驟／執行方式／交付雜湊、算術、調整代碼及限制。它不包含原始事件、提示詞與完整模型交付。此出口目前只允許已完成的合成 F03 試行摘要；未來私有案需另作資料授權與公開審核。

## 審查後的當前狀態
使用者於 2026-11-15 轉貼 Claude 針對 c002556 的審查。上面的 pending 與無回覆描述屬於原 run 快照，不是現在網站狀態。當前已收到指出缺陷的審查，網頁呈現 Gen 2 候選方法計畫；本文件描述的 runner 仍是 Gen 1，已知固定缺口、無 no_gap、可繞過計算等問題尚未修正。詳 web/evidence/f03-review.md 及 organization/versions/GEN2_CANDIDATE.md。
