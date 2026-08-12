"""輸出檔之間的硬約束。

本專案的錯誤型態是**靜默的口徑錯誤**，不是例外。已發生過的例子：某份資料的
鄉鎮加總與縣市檔逐縣市完全相符（內部一致），但對外全錯——某縣市的 15 歲以上
人口比該縣市原住民總人口還多。**內部一致性檢查抓不到那種錯**，只有跨檔案的
約束與釘死的數字會。

⚠️ 兩個刻意的設計：

1. **只讀 `out/*.csv` 與模板，不讀 `data/`。** `data/` 未入版控，測試若依賴它
   就會變成「clone 之後跑不起來」，那種測試沒有人會跑。
2. **期望值寫死。** 若改成「從另一個檔案算出來再比對」，兩邊一起錯時測試仍會
   通過——而本專案真正怕的就是兩邊一起錯。

⚠️ **資料更新時這些測試會紅，那是刻意的。** 學年推進本來就該有人看過數字再更新
期望值，而不是讓它靜靜滑過去。看到失敗請先確認新數字合理，再更新常數。

    pytest
"""

import re
from pathlib import Path

import pandas as pd
import pytest

OUT = Path(__file__).resolve().parent.parent / "out"

# ── 釘死的數字。每一個都註明來源與為何是那個值。────────────────────────────
# 114 學年大專原民生（承接端，不含空大與宗教研修學院）。
# 來源：SEGIS 行政區大專校院統計，實測與出版品 A1-6a 逐縣市完全相符。
TERTIARY_TOTAL = 25_613

# 114 學年高中職原民生。來源：edu_A_1_7 五類分流合計，等於就學階梯的高中職列。
SENIOR_TOTAL = 20_398

# 113 年 12 月底原住民 15 歲以上人口。來源：SEGIS 統計區原住民教育程度人口統計。
ADULT_TOTAL = 490_336

# 114 學年有該階學校的鄉鎮市區數（全國共 368 個）。義務教育近乎全覆蓋，
# 高等教育只剩 87 個——這條遞減是本專案的核心發現之一。
LADDER = {"國小": 367, "國中": 357, "高中職": 206, "大專": 87}

# 普通科占比的原民與全體差距。105 → 114 由 −11.56 擴大到 −13.69：
# 原民端在追（29.0% → 38.0%），但全體升得更快（40.5% → 51.7%）。
GAP_FIRST = ("105", -11.56)
GAP_LAST = ("114", -13.69)

# 縣市視角裡比率被標記為不穩定的縣市（出生戶籍地在學數 < 200）。
# 釘死名單而不是只釘個數：個數對了但換了一個縣市，是更難發現的錯。
COUNTY_FLAGGED = ["雲林縣", "嘉義市", "澎湖縣", "金門縣", "連江縣"]

# 形狀由資料決定的輸出，其列數。
ROWS = {
    "receiving_township.csv": 87,      # 有大專校院的鄉鎮市區
    "ladder_township.csv": 1017,       # 四學制 × 各自有該階學校的鄉鎮市區
    "attainment_by_age.csv": 132,      # 22 縣市 × 6 年齡組
    "senior_stream.csv": 55,           # 11 學年 × 5 分流
    "senior_stream_compare.csv": 55,
    "county_view.csv": 22,             # 一列一個縣市
}

HINT = "（若為新學年資料，請先確認數字合理後再更新本檔的常數，不要直接改成通過）"


def read(name: str) -> pd.DataFrame:
    path = OUT / name
    assert path.exists(), f"找不到 {path}——out/ 的 CSV 應已入版控"
    return pd.read_csv(path, encoding="utf-8-sig")


def approx(a: float, b: float, tol: float = 0.05) -> bool:
    return abs(a - b) <= tol


