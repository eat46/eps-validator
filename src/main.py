import argparse
from pathlib import Path

from src.config import ValidationConfig, SourceConfig
from src.loader import load_payload
from src.normalizers.annual import normalize_annual
from src.normalizers.quarterly import normalize_quarterly
from src.validators.annual_validator import validate_annual
from src.validators.quarterly_validator import validate_quarterly
from src.validators.reconcile_validator import reconcile_annual_quarterly
from src.reporters.json_reporter import write_json_report
from src.reporters.markdown_reporter import write_markdown_report


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate annual EPS, quarterly EPS, and reconciliation rules."
    )

    parser.add_argument(
        "--source",
        choices=["file", "api", "hybrid"],
        default="file",
        help="Data source mode: file, api, or hybrid. Default: file",
    )

    parser.add_argument(
        "--stock-code",
        dest="stock_code",
        default=None,
        help="Stock code for API requests, e.g. 1101 or 2454",
    )

    parser.add_argument(
        "--country",
        default="TW",
        help="Country code for API requests. Default: TW",
    )

    parser.add_argument(
        "--annual-url",
        dest="annual_url",
        default=None,
        help=(
            "Annual EPS API URL template. "
            "Example: https://.../ReutersSmartEstimate_EPS/{stock_code}?country={country}"
        ),
    )

    parser.add_argument(
        "--quarterly-url",
        dest="quarterly_url",
        default=None,
        help=(
            "Quarterly EPS API URL template. "
            "Example: https://.../ReutersSmartEstimate_EPS_Quarterly/{stock_code}?country={country}"
        ),
    )

    parser.add_argument(
        "--annual-fallback",
        dest="annual_fallback",
        required=True,
        help="Fallback local annual JSON path",
    )

    parser.add_argument(
        "--quarterly-fallback",
        dest="quarterly_fallback",
        required=True,
        help="Fallback local quarterly JSON path",
    )

    parser.add_argument(
        "--json-report",
        dest="json_report",
        required=True,
        help="Output path for JSON validation report",
    )

    parser.add_argument(
        "--md-report",
        dest="md_report",
        required=True,
        help="Output path for Markdown validation report",
    )

    return parser


def summarize(items):
    counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for item in items:
        counts[item.severity] += 1
    return counts


def main():
    parser = build_parser()
    args = parser.parse_args()

    cfg = ValidationConfig()
    src_cfg = SourceConfig.from_args(args)

    annual_raw, annual_meta = load_payload("annual", src_cfg, args.annual_fallback)
    quarterly_raw, quarterly_meta = load_payload("quarterly", src_cfg, args.quarterly_fallback)

    annual = normalize_annual(annual_raw)
    quarterly = normalize_quarterly(quarterly_raw)

    annual_res = validate_annual(annual)
    quarterly_res = validate_quarterly(quarterly)
    reconcile_res = reconcile_annual_quarterly(annual, quarterly, cfg)

    report = {
        "stock_code": annual["stock_code"],
        "stock_name": annual["stock_name"],
        "source_metadata": {
            "annual_source": annual_meta["source"],
            "annual_url": annual_meta["url"],
            "annual_api_error": annual_meta["error"],
            "quarterly_source": quarterly_meta["source"],
            "quarterly_url": quarterly_meta["url"],
            "quarterly_api_error": quarterly_meta["error"],
        },
        "annual_summary": summarize(annual_res),
        "quarterly_summary": summarize(quarterly_res),
        "reconcile_summary": summarize(reconcile_res),
        "annual_results": [r.__dict__ for r in annual_res],
        "quarterly_results": [r.__dict__ for r in quarterly_res],
        "reconcile_results": [r.__dict__ for r in reconcile_res],
    }

    Path(args.json_report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.md_report).parent.mkdir(parents=True, exist_ok=True)

    write_json_report(report, args.json_report)
    write_markdown_report(report, args.md_report)

    hard_errors = any(r.severity == "ERROR" for r in annual_res + quarterly_res)
    if cfg.fail_on_reconcile_warn:
        hard_errors = hard_errors or any(r.severity == "WARN" for r in reconcile_res)

    if hard_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()