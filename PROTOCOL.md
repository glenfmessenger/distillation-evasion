# PROTOCOL v1.0 (FROZEN 2026-11-10)

Status: frozen after HARD STOP 1 (Glen, 2026-11-10: "accept all recommendations"; decisions 3–14 in
DECISIONS.md). The freezing commit hash is recorded in GATES.md. Amendments are appended in §10,
never edited in place, and typed as MECHANISM REASSIGNED or EVIDENCE DISQUALIFIED (charter 3.2).

Charter corrections adopted (decision 11): the repair step after distillation is published
(arXiv:2609.35699); what it costs at the serving layer is not. No open-problem statement on cost
modelling is attributed to arXiv:2510.09023 beyond the passages in docs/related.md R1.

Model benchmark figures cite docs/related.md. Predictions are numeric and bind from this commit.

## 0. Hypotheses and numeric predictions (draft; Glen edits before freeze)

| ID | Statement | Numeric prediction at freeze |
|---|---|---|
| H1 | Volumetric/identity detectors (D1, D2) are evaded by identity splitting at zero capability cost. | At n ≥ 100 identities, D1 and D2 detection of campaign sessions at 0.1% FPR ≤ 5%; after-repair suite score within ±1.0 point of baseline (verification arm). |
| H2 | Temporal and output-shape detectors (D3–D7, D9) are evadable at a cost in attacker time and tokens, not capability. | Each is pushed below 10% detection at 0.1% FPR by its lever (L2–L5, L7) at the highest level swept; after-repair score within ±1.0 point of baseline for L2–L4; L5 and L7 measured, predicted within ±2.0. |
| H3 | Coverage reduction (L6) that evades D8 costs student capability, and the cost survives repair. | At the coverage level c* where D8 detection at 0.1% FPR first falls below 10%, after-SFT MATH-500 falls ≥ 8.0 points vs c = 1.0, after-repair falls ≥ 5.0 points, and repair recovers < 50% of the SFT-stage loss. |
| H4 | Jointly scored detectors form an intersection, not a curve. | For the full detector set at 0.1% FPR, no single lever at any swept level drives joint detection below 50%; the cheapest evading combination contains L6. |
| H5 | The H3 cost is not recoverable with identities or tokens. | In L1×L6 and L4×L6, the after-repair score at fixed c differs across n and f by < 2.0 points (point estimate with 95% BCa CI reported beside the prediction). |
| H6 | The content-blind coverage proxy (D8) tracks the content-aware upper bound (C1). | Let c*_D8 and c*_C1 be the coverage levels at which each detector's detection at 0.1% FPR first falls below 10%. Prediction: c*_C1 ≤ c*_D8, and c*_D8 is within one sweep level of c*_C1. If the gap is two or more levels, D8 is reported as an insufficient proxy and the gap is the paper's "price of blindness" result. |

Stop rules (charter 3.8) apply to every number above.

## 1. Models (decisions 5, 6)

Teacher candidates (served in vLLM, bf16):

| | Qwen3-8B (T-A, recommended) | DeepSeek-R1-Distill-Qwen-7B (T-B) |
|---|---|---|
| Licence | Apache-2.0 | MIT (weights derived from Qwen2.5, Apache-2.0) |
| Params / bf16 weights | 8.2B / ≈16.4 GB | 7.6B / ≈15.2 GB |
| Reasoning | native `<think>`; vLLM `qwen3` parser; thinking can be toggled | `<think>`; vLLM `deepseek_r1` parser |
| MATH-500 (thinking) | 97.4 | 92.8 |
| AIME'24 | 76.0 | 55.5 |
| LiveCodeBench | 57.5 (v5) | 37.6 |
| Fit on A100 40GB | yes, ≈20 GB headroom for KV cache | yes |

**Chosen: T-A (Qwen3-8B).** Stronger on code, same tokenizer family as the recommended student, thinking
toggle lets the benign replay run in whichever mode the protocol fixes (proposal: thinking ON
for all traffic, so reasoning share is a property of the request, not of the arm).

Student candidates (trained on the same GPU with the teacher offloaded):