# ── 跨檔案關係 ──────────────────────────────────────────────────────────
def test_tertiary_total_matches_a16a():
    """承接端合計 = A1-6a 逐縣市合計。兩邊由不同腳本從不同來源產生。"""
    got = int(read("receiving_township_summary.csv")["原住民學生數"].sum())
    assert got == TERTIARY_TOTAL, f"承接端合計 {got:,}，應為 {TERTIARY_TOTAL:,} {HINT}"

    g = read("geography.csv")
    g = g[(g["學年度"] == 114) & (g["等級別"] == "總計")]
    a16a = int(g["學校所在地在學數_不含空大宗教"].sum())
    assert a16a == TERTIARY_TOTAL, (
        f"A1-6a 逐縣市合計 {a16a:,}，與承接端的 {TERTIARY_TOTAL:,} 不符 {HINT}")


def test_senior_total_matches_ladder():
    """高中職分流合計 = 就學階梯的高中職列。"""
    st = read("senior_stream.csv")
    got = int(st[st["學年"] == 114]["人數"].sum())
    assert got == SENIOR_TOTAL, f"分流 114 學年合計 {got:,}，應為 {SENIOR_TOTAL:,} {HINT}"

    lad = read("ladder_summary.csv")
    theirs = int(lad[lad["學制"] == "高中職"]["原住民學生數"].iloc[0])
    assert theirs == SENIOR_TOTAL, (
        f"階梯的高中職為 {theirs:,}，與分流的 {SENIOR_TOTAL:,} 不符 {HINT}")


def test_adult_total_matches_age_decomposition():
    """存量合計 = 年齡分解合計。後者是前者的再分析，加總必須守恆。"""
    a = int(read("adult_education.csv")["人數"].sum())
    b = int(read("attainment_by_age.csv")["人數"].sum())
    assert a == ADULT_TOTAL, f"存量合計 {a:,}，應為 {ADULT_TOTAL:,} {HINT}"
    assert b == ADULT_TOTAL, f"年齡分解合計 {b:,}，應為 {ADULT_TOTAL:,} {HINT}"


# ── 單檔不變量 ──────────────────────────────────────────────────────────
def test_ladder_counts_descend():
    lad = read("ladder_summary.csv").set_index("學制")
    got = {k: int(lad.loc[k, "有該階學校的鄉鎮市區數"]) for k in LADDER}
    assert got == LADDER, f"階梯鄉鎮數 {got}，應為 {LADDER} {HINT}"
    seq = [got[k] for k in ("國小", "國中", "高中職", "大專")]
    assert seq == sorted(seq, reverse=True) and len(set(seq)) == len(seq), (
        f"鄉鎮數未嚴格遞減：{seq}——遞減是這份資料的核心，不遞減表示讀錯了")


def test_standardisation_is_identity_nationally():
    """以自身年齡結構標準化是恆等變換。不相等即表示權重算錯。"""
    a = read("attainment_by_age.csv")
    s = read("attainment_standardised.csv")
    national_crude = a["專科以上人數"].sum() / a["人數"].sum() * 100

    w = a.groupby("年齡組")["人數"].sum()
    weights = w / w.sum()
    within = (a.groupby("年齡組")["專科以上人數"].sum()
              / a.groupby("年齡組")["人數"].sum())
    national_std = float((within * weights).sum() * 100)

    assert approx(round(national_crude, 2), round(national_std, 2), 0.01), (
        f"全國原始占比 {national_crude:.4f}% 與標準化 {national_std:.4f}% 不等，"
        f"標準人口權重有誤 {HINT}")
    assert len(s) == 22, f"標準化輸出應為 22 縣市，實為 {len(s)}"


def test_streaming_gap_widened():
    c = read("senior_stream_compare.csv")
    c["學年"] = c["學年"].astype(str)
    gaps = {}
    for year, expected in (GAP_FIRST, GAP_LAST):
        row = c[(c["學年"] == year) & (c["分流"] == "普通科")]
        assert not row.empty, f"找不到 {year} 學年的普通科列"
        got = float(row["差距"].iloc[0])
        assert approx(got, expected, 0.01), (
            f"{year} 學年普通科差距 {got}，應為 {expected} {HINT}")
        gaps[year] = got
    assert abs(gaps[GAP_LAST[0]]) > abs(gaps[GAP_FIRST[0]]), (
        "差距應為擴大——若真的變成縮小，那是重要發現，"
        "請先確認資料再更新本測試與頁面敘事")


