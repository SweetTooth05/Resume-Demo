#!/usr/bin/env python3
"""
Step 1: Generate synthetic personal finance CSVs grounded in ABS macroeconomic data.

Reads ABS CSVs produced by 00_fetch_abs_data.py and emits one CSV per persona
in data/synthetic/.  Output columns (date, description, amount, balance) are
compatible with 01_prepare_dataset.py's generic CSV parser.

Usage:
    python 01_generate_synthetic_csv.py \
        [--abs-dir data/abs] [--output data/synthetic] [--seed 42]

Next: python 01_prepare_dataset.py --csv-dir data/synthetic
"""

import argparse
import csv
import math
import random
from datetime import date
from pathlib import Path


# ── ABS data loader ───────────────────────────────────────────────────────────

class ABSMetrics:
    """Monthly lookup table for all ABS indicators."""

    def __init__(self, abs_dir: Path):
        self.cpi     = self._load_q(abs_dir / "CPI_H.csv")
        self.wpi     = self._load_q(abs_dir / "WPI_H.csv")
        self.awe     = self._load_q(abs_dir / "AWE.csv")
        self.gdp     = self._load_q(abs_dir / "GDP.csv")
        self.unemp   = self._load_m(abs_dir / "LFORCE_H.csv")
        self.hsi     = self._load_m(abs_dir / "HSI_M_H.csv")
        self.rate    = self._load_m(abs_dir / "INT_RATE.csv")
        self.lending = self._load_m(abs_dir / "LENDING.csv")

        # Base values (2015-Q1 → 2015-01 after expansion)
        self.cpi_base     = self.cpi["2015-01"]
        self.wpi_base     = self.wpi["2015-01"]
        self.awe_base     = self.awe["2015-01"]
        self.hsi_base     = self.hsi["2015-01"]

    @staticmethod
    def _load_q(path: Path) -> dict[str, float]:
        """Load quarterly CSV and expand each quarter to 3 identical monthly entries."""
        rows: dict[str, float] = {}
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                p, v = r["period"], float(r["value"])
                year, q = p.split("-Q")
                start_m = (int(q) - 1) * 3 + 1
                for m in range(start_m, start_m + 3):
                    rows[f"{year}-{m:02d}"] = v
        return rows

    @staticmethod
    def _load_m(path: Path) -> dict[str, float]:
        rows: dict[str, float] = {}
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["period"]] = float(r["value"])
        return rows

    def get(self, month_key: str) -> dict:
        """Return all indicators for a given YYYY-MM month key."""
        k = month_key
        return {
            "cpi_factor":  self.cpi.get(k, self.cpi_base) / self.cpi_base,
            "wpi_factor":  self.wpi.get(k, self.wpi_base) / self.wpi_base,
            "awe_weekly":  self.awe.get(k, self.awe_base),
            "hsi_factor":  self.hsi.get(k, self.hsi_base) / self.hsi_base,
            "unemp_rate":  self.unemp.get(k, 5.0) / 100,
            "lending_rate": self.lending.get(k, 5.0) / 100,
            "cash_rate":   self.rate.get(k, 2.5) / 100,
        }


# ── Persona definitions ───────────────────────────────────────────────────────