| | Qwen3-1.7B-Base (S-A, primary) | Qwen3-1.7B (S-B) | Llama-3.2-1B-Instruct (S-C, cross-family) |
|---|---|---|---|
| Licence | Apache-2.0 | Apache-2.0 | Llama 3.2 Community |
| Post-training | none | full (already distilled by the Qwen team) | instruct |
| Headroom to T-A on MATH-500 | large (MATH 4-shot base 43.5) | 4.0 points (93.4) — too small to carry a cost (FINDINGS F3) | large (MATH 30.6) |
| Tokenizer/template | same as teacher | same | different |

**Chosen: S-A primary; S-C secondary arm at baseline and the L6 sweep only, if budget permits.**
S-B rejected (FINDINGS F3).

Trainability (verified in pilot, not assumed): full fine-tune of 1.7B in bf16 with fp32 AdamW
states ≈ 27 GB before activations; feasible on 40GB with gradient checkpointing at ≤ 6k tokens,
comfortable on 80GB. GRPO with generation colocated is the tight stage on 40GB. GPU: one A100 on Lambda (decision 4); VRAM recorded at M1. SFT regime per decision 10.

## 2. Capability bar (decision 7)

Suite (verifiable answers; sizes are the public test splits):

| Sub-suite | Items | Verifier | Reward usable for repair |
|---|---|---|---|
| MATH-500 | 500 | math-verify exact/equivalence | yes |
| GSM8K test | 1,319 | numeric match | yes |
| HumanEval | 164 | unit tests | yes |
| MBPP test | 500 | unit tests | yes |

Scoring: pass@1 estimated from 4 samples per item at the teacher's recommended thinking-mode
sampling (T=0.6, top-p 0.95, top-k 20), max 14,000 generated tokens (A1; was 8,192), BCa bootstrap over items
(2,000 resamples), seeds recorded. Reported at student-before, student-after-SFT, student-after-
repair. The paper's cost unit is after-repair.

Bar: "within 10 absolute points of the teacher on MATH-500 and HumanEval, and within 10 on GSM8K
and MBPP". Justification: the Qwen team's own post-trained 1.7B lands 4 points under the 8B on
MATH-500 with far more data than we will use, so 10 is reachable at full coverage and tight
enough that coverage loss shows. 

Contamination control: every training prompt is compared to every suite item by normalised
exact match and 13-gram overlap; hits are removed from the pool and the hit count is reported.

## 3. Campaign (the distillation pipeline)

Query pool (decision 13): MATH train (7,500) ∪ GSM8K train (7,473) for math; APPS train subset (5,000)
∪ MBPP train+validation (464) for code; ≈ 20.4k prompts before contamination removal. The pilot
establishes N_full, the sample count needed to reach the bar at c = 1.0; N_full is then fixed
across every arm so the only varying factor is the data's shape, not its count.

Sampling: OpenAI-compatible chat endpoint on the local vLLM teacher, thinking on, T=0.6, top-p
0.95, top-k 20, max 6,144 generated tokens. Each request carries identity and session tags and is
written as one RequestRecord. Responses with finish_reason=length are excluded from SFT and
counted (TtV T6).

SFT (fixed across arms): full fine-tune (pilot: fits in 17 GB), 3 epochs, lr 5e-5 cosine, effective
batch 16 sequences (A2; was 2 epochs, 1e-5, 64), max sequence 16,384 (A1; was 6,144), loss on response tokens including the `<think>` span,
seeds {0, 1, 2}.

Repair (fixed across arms, never optional): GRPO on the student alone with verifiable rewards from
pool prompts (math-verify; unit tests), 200 steps × 16 prompts × 8 generations, max 4,096
generated tokens, lr 1e-6, same seeds. Wall-clock and step count recorded per arm; the pilot
checks that this budget moves the score materially (else amended under §10).

## 4. Benign traffic model (decision 8)

Source: WildChat-1M (ODC-BY, ungated; timestamps, hashed_ip, user-agent, turn count). Shapes
derived: per-pseudo-user (hashed_ip + user-agent) session structure, inter-arrival, per-session
request count, turn depth, prompt length. Replay sends the real prompts to the same teacher, so
output-length, reasoning-share and cache statistics are real serving statistics.

Mixture (proposal):

