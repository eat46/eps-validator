from src.models import ValidationItem


def make_item(layer, rule, severity, period=None, message="", details=None):
    return ValidationItem(
        layer=layer,
        rule=rule,
        severity=severity,
        period=period,
        message=message,
        details=details or {},
    )