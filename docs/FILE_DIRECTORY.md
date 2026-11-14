# 檔案目錄

目前可執行內容為 web/ 的 Layer 1 首頁；其他區域為文件、模板或預留目錄。
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
    completed/
    templates/
      CASE_BRIEF.md
  data/
    private/
      README.md
    public/
  docs/
    CONCEPT.md
    FILE_DIRECTORY.md
    PROGRESS.md
  experiments/
    protocols/
      PILOT.md
    results/
  organization/
    roles/
    versions/
  presentation/
    DEMO_STORY.md
    layer-one-desktop.png
  README.md
  reviews/
    templates/
      REVIEW.md
  runs/
    README.md
  src/
  tests/
  web/
    index.html
    package.json
    serve.mjs
    src/
      app.js
      styles.css
```

## 主要區域

- web/：中英文靜態首頁、樣式與僅限本機的預覽伺服器。
- organization/、capabilities/：預留角色、組織版本及候選／驗證／退役能力，尚無 Agent 實作。
- cases/、reviews/：案件與審查模板；active/、completed/ 尚無研究案件。
- experiments/：可行性試行草案；results/ 尚無結果。
- data/private/、runs/：不提交內容，僅保留說明。
- presentation/：展示草案與首頁截圖。
- src/、tests/：預留研究執行器與測試；網站程式位於 web/src/。
- .gitattributes：文字 LF 與 PNG binary 規則。

GitHub 目前為 public；Pages 發布 Layer 1 靜態首頁。

- .github/workflows/pages.yml：main 分支網站更新時檢查語法並部署 Pages。

雙版本 UI：web/src/app.js 內 matrix 為標記清楚的虛構示意資料；data-matrix 開啟證據結構預覽，不代表已執行測試。版本設計詳 docs/CONCEPT.md。

第一輪範圍以 docs/CONCEPT.md、experiments/protocols/PILOT.md 為準；首頁版本矩陣為展示概念，非執行器功能。

- presentation/version-matrix-desktop.png：雙版本區塊的本機視覺檢查截圖（虛構矩陣）。
