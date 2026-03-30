"""
Download and persist the official ASX listed-companies CSV.

Source: https://www.asx.com.au/asx/research/ASXListedCompanies.csv

Yahoo Finance expects symbols like ``BHP.AX`` (three-letter ASX codes map directly;
numeric/short codes still use ``{CODE}.AX``).
"""

from __future__ import annotations

import csv
import io
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import httpx
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.stock import AsxCsvSnapshot, AsxListedCompany

logger = logging.getLogger(__name__)

# Browser-like request — ASX CDN often rejects generic Python clients.
_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,text/plain,*/*",
    "Accept-Language": "en-AU,en;q=0.9",
}


def _find_csv_header_row(lines: List[str]) -> Tuple[int, Optional[str]]:
    """Return index of the ``Company name,ASX code,...`` row and optional banner line."""
    banner: Optional[str] = None
    if lines and lines[0].strip() and not lines[0].strip().startswith("Company name"):
        banner = lines[0].strip()
    for i, line in enumerate(lines):
        s = line.strip()
        if s.lower().startswith("company name") and "asx code" in s.lower():
            return i, banner
    raise ValueError("Could not find CSV header row (Company name, ASX code) in ASX response")


def _normalize_asx_code(raw: str) -> Optional[str]:
    if not raw:
        return None
    code = raw.strip().upper()
    code = re.sub(r"\s+", "", code)
    if not code or code == "ASXCODE":
        return None
    return code


def download_official_asx_csv() -> Tuple[str, Optional[str]]:
    """Fetch CSV body from the header row onward, plus optional banner line."""
    url = settings.ASX_OFFICIAL_CSV_URL
    with httpx.Client(
        headers=_HTTP_HEADERS,
        follow_redirects=True,
        timeout=httpx.Timeout(120.0, connect=30.0),
    ) as client:
        r = client.get(url)
        r.raise_for_status()
        text = r.text
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    header_idx, banner = _find_csv_header_row(lines)
    body = "\n".join(lines[header_idx:])
    return body, banner


def parse_asx_csv_rows(csv_text: str) -> List[Tuple[str, str, str, Optional[str]]]:
    """
    Parse CSV into rows: (yahoo_ticker, asx_code, company_name, gics_group).
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    rows: List[Tuple[str, str, str, Optional[str]]] = []
    for row in reader:
        code = _normalize_asx_code(
            row.get("ASX code") or row.get("asx code") or row.get("ASX Code") or ""
        )
        if not code:
            continue
        name = (row.get("Company name") or row.get("company name") or "").strip()
        gics = (row.get("GICS industry group") or row.get("gics industry group") or "").strip()
        if not name:
            name = code
        yahoo = f"{code}.AX"
        rows.append((yahoo, code, name, gics or None))
    return rows


def sync_official_asx_list(db: Session, *, commit: bool = True) -> Tuple[int, Optional[str]]:
    """
    Replace ``asx_listed_companies`` and the CSV snapshot from the official ASX URL.

    Returns ``(row_count, error_message)``. Rolls back this session on persistence errors.
    """
    try:
        csv_body, banner = download_official_asx_csv()
    except Exception as exc:
        logger.exception("Failed to download official ASX CSV")
        return 0, str(exc)

    try:
        parsed = parse_asx_csv_rows(csv_body)
    except Exception as exc:
        logger.exception("Failed to parse ASX CSV")
        return 0, str(exc)

    if not parsed:
        return 0, "Parsed zero rows from ASX CSV"

    now = datetime.now(timezone.utc)
    url = settings.ASX_OFFICIAL_CSV_URL
    raw_for_storage = (banner + "\n\n" if banner else "") + csv_body

    try:
        snap = db.get(AsxCsvSnapshot, 1)
        if snap is None:
            db.add(
                AsxCsvSnapshot(
                    id=1,
                    raw_csv=raw_for_storage,
                    source_url=url[:512],
                    asx_banner_line=(banner[:512] if banner else None),
                    row_count=len(parsed),
                    synced_at=now,
                )
            )
        else:
            snap.raw_csv = raw_for_storage
            snap.source_url = url[:512]
            snap.asx_banner_line = banner[:512] if banner else None
            snap.row_count = len(parsed)
            snap.synced_at = now

        db.execute(delete(AsxListedCompany))
        for yahoo, code, name, gics in parsed:
            gics_val = None
            if gics:
                gics_val = gics[:256] if len(gics) <= 256 else gics[:253] + "..."
            db.add(
                AsxListedCompany(
                    yahoo_ticker=yahoo[:16],
                    asx_code=code[:10],
                    company_name=name[:512] if len(name) <= 512 else name[:509] + "...",
                    gics_industry_group=gics_val,
                    synced_at=now,
                )
            )

        if commit:
            db.commit()
        else:
            db.flush()
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to persist ASX listing rows")
        return 0, str(exc)

    logger.info("Synced %s ASX listings from official CSV", len(parsed))
    return len(parsed), None
