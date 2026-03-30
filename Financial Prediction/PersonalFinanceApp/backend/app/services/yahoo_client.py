"""
Browser-like HTTP sessions for yfinance (used across the backend).

Loads ``yahoo_http`` from ``StockPredictionModel`` when that package is on
``sys.path`` (local dev + Docker mount). Otherwise uses the same logic inline,
including optional ``YAHOO_HTTP_PROXIES`` rotation.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

_TLS = threading.local()
_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_FB_PROXY_LOCK = threading.Lock()
_FB_PROXY_I = 0


def _fallback_proxy_urls() -> list:
    raw = os.environ.get("YAHOO_HTTP_PROXIES", "").strip()
    lst = [x.strip() for x in raw.split(",") if x.strip()] if raw else []
    if not lst:
        one = (
            os.environ.get("YAHOO_HTTPS_PROXY", "").strip()
            or os.environ.get("HTTPS_PROXY", "").strip()
            or os.environ.get("https_proxy", "").strip()
        )
        if one:
            lst = [one]
    return lst


def _fallback_next_proxy() -> Optional[str]:
    global _FB_PROXY_I
    urls = _fallback_proxy_urls()
    if not urls:
        return None
    with _FB_PROXY_LOCK:
        u = urls[_FB_PROXY_I % len(urls)]
        _FB_PROXY_I += 1
    return u


def _fallback_build_yahoo_session() -> Any:
    url = _fallback_next_proxy()
    pdict = {"http": url, "https": url} if url else None
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


def _import_yahoo_http() -> Optional[Tuple[Any, Any, Any, Any]]:
    roots = [
        Path(__file__).resolve().parents[3] / "StockPredictionModel",
        Path("/StockPredictionModel"),
    ]
    for root in roots:
        if not root.is_dir():
            continue
        p = str(root)
        if p not in sys.path:
            sys.path.insert(0, p)
        try:
            import yahoo_http as yh  # type: ignore

            return (
                yh.build_yahoo_session,
                yh.thread_local_yahoo_session,
                yh.yfinance_ticker,
                yh.reset_thread_local_session,
            )
        except ImportError:
            continue
    return None


_impl = _import_yahoo_http()
if _impl is not None:
    build_yahoo_session, thread_local_yahoo_session, yfinance_ticker, reset_thread_local_session = _impl
else:
    build_yahoo_session = _fallback_build_yahoo_session

    def thread_local_yahoo_session() -> Any:
        if _fallback_proxy_urls():
            return _fallback_build_yahoo_session()
        if getattr(_TLS, "session", None) is None:
            _TLS.session = _fallback_build_yahoo_session()
        return _TLS.session

    def yfinance_ticker(symbol: str):
        import yfinance as yf

        return yf.Ticker(symbol, session=thread_local_yahoo_session())

    def reset_thread_local_session() -> None:
        if getattr(_TLS, "session", None) is not None:
            _TLS.session = None
