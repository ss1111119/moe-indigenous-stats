# 大專原住民學生統計 — 可機器讀取版

教育部把大專原住民學生的**學門／科系**統計鎖在 PDF 與 Excel 出版品裡，
互動圖表又是 Tableau Public 嵌入、抓不到底層資料。
這個專案把那些出版品解析出來，接上開放資料的全體學生數，
產出可以直接分析的 CSV，以及一份對照報告。

📊 **報告頁：`https://ss1111119.github.io/moe-indigenous-stats/`**

- **106–114 學年**，27 個學門、169 個細學類
- 原住民學生 vs 一般生的**結構差異**與**逐年增減趨勢**
- 每個數字都標明口徑，不可比的部分明確標記

## ⚠️ 用之前先看這三件事

這些是資料本身的問題，不是程式的 bug。直接拿數字去用會出錯。

| 問題 | 影響 | 已如何處理 |
|---|---|---|
| **109 學年分母缺漏** | `sdata` 該年少了 53,407 人（4.4%）。護理科從 30,063 掉到 1,886，隔年回到 29,975。拿各年總數對校別檔，其餘八年**完全相等**，只有 109 對不上 | 逐個細學類比對 108／110 內插值，**10 類**明顯偏低（護理及助產、藥學、醫學、一般法律、公共關係、視覺藝術等）已在 `trend_major.csv` 留白；全國層級用 `分母完整度` 欄標示。**該年占比一律偏高，勿引用** |
| **`999 其他學門` 不可比** | 分子（出版品）含空大及進修學校、宗教研修學院，分母（`sdata`）只有 140 所大專校院。無科系可歸的學生全堆進 999，使該欄原民數約為全體的 1/3，而整體水準只有 2% | `可比` 欄標成 `False`，並排除在結構占比的分母外 |
| **106 以前接不上** | `sdata` 103–105 用學科標準分類**第 4 次修正**的 6 碼代碼，106 起改**第 5 次修正**的 8 碼 | 學門／科系分析一律從 106 學年起算 |

還有一個環境問題：**`stats.moe.gov.tw` 的憑證缺 Subject Key Identifier**，
新版 OpenSSL 會拒絕連線，所以 `fetch.py` 關掉了憑證驗證（等同 `curl -k`）。
抓的是公開統計檔，風險僅止於內容可能遭中間人竄改——但這是繞過，不是修好。

## 快速開始

```bash
pip install -r requirements.txt

python fetch.py                # 開放資料（約 46MB）
python fetch.py ebooks sdata   # 出版品 xls/xlsx + 各校科系別概況（約 25MB）

python build.py                # 校別／年級層級
python build_field.py          # 學門與細學類層級
python build_trend.py          # 逐年指數序列
python export_report.py        # 報告頁 → docs/index.html
```

`out/` 的 CSV 已經放進版控，**不跑 pipeline 也能直接用**。
`data/`（原始檔 71MB）沒有進版控，`fetch.py` 可完整重建。

## 輸出

| 檔案 | 粒度 |
|---|---|
| `out/compare_field.csv` | 學年度 × **27 學門** × 6 等級：原民／一般生人數、結構占比、相對倍數 |
| `out/compare_major.csv` | 同上，**169 個細學類** |
| `out/growth_field.csv`／`growth_major.csv` | 106→114 的人數成長、占比變化、相對倍數變化 |
| `out/trend_major.csv` | 逐年指數（106 學年＝100），兩群人可畫在同一張圖上比走勢 |
| `out/compare_by_school.csv` | 學年度 × **學校** × 等級別（104–113） |
| `out/compare_national.csv` | 學年度 × 等級別，全國彙總 |
| `out/compare_grade.csv` | 學年度 × 等級別 × 年級（含延修生） |

**「一般生」＝全體學生 − 原住民學生**，與教育部提要分析口徑一致。
註：原民端含空大／宗教研修學院、全體端不含，相減會多扣約 0.14% 的全體人數。

## 資料從哪來

### 分子：原住民學生

opendata 只有等級別與校別，**學門／科系只存在於出版品**：

```
https://stats.moe.gov.tw/files/ebook/indigenous/<學年>/<學年>indigenous.xlsx
```

106–108 是舊版 `.xls`，109 起 `.xlsx`。sheet 名穩定：`A1-3`＝學門、`A1-4`＝細學類與科系名稱。

opendata 的部分（`fetch.py` 的 key）：

| key | 檔名 | 內容 | 學年度 |
|---|---|---|---|
| `A1-1` | `indigenous_students_A1-1` | 按**校別**分（含學校代碼） | 104–113 |
| `A2-3` | `indigenous_students_A2-3` | 按年級別、等級別、性別分 | 104–114 |
| `A_1_7` | `edu_A_1_7` | 各級學校原住民學生概況—按設立別 | 104–114 |

### 分母：全體學生

