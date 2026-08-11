"""抓取內政部統計處《行政區各級學校統計》的鄉鎮市區層級資料，四個學制。

國小、國中、高級中等學校、大專校院四筆，欄位命名完全相同，因此由同一支腳本的
`LEVELS` 清單驅動，不為個別學制複製程式碼。

這批資料提供本專案原本沒有的粒度：**鄉鎮市區**。教育部統計出版品的
`A1-6a`／`A1-6b` 只到縣市，講不出「宜蘭縣承接的原民生集中在礁溪還是宜蘭市」。

而且分子與分母在同一列——`NA_STU_CNT`（原住民學生數）與 `STU_CNT`（全體學生數）
同時存在，原民生占比不需要任何外部對照表。

四階合起來就是就學階梯。114 學年實測：有該階學校的鄉鎮市區數是
**367 → 357 → 206 → 87**——義務教育近乎全覆蓋，高等教育只剩 87 個鄉鎮。
那就是原民生必須離開戶籍地的結構性理由。

資料來自社會經濟資料服務平台（SEGIS），走開放服務端點，免登入、免申請。

用法：
    python fetch_segis_college.py

⚠️ **這四筆的原始統計機關都是教育部統計處**，與本專案既有的統計出版品同源。
它們**不是**獨立來源，數字相符不構成交叉驗證，四階彼此一致也不構成。
唯一的價值是鄉鎮市區粒度。

⚠️ **跨階的人數不可直接相比**——各學制年級數不同（國小 6 年、國中 3 年、
高中職 3 年，大專含二專五專學士碩博而不固定）。可比的是鄉鎮市區數，
因為每個鄉鎮在每一階都只被計數一次。詳見 build_ladder.py。

⚠️ **只拿得到最新一期（目前是 114 學年），拿不到歷年。** 實測依據四項：

1. 官方文件寫明 `oCode` ＝ 主題代碼＋統計單元代碼＋資料格式，**不含年度**。
2. `OpenService.asmx` 只有 GetAdmin／GetOrg／GetStat 三個方法，全部只吃
   `oCode`，沒有時間參數。
3. 平台上 99–114 共 16 個學年的產品頁，回傳的 `oCode` **完全相同**。
4. 該 `oCode` 回傳的資料，`INFO_TIME` 全部是 `114Y`。

歷年要走平台「連結」按鈕給的下載網址（`reqcontroller.go?method=
filedown.downloadproductfile&…&STTIME=<年度>`，method 是明文且帶年度），
但未登入直接請求只會回傳平台首頁 HTML——**要歷年就得登入**。本腳本不做那件事。

⚠️ **端點回傳的永遠是「平台當下的最新一期」，不是固定的 114 學年。**
明年它會變成 115 學年而腳本不會察覺。因此學年一律取自回應的 `INFO_TIME`，
任何地方都不要寫死 114（見 build_receiving.py）。

平台清單把本統計依縣市列成 21 筆「…_鄉鎮市區_○○縣」，看起來要逐縣市抓——
**不是**。實測任一縣市入口的 `oCode` 回傳的都是全國 87 個鄉鎮市區、21 個縣市。
一次請求就夠，不要沿用 fetch_segis.py 那支逐縣市抓 22 個檔的模式。
"""

import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "segis-college"

ENDPOINT = "https://segisws.moi.gov.tw/STATWSSTData/OpenService.asmx/GetAdminSTDataForOpenCode"

