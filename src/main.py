# src/main.py
import json
import sys
import pandas as pd
from rules import check_missing_value  # 引入剛剛寫的規則

def load_data(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def transform_to_rows(raw_data):
    stock_code = raw_data["stock_code"]
    source = raw_data["source"]
    return [
        {"stock_code": stock_code, "source": source, "period": p, "value": v}
        for p, v in raw_data["data"].items()
    ]

def main():
    # 1. 讀取與轉換資料
    input_path = "data/eps/6510_quarterly.json" # 測試用，之後可改為用參數傳入
    raw_json = load_data(input_path)
    rows = transform_to_rows(raw_json)
    df = pd.DataFrame(rows)
    
    # 2. 開始跑驗證規則，蒐集結果
    errors = []
    warns = []
    infos = []
    results_list = []
    
    # 橫向一列一列跑規則 (axis=1)
    for index, row in df.iterrows():
        # 測試規則 1：檢查缺失值
        res = check_missing_value(row)
        if res:
            results_list.append(res)
            if res["severity"] == "ERROR":
                errors.append(res)
            elif res["severity"] == "WARN":
                warns.append(res)

    # 3. 組裝成指南要求的 report.json 格式
    report = {
      "stock_code": raw_json["stock_code"],
      "run_mode": "ci",
      "summary": {
        "error_count": len(errors),
        "warn_count": len(warns),
        "info_count": len(infos)
      },
      "results": results_list
    }
    
    # 4. 輸出 JSON 檔案
    output_path = "output/reports/report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"✅ 驗證完成！報告已產出至 {output_path}")
    print(f"統計結果: ERROR: {len(errors)}, WARN: {len(warns)}")

    # 5. 關鍵：如果 error_count > 0，讓系統噴出 exit code 1 (這樣 GitHub Actions 就會知道失敗了！)
    if len(errors) > 0:
        print("❌ 偵測到嚴重錯誤，Pipeline 阻擋！")
        sys.exit(1)
    else:
        print("🎉 檢查全數通過！")
        sys.exit(0)

if __name__ == "__main__":
    main()