"""原住民成年人口的教育程度結構，按縣市。

本專案其餘部分算的都是「在學的原民生」；這支算的是**存量**——已經在社會上的
原住民受過多少教育。兩者合起來才看得出高教管道的效果：某縣的原民生大量外流，
在成年人口的學歷結構上會留下痕跡。

資料：內政部統計處《統計區原住民 15 歲以上人口十歲年齡組與性別與教育程度人口統計》
（SEGIS，民國 113 年 12 月底），由 fetch_segis.py 抓下 22 個縣市檔。

⚠️ 四件事在用之前要知道：

1. **基準日是 113 年 12 月底，不是學年度。** 不可以跟教育部的學年度資料畫在同一條
   時間軸上。這是人口普查口徑的存量，教育部那邊是學年度的在學人數。
2. **本腳本只做到縣市層級——這是選擇，不是資料的限制。**
   我們取的「統計區」版，空間單元只有發布區，代碼長成 `A1501-24`：
   `A` ＋ 縣市序號 ＋ 2 碼鄉鎮序號。縣市可以還原（`A15` → 10015 花蓮縣，見各檔的
   `Info.InCountyId`），但那 2 碼是 SEGIS 內部序號、不是 8 碼行政區代碼，
   接不回鄉鎮市區，所以這個版本只到縣市。

   ⚠️ **【2026-08-11 更正】本段原本寫「只能到縣市層級」，那是錯的。**
   同一份統計另有「**行政區**」版，空間統計單元直接是縣市／鄉鎮市區／村里，
   不必任何對照表。要下鑽就換那個版本抓，不要來這裡想辦法還原代碼。
   代價是行政區版最新只到 112 年 12 月，本版有到 114 年 12 月。
   （查證方式：平台的《產品總目錄》STATCatalog.xlsx，兩個版本並列在同一類別下。）
3. **教育程度是「原住民」整體，沒有分族別、沒有分平地／山地。**
4. **只取一期，但它有時間序列**——97 年 12 月起、多數年份一年兩期（06、12 月）。

輸出 out/adult_education.csv（長格式明細）與 out/adult_education_summary.csv（縣市摘要）。
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
SEGIS = ROOT / "data" / "segis"
OUT = ROOT / "out"

AGES = {
    "A15A24": "15-24歲", "A25A34": "25-34歲", "A35A44": "35-44歲",
    "A45A54": "45-54歲", "A55A64": "55-64歲", "A65UP": "65歲以上",
}
# 由高到低排列，前端與摘要都依這個順序
EDU = {
    "E1314": "博士", "E1112": "碩士", "E2122": "大學院校", "E3_4_5": "專科",
    "E6_7": "高中職", "E8_9": "國中初職", "E1_2": "小學",
    "E03": "自修", "E04": "不識字", "E99": "未詳",
}
SEXES = {"M": "男", "F": "女"}

CELL = re.compile(r"^(A\d+A\d+|A65UP)_([MF])_(E\S+)_CNT$")

# 全國 15 歲以上原住民人口的合理區間。113 年底原住民總人口約 61.2 萬
# （內政部〈115 年第 8 週內政統計通報〉：114 年底 62.9 萬、年增 2.9%），
# 15 歲以上約占 84%，即 51 萬上下。落在區間外表示抓漏了縣市或單位讀錯。
NATIONAL_RANGE = (480_000, 560_000)


def read_one(path: Path) -> tuple[dict, list[dict]]:
    """讀一個縣市檔，回傳 (Info, 資料列)。

    ⚠️ data.gov.tw 把 44 個 distribution 全部宣告為 XML，實際上至少
    「新北市_一級發布區」回傳 JSON。宣告格式不可信，一律嗅探首個非空白位元組。
    """
    raw = path.read_bytes().lstrip()
    if raw[:1] == b"{":
        doc = json.loads(raw.decode("utf-8"))
        return doc["Info"][0], doc["RowDataList"]

    root = ET.fromstring(raw.decode("utf-8"))
    info = {c.tag: c.text for c in root.find("Info")}
    rows = [{c.tag: c.text for c in row} for row in root.find("RowDataList")]
    return info, rows


def load(level: str) -> pd.DataFrame:
    """把該層級的 22 個縣市檔攤成長格式，並在過程中驗證。"""
    files = sorted(SEGIS.glob(f"*_{level}.*"))
    files = [f for f in files if not f.name.startswith("dataset-")]
    if not files:
        raise SystemExit(f"找不到 data/segis/*_{level}.*，先跑 python fetch_segis.py")

    cells: Counter = Counter()
    times, county_ids = set(), {}
    for path in files:
        county = path.stem.rsplit("_", 1)[0]
        info, rows = read_one(path)

        if int(info["OutTotal"]) != len(rows):
            raise SystemExit(
                f"{path.name}：宣告 {info['OutTotal']} 列、實際 {len(rows)} 列，"
                "檔案可能被截斷")

        # 發布區代碼的前 3 碼應該只對應一個縣市；跨檔也必須 1:1。
        # 這條是防「把整批列歸錯縣市」——那種錯不會報錯，只會產出一張錯的地圖。
        key = "CODE2" if level == "L2" else "CODE1"
        prefixes = {r[key][:3] for r in rows}
        if len(prefixes) != 1:
            raise SystemExit(f"{path.name}：{key} 出現 {len(prefixes)} 種縣市前綴 {prefixes}")
        prefix = prefixes.pop()
        if county_ids.setdefault(prefix, (county, info["InCountyId"])) != (
                county, info["InCountyId"]):
            raise SystemExit(f"{path.name}：前綴 {prefix} 與其他檔的縣市對應衝突")

        for row in rows:
            times.add(row["INFO_TIME"])
            for name, value in row.items():
                m = CELL.match(name)
                if not m:
                    continue
                age, sex, edu = m.groups()
                key = (info["InCountyId"], county, AGES[age], SEXES[sex], EDU[edu])
                cells[key] += int(float(value or 0))

    if len(times) != 1:
        raise SystemExit(f"各縣市的資料時間不一致：{sorted(times)}，不可彙總")
    if len(county_ids) != 22:
        raise SystemExit(f"只讀到 {len(county_ids)} 個縣市，應為 22")

    # 發布區層級就地加總掉，只留縣市 × 年齡組 × 性別 × 教育程度 = 22×6×2×10 列。
    # 這個版本的發布區代碼接不回鄉鎮市區（見模組說明），保留更細的粒度接不上任何
    # 行政區圖資。要鄉鎮層級的話是改抓行政區版，不是在這裡保留發布區。
    df = pd.DataFrame([(*k, v) for k, v in sorted(cells.items())], columns=[
        "縣市代碼", "縣市", "年齡組", "性別", "教育程度", "人數"])
    df["資料時間"] = times.pop()

    total = int(df["人數"].sum())
    lo, hi = NATIONAL_RANGE
    if not lo <= total <= hi:
        raise SystemExit(
            f"全國 15 歲以上原住民 {total:,} 人，超出合理區間 {lo:,}–{hi:,}")
    return df


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    wide = df.pivot_table(index=["縣市代碼", "縣市"], columns="教育程度",
                          values="人數", aggfunc="sum").fillna(0).astype(int)
    out = pd.DataFrame(index=wide.index)
    out["15歲以上人口"] = wide.sum(axis=1)
    out["大學以上"] = wide[["博士", "碩士", "大學院校"]].sum(axis=1)
    out["專科以上"] = out["大學以上"] + wide["專科"]
    out["國中以下"] = wide[["國中初職", "小學", "自修", "不識字"]].sum(axis=1)
    for col in ("大學以上", "專科以上", "國中以下"):
        out[f"{col}占比"] = (out[col] / out["15歲以上人口"] * 100).round(2)
    return out.reset_index().sort_values("專科以上占比", ascending=False)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(exist_ok=True)

    have = Counter(p.stem.rsplit("_", 1)[1] for p in SEGIS.glob("*_L*.*"))
    df = load("L2" if have["L2"] else "L1")

    # 一級與二級發布區是巢狀的（一級 ⊂ 二級），彙總到縣市必須得到同一組數字。
    # 兩級都抓齊才跑這條——只抓了一部分 L1 不足以驗證，跳過比誤報有用。
    if have["L2"] == 22 and have["L1"] == 22:
        other = load("L1").groupby("縣市")["人數"].sum()
        base = df.groupby("縣市")["人數"].sum()
        diff = (base - other).abs()
        if diff.max() != 0:
            raise SystemExit(f"一級與二級發布區彙總不一致：\n{diff[diff > 0]}")
        print(f"  ✓ 一級／二級發布區彙總結果一致（{len(base)} 縣市）")

    df.to_csv(OUT / "adult_education.csv", index=False, encoding="utf-8-sig")
    summary = summarise(df)
    summary.to_csv(OUT / "adult_education_summary.csv", index=False,
                   encoding="utf-8-sig")

    period = df["資料時間"].iloc[0]
    total = int(df["人數"].sum())
    print(f"adult_education.csv          {len(df):,} 列（{period}）")
    print(f"adult_education_summary.csv  {len(summary)} 縣市，"
          f"全國 15 歲以上原住民 {total:,} 人")

    nat = summary["專科以上"].sum() / summary["15歲以上人口"].sum() * 100
    print(f"\n專科以上比率（全國 {nat:.1f}%）")
    cols = ["縣市", "15歲以上人口", "專科以上占比", "大學以上占比", "國中以下占比"]
    print(summary[cols].to_string(index=False))


if __name__ == "__main__":
    main()
