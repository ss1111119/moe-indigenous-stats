## 1. 標題跟著選取的縣市

- [x] 1.1 交付 "Present a county chooser as an entry point, not an appendix" 新增的標題要求，即場景 "The heading follows the selection"：`geography_template.html` 的縣市入口區塊，其 `<h2>` 由選取的縣市決定，句型為 `<縣市> <有國小的鄉鎮數> 個鄉鎮有國小，只有 <有大專的鄉鎮數> 個有大專校院`；數字取自既有 `county` 資料的 `steps` 陣列第一與第四項，不新增資料、不改 `export_report.py`。驗證：重跑報告輸出後於瀏覽器選臺北市，標題顯示「臺北市 12 個鄉鎮有國小，只有 9 個有大專校院」。
- [x] 1.2 交付 "A county hosts no tertiary institution"：大專鄉鎮數為 0 時，句尾改為「沒有一個有大專校院」而非「只有 0 個有大專校院」。驗證：選連江縣，標題顯示「連江縣 4 個鄉鎮有國小，沒有一個有大專校院」。
- [x] 1.3 交付 "The default selection is unchanged"：預設選取仍為臺東縣，首屏標題與本變更前逐字相同。驗證：載入頁面未點選任何縣市，標題為「臺東縣 16 個鄉鎮有國小，只有 1 個有大專校院」。

## 2. 範圍與一致性

- [x] 2.1 依 Non-Goals「不改動區塊內其他任何文字」：`note`、eyebrow、legend 的文字皆不變，該區塊 `note` 仍為 72 字。驗證：以 `git diff geography_template.html` 確認改動只落在 `<h2>` 與縣市入口的繪製函式內，`note` 段落無變更。
- [x] 2.2 確認 `tests/test_page_description.py` 的區塊清單與開場白仍成立：本變更不新增也不移除區塊，`SECTIONS` 不需更動。驗證：`pytest` 全數通過且未修改該測試檔。

## 3. 輸出與文件

- [x] 3.1 重跑 `python export_report.py` 使 `docs/geography.html` 與模板同步（該檔由腳本產生，不手改）。驗證：`docs/geography.html` 內含動態標題的繪製程式碼，且 `docs/data/geography.json` 內容無變化。
- [x] 3.2 確認 `README.md` 無需更動：本變更不新增輸出檔、不新增指令、不改變任何口徑。驗證：逐項比對 README 的快速開始、輸出表與「六、縣市視角」一節，確認其敘述在本變更後仍為真；若有一項不再為真則就地更正。
