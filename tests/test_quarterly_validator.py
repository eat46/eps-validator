import json
from pathlib import Path

from src.normalizers.quarterly import normalize_quarterly
from src.validators.quarterly_validator import validate_quarterly


def load_sample_quarterly():
    path = Path("data/samples/2454_quarterly.json")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_normalize_quarterly_basic():
    payload = load_sample_quarterly()
    data = normalize_quarterly(payload)

    assert data["stock_code"] == "2454"
    assert data["stock_name"] == "聯發科"
    assert data["granularity"] == "quarterly"
    assert len(data["series"]) > 0


def test_validate_quarterly_sample_has_no_error():
    payload = load_sample_quarterly()
    data = normalize_quarterly(payload)
    results = validate_quarterly(data)

    error_results = [r for r in results if r.severity == "ERROR"]
    assert error_results == []


def test_validate_quarterly_sample_has_no_historical_gap_warn():
    payload = load_sample_quarterly()
    data = normalize_quarterly(payload)
    results = validate_quarterly(data)

    gap_warns = [r for r in results if r.rule == "historical_gap"]
    assert gap_warns == []