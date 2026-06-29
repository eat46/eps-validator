import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ValidationConfig:
    tolerance_pass: float = 0.05
    tolerance_close: float = 0.5
    fail_on_reconcile_warn: bool = False


@dataclass
class SourceConfig:
    source: str = "file"  # file | api | hybrid
    stock_code: str | None = None
    country: str = "TW"
    annual_url: str | None = None
    quarterly_url: str | None = None
    annual_fallback: str | None = None
    quarterly_fallback: str | None = None
    api_token: str | None = None
    timeout: float = 10.0

    @classmethod
    def from_args(cls, args):
        return cls(
            source=args.source,
            stock_code=args.stock_code,
            country=args.country,
            annual_url=args.annual_url,
            quarterly_url=args.quarterly_url,
            annual_fallback=args.annual_fallback,
            quarterly_fallback=args.quarterly_fallback,
            api_token=os.getenv("UANALYZE_API_TOKEN"),
            timeout=float(os.getenv("UANALYZE_API_TIMEOUT", "10")),
        )