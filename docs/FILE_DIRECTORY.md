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
    check_f03_v2.py
    package_f03_v2.py
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
      f03-gen2-workflow.json
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
      proposal-v2.js
      app.js
      styles.css
```

## 主要區域

- web/：中英文靜態首頁、樣式與僅限本機的預覽伺服器。
- organization/、capabilities/：已加入角色契約與世代紀錄（非獨立 Agent 部署）；候選／驗證／退役能力目錄仍預留。
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

## F03 v2 與重跑新增
- scripts/package_f03_v2.py：從已完成合成 run 整理公開最終交付；不複製原始角色 JSON、事件或聊天，不覆寫既存包。
- scripts/check_f03_v2.py：固定 manifest／檔案完整性、同一輸入與計算一致性檢查。
- web/evidence/f03/v2/：brief.md、proposal.md、review-brief.md、comparison.md、f03-costs.csv、calculation.json、publication.json、manifest.json。
- web/evidence/f03-gen2-workflow.json：本輪六步交付公開白名單摘要。
- web/src/proposal-v2.js：v1／v2 切換與整理版 v2 內容呈現。
- runs/f03-gen2-20261115-01/：原始執行與交付，只在本機、Git 忽略。

- presentation/f03-v2-desktop.png：方案 v2、版本切換及新成本拆分的桌面截圖。


## 固定方法重用與邊界檢查
- web/evidence/method-probe/：事前 protocol.md、三個合成 CSV、一般／定義衝突 metadata、expectations.json、整理結果 results.md／results.json；不是原始角色執行紀錄或未見案件。
- scripts/check_method_probe.py：固定兩代方法與來源指紋，重算三題並核對公開結果；未檢出的語意缺口保留為觀察，重現成功不表示缺口解決。
- web/src/evolution.js：沿用現有重跑比較區塊，顯示三列表與證據連結。
- .github/workflows/pages.yml：發布前加入上述結果重現檢查。
- web/src/app.js：等案件內容載入後恢復頁內直達位置。
- presentation/method-probe-desktop.png：三個公開合成情境的結果桌面截圖。


## v2 複審收斂與方案 v3
- web/evidence/f03/review-v2/review.md、response.md：外部審查結構化摘要與作者逐項回應，兩者分開。
- web/evidence/f03/source-attribution.json：追溯方法版本／指紋的補充證據；不改固定 v2 或公開原始 run。
- web/evidence/method-probe/revision-1.md、revision-1.json：等價對應、確定性數值性質與解讀修訂；保留原結果。
- web/evidence/f03/v3/：proposal.md、publication.json、changes.md、review-brief.md、manifest.json；方案修訂，不是新 run。
- organization/versions/GEN3_CANDIDATE.md：三層證據與決策閘門的候選設計，未實作。
- scripts/package_f03_revision.py：一次性建立補充指紋、校正結果與 v3 清單，拒絕覆寫輸出。
- scripts/check_f03_revision.py：固定 v3／補充數值與來源連續性檢查。
- web/src/proposal-v3.js、revision.js：沿用既有案件頁呈現 v3 及審查回應；app／case／proposal-v2／evolution／cases 同步版本與狀態。
- presentation/f03-v3-desktop.png：方案 v3 桌面驗證截圖。


## Gen 3 結構化閘門實作
- src/gen3_policy.py：原題／主張覆蓋、可比性與引用文字解析、L0–L3 聚合；不驗真來源或自然語言因果。
- src/gen3_workflow.py、organization/roles/gen3.json、cases/active/f03-gen3.json：獨立半自動 runner 與契約，保留 Gen 2。
- tests/test_gen3.py：敵意輸入、合成流程及數值邊界測試。
- docs/GEN3_IMPLEMENTATION.md：操作、已實作與不支援範圍。
- scripts/check_gen3.py、web/evidence/gen3/metadata-clean.json、development-results.json：公開合成開發情境與正規化指紋重現。
- web/evidence/f03/review-v3/review-and-response.md：設計複審摘要與回應，非逐字全文或實作驗收。
- web/evidence/f03/source-line-endings.md：歷史交接器 LF／CRLF 指紋說明。
- web/evidence/f03/v3-supplement-1.md：保留固定 v3 的小修補充。
- presentation/gen3-gate-desktop.png：已實作狀態與限制的桌面檢查截圖。
