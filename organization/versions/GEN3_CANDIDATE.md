# Gen 3 候選｜把資料可用、可比與決策充分性分開

日期：2026-11-15。狀態：設計完成，未實作、未執行、未驗證。唯一主要改變：CD 的證據判斷契約；保留 Gen 2 計算，不新增角色或模型調度。

來源：F03 v2 外部複審 F1、method-probe 定義衝突及作者回應。這是外部回饋驅動的設計，不是 CD 自主創造。

## 三層判斷
1. **可用性 availability**：所需欄位、日期、定義及引用是否存在／格式有效。provided / missing / invalid；提供了不代表真實。
2. **可比性 comparability**：針對本次計算及主張所用的期間、units、hours_per_unit、hourly_rate、material_price、material_per_unit、overhead_per_unit，逐項 yes / no / unknown / not_applicable。not_applicable 必須說明為何不影響該主張，不可用來跳過矛盾。
3. **決策充分性 decision sufficiency**：證據能支持哪類交付：算術展示、附條件分析、補資料建議、因果／效率判斷、現場試點。前一類可交付不代表後一類被批准。

每個可比性項目至少記 field、status、baseline_definition、actual_definition、source_refs、source_owner_or_unknown、verification（declared / inspected / independently_verified）、reason、affected_claim_ids、resolution。缺欄位／引用，或只有無依據的 yes，降為 unknown。引用文字本身不等於驗真；記錄誰主張、誰核對與仍未知部分。

來源內容有衝突時，存在檢查不得覆蓋比較結果。成本模型是否含固定費用、需求是否支持產量，亦須依受影響主張列限制；不硬套成每題都必填的會計清單。

## no_gap 的限定含義
沿用決策代碼，但含義限於「對目前明確列出的交付與主張，沒有未解的重大缺口」，不是無所不知、Claude 通過、來源真實或企業授權。

- CD 必須列 requested_decision、claim_ids、comparability 判斷、supporting_refs、unresolved_issues、permitted_claims、blocked_claims、release_status、review_status。
- 任何支撐該主張的 no / unknown，或矛盾引用，不能對該主張選 no_gap；轉 request_evidence、conditional_delivery 或 stop。conditional_delivery 是候選新增交付狀態，尚未加入 Gen 2 決策碼。
- 成本欄位可計算但定義未知時，可交付「按提供數值算出的條件式差異」與補資料方案，不可稱真實效率／率差或根因。若原問題要求這些判斷，必須明示未完整回答，不能用縮小題目來通過。
- 只詢問下一步如何補資料的案件，可交付有界調查建議，但仍保留已知證據缺口；不得為了 no_gap 清空它。
- 試點及重大承諾需要另外的預算、量測、品質／安全／交期限制與人類授權。外部審查狀態獨立於 no_gap，不能由它改成通過。
- 缺口影響以受影響的決策／主張判定；不只看金額，大金額門檻若需要須在案例規則事先定義。不得臨時挑百分比放行。

## 未實作前的例子與預期
| 輸入 | 預期判斷 |
|---|---|
| 時薪基本工資 vs 含福利成本，其他宣告完整 | availability 可完整；rate comparability=no；真實率差與節省主張 blocked；可提供機械計算及補資料方案，不能 no_gap。 |
| 來源宣稱定義相同但沒有引用 | unknown，不能僅靠 yes 放行。 |
| 可核對定義一致、來源明確、題目只求算術且沒有矛盾 | 該算術交付可選 scoped no_gap；仍不是企業成效或來源全面驗真。 |
| 期間不同且未提供正規化依據 | 原 Gen 2 已能發現期間差異；保留此警示，不將其當新遠遷移成果。 |
| 矛盾只影響未採用的主張 | 記錄 why not applicable，限制可說內容；不得隱藏與所求決策有關的缺口。 |

## 後續實作與驗證才可宣稱的事
先實作獨立契約／閘門、測 no/unknown 被阻擋及乾淨案例不誤擋，再固定版本。由隔離的出題者準備未參與修改的案例與答案；已公開 probe 不可冒充未見。先寫同工具／資料／模型／預算與判讀規則，再決定普通 Agent／Gen 2／Gen 3 的小型對照規模。這輪未啟動任何對照。
