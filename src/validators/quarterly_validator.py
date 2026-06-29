import re
from collections import defaultdict

from src.validators.common_rules import make_item


QUARTERLY_RE = re.compile(r"^(\d{4})Q([1-4])(\(f\))?$")


def validate_quarterly(data: dict):
    results = []
    grouped = defaultdict(list)
    seen = set()

    for field in ["stock_code", "stock_name", "country"]:
        if not data.get(field):
            results.append(
                make_item("quarterly", "required_field", "ERROR", None, f"missing {field}")
            )

    for item in data["series"]:
        p = item["period"]

        if p in seen:
            results.append(
                make_item("quarterly", "duplicate_period", "ERROR", p, "duplicate quarterly period")
            )
        seen.add(p)

        if not QUARTERLY_RE.match(p):
            results.append(
                make_item("quarterly", "period_format", "ERROR", p, "invalid quarterly period format")
            )

        if item["mean"] is not None and not isinstance(item["mean"], (int, float)):
            results.append(
                make_item("quarterly", "value_type", "ERROR", p, "mean must be numeric or null")
            )

        if (
            item["low"] is not None
            and item["high"] is not None
            and item["mean"] is not None
        ):
            if not (item["low"] <= item["mean"] <= item["high"]):
                results.append(
                    make_item(
                        "quarterly",
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
                        "quarterly",
                        "range_flat",
                        "INFO",
                        p,
                        "low = mean = high",
                        item,
                    )
                )

        grouped[item["year"]].append(item)

    for year, rows in grouped.items():
        hist_q = sorted(
            r["quarter"] for r in rows
            if not r["is_forecast"] and r["quarter"] is not None
        )
        forecast_q = sorted(
            r["quarter"] for r in rows
            if r["is_forecast"] and r["quarter"] is not None
        )

        if hist_q:
            expected = list(range(1, max(hist_q) + 1))
            if hist_q != expected:
                results.append(
                    make_item(
                        "quarterly",
                        "historical_gap",
                        "WARN",
                        str(year),
                        "historical quarters are not contiguous",
                        {"found": hist_q, "expected_prefix": expected},
                    )
                )

        if hist_q and forecast_q and min(forecast_q) <= max(hist_q):
            results.append(
                make_item(
                    "quarterly",
                    "forecast_boundary",
                    "ERROR",
                    str(year),
                    "forecast quarter overlaps historical quarter",
                    {"historical": hist_q, "forecast": forecast_q},
                )
            )

    return results