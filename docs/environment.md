# Environment

Recorded 2026-10-08 (first session), re-checked 2026-11-10. Re-verify at every GPU session start
(charter 4). Nothing here is assumed; every line was observed by a command in the session log.

## GPU node 2 (Lambda 2× H100, provisioned by Glen 2026-11-10; decision 17; observed 2026-11-10)

| Item | Observed |
|---|---|
| Host | Lambda Cloud, Ubuntu 22.04.5 LTS, kernel 6.8.0-1064-nvidia |
| GPUs | **2× NVIDIA H100 80GB HBM3** (81,559 MiB each), NVLink NV18 between them |
| Driver / CUDA | driver 580.105.08, CUDA 13.0 (driver); toolkit nvcc 12.8 |
| CPU / RAM / disk | 52 vCPU, 442 GiB RAM, 5.4 TB root |
| System Python / torch | 3.10.12 / 2.7.0+cu128 (unused by the harness) |
| Harness venv | uv-managed CPython 3.11; vLLM **0.33.0** (same pin as node 1), FlashInfer prebuilt kernels via `vllm download-kernels` |
| Data root | `HARNESS_HOST_REPO=/home/ubuntu/data` (migrated from node 1: pool, partial results, logs, evidence) |
| Replicas | one teacher replica per GPU (`scripts/serve_teacher.sh <gpu> <port>`), identity-sticky routing in the client |

Node 1 (A100 40GB, below) is superseded; its partial pilot outputs are kept under the migrated data root as `*_node1_*`.

## GPU node 1 (Lambda A100 40GB, provisioned by Glen 2026-11-10; superseded by node 2 the same day)

| Item | Observed |
|---|---|
| Host | Lambda Cloud, Ubuntu 22.04.5 LTS, kernel 6.8.0-1064-nvidia |
| GPU | **NVIDIA A100-SXM4-40GB** (40,960 MiB). Not the 80GB variant: GRPO with colocated generation is the tight stage; decision 10 (SFT regime in pilot) applies. |
| Driver / CUDA | driver 580.105.08, CUDA 13.0 (driver); toolkit nvcc 12.8 at /usr/local/cuda |
| CPU / RAM | 30 vCPU, 216 GiB RAM |
| Disk | 497 GB root, 472 GB free at session start |
| System Python | 3.10.12 (too old for the harness, which requires ≥ 3.11); project venv uses uv-managed 3.11 |
| System torch | 2.7.0 + cu128 (system site-packages; not used by the harness venv) |
| vLLM | **0.33.0** (latest on PyPI at install time, 2026-11-10), installed into the project venv with its own torch **2.14.0+cu130**; `uv pip install vllm==0.33.0`. Prebuilt FlashInfer kernels installed with `vllm download-kernels` (flashinfer-jit-cache 0.7.2.post1+cu130) because the first launch died in the FlashInfer sampler's JIT build (`ninja` absent); no engine patch, no env switch needed. Never upgraded after this line. First install stalled at 0 MB/s after 39 min (39/63 packages); killed and restarted with cache reuse, completed in minutes. |
| Secrets | HF and GitHub tokens in `/home/ubuntu/info` (two lines, `huggingface:` and `github:`); never echoed, never copied into the repo |
| Egress | huggingface.co and pypi.org reachable |
| Data root | `HARNESS_HOST_REPO=/home/ubuntu/data` (outside the clone) |
| Hourly rate | not observable from the instance; Glen to supply for the money proxy (decision 14) |

## Teacher launch (M1, 2026-11-10; `scripts/serve_teacher.sh`)

`vllm serve Qwen/Qwen3-8B --port 8000 --served-model-name Qwen/Qwen3-8B --reasoning-parser qwen3
--enable-prefix-caching --enable-prompt-tokens-details --max-model-len 16384
--gpu-memory-utilization 0.90 --dtype bfloat16 --disable-log-requests`. Non-default args as logged
by the server are in docs/evidence/m1/launch_args.txt. Sampler: FlashInfer (prebuilt). Model weights
snapshot: `b968826d9c46dd6066d109eabc6255188de91218`. GPU memory in use after startup: 36,483 of
40,960 MiB. Startup to healthy: ~65 s.

