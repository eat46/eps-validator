import re


ANNUAL_RE = re.compile(r"^(\d{4})(\(f\))?$")


def normalize_annual(payload: dict) -> dict:
    mean = payload["data"]["data"]["refinitiv_1"]["Data"]
    low = payload["data"]["data"].get("refinitiv_2", {}).get("Data", {})
    high = payload["data"]["data"].get("refinitiv_3", {}).get("Data", {})

    series = []
    for period, value in mean.items():
        m = ANNUAL_RE.match(period)

        series.append(
            {
                "period": period,
                "year": int(m.group(1)) if m else None,
                "quarter": None,
                "is_forecast": bool(m and m.group(2)),
                "mean": value,
                "low": low.get(period),
                "high": high.get(period),
            }
        )

    return {
        "stock_code": payload["data"]["stock_code"],
        "stock_name": payload["data"]["stock_name"],
        "country": payload["data"]["country"],
        "granularity": "annual",
        "series": series,
    }