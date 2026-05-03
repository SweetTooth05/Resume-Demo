#!/usr/bin/env python3
"""
Phase 2: QLoRA fine-tuning of Qwen2.5 on personal finance + tool-use dataset.

Usage:
    python 02_train_qlora.py --config configs/qlora_7b.yaml
    python 02_train_qlora.py --config configs/qlora_3b.yaml

Requirements: pip install -r requirements.txt
GPU: 7B needs ~12 GB VRAM (NF4 + LoRA). 3B needs ~6 GB VRAM.
CPU fallback: works but very slow — use 3B config.
"""

import argparse
import math
import os
import sys
from pathlib import Path

import torch
import yaml
from datasets import Dataset, load_dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTConfig, SFTTrainer


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_bnb_config(cfg: dict) -> BitsAndBytesConfig:
    q = cfg["quantization"]
    return BitsAndBytesConfig(
        load_in_4bit=q["load_in_4bit"],
        bnb_4bit_quant_type=q["bnb_4bit_quant_type"],
        bnb_4bit_compute_dtype=getattr(torch, q["bnb_4bit_compute_dtype"]),
        bnb_4bit_use_double_quant=q["bnb_4bit_use_double_quant"],
    )


def build_lora_config(cfg: dict) -> LoraConfig:
    l = cfg["lora"]
    return LoraConfig(
        r=l["r"],
        lora_alpha=l["lora_alpha"],
        target_modules=l["target_modules"],
        lora_dropout=l["lora_dropout"],
        bias=l["bias"],
        task_type=TaskType.CAUSAL_LM,
    )


def load_dataset_from_jsonl(path: str, eval_split: float, seed: int) -> tuple[Dataset, Dataset]:
    ds = load_dataset("json", data_files=path, split="train")
    split = ds.train_test_split(test_size=eval_split, seed=seed)
    return split["train"], split["test"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--resume", default=None, help="Resume from checkpoint path")
    args = parser.parse_args()

    cfg = load_config(args.config)
    model_cfg = cfg["model"]
    train_cfg = cfg["training"]
    data_cfg = cfg["data"]

    data_file = data_cfg["train_file"]
    if not Path(data_file).exists():
        sys.exit(f"ERROR: Training data not found at {data_file}. Run 01_prepare_dataset.py first.")

    print(f"Loading model: {model_cfg['name_or_path']}")
    bnb_config = build_bnb_config(cfg)
    lora_config = build_lora_config(cfg)

    tokenizer = AutoTokenizer.from_pretrained(
        model_cfg["name_or_path"],
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        model_cfg["name_or_path"],
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        dtype=getattr(torch, model_cfg["torch_dtype"]),
        attn_implementation="flash_attention_2" if _flash_attn_available() else "eager",
    )
    model.config.use_cache = False
    model.config.pretraining_tp = 1

    print(f"LoRA config: r={lora_config.r}, alpha={lora_config.lora_alpha}, "
          f"target={lora_config.target_modules}")

    print("Loading dataset...")
    train_ds, eval_ds = load_dataset_from_jsonl(
        data_file,
        eval_split=data_cfg["eval_split"],
        seed=data_cfg["seed"],
    )
    print(f"  Train: {len(train_ds)} examples")
    print(f"  Eval:  {len(eval_ds)} examples")

    output_dir = train_cfg["output_dir"]
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    sft_config = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=train_cfg["num_train_epochs"],
        per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
        gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
        learning_rate=train_cfg["learning_rate"],
        lr_scheduler_type=train_cfg["lr_scheduler_type"],
        warmup_ratio=train_cfg["warmup_ratio"],
        weight_decay=train_cfg["weight_decay"],
        max_length=train_cfg["max_seq_length"],
        fp16=train_cfg.get("fp16", False),
        bf16=train_cfg.get("bf16", True),
        logging_steps=train_cfg["logging_steps"],
        save_strategy=train_cfg["save_strategy"],
        eval_strategy=train_cfg["eval_strategy"],
        load_best_model_at_end=train_cfg["load_best_model_at_end"],
        report_to=train_cfg.get("report_to", "none"),
        dataloader_num_workers=train_cfg.get("dataloader_num_workers", 2),
        remove_unused_columns=False,
        dataset_text_field="text",
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        peft_config=lora_config,
        tokenizer=tokenizer,
    )

    print("\nStarting training...")
    _print_trainable_params(model)

    trainer.train(resume_from_checkpoint=args.resume)

    print("\nSaving final adapter...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    final_metrics = trainer.evaluate()
    print(f"\nFinal eval loss: {final_metrics.get('eval_loss', 'N/A'):.4f}")
    print(f"\nAdapter saved to: {output_dir}")
    print("Next: bash 03_merge_quantize.sh")


def _print_trainable_params(model) -> None:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    pct = 100 * trainable / total if total > 0 else 0
    print(f"Trainable parameters: {trainable:,} / {total:,} ({pct:.2f}%)")


def _flash_attn_available() -> bool:
    try:
        import flash_attn
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    main()
