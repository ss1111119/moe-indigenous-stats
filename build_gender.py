"""性別結構：原住民學生 vs 一般生，104–114 學年。

原民端用 opendata 的 A2-3（按年級別、等級別與性別分），全體端用校別學生數的
男生計／女生計。兩邊都只含「大專校院」，不含空大、進修學校與宗教研修學院，
所以這裡的口徑比學門分析乾淨——沒有分子分母範圍不一致的問題。

性別只交叉到等級別。出版品的 A1-3（學門）與 A1-4（科系）都沒有性別欄，
所以「原民生念什麼科系、男女差在哪」在公開資料裡做不出來。

輸出 out/gender.csv。
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "out"

GRADES = ["一年級", "二年級", "三年級", "四年級", "五年級", "六年級", "七年級"]

# A2-3 的等級別用詞逐年變動，收斂成 5 個桶（與其他腳本一致）
A23_LEVEL = {
    "博士班": "博士班", "碩士班": "碩士班", "學士班": "學士班",
    "大學四年制": "學士班", "大學四年制(或四技)": "學士班",
    "大學二年制(或二技)": "學士班", "二技": "學士班", "4+X": "學士班",
    "二專": "二專", "五專": "五專",
}
LEVEL_FROM_CODE = {"D": "博士班", "M": "碩士班", "B": "學士班",
                   "C": "學士班", "X": "學士班", "2": "二專", "5": "五專"}


def indigenous() -> pd.DataFrame:
    d = pd.read_json(DATA / "indigenous_students_A2-3.json", dtype=str)
    d = d[d["學校類別"] == "大專校院"].copy()
    d["等級別"] = d["等級別"].map(A23_LEVEL)
    d = d[d["等級別"].notna()]
    d["學年度"] = d["學年度"].astype(int)
    cols = [f"{g}學生人數" for g in GRADES] + ["延修生學生人數"]
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d["原民"] = d[cols].sum(axis=1)
    return d.pivot_table(index=["學年度", "等級別", "性別"],
                         values="原民", aggfunc="sum").reset_index()


def everyone() -> pd.DataFrame:
    a = pd.concat(
        [pd.read_json(DATA / f"{n}.json", dtype=str, encoding="utf-8-sig")
         for n in ("103-112_student", "student")], ignore_index=True)
    a["學年度"] = a["學年度"].astype(int)
    a["等級別"] = a["等級別"].str[0].map(LEVEL_FROM_CODE)
    a = a[a["等級別"].notna()]
    out = []
    for sex in ("男", "女"):
        t = a.copy()
        t["全體"] = pd.to_numeric(t[f"{sex}生計"], errors="coerce").fillna(0)
        t["性別"] = sex
        out.append(t[["學年度", "等級別", "性別", "全體"]])
    return pd.concat(out).groupby(["學年度", "等級別", "性別"],
                                  as_index=False)["全體"].sum()


def build() -> pd.DataFrame:
    m = indigenous().merge(everyone(), on=["學年度", "等級別", "性別"], how="inner")
    m["一般生"] = m["全體"] - m["原民"]
    wide = m.pivot_table(index=["學年度", "等級別"], columns="性別",
                         values=["原民", "一般生"]).fillna(0).astype(int)
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    wide["原民女比"] = (wide["原民_女"] / (wide["原民_男"] + wide["原民_女"]) * 100).round(2)
    wide["一般生女比"] = (wide["一般生_女"] / (wide["一般生_男"] + wide["一般生_女"]) * 100).round(2)
    wide["差距_百分點"] = (wide["原民女比"] - wide["一般生女比"]).round(2)
    return wide.reset_index()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(exist_ok=True)
    df = build()
    df.to_csv(OUT / "gender.csv", index=False, encoding="utf-8-sig")
    years = sorted(df["學年度"].unique())
    print(f"gender.csv  {len(df)} 列，{years[0]}–{years[-1]} 學年 × "
          f"{df['等級別'].nunique()} 個等級別")

    last = years[-1]
    cur = df[df["學年度"] == last].set_index("等級別")
    print(f"\n{last} 學年 女性占比")
    print(cur[["原民_男", "原民_女", "原民女比", "一般生女比", "差距_百分點"]].to_string())


if __name__ == "__main__":
    main()