| Component | Weight | Construction |
|---|---|---|
| Conversational users | 85% | WildChat sessions, English, non-toxic, sampled by pseudo-user |
| Heavy tail: eval-harness batch | 4% | one identity issuing MMLU/ARC prompts back-to-back (not GSM8K/MATH, to avoid pool overlap) |
| Heavy tail: batch summarisation | 3% | long-prompt/short-output jobs from WildChat long prompts |
| Heavy tail: agent loops | 3% | WildChat sessions with turn ≥ 8, replayed at machine cadence |
| Code assistants | 5% | WildChat conversations containing code fences (content used for construction only, never for detection) |

Scale: ≥ 20,000 benign sessions → FPR resolution 1/20,000 = 0.005%. Any budget with fewer than
10 benign exceedances is reported as "below resolution", never as 0%. In-flight records excluded
from calibration by default; exclusion count reported.

Timing: inter-arrivals replayed time-scaled by a recorded factor k, identical for benign and
campaign traffic (TtV T3; decision 12).

## 5. Detectors (content-blind; per-session or per-identity statistic stored, thresholds set later)

| ID | Statistic | Direction (campaign-like) | Positive control | Negative control | Predicted on unevaded baseline @0.1% FPR |
|---|---|---|---|---|---|
| D1 | max requests per identity per hour window | high | baseline single identity | median benign user | ≥ 90% |
| D2 | sessions per identity per day | high | baseline single identity | median benign user | endpoint (100%, reported as such) |
| D3 | CV of inter-arrival within session; fraction < 1 s | low CV | scripted loop | human-cadence benign | ≥ 90% |
| D4 | KS distance, session generated-token CDF vs benign pooled | high | baseline | benign resample | ≥ 50% |
| D5 | median reasoning_tokens / generated_tokens per session | high | baseline | benign chit-chat | ≥ 90% (TtV T5) |
| D6 | KS distance, prompt-token CDF vs benign | high | baseline | benign resample | ≥ 50% |
| D7 | mean cached_tokens / prompt_tokens per session | high | templated prompts | unique prompts | ≥ 30% (TtV T4) |
| D8 | JSD at matched request count: every identity subsampled to n_match = 30 requests, JSD of its (prompt-len bucket × output-len bucket) histogram against the benign population histogram, median over 20 subsamples; identities with < 30 scoreable requests are unscoreable and counted. Secondary: distinct cells per 100 requests at matched n. (Decision 3, FINDINGS F13: unmatched JSD is sample-size biased.) | high | baseline | benign heavy user (eval-harness component) | ≥ 90% |
| D9 | single-turn fraction per session | high | baseline | multi-turn benign | ≥ 90% |

Sessions with fewer than 10 scoreable requests are "unscoreable" for D4/D6/D8 and counted.
Joint scoring: a session is flagged by set S at budget b if any D ∈ S exceeds its threshold; the
union's threshold is calibrated empirically on benign sessions, not by Bonferroni.
**Content-aware upper bound (decision 3), reported in a separate table and never in the
content-blind set:**

| ID | Statistic | Reads | Direction | Controls |
|---|---|---|---|---|
| C1 | At matched n_match = 30: JSD between the identity's histogram over k = 50 topic clusters (k-means on `BAAI/bge-small-en-v1.5` prompt embeddings, fit on benign prompts only) and the benign population; secondary: mean pairwise cosine distance among the identity's prompt embeddings | prompt text | high | same as D8 |

C1 exists to bound what coverage detection could achieve with content, so that a null D8 result
is interpretable (H6). It is never scored jointly with D1–D9.

## 6. Evasion levers and sweeps

| Lever | Levels | Changes SFT data? | Predicted evades | Cost denomination |
|---|---|---|---|---|
| L1 identity split | n ∈ {1, 10, 100, 1000} | no | D1, D2 at n ≥ 100 | identities |
| L2 rate shaping | cap at benign quantile q ∈ {0.99, 0.9, 0.5} | no | D1 at q ≤ 0.9 | wall-clock |
| L3 cadence jitter | s ∈ {0.25, 0.5, 1.0} × benign CV | no | D3 at s ≥ 0.5 | wall-clock |
| L4 decoy mixing | f ∈ {0.25, 0.5, 0.75} WildChat decoys | no (decoys excluded) | D4, D5 at f ≥ 0.5 | tokens |
| L5 prompt-shape mimicry | match D6 to benign at {0.5, 0.75, 0.9} | yes (padded prompts) | D6 | tokens; capability measured at one level |
| L6 coverage reduction | c ∈ {1.0, 0.5, 0.25, 0.1} of shape cells retained, ranked by benign density | **yes** | D8 at c ≤ 0.25 | **capability** |
| L7 multi-turn wrapping | k ∈ {2, 4} | yes (context-conditioned responses) | D9 | tokens; capability measured at k = 2 |

