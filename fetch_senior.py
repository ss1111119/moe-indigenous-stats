"""抓取教育部統計處《高級中等學校校別資料檔－按學程別分》（`base3`），105–114 學年。

這是原民生分流的**一般生對照**。`build_stream.py` 原本只有原民端，因為當時找不到
全體學生的高中職學程別資料；來源就在教育部統計處的「學校基本統計資訊」頁，
不在 opendata 目錄下。

網址：`https://stats.moe.gov.tw/files/detail/<學年>/<學年>_base3.<csv|xlsx>`

⚠️ **這份資料的格式逐年不同**，實測結果：

| 項目 | 105–110 | 111–113 | 114 |
| --- | --- | --- | --- |
| 格式 | 只有 CSV | CSV 與 XLSX 皆有 | 只有 XLSX |
| 學生數欄 | 無 | CSV 無、XLSX 有 | 有 |
| 學程欄名 | `等級名稱` | `學程(等級)名稱` | `學程(等級)名稱` |
| 縣市欄 | 105 無、110 有 | 有 | 有 |

類別名稱也會變：`進修部(學校)` ↔ `進修部`、`專業群(職業)科` ↔ `專業群科`。
全部集中在 `build_stream.py` 的對照表處理，這支只負責把原始檔抓下來。

⚠️ **104 學年沒有這份檔案**（該學年只有 `base0` 校別資料與 `base2` 科別資料），
所以對照從 105 開始。原民端的 104 數字保留，但沒有對照。

用法：
    python fetch_senior.py
"""

import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data" / "moe-senior"
BASE = "https://stats.moe.gov.tw/files/detail"

# 學年 → 要抓的副檔名。依決策：一律走 CSV，只有 114 沒有 CSV 才用 XLSX。
# 111–113 兩種都有，抓 CSV 就好——建置端本來就統一用年級欄加總，不吃學生數欄。
YEARS = {y: "csv" for y in range(105, 114)}
YEARS[114] = "xlsx"

# stats.moe.gov.tw 的憑證缺 Subject Key Identifier，Python 3.13 起
# VERIFY_X509_STRICT 預設開啟會直接拒絕。只關掉這個 flag，憑證鏈與主機名稱驗證
# 都仍然有效——不要改用 _create_unverified_context()。與 fetch.py 同一套處理。
SSL_CTX = ssl.create_default_context()
SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def path_for(year: int, ext: str) -> Path:
    return DATA_DIR / f"{year}_base3.{ext}"


def save(year: int, ext: str) -> None:
    path = path_for(year, ext)
    if path.exists():
        print(f"  = {year} {path.name}（已存在，未連線）{path.stat().st_size:>9,} bytes")
        return

    url = f"{BASE}/{year}/{year}_base3.{ext}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=180, context=SSL_CTX) as resp:
            body = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SystemExit(
            f"{year} 學年取數失敗：{exc}\n  {url}\n"
            "若是 404，該學年的檔名或副檔名可能改了——"
            "到教育部統計處「學校基本統計資訊」該學年頁面確認。"
        )

    # 半截或錯誤頁絕不落地：留下來會被下次執行當成有效快取。
    if len(body) < 10_000:
        raise SystemExit(
            f"{year} 學年回應只有 {len(body):,} bytes，太小不像資料檔，未寫入快取。"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    print(f"  + {year} {path.name} {len(body):>9,} bytes")


def main() -> None:
    print("《高級中等學校校別資料檔－按學程別分》105–114 學年（一般生對照）")
    for year, ext in sorted(YEARS.items()):
        save(year, ext)
    print(f"\n  104 學年沒有這份檔案，對照從 105 開始。")


if __name__ == "__main__":
    main()
