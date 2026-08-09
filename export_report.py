"""把 out/ 的表整理成報告頁要用的 JSON（out/report_data.json）。"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "out"
DOCS = ROOT / "docs"

PAGE = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="原住民學生與一般生在大專科系的結構差異與 106–114 學年增減趨勢。資料來源：教育部統計處。">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>%F0%9F%93%8A</text></svg>">
</head>
<body>
{body}
</body>
</html>
"""

# 相對倍數趨勢圖挑的學門：兩個過度集中、兩個明顯不足，故事最清楚
TREND_FIELDS = ["社會福利學門", "教育學門", "資訊通訊科技學門", "工程及工程業學門"]


def totals(field: pd.DataFrame) -> dict:
    t = field.groupby("學年度")[["原民在學數", "一般生在學數"]].sum()
    t["原民占比"] = t["原民在學數"] / (t["原民在學數"] + t["一般生在學數"])
    first, last = t.index.min(), t.index.max()
    return {
        "years": [int(y) for y in t.index],
        "原民": [int(v) for v in t["原民在學數"]],
        "一般生": [int(v) for v in t["一般生在學數"]],
        "原民占比": [round(float(v), 5) for v in t["原民占比"]],
        "first_year": int(first),
        "last_year": int(last),
        "原民成長率": round(float(t.loc[last, "原民在學數"] / t.loc[first, "原民在學數"] - 1), 4),
        "一般生成長率": round(float(t.loc[last, "一般生在學數"] / t.loc[first, "一般生在學數"] - 1), 4),
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    field = pd.read_csv(OUT / "compare_field.csv", dtype={"代碼": str})
    field = field[(field["等級別"] == "總計") & field["可比"]]
    last = int(field["學年度"].max())

    cur = field[field["學年度"] == last].sort_values("結構差距_百分點", ascending=False)
    gap = [
        {
            "name": r["名稱"].replace("學門", ""),
            "ind": round(r["原民結構占比"] * 100, 2),
            "gen": round(r["一般生結構占比"] * 100, 2),
            "gap": round(r["結構差距_百分點"], 2),
            "ratio": round(r["相對倍數"], 2),
            "n": int(r["原民在學數"]),
        }
        for _, r in cur.iterrows()
    ]

    trend = {}
    for name in TREND_FIELDS:
        s = field[field["名稱"] == name].sort_values("學年度")
        trend[name.replace("學門", "")] = [round(float(v), 3) for v in s["相對倍數"]]

    growth = pd.read_csv(OUT / "growth_field.csv")
    shift = [
        {
            "name": r["名稱"].replace("學門", ""),
            "d": round(r["相對倍數變化"], 2),
            "a": round(r["相對倍數_106"], 2),
            "b": round(r["相對倍數_114"], 2),
            "ind_g": round(r["原民_成長率"] * 100, 1),
            "gen_g": round(r["一般生_成長率"] * 100, 1),
        }
        for _, r in growth.sort_values("相對倍數變化", ascending=False).iterrows()
    ]

    gmajor = pd.read_csv(OUT / "growth_major.csv")
    gmajor = gmajor[gmajor["原民_114"] >= 200].copy()
    major = [
        {
            "name": r["名稱"].replace("細學類", ""),
            "n06": int(r["原民_106"]),
            "n14": int(r["原民_114"]),
            "ind_g": round(r["原民_成長率"] * 100, 1),
            "gen_g": round(r["一般生_成長率"] * 100, 1),
            "a": round(r["相對倍數_106"], 2),
            "b": round(r["相對倍數_114"], 2),
            "d": round(r["相對倍數變化"], 2),
        }
        for _, r in gmajor.sort_values("原民_114", ascending=False).iterrows()
    ]

    # 小倍數圖：原民生最多的 12 個細學類，兩群人各自的指數走勢
    tr = pd.read_csv(OUT / "trend_major.csv", dtype={"代碼": str})
    top = tr[tr["學年度"] == tr["學年度"].max()].nlargest(12, "原民在學數")["代碼"]
    panels = []
    for code in top:
        s = tr[tr["代碼"] == code].sort_values("學年度")
        panels.append({
            "name": s["名稱"].iloc[-1].replace("細學類", ""),
            "n": int(s["原民在學數"].iloc[-1]),
            "ind": [round(float(v), 1) for v in s["原民指數"]],
            "gen": [None if pd.isna(v) else round(float(v), 1) for v in s["一般生指數"]],
        })

    data = {
        "panels": {"years": [int(y) for y in sorted(tr["學年度"].unique())], "items": panels},
        "totals": totals(field),
        "gap": gap,
        "trend": {"years": totals(field)["years"], "series": trend},
        "shift": shift,
        "major": major,
    }
    path = OUT / "report_data.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    # 把資料塞進報告頁模板。模板本身沒有 doctype／head，是給 Artifact 用的片段；
    # GitHub Pages 需要完整文件，尤其是 meta charset，少了中文會變亂碼。
    html = (ROOT / "report_template.html").read_text(encoding="utf-8")
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    fragment = html.replace("__DATA__", compact)
    (OUT / "report.html").write_text(fragment, encoding="utf-8")

    DOCS.mkdir(exist_ok=True)
    # 用 replace 不用 format：片段裡滿是 CSS／JS 的大括號，format 會直接爆掉
    (DOCS / "index.html").write_text(PAGE.replace("{body}", fragment), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    print(f"{path.name}：{len(gap)} 學門、{len(major)} 細學類（原民≥200 人）")
    print("report.html / docs/index.html：已套入模板")


if __name__ == "__main__":
    main()
