import json
from pathlib import Path

from src.normalizers.annual import normalize_annual
from src.validators.annual_validator import validate_annual


def load_sample_annual():
    path = Path("data/samples/2454_annual.json")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_normalize_annual_basic():
    payload = load_sample_annual()
    data = normalize_annual(payload)

    assert data["stock_code"] == "2454"
    assert data["stock_name"] == "聯發科"
    assert data["granularity"] == "annual"
    assert len(data["series"]) > 0


def test_validate_annual_sample_has_no_error():
    payload = load_sample_annual()
    data = normalize_annual(payload)
    results = validate_annual(data)

    error_results = [r for r in results if r.severity == "ERROR"]
    assert error_results == []


def test_validate_annual_has_range_flat_info():
    payload = load_sample_annual()
    data = normalize_annual(payload)
    results = validate_annual(data)

    range_flat = [r for r in results if r.rule == "range_flat"]
    assert len(range_flat) >= 1