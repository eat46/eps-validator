import json
from pathlib import Path

from src.config import ValidationConfig
from src.normalizers.annual import normalize_annual
from src.normalizers.quarterly import normalize_quarterly
from src.validators.reconcile_validator import reconcile_annual_quarterly


def load_sample_annual():
    path = Path("data/samples/2454_annual.json")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_sample_quarterly():
    path = Path("data/samples/2454_quarterly.json")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_reconcile_returns_results():
    annual = normalize_annual(load_sample_annual())
    quarterly = normalize_quarterly(load_sample_quarterly())
    config = ValidationConfig()

    results = reconcile_annual_quarterly(annual, quarterly, config)

    assert isinstance(results, list)
    assert len(results) > 0


def test_reconcile_2024_is_match():
    annual = normalize_annual(load_sample_annual())
    quarterly = normalize_quarterly(load_sample_quarterly())
    config = ValidationConfig()

    results = reconcile_annual_quarterly(annual, quarterly, config)

    target = [
        r for r in results
        if r.rule == "annual_vs_quarter_sum" and r.period == "2024"
    ]

    assert len(target) == 1
    assert target[0].severity == "INFO"
    assert target[0].message == "match"


def test_reconcile_2025_is_warn_or_info():
    annual = normalize_annual(load_sample_annual())
    quarterly = normalize_quarterly(load_sample_quarterly())
    config = ValidationConfig()

    results = reconcile_annual_quarterly(annual, quarterly, config)

    target = [
        r for r in results
        if r.rule == "annual_vs_quarter_sum" and r.period == "2025"
    ]

    assert len(target) == 1
    assert target[0].severity in ("INFO", "WARN")