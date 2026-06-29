import re


QUARTERLY_RE = re.compile(r"^(\d{4})Q([1-4])(\(f\))?$")


def normalize_quarterly(payload: dict) -> dict:
    mean = payload["data"]["refinitiv_1"]["Data"]
    low = payload["data"].get("refinitiv_2", {}).get("Data", {})
    high = payload["data"].get("refinitiv_3", {}).get("Data", {})

    series = []
    for period, value in mean.items():
        m = QUARTERLY_RE.match(period)

        series.append(
            {
                "period": period,
                "year": int(m.group(1)) if m else None,
                "quarter": int(m.group(2)) if m else None,
                "is_forecast": bool(m and m.group(3)),
                "mean": value,
                "low": low.get(period),
                "high": high.get(period),
            }
        )

    return {
        "stock_code": payload["stock_code"],
        "stock_name": payload["stock_name"],
        "country": payload["country"],
        "granularity": "quarterly",
        "series": series,
    }