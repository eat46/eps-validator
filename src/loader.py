import json
from pathlib import Path
from typing import Any
import requests


def load_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_headers(api_token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    return headers


def fetch_json(url: str, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()

    if isinstance(payload, dict) and payload.get("status") == "error":
        err = payload.get("error", {})
        raise ValueError(
            f"API returned error payload: code={err.get('code')}, message={err.get('message')}"
        )

    return payload


def build_url(template: str, stock_code: str, country: str) -> str:
    return template.format(stock_code=stock_code, country=country)


def load_payload(kind: str, source_config, fallback_path: str | None):
    template = source_config.annual_url if kind == "annual" else source_config.quarterly_url
    meta = {"source": None, "url": None, "error": None}

    if source_config.source in ("api", "hybrid"):
        if not template or not source_config.stock_code:
            meta["error"] = f"missing {kind} API template or stock_code"
            if source_config.source == "api":
                raise ValueError(meta["error"])
        else:
            url = build_url(template, source_config.stock_code, source_config.country)
            meta["url"] = url
            try:
                payload = fetch_json(
                    url,
                    build_headers(source_config.api_token),
                    source_config.timeout,
                )
                meta["source"] = "api"
                return payload, meta
            except Exception as e:
                meta["error"] = f"{type(e).__name__}: {e}"
                if source_config.source == "api":
                    raise

    if source_config.source == "file":
        if not fallback_path:
            raise ValueError(f"missing fallback file for {kind}")
        payload = load_json(fallback_path)
        meta["source"] = "file"
        return payload, meta

    if source_config.source == "hybrid" and fallback_path:
        payload = load_json(fallback_path)
        meta["source"] = "fallback_file"
        return payload, meta

    raise ValueError(
        f"unable to load {kind}: source={source_config.source}, "
        f"stock_code={source_config.stock_code}, error={meta['error']}"
    )