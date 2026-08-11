## 1. 取得端點並落地原始回應

- [x] 1.1 依決策「以一次性取得的 oCode 常數存取行政區開放服務端點」，用平台查詢介面開啟《行政區大專校院統計》的資料檢視頁，從該頁 HTML 取出 JSON 版開放服務網址。已於 2026-08-11 取得並實測回傳 87 筆。實作時把 oCode 與取得日期寫成 `fetch_segis_college.py` 的常數與註解。驗證：以該 oCode 呼叫 `GetAdminSTDataForOpenCode` 得到非空回應（已完成，`OutTotal` 為 87）。
- [x] 1.4 原提案的三個 Open Question 已實測解決：年度標示為**學年**（`INFO_TIME` 為 `114Y`），一次請求即涵蓋**全國 87 個鄉鎮市區、21 縣市**不需逐縣市取數，欄位帶正式名稱不需反推順序。驗證：三項結論已寫入 design 的決策段落，實作時一併寫入 `fetch_segis_college.py` 模組說明。
- [ ] 1.2 交付 "Fetch administrative-district college statistics from SEGIS"：`fetch_segis_college.py` 首次執行時把原始回應位元組寫入 `data/segis-college/` 並印出取得筆數；已有快取且無網路時仍能成功完成且不發出任何請求。驗證：連線執行一次後斷網再執行一次，兩次都成功，第二次無網路請求。
- [ ] 1.3 交付 oCode 失效時的行為：端點拒絕請求或回應不含任何紀錄時中止，錯誤訊息指名 oCode 常數與重新取得的一次性人工步驟，且不留下會被後續執行誤認為有效的空白或半截快取檔。驗證：暫時把 oCode 常數改為無效值執行，確認中止、訊息正確、快取目錄未新增檔案。
- [ ] 1.5 依決策「範圍限於 114 學年一期，因為開放服務端點取不到歷年」，在 `fetch_segis_college.py` 模組說明寫明：oCode 不含年度、`OpenService.asmx` 三個方法皆無時間參數、16 個學年產品頁回傳同一 oCode 且資料僅 `114Y`，歷年須走需登入的 `filedown.downloadproductfile` 流程。驗證：檢視模組說明確認四項依據齊備，且未宣稱本腳本可取得歷年。

## 2. 欄位驗證與一致性比對

- [ ] 2.1 交付 "Verify the field mapping before use"：依決策「欄位對照以名稱比對確認，不靠位置順序」，把必要欄位名稱寫成常數（`INFO_TIME`、`COUNTY_ID`、`COUNTY`、`TOWN_ID`、`TOWN`、`SCH_CNT`、`STU_CNT`、`NA_STU_CNT`、`NA_STU_M_CNT`、`NA_STU_F_CNT`），一律以名稱取值；`ColumnList` 缺任一必要名稱時中止並印出缺少與實收的欄位名，不產出輸出檔；回應多出欄位時正常完成。驗證：人工在必要名稱常數中加入不存在的欄位名執行，確認中止並印出缺少項。
- [ ] 2.2 交付逐列的性別分項檢查：任一紀錄的原住民男學生數加女學生數不等於原住民學生數時中止，並指出第一筆不符紀錄的學年與鄉鎮市區。驗證：spec 中 "sex-component validation" 的三組範例值逐一通過（120/70/50 接受、120/70/49 中止並指認、0/0/0 接受）。
- [ ] 2.3 交付 "Reconcile county totals against the published statistics"：依決策「縣市加總的比對對象是 A1-6a 而非 A1-6b」，把鄉鎮加總到縣市後與 `A1-6a` 的同學年數字比對，印出逐縣市差額；差額可由範圍差異解釋時回報為一致，否則不得回報為一致。驗證：執行後檢視逐縣市差額輸出；若先比 `A1-6a` 不符則再比 `A1-6b`，兩者實測結果與差額量級都寫入模組說明。

## 3. 鄉鎮層級輸出

- [ ] 3.1 交付 "Produce township-level receiving detail"，並依決策「鄉鎮市區代碼直接採用資料自帶的行政區代碼」與「一次請求即涵蓋全國，不逐縣市取數」：`build_receiving.py` 產出 `out/receiving_township.csv`，一列一個學年 × 鄉鎮市區，欄位為學年、縣市代碼、縣市、鄉鎮市區代碼、鄉鎮市區、學校數、全體學生數、原住民學生數、原住民男學生數、原住民女學生數、原民生占比；鄉鎮市區代碼取自來源 `TOWN_ID` 而非推導。驗證：輸出為 87 列、21 個相異縣市、87 個相異鄉鎮市區；欄位順序與名稱逐一核對；抽查數個 `TOWN_ID` 可對上行政區圖資。
- [ ] 3.2 交付 "Compute indigenous share from the same row"：原民生占比為同一列的原住民學生數除以全體學生數；全體學生數為零時輸出空值而非零。驗證：spec 中 "share computation" 的三組範例值逐一通過（10000/250 得 0.025、800/0 得 0.0、0/0 得空值）。
- [ ] 3.3 交付 "Produce a county-level summary for the latest period"：產出 `out/receiving_township_summary.csv`，一列一個縣市，欄位為縣市代碼、縣市、鄉鎮數、學校數、全體學生數、原住民學生數、原民生占比，且各縣市原住民學生數等於該縣市鄉鎮列之和。驗證：以明細檔重新分組加總，逐縣市與摘要檔比對相等；列數為 21。
- [ ] 3.4 交付 "Carry the academic year from the source"：學年欄的值取自回應的 `INFO_TIME` 而非寫死，明細檔分組後恰有一個學年。驗證：確認 CSV 學年欄值為 `114Y` 所對應的學年且與回應一致；人工把快取中的 `INFO_TIME` 改成別的值重跑，確認輸出跟著改變而非仍顯示 114。
- [ ] 3.5 交付 "Fail rather than emit partial output"：缺少快取時中止，訊息指示先執行抓取步驟，且不寫出任何輸出檔；建置階段不改用線上即時取數。驗證：暫時移走快取目錄後執行，確認中止、訊息正確、輸出檔未產生或未被覆寫。

## 4. 報告頁與文件

- [ ] 4.1 交付 "Present township receiving alongside county-level flow"：`geography_template.html` 與 `export_report.py` 讓「縣市」報告頁出現鄉鎮層級承接端區塊，逐鄉鎮顯示原住民學生數與原民生占比，與既有縣市層級流動並置。驗證：重跑報告輸出後在瀏覽器開啟該頁，確認區塊可見且數值與摘要檔一致。
- [ ] 4.2 交付小分母標註、單一學年說明與範圍差異說明：全體學生數低於 1,000 人的鄉鎮，其占比在頁面上標為不穩定；頁面明寫這是單一學年的快照而非趨勢，且學年字樣由資料帶出不寫死；鄉鎮區塊的縣市加總與頁面既有縣市層級數字不同時，頁面明寫兩者範圍不同。驗證：spec 中 "stability marking at the threshold" 的三組範例通過（999 標註、1000 不標註、12000 不標註）；確認單一學年與範圍差異兩段說明文字存在於頁面。
- [ ] 4.3 交付 "Record provenance and non-independence"：`fetch_segis_college.py` 模組說明與 `README.md` 明寫本資料原始機關即教育部統計處、與既有出版品同源，並把價值定位在鄉鎮市區粒度；任何文件都不得把與出版品的比對稱為獨立來源的交叉驗證，也不得宣稱涵蓋多個年度。驗證：檢視兩處文字確認同源敘述存在；全庫搜尋「交叉驗證」確認無把本資料描述為獨立驗證的句子。