| key | 檔名 | 內容 | 學年度 |
|---|---|---|---|
| `sdata` | `sdata` | 各校**科系別**概況（118,000 筆） | 103–114 |
| `student` | `student` | 校別學生數—當學年度 | 113–114 |
| `student_hist` | `103-112_student` | 校別學生數—歷年 | 103–112 |
| `graduate` | `graduate` | 校別畢業生人數 | 103–114 |

網址格式：`https://stats.moe.gov.tw/files/opendata/<檔名>.<json|csv>`
欄位名是中文 key、值一律是字串（含 `"-"` 之類的缺值符號）。

### 代碼怎麼接

`sdata` 的 8 碼科系代碼 ＝ 細學類(5) ＋ 序號(3)。

- **前 3 碼**去前導零 → `A1-3` 的學門代碼，兩邊都是 27 類、完全對應
- **前 5 碼** → `A1-4` 的細學類代碼

## 為什麼不直接抓那張互動圖表

[大專校院原住民學生數—主題式互動統計圖表](https://stats.moe.gov.tw/statedu/chart.aspx?pvalue=43)
是 ASP.NET 外殼嵌 Tableau Public。實測過的路全部走不通：

| 方式 | 結果 |
|---|---|
| `/views/{wb}/{sheet}.csv` | 404。只有 `Dashboard1` 是已發布 view，dashboard 本身不支援 csv 匯出 |
| `.twb` / `download/twbx` | 404，作者關閉下載 |
| `bootstrapSession` API | 頁面 `tsConfigContainer` 是空的，取不到 sessionid，得真跑瀏覽器 |

唯一能直接打的是工作表清單（純 metadata、無資料）：
`https://public.tableau.com/profile/api/workbook/20260521_17793481452890`

## 其他口徑注意事項

- **分母含境外生**：全體學生數包含僑生、外國生、陸生，所以占比是「占全體在學生」而非「占本國生」，會略微低估。
- **二專在 109 學年有口徑斷點**（`compare_national.csv` 的「口徑註記」欄已標）。109 學年起「○○科技大學附設進修專校」不再是獨立學校，學生改列母校進修部：
  - 學校名錄「空大及大專附設進修學校」108 學年 91 校 → 109 學年 28 校，消失的 63 校裡 40 校是附進修專校
  - 全體二專分母同時 4,784 → 12,144；原民端則是類別間搬家（大專校院 356→599、空大及進修學校 605→336，合計 961→935 持平）
  - 分子分母跳增幅度不同，占比從 7.44% 假性掉到 4.93%。**108 以前與 109 以後不可直接比較**，且分母端無法回補
- **空大與宗教研修學院沒有分母**：`compare_by_school.csv` 有 411 列有原民生卻對不到全體數，全國彙總已排除。
- **博碩士的「延修生」不可比**：全體檔那兩欄一律為 0（研究生不用該欄表示），原民檔卻有值。`compare_grade.csv` 已濾掉分母為 0 的列。
- **`A1-1` 只到 113 學年**，`A2-3` 到 114；校別分析上限是 113。
- **族籍別**在出版品 `A1-2`，本專案尚未解析。

### 併表時做的正規化

- **學校代碼**：當年度 `student.json` 沒補零（`"1"`），歷年檔與原民檔是 `"0001"` — 一律 zfill(4)
- **等級別**：全體檔用代碼前綴（`D/M/B/C/2/5/X`），`B 學士`、`B 四技`、`C 二技`、`C 二年制`、`X 4+X` 全歸「學士班」，`5 五專`、`5 七年` 歸「五專」
- **`A2-3` 的等級別用詞逐年變動**（`大學四年制`／`大學四年制(或四技)`／`學士班`／`二技`／`4+X`），另做對照表收斂
- **日間∕進修別**：原民檔不分，全體檔加總後再比

## 查證用的來源

```
https://stats.moe.gov.tw/files/school/<學年度>/u2_new.csv   # 空大及大專附設進修學校名錄
https://data.gov.tw/api/v2/rest/dataset/33513               # A1-1、A2-3
https://data.gov.tw/api/v2/rest/dataset/40117               # A_1_7
https://data.gov.tw/api/v2/rest/dataset/6231                # student、student_hist
https://data.gov.tw/api/v2/rest/dataset/6235                # graduate
https://data.gov.tw/api/v2/rest/dataset/9621                # sdata
```

教育部統計處自己每年也發布《原住民族教育概況統計結果提要分析》，
內含粗在學率、休退學率等一般生對照，可與本專案互相驗證：
`https://stats.moe.gov.tw/files/ebook/indigenous/<學年>/<學年>indigenous_ana.pdf`

## 授權

程式碼採 MIT，見 [LICENSE](LICENSE)。

`out/` 的衍生資料集改作自教育部統計處公開統計資料，原始資料依
[政府資料開放平臺開放資料授權條款－第 1 版](https://data.gov.tw/license) 授權，
可自由使用、改作、再散布，**惟須標示資料來源為教育部統計處**。
