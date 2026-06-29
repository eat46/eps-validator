# EPS Validator v2

這是一個用來驗證 **年度 EPS API**、**季度 EPS API** 與 **年季對帳邏輯** 的 Python 專案範本。

設計目標：不是只做一次性的資料清理，而是可以把資料驗證真正放進 pipeline、CI、排程任務與日常研究流程裡。

---

## 專案目標

這個專案主要解決以下問題：

- 年度 EPS 與季度 EPS 來自不同 API，必須分開驗證。
- 年資料與季資料之間不能互相覆蓋，但可以做 reconciliation 檢查。
- API 目前可能尚未穩定，因此需要支援 fallback sample 檔案。
- 驗證結果不能只有 pass/fail，還要輸出可讀的 JSON / Markdown report。
- 之後要能掛進 GitHub Actions、排程或每日資料檢查流程。

---

## 功能概覽

### 驗證層分成三層

1. **Annual validator**
   - 檢查年度 period 格式
   - 檢查歷史 / forecast 分界
   - 檢查 `Low <= Mean <= High`
   - 檢查重複 period

2. **Quarterly validator**
   - 檢查季度 period 格式
   - 檢查歷史季度是否連續
   - 檢查 forecast 是否插入歷史區間
   - 檢查 `Low <= Mean <= High`

3. **Reconcile validator**
   - 檢查 annual 是否約等於 Q1+Q2+Q3+Q4
   - 檢查年度值存在但季度不完整
   - 檢查季度存在但年度不存在
   - 使用 tolerance 避免被四捨五入差異誤判

---

## 支援的資料來源模式

### `file`
只讀本地 JSON 檔案，不打 API。

### `api`
強制從 API 取資料，API 失敗就直接中止。

### `hybrid`
優先打 API；若 API 回傳錯誤、timeout 或 response 結構異常，就 fallback 到本地 sample JSON。

例如 API 回傳：

```json
{
  "error": {"message": ["Not found."], "code": "E400004"},
  "status": "error"
}
```

這種情況 HTTP 可能是 200，但 payload 其實不是有效業務資料，因此 loader 需要把這類 response 視為 API failure，而不是正常資料。

---

## 專案結構

```text
eps-validator-v2/
├── README.md
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── data/
│   └── samples/
│       ├── 2454_annual.json
│       └── 2454_quarterly.json
├── output/
│   └── reports/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── loader.py
│   ├── main.py
│   ├── models.py
│   ├── normalizers/
│   │   ├── annual.py
│   │   └── quarterly.py
│   ├── reporters/
│   │   ├── json_reporter.py
│   │   └── markdown_reporter.py
│   ├── utils/
│   │   ├── periods.py
│   │   └── severity.py
│   └── validators/
│       ├── annual_validator.py
│       ├── common_rules.py
│       ├── quarterly_validator.py
│       └── reconcile_validator.py
└── tests/
    ├── test_annual_validator.py
    ├── test_loader.py
    ├── test_quarterly_validator.py
    └── test_reconcile_validator.py
```

---

## 各檔案用途

### `requirements.txt`
安裝專案所需套件：

- `pytest`
- `requests`

### `src/config.py`
放所有執行參數設定：

- validation tolerance
- API timeout
- source mode
- fallback 路徑
- token 環境變數讀取

### `src/models.py`
定義資料結構，例如：

- `ValidationItem`
- `ValidationReport`

### `src/loader.py`
負責資料載入：

- 讀本地 JSON
- 建立 Authorization header
- 建立 API URL
- 打 API
- 檢查 API payload 是否其實是 `status=error`
- fallback 到 sample 檔

### `src/normalizers/annual.py`
把 annual API / JSON 轉成統一內部格式。

### `src/normalizers/quarterly.py`
把 quarterly API / JSON 轉成統一內部格式。

### `src/validators/common_rules.py`
放共用 helper，例如建立 `ValidationItem`。

### `src/validators/annual_validator.py`
只驗 annual。

### `src/validators/quarterly_validator.py`
只驗 quarterly。

### `src/validators/reconcile_validator.py`
只驗 annual 與 quarterly 之間的關係。

### `src/reporters/json_reporter.py`
輸出機器可讀的 JSON report。

### `src/reporters/markdown_reporter.py`
輸出人可讀的 Markdown report。

### `src/main.py`
主程式入口，負責：

1. 讀參數
2. 決定 source mode
3. 載入 annual / quarterly payload
4. normalize
5. 跑三層 validation
6. 輸出 report
7. 根據規則決定 exit code

### `tests/`
放單元測試。

---

## 內部資料格式

normalizer 之後的 annual / quarterly 都會長成相同概念：

```python
{
    "stock_code": "2454",
    "stock_name": "聯發科",
    "country": "TW",
    "granularity": "annual",
    "series": [
        {
            "period": "2025",
            "year": 2025,
            "quarter": None,
            "is_forecast": False,
            "mean": 66.16,
            "low": None,
            "high": None
        }
    ]
}
```

季度資料則只是 `quarter` 會有值，例如 `1~4`。

