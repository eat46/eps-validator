# EPS Validator v2

這是一個用來驗證 **年度 EPS API**、**季度 EPS API** 與 **年季對帳邏輯** 的 Python 專案範本，支援單檔模式與批次模式，並可輸出 machine-readable 的 JSON report 與 human-readable 的 Markdown report。[1][2][3]

設計目標不是只做一次性的資料清理，而是把資料驗證真正放進 pipeline、CI、排程任務與日常研究流程裡；目前專案也已經支援 batch summary 輸出，可直接拿來做 nightly validation 或 GitHub Actions artifact。[1][2]

***

## 專案目標

這個專案主要解決以下問題：[1]

- 年度 EPS 與季度 EPS 來自不同 API，必須分開驗證。[1]
- 年資料與季資料之間不能互相覆蓋，但可以做 reconciliation 檢查。[1]
- API 可能暫時不穩定，因此需要支援 fallback sample 檔案。[1]
- 驗證結果不能只有 pass/fail，還要輸出可讀的 JSON / Markdown report。[1]
- 需要支援單檔執行與多股票 batch 執行。[4][5]
- 批次結果需要有 summary 層，方便 CI / dashboard / daily check 使用。[2][3]

***

## 功能概覽

### 驗證層分成三層

1. **Annual validator** [1]
   - 檢查年度 period 格式。[1]
   - 檢查歷史 / forecast 分界。[1]
   - 檢查 `Low <= Mean <= High`。[1]
   - 檢查重複 period。[1]

2. **Quarterly validator** [1]
   - 檢查季度 period 格式。[1]
   - 檢查歷史季度是否連續。[1]
   - 檢查 forecast 是否插入歷史區間。[1]
   - 檢查 `Low <= Mean <= High`。[1]

3. **Reconcile validator** [1]
   - 檢查 annual 是否約等於 Q1+Q2+Q3+Q4。[1]
   - 檢查年度值存在但季度不完整。[1]
   - 檢查季度存在但年度不存在。[1]
   - 使用 tolerance 避免被四捨五入差異誤判。[1]

***

## 支援的資料來源模式

### `file`
只讀本地 JSON 檔案，不打 API。[1]

### `api`
強制從 API 取資料，API 失敗就直接中止。[1]

### `hybrid`
優先打 API；若 API 回傳錯誤、timeout 或 response 結構異常，就 fallback 到本地 sample JSON。[1]

例如 API 回傳以下 payload 時，即使 HTTP status 是 200，也應視為 API failure，而不是正常資料：[1][6]

```json
{
  "error": {"message": ["Not found."], "code": "E400004"},
  "status": "error"
}
```

***

## 單檔與批次模式

### 單檔模式

單檔模式適合本地快速驗證單一股票，輸出一組 `report.json` / `report.md`。[1][6]

### 批次模式

批次模式透過 `--stocks-file` 讀入股票清單，會為每一檔股票各自產生 individual report，並額外輸出 `summary.json` 與 `summary.md` 作為整批結果摘要。[4][5][2][3]

目前 batch summary 已包含以下欄位，可直接作為 CI summary schema：[2]

- `stock_code`
- `stock_name`
- `country`
- `status`
- `annual_source`
- `quarterly_source`
- `annual_errors`
- `annual_warns`
- `quarterly_errors`
- `quarterly_warns`
- `reconcile_errors`
- `reconcile_warns`
- `error`

***

## 輸出檔案

### 單檔輸出

單檔執行會產生：[1][6]

- `output/reports/report.json`
- `output/reports/report.md`

### 批次輸出

批次執行會產生：[5][2][3]

- `output/reports/2454_report.json`
- `output/reports/2454_report.md`
- `output/reports/2330_report.json`
- `output/reports/2330_report.md`
- `output/reports/AAPL_report.json`
- `output/reports/AAPL_report.md`
- `output/reports/summary.json`
- `output/reports/summary.md`

***

## 專案結構

