from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class ValidationItem:
    layer: str
    rule: str
    severity: str
    period: Optional[str] = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationReport:
    stock_code: str
    stock_name: str
    annual_results: list[ValidationItem] = field(default_factory=list)
    quarterly_results: list[ValidationItem] = field(default_factory=list)
    reconcile_results: list[ValidationItem] = field(default_factory=list)