Joint: L1×L6 (n ∈ {1, 100} × c ∈ {1.0, 0.25, 0.1}) and L4×L6 (f ∈ {0, 0.5} × same c).

Replicates: capability arms 3 seeds (SFT + repair); detection cells 5 re-schedulings of recorded
responses (new identity assignment and timing; no new teacher calls). Levers that do not change
the SFT data share the baseline capability arm; the L1 n=100 verification arm re-trains once to
confirm the data hash and score are unchanged (charter M4, "verified, not assumed").

## 7. Cost accounting

Per cell: identities, wall-clock, teacher prompt tokens, teacher generated tokens, decoy share,
SFT compute (fixed), repair compute (fixed), after-repair suite score with CI. Money = derived
column from parameters, defaults (decision 14, placeholders until Glen sets them; re-priceable by
the reader): p_identity = 5 USD per account; p_token = 1 USD per 1M prompt tokens and 3 USD per 1M
generated tokens; p_gpu_hour = the Lambda A100 hourly rate observed at M1.

## 8. Analysis plan

Per lever: per-cell detection at 1%, 0.1% and the resolution floor; per-replicate threshold
location (the level at which detection crosses 50%) found first, then pooled as median and range
(charter 3.5); cost law fitted only where monotone, exponent reported, extrapolation unsupported.
Joint: intersection table of cheapest evading combination per detector set with its capability
cost. Thesis test: after-repair score regressed on c with n and f as factors; H5 pre-registered
prediction beside the estimate. All CIs BCa, 2,000 resamples, seeds committed.

## 9. Compute estimate (single A100, GPU-hours; assumptions stated, pilot re-estimates)

Assumed throughput: teacher ≈ 1,500 generated tok/s aggregate in vLLM; SFT ≈ 4,000 tok/s for 1.7B;
eval ≈ 0.5 h per student. N_full assumed 10k–20k prompts × ≈3k tokens.

| Milestone | Estimate | Basis |
|---|---|---|
| M1 serving/metric surface | 2 | bring-up + truncated-run test |
| M2 pilot (10%) | 5 | 1 sample run + 1 SFT + 1 repair + eval |
| M2 full baseline | 30–45 | sampling 6–11 h; 3 × (SFT 4–8 h + repair 3 h + eval 0.5 h) |
| M3 benign replay | 10 | ≈20k sessions + heavy tail |
| M4 single-lever | 150–220 | L6: 3 levels × 3 seeds; L5, L7 one level × 3 seeds; L1 verification; teacher re-sampling for L4/L5/L7 |
| M5 joint | 5–40 | detection is re-scheduling (CPU); one re-trained joint cell × 3 seeds if required |
| M6 | 2 | archive |
| **Total** | **≈ 200–320** | money at the Lambda hourly rate recorded at M1 |

## 10. Amendments

**A1 — 2026-11-10 — Generation caps raised (parameter change; reason: FINDINGS F20).** Campaign
max generated tokens 6,144 → 14,000 (§3); scoring max generated tokens 8,192 → 14,000 (§2); SFT
max sequence length 6,144 → 16,384 (§3) so that long traces are trained on rather than dropped.
Teacher context stays 16,384. The GRPO completion budget (4,096) is unchanged and will be
reviewed at HARD STOP 3 against the student's observed trace lengths. Reason: at the frozen caps
38% of pilot campaign responses were truncated (APPS 86%, MATH 39%), and dropping them would
remove the hard region of the request space that lever L6 manipulates, confounding H3. No
evidence existed before this amendment; nothing is reassigned or disqualified. Approved by Glen
(chat, "go with your recommendation (1)"); decision 16.

