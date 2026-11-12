#!/usr/bin/env python
"""Supervised distillation of the student on campaign pairs (PROTOCOL §3; PLAN M2 step 4).

Fixed hyperparameters across arms (PROTOCOL §3, amendment A2): 3 epochs, lr 5e-5 cosine, effective batch 16,
max sequence 6,144, loss on assistant tokens only (reasoning kept inside <think>...</think>).
Regime (decision 10): --regime full | lora. The regime, seed, pair count, dropped (finish=length)
count and the data hash are written to train_manifest.json next to the checkpoint.

Usage: train_sft.py --pairs <pairs.jsonl> --out <dir> --seed 0 --regime full [--limit N]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

from dev_harness.sft_data import examples_for, load_pairs

STUDENT = "Qwen/Qwen3-1.7B-Base"
TEACHER_TEMPLATE_FROM = (
    "Qwen/Qwen3-1.7B"  # the base checkpoint has no chat template; use the family's
)
MAX_LEN = 16384


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--regime", choices=["full", "lora"], required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--per-device-batch", type=int, default=1)
    ap.add_argument("--effective-batch", type=int, default=16)
    ap.add_argument(
        "--max-gen-tokens",
        type=int,
        default=0,
        help="A5 variant: keep only pairs with at most this many generated tokens (0 = off)",
    )
    ap.add_argument(
        "--answer-only-copy",
        action="store_true",
        help="A5 variant b: add one answer-only example per pair",
    )
    a = ap.parse_args()

    from trl import SFTConfig, SFTTrainer

    torch.manual_seed(a.seed)
    rows, counts, data_hash = load_pairs(Path(a.pairs), a.limit, a.max_gen_tokens)
    tok = AutoTokenizer.from_pretrained(TEACHER_TEMPLATE_FROM)
    tok.pad_token = tok.pad_token or tok.eos_token
    examples = []
    n_long = 0
    for d in rows:
        prompt = tok.apply_chat_template(
            d["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=True
        )
        exs = examples_for(prompt, d, tok.eos_token, a.answer_only_copy)
        if len(tok(exs[0]["prompt"] + exs[0]["completion"])["input_ids"]) > MAX_LEN:
            n_long += 1
            continue
        examples.extend(exs)
    if not examples:
        raise RuntimeError("all examples exceed MAX_LEN")
    ds = Dataset.from_list(examples).shuffle(seed=a.seed)

    model = AutoModelForCausalLM.from_pretrained(
        STUDENT, dtype=torch.bfloat16, attn_implementation="sdpa"
    )
    peft_config = None
    if a.regime == "lora":
        from peft import LoraConfig

        peft_config = LoraConfig(
            r=64,
            lora_alpha=128,
            lora_dropout=0.0,
            task_type="CAUSAL_LM",
            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
        )

    steps_per_epoch = math.ceil(len(ds) / a.effective_batch)
    warmup = max(1, int(0.03 * steps_per_epoch * a.epochs))  # transformers 5 has no warmup_ratio
    cfg = SFTConfig(
        output_dir=a.out,
        num_train_epochs=a.epochs,
        learning_rate=a.lr,
        lr_scheduler_type="cosine",
        warmup_steps=warmup,
        per_device_train_batch_size=a.per_device_batch,
        gradient_accumulation_steps=max(1, a.effective_batch // a.per_device_batch),
        max_length=MAX_LEN,
        completion_only_loss=True,
        bf16=True,
        gradient_checkpointing=True,
        logging_steps=5,
        save_strategy="no",
        report_to=[],
        seed=a.seed,
        dataloader_num_workers=2,
        optim="adamw_torch",
        weight_decay=0.0,
        max_grad_norm=1.0,
    )
    trainer = SFTTrainer(
        model=model, args=cfg, train_dataset=ds, processing_class=tok, peft_config=peft_config
    )
    t0 = time.time()
    result = trainer.train()
    if a.regime == "lora":
        trainer.model = trainer.model.merge_and_unload()
    trainer.model.save_pretrained(a.out, safe_serialization=True)
    tok.save_pretrained(a.out)
    manifest = {
        "student": STUDENT,
        "template_from": TEACHER_TEMPLATE_FROM,
        "regime": a.regime,
        "seed": a.seed,
        "pairs_file": a.pairs,
        "pairs_sha256_usable": data_hash,
        "n_pairs_usable": len(rows),
        "n_trained": len(examples),
        "n_dropped_finish_length": counts["dropped_finish_length"],
        "n_errors_in_pairs": counts["errors"],
        "max_gen_tokens": a.max_gen_tokens,
        "n_dropped_over_max_gen": counts["dropped_over_max_gen"],
        "answer_only_copy": a.answer_only_copy,
        "n_dropped_over_max_len": n_long,
        "epochs": a.epochs,
        "lr": a.lr,
        "effective_batch": a.effective_batch,
        "max_len": MAX_LEN,
        "train_loss": result.training_loss,
        "global_steps": result.global_step,
        "seconds": round(time.time() - t0),
        "peak_gpu_mem_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2),
        "log_history": trainer.state.log_history,
    }
    Path(a.out, "train_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in (
                    "regime",
                    "n_trained",
                    "n_dropped_finish_length",
                    "n_dropped_over_max_len",
                    "train_loss",
                    "global_steps",
                    "seconds",
                    "peak_gpu_mem_gb",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