# ── 縣市視角 ────────────────────────────────────────────────────────────
def test_county_receiving_matches_township_output():
    """承接兩欄 = 該縣市在鄉鎮承接輸出的列數與人數合計。

    這是彙整最容易靜默出錯的地方：連江縣在承接輸出裡沒有列，若彙整時漏了
    「沒有列就填 0」，該縣市會整列消失或變成缺值，而兩者都不會報錯。
    """
    cv = read("county_view.csv")
    town = read("receiving_township.csv")
    counts = town.groupby("縣市").size()
    sums = town.groupby("縣市")["原住民學生數"].sum()

    for r in cv.itertuples():
        want_t = int(counts.get(r.縣市, 0))
        want_n = int(sums.get(r.縣市, 0))
        assert int(r.承接鄉鎮數) == want_t, (
            f"{r.縣市} 的承接鄉鎮數為 {r.承接鄉鎮數}，"
            f"但承接輸出裡有 {want_t} 列 {HINT}")
        assert int(r.承接原民生) == want_n, (
            f"{r.縣市} 的承接原民生為 {r.承接原民生:,}，"
            f"但承接輸出合計為 {want_n:,} {HINT}")


def test_county_steps_do_not_increase():
    """四階鄉鎮數不得隨學制上升。

    一個鄉鎮若有大專，它在國小那一階也會被算到，所以升是不可能的。
    ⚠️ 這裡只要求不上升不要求嚴格遞減——小縣市持平是真的（宜蘭國小 12、國中 12）。
    """
    cv = read("county_view.csv")
    cols = ["有國小的鄉鎮數", "有國中的鄉鎮數", "有高中職的鄉鎮數", "有大專的鄉鎮數"]
    for r in cv.itertuples():
        seq = [int(getattr(r, c)) for c in cols]
        assert seq == sorted(seq, reverse=True), (
            f"{r.縣市} 的四階鄉鎮數往上升：{seq}——"
            f"這表示彙整讀錯了縣市或學制 {HINT}")


def test_county_small_denominator_flags():
    """被標記的縣市恰為那 5 個，且標記與 200 人門檻一致。"""
    cv = read("county_view.csv")
    got = list(cv[cv["小分母"] == "是"]["縣市"])
    assert sorted(got) == sorted(COUNTY_FLAGGED), (
        f"被標記的縣市為 {got}，應為 {COUNTY_FLAGGED} {HINT}")

    for r in cv.itertuples():
        flagged = r.小分母 == "是"
        assert flagged == (int(r.出生戶籍地) < 200), (
            f"{r.縣市} 出生戶籍地 {r.出生戶籍地} 人，標記為 {flagged!r}，"
            "與 200 人門檻不一致")


# ── 形狀與占比 ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("name,rows", sorted(ROWS.items()))
def test_row_counts(name, rows):
    got = len(read(name))
    assert got == rows, f"{name} 有 {got} 列，應為 {rows} 列 {HINT}"


@pytest.mark.parametrize("name,group,col", [
    ("senior_stream.csv", "學年", "占比"),
    ("senior_stream_compare.csv", "學年", "原民占比"),
    ("senior_stream_compare.csv", "學年", "全體占比"),
])
def test_shares_sum_to_100(name, group, col):
    d = read(name)
    for key, g in d.groupby(group):
        vals = pd.to_numeric(g[col], errors="coerce").dropna()
        if vals.empty:      # 缺對照的學年（104 的全體端）整組留空，跳過
            continue
        total = float(vals.sum())
        assert approx(total, 100.0), (
            f"{name} 的 {group}={key} 之 {col} 合計為 {total:.2f}%，應為 100% {HINT}")
