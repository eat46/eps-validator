# src/rules.py
import pandas as pd

def check_missing_value(row):
    """檢查關鍵數值是否缺失 (ERROR)"""
    if row["value"] == "" or pd.isna(row["value"]):
        return {
            "rule": "missing_value_check",
            "severity": "ERROR",
            "period": row["period"],
            "message": "數值缺失 (Missing Value)"
        }
    return None

def check_forecast_range(row):
    """檢查預估值區間 Low <= Mean <= High (ERROR)"""
    # 這裡先寫個概念，未來如果你有 low/mean/high 欄位時可以啟用
    # if row["low"] > row["mean"]: return {"rule": "forecast_range", "severity": "ERROR", ...}
    return None