```text
eps-validator-v2/
├── README.md
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── data/
│   ├── samples/
│   │   ├── 2454_annual.json
│   │   └── 2454_quarterly.json
│   └── test_stocks.json
├── output/
│   └── reports/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── loader.py
│   ├── main.py
│   ├── stock_list.py
│   ├── models.py
│   ├── normalizers/
│   │   ├── annual.py
│   │   └── quarterly.py
│   ├── reporters/
│   │   ├── json_reporter.py
│   │   ├── markdown_reporter.py
│   │   └── batch_summary_reporter.py
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

這個結構延續原本專案設計，並加入 batch stock list 與 batch summary reporter。[1][2][3]

***

## 各檔案用途

### `src/config.py`
放所有執行參數設定，包含 validation tolerance、API timeout、source mode、fallback 路徑、token 與 `.env` 載入。[7][1]

### `src/loader.py`
負責資料載入：讀本地 JSON、建立 Authorization header、建立 API URL、打 API、檢查 `status=error` payload、在 hybrid 模式下 fallback 到 sample 檔。[8][1]

### `src/main.py`
主程式入口，負責讀參數、決定單檔或批次模式、載入 annual / quarterly payload、normalize、執行三層 validation、輸出 report，最後依規則決定 exit code。[1][4][5]

### `src/stock_list.py`
負責讀入 batch 模式的股票清單，例如 `data/test_stocks.json`。[4][5]

### `src/reporters/batch_summary_reporter.py`
輸出批次 summary 的 JSON / Markdown，供 CI artifact 與人工作業檢視使用。[3][2]

***

## `.env` 與參數覆蓋規則

目前專案已改成以 `.env` 作為常用預設值來源，平常執行時不需要每次手動傳一長串參數；CLI 則保留為臨時覆蓋用途。[7][4][9]

建議優先順序如下：[7]

1. CLI 參數
2. `.env`
3. 程式內建預設值

也就是說，如果 `.env` 已經設定完整，日常執行通常只需要：[9][5]

```bash
PYTHONPATH=. python -m src.main
```

***

## 建議的 `.env` 內容

```dotenv
UANALYZE_SOURCE=hybrid
UANALYZE_STOCKS_FILE=data/test_stocks.json
UANALYZE_STOCK_CODE=2454
UANALYZE_COUNTRY=TW

UANALYZE_ANNUAL_URL=https://develop.api.uanalyze.com.tw/data_fetch/api/ReutersSmartEstimate_EPS/{stock_code}?country={country}
UANALYZE_QUARTERLY_URL=https://develop.api.uanalyze.com.tw/data_fetch/api/ReutersSmartEstimate_EPS_Quarterly/{stock_code}?country={country}

UANALYZE_ANNUAL_FALLBACK=data/samples/2454_annual.json
UANALYZE_QUARTERLY_FALLBACK=data/samples/2454_quarterly.json

UANALYZE_JSON_REPORT=output/reports/report.json
UANALYZE_MD_REPORT=output/reports/report.md

UANALYZE_API_TOKEN=your_token
UANALYZE_API_TIMEOUT=10
```

如果走單檔模式，`UANALYZE_STOCK_CODE` 很重要；若缺少 `stock_code` 且 source 是 `api`，loader 會因為無法組 API request 而直接失敗。[9][8]

如果走批次模式，請設定 `UANALYZE_STOCKS_FILE`，讓程式進入 batch 分支。[4][5]

***

## 安裝方式

### 1. 建立虛擬環境（建議）

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：[1]

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. 安裝套件

```bash
pip install -r requirements.txt
```

如果專案已經使用 `.env` 自動載入，`requirements.txt` 建議至少包含以下套件：[1]

- `pytest`
- `requests`
- `python-dotenv`

***

## 股票清單格式

批次模式的股票清單建議使用 JSON，例如：[4][2]

```json
[
  {"stock_code": "2454", "stock_name": "聯發科", "country": "TW"},
  {"stock_code": "2330", "stock_name": "台積電", "country": "TW"},
  {"stock_code": "AAPL", "stock_name": "蘋果公司", "country": "USA"}
]
```

這樣 summary report 就能直接帶出 `stock_name`，不需要額外對照代號。[2][3]

***

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

### 模式二：強制讀 API（單檔）

```bash
PYTHONPATH=. python -m src.main \
  --source api \
  --stock-code 2454 \
  --country TW
