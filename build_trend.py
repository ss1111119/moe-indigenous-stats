"""細學類的逐年增減趨勢：原住民學生 vs 一般生，106–114 學年。

把 compare_major.csv 轉成以 106 學年為基期（=100）的指數序列，兩群人可以放在
同一張圖上比較走勢，不受人數規模差 40 倍的影響。

sdata 109 學年有缺漏（全年短少 4.4%），但不是均勻分布——只有 10 個細學類受到
影響。這裡逐類檢查，把 109 明顯低於 108／110 內插值的那幾類標成分母異常，
其指數留白，畫線時斷開。

輸出 out/trend_major.csv。先跑 `python build_field.py`。
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "out"

BASE_YEAR = 106
SUSPECT_YEAR = 109
# 109 年低於 108／110 內插值這個比例，就當作該類的分母有缺漏
SUSPECT_RATIO = 0.9


def load() -> pd.DataFrame:
    df = pd.read_csv(OUT / "compare_major.csv", dtype={"代碼": str})
    return df[(df["等級別"] == "總計") & df["可比"]].copy()


def flag_suspect(df: pd.DataFrame) -> pd.Series:
    """逐個細學類判斷 109 學年的一般生人數是否明顯偏低。"""
    p = df.pivot_table(index="代碼", columns="學年度", values="一般生在學數")
    if not {108, 110, SUSPECT_YEAR} <= set(p.columns):
        return pd.Series(False, index=df.index)
    expected = (p[108] + p[110]) / 2
    ratio = p[SUSPECT_YEAR] / expected.replace(0, float("nan"))
    suspect = set(ratio[ratio < SUSPECT_RATIO].index)
    return (df["學年度"] == SUSPECT_YEAR) & df["代碼"].isin(suspect)


def build() -> pd.DataFrame:
    df = load().sort_values(["代碼", "學年度"])
    df["分母異常"] = flag_suspect(df)

    base = df[df["學年度"] == BASE_YEAR].set_index("代碼")
    for who in ("原民", "一般生"):
        col = f"{who}在學數"
        b = df["代碼"].map(base[col]).astype(float).replace(0, float("nan"))
        df[f"{who}指數"] = (df[col] / b * 100).round(1)
    # 分母有缺漏的那一年不畫，留白讓折線斷開，不要用內插假裝有值
    df.loc[df["分母異常"], ["一般生指數", "一般生在學數"]] = pd.NA

    keep = ["學年度", "代碼", "名稱", "原民在學數", "一般生在學數",
            "原民指數", "一般生指數", "相對倍數", "分母異常"]
    return df[keep]


def classify(df: pd.DataFrame) -> pd.DataFrame:
    """依 106→114 兩群人的增減方向分四類，看趨勢是同向還是背道而馳。"""
    last = df["學年度"].max()
    a = df[df["學年度"] == BASE_YEAR].set_index("代碼")
    b = df[df["學年度"] == last].set_index("代碼")
    keep = a.index.intersection(b.index)
    out = pd.DataFrame({
        "名稱": b.loc[keep, "名稱"],
        "原民114": b.loc[keep, "原民在學數"],
        "原民指數": b.loc[keep, "原民指數"],
        "一般生指數": b.loc[keep, "一般生指數"],
    }).dropna()
    out["型態"] = [
        ("原民增・一般增" if g >= 100 else "原民增・一般減") if i >= 100
        else ("原民減・一般增" if g >= 100 else "原民減・一般減")
        for i, g in zip(out["原民指數"], out["一般生指數"])
    ]
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    df = build()
    df.to_csv(OUT / "trend_major.csv", index=False, encoding="utf-8-sig")
    n_flag = int(df["分母異常"].sum())
    print(f"trend_major.csv  {len(df):,} 列，{df['代碼'].nunique()} 個細學類"
          f"（{n_flag} 個類別的 109 學年分母有缺漏，已留白）")
    if n_flag:
        names = df.loc[df["分母異常"], "名稱"].str.replace("細學類", "", regex=False)
        print("  留白：" + "、".join(sorted(names)))

    c = classify(df)
    print("\n106 → 114 增減型態（細學類，以 200 人以上者為主）")
    big = c[c["原民114"] >= 200]
    for name, grp in big.groupby("型態"):
        print(f"  {name}　{len(grp)} 類：" +
              "、".join(grp.sort_values("原民114", ascending=False)["名稱"]
                        .str.replace("細學類", "", regex=False).head(6)))


if __name__ == "__main__":
    main()
