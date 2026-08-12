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


def pack_ethnicity() -> dict:
    """族籍別：每族逐年的等級別 × 性別人數（104–114 學年）。

    另外附上一般生的學位結構當外部錨點——族籍本身沒有一般生對照，
    但「原民整體 vs 一般生」的落差是讀這一區的必要背景。
    """
    e = pd.read_csv(OUT / "ethnicity.csv")
    years = sorted(int(y) for y in e["學年度"].unique())
    items = []
    for name, g in e[e["族籍別"] != "總計"].groupby("族籍別"):
        d = {}
        for lv, gl in g.groupby("等級別"):
            p = gl.pivot_table(index="學年度", columns="性別", values="在學數",
                               aggfunc="sum").reindex(years).fillna(0)
            d[lv] = [[int(v) for v in p.get("男", 0)], [int(v) for v in p.get("女", 0)]]
        items.append({"n": name, "d": d})
    items.sort(key=lambda r: -sum(x[-1] for x in r["d"]["總計"]))

    nat = pd.read_csv(OUT / "compare_national.csv")
    c = nat[nat["學年度"] == nat["學年度"].max()].set_index("等級別")
    gen = c["全體在學數"] - c["原住民在學數"]
    ref = {
        "genGrad": round(float((gen["博士班"] + gen["碩士班"]) / gen.sum() * 100), 1),
        "gen5": round(float(gen["五專"] / gen.sum() * 100), 1),
    }
    return {"years": years, "items": items, "ref": ref}


