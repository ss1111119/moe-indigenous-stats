"""報告頁必須如實描述自己。

2026-08-11 一天內給「縣市」頁加了五個區塊，開場白卻還寫著「這一頁把**三件事**
放在一起看」，byline 的來源也只剩最早那兩個。**讀者最先看到的兩段文字，
描述的是一個已經不存在的頁面。** 這支測試就是為了讓那件事下次自動現形。

⚠️ 刻意**不做全文比對**——那會讓任何文案潤飾都變成測試失敗，很快就會養成
「先改測試」的習慣而失去意義。只釘住兩件會因新增區塊而過期的事：
開場白宣稱的數量、以及 byline 是否涵蓋所有來源。

    pytest
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# 中文數字 → 阿拉伯數字。開場白若寫「把三件事放在一起看」而頁面有 10 個區塊，
# 就是過期了。
CN_NUM = {"一": 1, "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

# 頁面目前的區塊。釘死它是為了讓「新增區塊」這件事本身觸發失敗——
# ⚠️ 光檢查「開場白宣稱的數量」不夠：開場白若寫成不含數字的句子，那條斷言
# 就變成空的，加了區塊也不會紅。實測過這個漏洞，所以改成連清單一起釘。
# 新增區塊時請一併確認開場白與 byline 是否仍如實描述這一頁，再更新這裡。
SECTIONS = {
    "geography_template.html": [
        "overview", "flow", "trend", "ladder", "stream",
        "town", "stock", "agedec", "link", "caveats",
    ],
}

# 頁面目前用到的來源。新增區塊若引入新來源，這裡與 byline 都要一起加。
SOURCES = {
    "geography_template.html": [
        ("出版品 A1-5／A1-6", r"A1-5"),
        ("各級學校原住民學生概況", r"edu_A_1_7|各級學校原住民學生概況"),
        ("SEGIS 行政區各級學校統計", r"SEGIS|行政區各級學校"),
        ("高中職學程別 base3", r"base3|學程別"),
        ("統計區原住民教育程度", r"教育程度"),
    ],
}


def template(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def sections(html: str) -> list[str]:
    return re.findall(r'<section id="([^"]+)"', html)


def deck(html: str) -> str:
    m = re.search(r'<p class="deck">(.*?)</p>', html, re.S)
    assert m, "找不到 <p class=\"deck\">"
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", m.group(1)))


def byline(html: str) -> str:
    m = re.search(r'<div class="byline">(.*?)</div>', html, re.S)
    assert m, "找不到 <div class=\"byline\">"
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", m.group(1)))


@pytest.mark.parametrize("name", sorted(SECTIONS))
def test_section_list_is_pinned(name):
    """區塊清單釘死。改動它時必須順便確認開場白與 byline 還說得通。"""
    got = sections(template(name))
    assert got == SECTIONS[name], (
        f"{name} 的區塊清單變了。\n  預期：{SECTIONS[name]}\n  實際：{got}\n"
        "新增或移除區塊時，請先確認開場白與 byline 是否仍如實描述這一頁，"
        "再更新本測試的 SECTIONS。不要只改測試讓它通過。")


@pytest.mark.parametrize("name", sorted(SOURCES))
def test_deck_does_not_claim_a_stale_topic_count(name):
    """開場白不得宣稱一個與實際區塊數不符的數量。"""
    html = template(name)
    n = len(sections(html))
    text = deck(html)

    claims = []
    for m in re.finditer(r"把([一二兩三四五六七八九十]+|\d+)(件事|個|項)", text):
        raw = m.group(1)
        claims.append(int(raw) if raw.isdigit() else CN_NUM.get(raw, -1))

    for c in claims:
        assert c == n, (
            f"{name} 的開場白宣稱「{c}」，但頁面實際有 {n} 個區塊。\n"
            "新增或移除區塊時，開場白必須在同一個變更裡一起更新。")


@pytest.mark.parametrize("name", sorted(SOURCES))
def test_byline_names_every_source(name):
    """byline 必須涵蓋頁面用到的每一個來源，比對關鍵字而非全文。"""
    text = byline(template(name))
    missing = [label for label, pat in SOURCES[name]
               if not re.search(pat, text)]
    assert not missing, (
        f"{name} 的 byline 沒有提到這些來源：{missing}\n"
        f"目前 byline：{text}\n"
        "區塊引入新來源時，byline 必須在同一個變更裡一起補上。")
