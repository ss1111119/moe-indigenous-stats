"""產生 GitHub Pages 站台：docs/index.html ＋ docs/data/*.json。

頁面在瀏覽器端 fetch 這些 JSON，所以資料換版時只有 JSON 檔會變動，
git diff 乾淨，而且那些 JSON 本身就能被別人當現成的資料端點使用。

送出的是原始人數，占比、指數、相對倍數一律在前端算——這樣等級別切換器
換到任何一個學制，所有圖表都用同一套公式重算，口徑不會分岔。

因為要 fetch，本機預覽不能直接開 file://，要起一個 server：
    python -m http.server -d docs 8000
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "out"
DOCS = ROOT / "docs"

LEVELS = ["總計", "博士班", "碩士班", "學士班", "二專", "五專"]

# 軌跡圖預設挑的學門：兩個過度集中、兩個明顯不足，故事最清楚
TREND_FIELDS = ["社會福利", "教育", "資訊通訊科技", "工程及工程業"]


def suspect_codes(df: pd.DataFrame) -> set:
    """找出 109 學年一般生人數明顯低於 108／110 內插值的類別。

    sdata 109 年整體短少 4.4%，但集中在少數類別，逐類判斷比整年作廢精準。
    """
    p = df[df["等級別"] == "總計"].pivot_table(
        index="代碼", columns="學年度", values="一般生在學數")
    if not {108, 109, 110} <= set(p.columns):
        return set()
    ratio = p[109] / ((p[108] + p[110]) / 2).replace(0, float("nan"))
    return set(ratio[ratio < 0.9].index)


def pack_categories(df: pd.DataFrame, strip: str) -> list:
    """打包成 [{c 代碼, n 名稱, cmp 可比, d {等級別: [原民[], 一般生[]]}}]。

    109 分母有缺漏的類別，其一般生數值送 null，前端畫線時斷開、算占比時跳過。
    """
    bad = suspect_codes(df)
    out = []
    for code, g in df.groupby("代碼"):
        rec = {"c": code, "n": g["名稱"].iloc[-1].replace(strip, ""),
               "cmp": 1 if bool(g["可比"].iloc[-1]) else 0, "d": {}}
        for lv in LEVELS:
            s = g[g["等級別"] == lv].sort_values("學年度")
            if s.empty:
                continue
            rec["d"][lv] = [
                [int(v) for v in s["原民在學數"].fillna(0)],
                [None if (pd.isna(v) or (code in bad and y == 109)) else int(v)
                 for v, y in zip(s["一般生在學數"], s["學年度"])],
            ]
        out.append(rec)
    return sorted(out, key=lambda r: r["c"])


def pack_schools() -> dict:
    """校別：每校每等級別的原民與全體人數，附全國占比對照。"""
    s = pd.read_csv(OUT / "compare_by_school.csv", dtype={"學校代碼": str})
    s = s[s["原住民在學數"] > 0]
    years = sorted(int(y) for y in s["學年度"].unique())
    idx = {y: i for i, y in enumerate(years)}

    schools = {}
    for (code, name), g in s.groupby(["學校代碼", "學校名稱"]):
        rec = schools.setdefault(
            code, {"c": code, "n": name, "t": g["學校類別"].iloc[-1], "d": {}})
        for lv, gl in g.groupby("等級別"):
            ind, tot = [0] * len(years), [None] * len(years)
            for r in gl.itertuples():
                i = idx[int(r.學年度)]
                ind[i] = int(r.原住民在學數)
                tot[i] = None if pd.isna(r.全體在學數) else int(r.全體在學數)
            rec["d"][lv] = [ind, tot]

    nat = pd.read_csv(OUT / "compare_national.csv")
    ref = {}
    for lv, g in nat.groupby("等級別"):
        g = g.set_index("學年度")
        ref[lv] = [None if y not in g.index else round(float(g.loc[y, "原住民佔比"]), 5)
                   for y in years]

    return {"years": years, "ref": ref,
            "items": sorted(schools.values(), key=lambda r: r["n"])}


def pack_gender() -> dict:
    """性別：每個等級別逐年的原民／一般生男女人數（104–114 學年）。"""
    g = pd.read_csv(OUT / "gender.csv")
    years = sorted(int(y) for y in g["學年度"].unique())
    order = ["博士班", "碩士班", "學士班", "二專", "五專"]
    items = []
    for lv in order:
        s = g[g["等級別"] == lv].set_index("學年度")
        if s.empty:
            continue
        items.append({
            "lv": lv,
            "im": [int(s.loc[y, "原民_男"]) for y in years],
            "if_": [int(s.loc[y, "原民_女"]) for y in years],
            "gm": [int(s.loc[y, "一般生_男"]) for y in years],
            "gf": [int(s.loc[y, "一般生_女"]) for y in years],
        })
    return {"years": years, "items": items}


def totals(field: pd.DataFrame) -> dict:
    f = field[(field["等級別"] == "總計") & field["可比"]]
    t = f.groupby("學年度")[["原民在學數", "一般生在學數"]].sum()
    t["占比"] = t["原民在學數"] / (t["原民在學數"] + t["一般生在學數"])
    first, last = t.index.min(), t.index.max()
    return {
        "years": [int(y) for y in t.index],
        "ind": [int(v) for v in t["原民在學數"]],
        "gen": [int(v) for v in t["一般生在學數"]],
        "share": [round(float(v), 5) for v in t["占比"]],
        "indGrowth": round(float(t.loc[last, "原民在學數"] / t.loc[first, "原民在學數"] - 1), 4),
        "genGrowth": round(float(t.loc[last, "一般生在學數"] / t.loc[first, "一般生在學數"] - 1), 4),
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    field = pd.read_csv(OUT / "compare_field.csv", dtype={"代碼": str})
    major = pd.read_csv(OUT / "compare_major.csv", dtype={"代碼": str})
    years = [int(y) for y in sorted(field["學年度"].unique())]

    files = {
        "narrative.json": {"totals": totals(field), "trendFields": TREND_FIELDS},
        "fields.json": {"years": years, "levels": LEVELS,
                        "items": pack_categories(field, "學門")},
        "majors.json": {"years": years, "levels": LEVELS,
                        "items": pack_categories(major, "細學類")},
        "schools.json": pack_schools(),
        "gender.json": pack_gender(),
    }

    DOCS.mkdir(exist_ok=True)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "index.html").write_text(
        (ROOT / "report_template.html").read_text(encoding="utf-8"), encoding="utf-8")

    for name, obj in files.items():
        blob = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        (DOCS / "data" / name).write_text(blob, encoding="utf-8")
        print(f"  docs/data/{name:<15} {len(blob.encode())/1024:6.0f} KB")

    print(f"docs/index.html：{len(files['fields.json']['items'])} 學門、"
          f"{len(files['majors.json']['items'])} 細學類、"
          f"{len(files['schools.json']['items'])} 所學校")


if __name__ == "__main__":
    main()
