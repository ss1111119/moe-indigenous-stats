"""就學階梯：原民生在四個學制上，分別散布在多少個鄉鎮市區。

114 學年，有該階學校的鄉鎮市區數：**367 → 357 → 206 → 87**。

義務教育近乎全覆蓋（全國 368 個鄉鎮市區），到了高等教育只剩 87 個。
這就是原民生必須離開戶籍地的結構性理由——不是偏好問題，是他家鄉沒有下一階的學校。
現有的地理頁只呈現「離開了」這個結果，這支腳本補的是原因。

資料：內政部統計處《行政區各級學校統計》四筆（SEGIS），由 fetch_segis_college.py
抓下。四筆欄位命名完全相同，驗證邏輯共用 build_receiving.load_level()。

⚠️ **跨階的人數不可直接相比，可比的是鄉鎮市區數。**

各學制年級數不同：國小 6 年、國中 3 年、高中職 3 年，大專同時含二專、五專、
學士、碩士、博士而沒有單一數字。國小的 52,051 人涵蓋 6 個年級、高中職的
20,398 人涵蓋 3 個年級，直接相比會讓人誤以為流失了六成。

鄉鎮市區數則乾淨——每個鄉鎮在每一階都只被計數一次，不受年級數影響。

⚠️ **四階是同一時點的橫斷面，不是同一批人的追蹤。**
今年的國小生和今年的大專生是不同的人，兩者相除不是升學率也不是流失率。
本腳本刻意不輸出任何跨階相除的數字。

⚠️ 四筆的原始統計機關都是教育部統計處，四階彼此一致**不構成交叉驗證**。

輸出 out/ladder_township.csv（學制 × 鄉鎮明細）與 out/ladder_summary.csv（階梯摘要）。
"""

import csv
import sys
from pathlib import Path

from build_receiving import academic_year, load_level
from fetch_segis_college import LEVELS

ROOT = Path(__file__).parent
OUT = ROOT / "out"

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def collect() -> tuple[str, list[dict]]:
    """讀四個學制，回傳 (學年, 明細列)。任一學制不合格即中止。"""
    detail: list[dict] = []
    times: dict[str, str] = {}

    for code, label, years, _ocode in LEVELS:
        info_time, rows = load_level(code, label)
        times[label] = info_time
        for r in rows:
            detail.append({
                "學年": "",  # 四階校對過期別後才填，見下方
                "學制": label,
                "年級數": "" if years is None else years,
                "縣市代碼": r["COUNTY_ID"],
                "縣市": r["COUNTY"],
                "鄉鎮市區代碼": r["TOWN_ID"],
                "鄉鎮市區": r["TOWN"],
                "學校數": int(r["SCH_CNT"] or 0),
                "全體學生數": int(r["STU_CNT"] or 0),
                "原住民學生數": int(r["NA_STU_CNT"] or 0),
                "原住民男學生數": int(r["NA_STU_M_CNT"] or 0),
                "原住民女學生數": int(r["NA_STU_F_CNT"] or 0),
            })

    # 四階若不同期，放在同一張階梯圖上就是錯的——寧可中止也不要畫出來。
    if len(set(times.values())) != 1:
        lines = "\n".join(f"    {k}：{v}" for k, v in times.items())
        raise SystemExit(f"四個學制的期別不一致，未產出任何輸出檔：\n{lines}")

    year = academic_year(next(iter(times.values())))
    for d in detail:
        d["學年"] = year
    return year, detail


def summarise(year: str, detail: list[dict]) -> list[dict]:
    order = [label for _c, label, _y, _o in LEVELS]
    years_of = {label: ("" if y is None else y) for _c, label, y, _o in LEVELS}

    out = []
    for label in order:
        rows = [d for d in detail if d["學制"] == label]
        out.append({
            "學年": year,
            "學制": label,
            "年級數": years_of[label],
            "有該階學校的鄉鎮市區數": len({d["鄉鎮市區代碼"] for d in rows}),
            "有原民生的鄉鎮市區數": len({d["鄉鎮市區代碼"] for d in rows
                                        if d["原住民學生數"] > 0}),
            "涵蓋縣市數": len({d["縣市代碼"] for d in rows}),
            "原住民學生數": sum(d["原住民學生數"] for d in rows),
        })
    return out


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    year, detail = collect()
    summary = summarise(year, detail)

    detail.sort(key=lambda d: (
        [l for _c, l, _y, _o in LEVELS].index(d["學制"]),
        d["縣市代碼"], d["鄉鎮市區代碼"]))

    OUT.mkdir(exist_ok=True)
    write(OUT / "ladder_township.csv", detail)
    write(OUT / "ladder_summary.csv", summary)

    print(f"《行政區各級學校統計》{year} 學年，四個學制")
    print(f"  ladder_township.csv  {len(detail)} 列")
    print(f"  ladder_summary.csv   {len(summary)} 列\n")

    print("  有該階學校的鄉鎮市區數（全國共 368 個）：")
    counts = [s["有該階學校的鄉鎮市區數"] for s in summary]
    for s in summary:
        bar = "█" * round(s["有該階學校的鄉鎮市區數"] / max(counts) * 40)
        yr = f"{s['年級數']} 年" if s["年級數"] != "" else "年級數不一"
        print(f"    {s['學制']:<3} {s['有該階學校的鄉鎮市區數']:>4} {bar}"
              f"　原民生 {s['原住民學生數']:>7,}（{yr}）")

    # 遞減是這份資料的重點，不遞減表示讀錯了——講出來而不是預設它成立。
    if counts != sorted(counts, reverse=True):
        print(f"\n  ! 鄉鎮市區數並非遞減：{counts}，請檢查資料")
    else:
        print(f"\n  ✓ 鄉鎮市區數遞減：{' → '.join(str(c) for c in counts)}")

    print("\n  ⚠️ 跨階人數不可相比（年級數不同），四階也非同一批人的追蹤。")


if __name__ == "__main__":
    main()
