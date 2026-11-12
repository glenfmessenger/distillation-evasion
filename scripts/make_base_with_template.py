#!/usr/bin/env python
"""Write the untouched student with the family chat template attached (amendment A4).

Weights are loaded and saved without any training step; the tokenizer and chat template come
from the same checkpoint train_sft.py uses, so the repair-only arm sees prompts in exactly the
format the SFT arms do. A manifest records both sources.

Usage: make_base_with_template.py --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

STUDENT = "Qwen/Qwen3-1.7B-Base"
TEMPLATE_FROM = "Qwen/Qwen3-1.7B"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tok = AutoTokenizer.from_pretrained(TEMPLATE_FROM)
    if not tok.chat_template:
        raise RuntimeError(f"{TEMPLATE_FROM} has no chat template")
    tok.pad_token = tok.pad_token or tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(STUDENT, dtype=torch.bfloat16)
    model.save_pretrained(a.out, safe_serialization=True)
    tok.save_pretrained(a.out)
    Path(a.out, "base_manifest.json").write_text(
        json.dumps({"student": STUDENT, "template_from": TEMPLATE_FROM, "trained": False}, indent=1)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
