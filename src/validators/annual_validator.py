import re

from src.validators.common_rules import make_item


ANNUAL_RE = re.compile(r"^(\d{4})(\(f\))?$")


def validate_annual(data: dict):
    results = []

    for field in ["stock_code", "stock_name", "country"]:
        if not data.get(field):
            results.append(
                make_item("annual", "required_field", "ERROR", None, f"missing {field}")
            )

    hist_years = []
    forecast_years = []
    seen = set()

    for item in data["series"]:
        p = item["period"]

        if p in seen:
            results.append(
                make_item("annual", "duplicate_period", "ERROR", p, "duplicate annual period")
            )
        seen.add(p)

        if not ANNUAL_RE.match(p):
            results.append(
                make_item("annual", "period_format", "ERROR", p, "invalid annual period format")
            )

        if item["mean"] is not None and not isinstance(item["mean"], (int, float)):
            results.append(
                make_item("annual", "value_type", "ERROR", p, "mean must be numeric or null")
            )

        if item["year"] is not None:
            if item["is_forecast"]:
                forecast_years.append(item["year"])
            else:
                hist_years.append(item["year"])

        if (
            item["low"] is not None
            and item["high"] is not None
            and item["mean"] is not None
        ):
            if not (item["low"] <= item["mean"] <= item["high"]):
                results.append(
                    make_item(
                        "annual",
                        "range_order",
                        "ERROR",
                        p,
                        "expected Low <= Mean <= High",
                        item,
                    )
                )
            elif item["low"] == item["mean"] == item["high"]:
                results.append(
                    make_item(
                        "annual",
                        "range_flat",
                        "INFO",
                        p,
                        "low = mean = high",
                        item,
                    )
                )

    if hist_years and forecast_years and min(forecast_years) <= max(hist_years):
        results.append(
            make_item(
                "annual",
                "forecast_boundary",
                "ERROR",
                None,
                "forecast years overlap historical years",
            )
        )

    return results