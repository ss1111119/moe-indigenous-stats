"""承接端的鄉鎮市區層級：哪些鄉鎮在收原民生，以及他們占當地大專學生的比重。

資料：內政部統計處《行政區大專校院統計》（SEGIS），由 fetch_segis_college.py
抓下全國一次取回的鄉鎮市區檔。

⚠️ 四件事：

1. **只有一個學年，這是快照不是趨勢。** 開放服務端點取不到歷年，理由與實測依據
   寫在 fetch_segis_college.py 的模組說明。輸出仍保留「學年」欄，是為了日後補進
   歷年時資料形狀不必改。

2. **學年取自回應的 `INFO_TIME`，絕不寫死。** 端點回傳的是「平台當下最新一期」，
   明年會變成 115 學年而腳本不會察覺。寫死的話就會出現「標題寫 114、
   數字其實是 115」這種最難發現的錯。

3. **比對對象是 `A1-6a` 不是 `A1-6b`。** 本資料範圍是大專校院，不含宗教研修學院
   與空大暨大專附設進修學校（那兩類在平台上是各自獨立的資料集）。geography.csv
   裡對應的欄位是 `學校所在地在學數_不含空大宗教`。

4. **本資料與教育部出版品同源**（原始統計機關就是教育部統計處），
   縣市加總相符**不構成交叉驗證**。做這個比對只是為了確認沒有把資料讀錯。

輸出 out/receiving_township.csv（鄉鎮明細）與
out/receiving_township_summary.csv（縣市摘要）。
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CACHE = ROOT / "data" / "segis-college" / "admin_college_town.json"
OUT = ROOT / "out"
GEOGRAPHY = OUT / "geography.csv"

# 一律以「名稱」取值。不得改用欄位在陣列中的位置——平台改版新增欄位時，
# 位置取值會靜默錯位，那種錯不會報錯，只會產出一張錯的地圖。
REQUIRED = [
    "INFO_TIME", "COUNTY_ID", "COUNTY", "TOWN_ID", "TOWN",
    "SCH_CNT", "STU_CNT", "NA_STU_CNT", "NA_STU_M_CNT", "NA_STU_F_CNT",
]

# 全體學生數低於此數的鄉鎮，占比不穩定：一名學生的增減就會顯著移動比率。
# 取 1,000 是因為單一小型校區規模即在此量級。
SMALL_DENOMINATOR = 1000

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load() -> tuple[str, list[dict]]:
    """讀快取並驗證，回傳 (學年, 資料列)。任何一項不對就中止，不產出半套輸出。"""
    if not CACHE.exists():
        raise SystemExit(
            f"找不到 {CACHE.relative_to(ROOT)}。請先執行：python fetch_segis_college.py\n"
            "本腳本不會自己上網取數——建置階段線上取數會讓輸出無法重現。"
        )

    doc = json.loads(CACHE.read_text(encoding="utf-8-sig"))
    names = [c["COLUMN_NAME"] for c in doc["ColumnList"]]
    missing = [n for n in REQUIRED if n not in names]
    if missing:
        raise SystemExit(
            f"回應缺少必要欄位 {missing}。\n實際收到的欄位：{names}\n"
            "平台可能改版了欄位命名，未產出任何輸出檔。"
        )

    rows = doc["RowDataList"]
    if not rows:
        raise SystemExit("RowDataList 是空的，未產出任何輸出檔。")

    times = {r["INFO_TIME"] for r in rows}
    if len(times) != 1:
        raise SystemExit(f"資料含多個期別 {sorted(times)}，本腳本只處理單一期別。")
    info_time = times.pop()

    # 逐列檢查性別分項。加總對不上表示欄位讀錯或來源有誤，
    # 兩種都不該讓它靜靜流進輸出。
    for r in rows:
        m, f, t = r["NA_STU_M_CNT"], r["NA_STU_F_CNT"], r["NA_STU_CNT"]
        if (m or 0) + (f or 0) != (t or 0):
            raise SystemExit(
                f"{info_time} {r['COUNTY']}{r['TOWN']}："
                f"原住民男 {m} ＋ 女 {f} ≠ 總計 {t}，未產出任何輸出檔。"
            )

    return info_time, rows


def academic_year(info_time: str) -> str:
    """'114Y' → '114'。格式不符就原樣保留，不猜。"""
    return info_time[:-1] if info_time.endswith("Y") else info_time


def share(indigenous: float, total: float) -> str:
    """原民生占比。分母為零時回空字串——寫 0 會被讀成「一個原民生都沒有」。"""
    if not total:
        return ""
    return f"{indigenous / total:.4f}"


def build_detail(year: str, rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        out.append({
            "學年": year,
            "縣市代碼": r["COUNTY_ID"],
            "縣市": r["COUNTY"],
            "鄉鎮市區代碼": r["TOWN_ID"],  # 來源自帶的正式行政區代碼，不推導
            "鄉鎮市區": r["TOWN"],
            "學校數": int(r["SCH_CNT"] or 0),
            "全體學生數": int(r["STU_CNT"] or 0),
            "原住民學生數": int(r["NA_STU_CNT"] or 0),
            "原住民男學生數": int(r["NA_STU_M_CNT"] or 0),
            "原住民女學生數": int(r["NA_STU_F_CNT"] or 0),
            "原民生占比": share(r["NA_STU_CNT"] or 0, r["STU_CNT"] or 0),
            "分母過小": "是" if (r["STU_CNT"] or 0) < SMALL_DENOMINATOR else "",
        })
    out.sort(key=lambda x: (x["縣市代碼"], x["鄉鎮市區代碼"]))
    return out


def build_summary(detail: list[dict]) -> list[dict]:
    by_county: dict[str, dict] = {}
    for d in detail:
        c = by_county.setdefault(d["縣市代碼"], {
            "縣市代碼": d["縣市代碼"], "縣市": d["縣市"], "鄉鎮數": 0,
            "學校數": 0, "全體學生數": 0, "原住民學生數": 0,
        })
        c["鄉鎮數"] += 1
        c["學校數"] += d["學校數"]
        c["全體學生數"] += d["全體學生數"]
        c["原住民學生數"] += d["原住民學生數"]
    for c in by_county.values():
        c["原民生占比"] = share(c["原住民學生數"], c["全體學生數"])
    return sorted(by_county.values(), key=lambda x: x["縣市代碼"])


def reconcile(year: str, summary: list[dict]) -> None:
    """縣市加總 vs A1-6a。不一致不靜默通過，但也不修改資料——只如實印出。"""
    if not GEOGRAPHY.exists():
        print(f"  ! 找不到 {GEOGRAPHY.name}，略過與 A1-6a 的比對")
        return

    import pandas as pd

    g = pd.read_csv(GEOGRAPHY, encoding="utf-8-sig")
    g = g[(g["學年度"].astype(str) == year) & (g["等級別"] == "總計")]
    if g.empty:
        print(f"  ! geography.csv 沒有 {year} 學年的總計列，略過比對")
        return

    a16a = dict(zip(g["縣市"], g["學校所在地在學數_不含空大宗教"]))
    ours = {c["縣市"]: c["原住民學生數"] for c in summary}

    print(f"\n  與 A1-6a（學校所在地、不含空大宗教）逐縣市比對，{year} 學年：")
    total_ours = total_theirs = 0
    diffs = []
    for county in sorted(set(a16a) | set(ours)):
        mine, theirs = ours.get(county, 0), int(a16a.get(county, 0))
        total_ours += mine
        total_theirs += theirs
        if mine != theirs:
            diffs.append((county, mine, theirs, mine - theirs))

    print(f"    全國：SEGIS {total_ours:,} vs A1-6a {total_theirs:,}"
          f"（差 {total_ours - total_theirs:+,}）")
    if diffs:
        print(f"    有差額的縣市 {len(diffs)} 個：")
        for county, mine, theirs, d in sorted(diffs, key=lambda x: -abs(x[3])):
            print(f"      {county:<5} SEGIS {mine:>6,}  A1-6a {theirs:>6,}  差 {d:+,}")
    else:
        print("    逐縣市完全相符")


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    info_time, rows = load()
    year = academic_year(info_time)

    detail = build_detail(year, rows)
    summary = build_summary(detail)

    OUT.mkdir(exist_ok=True)
    write(OUT / "receiving_township.csv", detail)
    write(OUT / "receiving_township_summary.csv", summary)

    counties = {d["縣市"] for d in detail}
    towns = {d["鄉鎮市區代碼"] for d in detail}
    small = sum(1 for d in detail if d["分母過小"])

    print(f"《行政區大專校院統計》{year} 學年（來源 INFO_TIME={info_time}）")
    print(f"  receiving_township.csv          {len(detail)} 列，"
          f"{len(towns)} 個鄉鎮市區、{len(counties)} 個縣市")
    print(f"  receiving_township_summary.csv  {len(summary)} 縣市")
    print(f"  分母低於 {SMALL_DENOMINATOR:,} 人而占比不穩定的鄉鎮：{small} 個")

    top = sorted(detail, key=lambda d: -d["原住民學生數"])[:5]
    print("\n  承接最多的 5 個鄉鎮市區：")
    for d in top:
        pct = f"{float(d['原民生占比']) * 100:.2f}%" if d["原民生占比"] else "—"
        print(f"    {d['縣市']}{d['鄉鎮市區']:<5} 原民生 {d['原住民學生數']:>5,}"
              f"  占當地 {pct}")

    reconcile(year, summary)


if __name__ == "__main__":
    main()
