## Why

`township-level-receiving` 把大專的承接端降到鄉鎮市區，得到一個數字：全國只有
**87 個**鄉鎮市區有大專校院。但那個數字單獨看不出意義——要有比較對象才知道 87 是多是少。

SEGIS 另有三筆結構完全相同的資料（同樣的空間單元、同樣的 `NA_STU_CNT` 欄位命名）：
國民小學、國民中學、高級中等學校。四階合起來就是鄉鎮市區層級的完整就學階梯。

實測 114 學年（本提案撰寫前已取得四筆資料並驗證）：

| 階段 | 有該階學校的鄉鎮市區 | 其中有原民生的 | 原民生總數 |
| --- | ---: | ---: | ---: |
| 國小 | 367 | 363 | 52,051 |
| 國中 | 357 | 339 | 24,513 |
| 高中職 | 206 | 197 | 20,398 |
| 大專 | 87 | 86 | 25,613 |

**367 → 357 → 206 → 87。** 這回答了本專案從第一頁就在問而一直只能用推論回答的問題：
原民生為什麼離開戶籍地。不是偏好問題，是他家鄉根本沒有下一階的學校。
現有的地理頁只能呈現「離開了」這個結果，補上這條線才說得出原因的結構面。

## What Changes

- 新增一支抓取腳本，取得國小、國中、高級中等學校三筆行政區統計的鄉鎮市區資料，
  並在本機快取原始回應。三筆各一個 oCode，各自一次請求涵蓋全國。
- 既有的抓取與建置腳本改為同時處理四個學制，共用同一套欄位驗證與解析邏輯，
  不是複製三份。
- 新增階梯輸出：每個鄉鎮市區在四個學制上各有多少原民生、以及全國層級的
  「有該階學校的鄉鎮數」遞減序列。
- 「縣市」報告頁的鄉鎮區塊上方新增階梯段落，把 367 → 87 這條線放在
  既有的大專承接端之前，作為它的脈絡。
- 文件寫明跨階人數不可直接相比的理由（年級數不同），並在頁面上以鄉鎮數為主、
  人數為輔呈現。

## Non-Goals

- 不做時間序列。四筆的開放服務端點都只回傳最新一期，理由與實測依據已寫在
  `township-level-receiving` 的提案與 `fetch_segis_college.py` 的模組說明。
- 不計算跨階的「升學率」或「流失率」。四階是同一時點的橫斷面，不是同一批人的
  追蹤，相除得到的數字沒有世代意義。
- 不做族別維度。四筆都沒有族別欄位。
- 不改動流出端（出生戶籍地）的粒度，也不改動存量資料來源。
- 不把本資料當作教育部出版品的獨立交叉驗證來源——四筆的原始統計機關同為
  教育部統計處。
- 不新增第五個學制（幼兒園、進修學校、宗教研修學院等）。

## Capabilities

### New Capabilities

- `education-ladder`: 四個學制的鄉鎮市區原民生資料之取得、驗證與階梯指標計算，
  含「有該階學校的鄉鎮市區數」遞減序列，以及跨階可比性的限制標註。

### Modified Capabilities

- `admin-district-college-ingest`: 從只處理大專一個學制，改為以學制為參數處理四個
  學制；快取檔名與錯誤訊息須能指出是哪一個學制失敗。
- `township-receiving`: 報告頁的鄉鎮區塊新增階梯脈絡段落，且該段落須標明
  跨階人數不可直接相比。

## Impact

- Affected specs: education-ladder, admin-district-college-ingest, township-receiving
- Affected code:
  - New:
    - build_ladder.py
    - out/ladder_township.csv
    - out/ladder_summary.csv
  - Modified:
    - fetch_segis_college.py
    - build_receiving.py
    - export_report.py
    - geography_template.html
    - README.md
  - Removed: (none)
- 外部依賴：SEGIS 開放服務端點 GetAdminSTDataForOpenCode，免登入。三個新的 oCode
  已於 2026-08-11 取得並實測。
- 既有輸出 `out/receiving_township.csv` 與 `out/receiving_township_summary.csv`
  的欄位不變，既有頁面區塊不受影響。
