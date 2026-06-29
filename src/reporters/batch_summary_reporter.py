import json
from pathlib import Path


def write_batch_summary_json(report: dict, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _safe(value):
    return "" if value is None else str(value)


def write_batch_summary_markdown(report: dict, output_path: str) -> None:
    run_summary = report["run_summary"]
    items = report["items"]

    lines = [
        "# Batch Validation Summary",
        "",
        "## Run Summary",
        "",
        f"- Total: {run_summary['total']}",
        f"- Pass: {run_summary['pass']}",
        f"- Fail: {run_summary['fail']}",
        "",
        "## Stock Results",
        "",
        "| Stock | Name | Country | Status | Annual Source | Quarterly Source | Annual E | Annual W | Quarterly E | Quarterly W | Reconcile E | Reconcile W | Error |",
        "|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for item in items:
        lines.append(
            f"| {_safe(item.get('stock_code'))} "
            f"| {_safe(item.get('stock_name'))} "
            f"| {_safe(item.get('country'))} "
            f"| {_safe(item.get('status'))} "
            f"| {_safe(item.get('annual_source'))} "
            f"| {_safe(item.get('quarterly_source'))} "
            f"| {_safe(item.get('annual_errors'))} "
            f"| {_safe(item.get('annual_warns'))} "
            f"| {_safe(item.get('quarterly_errors'))} "
            f"| {_safe(item.get('quarterly_warns'))} "
            f"| {_safe(item.get('reconcile_errors'))} "
            f"| {_safe(item.get('reconcile_warns'))} "
            f"| {_safe(item.get('error'))} |"
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")