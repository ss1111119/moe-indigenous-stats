"""原住民高中職學生的分流：普通科、職業科，還是進修部。

本專案說得出「原民生集中在哪些學門」，但說不出那個集中是從哪裡開始的。
高中的分流決定升學時的選項，是科系分析的上游。

104 → 114 學年：**普通科 27.6% → 38.0%（＋10.4 個百分點）、
進修部 12.4% → 6.2%（腰斬）、專業群（職業）科 41.8% → 41.9%（幾乎不動）。**

資料來自既有的 `data/edu_A_1_7.json`（各級學校原住民學生概況—按設立別，
由 `fetch.py` 取得）。**不抓取任何新資料。**

⚠️ 四件事：

1. **本輪沒有一般生對照。** 專案的分母資料（`sdata`／`student`／`graduate`）
   全部是大專層級，沒有高中職科別的全體學生數。所以這裡的占比是
   **原民生之內的組成**，不是「跟全體學生比多還少」。要加對照得另尋來源。

2. **不解讀總人數的下降**（24,195 → 20,398）。那受少子化、原住民人口結構、
   學制變動與登記行為影響，要拆開需要本專案沒有的資料。給一個沒有依據的解釋
   比不解釋更糟。同理，綜合高中的萎縮是全國性的學制趨勢，
   **不可解讀成原民生的選擇改變**。

3. **`項目別` 有三種互斥切法**（設立別／性別／族別），每一種的加總都是同一個母體。
   **全部相加會得到三倍**。本腳本固定取設立別那組，另外兩組拿來交叉驗證。

4. **與就學階梯的高中職數字相符不構成交叉驗證**——兩者同為教育部統計處，
   只證明沒有讀錯欄位。

輸出 out/senior_stream.csv。
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / "data" / "edu_A_1_7.json"
OUT = ROOT / "out"
LADDER = OUT / "ladder_summary.csv"

# 欄位名 → 分流名。「進修部」與其他四類不完全平行（它同時帶有就學型態的意涵），
# 呈現時單獨標註，不拿來跟其他四類做「普通 vs 職業」的二分。
STREAMS = {
    "高級中等學校-普通科小計": "普通科",
    "高級中等學校-綜合高中小計": "綜合高中",
    "高級中等學校-專業群(職業)科小計": "專業群(職業)科",
    "高級中等學校-實用技能學程 (延教班)小計": "實用技能學程",
    "高級中等學校-進修部(學校)小計": "進修部",
}

ESTABLISHMENT = {"公立", "私立"}
SEX = {"男", "女"}

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load() -> list[dict]:
    if not SOURCE.exists():
        raise SystemExit(
            f"找不到 {SOURCE.relative_to(ROOT)}。請先執行：python fetch.py\n"
            "本腳本只做既有下載檔的分析，不抓取任何新資料。"
        )
    rows = json.loads(SOURCE.read_text(encoding="utf-8"))

    have = set(rows[0])
    missing = [c for c in STREAMS if c not in have]
    if missing:
        raise SystemExit(
            f"來源缺少高中職欄位 {missing}。\n實際欄位：{sorted(have)}\n"
            "來源可能改版，未產出任何輸出檔。"
        )
    return rows


def num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def senior_total(rows: list[dict]) -> float:
    return sum(num(r[c]) for r in rows for c in STREAMS)


def build(rows: list[dict]) -> list[dict]:
    years = sorted({r["學年度"] for r in rows}, key=int)
    out = []

    for year in years:
        yr = [r for r in rows if r["學年度"] == year]
        est = [r for r in yr if r["項目別"] in ESTABLISHMENT]
        sex = [r for r in yr if r["項目別"] in SEX]
        eth = [r for r in yr if r["項目別"] not in ESTABLISHMENT | SEX]

        # 三種切法必須得到同一個母體。不相等表示欄位讀錯或來源改版——
        # 那種錯不會報錯，只會產出一組看起來合理的錯占比。
        totals = (senior_total(est), senior_total(sex), senior_total(eth))
        if len({round(t) for t in totals}) != 1:
            raise SystemExit(
                f"{year} 學年三種切法的高中職合計不一致，未產出任何輸出檔：\n"
                f"    設立別 {totals[0]:,.0f}／性別 {totals[1]:,.0f}／"
                f"族別 {totals[2]:,.0f}"
            )

        total = totals[0]
        for col, name in STREAMS.items():
            n = sum(num(r[col]) for r in est)
            out.append({
                "學年": year,
                "分流": name,
                "人數": int(n),
                "占比": round(n / total * 100, 2) if total else "",
            })

        share = sum(o["占比"] for o in out[-len(STREAMS):] if o["占比"] != "")
        if abs(share - 100) > 0.05:
            raise SystemExit(f"{year} 學年五類占比加總為 {share:.2f}%，不是 100%。")

    return out


def check_ladder(rows: list[dict]) -> None:
    """與就學階梯的高中職數字比對。相符只證明沒讀錯欄位，不是交叉驗證。"""
    if not LADDER.exists():
        print("  ! 找不到 ladder_summary.csv，略過與就學階梯的比對")
        return
    with LADDER.open(encoding="utf-8-sig") as fh:
        lad = {r["學制"]: r for r in csv.DictReader(fh)}
    if "高中職" not in lad:
        print("  ! ladder_summary.csv 沒有高中職那列，略過比對")
        return

    year = lad["高中職"]["學年"]
    theirs = int(lad["高中職"]["原住民學生數"])
    mine = sum(r["人數"] for r in rows if r["學年"] == year)
    mark = "✓" if mine == theirs else "!"
    print(f"  {mark} 與就學階梯比對（{year} 學年）："
          f"本檔 {mine:,} vs ladder {theirs:,}"
          f"{'' if mine == theirs else '——不一致，請檢查'}")
    print("    （同為教育部統計處，相符只證明沒讀錯欄位，不是交叉驗證）")


def main() -> None:
    rows = build(load())

    OUT.mkdir(exist_ok=True)
    path = OUT / "senior_stream.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["學年", "分流", "人數", "占比"])
        w.writeheader()
        w.writerows(rows)

    years = sorted({r["學年"] for r in rows}, key=int)
    first, last = years[0], years[-1]
    print(f"原住民高中職學生的分流（{first}–{last} 學年）")
    print(f"  senior_stream.csv  {len(rows)} 列\n")

    ta = sum(r["人數"] for r in rows if r["學年"] == first)
    tb = sum(r["人數"] for r in rows if r["學年"] == last)

    # ⚠️ 顯示一律從人數重算，不要拿 CSV 裡已四捨五入到 2 位的占比再格式化成 1 位。
    # 兩次四捨五入會讓 41.945% 變成 42.0%（真值 41.9%）。
    def pct(year: str, name: str, total: int) -> float:
        n = next(r["人數"] for r in rows if r["學年"] == year and r["分流"] == name)
        return n / total * 100 if total else 0.0

    print(f"  {'分流':<14}{first + ' 學年':>10}{last + ' 學年':>10}{'變化':>9}")
    for n in STREAMS.values():
        a, b = pct(first, n, ta), pct(last, n, tb)
        print(f"  {n:<14}{a:>9.1f}%{b:>9.1f}%{b - a:>+8.1f}")

    print(f"\n  總人數 {ta:,} → {tb:,}（本腳本不解讀這個變化，見模組說明）")
    check_ladder(rows)
    print("  ⚠️ 本輪沒有一般生對照，占比是原民生之內的組成。")


if __name__ == "__main__":
    main()
