import argparse
import copy
import os
from pathlib import Path

from dotenv import load_dotenv

from src.config import ValidationConfig, SourceConfig
from src.loader import load_payload
from src.normalizers.annual import normalize_annual
from src.normalizers.quarterly import normalize_quarterly
from src.reporters.json_reporter import write_json_report
from src.reporters.markdown_reporter import write_markdown_report
from src.reporters.batch_summary_reporter import (
    write_batch_summary_json,
    write_batch_summary_markdown,
)
from src.stock_list import load_stock_list
from src.validators.annual_validator import validate_annual
from src.validators.quarterly_validator import validate_quarterly
from src.validators.reconcile_validator import reconcile_annual_quarterly

load_dotenv()


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate annual EPS, quarterly EPS, and reconciliation rules."
    )

    parser.add_argument(
        "--source",
        choices=["file", "api", "hybrid"],
        default=os.getenv("UANALYZE_SOURCE", "file"),
        help="Data source mode: file, api, or hybrid.",
    )
    parser.add_argument(
        "--stock-code",
        dest="stock_code",
        default=os.getenv("UANALYZE_STOCK_CODE"),
        help="Stock code for API requests, e.g. 2454 or AAPL",
    )
    parser.add_argument(
        "--country",
        default=os.getenv("UANALYZE_COUNTRY", "TW"),
        help="Country code for API requests, e.g. TW or USA",
    )
    parser.add_argument(
        "--stocks-file",
        dest="stocks_file",
        default=os.getenv("UANALYZE_STOCKS_FILE"),
        help="JSON file containing a stock list for batch mode.",
    )
    parser.add_argument(
        "--annual-url",
        dest="annual_url",
        default=os.getenv("UANALYZE_ANNUAL_URL"),
        help="Annual EPS API URL template.",
    )
    parser.add_argument(
        "--quarterly-url",
        dest="quarterly_url",
        default=os.getenv("UANALYZE_QUARTERLY_URL"),
        help="Quarterly EPS API URL template.",
    )
    parser.add_argument(
        "--annual-fallback",
        dest="annual_fallback",
        default=os.getenv("UANALYZE_ANNUAL_FALLBACK"),
        help="Fallback local annual JSON path.",
    )
    parser.add_argument(
        "--quarterly-fallback",
        dest="quarterly_fallback",
        default=os.getenv("UANALYZE_QUARTERLY_FALLBACK"),
        help="Fallback local quarterly JSON path.",
    )
    parser.add_argument(
        "--json-report",
        dest="json_report",
        default=os.getenv("UANALYZE_JSON_REPORT", "output/reports/report.json"),
        help="Output path for JSON validation report",
    )
    parser.add_argument(
        "--md-report",
        dest="md_report",
        default=os.getenv("UANALYZE_MD_REPORT", "output/reports/report.md"),
        help="Output path for Markdown validation report",
    )

    return parser


def summarize(items):
    counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for item in items:
        counts[item.severity] += 1
    return counts


def should_fail(annual_res, quarterly_res, reconcile_res, cfg: ValidationConfig) -> bool:
    hard_errors = any(r.severity == "ERROR" for r in annual_res + quarterly_res)
    if cfg.fail_on_reconcile_warn:
        hard_errors = hard_errors or any(r.severity == "WARN" for r in reconcile_res)
    return hard_errors


