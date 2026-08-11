## 1. 分流輸出

- [x] 1.1 交付 "Produce senior-secondary streaming shares across academic years"：`build_stream.py` 從既有 `data/edu_A_1_7.json` 產出 `out/senior_stream.csv`，一列一個學年 × 分流，欄位為學年、分流、人數、占比；分流為普通科、綜合高中、專業群(職業)科、實用技能學程、進修部；不新增任何抓取。驗證：spec 中 "expected shape" 通過——輸出 55 列（11 學年 × 5 分流）。
- [x] 1.2 交付來源缺檔與欄位缺漏時的行為：`data/edu_A_1_7.json` 不存在時中止並指示先執行 `python fetch.py`；五個高中職欄位有任一不存在時中止並列出實際欄位名稱。兩者都不寫出輸出檔。驗證：暫時改名來源檔執行確認訊息正確；再人工刪掉一個欄位執行，確認中止並列出實際欄位。
- [x] 1.3 交付 "Select one breakdown and cross-check against the others"，依決策「以設立別那一組列計算，而不是把整份加總」：只取公立與私立兩列相加，並逐學年驗證「男＋女」與「族別合計」得到相同的高中職總計；不相等即中止並列出三個數字。驗證：spec 中 "observed totals" 的兩列相符（104 與 114 皆為 24,195 與 20,398 三者相等）。
- [x] 1.4 交付 "Report shares that sum to one hundred percent"：各學年五類占比以該年五類之和為分母，加總須為 100%，否則中止。驗證：spec 中 "observed shares" 的兩列數值逐一相符（104 為 27.6／13.2／41.8／5.1／12.4，114 為 38.0／8.9／41.9／5.0／6.2）。
- [x] 1.5 交付 "Cross-check the latest year against the education ladder"，依決策「與就學階梯的高中職數字交叉檢查，但不稱之為驗證」：最新學年的總計與 `out/ladder_summary.csv` 高中職那列比對並印出結果。驗證：spec 中 "observed value" 通過——114 學年兩者皆為 20,398。

## 2. 報告頁

- [x] 2.1 交付 "Present streams as shares and disclose the absence of a comparison" 的版面部分，依決策「主軸是占比，人數僅作為背景」：`export_report.py` 與 `geography_template.html` 讓分流區塊出現在就學階梯區塊之後、鄉鎮承接端區塊之前，以占比為主要圖形、人數以文字標示於旁。驗證：重跑報告後於瀏覽器確認三個區塊的文件順序為階梯 → 分流 → 承接端，且圖形畫的是占比不是人數。
- [x] 2.2 交付兩段限制文字：頁面明寫本區沒有一般生對照、數字描述的是原民生之內的組成；並明寫不解讀總人數的變化。驗證：確認兩段文字存在；全區搜尋確認沒有任何把原民占比與全體學生相比的敘述。
- [x] 2.3 依決策「不把總人數下降納入敘事」與風險對策，確認進修部單獨標註、不與其他四類做「普通 vs 職業」二分，且綜合高中的下降未被解讀為原民生的選擇改變。驗證：檢視區塊文字確認三點皆成立。

## 3. 文件

- [x] 3.1 在 `README.md` 的輸出表與快速開始段補上 `build_stream.py` 與 `out/senior_stream.csv`，並新增一節呈現 104 與 114 的分流占比對照。驗證：依 README 指令從零跑一次，輸出檔產生成功。
- [x] 3.2 在該節記錄三個限制：本輪沒有一般生對照及其理由（專案的分母資料全是大專層級）、總人數下降不做歸因、與階梯數字相符不構成交叉驗證（同為教育部統計處）。並更正 README 中 `edu_A_1_7` 先前未被任何腳本使用的狀態描述。驗證：檢視該節確認三點齊備。
