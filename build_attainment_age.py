"""原住民教育程度的年齡分解與年齡標準化，按縣市。

存量區塊呈現的「專科以上占比」把兩件事混在一起：各年齡層的教育程度差異，
以及各縣市原住民人口的**年齡結構**差異。臺東有 18.9% 的原住民是 65 歲以上，
臺北只有 10.4%——而 65 歲以上那一代不論在哪個縣市，專科以上比率都很低。

分年齡看，差距的形狀完全不同：15-24 歲的縣市全距只有約 14 個百分點，
35-44 歲卻有約 31 個。**最年輕的世代差距最小。**

⚠️ 四件事：

1. **本腳本不推翻既有結論，只是分解它。** 原始全距 24.6 個百分點、年齡標準化後
   仍有 21.4，年齡結構只解釋約 13%。散布圖的相關性也對標準化穩健
   （+0.798 對 +0.806，去掉臺東後 +0.785 對 +0.802）。既有的數字與說法都成立。

2. **原始占比與標準化占比並列，後者不取代前者。** 兩者回答不同問題：
   原始占比是「現在住在這個縣市的原住民，實際的學歷結構」——規劃在地服務要看它；
   標準化占比是「排除人口老化程度的差異後，各縣市差多少」。

3. **標準化是分解，不是校正，不支持因果推論。** 年齡結構本身就是遷移的結果，
   不是外生變數。把年齡調整掉等於把一部分現象也調整掉了。

4. **人數低於 500 的格不穩定**，標記出來且不納入全距計算——連江縣 65 歲以上
   只有數十人，其比率會主導全距而讓那個統計量失去意義。

資料來自既有的 out/adult_education.csv（build_education.py 產生，113 年 12 月底），
**不抓取任何新資料**。

輸出 out/attainment_by_age.csv 與 out/attainment_standardised.csv。
"""

import csv
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "out"
SOURCE = OUT / "adult_education.csv"

BANDS = ["15-24歲", "25-34歲", "35-44歲", "45-54歲", "55-64歲", "65歲以上"]
TERTIARY = {"博士", "碩士", "大學院校", "專科"}

# 低於此數的格，一個百分點對應不到 5 個人，比率不穩定。
SMALL_CELL = 500

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load() -> pd.DataFrame:
    if not SOURCE.exists():
        raise SystemExit(
            f"找不到 {SOURCE.relative_to(ROOT)}。請先執行：python build_education.py\n"
            "本腳本只做既有輸出的再分析，不抓取任何新資料。"
        )
    df = pd.read_csv(SOURCE)

    found = sorted(df["年齡組"].unique())
    if set(found) != set(BANDS):
        raise SystemExit(
            f"年齡組不是預期的六組，未產出任何輸出檔。\n"
            f"  預期：{BANDS}\n  實際：{found}\n"
            "標準人口的權重會對不上，不能繼續。"
        )
    return df


def by_age(df: pd.DataFrame) -> pd.DataFrame:
    period = df["資料時間"].iloc[0]
    codes = df.groupby("縣市")["縣市代碼"].first()

    pop = df.groupby(["縣市", "年齡組"])["人數"].sum()
    ter = (df[df["教育程度"].isin(TERTIARY)]
           .groupby(["縣市", "年齡組"])["人數"].sum())

    rows = []
    for (county, band), n in pop.items():
        t = int(ter.get((county, band), 0))
        n = int(n)
        rows.append({
            "資料時間": period,
            "縣市代碼": codes[county],
            "縣市": county,
            "年齡組": band,
            "人數": n,
            "專科以上人數": t,
            "專科以上占比": round(t / n * 100, 2) if n else "",
            "人數過少": "是" if n < SMALL_CELL else "",
        })
    rows.sort(key=lambda r: (r["縣市代碼"], BANDS.index(r["年齡組"])))
    return pd.DataFrame(rows)