```

在 `.env` 已設定 URL、token、report 路徑時，通常不需要再重複帶這些值。[7][9]

### 模式三：Hybrid（單檔，推薦）

```bash
PYTHONPATH=. python -m src.main \
  --source hybrid \
  --stock-code 2454 \
  --country TW
```

這種模式下 API 若失敗，仍可 fallback 到 sample 並產出 report。[1][6]

### 模式四：Batch（推薦）

```bash
PYTHONPATH=. python -m src.main \
  --source hybrid \
  --stocks-file data/test_stocks.json
```

若 `.env` 已設定 `UANALYZE_SOURCE` 與 `UANALYZE_STOCKS_FILE`，則可以直接執行：[5][2]

```bash
PYTHONPATH=. python -m src.main
```

***

## Source metadata

每次單檔 report 都會把來源資訊寫進 report，方便追蹤該次結果是來自真 API 還是 fallback sample。[1][6]

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

這段資訊非常重要，因為可以從中得知：[1][6]

- 這次 report 是吃到真 API 還是 sample。
- annual 與 quarterly 是否來自不同來源。
- API 是 HTTP fail 還是 payload business error。

***

## Batch summary 範例

目前 batch summary 的 run summary 與 item schema 如下：[2]

```json
{
  "run_summary": {
    "total": 3,
    "pass": 3,
    "fail": 0
  },
  "items": [
    {
      "stock_code": "2454",
      "stock_name": "聯發科",
      "country": "TW",
      "status": "PASS",
      "annual_source": "api",
      "quarterly_source": "api",
      "annual_errors": 0,
      "annual_warns": 0,
      "quarterly_errors": 0,
      "quarterly_warns": 0,
      "reconcile_errors": 0,
      "reconcile_warns": 0,
      "error": null
    }
  ]
}
```

這份 schema 已適合直接作為 CI / dashboard / nightly monitor 的摘要資料來源。[2][3]

***

## 測試方式

```bash
PYTHONPATH=. pytest -q
```

建議至少保留以下測試：[1]

- annual validator 的 `range_flat`
- quarterly validator 的 `historical_gap`
- reconcile validator 的 `match`
- loader 的 header / URL 組裝
- batch stock list loading
- batch summary reporter 欄位完整性

***

## exit code 規則

目前 `main.py` 的預設邏輯是：[1]

- annual / quarterly 只要出現 `ERROR` → exit 1。
- reconcile 的 `WARN` 預設不讓 pipeline fail。
- 如果未來要更嚴格，可以把 `fail_on_reconcile_warn=True`。[1]

這個策略適合現在的階段，因為年 / 季對帳常常會有 rounding 或資料更新時間差，不適合一開始就把所有 reconcile warning 當成 hard failure。[1]

***

## GitHub Actions 方向

建議 workflow 流程如下：[1][10]

1. checkout repo
2. setup python
3. install requirements
4. 注入 `UANALYZE_API_TOKEN`
5. 用 `--source hybrid` 跑 validator
6. 把 `output/reports/` 上傳為 artifact

如果 batch mode 已是主要使用方式，建議在 CI 中直接上傳 individual reports 加 summary reports，方便回看每檔細節與整批狀態。[10][2][3]

***

## 下一步可以擴充什麼

### 1. Summary metadata

可以在 `summary.json` 再加入：[2]

- `generated_at`
- `validator_version`
- `annual_api_error`
- `quarterly_api_error`

### 2. Snapshot compare

可以把前一天 API 結果存到 `data/snapshots/`，再比對：[1]

- 哪個 historical 值被改寫
- 哪個 forecast 大幅跳動
- 哪個 coverage 區間突然消失

### 3. 更細的 business rules

例如：[1]

- forecast 年度必須連續
- 季資料 forecast 不可倒退
- 某些異常跳幅列成 warning
- 不同 coverage 數量觸發不同等級提醒

### 4. 支援更多輸出目的地

之後可把結果寫進：[1]

- CSV
- SQLite / Postgres
- dbt test layer
- 內部 dashboard