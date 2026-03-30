"""
Browser-like HTTP sessions for yfinance.

- TLS: curl_cffi Chrome impersonation (or requests + real Chrome UA).
- Optional IP rotation: set YAHOO_HTTP_PROXIES to a comma-separated list of
  proxy URLs (http://host:port or http://user:pass@host:port). Each new
  session takes the next proxy in round-robin order.

When any proxy is configured, yfinance uses a fresh session per call so
rotation actually changes egress IP. Without proxies, sessions are thread-local
for efficiency.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

_TLS = threading.local()
_PROXY_LOCK = threading.Lock()
_PROXY_INDEX = 0

_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _parse_proxy_list() -> List[str]:
    raw = os.environ.get("YAHOO_HTTP_PROXIES", "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _env_single_proxy() -> str:
    return (
        os.environ.get("YAHOO_HTTPS_PROXY", "").strip()
        or os.environ.get("HTTPS_PROXY", "").strip()
        or os.environ.get("https_proxy", "").strip()
    )


def _proxy_urls_resolved() -> List[str]:
    """Read env each time so backend can sync pydantic .env into os.environ before first Yahoo call."""
    lst = _parse_proxy_list()
    if not lst:
        one = _env_single_proxy()
        if one:
            lst = [one]
    return lst


def reload_proxy_config() -> None:
    """Reset round-robin (e.g. tests)."""
    global _PROXY_INDEX
    with _PROXY_LOCK:
        _PROXY_INDEX = 0


def proxies_configured() -> bool:
    return len(_proxy_urls_resolved()) > 0


def _next_proxy_url() -> Optional[str]:
    urls = _proxy_urls_resolved()
    if not urls:
        return None
    global _PROXY_INDEX
    with _PROXY_LOCK:
        url = urls[_PROXY_INDEX % len(urls)]
        _PROXY_INDEX += 1
    return url


def _proxies_dict(url: Optional[str]) -> Optional[dict]:
    if not url:
        return None
    return {"http": url, "https": url}


def build_yahoo_session(proxy_url: Optional[str] = None) -> Any:
    """
    New HTTP session for Yahoo. If *proxy_url* is omitted, uses round-robin
    from env when YAHOO_HTTP_PROXIES / HTTPS_PROXY is set.
    """
    url = proxy_url if proxy_url is not None else _next_proxy_url()
    pdict = _proxies_dict(url)

    try:
        from curl_cffi import requests as cf

        kw: dict = {"impersonate": "chrome"}
        if pdict:
            kw["proxies"] = pdict
        return cf.Session(**kw)
    except Exception as exc:
        logger.debug("curl_cffi session unavailable (%s); using requests", exc)
        import requests

        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": _CHROME_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }
        )
        if pdict:
            s.proxies.update(pdict)
        return s


def thread_local_yahoo_session() -> Any:
    """
    With YAHOO_HTTP_PROXIES / HTTPS_PROXY set: new session (next proxy) every call.
    Otherwise: one session per thread for connection reuse.
    """
    if proxies_configured():
        return build_yahoo_session()
    if getattr(_TLS, "session", None) is None:
        _TLS.session = build_yahoo_session()
    return _TLS.session


def yfinance_ticker(symbol: str):
    import yfinance as yf

    return yf.Ticker(symbol, session=thread_local_yahoo_session())


def reset_thread_local_session() -> None:
    if getattr(_TLS, "session", None) is not None:
        _TLS.session = None
