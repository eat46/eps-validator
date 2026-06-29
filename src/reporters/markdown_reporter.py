from pathlib import Path

def write_markdown_report(report: dict, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    s = report['source_metadata']
    lines = []
    lines.append(f"# Validation Report: {report['stock_code']} {report['stock_name']}")
    lines.append("")
    lines.append("## Source metadata")
    lines.append("")
    lines.append(f"- annual_source: {s['annual_source']}")
    lines.append(f"- annual_url: {s['annual_url']}")
    lines.append(f"- annual_api_error: {s['annual_api_error']}")
    lines.append(f"- quarterly_source: {s['quarterly_source']}")
    lines.append(f"- quarterly_url: {s['quarterly_url']}")
    lines.append(f"- quarterly_api_error: {s['quarterly_api_error']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Annual: {report['annual_summary']}")
    lines.append(f"- Quarterly: {report['quarterly_summary']}")
    lines.append(f"- Reconcile: {report['reconcile_summary']}")
    lines.append("")
    for section in ['annual_results', 'quarterly_results', 'reconcile_results']:
        lines.append(f"## {section}")
        lines.append("")
        items = report[section]
        if not items:
            lines.append("- No issues found.")
        else:
            for item in items:
                lines.append(
                    f"- [{item['severity']}] {item['rule']} | period={item.get('period')} | "
                    f"{item['message']} | details={item.get('details', {})}"
                )
        lines.append("")
    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))