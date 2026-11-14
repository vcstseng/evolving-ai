# The Evolving Firm

AI 組織能力發展研究。工作名稱：Evolving AI Consulting Firm。

**研究問題：AI 組織能否從案件中發現能力缺口，取得或建立新能力，並在後續案件中有效重用？**

## 目前進度

Layer 1 中英文首頁原型已完成，延續 Startup Radar／Capability Store 的視覺風格。目前為靜態 UI 原型，尚未選定或執行研究案件，沒有自主 Agent 執行器或實驗結果。

- 案件、組織與能力、改進紀錄三個入口，使用預覽對話框。
- 五階段互動：提出問題 → 提出方案 → 外部審查 → 診斷與調整 → 驗證重用。
- 示意案例與研究狀態明確標示；三種證據分開說明。
- 中英文桌面與 320px 手機版已檢查。

![Layer 1 首頁](presentation/layer-one-desktop.png)

## 本機啟動

需要 Node.js（支援 `import.meta.dirname`，例如 Node 22+）。沒有第三方依賴，不需要 npm install。

```powershell
cd D:\evolving-ai\web
npm run dev
```

開啟 http://127.0.0.1:4183/ 。預設中文，英文網址為 http://127.0.0.1:4183/?lang=en 。
伺服器只綁定本機，僅提供 web 目錄內容；結束預覽按 Ctrl+C。

語法檢查：

```powershell
node --check web/src/app.js
node --check web/serve.mjs
```

## 研究設計

- 三層責任：專業執行、案件整合、能力發展；證據與評估提供橫向支援。
- 延用既有 16 種角色規格作為專業底座；本 repo 尚未匯入或部署這些角色。
- Junior／Senior／Director 等職級為早期例子，不是固定需求。
- 新增 Agent 是選項之一，先判斷是否缺資料、方法、工具或分工。
- 第一版定位為可行性觀察；單 Agent、固定組織與可調整組織的比較仍待定義與執行。
- 通過模型審查不等於企業成效已驗證。

## 文件入口

| 文件 | 用途 |
|---|---|
| [概念](docs/CONCEPT.md) | 目前概念與研究邊界 |
| [進度](docs/PROGRESS.md) | 已完成、限制與下一步 |
| [目錄](docs/FILE_DIRECTORY.md) | 實際檔案與預留區域 |
| [試行協議草案](experiments/protocols/PILOT.md) | 執行前需確認的評估與預算 |
| [案件模板](cases/templates/CASE_BRIEF.md) | 案件範圍、證據與驗收 |
| [審查模板](reviews/templates/REVIEW.md) | 問題、證據與未解分歧 |
| [展示構想](presentation/DEMO_STORY.md) | 後續案件故事線 |

## 資料與版本

私有資料、金鑰與原始執行紀錄不納入 Git。`data/private/` 與 `runs/` 只保留使用說明。未經確認授權，不傳送私有資料給外部模型。

GitHub：公開 repo https://github.com/vcstseng/evolving-ai 。

網站：https://vcstseng.github.io/evolving-ai/ （英文：?lang=en）。

GitHub Pages 透過 `.github/workflows/pages.yml` 發布，main 的 web/ 或 workflow 更新觸發部署。只上傳 index.html、app.js 與 styles.css；本機伺服器、研究文件與資料不納入網站 artifact。
