## 1. 彙整輸出

- [x] 1.1 交付 "Assemble one row per county from existing outputs"：`build_county.py` 從 `geography.csv`、`ladder_township.csv`、`receiving_township.csv`、`attainment_standardised.csv` 彙整出 `out/county_view.csv`，一列一個縣市共 22 列，欄位為縣市代碼、縣市、出生戶籍地、學校所在地、淨流動、就學戶籍比、有國小／國中／高中職／大專的鄉鎮數、承接鄉鎮數、承接原民生、原始專科以上占比、年齡標準化占比、小分母；不新增抓取、不讀 `data/`。驗證：輸出 22 列；spec 中 "observed counties" 的臺東與新北兩列逐一相符（16／14／4／1、20.3%、1 個鄉鎮 792 人、29.3→33.0；29／29／22／13、142.8%、13 個鄉鎮）。
- [x] 1.2 交付缺上游與縣市數不符時的行為：任一上游輸出不存在時中止，訊息指名缺哪一個檔與產生它的建置腳本；縣市數不是 22 時中止並列出實際縣市。兩者都不寫出輸出檔。驗證：暫時移走其中一個上游檔執行，確認訊息指名該檔與對應腳本。
- [x] 1.3 交付無大專校院縣市的處理：該縣市在 `receiving_township.csv` 沒有列時，承接鄉鎮數與承接原民生皆為 0 而非缺值。驗證：連江縣兩欄皆為 0 且該列存在。

## 2. 標記與一致性

- [x] 2.1 交付 "Flag counties whose ratios rest on a tiny denominator"，依決策「出生戶籍地在學數低於 200 的縣市，其比率標記為不穩定」：標記門檻 200，標記的是比率而非人數，且被標記的縣市不從資料或選單中移除。驗證：spec 中 "flagged counties at academic year 114" 的三列通過（連江 4 標記、雲林 166 標記、新竹市 215 不標記）；被標記者恰為連江、金門、澎湖、嘉義市、雲林 5 個。
- [x] 2.2 交付 "Township counts per level do not increase with level"：每個縣市的四階鄉鎮數依學制遞增方向不得上升（允許持平，如宜蘭國小 12、國中 12）。驗證：22 個縣市逐一檢查通過。
- [x] 2.3 交付 "Receiving figures agree with the township receiving output"：承接鄉鎮數等於該縣市在 `receiving_township.csv` 的列數，承接原民生等於該縣市原住民學生數合計。驗證：逐縣市比對相等。

## 3. 報告頁

- [x] 3.1 交付 "Present a county chooser as an entry point, not an appendix"，依決策「放在頁面前段當入口，而不是第 11 個附加區塊」：`export_report.py` 與 `geography_template.html` 新增縣市入口區塊，置於流動區塊之後、走勢區塊之前，可切換縣市並同時顯示該縣市的流動、四階鄉鎮數、承接與存量。驗證：重跑報告後於瀏覽器確認區塊位置在 `trend` 之前，且切換縣市時四組數字同步更新。
- [x] 3.2 依決策「只給關鍵數字與迷你階梯，不重複既有圖形」：本區塊只呈現彙整數字與一個緊湊的四階長條，不重做既有的啞鈴圖、面板圖與散布圖。驗證：檢視區塊確認沒有重複既有圖形。
- [x] 3.3 交付兩段必要說明，並依決策「不納入高中職分流，並在頁面明說」與「說明文字以 150 字為上限」：頁面明寫高中職分流沒有縣市分項、以及小分母縣市的比率已標記；該區塊 `note` 不超過 150 字。驗證：兩段文字存在；計算 `note` 純文字字數確認 ≤ 150。
- [x] 3.4 交付小分母縣市被選取時的呈現：其比率標記為不穩定，且同時看得到分母人數。驗證：選取連江縣，確認比率有標記且畫面顯示出生戶籍地為 4 人。

## 4. 測試與文件

- [x] 4.1 在 `tests/test_invariants.py` 加入 `county_view.csv` 的檢查：列數 22、承接兩欄與 `receiving_township.csv` 逐縣市相符、四階鄉鎮數不遞增、被標記的縣市恰為 5 個。驗證：`pytest` 全數通過；人工改動其中一項使對應測試失敗。
- [x] 4.2 更新 `tests/test_page_description.py` 的 `SECTIONS` 常數以納入新區塊，並確認開場白仍如實描述頁面。驗證：`pytest` 通過；把新區塊從模板移除後測試失敗。
- [x] 4.3 在 `README.md` 的快速開始與輸出表補上 `build_county.py` 與 `out/county_view.csv`，並說明縣市視角涵蓋四塊、不含分流及其理由。驗證：依 README 指令從零跑一次，輸出檔產生成功。
