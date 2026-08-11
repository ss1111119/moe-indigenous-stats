"""原民生的地理流動：出生戶籍地 → 學校所在地，104–114 學年。

回答「哪些縣市的原民生離開、哪些縣市在承接」。

資料來自統計出版品的三張表（opendata 沒有這個維度）：

| sheet | 內容 | 範圍 |
| --- | --- | --- |
| `A1-5` | 按等級別與**出生戶籍地**分 | 含宗教研修學院、空大及大專進修學校 |
| `A1-6b` | 按等級別與**學校所在地**分 | 同上 |
| `A1-6a` | 按等級別與學校所在地分 | **不含**宗教研修、空大進修學校 |

★ **`A1-5` 與 `A1-6b` 是同一個母體**——11 個學年的總計兩兩相等（本腳本會驗），
所以「出生戶籍地人數 − 學校所在地人數」是精確的淨流動，不是兩份資料硬湊。

`A1-6a` 範圍不同（總計較少約 1,700 人），**不可拿去跟 A1-5 相減**，
本腳本只把它當參考欄輸出，不參與任何運算。

⚠️ 三件事：

1. **沒有一般生對照。** 全體學生的開放資料沒有出生地，`sdata` 也沒有；
   本專案其他維度都有的「原民 vs 一般生」在這裡做不出來。這裡的數字只能自己跟自己比。
2. **表頭與總計列的位置逐年會動**（`A1-5` 的總計列 104–108 在第 5 列、109 起在第 6 列；
   `A1-6b` 的表頭列 110 學年是第 4 列、其餘年是第 5 列）。一律**依內容定位**，
   不可寫死列號。
3. **這兩張表沒有 109 學年的二專斷點。** 因為範圍含空大及進修學校，
   109 學年那次「附設進修專校併回母校」的類別間搬家在總數上互相抵銷
   （二專全國 961 → 935 → 1010，平滑）。README 對其他維度標註的二專警語，
   **不適用於這裡**。

輸出 out/geography.csv。
"""

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
EBOOK = ROOT / "data" / "ebook"
OUT = ROOT / "out"

if hasattr(sys.stdout, "reconfigure"):  # 驗證失敗的訊息含中文，要在最前面設好
    sys.stdout.reconfigure(encoding="utf-8")

YEARS = range(104, 115)
LEVELS = ["總計", "博士班", "碩士班", "學士班", "二專", "五專"]
# ⚠️ 同一列表頭，在學欄寫「博士班」、畢業欄寫「博士」，不對稱。左右兩半不能共用同一份清單。
GRAD_LEVELS = ["總計", "博士", "碩士", "學士", "二專", "五專"]
# 22 縣市；「臺灣地區」「金馬地區」是小計列，另外處理
SUBTOTALS = {"臺灣地區", "金馬地區"}


def clean(text: str) -> str:
    """去掉全形空白、英文名與標點，只留中文地區名。"""
    s = unicodedata.normalize("NFKC", str(text))
    s = re.sub(r"[A-Za-z&\.]+", "", s)
    return re.sub(r"[\s　]+", "", s)


