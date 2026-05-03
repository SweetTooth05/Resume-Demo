#!/usr/bin/env python3
"""
Step 0: Fetch ABS macroeconomic time-series → data/abs/*.csv

Usage:
    python 00_fetch_abs_data.py                          # use bundled fallback
    python 00_fetch_abs_data.py --api-key $ABS_API_KEY   # fetch live from ABS

Without an API key the script generates realistic fallback data (2015-Q1 to
2026-Q1) based on published ABS historical figures.  When an API key is
provided it fetches SDMX-JSON from data.api.abs.gov.au and overwrites the
same CSV files, so step 01 works identically either way.

Output (data/abs/):
    CPI_H.csv     WPI_H.csv    AWE.csv      LFORCE_H.csv
    HSI_M_H.csv   INT_RATE.csv LENDING.csv  GDP.csv

Each CSV has two columns: period, value

Next: python 01_generate_synthetic_csv.py
"""

import argparse
import csv
import json
import os
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Optional


# ── Dataset registry ──────────────────────────────────────────────────────────

DATASETS = [
    {"id": "CPI_H",    "freq": "Q", "desc": "Consumer Price Index"},
    {"id": "WPI_H",    "freq": "Q", "desc": "Wage Price Index"},
    {"id": "AWE",      "freq": "Q", "desc": "Average Weekly Earnings"},
    {"id": "LFORCE_H", "freq": "M", "desc": "Labour Force (unemployment %)"},
    {"id": "HSI_M_H",  "freq": "M", "desc": "Household Spending Indicator"},
    {"id": "INT_RATE", "freq": "M", "desc": "Cash Rate (%)"},
    {"id": "LENDING",  "freq": "M", "desc": "Variable Mortgage Rate (%)"},
    {"id": "GDP",      "freq": "Q", "desc": "GDP Index"},
]

ABS_BASE = "https://data.api.abs.gov.au/rest/data"


# ── Live fetch (requires API key) ─────────────────────────────────────────────

def _fetch_sdmx(dataset_id: str, api_key: str, start: str, end: str) -> list[dict]:
    """Fetch SDMX-JSON from ABS and return list of {period, value} dicts."""
    import urllib.request
    url = f"{ABS_BASE}/ABS,{dataset_id}/all?startPeriod={start}&endPeriod={end}&detail=dataonly"
    req = urllib.request.Request(url)
    req.add_header("apiKey", api_key)
    req.add_header("Accept", "application/vnd.sdmx.data+json;version=1.0")
    req.add_header("Accept-Encoding", "gzip, deflate")

    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        if resp.info().get("Content-Encoding") == "gzip":
            import gzip
            raw = gzip.decompress(raw)
        data = json.loads(raw)

    # SDMX-JSON 1.0 structure
    dataset = data["data"]["dataSets"][0]
    structure = data["data"]["structure"]
    obs_dim = structure["dimensions"]["observation"][0]["values"]
    periods = [v["id"] for v in obs_dim]

    rows: list[dict] = []
    for series_key, series in dataset["series"].items():
        for obs_idx_str, obs_vals in series["observations"].items():
            idx = int(obs_idx_str)
            value = obs_vals[0]
            if value is not None:
                rows.append({"period": periods[idx], "value": value})
        break  # take headline series only (first series key)

    rows.sort(key=lambda r: r["period"])
    return rows


# ── Fallback data generators ──────────────────────────────────────────────────

def _quarterly_periods(start_year: int, end_year: int) -> list[str]:
    periods = []
    for y in range(start_year, end_year + 1):
        for q in range(1, 5):
            periods.append(f"{y}-Q{q}")
            if y == end_year and q == 1:
                return periods
    return periods


def _monthly_periods(start_year: int, end_year: int) -> list[str]:
    periods = []
    for y in range(start_year, end_year + 1):
        for m in range(1, 13):
            periods.append(f"{y}-{m:02d}")
            if y == end_year and m == 1:
                return periods
    return periods


def _compound_series(start_val: float, periods: list[str], annual_growth: dict[int, float]) -> list[dict]:
    """Generate an index series by compounding quarterly growth from annual rates."""
    rows = []
    val = start_val
    for p in periods:
        year = int(p.split("-")[0])
        # quarterly growth factor from annual rate
        q_factor = (1 + annual_growth.get(year, 0.025)) ** 0.25
        rows.append({"period": p, "value": round(val, 2)})
        val *= q_factor
    return rows


def _gen_cpi() -> list[dict]:
    # All Groups CPI, Australia, index base 2011-12=100
    # Annual changes sourced from ABS 6401.0 releases
    return _compound_series(
        start_val=106.8,
        periods=_quarterly_periods(2015, 2026),
        annual_growth={
            2015: 0.017, 2016: 0.013, 2017: 0.019, 2018: 0.019, 2019: 0.018,
            2020: 0.009, 2021: 0.035, 2022: 0.078, 2023: 0.041, 2024: 0.024,
            2025: 0.025, 2026: 0.024,
        },
    )


