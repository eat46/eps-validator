from src.main import build_parser


def test_build_parser():
    parser = build_parser()
    args = parser.parse_args([
        "--source", "file",
        "--annual-fallback", "data/samples/2454_annual.json",
        "--quarterly-fallback", "data/samples/2454_quarterly.json",
        "--json-report", "output/reports/report.json",
        "--md-report", "output/reports/report.md",
    ])

    assert args.source == "file"
    assert args.annual_fallback.endswith("2454_annual.json")
    assert args.quarterly_fallback.endswith("2454_quarterly.json")