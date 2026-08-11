## 1. 三個新學制的取數

- [x] 1.1 依決策「以學制為參數重構既有腳本，而不是複製三份」，把 `fetch_segis_college.py` 改為由單一學制清單驅動，每個學制一組（代碼、名稱、oCode、快取檔名、年級數），四個學制共用同一套取數與中止邏輯。三個新 oCode 已於 2026-08-11 取得並實測。驗證：執行後 `data/segis-college/` 出現四個快取檔，檔名各自標明學制；程式中沒有任何為單一學制重複撰寫的取數區塊。
- [x] 1.2 交付 "Fetch administrative-district college statistics from SEGIS" 的四學制版本：首次執行時逐學制寫入快取並印出學制與筆數；四個快取都存在且無網路時仍成功完成且不發出任何請求。驗證：連線執行一次後斷網再執行一次，兩次都成功、第二次無網路請求。
- [x] 1.3 交付單一學制失敗時的行為：任一學制的端點拒絕或回應不含紀錄時中止，錯誤訊息指名**是哪一個學制**與其 oCode 常數，且不留下空白或半截快取；不得只用其餘學制產出殘缺的階梯。驗證：把國中的 oCode 改為無效值執行，確認訊息指名國中、快取未新增、無任何輸出檔產生。

## 2. 共用驗證

- [x] 2.1 交付 "Verify the field mapping before use" 的四學制版本：必要欄位名稱常數與以名稱取值的邏輯抽成共用函式，四個學制共用；任一學制缺必要欄位時中止並指名該學制、印出缺少與實收欄位。驗證：人工移除國小快取中的 `NA_STU_CNT` 欄位定義後執行，確認訊息指名國小且無輸出檔。
- [x] 2.2 交付四學制的逐列性別分項檢查：任一學制任一紀錄的原住民男加女不等於總計時中止，並指出學制、學年與鄉鎮市區。驗證：人工把高中職某列的女學生數減 1，確認訊息同時指出學制與該鄉鎮。
- [x] 2.3 交付 "Require a single shared academic year across levels"：四個學制的學年不一致時中止，列出各學制的期別，不產出任何輸出檔。驗證：人工把國中快取的 `INFO_TIME` 改成 `113Y` 執行，確認中止並列出四個學制各自的學年。

## 3. 階梯輸出

- [x] 3.1 交付 "Produce the education-ladder detail across four levels"：`build_ladder.py` 產出 `out/ladder_township.csv`，一列一個學制 × 鄉鎮市區，欄位為學年、學制、年級數、縣市代碼、縣市、鄉鎮市區代碼、鄉鎮市區、學校數、全體學生數、原住民學生數、原住民男學生數、原住民女學生數。驗證：四個學制皆有列；大專的列數等於既有 `out/receiving_township.csv` 的列數（87）。
- [x] 3.2 交付 "Carry the number of school years to block invalid comparison"，依決策「跨階不可比的警語寫進資料本身，不只寫在頁面」：年級數欄在國小、國中、高中職、大專分別為 6、3、3、空值。驗證：spec 中 "school years by level" 的四組值逐一核對。
- [x] 3.3 交付 "Produce the ladder summary as a descending township count"：產出 `out/ladder_summary.csv`，一列一個學制、由下而上排序，欄位為學年、學制、年級數、有該階學校的鄉鎮市區數、有原民生的鄉鎮市區數、涵蓋縣市數、原住民學生總數。驗證：spec 中 "observed ladder for academic year 114" 的四列數值逐一相符（367／357／206／87 與 52,051／24,513／20,398／25,613）。
- [x] 3.4 依決策「主要指標是「鄉鎮市區數」而不是人數」，確認鄉鎮市區數序列遞減，且大專列的原住民學生總數與既有 `out/receiving_township_summary.csv` 的加總一致。驗證：程式印出遞減序列；大專總數為 25,613，與既有輸出及 A1-6a 相符。
- [x] 3.5 交付缺少快取時的行為：任一學制快取不存在時中止，訊息指示先執行抓取步驟並指名缺哪一個學制，不寫出任何輸出檔。驗證：移走高中職快取後執行，確認中止、訊息指名高中職、輸出檔未產生或未被覆寫。

## 4. 報告頁與文件

- [x] 4.1 交付 "Present the ladder without inviting cross-level division" 與 "Present township receiving alongside county-level flow" 的順序調整，依決策「階梯段落放在鄉鎮承接端之前」：`geography_template.html` 與 `export_report.py` 讓階梯段落出現在鄉鎮承接端段落**之前**，以鄉鎮市區數為主要圖形、人數為次要資訊。驗證：重跑報告後於瀏覽器檢查兩段落的文件順序；階梯段落顯示 367／357／206／87。
- [x] 4.2 交付兩段警語：頁面明寫四階是同一時點的橫斷面而非同一批人的追蹤，且各階年級數不同故人數不可跨階相比。驗證：確認兩段文字存在於階梯段落；全頁搜尋確認沒有任何由兩個學制相除得到的百分比或比值。
- [x] 4.3 交付 "Record provenance and non-independence" 的四學制版本：`fetch_segis_college.py` 模組說明與 `README.md` 明寫四筆的原始機關同為教育部統計處，四階彼此一致不構成交叉驗證，價值在鄉鎮市區粒度。驗證：檢視兩處文字；全庫搜尋「交叉驗證」確認無把這四筆描述為獨立驗證的句子。
- [x] 4.4 在 `README.md` 的輸出表與快速開始段補上 `build_ladder.py` 與兩個新輸出檔，並新增一節說明階梯的四個限制（單一期別、橫斷面非追蹤、年級數不同、無族別）。驗證：依 README 的指令順序從零跑一次 pipeline，四個學制的快取與兩個輸出檔都產生成功。
