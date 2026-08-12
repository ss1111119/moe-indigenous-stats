"""縣市視角：把四份既有輸出彙整成「一列一個縣市」。

「縣市」頁有 10 個區塊，全部是全國彙總或 22 縣市的排行榜。讀者想知道**某一個
縣市的完整處境**時，得自己橫跨四個區塊把數字拼起來。這支腳本把它們併成一列。

全國那條 367 → 87 在縣市層級變得具體得多：
**臺東縣 16 個鄉鎮有國小，只有 1 個有大專校院。**

資料全部來自既有輸出，**不抓取任何新資料、不讀 `data/`**：

| 來源 | 提供 |
| --- | --- |
| `geography.csv` | 出生戶籍地、學校所在地、淨流動、就學戶籍比 |
| `ladder_township.csv` | 該縣市內有各學制學校的鄉鎮市區數 |
| `receiving_township.csv` | 該縣市承接原民生的鄉鎮數與人數 |
| `attainment_standardised.csv` | 原始與年齡標準化的專科以上占比 |

⚠️ 三件事：

1. **不含高中職分流。** 原民端的分流資料（`edu_A_1_7`）的 `項目別` 只有
   設立別／性別／族別三種切法，**沒有縣市**。全體端的 `base3` 有縣市，
   但單邊有分項無法構成對照。所以縣市視角是四塊不是五塊——
   這是資料的限制，頁面上要寫出來，不要靜靜少一塊讓人以為忘了做。

2. **小分母縣市的比率不可當真。** 連江縣 114 學年的出生戶籍地在學數是 **4 人**，
   算出來的就學戶籍比是 0.0%；金門 14 人算出 371%、嘉義市 49 人算出 367%。
   這些與臺東 3,909 人算出的 20.3% 放在同一個選單裡，讀者沒有理由知道
   可信度差了兩個數量級。低於 200 人者標記，但**不從資料中移除**——
   它們的人數本身是真實的。

3. **連江縣沒有大專校院**，`receiving_township.csv` 只有 21 個縣市。
   該縣市的承接兩欄填 0 而不是留空，否則下游會分不出「沒有」與「漏了」。

輸出 out/county_view.csv。
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "out"

# 上游檔 → 產生它的腳本。缺檔時要指名兩者，只說「找不到檔案」不夠。
UPSTREAM = {
    "geography.csv": "build_geography.py",
    "ladder_township.csv": "build_ladder.py",
    "receiving_township.csv": "build_receiving.py",
    "attainment_standardised.csv": "build_attainment_age.py",
}

LEVELS = ["國小", "國中", "高中職", "大專"]

# 出生戶籍地在學數低於此數的縣市，其**比率**標記為不穩定（人數照常顯示）。
# 與專案既有做法同一個量級：承接端用 1,000、年齡分解用 500，
# 都是「一個百分點對應不到 5 個單位」。
SMALL_DENOMINATOR = 200

YEAR = 114

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def read(name: str) -> pd.DataFrame:
    path = OUT / name
    if not path.exists():
        raise SystemExit(
            f"找不到 {path.relative_to(ROOT)}。"
            f"請先執行：python {UPSTREAM[name]}\n"
            "本腳本只彙整既有輸出，不抓取任何新資料。"
        )
    return pd.read_csv(path, encoding="utf-8-sig")


def build() -> pd.DataFrame:
    geo = read("geography.csv")
    geo = geo[(geo["學年度"] == YEAR) & (geo["等級別"] == "總計")]
    if geo.empty:
        raise SystemExit(f"geography.csv 沒有 {YEAR} 學年的總計列，未產出輸出檔。")

    lad = read("ladder_township.csv")
    rec = read("receiving_township.csv")
    std = read("attainment_standardised.csv").set_index("縣市")

    rows = []
    for r in geo.itertuples():
        county = r.縣市
        if county not in std.index:
            raise SystemExit(f"{county} 在 attainment_standardised.csv 找不到，未產出輸出檔。")
        s = std.loc[county]

        L = lad[lad["縣市"] == county]
        steps = [L[L["學制"] == lv]["鄉鎮市區代碼"].nunique() for lv in LEVELS]

        # 沒有大專校院的縣市在 receiving 裡沒有列——填 0 而不是留空，
        # 否則下游分不出「沒有」與「漏了」。
        R = rec[rec["縣市"] == county]

        born = int(r.出生戶籍地在學數)
        rows.append({
            "縣市代碼": s["縣市代碼"],
            "縣市": county,
            "出生戶籍地": born,
            "學校所在地": int(r.學校所在地在學數),
            "淨流動": int(r.淨流動),
            "就學戶籍比": round(float(r.就學戶籍比), 2),
            "有國小的鄉鎮數": steps[0],
            "有國中的鄉鎮數": steps[1],
            "有高中職的鄉鎮數": steps[2],
            "有大專的鄉鎮數": steps[3],
            "承接鄉鎮數": len(R),
            "承接原民生": int(R["原住民學生數"].sum()),
            "原始專科以上占比": float(s["原始專科以上占比"]),
            "年齡標準化占比": float(s["年齡標準化占比"]),
            "小分母": "是" if born < SMALL_DENOMINATOR else "",
        })

    df = pd.DataFrame(rows).sort_values("縣市代碼").reset_index(drop=True)

    if len(df) != 22:
        raise SystemExit(
            f"縣市數為 {len(df)}，應為 22，未產出輸出檔。\n實際：{list(df['縣市'])}")

    # 一個鄉鎮若有大專，它在國小那一階也會被算到，所以四階不可能往上升。
    # 升了就表示彙整寫錯了——那種錯不會報錯，只會產出一張錯的階梯。
    for r in df.itertuples():
        seq = [r.有國小的鄉鎮數, r.有國中的鄉鎮數, r.有高中職的鄉鎮數, r.有大專的鄉鎮數]
        if any(b > a for a, b in zip(seq, seq[1:])):
            raise SystemExit(f"{r.縣市} 的四階鄉鎮數往上升：{seq}，未產出輸出檔。")

    return df


def main() -> None:
    df = build()
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "county_view.csv", index=False, encoding="utf-8-sig")

    flagged = df[df["小分母"] == "是"]
    print(f"縣市視角（{YEAR} 學年）")
    print(f"  county_view.csv  {len(df)} 列\n")

    show = df.sort_values("就學戶籍比").head(5)
    print(f"  {'縣市':<7}{'四階鄉鎮數':>14}{'就學戶籍比':>11}{'承接':>8}{'存量標準化':>11}")
    for r in show.itertuples():
        steps = f"{r.有國小的鄉鎮數}／{r.有國中的鄉鎮數}／{r.有高中職的鄉鎮數}／{r.有大專的鄉鎮數}"
        print(f"  {r.縣市:<7}{steps:>16}{r.就學戶籍比:>10.1f}%"
              f"{r.承接鄉鎮數:>6} 鄉鎮{r.年齡標準化占比:>10.1f}%")

    print(f"\n  比率標記為不穩定的縣市（出生戶籍地 < {SMALL_DENOMINATOR} 人）："
          f"{len(flagged)} 個")
    for r in flagged.itertuples():
        print(f"    {r.縣市:<5} 出生戶籍地 {r.出生戶籍地:>4} 人"
              f"　就學戶籍比 {r.就學戶籍比:.1f}%（分母太小，不可當真）")

    print("\n  ⚠️ 不含高中職分流——原民端的分流資料沒有縣市分項，見模組說明。")


if __name__ == "__main__":
    main()