# 四個學制的 oCode，全部 2026-08-11 取得。取法（一次性、人工，端點沒有目錄方法）：
#   1. https://segis.moi.gov.tw/STATCloud/QueryInterface?keyword=<資料集名稱>
#   2. 點任一筆「…_鄉鎮市區_○○縣」，會開新分頁 QueryInterfaceView?COL=…&MCOL=…
#      （任一縣市入口都可以——實測回傳的都是全國資料，不是該縣市而已）
#   3. 該頁 HTML 原始碼裡有 4 個 oCode 網址（JSON／XML／GeoJSON TWD97／WGS84），
#      取第一個 JSON 版。
# 平台若換發 oCode，該學制會失效——那時錯誤訊息會指名學制並指回這段註解。
#
# ⚠️ 年級數是給 build_ladder.py 用的：國小 6 年、國中 3 年、高中職 3 年，
# 大專填 None 因為它同時含二專、五專、學士、碩士、博士，沒有單一數字。
# 這欄的存在就是為了擋住「把國小人數除以大專人數當流失率」那種讀法。
LEVELS = [
    ("primary",   "國小",   6,
     "BF3B727F4239635617E7ED8441296DE6D5165CB1390D6FDB"
     "194022E6F0D9B0802539094FCB65D41BDDE79C332EB9258D"),
    ("junior",    "國中",   3,
     "BF3B727F4239635617E7ED8441296DE6D5165CB1390D6FDB"
     "52F41FB9881F3E9A212AB7B0B0B2E8CAD5421BC7960893AF"),
    ("senior",    "高中職", 3,
     "BF3B727F4239635617E7ED8441296DE6D5165CB1390D6FDB"
     "6FE3E4F8E9346D982539094FCB65D41BDDE79C332EB9258D"),
    ("tertiary",  "大專",   None,
     "BF3B727F423963563B5AF84EB7980862D5165CB1390D6FDB"
     "17F383C56D3DEE0F7EAC806A7E3C1369D5421BC7960893AF"),
]

# 大專的快取檔名沿用原本的名字，不改——改了會讓已入版控的既有流程重抓。
CACHE_NAMES = {
    "primary": "admin_primary_town.json",
    "junior": "admin_junior_town.json",
    "senior": "admin_senior_town.json",
    "tertiary": "admin_college_town.json",
}


def cache_path(code: str) -> Path:
    return DATA_DIR / CACHE_NAMES[code]

# segisws.moi.gov.tw 的憑證缺 Subject Key Identifier，Python 3.13 起
# VERIFY_X509_STRICT 預設開啟會直接拒絕。只關掉這個 flag，憑證鏈與主機名稱驗證
# 都仍然有效——不要改用 _create_unverified_context()，那會連中間人都擋不住。
# 與 fetch.py／fetch_segis.py 同一套處理。
SSL_CTX = ssl.create_default_context()
SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設 cp950，中文會亂碼
    sys.stdout.reconfigure(encoding="utf-8")
    # stderr 也要——本檔的中止訊息走 SystemExit（stderr），漏掉的話出錯時
    # 看到的是一串亂碼，而那正是最需要讀懂訊息的時候。
    sys.stderr.reconfigure(encoding="utf-8")


def fetch(ocode: str, timeout: int = 180) -> bytes:
    url = f"{ENDPOINT}?oCode={ocode}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
        return resp.read()


def save(code: str, label: str, ocode: str) -> None:
    """取一個學制。四個學制共用這支——不要為個別學制另寫一份。"""
    path = cache_path(code)
    if path.exists():
        print(f"  = {label:<3} {path.name}（已存在，未連線）{path.stat().st_size:>9,} bytes")
        return

    try:
        body = fetch(ocode)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SystemExit(
            f"{label}：取數失敗 {exc}\n"
            "若是端點拒絕而非網路問題，多半是該學制的 oCode 失效——"
            "依本檔 LEVELS 上方註解的三個步驟重新取得。"
        )

    # 空白或半截回應絕不落地：留下來會被下次執行當成有效快取，
    # 那種錯不會報錯，只會讓建置端產出一張空的地圖。
    head = body.lstrip()[:1]
    if head != b"{":
        raise SystemExit(
            f"{label}：回應不是 JSON（開頭為 {head!r}，長度 {len(body):,}）。"
            "多半是該學制的 oCode 失效後平台回傳了 HTML 錯誤頁，未寫入快取。"
        )
    if b'"RowDataList"' not in body:
        raise SystemExit(
            f"{label}：回應沒有 RowDataList（長度 {len(body):,}），未寫入快取。"
            f"請確認 {code} 的 oCode 是否仍有效。"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    print(f"  + {label:<3} {path.name} {len(body):>9,} bytes")


def main() -> None:
    print("《行政區各級學校統計》鄉鎮市區層級，四個學制各一次請求涵蓋全國")
    # 任一學制失敗即整體中止（save 會 raise）——不要留下只有三階的殘缺階梯，
    # 那會讓 build_ladder.py 產出一條少一級的線而不自知。
    for code, label, _years, ocode in LEVELS:
        save(code, label, ocode)


if __name__ == "__main__":
    main()
