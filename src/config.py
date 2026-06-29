import os
from dataclasses import dataclass


DEFAULT_ANNUAL_URL = (
    "https://develop.api.uanalyze.com.tw/data_fetch/api/"
    "ReutersSmartEstimate_EPS/{stock_code}?country={country}"
)

DEFAULT_QUARTERLY_URL = (
    "https://develop.api.uanalyze.com.tw/data_fetch/api/"
    "ReutersSmartEstimate_EPS_Quarterly/{stock_code}?country={country}"
)


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
        annual_url = getattr(args, "annual_url", None) or os.getenv(
            "UANALYZE_ANNUAL_URL",
            DEFAULT_ANNUAL_URL,
        )
        quarterly_url = getattr(args, "quarterly_url", None) or os.getenv(
            "UANALYZE_QUARTERLY_URL",
            DEFAULT_QUARTERLY_URL,
        )

        return cls(
            source=getattr(args, "source", "file"),
            stock_code=getattr(args, "stock_code", None),
            country=getattr(args, "country", "TW"),
            annual_url=annual_url,
            quarterly_url=quarterly_url,
            annual_fallback=getattr(args, "annual_fallback", None),
            quarterly_fallback=getattr(args, "quarterly_fallback", None),
            api_token=os.getenv("UANALYZE_API_TOKEN"),
            timeout=float(os.getenv("UANALYZE_API_TIMEOUT", "10")),
        )