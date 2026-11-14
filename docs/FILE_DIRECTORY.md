# 檔案目錄

目前可執行內容包括 web/ 的首頁與案件頁，以及 src/ 的本機半自動案件交接器。其他區域為契約、設定、文件、模板或預留目錄。
.git/ 為本機版本資料，不列入以下目錄。

```text
evolving-ai/
  .github/
    workflows/
      pages.yml
  .gitattributes
  .gitignore
  AGENTS.md
  capabilities/
    candidates/
    retired/
    validated/
  cases/
    active/
      f03-pilot.json
      f03-gen2.json
    completed/
    templates/
      CASE_BRIEF.md
  data/
    private/
      README.md
    public/
  docs/
    LOCAL_WORKFLOW.md
    GEN2_IMPLEMENTATION.md
    CONCEPT.md
    FILE_DIRECTORY.md
    PROGRESS.md
  experiments/
    protocols/
      PILOT.md
    results/
  organization/
    roles/
      pilot.json
      gen2.json
    versions/
      GEN1.md
      GEN2_CANDIDATE.md
  presentation/
    DEMO_STORY.md
    layer-one-desktop.png
  README.md
  reviews/
    templates/
      REVIEW.md
  runs/
    README.md
  scripts/
    check_f03.py
    check_versions.py
  src/
    __init__.py
    workflow.py
    cost_analysis.py
    gen2_workflow.py
    gen2_analysis.py
  tests/
    test_workflow.py
    test_gen2.py
  web/
    index.html
    package.json
    serve.mjs
    evidence/
      f03-workflow.json
      f03-review.md
      gen2-checks.json
      f03-gen2-calculation.json
      f03-costs.csv
      f03-summary.md
      f03-provenance.json
      f03/
        v1/
          brief.md
          proposal.md
          f03-costs.csv
          f03-provenance.json
          manifest.json
    src/
      case.js
      cases.js
      workflow.js
      evolution.js
      app.js
      styles.css
```

## 主要區域

- web/：中英文靜態首頁、樣式與僅限本機的預覽伺服器。
- organization/、capabilities/：預留角色、組織版本及候選／驗證／退役能力，尚無 Agent 實作。
- cases/、reviews/：案件與審查模板；active/ 有 F03 本機合成試行設定；completed/ 尚無完成研究案件。
- experiments/：可行性試行草案；results/ 尚無結果。
- data/private/、runs/：不提交內容，僅保留說明。
- presentation/：展示草案與首頁截圖。
- src/、tests/：本機半自動交接器、成本計算與流程測試；網站程式位於 web/src/。
- .gitattributes：文字 LF 與 PNG binary 規則。

GitHub 目前為 public；Pages 發布雙語首頁、案件頁與合成證據。

- .github/workflows/pages.yml：main 分支網站更新時檢查語法並部署 Pages。

雙版本 UI：web/src/app.js 內 matrix 為標記清楚的虛構示意資料；data-matrix 開啟證據結構預覽，不代表已執行測試。版本設計詳 docs/CONCEPT.md。

第一輪範圍以 docs/CONCEPT.md、experiments/protocols/PILOT.md 為準；首頁版本矩陣為展示概念，非執行器功能。

- presentation/version-matrix-desktop.png：雙版本區塊的本機視覺檢查截圖（虛構矩陣）。

- web/src/case.js：F03 歷史合成案件頁，已收到轉貼審查，Gen 2 候選待實作。
- web/evidence/：可公開的合成 CSV、方案核對稿、來源雜湊；非原始執行 bundle。
- scripts/check_f03.py：獨立算術與發布資料完整性檢查。

- presentation/f03-case-desktop.png：案件頁桌面檢查截圖。

方案優先調整：web/src/case.js 呈現方案、Claude 審查與修改；web/evidence/f03-summary.md 是方案與審查說明，CSV 為選用佐證。cases/templates/CASE_BRIEF.md 與 reviews/templates/REVIEW.md 已同步交付與審查規則。Layer 2 隨網站部署一併發布。

- web/src/cases.js：雙語案件登錄與狀態篩選；首頁、列表、案件相互導覽。
- web/evidence/f03/v1/：固定文件版本，保留題目／方案／選用佐證及來源與 SHA-256。
- scripts/check_versions.py：核對固定 manifest 與檔案完整性。

- presentation/case-register-desktop.png：案件列表桌面驗證截圖。

UI／UX 整理沿用 web/src/app.js、cases.js、case.js 與 styles.css；沒有新增功能模組或資料目錄。web/evidence/f03/v1/ 的固定文件維持原樣。

## 本機流程新增檔案
- src/workflow.py：本機交接、依賴、提交上限、缺口分類與白名單摘要出口。
- src/cost_analysis.py：輸入驗證與 Decimal 固定順序差異計算；不作因果推論。
- src/__init__.py：Python 套件入口。
- organization/roles/pilot.json：A01/A02/A06/A08/CD 的本輪契約。
- cases/active/f03-pilot.json：合成試行範圍與交付上限。
- tests/test_workflow.py：執行流程及錯誤情境測試。
- docs/LOCAL_WORKFLOW.md：操作方式、實際完成與未完成範圍。
- web/evidence/f03-workflow.json：公開白名單執行摘要，不含原始交付與事件。
- web/src/workflow.js：在既有案件頁顯示本輪摘要。
- runs/f03-20261115-01/：只在本機，Git 忽略，含交付與事件；不納入公開目錄樹或 Pages artifact。

- presentation/local-workflow-desktop.png：本輪執行摘要桌面截圖。

- web/src/evolution.js：世代導覽、轉貼審查摘要、候選方法與待重跑比較；不產生實驗結果。
- web/evidence/f03-review.md：審查來源、範圍及發現摘要，非逐字全文。
- organization/versions/GEN1.md、GEN2_CANDIDATE.md：受審查基線與未實作候選的區分。

- presentation/gen2-candidate-desktop.png：候選方法、世代／方案區分的桌面檢查截圖。

## Gen 2 方法實作新增
- src/gen2_analysis.py：動態資料可用性、產量與產品拆分、720 種順序及 Shapley 敏感度。
- src/gen2_workflow.py：獨立 Gen 2 runner、no_gap、CD 輸入與數值一致性約束；原 src/workflow.py 保留 Gen 1。
- organization/roles/gen2.json、cases/active/f03-gen2.json：Gen 2 契約及已知合成回歸案件設定。
- tests/test_gen2.py：十四項新測試；合成 fixture 不是未見研究案例。
- docs/GEN2_IMPLEMENTATION.md：操作方式、數值約束及尚未完成範圍。
- web/evidence/gen2-checks.json：24 項測試摘要及正規化文字來源雜湊。
- web/evidence/f03-gen2-calculation.json：已知 F03 的工具回歸輸出，不是完整案件重跑。

- presentation/gen2-code-checks-desktop.png：程式檢查與待案件重跑比較的桌面截圖。
