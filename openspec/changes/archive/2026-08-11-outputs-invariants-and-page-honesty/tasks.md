## 1. 不變量測試

- [x] 1.1 交付 "Assert cross-file invariants on the committed outputs"，依決策「測輸出而不是測函式」與「測試不讀 `data/`」：新增 `tests/test_invariants.py`，只讀 `out/*.csv` 與模板檔，不呼叫建置腳本的內部函式、不讀 `data/`。驗證：在無網路且未跑 pipeline 的情況下執行 `pytest`，全部通過且耗時在數秒內。
- [x] 1.2 交付 spec 中 "constrained relationships" 的三條跨檔約束：承接端合計 25,613 且等於 `geography.csv` 114 學年總計列的「學校所在地在學數_不含空大宗教」逐縣市合計；`senior_stream.csv` 114 學年五類合計 20,398 且等於 `ladder_summary.csv` 高中職列；`adult_education.csv` 合計 490,336 且等於 `attainment_by_age.csv` 合計。驗證：三條各自通過；人工改動其中一檔一位數字，對應測試失敗。
- [x] 1.3 交付 "Pin the headline figures as explicit constants"，依決策「數字寫死在測試裡，並在斷言訊息中說明它從哪來」：期望值寫成常數並各自註明來源；失敗訊息含約束名稱、期望值、實際值，以及「若為新學年資料請先確認再更新常數」的提示。驗證：人工改動一個輸出使測試失敗，檢視訊息確認四項資訊齊備。
- [x] 1.4 交付 "Assert the ladder counts descend"：斷言四個學制的鄉鎮市區數為 367／357／206／87 且嚴格遞減。驗證：測試通過；人工把其中一個值改大使序列不遞減，測試失敗。
- [x] 1.5 交付 "Assert standardisation is identity at the national level"：全國原始占比與年齡標準化占比相等至小數兩位。驗證：測試通過（實測皆 35.00%）。
- [x] 1.6 交付 "Assert row counts and share totals"：釘住 spec 中 "pinned row counts" 的五個列數（87／1017／132／55／55），並斷言各分組內占比合計為 100%（容許 0.05）。驗證：五個列數逐一相符；占比檢查涵蓋 `senior_stream`、`senior_stream_compare` 兩端與 `ladder`／`receiving` 的相關分組。
- [x] 1.7 交付 "Assert the streaming gap widened"：105 學年普通科差距 −11.56、114 學年 −13.69，且後者絕對值較大。驗證：兩個值逐一相符且方向斷言通過。

## 2. 頁面自我描述

- [x] 2.1 交付 "The page deck SHALL describe the page as it currently is" 的修正：改寫 `geography_template.html` 的開場白，使其不再宣稱「三件事」，而如實描述目前 10 個區塊涵蓋的內容。驗證：重跑報告後於瀏覽器確認開場白與頁面內容相符。
- [x] 2.2 交付 "The byline SHALL list every data source the page uses" 的修正：byline 補上當日新接的來源（行政區各級學校統計、`edu_A_1_7`、`base3`），涵蓋目前所有來源。驗證：逐一對照頁面各區塊所用來源，確認 byline 皆有提及。
- [x] 2.3 交付 `tests/test_page_description.py`，依決策「頁面自我描述以區塊數與來源關鍵字檢查，不做全文比對」：斷言開場白提到的區塊數與實際 `<section>` 數一致、byline 涵蓋所有來源關鍵字；不做全文比對。驗證：spec 中 "the state this requirement was written to correct" 的情境會失敗——人工把開場白改回「三件事」，測試失敗並列出兩個數字；人工在模板新增一個 `<section>` 而不改開場白，測試亦失敗。

## 3. 文件與相依

- [x] 3.1 在 `requirements.txt` 加入 `pytest`，並在 `README.md` 的快速開始段說明如何執行測試與它檢查什麼。驗證：依 README 指令從 clone 狀態執行測試成功。
- [x] 3.2 在 README 記錄測試的兩個設計取捨：數字寫死故資料更新時會紅（刻意，須先確認再更新常數）、以及測試只讀 `out/` 與模板不讀 `data/`（故 clone 後可立即執行）。驗證：檢視該段確認兩點齊備。
