from collections import defaultdict

from src.validators.common_rules import make_item


def reconcile_annual_quarterly(annual: dict, quarterly: dict, config):
    results = []

    annual_map = {
        i["year"]: i
        for i in annual["series"]
        if not i["is_forecast"]
    }

    quarter_map = defaultdict(dict)

    for item in quarterly["series"]:
        if (
            not item["is_forecast"]
            and item["year"] is not None
            and item["quarter"] is not None
        ):
            quarter_map[item["year"]][item["quarter"]] = item["mean"]

    years = sorted(set(annual_map) | set(quarter_map))

    for year in years:
        annual_item = annual_map.get(year)
        q = quarter_map.get(year, {})

        if annual_item is None:
            results.append(
                make_item(
                    "reconcile",
                    "annual_missing",
                    "INFO",
                    str(year),
                    "quarterly history exists but annual history missing",
                    {"quarters_found": sorted(q)},
                )
            )
            continue

        if len(q) < 4:
            results.append(
                make_item(
                    "reconcile",
                    "quarterly_incomplete",
                    "INFO",
                    str(year),
                    "annual exists but quarterly history incomplete",
                    {"quarters_found": sorted(q)},
                )
            )
            continue

        qsum = round(sum(q[i] for i in [1, 2, 3, 4]), 2)
        annual_value = annual_item["mean"]
        diff = round(abs(annual_value - qsum), 2)

        details = {
            "annual": annual_value,
            "quarter_sum": qsum,
            "diff": diff,
        }

        if diff <= config.tolerance_pass:
            results.append(
                make_item(
                    "reconcile",
                    "annual_vs_quarter_sum",
                    "INFO",
                    str(year),
                    "match",
                    details,
                )
            )
        elif diff <= config.tolerance_close:
            results.append(
                make_item(
                    "reconcile",
                    "annual_vs_quarter_sum",
                    "WARN",
                    str(year),
                    "close but not exact",
                    details,
                )
            )
        else:
            results.append(
                make_item(
                    "reconcile",
                    "annual_vs_quarter_sum",
                    "WARN",
                    str(year),
                    "needs review",
                    details,
                )
            )

    return results