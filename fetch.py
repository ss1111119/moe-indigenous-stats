"""抓取教育部統計處「原住民學生」開放資料。

資料來源為靜態 JSON/CSV 檔，非查詢式 API，每學年更新一次。
用法：
    python fetch.py            # 全部抓一遍，存到 data/
    python fetch.py A2-3       # 只抓指定 key
"""

import json
import ssl
import sys
import urllib.request
from pathlib import Path

BASE = "https://stats.moe.gov.tw/files/opendata"
DATA_DIR = Path(__file__).parent / "data"

# stats.moe.gov.tw 的憑證缺 Subject Key Identifier，新版 OpenSSL 會拒絕，
# 只好關掉驗證。這裡抓的是公開統計檔，沒有機敏內容，風險僅止於內容遭竄改。
SSL_CTX = ssl._create_unverified_context()

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")

# key -> (檔名, 說明)
DATASETS = {
    "A1-1": (
        "indigenous_students_A1-1",
        "大專校院原住民學生數—按校別分（含學校代碼、各等級在學與畢業人數）",
    ),
    "A2-3": (
        "indigenous_students_A2-3",
        "大專校院原住民學生及畢業生人數—按年級別、等級別與性別分",
    ),
    "A_1_7": (
        "edu_A_1_7",
        "各級學校原住民學生概況—按設立別（幼兒園至博士班）",
    ),
    # ↓ 分母：全體（一般生＋原住民生）大專校院學生數
    "student": (
        "student",
        "大專院校校別學生數—當學年度（按校、日間∕進修、等級、年級、性別）",
    ),
    "student_hist": (
        "103-112_student",
        "大專院校校別學生數—103～112 學年度歷年檔",
    ),
    "graduate": (
        "graduate",
        "大專校院校別畢業生人數（上學年度）",
    ),
    "sdata": (
        "sdata",
        "大專校院各校科系別概況（每校每科系每等級的學生數，37MB）",
    ),
}

# 原住民的學門／科系資料只出現在統計出版品裡，沒有 opendata 版本。
# 106～108 是舊版 .xls，109 起改 .xlsx；sheet A1-3（學門）、A1-4（科系）名稱穩定。
EBOOK_BASE = "https://stats.moe.gov.tw/files/ebook/indigenous"
EBOOK_YEARS = range(106, 115)

# 對應的政府資料開放平臺 dataset id，可查後設資料
DATA_GOV_IDS = {
    "A1-1": 33513,
    "A2-3": 33513,
    "A_1_7": 40117,
    "student": 6231,
    "student_hist": 6231,
    "graduate": 6235,
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as resp:
        return resp.read()


def save(key: str) -> None:
    stem, desc = DATASETS[key]
    DATA_DIR.mkdir(exist_ok=True)
    for ext in ("json", "csv"):
        url = f"{BASE}/{stem}.{ext}"
        try:
            body = fetch(url)
        except Exception as exc:  # 有些資料集只提供其中一種格式
            print(f"  ! {ext:4} 失敗 {exc}")
            continue
        out = DATA_DIR / f"{stem}.{ext}"
        out.write_bytes(body)
        note = ""
        if ext == "json":
            rows = json.loads(body)
            note = f"，{len(rows)} 筆，欄位 {len(rows[0])} 個"
        print(f"  + {out.name} ({len(body):,} bytes{note})")


def save_ebooks() -> None:
    out_dir = DATA_DIR / "ebook"
    out_dir.mkdir(parents=True, exist_ok=True)
    for year in EBOOK_YEARS:
        ext = "xls" if year <= 108 else "xlsx"
        out = out_dir / f"{year}indigenous.{ext}"
        if out.exists():
            print(f"  = {out.name}（已存在）")
            continue
        try:
            body = fetch(f"{EBOOK_BASE}/{year}/{year}indigenous.{ext}")
        except Exception as exc:
            print(f"  ! {year} 失敗 {exc}")
            continue
        out.write_bytes(body)
        print(f"  + {out.name} ({len(body):,} bytes)")


def main() -> None:
    keys = sys.argv[1:] or list(DATASETS)
    if "ebooks" in keys:
        print("原住民學生概況統計出版品（學門／科系用）")
        save_ebooks()
        keys = [k for k in keys if k != "ebooks"]
    for key in keys:
        if key not in DATASETS:
            print(f"未知的 key: {key}（可用：{', '.join(DATASETS)}）")
            continue
        print(f"{key} — {DATASETS[key][1]}")
        save(key)


if __name__ == "__main__":
    main()