這樣做的好處是 validator 不需要知道原始 API 的巢狀結構，只需要驗標準格式。

---

## 驗證規則設計

### Annual validator

檢查：

- `period` 是否符合 `YYYY` 或 `YYYY(f)`
- 是否有 duplicate period
- `mean` 是否為數字
- `Low <= Mean <= High`
- 若 `low = mean = high`，標成 `INFO`
- forecast 年份是否與歷史年份重疊

### Quarterly validator

檢查：

- `period` 是否符合 `YYYYQn` 或 `YYYYQn(f)`
- 是否有 duplicate period
- `mean` 是否為數字
- `Low <= Mean <= High`
- 歷史季度是否連續，例如不能有 Q1、Q3 但沒有 Q2
- forecast 季度不能插進歷史區間

### Reconcile validator

檢查：

- 若某年沒有 annual，但有 quarterly，標成 `annual_missing`
- 若某年有 annual，但季度不滿四季，標成 `quarterly_incomplete`
- 若四季完整，檢查 annual 是否等於四季加總
- 容忍小數差異：
  - `diff <= 0.05` → `INFO match`
  - `0.05 < diff <= 0.5` → `WARN close but not exact`
  - `diff > 0.5` → `WARN needs review`

---

## Source metadata

每次執行都會把來源資訊寫進 report：

```json
{
  "source_metadata": {
    "annual_source": "fallback_file",
    "annual_url": "https://...",
    "annual_api_error": "ValueError: API returned error payload: code=E400004, message=['Not found.']",
    "quarterly_source": "api",
    "quarterly_url": "https://...",
    "quarterly_api_error": null
  }
}
```

這段資訊非常重要，因為可以從中得知：

- 這次 report 是吃到真 API 還是 sample
- annual 與 quarterly 是否來自不同來源
- API 是 HTTP fail 還是 payload business error

---

## 安裝方式

### 1. 建立虛擬環境（建議）

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. 安裝套件

```bash
pip install -r requirements.txt
```

---

## sample 檔案準備方式

如果已有 JSON，將檔案放到 data/samples/ 目錄下，例如：

```text
data/samples/2454_annual.json
data/samples/2454_quarterly.json
```

---

## 執行方式

### 模式一：只讀本地檔

```bash
PYTHONPATH=. python -m src.main \
  --source file \
  --annual-fallback data/samples/2454_annual.json \
  --quarterly-fallback data/samples/2454_quarterly.json \
  --json-report output/reports/report.json \
  --md-report output/reports/report.md
```

### 模式二：強制讀 API

```bash
export UANALYZE_API_TOKEN='your_token'
PYTHONPATH=. python -m src.main \
  --source api \
  --stock-code 1101 \
  --country TW \
  --annual-url 'https://develop.api.uanalyze.com.tw/data_fetch/api/ReutersSmartEstimate_EPS/{stock_code}?country={country}' \
  --quarterly-url 'https://develop.api.uanalyze.com.tw/data_fetch/api/ReutersSmartEstimate_EPS_Quarterly/{stock_code}?country={country}' \
  --annual-fallback data/samples/2454_annual.json \
  --quarterly-fallback data/samples/2454_quarterly.json \
  --json-report output/reports/report.json \
  --md-report output/reports/report.md
```

這種模式下 API 失敗會直接中止。

### 模式三：Hybrid（推薦）

```bash
export UANALYZE_API_TOKEN='your_token'
PYTHONPATH=. python -m src.main \
  --source hybrid \
  --stock-code 1101 \
  --country TW \
  --annual-url 'https://develop.api.uanalyze.com.tw/data_fetch/api/ReutersSmartEstimate_EPS/{stock_code}?country={country}' \
  --quarterly-url 'https://develop.api.uanalyze.com.tw/data_fetch/api/ReutersSmartEstimate_EPS_Quarterly/{stock_code}?country={country}' \
  --annual-fallback data/samples/2454_annual.json \
  --quarterly-fallback data/samples/2454_quarterly.json \
  --json-report output/reports/report.json \
  --md-report output/reports/report.md
```

這種模式下 API 若失敗，仍可產出 report。

---

## 環境變數與 Secrets

本專案使用環境變數管理敏感設定與執行參數，例如：

- `UANALYZE_API_TOKEN`
- `UANALYZE_API_TIMEOUT`

這樣做的原因是：API token 不應寫死在程式碼、README 或 repo 裡，而應由執行環境提供。這也符合 12-factor app 對 config 的建議：將設定存放在環境變數，而不是硬編碼在程式中。

### 必要的環境變數

#### `UANALYZE_API_TOKEN`
用來呼叫 UAnalyze API 的 Bearer token。

#### `UANALYZE_API_TIMEOUT`
API timeout 秒數，預設可設為 `10`。

---

## 本機開發

本機開發有兩種常見方式：

### 方式一：直接在 shell 設定（推薦、最簡單）

```bash
export UANALYZE_API_TOKEN='your_token'
export UANALYZE_API_TIMEOUT='10'
```

然後再執行程式：