def standardise(age: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    """直接法：以全國年齡結構為標準人口，加權各縣市的組內占比。"""
    wide_n = age.pivot(index="縣市", columns="年齡組", values="人數")[BANDS]
    wide_t = age.pivot(index="縣市", columns="年齡組", values="專科以上人數")[BANDS]
    codes = age.groupby("縣市")["縣市代碼"].first()
    period = age["資料時間"].iloc[0]

    national = wide_n.sum(axis=0)
    weights = national / national.sum()

    within = wide_t / wide_n            # 各縣市各年齡組的組內占比
    crude = wide_t.sum(axis=1) / wide_n.sum(axis=1) * 100
    std = (within.fillna(0) * weights).sum(axis=1) * 100
    p65 = wide_n["65歲以上"] / wide_n.sum(axis=1) * 100

    # 標準化占比是該縣市組內占比的加權平均。若該縣市大半人口落在不穩定的格裡，
    # 這個看起來很紮實的單一數字其實一樣不穩定——嘉義市六個年齡組全部低於 500 人。
    small = wide_n.where(wide_n < SMALL_CELL).fillna(0)
    unstable_share = small.sum(axis=1) / wide_n.sum(axis=1) * 100

    crude_rank = crude.rank(ascending=False, method="min").astype(int)
    std_rank = std.rank(ascending=False, method="min").astype(int)

    out = pd.DataFrame({
        "資料時間": period,
        "縣市代碼": codes,
        "縣市": crude.index,
        "15歲以上人數": wide_n.sum(axis=1).astype(int),
        "原始專科以上占比": crude.round(2),
        "年齡標準化占比": std.round(2),
        "標準化差值": (std - crude).round(2),
        "65歲以上占比": p65.round(2),
        "原始排名": crude_rank,
        "標準化排名": std_rank,
        "排名變動": crude_rank - std_rank,   # 正數＝標準化後名次前進
        "不穩定人口占比": unstable_share.round(1),
        "標準化不穩定": unstable_share.map(lambda v: "是" if v >= 50 else ""),
    }).sort_values("縣市代碼").reset_index(drop=True)

    nat_crude = wide_t.sum().sum() / wide_n.sum().sum() * 100
    nat_std = ((wide_t.sum() / wide_n.sum()) * weights).sum() * 100
    return out, nat_crude, nat_std


def spreads(age: pd.DataFrame) -> list[tuple[str, float, int]]:
    """各年齡組的縣市全距，排除人數過少的格。"""
    out = []
    for band in BANDS:
        sub = age[(age["年齡組"] == band) & (age["人數過少"] != "是")]
        v = pd.to_numeric(sub["專科以上占比"])
        out.append((band, float(v.max() - v.min()), len(v)))
    return out


def main() -> None:
    df = load()
    age = by_age(df)
    std, nat_crude, nat_std = standardise(age)

    # 以自身年齡結構標準化是恆等變換。不相等就是權重算錯了——
    # 那種錯不會報錯，只會產出一組看起來合理但錯的排名。
    if round(nat_crude, 2) != round(nat_std, 2):
        raise SystemExit(
            f"全國原始占比 {nat_crude:.4f}% 與標準化占比 {nat_std:.4f}% 不相等，"
            "標準人口權重有誤，未產出任何輸出檔。"
        )

    OUT.mkdir(exist_ok=True)
    age.to_csv(OUT / "attainment_by_age.csv", index=False,
               encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
    std.to_csv(OUT / "attainment_standardised.csv", index=False,
               encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    total = int(age["人數"].sum())
    small = int((age["人數過少"] == "是").sum())
    print(f"原住民教育程度的年齡分解（{age['資料時間'].iloc[0]}）")
    print(f"  attainment_by_age.csv        {len(age)} 列，{total:,} 人")
    print(f"  attainment_standardised.csv  {len(std)} 縣市")
    print(f"  ✓ 全國原始與標準化占比一致：{nat_crude:.2f}%（權重檢查通過）")
    print(f"  人數低於 {SMALL_CELL} 而不穩定的格：{small} 個\n")

    print("  各年齡組的縣市全距（已排除人數過少的格）：")
    for band, sp, n in spreads(age):
        print(f"    {band:<7} {sp:>5.1f} 個百分點  (n={n})")

    print("\n  標準化後名次前進最多的縣市：")
    top = std.sort_values("排名變動", ascending=False).head(5)
    for r in top.itertuples():
        print(f"    {r.縣市:<5} {r.原始專科以上占比:>5.1f}% → {r.年齡標準化占比:>5.1f}%"
              f"　第 {r.原始排名} 名 → 第 {r.標準化排名} 名"
              f"（65+ 占 {r._8:.1f}%）")

    flagged = std[std["標準化不穩定"] == "是"]["縣市"].tolist()
    print(f"\n  標準化占比建立在不穩定格上而被標記的縣市（{len(flagged)} 個）："
          f"{'、'.join(flagged)}")

    def spread(df: pd.DataFrame) -> tuple[float, float]:
        return (float(df["原始專科以上占比"].max() - df["原始專科以上占比"].min()),
                float(df["年齡標準化占比"].max() - df["年齡標準化占比"].min()))

    crude_sp, std_sp = spread(std)
    keep_c, keep_s = spread(std[std["標準化不穩定"] != "是"])

    # 全距若依賴被標記的縣市，對外就不能用全部縣市的版本——先驗再說。
    if (round(crude_sp, 1), round(std_sp, 1)) != (round(keep_c, 1), round(keep_s, 1)):
        print(f"  ! 全距依賴被標記縣市：全部 {crude_sp:.1f}/{std_sp:.1f}、"
              f"排除後 {keep_c:.1f}/{keep_s:.1f}——對外應採用排除後的數字")
        crude_sp, std_sp = keep_c, keep_s
    else:
        print(f"  ✓ 全距不依賴被標記縣市（排除前後皆為 "
              f"{crude_sp:.1f} 與 {std_sp:.1f}）")

    print(f"\n  縣市全距：原始 {crude_sp:.1f} → 標準化 {std_sp:.1f} 個百分點"
          f"（年齡結構解釋約 {(crude_sp - std_sp) / crude_sp * 100:.0f}%）")
    print("  ⚠️ 這是分解不是校正——年齡結構本身就是遷移的結果，不支持因果推論。")


if __name__ == "__main__":
    main()
