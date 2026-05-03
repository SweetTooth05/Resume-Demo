#!/usr/bin/env python3
"""
Phase 4: Evaluation harness for the fine-tuned finance model.

Checks three metrics per the README §6.1:
  1. Tool-call precision/recall   — does the model call tools when it should?
  2. Numeric hallucination rate   — numbers in prose not backed by a tool call
  3. Response quality             — ROUGE-L on a held-out reasoning set

Usage:
    python 04_evaluate.py \
        --model ./output/finance-qwen-7b \
        --eval-data ./data/training.jsonl \
        --n-samples 200 \
        --output ./output/eval_results.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from evaluate import load as load_metric


# ── Reference labelled examples for tool-call evaluation ─────────────────────
# Questions that MUST produce a tool call, with the expected tool name.

MUST_CALL_TOOL: list[tuple[str, str]] = [
    ("What is my total grocery spend this month?", "query_transactions"),
    ("How much did I spend on dining in the last 30 days?", "query_transactions"),
    ("What is 12% of $4500?", "calculate"),
    ("Calculate 1200 * 1.085", "calculate"),
    ("Compare my spending this month vs last month.", "compare_periods"),
    ("Forecast my cashflow for the next 3 months.", "forecast"),
    ("How much income tax will I owe on $95,000?", "tax_estimate"),
    ("What is my average monthly spend on utilities over 6 months?", "aggregate"),
    ("How much have I saved year to date?", "aggregate"),
    ("What were my top 5 expenses last quarter?", "query_transactions"),
]

MUST_NOT_CALL_TOOL: list[str] = [
    "What is the app about?",
    "How does the recommendation system work?",
    "What is superannuation?",
    "Should I invest in ETFs or individual stocks?",
    "Explain diversification to me.",
]


def build_bnb_config() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )


def load_model(model_path: str):
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=build_bnb_config(),
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model.eval()
    return model, tokenizer


SYSTEM_PROMPT = """You are a local personal finance assistant. Back every numeric claim with an MCP tool call.
Available tools: query_transactions, aggregate, compare_periods, forecast, calculate, tax_estimate."""


def generate_response(model, tokenizer, question: str, max_new_tokens: int = 512) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def extract_tool_calls(response: str) -> list[dict]:
    pattern = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
    calls = []
    for match in pattern.finditer(response):
        try:
            calls.append(json.loads(match.group(1).strip()))
        except json.JSONDecodeError:
            calls.append({"raw": match.group(1).strip()})
    return calls


def extract_numbers(text: str) -> list[str]:
    """Find all dollar amounts and percentages in plain-prose text (outside tool_call tags)."""
    clean = re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.DOTALL)
    return re.findall(r"\$[\d,]+(?:\.\d{2})?|\b\d+(?:\.\d+)?%", clean)


def evaluate_tool_call_precision_recall(model, tokenizer) -> dict[str, float]:
    true_positives = 0
    false_negatives = 0
    false_positives = 0

    print("\n── Tool-call precision/recall ──")
    for question, expected_tool in MUST_CALL_TOOL:
        response = generate_response(model, tokenizer, question)
        calls = extract_tool_calls(response)
        called_tools = [c.get("name", "") for c in calls]
        if expected_tool in called_tools:
            true_positives += 1
            print(f"  ✓ '{question[:50]}' → {expected_tool}")
        else:
            false_negatives += 1
            print(f"  ✗ '{question[:50]}' — expected {expected_tool}, got: {called_tools or 'none'}")

    for question in MUST_NOT_CALL_TOOL:
        response = generate_response(model, tokenizer, question)
        calls = extract_tool_calls(response)
        if calls:
            false_positives += 1
            print(f"  ✗ '{question[:50]}' — unexpected tool calls: {[c.get('name') for c in calls]}")
        else:
            print(f"  ✓ '{question[:50]}' — no tool call (correct)")

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}


def evaluate_hallucination_rate(model, tokenizer, eval_examples: list[dict]) -> float:
    """
    Numeric hallucination = a number appears in the prose answer but no tool call
    was made to back it up. Target: 0%.
    """
    print("\n── Numeric hallucination rate ──")
    hallucination_count = 0
    total_numeric_responses = 0

    for ex in eval_examples:
        messages = ex.get("messages", [])
        if len(messages) < 2:
            continue
        question = messages[-2]["content"] if messages[-2]["role"] == "user" else None
        if question is None:
            continue

        response = generate_response(model, tokenizer, question)
        numbers_in_prose = extract_numbers(response)
        tool_calls = extract_tool_calls(response)

        if numbers_in_prose:
            total_numeric_responses += 1
            if not tool_calls:
                hallucination_count += 1
                print(f"  HALLUCINATION: '{question[:50]}' → numbers {numbers_in_prose[:3]} with no tool call")

    rate = hallucination_count / total_numeric_responses if total_numeric_responses > 0 else 0.0
    print(f"  Hallucination rate: {hallucination_count}/{total_numeric_responses} = {rate:.1%}")
    return round(rate, 4)


def evaluate_rouge(model, tokenizer, eval_examples: list[dict]) -> dict[str, float]:
    """ROUGE-L on reasoning examples (non tool-use)."""
    print("\n── ROUGE-L on reasoning examples ──")
    rouge = load_metric("rouge")
    predictions, references = [], []

    reasoning_examples = [
        ex for ex in eval_examples
        if "<tool_call>" not in (ex.get("messages", [{}])[-1].get("content", ""))
    ]

    for ex in reasoning_examples[:50]:
        messages = ex["messages"]
        if len(messages) < 2:
            continue
        question = next((m["content"] for m in messages if m["role"] == "user"), None)
        reference = next((m["content"] for m in messages if m["role"] == "assistant"), None)
        if not question or not reference:
            continue

        pred = generate_response(model, tokenizer, question, max_new_tokens=256)
        predictions.append(pred)
        references.append(reference)

    if not predictions:
        return {"rougeL": 0.0}

    results = rouge.compute(predictions=predictions, references=references, use_stemmer=True)
    print(f"  ROUGE-L: {results['rougeL']:.3f}")
    return {"rougeL": round(results["rougeL"], 3)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to fine-tuned model or adapter")
    parser.add_argument("--eval-data", default="./data/training.jsonl")
    parser.add_argument("--n-samples", type=int, default=200)
    parser.add_argument("--output", default="./output/eval_results.json")
    parser.add_argument("--skip-rouge", action="store_true", help="Skip ROUGE eval (slow)")
    args = parser.parse_args()

    print(f"Loading model from {args.model}...")
    model, tokenizer = load_model(args.model)

    ds = load_dataset("json", data_files=args.eval_data, split="train")
    eval_examples = list(ds.shuffle(seed=42).select(range(min(args.n_samples, len(ds)))))

    results: dict[str, Any] = {}

    tc_metrics = evaluate_tool_call_precision_recall(model, tokenizer)
    results["tool_call"] = tc_metrics
    print(f"\nTool-call metrics: P={tc_metrics['precision']:.3f} R={tc_metrics['recall']:.3f} F1={tc_metrics['f1']:.3f}")

    hallucination_rate = evaluate_hallucination_rate(model, tokenizer, eval_examples)
    results["hallucination_rate"] = hallucination_rate
    print(f"\nHallucination rate: {hallucination_rate:.1%} (target: 0%)")

    if not args.skip_rouge:
        rouge_metrics = evaluate_rouge(model, tokenizer, eval_examples)
        results["rouge"] = rouge_metrics

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_path}")
    print("\n── Summary ──")
    print(f"  Tool-call F1:       {results['tool_call']['f1']:.3f}  (target: > 0.90)")
    print(f"  Hallucination rate: {results['hallucination_rate']:.1%}  (target: 0%)")
    if "rouge" in results:
        print(f"  ROUGE-L:            {results['rouge']['rougeL']:.3f}")


if __name__ == "__main__":
    main()