```bash
PYTHONPATH=. python -m src.main \
  --source hybrid \
  --stock-code 1101 \
  --country TW \
  --annual-url 'https://develop.api.uanalyze.com.tw/data_fetch/api/ReutersSmartEstimate_EPS/{stock_code}?country={country}' \
  --quarterly-url 'https://develop.api.uanalyze.com.tw/data_fetch/api/ReutersSmartEstimate_EPS_Quarterly/{stock_code}?country={country}' \
  --annual-fallback data/samples/2454_annual.json \
  --quarterly-fallback data/samples/2454_quarterly.json \
  --json-report output/reports/report.json \
  --md-report output/reports/report.md
```

### 方式二：使用 `.env` 檔（方便，但非必要）

在專案根目錄建立 `.env`：

```env
UANALYZE_API_TOKEN=your_token
UANALYZE_API_TIMEOUT=10
```

並建立 `.env.example` 作為範本：

```env
UANALYZE_API_TOKEN=
UANALYZE_API_TIMEOUT=10
```

請注意：

- `.env` 放真實值，只供本機使用
- `.env.example` 可 commit，讓其他人知道需要哪些變數
- `.env` 不可 commit，應加入 `.gitignore`

---

## dotenv 是必要的嗎？

不是必要。

本專案只要透過 `os.getenv()` 讀取環境變數，就能正常運作。也就是說：

- 本機可以用 `export ...` 設定
- GitHub Actions 可以用 Secrets 注入
- 正式環境可以由部署平台提供 env vars

如果希望本機開發更方便，可以自行加入 `python-dotenv` 與 `load_dotenv()`，讓 `.env` 自動載入；但這不是 CI 或 production 的必要條件。

---

## GitHub Actions Secrets

在 GitHub Actions 中，不要把 token 寫在 workflow 檔案裡，應使用 GitHub Secrets。

### 新增 repository secret 的步驟

1. 打開 GitHub repository
2. 進入 `Settings`
3. 點選 `Secrets and variables`
4. 點選 `Actions`
5. 按 `New repository secret`
6. Name 輸入：`UANALYZE_API_TOKEN`
7. Value 輸入你的實際 token

之後就可以在 workflow 中這樣使用：

```yaml
env:
  UANALYZE_API_TOKEN: ${{ secrets.UANALYZE_API_TOKEN }}
  UANALYZE_API_TIMEOUT: "10"
```

---

## `.gitignore` 建議

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
output/
```

---

## config.py 讀取方式

本專案建議在 `src/config.py` 中用 `os.getenv()` 讀環境變數，例如：

```python
api_token = os.getenv("UANALYZE_API_TOKEN")
timeout = float(os.getenv("UANALYZE_API_TIMEOUT", "10"))
```

這樣做的好處是：

- 不需要把 token 寫死在 repo
- 本機、CI、正式環境可共用同一份程式碼
- 變更設定時不需要改 code，只需要改執行環境

---

## 建議做法總結

- 本機開發：可直接用 `export`，或選擇使用 `.env`
- `.env`：只供本機使用，不可 commit
- `.env.example`：可 commit
- GitHub Actions：使用 repository secrets
- production：使用部署平台提供的環境變數

---

## 測試方式

```bash
PYTHONPATH=. pytest -q
```

建議至少保留以下測試：

- annual validator 的 `range_flat`
- quarterly validator 的 `historical_gap`
- reconcile validator 的 `match`
- loader 的 header / URL 組裝

---

## 建議的 exit code 規則

目前 `main.py` 的預設邏輯是：

- annual / quarterly 只要出現 `ERROR` → exit 1
- reconcile 的 `WARN` 暫時不讓 pipeline fail
- 如果未來要更嚴格，可以把 `fail_on_reconcile_warn=True`

這個策略適合現在的階段，因為年 / 季對帳常常會有 rounding 或資料更新時間差，不應一開始就把所有 reconcile warning 當成 hard failure。

---

## 建議的 GitHub Actions 方向

1. checkout repo
2. setup python
3. install requirements
4. 注入 `UANALYZE_API_TOKEN`
5. 用 `--source hybrid` 跑 validator
6. 把 `output/reports/` 上傳為 artifact

另外，token 應該放在 GitHub Secrets，不要寫死在 repo 裡。

---

## 下一步可以擴充什麼

### 1. 批次多股票模式

目前先支援單一 stock code，下一步可以改成：

- `--stock-codes 1101,2454,2317`
- 批次跑 annual / quarterly
- 產出 summary table

### 2. Snapshot compare

可以把前一天 API 結果存到 `data/snapshots/`，再比對：

- 哪個 historical 值被改寫
- 哪個 forecast 大幅跳動
- 哪個 coverage 區間突然消失

### 3. 更細的 business rules

例如：

- forecast 年度必須連續
- 季資料 forecast 不可倒退
- 某些異常跳幅列成 warning
- 不同 coverage 數量觸發不同等級提醒

### 4. 支援 CSV / db / dashboard

之後可把結果寫進：

- CSV
- SQLite / Postgres
- dbt test layer
- 內部 dashboard