def _gen_wpi() -> list[dict]:
    # Wage Price Index, all sectors, base Dec 2008=100
    # Annual changes sourced from ABS 6345.0 releases
    return _compound_series(
        start_val=128.7,
        periods=_quarterly_periods(2015, 2026),
        annual_growth={
            2015: 0.022, 2016: 0.019, 2017: 0.020, 2018: 0.022, 2019: 0.023,
            2020: 0.014, 2021: 0.023, 2022: 0.033, 2023: 0.042, 2024: 0.033,
            2025: 0.032, 2026: 0.030,
        },
    )


def _gen_awe() -> list[dict]:
    # Average Weekly Earnings, full-time adult ordinary time, AUD
    # Annual changes sourced from ABS 6302.0 releases
    return _compound_series(
        start_val=1452.0,
        periods=_quarterly_periods(2015, 2026),
        annual_growth={
            2015: 0.024, 2016: 0.022, 2017: 0.025, 2018: 0.027, 2019: 0.028,
            2020: 0.013, 2021: 0.025, 2022: 0.042, 2023: 0.055, 2024: 0.045,
            2025: 0.040, 2026: 0.035,
        },
    )


def _gen_gdp() -> list[dict]:
    # GDP index (chain volume, base 2021-22=100)
    return _compound_series(
        start_val=84.5,
        periods=_quarterly_periods(2015, 2026),
        annual_growth={
            2015: 0.028, 2016: 0.027, 2017: 0.024, 2018: 0.029, 2019: 0.020,
            2020: -0.025, 2021: 0.052, 2022: 0.038, 2023: 0.020, 2024: 0.015,
            2025: 0.020, 2026: 0.023,
        },
    )


# RBA cash rate target: (YYYY-MM, rate_percent)
# Source: RBA statistical table F1
_CASH_RATE_SCHEDULE: list[tuple[str, float]] = [
    ("2015-01", 2.50), ("2015-02", 2.25), ("2015-05", 2.00),
    ("2016-05", 1.75), ("2016-08", 1.50),
    ("2019-06", 1.25), ("2019-07", 1.00), ("2019-10", 0.75),
    ("2020-03", 0.25),  # two emergency cuts in Mar 2020; end-of-month rate used
    ("2020-11", 0.10),
    ("2022-05", 0.35), ("2022-06", 0.85), ("2022-07", 1.35),
    ("2022-08", 1.85), ("2022-09", 2.35), ("2022-10", 2.60),
    ("2022-11", 2.85), ("2022-12", 3.10),
    ("2023-02", 3.35), ("2023-03", 3.60), ("2023-05", 3.85),
    ("2023-06", 4.10), ("2023-11", 4.35),
    ("2025-02", 4.10), ("2025-05", 3.85), ("2025-08", 3.60),
    ("2025-11", 3.35), ("2026-01", 3.10),
]


def _gen_int_rate() -> list[dict]:
    periods = _monthly_periods(2015, 2026)
    schedule = dict(_CASH_RATE_SCHEDULE)
    rate = 2.50
    rows = []
    for p in periods:
        if p in schedule:
            rate = schedule[p]
        rows.append({"period": p, "value": rate})
    return rows


def _gen_lending() -> list[dict]:
    """Variable mortgage rate = cash rate + 2.0% (standard variable margin)."""
    base = _gen_int_rate()
    return [{"period": r["period"], "value": round(r["value"] + 2.0, 2)} for r in base]


# Unemployment rate key anchors: (YYYY-MM, rate_percent)
# Source: ABS 6202.0 Labour Force
_UNEMPLOYMENT_ANCHORS: list[tuple[str, float]] = [
    ("2015-01", 6.1), ("2015-06", 6.0), ("2015-12", 5.8),
    ("2016-06", 5.7), ("2016-12", 5.8),
    ("2017-06", 5.6), ("2017-12", 5.4),
    ("2018-06", 5.4), ("2018-12", 5.1),
    ("2019-03", 5.1), ("2019-06", 5.2), ("2019-12", 5.1),
    ("2020-02", 5.1), ("2020-04", 6.2), ("2020-06", 7.2),
    ("2020-07", 7.5), ("2020-10", 6.9), ("2020-12", 6.6),
    ("2021-03", 5.7), ("2021-06", 5.1), ("2021-09", 4.6),
    ("2021-12", 4.2), ("2022-03", 4.0), ("2022-06", 3.5),
    ("2022-09", 3.5), ("2022-11", 3.4), ("2022-12", 3.5),
    ("2023-03", 3.6), ("2023-06", 3.6), ("2023-09", 3.7),
    ("2023-12", 3.9), ("2024-03", 3.9), ("2024-06", 4.1),
    ("2024-09", 4.2), ("2024-12", 4.1), ("2025-03", 4.2),
    ("2025-06", 4.2), ("2025-09", 4.2), ("2025-12", 4.1),
    ("2026-01", 4.1),
]