def read_sheet(year: int, sheet: str) -> pd.DataFrame:
    """讀一張表，回傳 index=地區、columns=(在學|畢業) × 等級別。

    表頭列與總計列的位置逐年會動，兩者都依內容定位。
    """
    path = EBOOK / f"{year}indigenous.{'xls' if year <= 108 else 'xlsx'}"
    raw = pd.read_excel(path, sheet_name=sheet, header=None)

    header = next(i for i, v in raw[1].items() if str(v).strip() == "總計")
    grand = next(i for i, v in raw[0].items()
                 if isinstance(v, str) and v.startswith("總"))

    cols = [clean(v) for v in raw.iloc[header, 1:13]]
    if cols != LEVELS + GRAD_LEVELS:
        raise SystemExit(f"{year} {sheet}：表頭不是預期的 12 欄，讀到 {cols}")

    records = {}
    for i, label in raw[0].items():
        if not isinstance(label, str) or i < grand:
            continue
        if label.startswith(("說明", "註", "資料")):
            continue
        name = "總計" if i == grand else clean(label)
        values = pd.to_numeric(raw.iloc[i, 1:13], errors="coerce").fillna(0)
        records[name] = values.astype(int).to_list()

    df = pd.DataFrame.from_dict(
        records, orient="index",
        columns=[f"在學_{lv}" for lv in LEVELS] + [f"畢業_{lv}" for lv in LEVELS])

    # 各縣市 + 兩個地區小計必須加回總計。這條擋的是「漏讀一列」——
    # 漏一個縣市不會報錯，只會讓那個縣市從地圖上消失。
    counties = df.drop(index=["總計"] + sorted(SUBTOTALS))
    if int(counties["在學_總計"].sum()) != int(df.loc["總計", "在學_總計"]):
        raise SystemExit(
            f"{year} {sheet}：22 縣市加總 {counties['在學_總計'].sum()} "
            f"≠ 總計 {df.loc['總計', '在學_總計']}")
    if len(counties) != 22:
        raise SystemExit(f"{year} {sheet}：讀到 {len(counties)} 個縣市，應為 22")
    return df


def build() -> pd.DataFrame:
    rows = []
    for year in YEARS:
        birth = read_sheet(year, "A1-5")
        school = read_sheet(year, "A1-6b")
        school_narrow = read_sheet(year, "A1-6a")

        # A1-5 與 A1-6b 必須是同一個母體，否則相減沒有意義。
        # 逐等級別檢查，不是只看總計——總計相同但等級別分布不同也不能相減。
        for lv in LEVELS:
            a, b = birth.loc["總計", f"在學_{lv}"], school.loc["總計", f"在學_{lv}"]
            if a != b:
                raise SystemExit(
                    f"{year}：A1-5 與 A1-6b 的「{lv}」總計不符（{a} vs {b}），"
                    "兩表母體不同，不可相減")

        for county in birth.index:
            if county == "總計" or county in SUBTOTALS:
                continue
            for lv in LEVELS:
                out_n = int(birth.loc[county, f"在學_{lv}"])
                in_n = int(school.loc[county, f"在學_{lv}"])
                rows.append({
                    "學年度": year, "縣市": county, "等級別": lv,
                    "出生戶籍地在學數": out_n,
                    "學校所在地在學數": in_n,
                    "學校所在地在學數_不含空大宗教":
                        int(school_narrow.loc[county, f"在學_{lv}"]),
                    "淨流動": in_n - out_n,
                    # ⚠️ 不要叫它「留存率」。淨流入的縣市會超過 100%
                    # （臺北市 412%），那不是留存，是承接。<100% 才讀得成留存率。
                    "就學戶籍比": round(in_n / out_n * 100, 2) if out_n else None,
                    "出生戶籍地畢業數": int(birth.loc[county, f"畢業_{lv}"]),
                    "學校所在地畢業數": int(school.loc[county, f"畢業_{lv}"]),
                })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(exist_ok=True)

    df = build()
    df.to_csv(OUT / "geography.csv", index=False, encoding="utf-8-sig")
    years = sorted(df["學年度"].unique())
    print(f"geography.csv  {len(df):,} 列，{years[0]}–{years[-1]} 學年 × "
          f"{df['縣市'].nunique()} 縣市 × {df['等級別'].nunique()} 等級別")

    last = years[-1]
    cur = df[(df["學年度"] == last) & (df["等級別"] == "總計")]
    cur = cur.sort_values("淨流動")
    cols = ["縣市", "出生戶籍地在學數", "學校所在地在學數", "淨流動", "就學戶籍比"]
    print(f"\n{last} 學年 淨流動（負＝原民生離開該縣市就學）")
    print(cur[cols].to_string(index=False))


if __name__ == "__main__":
    main()