def build_single_report(
    annual,
    annual_meta,
    quarterly_meta,
    annual_res,
    quarterly_res,
    reconcile_res,
    src_cfg,
):
    return {
        "stock_code": annual["stock_code"],
        "stock_name": annual["stock_name"],
        "country": annual.get("country", src_cfg.country),
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


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def run_once(cfg: ValidationConfig, src_cfg: SourceConfig, json_report_path: str, md_report_path: str):
    annual_raw, annual_meta = load_payload("annual", src_cfg, src_cfg.annual_fallback)
    quarterly_raw, quarterly_meta = load_payload("quarterly", src_cfg, src_cfg.quarterly_fallback)

    annual = normalize_annual(annual_raw)
    quarterly = normalize_quarterly(quarterly_raw)

    annual_res = validate_annual(annual)
    quarterly_res = validate_quarterly(quarterly)
    reconcile_res = reconcile_annual_quarterly(annual, quarterly, cfg)

    report = build_single_report(
        annual=annual,
        annual_meta=annual_meta,
        quarterly_meta=quarterly_meta,
        annual_res=annual_res,
        quarterly_res=quarterly_res,
        reconcile_res=reconcile_res,
        src_cfg=src_cfg,
    )

    ensure_parent(json_report_path)
    ensure_parent(md_report_path)
    write_json_report(report, json_report_path)
    write_markdown_report(report, md_report_path)

    failed = should_fail(annual_res, quarterly_res, reconcile_res, cfg)
    return report, failed


def build_batch_item_from_report(report: dict, failed: bool) -> dict:
    return {
        "stock_code": report["stock_code"],
        "stock_name": report.get("stock_name"),
        "country": report.get("country"),
        "status": "FAIL" if failed else "PASS",
        "annual_source": report["source_metadata"]["annual_source"],
        "quarterly_source": report["source_metadata"]["quarterly_source"],
        "annual_errors": report["annual_summary"]["ERROR"],
        "annual_warns": report["annual_summary"]["WARN"],
        "quarterly_errors": report["quarterly_summary"]["ERROR"],
        "quarterly_warns": report["quarterly_summary"]["WARN"],
        "reconcile_errors": report["reconcile_summary"]["ERROR"],
        "reconcile_warns": report["reconcile_summary"]["WARN"],
        "error": None,
    }


def build_batch_item_from_exception(stock_code: str, stock_name: str | None, country: str, exc: Exception) -> dict:
    return {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "country": country,
        "status": "FAIL",
        "annual_source": None,
        "quarterly_source": None,
        "annual_errors": None,
        "annual_warns": None,
        "quarterly_errors": None,
        "quarterly_warns": None,
        "reconcile_errors": None,
        "reconcile_warns": None,
        "error": f"{type(exc).__name__}: {exc}",
    }


def write_batch_outputs(summary_items: list[dict], json_report_path: str, md_report_path: str) -> dict:
    batch_report = {
        "run_summary": {
            "total": len(summary_items),
            "pass": sum(1 for x in summary_items if x["status"] == "PASS"),
            "fail": sum(1 for x in summary_items if x["status"] == "FAIL"),
        },
        "items": summary_items,
    }

    summary_json_path = str(Path(json_report_path).with_name("summary.json"))
    summary_md_path = str(Path(md_report_path).with_name("summary.md"))

    ensure_parent(summary_json_path)
    ensure_parent(summary_md_path)
    write_batch_summary_json(batch_report, summary_json_path)
    write_batch_summary_markdown(batch_report, summary_md_path)

    return batch_report


def run_batch(cfg: ValidationConfig, src_cfg: SourceConfig, args) -> int:
    stocks = load_stock_list(args.stocks_file)
    summary_items = []
    overall_fail = False

    for item in stocks:
        per_cfg = copy.deepcopy(src_cfg)
        per_cfg.stock_code = item["stock_code"]
        per_cfg.country = item["country"]

        json_path = str(Path(args.json_report).with_name(f"{item['stock_code']}_report.json"))
        md_path = str(Path(args.md_report).with_name(f"{item['stock_code']}_report.md"))

        try:
            report, failed = run_once(cfg, per_cfg, json_path, md_path)
            summary_items.append(build_batch_item_from_report(report, failed))
            overall_fail = overall_fail or failed
        except Exception as e:
            summary_items.append(
                build_batch_item_from_exception(
                    stock_code=item["stock_code"],
                    stock_name=item.get("stock_name"),
                    country=item["country"],
                    exc=e,
                )
            )
            overall_fail = True

    write_batch_outputs(summary_items, args.json_report, args.md_report)
    return 1 if overall_fail else 0


def run_single(cfg: ValidationConfig, src_cfg: SourceConfig, args) -> int:
    _, failed = run_once(cfg, src_cfg, args.json_report, args.md_report)
    return 1 if failed else 0


def main():
    parser = build_parser()
    args = parser.parse_args()

    cfg = ValidationConfig()
    src_cfg = SourceConfig.from_args(args)

    print(cfg)
    print(src_cfg)

    if args.stocks_file:
        exit_code = run_batch(cfg, src_cfg, args)
    else:
        exit_code = run_single(cfg, src_cfg, args)

    if exit_code != 0:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()