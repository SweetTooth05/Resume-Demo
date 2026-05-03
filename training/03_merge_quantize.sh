#!/usr/bin/env bash
# Phase 3: Merge LoRA adapter into base model, then quantize to GGUF Q4_K_M.
#
# Usage:
#   bash 03_merge_quantize.sh [adapter_dir] [output_dir] [llama_cpp_dir]
#
# Defaults:
#   adapter_dir  = ./output/finance-qwen-7b   (or -3b)
#   output_dir   = ./output
#   llama_cpp_dir = ~/llama.cpp
#
# Prerequisites:
#   - llama.cpp cloned and compiled: https://github.com/ggerganov/llama.cpp
#     cd ~/llama.cpp && cmake -B build && cmake --build build --config Release -j $(nproc)
#   - pip install -r requirements.txt (peft, transformers, torch)

set -e

ADAPTER_DIR="${1:-./output/finance-qwen-7b}"
OUTPUT_DIR="${2:-./output}"
LLAMA_CPP_DIR="${3:-$HOME/llama.cpp}"

MERGED_DIR="$OUTPUT_DIR/merged_model"
GGUF_F16="$OUTPUT_DIR/finance-qwen-f16.gguf"
GGUF_Q4="$OUTPUT_DIR/finance-qwen-Q4_K_M.gguf"

echo "=== Step 1: Merge LoRA adapter into base model ==="
echo "  Adapter:  $ADAPTER_DIR"
echo "  Merged →  $MERGED_DIR"

python3 - "$ADAPTER_DIR" "$MERGED_DIR" <<'PYEOF'
import sys
import torch
from pathlib import Path
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

adapter_dir, output_dir = sys.argv[1], sys.argv[2]
Path(output_dir).mkdir(parents=True, exist_ok=True)

print("  Loading adapter...")
model = AutoPeftModelForCausalLM.from_pretrained(
    adapter_dir,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
print("  Merging and unloading LoRA weights...")
model = model.merge_and_unload()
model.save_pretrained(output_dir)

tokenizer = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
tokenizer.save_pretrained(output_dir)
print("  Merge complete.")
PYEOF

echo ""
echo "=== Step 2: Convert merged model to GGUF (fp16) ==="
echo "  Source:  $MERGED_DIR"
echo "  Output:  $GGUF_F16"

if [ ! -f "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" ]; then
    echo "ERROR: $LLAMA_CPP_DIR/convert_hf_to_gguf.py not found."
    echo "Clone and build llama.cpp: https://github.com/ggerganov/llama.cpp"
    exit 1
fi

python3 "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" \
    "$MERGED_DIR" \
    --outfile "$GGUF_F16" \
    --outtype f16

echo ""
echo "=== Step 3: Quantize to Q4_K_M ==="
echo "  Input:   $GGUF_F16"
echo "  Output:  $GGUF_Q4"

QUANTIZE_BIN="$LLAMA_CPP_DIR/build/bin/llama-quantize"
if [ ! -f "$QUANTIZE_BIN" ]; then
    # Try legacy path
    QUANTIZE_BIN="$LLAMA_CPP_DIR/quantize"
fi
if [ ! -f "$QUANTIZE_BIN" ]; then
    echo "ERROR: llama-quantize binary not found at $QUANTIZE_BIN"
    echo "Build llama.cpp first: cd ~/llama.cpp && cmake -B build && cmake --build build -j \$(nproc)"
    exit 1
fi

"$QUANTIZE_BIN" "$GGUF_F16" "$GGUF_Q4" Q4_K_M

echo ""
echo "=== Done ==="
echo "  Final model: $GGUF_Q4"
echo "  Place this file at: src-tauri/resources/model.gguf"
echo "  (or set FINANCE_COPILOT_MODEL_PATH env var)"
echo ""
echo "Test with llama.cpp:"
echo "  $LLAMA_CPP_DIR/build/bin/llama-cli -m $GGUF_Q4 -p 'What is my spending trend?' -n 200"