PERSONAS = [
    {
        "id": "renter_single",
        "employer": "Riverstone Consulting PTY",
        "income_weekly": 1442,      # ~$75k / 52
        "income_wpi_scaled": True,
        "housing": "rent",
        "base_rent": 2200,          # monthly, Sydney 2015
        "loan_amount": 0,
        "loan_term_months": 0,
        "grocery_weekly": 130,
        "transport_monthly": 150,
        "utilities_quarterly": 310,
        "dining_monthly": 280,
        "entertainment_monthly": 55,
        "insurance_monthly": 110,
        "shopping_monthly": 140,
        "healthcare_annual": 380,
        "has_centrelink": False,
        "has_investment": False,
        "unemp_sensitivity": 0.6,
        "starting_balance": 5200.0,
        "casual": False,
    },
    {
        "id": "mortgagor_couple",
        "employer": "BHP Group PTY",
        "income_weekly": 1827,      # ~$95k / 52
        "income_wpi_scaled": True,
        "housing": "mortgage",
        "base_rent": 0,
        "loan_amount": 620_000,
        "loan_term_months": 360,
        "grocery_weekly": 220,
        "transport_monthly": 280,
        "utilities_quarterly": 480,
        "dining_monthly": 350,
        "entertainment_monthly": 90,
        "insurance_monthly": 250,
        "shopping_monthly": 250,
        "healthcare_annual": 700,
        "has_centrelink": False,
        "has_investment": False,
        "unemp_sensitivity": 0.4,
        "starting_balance": 14_500.0,
        "casual": False,
    },
    {
        "id": "family_dual",
        "employer": "Telstra Corporation PTY",
        "income_weekly": 2500,      # ~$130k / 52
        "income_wpi_scaled": True,
        "housing": "mortgage",
        "base_rent": 0,
        "loan_amount": 780_000,
        "loan_term_months": 360,
        "grocery_weekly": 380,
        "transport_monthly": 420,
        "utilities_quarterly": 680,
        "dining_monthly": 400,
        "entertainment_monthly": 130,
        "insurance_monthly": 380,
        "shopping_monthly": 400,
        "healthcare_annual": 1200,
        "has_centrelink": False,
        "has_investment": False,
        "unemp_sensitivity": 0.3,
        "starting_balance": 12_000.0,
        "casual": False,
    },
    {
        "id": "student_casual",
        "employer": "Woolworths Group Direct Credit",
        "income_weekly": 538,       # ~$28k / 52
        "income_wpi_scaled": False,
        "housing": "rent",
        "base_rent": 900,           # share house room
        "loan_amount": 0,
        "loan_term_months": 0,
        "grocery_weekly": 75,
        "transport_monthly": 130,
        "utilities_quarterly": 0,   # included in rent
        "dining_monthly": 120,
        "entertainment_monthly": 35,
        "insurance_monthly": 0,
        "shopping_monthly": 60,
        "healthcare_annual": 120,
        "has_centrelink": True,
        "has_investment": False,
        "unemp_sensitivity": 2.0,   # casual → higher gap risk
        "starting_balance": 1400.0,
        "casual": True,
    },
    {
        "id": "empty_nester",
        "employer": "Macquarie Group PTY Payslip",
        "income_weekly": 2308,      # ~$120k / 52
        "income_wpi_scaled": True,
        "housing": "owns",
        "base_rent": 0,
        "loan_amount": 0,           # paid off
        "loan_term_months": 0,
        "grocery_weekly": 200,
        "transport_monthly": 300,
        "utilities_quarterly": 520,
        "dining_monthly": 500,
        "entertainment_monthly": 150,
        "insurance_monthly": 400,
        "shopping_monthly": 350,
        "healthcare_annual": 1500,
        "has_centrelink": False,
        "has_investment": True,     # dividends from ComSec portfolio
        "unemp_sensitivity": 0.2,
        "starting_balance": 25_000.0,
        "casual": False,
    },
    {
        "id": "low_income_welfare",
        "employer": "Cleanaway Waste PTY Wage",
        "income_weekly": 730,       # ~$38k / 52
        "income_wpi_scaled": False,
        "housing": "rent",
        "base_rent": 1400,
        "loan_amount": 0,
        "loan_term_months": 0,
        "grocery_weekly": 90,
        "transport_monthly": 110,
        "utilities_quarterly": 380,
        "dining_monthly": 80,
        "entertainment_monthly": 20,
        "insurance_monthly": 60,
        "shopping_monthly": 70,
        "healthcare_annual": 300,
        "has_centrelink": True,
        "has_investment": False,
        "unemp_sensitivity": 1.8,
        "starting_balance": 820.0,
        "casual": True,
    },
    {
        "id": "high_income_professional",
        "employer": "PwC Australia PTY Payroll",
        "income_weekly": 4038,      # ~$210k / 52
        "income_wpi_scaled": True,
        "housing": "mortgage",
        "base_rent": 0,
        "loan_amount": 1_200_000,
        "loan_term_months": 360,
        "grocery_weekly": 350,
        "transport_monthly": 600,
        "utilities_quarterly": 750,
        "dining_monthly": 900,
        "entertainment_monthly": 280,
        "insurance_monthly": 650,
        "shopping_monthly": 800,
        "healthcare_annual": 3500,
        "has_centrelink": False,
        "has_investment": True,     # Vanguard ETF investments
        "unemp_sensitivity": 0.1,
        "starting_balance": 30_000.0,
        "casual": False,
    },
    {
        "id": "retiree",
        "employer": "Direct Credit Superannuation Fund",
        "income_weekly": 1058,      # ~$55k / 52 (pension + super drawdown)
        "income_wpi_scaled": False,
        "housing": "owns",
        "base_rent": 0,
        "loan_amount": 0,
        "loan_term_months": 0,
        "grocery_weekly": 170,
        "transport_monthly": 180,
        "utilities_quarterly": 450,
        "dining_monthly": 350,
        "entertainment_monthly": 100,
        "insurance_monthly": 350,
        "shopping_monthly": 200,
        "healthcare_annual": 2200,
        "has_centrelink": True,     # Age pension component
        "has_investment": True,     # Vanguard / Pearler ETFs
        "unemp_sensitivity": 0.0,
        "starting_balance": 20_000.0,
        "casual": False,
    },
    {
        "id": "small_biz_owner",
        "employer": "Sole Trader Direct Credit",
        "income_weekly": 1635,      # ~$85k / 52 (volatile)
        "income_wpi_scaled": False,
        "housing": "mortgage",
        "base_rent": 0,
        "loan_amount": 520_000,
        "loan_term_months": 360,
        "grocery_weekly": 200,
        "transport_monthly": 350,
        "utilities_quarterly": 550,
        "dining_monthly": 320,
        "entertainment_monthly": 80,
        "insurance_monthly": 280,
        "shopping_monthly": 220,
        "healthcare_annual": 900,
        "has_centrelink": False,
        "has_investment": False,
        "unemp_sensitivity": 0.8,   # business income volatility
        "starting_balance": 9_500.0,
        "casual": True,             # income variance
    },
    {
        "id": "migrant_temp_visa",
        "employer": "Coles Group PTY Payroll",
        "income_weekly": 1250,      # ~$65k / 52
        "income_wpi_scaled": False,
        "housing": "rent",
        "base_rent": 1800,
        "loan_amount": 0,
        "loan_term_months": 0,
        "grocery_weekly": 110,
        "transport_monthly": 140,
        "utilities_quarterly": 0,   # often included or split
        "dining_monthly": 180,
        "entertainment_monthly": 40,
        "insurance_monthly": 90,
        "shopping_monthly": 100,
        "healthcare_annual": 250,
        "has_centrelink": False,    # temp visa = no Centrelink
        "has_investment": False,
        "unemp_sensitivity": 1.2,
        "starting_balance": 3_200.0,
        "casual": False,
    },
]


