from src.loader import build_headers, build_url


def test_build_headers_with_token():
    headers = build_headers("abc123")
    assert headers["Accept"] == "application/json"
    assert headers["Authorization"] == "Bearer abc123"


def test_build_headers_without_token():
    headers = build_headers(None)
    assert headers["Accept"] == "application/json"
    assert "Authorization" not in headers


def test_build_url():
    template = "https://example.com/api/{stock_code}?country={country}"
    url = build_url(template, "2454", "TW")
    assert url == "https://example.com/api/2454?country=TW"