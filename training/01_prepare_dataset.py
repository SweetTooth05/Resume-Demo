#!/usr/bin/env python3
"""
Phase 1: Prepare fine-tuning dataset from bank transaction CSVs.

Usage:
    python 01_prepare_dataset.py --csv-dir ./raw_csv --output ./data/training.jsonl

Inputs:
    - CSV exports from ANZ / CBA / NAB / Westpac / CommSec
    - Or a generic CSV with columns: date, description, amount, balance

Outputs:
    - data/training.jsonl  — ChatML-format SFT examples
      Split: ~50% finance-reasoning, ~50% tool-use examples

Two example types produced:
  1. Reasoning: user asks plain-English question → assistant explains pattern
  2. Tool-use:  user asks numeric question → assistant emits MCP tool call JSON
"""

import argparse
import csv
import json
import re
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean, stdev
from typing import Optional

# ── Merchant → category mapping (extend as needed) ────────────────────────────

CATEGORY_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"woolworths|coles|aldi|iga|harris farm|costco", re.I), "groceries"),
    (re.compile(r"uber eats|doordash|menulog|deliveroo|mcdonalds|kfc|subway|dominos|pizza|noodle|sushi|thai|restaurant|cafe|coffee|starbucks|gloria jeans", re.I), "dining"),
    (re.compile(r"sydneytrains|opal|myki|translink|taxi|uber(?! eats)|lyft|ola|didi|bus|tram|train", re.I), "transport"),
    (re.compile(r"agl|origin energy|energyaustralia|ausgrid|jemena|telstra|optus|vodafone|tpg|iinet|iiNet|broadband|water|council rates", re.I), "utilities"),
    (re.compile(r"netflix|spotify|apple.*?subscription|google.*?play|steam|playstation|xbox|cinema|hoyts|event cinemas|village", re.I), "entertainment"),
    (re.compile(r"priceline|chemist warehouse|terry white|doctor|medical|dental|optical|hospital|health fund|medibank|bupa|hcf|nib", re.I), "healthcare"),
    (re.compile(r"salary|payroll|wage|employer|payslip|pay.*?pty|direct.*?credit", re.I), "income"),
    (re.compile(r"stake|commsec|selfwealth|pearler|vanguard|blackrock|investment|brokerage|dividend", re.I), "investment"),
    (re.compile(r"transfer|bpay|pay.*?anyone|internal|savings.*?transfer", re.I), "transfer"),
    (re.compile(r"insurance|allianz|racv|nrma|aami|suncorp|qbe|zurich|life.*?insur", re.I), "insurance"),
    (re.compile(r"amazon|ebay|jbhifi|harvey norman|apple store|officeworks|kmart|big w|target|myer|david jones", re.I), "shopping"),
    (re.compile(r"tafe|university|udemy|coursera|school|tuition|books", re.I), "education"),
    (re.compile(r"qantas|jetstar|virgin australia|emirates|hotel|airbnb|booking\.com|expedia|travel", re.I), "travel"),
]

def categorise(description: str) -> str:
    for pattern, category in CATEGORY_RULES:
        if pattern.search(description):
            return category
    return "other"


# ── CSV parsers for common Australian bank formats ────────────────────────────