**A2 — 2026-11-11 — SFT recipe changed (parameter change; reason: FINDINGS F27, F29).** SFT
learning rate 1e-5 → 5e-5 (cosine), effective batch 64 → 16, epochs 2 → 3; full fine-tune; fixed
for every arm. Reason: under the frozen recipe (56 optimizer steps on the pilot data) the base
student never learns its chat control tokens and returns no structured answers. Chosen from two
exploratory runs on pilot data (DECISIONS D-17 table; non-reportable). Residual thinking-span
loops after SFT are deliberately left to the repair stage. No reportable evidence existed under
the old recipe; nothing is reassigned or disqualified. Approved by Glen (chat, "1"); decision 18.

**A3 (ratified 2026-11-11, decision 23; text below as written when provisional) — 2026-11-11 — Benign model sizing (reason:
FINDINGS F31, F32).** §4's single 85/4/3/3/5 identity mixture replayed in full is replaced by two
artefacts: a full-corpus timeline (all real pseudo-users, no prompt text, no teacher requests)
that calibrates D1, D2, D3 and D9; and a stratified replay subset (heavy real users oversampled,
strata and population counts recorded, 40-request cap per identity) that calibrates D4–D8 and C1.
Turn time is the timestamp of the reply that follows the turn (WildChat does not timestamp user
messages). FPR is defined over scoreable units. Taken under delegated authority (decision 19); if
Glen rejects it, the replayed records remain valid data and only the calibration design changes.

**A4 — 2026-11-11 — Repair-only arm added (arm added; reason: FINDINGS F39, F41).** A new
capability arm: the frozen repair of §3 applied to the untouched student, with no SFT. The base
checkpoint's weights are unchanged; it carries the tokenizer and chat template of Qwen/Qwen3-1.7B
exactly as the SFT checkpoints do. Same RL prompt draw as the pilot (same seed and exclusion
list), then the suite of §2 in chat mode. Known limit, stated before running: the untouched
student has never been trained on its chat control tokens (F27), so a low repair-only score
cannot by itself separate "the copy supplied knowledge" from "the copy supplied the answer
format". If mean practice reward over the first 20 steps is below 0.05 the arm is labelled
format-starved and reported as such. No evidence is reassigned or disqualified. Decision 24.

**A5 — 2026-11-11 — Exploratory SFT variants and their selection rule (exploration; reason:
FINDINGS F34, F39, F41).** Two non-reportable variants on the pilot pairs, A2 hyperparameters,
seed 0: (a) only pairs whose teacher response has at most 4,096 generated tokens; (b) as (a),
plus one extra training example per pair whose loss covers only the final answer (the prompt
extended through the closing think tag). Each is scored on MATH-500 only, chat mode, k = 4.
Selection rule, fixed here before any score exists: a variant qualifies if fewer than 20% of its
MATH-500 samples are truncated and the lower bound of its 95% BCa interval exceeds 0.3695 (the
untouched student, F28); among qualifying variants the higher pass@1 is selected; if none
qualifies the question returns to Glen (D-20 options 2 and 3). Adopting a selected variant as the
recipe for every arm is a separate amendment needing approval. Decision 25.

**A6 — 2026-11-11 — Capability ladder; repair on a named subset; Price 2 defined against the
baseline arm (design change; reason: FINDINGS F30, F39, F40, F41).** §3's "repair fixed across
arms, never optional" is replaced by: Level A, extraction yield for every arm (completed pairs,
truncation share, cell coverage); Level B, after-SFT suite for every arm that changes the SFT
data, 3 seeds; Level C, after-repair suite for the baseline, the repair-only arm, and L6 at
c = 0.25 and c = 0.1. Level C runs at 3 seeds if the copy is shown to matter and at 1 seed
otherwise. Criterion, fixed here before the repair-only arm reports: the copy matters if the
upper bound of the repair-only arm's 95% BCa interval on MATH-500 is below 0.5706 (the lower
bound of the repaired pilot copy, F41). The bar of §2 stays as registered and is reported as not
met by the pilot; capability cost ("Price 2") is the difference from the baseline arm at the same
level. Hypotheses H2 to H5 keep their registered wording and predictions and are evaluated
against whatever levels exist; predictions that reference after-repair scores for arms without
Level C are reported as not tested. §7: p_gpu_hour = 4.19 USD. Mechanism reassigned (which
arms are repaired); no evidence disqualified. Decisions 26, 28, 31.

Editorial (no method or threshold change): 2026-11-10, §1 line referencing draft labels "D-1 and D-8" replaced with decision numbers 4 and 10.
