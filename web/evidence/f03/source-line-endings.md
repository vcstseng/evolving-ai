# Gen 2 交接器的來源指紋差異

2026-11-15。補充 source-attribution.json，不覆寫既有證據。

- 正規化 LF 的 SHA-256：`b491462f8678710575622765fd5c4b6b5f723e861384bbe529cc2e6587c343e9`。
- 相同內容以 CRLF 編碼的 SHA-256：`6901fe4709929a6b88b6ccd65a8671b5a9267fbec93d5b9dfc023d0cb7f5f6ac`。
- 後者等於原欄位 author_checked_local_run_source_sha256；前者等於兩個 Git 歷史 blob 的 sha256_lf。差異僅為行尾位元組。原欄位沒有寫明 raw bytes，造成可避免的歧義。

`scripts/check_gen3.py` 從保留的 Gen 2 交接器讀取正規化文字，再轉成 CRLF 重算，並對照兩個已公開指紋。development-results.json 亦記錄結果，可在 Windows／Linux 重現。Gen 3 從這份相同正規化內容分出獨立程式，再加入閘門。

這可以核對來源文字與位元組格式，不足以獨立證明原 run 實際如何執行；原始角色交付與事件仍未公開。
