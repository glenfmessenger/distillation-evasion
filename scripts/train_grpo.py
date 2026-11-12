#!/usr/bin/env python
"""Repair stage: GRPO with verifiable rewards on the student alone (PROTOCOL §3; PLAN M2 step 5).

Fixed budget across arms: --steps 200, 16 prompts per step, 8 generations per prompt,
max 4,096 generated tokens, lr 1e-6. Rewards come from the pool verifiers (math-verify, unit
tests, stdin/stdout tests); no teacher output is used. The budget, regime, wall-clock, peak memory
and reward curve are written to repair_manifest.json next to the checkpoint.

Usage: train_grpo.py --model <sft_ckpt_dir> --out <dir> --seed 0 --regime full|lora [--steps 200]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import torch
from datasets import Dataset

from dev_harness.paths import host_repo
from dev_harness.pool import read_jsonl
from dev_harness.prompts import chat_messages
from dev_harness.verify import VerifyTimeout, verify_item

PROMPTS_PER_STEP = 16
GENERATIONS = 8
MAX_COMPLETION = 4096


def reward_fn(completions, verifier, payload, prompt_text, **kwargs):
    out = []
    for comp, v, pl, pt in zip(completions, verifier, payload, prompt_text):
        text = comp[0]["content"] if isinstance(comp, list) else comp
        # strip the thinking span: rewards are on the final answer only
        if "</think>" in text:
            text = text.split("</think>", 1)[1]
        try:
            out.append(1.0 if verify_item(v, json.loads(pl), text, pt, False) else 0.0)
        except VerifyTimeout:
            out.append(0.0)  # a timeout is a non-answer for reward purposes; counted below
            reward_fn.timeouts += 1
    return out


reward_fn.timeouts = 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--regime", choices=["full", "lora"], required=True)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--lr", type=float, default=1e-6)
    ap.add_argument(
        "--exclude-ids",
        default="",
        help="file with pool ids used for SFT, excluded from RL prompts",
    )
    ap.add_argument("--vllm-mem", type=float, default=0.25)
    a = ap.parse_args()

    from trl import GRPOConfig, GRPOTrainer

    rng = random.Random(a.seed)
    torch.manual_seed(a.seed)
    pool = read_jsonl(host_repo() / "pool" / "pool.jsonl")
    excluded = set(Path(a.exclude_ids).read_text().split()) if a.exclude_ids else set()
    cands = [it for it in pool if it.id not in excluded]
    rng.shuffle(cands)
    need = a.steps * PROMPTS_PER_STEP
    if len(cands) < need:
        raise RuntimeError(f"pool has {len(cands)} prompts, need {need}")
    rows = [
        {
            "prompt": chat_messages(it),
            "verifier": it.verifier,
            "payload": json.dumps(it.payload),
            "prompt_text": it.prompt,
            "pool_id": it.id,
        }
        for it in cands[:need]
    ]
    ds = Dataset.from_list(rows)

    peft_config = None
    if a.regime == "lora":
        from peft import LoraConfig

        peft_config = LoraConfig(
            r=64,
            lora_alpha=128,
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

    cfg = GRPOConfig(
        output_dir=a.out,
        learning_rate=a.lr,
        lr_scheduler_type="constant",
        max_steps=a.steps,
        per_device_train_batch_size=GENERATIONS,
        gradient_accumulation_steps=PROMPTS_PER_STEP,
        num_generations=GENERATIONS,
        max_completion_length=MAX_COMPLETION,
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        bf16=True,
        gradient_checkpointing=True,
        use_vllm=True,
        vllm_mode="colocate",
        vllm_gpu_memory_utilization=a.vllm_mem,
        vllm_max_model_length=8192,
        logging_steps=1,
        save_strategy="no",
        report_to=[],
        seed=a.seed,
        beta=0.0,
        loss_type="dr_grpo",
        num_iterations=1,
        scale_rewards=False,
        chat_template_kwargs={"enable_thinking": True},
    )
    trainer = GRPOTrainer(
        model=a.model, reward_funcs=reward_fn, args=cfg, train_dataset=ds, peft_config=peft_config
    )
    t0 = time.time()
    result = trainer.train()
    if a.regime == "lora":
        trainer.model = trainer.model.merge_and_unload()
    trainer.model.save_pretrained(a.out, safe_serialization=True)
    trainer.processing_class.save_pretrained(a.out)
    manifest = {
        "base": a.model,
        "regime": a.regime,
        "seed": a.seed,
        "steps": a.steps,
        "prompts_per_step": PROMPTS_PER_STEP,
        "generations": GENERATIONS,
        "max_completion": MAX_COMPLETION,
        "lr": a.lr,
        "n_prompts": need,
        "n_excluded_ids": len(excluded),
        "seconds": round(time.time() - t0),
        "global_steps": result.global_step,
        "peak_gpu_mem_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2),
        "verify_timeouts": reward_fn.timeouts,
        "log_history": trainer.state.log_history,
    }
    Path(a.out, "repair_manifest.json").write_text(json.dumps(manifest, indent=1))
    rewards = [h.get("reward") for h in trainer.state.log_history if "reward" in h]
    print(
        json.dumps(
            {
                "regime": a.regime,
                "steps": result.global_step,
                "seconds": manifest["seconds"],
                "peak_gpu_mem_gb": manifest["peak_gpu_mem_gb"],
                "reward_first10": rewards[:10],
                "reward_last10": rewards[-10:],
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