# ── Transaction generators ────────────────────────────────────────────────────

def _vary(base: float, pct: float = 0.12) -> float:
    """Return base amount with ±pct random variation, minimum $1."""
    return max(1.0, base * (1 + random.gauss(0, pct)))


def _make(d: date, desc: str, amount: float) -> dict:
    return {"date": d, "description": desc, "amount": round(amount, 2), "balance": 0.0}


# Merchant pools — names match CATEGORY_RULES regex in 01_prepare_dataset.py
GROCERS   = ["Woolworths", "Coles", "Aldi", "IGA", "Harris Farm Markets"]
CAFES     = ["The Coffee Club", "Gloria Jeans Coffee", "Restaurant Local", "Cafe Nero"]
DINERS    = ["Thai Restaurant", "Noodle Bar", "Sushi Train", "Pizza Hut", "Local Cafe"]
RIDESHARE = ["Uber", "Ola Ride", "DiDi Transport"]
STREAMING = ["Netflix Subscription", "Spotify Subscription", "Apple Music Subscription"]
ENERGY    = ["AGL Energy", "Origin Energy", "EnergyAustralia"]
TELCO     = ["Telstra Broadband", "Optus Mobile", "TPG Internet"]
HEALTH    = ["Chemist Warehouse", "Medicare Refund", "Doctor Medical Centre", "Bupa Health Fund"]
INSURE    = ["NRMA Insurance", "AAMI Insurance", "Allianz Insurance"]
SHOPS     = ["Kmart", "Big W", "JB Hi-Fi", "Amazon AU", "Target"]
INVEST    = ["Vanguard Investment", "CommSec Brokerage", "Pearler Investment"]
PENSION   = ["Centrelink Direct Credit"]