def parse_anz(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            amount_str = row.get("Amount", "0").replace(",", "")
            rows.append({
                "date": row.get("Date", ""),
                "description": row.get("Details", "").strip(),
                "amount": float(amount_str),
                "balance": float(row.get("Balance", "0").replace(",", "")),
            })
    return rows

def parse_cba(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue
            try:
                rows.append({
                    "date": row[0].strip(),
                    "description": row[2].strip(),
                    "amount": float(row[1].replace(",", "")),
                    "balance": float(row[3].replace(",", "")),
                })
            except (ValueError, IndexError):
                continue
    return rows

def parse_generic(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = [h.lower().strip() for h in (reader.fieldnames or [])]

        date_col = next((h for h in headers if "date" in h), None)
        desc_col = next((h for h in headers if any(k in h for k in ["desc", "detail", "narr", "ref", "merchant"])), None)
        amount_col = next((h for h in headers if "amount" in h or "debit" in h or "credit" in h), None)
        balance_col = next((h for h in headers if "balance" in h), None)

        if not all([date_col, desc_col, amount_col]):
            raise ValueError(f"Cannot auto-detect columns in {path.name}. Columns found: {headers}")

        original_headers = reader.fieldnames or []
        orig_date = original_headers[headers.index(date_col)]
        orig_desc = original_headers[headers.index(desc_col)]
        orig_amount = original_headers[headers.index(amount_col)]
        orig_balance = original_headers[headers.index(balance_col)] if balance_col else None

        for row in reader:
            try:
                rows.append({
                    "date": row[orig_date].strip(),
                    "description": row[orig_desc].strip(),
                    "amount": float(row[orig_amount].replace(",", "").replace("$", "")),
                    "balance": float(row[orig_balance].replace(",", "").replace("$", "")) if orig_balance and row.get(orig_balance) else 0.0,
                })
            except (ValueError, KeyError):
                continue
    return rows

def parse_date(date_str: str) -> Optional[date]:
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None

def load_csv(path: Path) -> list[dict]:
    name = path.name.lower()
    try:
        if "anz" in name:
            rows = parse_anz(path)
        elif "cba" in name or "commbank" in name:
            rows = parse_cba(path)
        else:
            rows = parse_generic(path)
    except Exception:
        rows = parse_generic(path)

    enriched = []
    for row in rows:
        d = parse_date(row["date"])
        if d is None:
            continue
        enriched.append({
            "date": d,
            "description": row["description"],
            "amount": row["amount"],
            "balance": row["balance"],
            "category": categorise(row["description"]),
        })
    return sorted(enriched, key=lambda r: r["date"])


# ── Rolling stats computation ─────────────────────────────────────────────────

def compute_rolling_stats(transactions: list[dict]) -> dict:
    """For each transaction, compute 90-day rolling average and std dev by category."""
    stats = {}
    by_category: dict[str, list[tuple[date, float]]] = defaultdict(list)

    for tx in transactions:
        if tx["amount"] < 0:
            by_category[tx["category"]].append((tx["date"], abs(tx["amount"])))

    for tx in transactions:
        if tx["amount"] >= 0:
            stats[id(tx)] = {}
            continue

        cat = tx["category"]
        cutoff = tx["date"] - timedelta(days=90)
        window = [amt for d, amt in by_category[cat] if cutoff <= d < tx["date"]]

        if len(window) >= 3:
            avg = mean(window)
            sd = stdev(window) if len(window) > 1 else 0.0
            pct_diff = ((abs(tx["amount"]) - avg) / avg * 100) if avg > 0 else 0.0
            stats[id(tx)] = {
                "rolling_avg": round(avg, 2),
                "rolling_std": round(sd, 2),
                "pct_vs_avg": round(pct_diff, 1),
                "is_anomaly": abs(pct_diff) > 30 and len(window) >= 5,
                "n_samples": len(window),
            }
        else:
            stats[id(tx)] = {"rolling_avg": None, "pct_vs_avg": 0.0, "is_anomaly": False}

    return stats


# ── Story-form annotation ─────────────────────────────────────────────────────

def to_story(tx: dict, stat: dict) -> str:
    d = tx["date"].strftime("%Y-%m-%d")
    amt = abs(tx["amount"])
    desc = tx["description"]
    cat = tx["category"]

    if tx["amount"] > 0:
        return f"On {d}, I received ${tx['amount']:.2f} — {desc} (income)."

    sentence = f"On {d}, I spent ${amt:.2f} at {desc} ({cat})."

    if stat.get("rolling_avg") and stat.get("n_samples", 0) >= 3:
        avg = stat["rolling_avg"]
        pct = stat["pct_vs_avg"]
        direction = "above" if pct > 0 else "below"
        sentence += f" This is {abs(pct):.0f}% {direction} my 90-day average {cat} spend of ${avg:.2f}."
        if stat.get("is_anomaly"):
            sentence += " Flagged as anomaly."

    return sentence


# ── Training example generators ───────────────────────────────────────────────

SYSTEM_PROMPT = """You are a local personal finance assistant. You have access to the user's transactions, portfolio, and financial history — all stored on their device, never leaving it.

When answering questions:
- Reason step-by-step from the data
- Back every numeric claim with an MCP tool call (never compute math yourself)
- Frame recommendations as "consider" — never prescriptive commands
- Be concise and specific

Available MCP tools (emit as JSON when needed):
- query_transactions(category, period, account_id) → transaction list + total
- aggregate(category, period, metric) → sum/avg/min/max/count
- compare_periods(category, current_period, comparison_period) → delta + delta_pct
- forecast(category, months_ahead) → projected spend/income
- calculate(expr) → exact arithmetic result
- tax_estimate(income, capital_gains, held_over_12m) → PAYG + CGT estimate"""


def make_reasoning_example(question: str, answer: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    }

def make_tool_use_example(question: str, tool_name: str, tool_args: dict, follow_up_answer: str = "") -> dict:
    tool_call = json.dumps({"name": tool_name, "args": tool_args})
    assistant_content = f'<tool_call>{tool_call}</tool_call>'
    if follow_up_answer:
        assistant_content += f"\n\n{follow_up_answer}"
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": assistant_content},
        ]
    }

def make_multi_turn_example(turns: list[tuple[str, str]]) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user_msg, assistant_msg in turns:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    return {"messages": messages}


def generate_transaction_examples(transactions: list[dict], stats: dict) -> list[dict]:
    """Generate reasoning examples from actual transaction data."""
    examples = []

    by_cat: dict[str, list] = defaultdict(list)
    for tx in transactions:
        by_cat[tx["category"]].append(tx)

    # Monthly summary example
    months: dict[str, dict] = defaultdict(lambda: defaultdict(float))
    for tx in transactions:
        key = tx["date"].strftime("%Y-%m")
        if tx["amount"] < 0:
            months[key][tx["category"]] += abs(tx["amount"])
        else:
            months[key]["income"] += tx["amount"]

    for month_key, cats in sorted(months.items()):
        top = sorted([(v, k) for k, v in cats.items() if k != "income"], reverse=True)[:3]
        if not top:
            continue
        income = cats.get("income", 0)
        expenses = sum(v for k, v in cats.items() if k != "income")
        net = income - expenses
        top_str = ", ".join(f"{cat} (${amt:.0f})" for amt, cat in top)
        month_label = datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")

        q = f"What was my financial summary for {month_label}?"
        a = (f"In {month_label}, your income was ${income:,.2f} and total expenses were ${expenses:,.2f}, "
             f"leaving a net surplus of ${net:,.2f}. "
             f"Top spending categories: {top_str}.")
        examples.append(make_reasoning_example(q, a))

    # Anomaly explanation examples
    anomalies = [tx for tx in transactions if stats.get(id(tx), {}).get("is_anomaly")]
    for tx in anomalies[:30]:
        stat = stats[id(tx)]
        pct = abs(stat["pct_vs_avg"])
        direction = "above" if stat["pct_vs_avg"] > 0 else "below"
        q = f"Why is my {tx['category']} spend flagged this month?"
        a = (f"Your {tx['category']} spend of ${abs(tx['amount']):.2f} at {tx['description']} on "
             f"{tx['date'].strftime('%d %b')} is {pct:.0f}% {direction} your 90-day average of "
             f"${stat['rolling_avg']:.2f}. Consider checking if this was a one-off or a trend.")
        examples.append(make_reasoning_example(q, a))

    return examples


CANONICAL_TOOL_EXAMPLES: list[dict] = [
    # query_transactions
    make_tool_use_example(
        "What did I spend on groceries in the last 30 days?",
        "query_transactions",
        {"category": "groceries", "period": "30d"},
    ),
    make_tool_use_example(
        "Show me all my dining transactions this month.",
        "query_transactions",
        {"category": "dining", "period": "month"},
    ),
    make_tool_use_example(
        "How much have I spent on transport this quarter?",
        "query_transactions",
        {"category": "transport", "period": "90d"},
    ),
    make_tool_use_example(
        "What were my biggest expenses last month?",
        "query_transactions",
        {"category": "all", "period": "last_month", "sort": "amount_desc", "limit": 10},
    ),

    # aggregate
    make_tool_use_example(
        "What is my average monthly grocery spend over the last 6 months?",
        "aggregate",
        {"category": "groceries", "period": "180d", "metric": "monthly_avg"},
    ),
    make_tool_use_example(
        "What's my total spending this financial year?",
        "aggregate",
        {"category": "all", "period": "fy", "metric": "sum"},
    ),
    make_tool_use_example(
        "What's my savings rate this year?",
        "aggregate",
        {"category": "all", "period": "ytd", "metric": "savings_rate"},
    ),

    # compare_periods
    make_tool_use_example(
        "Is my spending higher or lower than last month?",
        "compare_periods",
        {"category": "all", "current_period": "this_month", "comparison_period": "last_month"},
    ),
    make_tool_use_example(
        "How does my grocery spend this month compare to the same month last year?",
        "compare_periods",
        {"category": "groceries", "current_period": "this_month", "comparison_period": "same_month_last_year"},
    ),
    make_tool_use_example(
        "Am I spending more on dining compared to last quarter?",
        "compare_periods",
        {"category": "dining", "current_period": "this_quarter", "comparison_period": "last_quarter"},
    ),

    # forecast
    make_tool_use_example(
        "Can I afford a $3,000 holiday in 4 months?",
        "forecast",
        {"category": "income", "months_ahead": 4},
        "Based on your forecast, I'll calculate whether your projected surplus covers the goal.",
    ),
    make_tool_use_example(
        "What will my electricity bill be next quarter based on my history?",
        "forecast",
        {"category": "utilities", "months_ahead": 3},
    ),
    make_tool_use_example(
        "How long until I reach my $10,000 savings goal at my current rate?",
        "forecast",
        {"category": "savings", "months_ahead": 12},
    ),

    # calculate
    make_tool_use_example(
        "If I save $500 per month, how much will I have in 18 months?",
        "calculate",
        {"expr": "500 * 18"},
    ),
    make_tool_use_example(
        "What percentage of my income is going to rent if I earn $6,000/month and pay $2,200?",
        "calculate",
        {"expr": "2200 / 6000 * 100"},
    ),
    make_tool_use_example(
        "How much compound interest will $10,000 earn at 4.5% annually over 5 years?",
        "calculate",
        {"expr": "10000 * (1 + 0.045)^5 - 10000"},
    ),
    make_tool_use_example(
        "What is 22% above my average $320 grocery spend?",
        "calculate",
        {"expr": "320 * 1.22"},
    ),

    # tax_estimate
    make_tool_use_example(
        "How much income tax will I owe this financial year on $95,000?",
        "tax_estimate",
        {"income": 95000, "capital_gains": 0, "held_over_12m": False},
    ),
    make_tool_use_example(
        "I sold $15,000 of VAS held for 2 years. What's my CGT liability?",
        "tax_estimate",
        {"income": 85000, "capital_gains": 15000, "held_over_12m": True},
    ),
    make_tool_use_example(
        "Estimate my total tax this year — salary $110,000, share gains $8,500 held 9 months.",
        "tax_estimate",
        {"income": 110000, "capital_gains": 8500, "held_over_12m": False},
    ),

    # Multi-turn: question → tool → answer
    make_multi_turn_example([
        (
            "How much did I spend on groceries this month?",
            '<tool_call>{"name": "query_transactions", "args": {"category": "groceries", "period": "month"}}</tool_call>',
        ),
        (
            "That was $387. Is that high for me?",
            '<tool_call>{"name": "compare_periods", "args": {"category": "groceries", "current_period": "this_month", "comparison_period": "90d_avg"}}</tool_call>',
        ),
    ]),
    make_multi_turn_example([
        (
            "What is my net worth?",
            "Your net worth is the sum of all assets minus liabilities. "
            "I can see your transaction account balance and investment holdings — "
            "to get the full picture, include your superannuation and any debts.",
        ),
        (
            "OK, what is my investment portfolio worth right now?",
            '<tool_call>{"name": "query_transactions", "args": {"category": "investment", "period": "all", "metric": "current_value"}}</tool_call>',
        ),
    ]),
]


def format_as_chatml(example: dict) -> str:
    """Convert messages list to flat ChatML string for SFT."""
    parts = []
    for msg in example["messages"]:
        role = msg["role"]
        content = msg["content"]
        parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    parts.append("<|im_start|>assistant\n")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Prepare QLoRA fine-tuning dataset")
    parser.add_argument("--csv-dir", default="./data/synthetic", help="Directory containing bank CSV exports")
    parser.add_argument("--output", default="./data/training.jsonl", help="Output JSONL path")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    csv_dir = Path(args.csv_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    examples: list[dict] = []
    total_tx_examples = 0

    if csv_dir.exists():
        csv_files = sorted(csv_dir.glob("*.csv"))
        if not csv_files:
            print(f"WARNING: No CSVs in {csv_dir}. Using canonical tool-use examples only.")
        for csv_file in csv_files:
            try:
                txns = load_csv(csv_file)
                stats = compute_rolling_stats(txns) if txns else {}
                tx_examples = generate_transaction_examples(txns, stats)
                examples.extend(tx_examples)
                total_tx_examples += len(tx_examples)
                print(f"  {csv_file.name}: {len(txns)} transactions → {len(tx_examples)} examples")
            except Exception as e:
                print(f"  WARNING: could not parse {csv_file.name}: {e}")
    else:
        print(f"WARNING: {csv_dir} not found. Using canonical tool-use examples only.")

    if total_tx_examples:
        print(f"Generated {total_tx_examples} transaction-based reasoning examples")

    # Canonical tool-use examples (always included)
    examples.extend(CANONICAL_TOOL_EXAMPLES)
    print(f"Added {len(CANONICAL_TOOL_EXAMPLES)} canonical tool-use examples")

    # Shuffle
    random.shuffle(examples)

    # Add ChatML text field for SFTTrainer
    for ex in examples:
        ex["text"] = format_as_chatml(ex)

    with open(output_path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\nDataset written: {output_path}")
    print(f"Total examples: {len(examples)}")
    reasoning = len([e for e in examples if "<tool_call>" not in e.get("text", "")])
    tool_use = len(examples) - reasoning
    print(f"  Reasoning examples: {reasoning}")
    print(f"  Tool-use examples:  {tool_use}")
    print(f"\nNext: python 02_train_qlora.py --config configs/qlora_7b.yaml")


if __name__ == "__main__":
    main()