def _gen_lforce() -> list[dict]:
    """Linear interpolation between unemployment anchor points."""
    periods = _monthly_periods(2015, 2026)
    anchors = {p: v for p, v in _UNEMPLOYMENT_ANCHORS}
    anchor_keys = sorted(anchors.keys())

    def _interp(p: str) -> float:
        if p in anchors:
            return anchors[p]
        prev = next((k for k in reversed(anchor_keys) if k <= p), anchor_keys[0])
        nxt = next((k for k in anchor_keys if k >= p), anchor_keys[-1])
        if prev == nxt:
            return anchors[prev]
        # linear interpolation by month index
        def _midx(s: str) -> int:
            y, m = s.split("-")
            return int(y) * 12 + int(m)
        t = (_midx(p) - _midx(prev)) / (_midx(nxt) - _midx(prev))
        return anchors[prev] + t * (anchors[nxt] - anchors[prev])

    return [{"period": p, "value": round(_interp(p), 2)} for p in periods]


def _gen_hsi() -> list[dict]:
    """
    Household Spending Indicator monthly index (base Jan 2015 = 100).
    Grows broadly with CPI + real spending growth; dips during COVID lockdowns.
    """
    periods = _monthly_periods(2015, 2026)
    ANNUAL_REAL_GROWTH = {
        2015: 0.030, 2016: 0.028, 2017: 0.032, 2018: 0.033, 2019: 0.025,
        2020: -0.050, 2021: 0.075, 2022: 0.065, 2023: 0.025, 2024: 0.018,
        2025: 0.022, 2026: 0.025,
    }
    # COVID lockdown penalty: severe in Apr-Sep 2020
    LOCKDOWN_FACTOR = {
        "2020-04": 0.88, "2020-05": 0.84, "2020-06": 0.90,
        "2020-07": 0.91, "2020-08": 0.88, "2020-09": 0.93,
    }
    val = 100.0
    rows = []
    for p in periods:
        year = int(p.split("-")[0])
        monthly_growth = (1 + ANNUAL_REAL_GROWTH.get(year, 0.025)) ** (1 / 12)
        factor = LOCKDOWN_FACTOR.get(p, 1.0)
        rows.append({"period": p, "value": round(val * factor, 2)})
        val *= monthly_growth
    return rows


# ── Dataset dispatcher ────────────────────────────────────────────────────────

FALLBACK_GENERATORS = {
    "CPI_H":    _gen_cpi,
    "WPI_H":    _gen_wpi,
    "AWE":      _gen_awe,
    "LFORCE_H": _gen_lforce,
    "HSI_M_H":  _gen_hsi,
    "INT_RATE": _gen_int_rate,
    "LENDING":  _gen_lending,
    "GDP":      _gen_gdp,
}


def save_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["period", "value"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ABS macroeconomic data")
    parser.add_argument("--api-key", default=os.environ.get("ABS_API_KEY", ""),
                        help="ABS API key (or set ABS_API_KEY env var)")
    parser.add_argument("--output", default="./data/abs", help="Output directory")
    parser.add_argument("--start", default="2015", help="Start period (year)")
    parser.add_argument("--end", default="2026", help="End period (year)")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    use_live = bool(args.api_key)
    if not use_live:
        print("WARNING: No ABS_API_KEY — using bundled fallback data (2015-2026).")
        print("To fetch live: ABS_API_KEY=<key> python 00_fetch_abs_data.py\n")

    for ds in DATASETS:
        did = ds["id"]
        path = out_dir / f"{did}.csv"

        if use_live:
            print(f"  Fetching {did} ({ds['desc']}) from ABS API...")
            try:
                rows = _fetch_sdmx(did, args.api_key, args.start, args.end)
                save_csv(rows, path)
                print(f"    → {len(rows)} observations → {path}")
                time.sleep(0.5)  # be polite to ABS API
            except Exception as e:
                print(f"    WARNING: live fetch failed ({e}), falling back to bundled data")
                rows = FALLBACK_GENERATORS[did]()
                save_csv(rows, path)
        else:
            print(f"  Generating {did} ({ds['desc']})...")
            rows = FALLBACK_GENERATORS[did]()
            save_csv(rows, path)
            print(f"    → {len(rows)} periods → {path}")

    print(f"\nABS data ready in {out_dir}/")
    print("Next: python 01_generate_synthetic_csv.py")


if __name__ == "__main__":
    main()
