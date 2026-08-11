"""抓取內政部統計處「統計區原住民 15 歲以上人口十歲年齡組與性別與教育程度人口統計」。

這份資料提供本專案原本沒有的分母：**原住民成年人口的教育程度結構**。
教育部端只有「在學的原民生」，這裡是「已經在社會上的原住民受過多少教育」。

資料來自社會經濟資料服務平台（SEGIS），走 data.gov.tw dataset 18672 取得下載清單。

用法：
    python fetch_segis.py            # 抓 22 縣市的二級發布區檔（預設，約 20MB）
    python fetch_segis.py --level l1 # 改抓一級發布區（粒度更細，約 200MB）
    python fetch_segis.py --level both

⚠️ 本專案只用到縣市層級的彙總。一級／二級發布區都會彙總出相同的縣市數字
（實測花蓮縣兩者皆 79,475），抓兩級是為了互相驗證，不是為了更細的呈現——
發布區代碼無法還原成鄉鎮市區代碼，見 build_education.py 的說明。
"""

import json
import ssl
import sys
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "segis"
DATASET_ID = 18672
META_URL = f"https://data.gov.tw/api/v2/rest/dataset/{DATASET_ID}"

# segisws.moi.gov.tw 的憑證缺 Subject Key Identifier，Python 3.13 起 VERIFY_X509_STRICT
# 預設開啟會直接拒絕。只關掉這個 flag，憑證鏈與主機名稱驗證都仍然有效——
# 不要改用 _create_unverified_context()，那會連中間人都擋不住。詳見 fetch.py。
SSL_CTX = ssl.create_default_context()
SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")


def fetch(url: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
        return resp.read()


def distributions() -> list[tuple[str, str, str]]:
    """回傳 [(縣市, 'L1'|'L2', 下載網址)]，共 22 縣市 × 2 級 = 44 筆。

    平台沒有提供縣市級的彙總檔，只能逐縣市抓下來自己加總。
    """
    meta_path = DATA_DIR / f"dataset-{DATASET_ID}.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        body = fetch(META_URL, timeout=60)
        meta_path.write_bytes(body)
        meta = json.loads(body.decode("utf-8"))

    out = []
    for dist in meta["result"]["distribution"]:
        desc = dist["resourceDescription"]
        url = dist["resourceDownloadUrl"]
        level = "L1" if desc.endswith("一級發布區") else "L2"
        out.append((desc[:3], level, url))
    return out


def save(county: str, level: str, url: str) -> None:
    # ⚠️ 後設資料把 44 筆全部宣告為 XML，但實際上至少「新北市_一級發布區」回傳 JSON。
    # 宣告格式不可信，副檔名依實際內容決定，解析端也必須嗅探（見 build_education.py）。
    existing = list(DATA_DIR.glob(f"{county}_{level}.*"))
    if existing:
        print(f"  = {existing[0].name}（已存在）")
        return

    body = fetch(url)
    head = body.lstrip()[:1]
    ext = "json" if head == b"{" else "xml"
    out = DATA_DIR / f"{county}_{level}.{ext}"
    out.write_bytes(body)
    print(f"  + {out.name} ({len(body):,} bytes)")


def main() -> None:
    argv = sys.argv[1:]
    level = "l2"
    if "--level" in argv:
        level = argv[argv.index("--level") + 1].lower()
    wanted = {"l1": {"L1"}, "l2": {"L2"}, "both": {"L1", "L2"}}.get(level)
    if wanted is None:
        print("--level 只接受 l1 / l2 / both")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dists = [d for d in distributions() if d[1] in wanted]
    print(f"統計區原住民 15 歲以上人口教育程度統計（data.gov.tw dataset {DATASET_ID}）")
    print(f"  {len(dists)} 個檔，空間統計單元 {'／'.join(sorted(wanted))}")
    for county, lvl, url in sorted(dists):
        try:
            save(county, lvl, url)
        except Exception as exc:
            print(f"  ! {county}_{lvl} 失敗 {exc}")


if __name__ == "__main__":
    main()