def gen_income(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """Fortnightly payroll — two deposits per month."""
    base_weekly = persona["income_weekly"]
    if persona["income_wpi_scaled"]:
        base_weekly *= m["wpi_factor"]

    fortnightly = base_weekly * 2
    if persona["casual"]:
        fortnightly *= random.uniform(0.6, 1.1)  # casual income variance

    employer = persona["employer"]
    return [
        _make(date(year, month, 1),  employer, round(fortnightly, 2)),
        _make(date(year, month, 15), employer, round(fortnightly, 2)),
    ]


def gen_centrelink(year: int, month: int, persona: dict) -> list[dict]:
    """Centrelink payment when applicable (welfare/student/retiree)."""
    if not persona["has_centrelink"]:
        return []
    amount = random.uniform(500, 900) if persona["id"] != "retiree" else 1100
    return [_make(date(year, month, 5), PENSION[0], round(amount, 2))]


def gen_housing(year: int, month: int, persona: dict, m: dict, state: dict) -> list[dict]:
    housing = persona["housing"]
    if housing == "rent":
        rent = _vary(persona["base_rent"] * m["cpi_factor"], 0.02)
        return [_make(date(year, month, 1), "Rent Payment Transfer", -round(rent, 2))]

    if housing == "mortgage":
        # Recalculate P&I repayment each month given current rate and remaining balance
        balance = state.get("loan_balance", persona["loan_amount"])
        months_elapsed = state.get("months_elapsed", 0)
        remaining = max(1, persona["loan_term_months"] - months_elapsed)
        r = m["lending_rate"] / 12
        if r > 0:
            repayment = balance * (r * (1 + r) ** remaining) / ((1 + r) ** remaining - 1)
        else:
            repayment = balance / remaining
        repayment = min(repayment, balance)

        # Update outstanding loan balance
        interest = balance * r
        principal = max(0.0, repayment - interest)
        state["loan_balance"] = max(0.0, balance - principal)
        state["months_elapsed"] = months_elapsed + 1

        return [_make(date(year, month, 1), "Mortgage Repayment Transfer", -round(repayment, 2))]

    return []  # owns outright


def gen_groceries(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """3–4 weekly grocery shops, scaled by CPI."""
    base = persona["grocery_weekly"] * m["cpi_factor"]
    # Spending appetite reduced during COVID lockdowns
    base *= m["hsi_factor"] if m["hsi_factor"] < 0.95 else 1.0

    txns = []
    # 4 weekly shops on days 3, 10, 17, 24
    for day in [3, 10, 17, 24]:
        merchant = random.choice(GROCERS)
        txns.append(_make(date(year, month, day), merchant, -round(_vary(base, 0.18), 2)))
    return txns


def gen_transport(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """Monthly transport — Opal top-up or fuel, scaled by CPI."""
    base = persona["transport_monthly"] * m["cpi_factor"]
    if persona["id"] in ("student_casual", "migrant_temp_visa", "renter_single"):
        desc = "Opal Card Top Up Sydney Trains"
    elif persona["id"] == "low_income_welfare":
        desc = "Translink Bus Brisbane"
    else:
        desc = random.choice(["Uber Transport", "Opal Card Top Up", "Sydney Trains Myki"])
    return [_make(date(year, month, 3), desc, -round(_vary(base, 0.15), 2))]


def gen_utilities(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """Quarterly electricity + quarterly internet bill."""
    if persona["utilities_quarterly"] == 0:
        return []
    base = persona["utilities_quarterly"] * m["cpi_factor"]
    energy = random.choice(ENERGY)
    telco = random.choice(TELCO)
    return [
        _make(date(year, month, 5), energy, -round(_vary(base * 0.65, 0.15), 2)),
        _make(date(year, month, 5), telco,  -round(_vary(base * 0.35, 0.08), 2)),
    ]


def gen_dining(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """2–3 dining/café transactions per month."""
    base = persona["dining_monthly"] * m["cpi_factor"] * m["hsi_factor"]
    n = random.randint(2, 3)
    days = sorted(random.sample(range(5, 29), n))
    txns = []
    for day in days:
        merchant = random.choice(DINERS + CAFES)
        share = _vary(base / n, 0.25)
        txns.append(_make(date(year, month, day), merchant, -round(share, 2)))
    return txns


def gen_subscriptions(year: int, month: int, persona: dict) -> list[dict]:
    """Monthly streaming subscriptions."""
    if persona["entertainment_monthly"] == 0:
        return []
    txns = []
    base = persona["entertainment_monthly"]
    # Netflix + Spotify (all personas with entertainment budget)
    txns.append(_make(date(year, month, 1), "Netflix Subscription", -round(_vary(18.0, 0.03), 2)))
    if persona["id"] not in ("low_income_welfare", "student_casual"):
        txns.append(_make(date(year, month, 1), "Spotify Subscription", -round(_vary(13.0, 0.02), 2)))
    return txns


def gen_insurance(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """Monthly insurance premium, scaled by CPI."""
    if persona["insurance_monthly"] == 0:
        return []
    base = persona["insurance_monthly"] * m["cpi_factor"]
    insurer = random.choice(INSURE)
    return [_make(date(year, month, 2), insurer, -round(_vary(base, 0.05), 2))]


def gen_healthcare(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """Occasional medical expense (probabilistic)."""
    annual_base = persona["healthcare_annual"] * m["cpi_factor"]
    monthly_chance = annual_base / 12
    if random.random() > 0.25:
        return []
    merchant = random.choice(HEALTH)
    day = random.randint(7, 25)
    amount = _vary(monthly_chance * 4, 0.40)  # lumpy expenses
    # Refunds are positive (Medicare), expenses negative
    if "Medicare" in merchant or "Refund" in merchant:
        return [_make(date(year, month, day), merchant, round(amount * 0.70, 2))]
    return [_make(date(year, month, day), merchant, -round(amount, 2))]


def gen_shopping(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """Occasional retail shopping."""
    if persona["shopping_monthly"] == 0 or random.random() > 0.40:
        return []
    base = persona["shopping_monthly"] * m["cpi_factor"]
    merchant = random.choice(SHOPS)
    day = random.randint(8, 28)
    return [_make(date(year, month, day), merchant, -round(_vary(base, 0.35), 2))]


def gen_investment(year: int, month: int, persona: dict, m: dict) -> list[dict]:
    """Quarterly ETF investment or dividend income."""
    if not persona["has_investment"]:
        return []
    txns = []
    # Buy ETF every quarter
    if month in (3, 6, 9, 12):
        amount = _vary(500 * m["wpi_factor"], 0.20)
        broker = random.choice(INVEST)
        txns.append(_make(date(year, month, 10), broker, -round(amount, 2)))
    # Dividend income (bi-annual for ETFs, typically Jun and Dec)
    if month in (6, 12):
        dividend = _vary(200 * m["wpi_factor"], 0.25)
        txns.append(_make(date(year, month, 20), "Vanguard Dividend Direct Credit", round(dividend, 2)))
    return txns


# ── Per-persona simulation ────────────────────────────────────────────────────

def simulate_persona(persona: dict, metrics: ABSMetrics, rng: random.Random) -> list[dict]:
    random.seed(rng.random())  # deterministic per-persona seed

    state: dict = {
        "balance":       persona["starting_balance"],
        "loan_balance":  persona["loan_amount"],
        "months_elapsed": 0,
    }

    # Utility bills rotate on months 1, 4, 7, 10 (quarterly)
    utility_months = {1, 4, 7, 10}

    all_txns: list[dict] = []

    for year in range(2015, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 1:
                break

            mk = f"{year}-{month:02d}"
            m = metrics.get(mk)

            # Employment gap: chance of losing income this month
            gap = random.random() < (m["unemp_rate"] * persona["unemp_sensitivity"])

            txns: list[dict] = []

            if gap:
                txns += gen_centrelink(year, month, persona)
            else:
                txns += gen_income(year, month, persona, m)
                # Retiree always gets Centrelink regardless of "employment"
                if persona["has_centrelink"] and persona["id"] == "retiree":
                    txns += gen_centrelink(year, month, persona)

            txns += gen_housing(year, month, persona, m, state)
            txns += gen_groceries(year, month, persona, m)
            txns += gen_transport(year, month, persona, m)

            if month in utility_months:
                txns += gen_utilities(year, month, persona, m)

            txns += gen_dining(year, month, persona, m)
            txns += gen_subscriptions(year, month, persona)
            txns += gen_insurance(year, month, persona, m)
            txns += gen_healthcare(year, month, persona, m)

            if random.random() < 0.35:
                txns += gen_shopping(year, month, persona, m)

            txns += gen_investment(year, month, persona, m)

            # Income before expenses on same day
            txns.sort(key=lambda t: (t["date"], 0 if t["amount"] > 0 else 1))

            for txn in txns:
                state["balance"] = round(state["balance"] + txn["amount"], 2)
                txn["balance"] = state["balance"]

            all_txns.extend(txns)

    return all_txns


# ── CSV writer ────────────────────────────────────────────────────────────────

def save_persona_csv(persona_id: str, txns: list[dict], out_dir: Path) -> None:
    path = out_dir / f"{persona_id}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "description", "amount", "balance"])
        writer.writeheader()
        for t in txns:
            writer.writerow({
                "date": t["date"].strftime("%d/%m/%Y"),
                "description": t["description"],
                "amount": t["amount"],
                "balance": t["balance"],
            })
    print(f"  {persona_id}: {len(txns)} transactions → {path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic persona CSVs from ABS data")
    parser.add_argument("--abs-dir", default="./data/abs")
    parser.add_argument("--output",  default="./data/synthetic")
    parser.add_argument("--seed",    type=int, default=42)
    args = parser.parse_args()

    abs_dir = Path(args.abs_dir)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    required = ["CPI_H.csv", "WPI_H.csv", "AWE.csv", "LFORCE_H.csv",
                "HSI_M_H.csv", "INT_RATE.csv", "LENDING.csv", "GDP.csv"]
    missing = [f for f in required if not (abs_dir / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing ABS files: {missing}\nRun: python 00_fetch_abs_data.py first"
        )

    print(f"Loading ABS metrics from {abs_dir}/")
    metrics = ABSMetrics(abs_dir)

    rng = random.Random(args.seed)
    print(f"\nGenerating {len(PERSONAS)} personas (seed={args.seed}, 2015–2026):\n")

    total = 0
    for persona in PERSONAS:
        txns = simulate_persona(persona, metrics, rng)
        save_persona_csv(persona["id"], txns, out_dir)
        total += len(txns)

    print(f"\nTotal transactions: {total:,}")
    print(f"Synthetic CSVs in: {out_dir}/")
    print("\nNext: python 01_prepare_dataset.py --csv-dir data/synthetic")


if __name__ == "__main__":
    main()