def pack_geography() -> dict:
    """縣市頁：流動（出生戶籍地 → 學校所在地）＋ 存量（成年人口學歷結構）。

    ⚠️ 兩塊的基準日不同——流動是學年度，存量是民國 113 年 12 月底的人口統計。
    因此存量不進 `d`（不受等級別／學年度切換影響），另放在 `edu` 底下，
    前端必須各自標明基準日。這不是疏漏，是刻意不讓兩者被同一個控制項帶著跑。
    """
    g = pd.read_csv(OUT / "geography.csv")
    years = sorted(int(y) for y in g["學年度"].unique())
    idx = {y: i for i, y in enumerate(years)}

    # 每個等級別送四條序列：出生戶籍地、學校所在地、學校所在地(A1-6a)、集中倍數。
    # 前兩條是同一母體、可相減；第三條才是能配一般生的那個範圍。集中倍數在建置期
    # 算好而不是丟給前端，因為它的分母是「全國扣掉沒有大專校院的縣市」，
    # 前端從各縣市數字自己加總會得到不同的分母。
    counties = {}
    for name, gc in g.groupby("縣市"):
        rec = counties.setdefault(name, {"n": name, "d": {}})
        for lv, gl in gc.groupby("等級別"):
            birth, school = [0] * len(years), [0] * len(years)
            narrow, conc = [0] * len(years), [None] * len(years)
            for r in gl.itertuples():
                i = idx[int(r.學年度)]
                birth[i] = int(r.出生戶籍地在學數)
                school[i] = int(r.學校所在地在學數)
                narrow[i] = int(r.學校所在地在學數_不含空大宗教)
                conc[i] = None if pd.isna(r.集中倍數) else round(float(r.集中倍數), 3)
            rec["d"][lv] = [birth, school, narrow, conc]

    edu = pd.read_csv(OUT / "adult_education.csv")
    labels = ["博士", "碩士", "大學院校", "專科", "高中職",
              "國中初職", "小學", "自修", "不識字", "未詳"]
    wide = edu.pivot_table(index="縣市", columns="教育程度", values="人數",
                           aggfunc="sum").fillna(0).astype(int)
    items = [{"n": n, "v": [int(wide.loc[n, c]) for c in labels]}
             for n in sorted(wide.index)]

    # 鄉鎮層級承接端。⚠️ 這塊也不進 `d`：它只有一個學年，跟著學年控制項跑會
    # 讓讀者以為切了年份數字有變。學年字樣一律從 CSV 帶出，不寫死——來源端點
    # 回傳的是「平台當下最新一期」，明年會變 115 學年（見 build_receiving.py）。
    town = pd.read_csv(OUT / "receiving_township.csv")
    town_year = str(town["學年"].iloc[0])
    towns = [{
        "c": r.縣市, "n": r.鄉鎮市區,
        "ind": int(r.原住民學生數), "all": int(r.全體學生數),
        "sch": int(r.學校數),
        "sh": None if pd.isna(r.原民生占比) else round(float(r.原民生占比), 5),
        "small": r.分母過小 == "是",
    } for r in town.itertuples()]
    towns.sort(key=lambda t: -t["ind"])

    # 縣市入口。⚠️ 這一份是既有四份輸出的彙整（見 build_county.py），不另行計算——
    # 入口區塊的數字與後面各區必須是同一批數字，否則讀者會以為那是兩份資料。
    # 學年不寫死：county_view.csv 沒有學年欄，改以「出生戶籍地逐縣市與 geography.csv
    # 相符」反推是哪一年。對不上就中止——那表示 build_county.py 的 YEAR 已經落後，
    # 而那種錯不會報錯，只會讓頁面標著今年的學年顯示去年的數字。
    cv = pd.read_csv(OUT / "county_view.csv")
    cv_year = None
    for y in reversed(years):
        ref = g[(g["學年度"] == y) & (g["等級別"] == "總計")].set_index("縣市")
        if len(ref) == len(cv) and all(
                int(ref.loc[r.縣市, "出生戶籍地在學數"]) == int(r.出生戶籍地)
                for r in cv.itertuples()):
            cv_year = y
            break
    if cv_year is None:
        raise SystemExit(
            "county_view.csv 的出生戶籍地對不上 geography.csv 的任何一個學年。\n"
            "請重跑 python build_county.py（並確認其 YEAR 與最新資料一致）。")

    county = {"year": str(cv_year), "items": [{
        "n": r.縣市,
        "birth": int(r.出生戶籍地), "school": int(r.學校所在地),
        "net": int(r.淨流動), "ratio": float(r.就學戶籍比),
        "steps": [int(r.有國小的鄉鎮數), int(r.有國中的鄉鎮數),
                  int(r.有高中職的鄉鎮數), int(r.有大專的鄉鎮數)],
        "recT": int(r.承接鄉鎮數), "recN": int(r.承接原民生),
        "crude": float(r.原始專科以上占比), "std": float(r.年齡標準化占比),
        "small": r.小分母 == "是",
    } for r in cv.itertuples()]}

    # 年齡分解與標準化。⚠️ 原始占比一併送出且不被取代——兩者回答不同問題，
    # 而且既有區塊用的就是原始占比，只送標準化會讓同一頁兩個數字對不上。
    aa = pd.read_csv(OUT / "attainment_by_age.csv")
    ast = pd.read_csv(OUT / "attainment_standardised.csv")
    band_order = ["15-24歲", "25-34歲", "35-44歲", "45-54歲", "55-64歲", "65歲以上"]
    spread = []
    for b in band_order:
        sub = aa[(aa["年齡組"] == b) & (aa["人數過少"] != "是")]["專科以上占比"]
        spread.append(round(float(sub.max() - sub.min()), 1))
    byname = {n: g for n, g in aa.groupby("縣市")}
    ages = [{
        "n": r.縣市,
        "crude": float(r.原始專科以上占比),
        "std": float(r.年齡標準化占比),
        "p65": float(r._8),
        "rk": int(r.原始排名), "rkStd": int(r.標準化排名),
        "weak": r.標準化不穩定 == "是",
        "v": [None if row.人數過少 == "是" else float(row.專科以上占比)
              for row in byname[r.縣市].set_index("年齡組").loc[band_order].itertuples()],
    } for r in ast.itertuples()]

    # 高中職分流。⚠️ 送占比與人數，但頁面只畫占比——總人數十一年間降了 15.7%，
    # 用人數畫線會讓每一類一起往下掉，把「普通科比重上升」這個訊息淹掉。
    st = pd.read_csv(OUT / "senior_stream_compare.csv")
    st["學年"] = st["學年"].astype(str)
    st_years = sorted(st["學年"].unique(), key=int)
    st_names = ["普通科", "綜合高中", "專業群(職業)科", "實用技能學程", "進修部"]

    def cell(y, n, col):
        v = st[(st["學年"] == y) & (st["分流"] == n)][col].iloc[0]
        return None if pd.isna(v) or v == "" else round(float(v), 2)

    stream = {
        "years": st_years, "names": st_names,
        # 三組序列並送。⚠️ 缺對照的學年（104）送 null 而不是 0——
        # 送 0 會在圖上畫成「全體占比是零」，那比不畫更糟。
        "ind": [[cell(y, n, "原民占比") for y in st_years] for n in st_names],
        "gen": [[cell(y, n, "全體占比") for y in st_years] for n in st_names],
        "gap": [[cell(y, n, "差距") for y in st_years] for n in st_names],
        "indN": [[int(st[(st["學年"] == y) & (st["分流"] == n)]["原民人數"].iloc[0])
                  for y in st_years] for n in st_names],
        "total": [int(st[st["學年"] == y]["原民人數"].sum()) for y in st_years],
    }

    # 就學階梯。⚠️ 只送鄉鎮市區數與人數，不送任何跨階相除的結果——
    # 四階是橫斷面不是同一批人，而且年級數不同，相除沒有意義。
    # 前端也不得自行相除，見 geography_template.html 的 ladder()。
    lad = pd.read_csv(OUT / "ladder_summary.csv")
    ladder = [{
        "lv": r.學制,
        "yrs": None if pd.isna(r.年級數) else int(r.年級數),
        "towns": int(r.有該階學校的鄉鎮市區數),
        "townsInd": int(r.有原民生的鄉鎮市區數),
        "ind": int(r.原住民學生數),
    } for r in lad.itertuples()]

    return {
        "years": years, "levels": LEVELS,
        "counties": sorted(counties.values(), key=lambda r: r["n"]),
        "edu": {"period": "民國 113 年 12 月底", "labels": labels, "items": items},
        "age": {
            "bands": band_order, "spread": spread, "items": ages,
            "crudeSpread": round(float(ast["原始專科以上占比"].max()
                                       - ast["原始專科以上占比"].min()), 1),
            "stdSpread": round(float(ast["年齡標準化占比"].max()
                                     - ast["年齡標準化占比"].min()), 1),
        },
        "county": county,
        "ladder": {"year": str(lad["學年"].iloc[0]), "total": 368, "items": ladder},
        "stream": stream,
        "town": {"year": town_year, "items": towns},
    }


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
        "ethnicity.json": pack_ethnicity(),
        "geography.json": pack_geography(),
    }

    # 兩個頁面共用同一份 CSS。抽出來是為了讓配色與元件只有一個定義處——
    # 兩頁各自內嵌一份的話，改了一邊忘了另一邊不會有任何錯誤訊息。
    pages = {"index.html": "report_template.html",
             "geography.html": "geography_template.html"}

    DOCS.mkdir(exist_ok=True)
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "style.css").write_text(
        (ROOT / "site_style.css").read_text(encoding="utf-8"), encoding="utf-8")
    for out_name, src in pages.items():
        (DOCS / out_name).write_text(
            (ROOT / src).read_text(encoding="utf-8"), encoding="utf-8")

    for name, obj in files.items():
        blob = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        (DOCS / "data" / name).write_text(blob, encoding="utf-8")
        print(f"  docs/data/{name:<15} {len(blob.encode())/1024:6.0f} KB")

    print(f"docs/index.html：{len(files['fields.json']['items'])} 學門、"
          f"{len(files['majors.json']['items'])} 細學類、"
          f"{len(files['schools.json']['items'])} 所學校")


if __name__ == "__main__":
    main()