## GCP (checked 2026-10-08; superseded by the Lambda VM, kept for the record)

| Check | Result |
|---|---|
| `gcloud compute instances list` in the author's own GCP project (active) | no instances |
| `gcloud compute instances list --format=json(guestAccelerators)` | `[]` |
| Second accessible project `gen-lang-client-0364691900` | Gemini default project, not checked for instances |
| us-central1 GPU quotas in the active project | K80, P100, V100, P4 families at limit 1; no `NVIDIA_A100_GPUS` line (treated as 0) |
| `~/.ssh/config` hosts | none |
| `nvidia-smi` locally | not found (Apple Silicon host) |

Superseded by decision 4 (Lambda A100).

## Local workstation (CPU-side work only)

| Item | Observed |
|---|---|
| Host | macOS 26.5.1, Darwin 25.5.0, arm64 (Apple Silicon) |
| Python for the harness | CPython 3.11.15 via `uv` (`.venv`); 3.12.13 and 3.14.7 also present |
| `uv` | 0.11.10 |
| git | 2.39.3 (Apple Git-146) |
| `pre-commit` | 4.2.0 in `.venv`; git hook installed at `.git/hooks/pre-commit` |
| Free disk (local) | ~22 GiB of 228 GiB; not suitable for raw results, which live on the VM under `HARNESS_HOST_REPO` |
| Network egress | arxiv.org, huggingface.co, pypi.org all reachable (HTTP 200) |
| gcloud | 'default' config; two projects visible |

## Serving stack (pins deferred until observed on the VM)

- vLLM latest on PyPI at 2026-10-08: **0.31.0** (GitHub release tag v0.31.0, published 2026-10-05).
  Not installed anywhere yet. The version actually installed on the VM is what gets pinned
  (charter 4, "pin the version you find"); do not pre-pin from PyPI.
- Usage fields verified in vLLM `main` source on 2026-10-08
  (`vllm/entrypoints/serve/engine/protocol.py`, `vllm/entrypoints/openai/chat_completion/serving.py`):
  - `UsageInfo.prompt_tokens_details.cached_tokens` — per request, server side, populated only when
    the server is started with `enable_prompt_tokens_details` (flag) and prefix caching is on.
  - `UsageInfo.completion_tokens_details.reasoning_tokens` — per request, server side, populated only
    when a reasoning parser is configured (`qwen3` or `deepseek_r1`); counted via
    `parser.count_reasoning_tokens`.
  - Consequence: detectors D5 (reasoning share) and D7 (prefix-cache share) are feasible with
    **no engine patch**, pending M1 confirmation on the pinned release. GitHub issue #16162
    (V1 engine not reporting `cached_tokens`) is closed; the fix release was not identifiable from
    the issue page, so M1 must assert the field is non-null on a repeated-prefix request.

## Unit-price inputs for the money proxy (aggregator figures, NOT official)

| SKU | On-demand, us-central1 | Source (fetched 2026-10-08) |
|---|---|---|
| a2-highgpu-1g (A100 40GB, 12 vCPU, 85 GiB) | ≈ $3.67/h | holori.com, devzero.io |
| a2-ultragpu-1g (A100 80GB, 12 vCPU, 170 GiB) | ≈ $5.03–5.06/h | holori.com, devzero.io |

Verify against Google's pricing page before any figure reaches the paper. One aggregator (vantage)
showed ~5x lower figures and is treated as stale.

## Off-node copy of raw data (2026-11-11, 14:26 PST)
`<local data root>/` holds an rsync copy of the node's
`results/raw` (campaign records and pairs, benign replay records, suite scores), `benign` (schedules,
timeline, manifest), `campaign_prompts`, `pool` and `logs`, about 1.35 GB, taken after the C-real
campaign finished. Not copied: `checkpoints` (42 GB of trained students; re-creatable from the
committed recipes and the copied pairs) and the HF cache. `results/aggregates` is copied after the
v2 analyses finish. The node can be released once that copy is confirmed.
