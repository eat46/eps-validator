import json
import os
from pathlib import Path


def load_stock_list(path: str | None) -> list[dict]:
    if not path:
        raise ValueError("missing stock list file path")

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"stock list file not found: {path}")

    with open(file_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list) or not items:
        raise ValueError("stock list must be a non-empty list")

    normalized = []
    default_country = os.getenv("UANALYZE_DEFAULT_COUNTRY", "TW")

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"stock list item #{i} must be an object")

        stock_code = str(item.get("stock_code", "")).strip()
        country = str(item.get("country", default_country)).strip()

        if not stock_code:
            raise ValueError(f"stock list item #{i} missing stock_code")
        if not country:
            raise ValueError(f"stock list item #{i} missing country")

        normalized.append(
            {
                "stock_code": stock_code,
                "country": country,
            }
        )

    return normalized