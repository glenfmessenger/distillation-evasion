# Distillation evasion harness — DECISIONS
Numbered log. Any choice that changes method, scope, or claims gets a row with date, options considered, and the one taken (global rule 9). Amend, do not rewrite.

## Taken

| # | Date | Decision | Options considered | Taken because | Status | Source |
|---|---|---|---|---|---|---|
| 1 | 2026-10-08 | Area is experimental (GATES.md created). | experimental / conceptual | Numbers will be produced. | final | chat (Glen) |
| 2 | 2026-10-08 | Pre-registration lives in PROTOCOL.md; GATES.md records the frozen hash. | GATES.md as the register / PROTOCOL.md | Charter 3.1 names PROTOCOL.md; one register, not two. | final | charter |
| 3 | 2026-11-10 | Run both a content-blind detector set (the central claim) and a content-aware coverage arm as a labelled upper bound; D8 uses a sample-size-independent statistic. Resolves D-6 as options 2+3. | D-6 options 1 / 2 / 3 | Without the upper bound a null D8 result is ambiguous between "unobservable blind" and "does not bind"; the gap between arms is itself a result (the price of blindness). | taken, to be written into PROTOCOL v1.0 | chat 2026-11-10 (Glen: "we should do research on both") |
| 4 | 2026-11-10 | GPU: a single A100 on Lambda (provisioned by Glen); VRAM to be recorded at M1. Supersedes D-1's GCP options. | D-1 options 1–3 / Lambda | Glen provisioned it; GCP quota not needed. | taken | chat 2026-11-10 |
| 5 | 2026-11-10 | Teacher Qwen3-8B. | D-2 options 1–2 | Recommendation accepted. | taken | chat 2026-11-10 |
| 6 | 2026-11-10 | Student Qwen3-1.7B-Base primary; Llama-3.2-1B-Instruct cross-family arm if budget. | D-3 options 1–3 | Recommendation accepted. | taken | chat 2026-11-10 |
| 7 | 2026-11-10 | Suite MATH-500 + GSM8K test + HumanEval + MBPP test; bar = within 10 points of teacher per sub-suite. | D-4 options 1–3 | Recommendation accepted. | taken | chat 2026-11-10 |
| 8 | 2026-11-10 | Benign source WildChat-1M, mixture 85/4/3/3/5. | D-5 options 1–2 | Recommendation accepted. | taken | chat 2026-11-10 |
| 9 | 2026-11-10 | Replicates: 3 capability seeds, 5 detection re-schedulings. | D-7 options 1–2 | Recommendation accepted. | taken | chat 2026-11-10 |
| 10 | 2026-11-10 | SFT regime decided in pilot (full FT if it fits, else LoRA r=64), fixed thereafter. | D-8 options 1–2 | Recommendation accepted. | taken | chat 2026-11-10 |
| 11 | 2026-11-10 | Charter rewordings C1 and C2 (docs/related.md) adopted. | D-9 options 1–2 | Recommendation accepted. | taken | chat 2026-11-10 |
| 12 | 2026-11-10 | Time-scaled replay, factor recorded, identical for benign and campaign. | D-10 options 1–2 | Recommendation accepted. | taken | chat 2026-11-10 |
| 13 | 2026-11-10 | Query pool MATH train + GSM8K train + APPS subset + MBPP train/val. | D-11 options 1–2 | Recommendation accepted. | taken | chat 2026-11-10 |
| 14 | 2026-11-10 | Money-proxy unit prices: placeholder defaults written into PROTOCOL v1.0 §7 (Glen gave no values; "accept all recommendations" had none to accept). Re-priceable; money is a derived column. | defaults / wait for values | Unblocks the freeze; prices never enter a measured claim. | taken, defaults flagged | chat 2026-11-10 |
| 15 | 2026-11-10 | Start the M2 pilot as planned in PLAN.md (≈8–12 GPU-h). | start / wait | Glen: "start M2 pilot". | taken | chat 2026-11-10 |
| 16 | 2026-11-10 | Amendment A1: campaign cap 14,000, scoring cap 14,000, SFT max length 16,384; restart campaign and teacher scoring. | D-13 options 1–4 | Option 1 recommended and taken: keeps the hard region in the pool; cost ≈ 7–10 GPU-h for teacher scoring. | taken | chat 2026-11-10 ("go with your recommendation (1)") |
| 17 | 2026-11-10 | Move to a Lambda 2× H100 80GB SXM5 node (D-14 option 6); old node's partial outputs are superseded; same vLLM pin and weights. | D-14 options 1–6 | Similar wall-clock to 8× A100 at about a third of the cost; 80 GB removes the GRPO memory risk. | taken | chat 2026-11-10 |
| 18 | 2026-11-11 | Amendment A2: SFT lr 5e-5, effective batch 16, 3 epochs, full FT, all arms. | D-17 options 1–3 | Only recipe that yields structured answers; loops left to repair. | taken | chat 2026-11-11 ("1") |
| 19 | 2026-11-11 | **Taken under delegation (Glen asleep; "you can make judgement calls yourself"), for ratification.** Benign model for M3 = provisional amendment A3: (i) timeline detectors D1, D2, D3, D9 are calibrated on the full WildChat timeline (118,465 identities, no teacher requests needed); (ii) serving-statistic detectors D4–D8 and C1 are calibrated on a stratified replay subset: 1,000 heavy real users (≥ 30 requests) + 1,500 light + 30 eval-harness (50–200 prompts) + 30 batch + 60 agent identities, each capped at its first 40 requests; (iii) replay runs at capacity with the corpus timestamp attached; (iv) FPR is defined over scoreable units and reported with its floor. | D-18 a1–a3, b1–b2, c1–c2, d1 | The 85/4/3/3/5 identity mixture leaves 9% of identities scoreable for coverage and spends 73% of requests on the eval-harness tail (F32); the stratified design gives 1,061 scoreable identities for ≈ 50k requests and is re-weightable from the recorded strata. Hypotheses and their numeric predictions are untouched. | provisional | chat 2026-11-11; FINDINGS F32, F33 |
| 20 | 2026-11-11 | **Taken under delegation, for ratification.** Start M3's benign replay and detector calibration before HARD STOP 3, on the GPU freed by the pilot; D-15 (APPS truncation) left as frozen (truncated pairs excluded and counted). Detector results are provisional until the HARD STOP 4 review. | wait for review / proceed | Six idle GPU-hours otherwise; the replay does not depend on any HARD STOP 3 choice (bar, sample count, repair budget concern the student only). | provisional | chat 2026-11-11 |
| 21 | 2026-11-11 | **Taken under delegation, for ratification.** Reorder GPU 1: after the after-SFT MATH-500 pass, pause the other three after-SFT suites, run the benign replay first, then resume them (resume keeps every completed sample; no reading is dropped or shortened). | keep order (replay ≈ 6 h later) / reorder | After-SFT scoring is slow because looping samples run to the cap; the detector calibration is independent of it and is the larger gap in the paper's data. | provisional | chat 2026-11-11 |
| 22 | 2026-11-11 | Scope confirmed by Glen: the paper's headline question is the content-blind one ("Can someone copying a model through its API hide from a server that watches traffic patterns but never reads the content, and if they can, what does hiding cost them in the quality of the copy?"). No expansion toward a content-reading study. The existing C1 measure stays as a single labelled side comparison from the frozen protocol; it is not to be described as an upper bound (F36), and whether to keep or cut it is an item for HARD STOP 4. | widen to a content-reading study / keep the content-blind headline | Glen's decision. | taken | chat 2026-11-11 |
| 23 | 2026-11-11 | Ratified: decisions 19, 20, 21 and amendment A3 (benign model sizing as replayed). D-18 closed as a1, b1, c1, d1. | ratify / revisit | The replay they produced completed with 0 failures (F40). | taken | chat 2026-11-11 ("go with all your recommendations") |
| 24 | 2026-11-11 | D-19: add a repair-only arm. Frozen repair settings (200 steps × 16 prompts × 8 generations, cap 4,096, lr 1e-6, same prompt draw as the pilot) applied to the untouched student carrying the family chat template, seed 0, then the full suite in chat mode. Amendment A4. | D-19 options 1–2 | The pilot cannot attribute the after-repair score to the copied data (F39, F41). | taken | chat 2026-11-11 ("go with all your recommendations") |
| 25 | 2026-11-11 | D-20: two exploratory, non-reportable SFT variants on the pilot pairs, scored on MATH-500 only: (a) pairs with at most 4,096 generated tokens; (b) as (a) plus one answer-only example per pair. Selection rule fixed before scoring (amendment A5). The SFT recipe itself is not changed until a variant is selected and a further amendment is approved. | D-20 options 1–3 | SFT alone shows no gain under A2 (F34, F39, F41). | taken | chat 2026-11-11 ("go with all your recommendations") |
| 26 | 2026-11-11 | D-21: capability ladder. Level A extraction yield for every arm; Level B after-SFT suite for every data-changing arm, 3 seeds; Level C after-repair on baseline, repair-only, L6 at c = 0.25 and c = 0.1, at 3 seeds if the D-19 criterion in A6 is met and 1 seed otherwise. Replaces 'repair fixed across arms, never optional'. Amendment A6. | D-21 options 1–3 | Repair is about 60% of per-arm compute and is needed only to test whether a quality gap survives it. | taken | chat 2026-11-11 ("go with all your recommendations") |
| 27 | 2026-11-11 | D-22: detectors D3 to D9 are reported per cell as observed beside their registered predictions; D9 marked unscoreable; all are carried through the evasion cells; none dropped, redefined or re-thresholded; no post-hoc detectors registered. | D-22 options 1–2 | Failed predictions are results (F40). | taken | chat 2026-11-11 ("go with all your recommendations") |
| 28 | 2026-11-11 | D-23: the bar of decision 7 stays the registered criterion and is reported as not met by the pilot; Price 2 (copy quality) is defined relative to the baseline arm's score. This reframes the capability claim. Accepted by Glen's blanket acceptance; I had asked for a specific yes, so it is to be reconfirmed before any manuscript text depends on it. | D-23 options 1–2 | The pilot is 13 to 36 points short of the teacher (F41). | taken; reconfirm at drafting | chat 2026-11-11 ("go with all your recommendations") |
| 29 | 2026-11-11 | D-15: APPS stays in the pool at the A1 cap; the stratum's truncation is reported; the length question is folded into D-20. | D-15 options 1–4 | The D-20 length filter treats long traces uniformly across strata. | taken | chat 2026-11-11 ("go with all your recommendations") |
| 30 | 2026-11-11 | D-24: D-19 on GPU 0 and D-20 on GPU 1 of the current node tonight; then the Price 1 detection cells; the node for Levels B and C is chosen after D-19 reports. | D-24 options 1–2 | Both answers size everything that follows. | taken | chat 2026-11-11 ("go with all your recommendations") |
| 31 | 2026-11-11 | Decision 14 completed: p_gpu_hour = 4.19 USD (2× H100 at 8.38 USD per hour, Glen 2026-11-11); p_identity = 5 USD and token prices of 1 and 3 USD per 1M stay as reader-repriceable defaults. | confirm / replace | Glen supplied the node price. | taken | chat 2026-11-11 ("go with all your recommendations") |
| 32 | 2026-11-11 | **Pivot of the central claim (sign-off gate).** The paper measures what a serving-layer defender must see to detect a distillation campaign, at three visibility levels (pattern, volume, content) on the same campaigns against the same calibrated benign baseline, plus the attacker effort price of getting under the volume level. The quality-price claim ("what the distiller cannot buy") is dropped: at pilot scale, with verifiable-reward tasks, copying added nothing measurable to the repaired student (F43), so there is no quality to price. The content level is defender-side only: no lever targets it (PROTOCOL_v2.md §0 boundary). PROTOCOL v1.0 is superseded on v2.0 freeze; its results are retained and reported as tested/not tested. Draft protocol in PROTOCOL_v2.md for review; nothing run under it yet. | narrow to detection only / pivot to the visibility ladder / redesign the quality half around tasks without an answer key / stop | Glen: "yes to the pivot" after the assessment that the result would be modestly novel and useful (calibrated negative results, the ladder, a reproducible local-teacher harness) and that R3 already publishes a content-reading detector, so the content level must re-implement R3 rather than claim a new detector. | taken | chat 2026-11-11 ("yes to the pivot") |
| 33 | 2026-11-11 | PROTOCOL v2.0 frozen with predictions P1 to P6 as drafted and the working title accepted. Agent judgement at freeze, logged: the held-out split for C-real is disjoint by pseudo-user from the benign replay subset (the only calibration set whose prompt text is used), not from the timeline, which calibrates timing only; and C-real is defined as the first 20 sessions of one 8,000-request run so the sensitivity needs no second run. | accept / edit | Glen accepted the draft; the two refinements remove an impossible disjointness requirement (the timeline holds every pseudo-user) and a duplicated run. | taken | chat 2026-11-11 ("proceed with your recommendations (and the working title is good)") |
| 34 | 2026-11-11 | D-25 option 1: one scoring rule for every arm (verify the answer text; if the think span never closed, verify the whole output); every canonical score re-derived under it from stored rows; registered-path numbers shown beside them once. Amendment A7 to v1.0's scoring, applying to the capability side table only. | D-25 options 1–3 | Removes a path where the exam and the repair reward disagree about the same output (F43). | taken | chat 2026-11-11 ("proceed with your recommendations (and the working title is good)") |
| 35 | 2026-11-11 | D-26 option 1: the untouched student scored in chat mode, no repair (started 12:53 PST on GPU 0). | D-26 options 1–2 | Splits the repair-only score into what repair added and what the student already had. | taken | chat 2026-11-11 ("proceed with your recommendations (and the working title is good)") |
| 36 | 2026-11-11 | N = 8,000 C-real run included; C-real proper is its first 20 sessions. | include / omit | About 17 USD; checks that P4 is not an artefact of N. | taken | chat 2026-11-11 ("proceed with your recommendations (and the working title is good)") |
| 37 | 2026-11-11 | Breadth amendment B1 to PROTOCOL v2.0 (second C-real seed, approved by Glen; content calibration on all heavy real users; post-hoc C3 and two-sided C2 registered with predictions on the seed-1 campaign; second embedding model; n_match and block sensitivity; R3 share curve with the first-turn control; C-instr pending approval). | as listed / none | Glen: "go with your recommendation on the first gap" and asked for breadth. | taken (item 7 pending) | chat 2026-11-11 |
| 38 | 2026-11-11 | C-instr campaign approved (amendment B1 item 7): 2,000 prompts from databricks-dolly-15k (instruction plus context), one identity, sessions of 100, as the other campaigns; then the three levels and the content breadth on it. About 3 USD. | run / omit | Glen: "yes to \"C-instr campaign\"". | taken | chat 2026-11-11 |
| 39 | 2026-11-11 | Amendment B2: D10, a content-blind cross-identity coordination detector (identity-day feature density on the full benign timeline), with the heterogeneous split lever L8 as the registered adaptive attacker and predictions P7 to P10 fixed before any run. CPU only. | build / not | Glen: "i want the coordination detector"; the split lever defeats every per-identity detector (F47, F49, F53, F56) and leaves a population-level signature. | taken | chat 2026-11-11 |
| 40 | 2026-11-11 | Amendment B3: D11 account-birth burst registered with predictions P11 to P15; joint price across D1 to D11 defined as the cheapest cell with every detector under 10% flagged; two generated figures and a cold-read review of the draft also commissioned. All on the Mac from the copied data; the node can be released. | as listed | Glen: "all four". | taken | chat 2026-11-11 |
| 41 | 2026-11-11 | Amendment B4 (post-review): benign coordinated-population controls for D10 and D11, a combined adaptive attacker L9 searched against D1 to D11, D3 on completion times, an expected-alert-volume table, and an optional request-weighted pooled reference; predictions P16 to P22 fixed before any run; scope wording and the concurrent citation carried. Node to be released by Glen; everything runs on the Mac. | as listed | Glen: "go ahead with the proposed plan"; three external reviews agreed on the first two items. | taken | chat 2026-11-11 |
| 42 | 2026-11-11 | Amendment A8: no credit for truncated output without a boxed answer (capability side table). Found by the pre-submission audit (F65): under A7, 5% of the after-SFT arm's samples were credited from the trailing text of truncated, unboxed traces, almost the whole uplift A7 gave that arm. Applied, with A7 and the registered path shown beside it once. | keep A7 / tighten | Agent judgement during the audit Glen asked for; ratified by Glen 2026-11-11. | taken, ratified | chat 2026-11-11 |
| 43 | 2026-11-12 | Author review of the draft (Glen, 30-odd points): amendment B5 registers two consistency checks (gap-rule sessions for campaigns; size-matched sessions for D4 and D6) with predictions P23 and P24; the manuscript is restructured per the review (three campaigns in the method, levels defined by features read, cross-account detectors as their own rung, method summary table with realised false-alarm rates, discussion and dual-use statement, capability appendix reduced, terminology unified, abstract replaced). Decision 42 (A8) is treated as accepted by the review's instruction to keep one capability table. | apply / defer | Glen's edit list, pasted 2026-11-12. | taken | chat 2026-11-12 |

## Open (for HARD STOP 1; reply "D-n option k")

All resolved 2026-11-10 ("accept all recommendations"); the list below is kept for the record of what was offered.

**D-1 GPU VM.** None exists (FINDINGS F1).
1. a2-ultragpu-1g, A100 80GB, on-demand ≈ $5.05/h — comfortable for full-FT SFT and GRPO with colocated generation. **Recommended.**
2. a2-highgpu-1g, A100 40GB, ≈ $3.67/h — fits teacher serving and SFT; GRPO likely forces LoRA or small batches; ≈25% cheaper.
3. Spot of either — ≈10% cheaper, preemption risk on 8 h training arms; only with checkpoint/resume.
Either needs an A100 quota request in the chosen region first.

**D-2 Teacher.** 1. Qwen3-8B. **Recommended.** 2. DeepSeek-R1-Distill-Qwen-7B (math-skewed, weaker code, different tokenizer from Qwen3 students).

**D-3 Student.** 1. Qwen3-1.7B-Base primary + Llama-3.2-1B-Instruct cross-family arm if budget. **Recommended.** 2. Qwen3-1.7B-Base only. 3. Qwen3-1.7B post-trained (rejected: FINDINGS F3).

**D-4 Capability suite and bar.** 1. MATH-500 + GSM8K test + HumanEval + MBPP test; bar = within 10 points of teacher per sub-suite. **Recommended.** 2. Same suite, bar = recover ≥ 80% of the before→teacher gap per sub-suite (scale-free, harder to read). 3. Add AIME'24 (30 items; too few for CIs; rejected).

**D-5 Benign source and mixture.** 1. WildChat-1M, 85/4/3/3/5 as PROTOCOL §4. **Recommended.** 2. Same with the heavy tail at 20% total (stresses FPR tail harder; less representative). LMSYS-Chat-1M rejected (F7).

**D-6 D8 coverage statistic and content-aware arm. TAKEN 2026-11-10 as options 2+3 (row 3 above); kept here for the record.** 1. JSD over (prompt-len × output-len) cells plus distinct-cells-per-100; no content-aware arm in v1. **Recommended.** 2. Same plus an embedding-diversity comparison arm clearly labelled content-reading (charter says ask first). **Recommendation changed 2026-11-10 to option 2**: without it, a null D8 result cannot distinguish "coverage is unobservable content-blind" from "coverage does not bind" (chat, Glen's question). The content-aware arm is an upper bound, never in the content-blind table.
3. (added 2026-11-10, FINDINGS F13) Replace JSD in D8 with a sample-size-independent coverage statistic (e.g. a U-statistic over cell coincidences, or JSD at matched request count by subsampling every identity to the same n). **Recommended in combination with option 2.** JSD alone is at risk of firing on benign exploration with the wrong sign.

**D-7 Replicates.** 1. 3 capability seeds, 5 detection re-schedulings. **Recommended.** 2. 5 and 10 (≈ +60% GPU on M4).

**D-8 SFT regime.** 1. Decide in pilot: full FT if it fits with ≤ 5% exclusion at 6,144 tokens, else LoRA r=64; fixed thereafter. **Recommended.** 2. LoRA from the start (cheaper, may understate attainable capability).

**D-9 Charter framing fixes.** 1. Rewrite the repair-step sentence (F4) and soften the Nasr cost-gap sentence (F5) as in docs/related.md C1–C2. **Recommended.** 2. Keep the Nasr sentence if Glen supplies the passage.

**D-10 Replay timing.** 1. Time-scaled replay, factor k recorded, identical for benign and campaign; cadence detectors on scheduled inter-arrivals. **Recommended.** 2. Real-time replay (days of wall-clock per arm; rejected on budget).

**D-11 Query pool.** 1. MATH train + GSM8K train + APPS subset + MBPP train/val (≈20.4k). **Recommended.** 2. Add NuminaMath (larger, licence check needed).

**D-12 Unit prices for the money proxy.** Glen sets p_identity, p_token, p_gpu_hour; defaults proposed at freeze. No recommendation; these are parameters.

## Open (M2 pilot stop, 2026-11-10)

**D-13 Campaign and scoring generation caps — TAKEN as option 1 (decision 16, amendment A1).**
Trigger: FINDINGS F20 (38% of campaign responses hit the 6,144 cap; APPS 86%, MATH 39%).
1. **Amendment A1: raise the campaign cap to 14,000 generated tokens and the scoring cap from 8,192 to 14,000** (teacher served at 16,384 context; prompts are < 2k). Restart the campaign and the teacher scoring from scratch (34 MATH-500 items scored so far are discarded, nothing reportable produced). Cost: mean tokens per pair rises (deciles suggest most complete by ~6k; the tail is unknown), teacher scoring ≈ 40–60M tokens ≈ 7–10 GPU-h at 1,635 tok/s; campaign ≈ 10M tokens ≈ 2 h. Keeps the hard region in the pool. **Recommended.**
2. Keep 6,144 and drop truncated pairs as frozen. Cheapest, but removes most APPS and ~40% of MATH from the training data by difficulty, which is the very shape L6 manipulates; H3 becomes uninterpretable. Not recommended.
3. Raise the teacher's context to 32,768 (Qwen3 native) and the caps to 30,000. Removes truncation almost entirely; halves concurrency (KV cache), roughly doubles the per-token cost of the tail; scoring could reach 15+ GPU-h. Only if option 1 still shows a material truncation rate (re-measured at 500 pairs).
4. Drop APPS from the pool (keep MBPP as the only code source) and keep 6,144. Removes the worst stratum but leaves MATH at 39%; shrinks the code side to 464 prompts. Not recommended.
Amendment type if taken: a parameter change with reason, logged in PROTOCOL §10 (neither MECHANISM REASSIGNED nor EVIDENCE DISQUALIFIED; no evidence existed yet).

## Open (throughput, 2026-11-10)

**D-14 Teacher throughput at the amended cap (needs Glen; paid-GPU change is a sign-off gate).**
Measured: 669 generated tok/s, 18 concurrent sequences, KV cache 92%, zero preemptions (F21). At
this rate the teacher side of the pilot is ≈ 20 GPU-hours and every later campaign arm scales the
same way; the 40 GB card is also the tight stage for GRPO with colocated generation.
1. **Switch the VM to an 80 GB card (H100 80GB if available on Lambda, else A100 80GB).** H100 is
   ≈ 2–3× the decode throughput and 4× the KV budget: teacher side ≈ 4–6 h; GRPO full-FT fits.
   Environment re-recorded (same vLLM 0.33.0 pin, same weights); the 89 partial outputs are
   discarded for consistency (nothing reportable). **Recommended.**
2. Keep the 40 GB card and serve the teacher with an FP8 KV cache (`--kv-cache-dtype fp8`):
   ≈ 2× KV capacity → ≈ 36 concurrent → ≈ 1,300 tok/s, teacher side ≈ 10 h. Quantises the
   teacher's KV, a small numeric change to the object under study; would be logged as decision
   and applied uniformly for the whole project. Acceptable second choice.
3. Keep everything and accept ≈ 20 h for the pilot's teacher side (and ≈ 2× every later estimate).
4. Amend k=4 → k=2 for teacher scoring only. Halves scoring cost; weakens the teacher CI; needs an
   amendment. Not recommended on its own.
5. **8× A100 (Lambda gpu_8x_a100, 40 GB or 80 GB).** The workload is embarrassingly parallel:
   8 teacher replicas (identity-sticky routing so D7's prefix-cache statistics stay per replica),
   8 training arms in parallel, 8 student replicas for scoring. Rough aggregate ≈ 5,000–6,000
   teacher tok/s. Whole study (M2–M5, F22 token totals): teacher ≈ 300M tokens ≈ 15 h; student
   scoring ≈ 750M tokens ≈ 45–50 h across 8 replicas; training ≈ 15 h wall with 8 arms in
   parallel → ≈ 3–4 days of continuous use, ≈ $800–1,000 at the 40 GB rate. Pilot alone ≈ 6–8 h
   wall. Harness changes: replica launcher, sticky client routing, per-replica metric scrape.
   Recommended if Glen wants wall-clock, otherwise option 1 (single H100 ≈ 7 days, ≈ $450).
6. **2× H100 80 GB SXM5 (Lambda, ≈ $6/h).** Per GPU ≈ 2.5–3× A100-40GB decode bandwidth and
   ≈ 65 GB of KV (≈ 440k tokens, ≈ 30–40 long sequences), so each replica batches well: teacher
   ≈ 2,500–3,500 tok/s per GPU, student ≈ 6,000–8,000. Whole study: teacher ≈ 300M tokens ≈ 14 h;
   student scoring ≈ 750M ≈ 15 h (≈ 10 h with the GSM8K-subset amendment); SFT ≈ 12 h and GRPO
   ≈ 25 h with two arms in parallel → ≈ 2.5–3 days, ≈ $400–450. Pilot ≈ 5–6 h. Full-FT GRPO fits
   in 80 GB. Harness changes are small (two replicas, sticky routing). **Recommended over 5:
   similar wall-clock at roughly a third of the cost.**
Jobs continue at the current setting until decided; resume keeps completed work under option 3 and
discards it under 1, 2, 5 and 6 (different hardware or numerics).

## Open (APPS truncation, 2026-11-10)

**D-15 APPS stratum at the A1 cap (FINDINGS F23).** The pilot continues meanwhile; truncated pairs
are excluded from SFT and counted, as frozen.
1. **Proceed with the pilot as is; decide at HARD STOP 3 with the full 2,000-pair numbers.** Add
   one sensitivity arm then if needed: re-sample only the truncated APPS items with the teacher
   served at 32,768 context and a 30,000 cap, and report whether SFT on the longer traces changes
   the after-repair score or the D8 baseline statistic. **Recommended** (no further amendment
   now; nothing reportable is lost).
2. Amend now: teacher context 32,768 and campaign cap 30,000 for the APPS stratum only. Removes
   most APPS truncation; ≈ 2× the APPS token cost; requires restarting the two replicas (scoring
   is unaffected; its cap stays 14,000).
3. Amend now: drop APPS from the pool; code side = MBPP only (464 prompts). Shrinks the code
   stratum to the easy end; weakens the code half of L6.
4. Amend now: re-weight the campaign (APPS 400 → 200, MATH +200). Reduces the share of
   truncated data without changing caps; still drops the hardest APPS half.

## Open (SFT recipe, 2026-11-11)

**D-17 SFT hyperparameters (amendment A2 to frozen PROTOCOL §3; needs Glen).** Trigger: F27.
Exploratory runs on the pilot data (labelled `explore_*`, never reported): E1 = lr 5e-5, effective
batch 16, 3 epochs (≈ 324 steps); E2 = lr 2e-5, effective batch 16, 3 epochs. Each is checked for
P(`<think>`), P(`</think>`), and accuracy on the first 100 MATH-500 and 100 GSM8K items.
Options are completed with the E1/E2 results before Glen is asked.

Exploratory results (non-reportable; first 100 items × k=2 per suite; F29 and VM logs/explore_sft.log):

| Recipe | Steps | Train loss | MATH-500 | truncated | GSM8K | truncated | empty answers |
|---|---|---|---|---|---|---|---|
| Frozen: lr 1e-5, batch 64, 2 ep | 56 | 0.576 | no structured answers (F27) | | | | all |
| E2: lr 2e-5, batch 16, 3 ep | 327 | 0.477 | 0.19 | 116/200 | 0.34 | 87/200 | 94 |
| E1: lr 5e-5, batch 16, 3 ep | 327 | 0.411 | 0.51 | 93/200 | 0.58 | 82/200 | 0 |

Options:
1. **Amendment A2 = E1 recipe (lr 5e-5 cosine, effective batch 16, 3 epochs, full FT), fixed for all
   arms.** Structure is learned (no empty answers; 95–98% correct when it finishes); the looping
   on ~45% of generations is left for the repair stage to address, which is the phenomenon the
   paper is about. **Recommended.**
2. A2 = E1 plus one more exploratory run first (lr 1e-4 or 5 epochs) to see whether SFT alone
   removes the loops. ≈ 45 min more; risk of tuning SFT until repair has nothing to do.
3. Switch the primary student to post-trained Qwen3-1.7B (control tokens already trained).
   Rejected earlier for lack of headroom (F3); not recommended.

## Open (benign traffic design, for the HARD STOP 3 / M3 review, 2026-11-11)

**D-18 Benign model sizing and scoreability (FINDINGS F32, F31).** Four linked choices:
a. *Who is scoreable for coverage (D8, C1).* (1) Keep matched n = 30 and oversample heavy real
   users: draw conversational identities from all 14 files but keep every user with ≥ 30 requests
   and a thinned sample of the rest, reporting the sampling weights. **Recommended.** (2) Lower
   matched n to 10 (more users scoreable, noisier statistic; changes the frozen D8 definition →
   amendment). (3) Keep as is and report D8 only at the 1% budget.
b. *Eval-harness size.* (1) 50–200 prompts per identity instead of 200–1,000 (cuts the component
   from 73% to ≈ 30% of requests). **Recommended.** (2) Keep.
c. *Timeline.* Replay runs as fast as capacity allows, per-session order preserved, with the
   corpus timestamp attached to every record for the cadence detectors; this is decision 12's
   time-scaled replay with an unbounded factor. (1) Accept and record. **Recommended.** (2) Real
   bounded factor k (wall-clock days).
d. *FPR budgets.* With (a1) the realistic target is ≈ 2,000–3,000 scoreable identities: 1% is
   resolvable, 0.1% is at or below the floor for identity-level detectors and resolvable for
   session-level ones only with ≈ 10,000 scoreable sessions. (1) Report 1% as the primary budget
   for identity-level detectors and 0.1% where resolved, stating the floor (the protocol already
   requires "below resolution" labelling). **Recommended.**

## Open (HARD STOP 3 and 4 review, 2026-11-11)

Options, evidence and recommendations for D-19 (repair-only arm), D-20 (copy recipe and N_full),
D-21 (capability ladder and repair subset), D-22 (detectors that failed predictions), D-23 (the
bar), D-24 (compute), together with the still-open D-15, D-18 and the ratification of decisions
19 to 21, are in docs/review_hardstop_3_4.md. Nothing listed there has been started.

**Closed 2026-11-11:** all of the above taken as recommended (decisions 23 to 31). D-25 and D-26 closed as decisions 34 and 35.

## Open (repair-only arm scoring, 2026-11-11)

**D-25 How to score output that never closes its think span (FINDINGS F43).** The registered
path gives the repair-only arm 0.0000 on every suite because its whole output lands in the
reasoning field. The choice changes other arms' numbers too.
1. **Adopt one rule for every arm, as an amendment: verify the answer text; if the think span
   never closed, verify the whole output. Re-derive every canonical score under it (no new
   generation needed) and report the old numbers beside the new ones once. Apply the A6
   criterion under this rule. Recommended.** It is the rule the repair reward already uses, and
   it removes a path where the exam and the reward disagree about the same output.
2. Keep the registered path for every arm and re-serve the repair-only student without the
   reasoning parser for its exam. Leaves the other arms' canonical numbers unchanged but scores
   arms through two different serving configurations.
3. Keep the registered path and report the repair-only arm as unscoreable.
**D-26 Missing control: the untouched student in chat mode, no repair (F43).** About 15 minutes
on the idle GPU; the checkpoint already exists (repair_only_s0/base).
1. **Score it on the full suite now, under whichever rule D-25 selects. Recommended.** Without it
   the repair-only score cannot be split into what repair added and what the student already had.
2. Do not run it; keep the few-shot completion-mode numbers (F28) as the only untouched baseline.

| 44 | 2026-11-12 | Revision R1 after three external AI reviews (all "reject, resubmission encouraged"): amendment B6 registers held-out calibration, all-day placements for the reported cells, a pooled-account content control, benign-volume and D10-scale sensitivity, and the benign-tail checks, with predictions P25 to P36, before any run. Two attacker-side items in the proposed plan (a further attacker family; a finer stagger grid) are not run: the reviewers' request for a test against an attacker the cross-account detectors were not designed for is answered as a stated limitation. Text changes: claims scoped to the corpus and teacher; content conclusion rewritten; C2 relabelled an adaptation; prediction counts by protocol; related work and ethics additions; the cell recipe leaves the abstract and conclusion and Table VI reports cost ranges rather than exact parameters. | run the full proposed plan / run the defender-side subset / text only | Glen: "i agree with your recommendations. go" (2026-11-12); the two attacker-side items dropped by the agent after a safety stop. | taken | chat 2026-11-12 |
| 45 | 2026-11-12 | Title confirmed: "What a Serving Layer Can See: Calibrated Detection of LLM Distillation Campaigns across Pattern, Account and Content Visibility" (drops "must"; names the three kinds of visibility as section II defines them). Competing-interest sentence removed from the ethics statement; no funding statement in the paper. | four candidate titles | Glen: "go with title #1" (2026-11-12) | taken | chat 2026-11-12 |
| 46 | 2026-11-12 | Second-round review (same reviewer, verdict (c) with a stated path to (b)): amendment B7 registers six defender-side re-analyses (P37 to P42). The reviewer's request to re-score the lever cells against a recalibrated cadence detector is not run: writing it requires characterising the lever's pacing against the detector, which the agent will not do; the manuscript states the untested question as a limitation. Text changes per the review's consistency list; Table III keeps client-declared sessions with a sharper caption; Table VII keeps cost ranges and the register's P30 wording is trimmed to match. | full list / defender-side subset / text only | Glen: "go" (2026-11-12) | taken | chat 2026-11-12 |
| 47 | 2026-11-12 | Adversary pass (fresh agent, PDF only) answered: amendment B8 registers eight defender-side items (P43 to P50) and one public prompt sample; the sign of the programmatic-baseline price statement corrected; the registered instruction-corpus content result restored to the headline; the sessions-per-day sentence corrected. Not run: paced cells against a recalibrated cadence detector, aged accounts, finer stagger grids (attacker-side). | full list / defender-side subset | Glen: "go" (2026-11-12) | taken | chat 2026-11-12 |
| 48 | 2026-11-12 | Fourth review (fresh agent, PDF only) decided on the paced cells against the recalibrated cadence detector. Amendment B9 registers that scoring as a defender-side re-analysis of recorded cells (P51), plus a kernel diagnostic; text fixes per the review. | run / decline again | agent, under Glen's standing "go" for thoroughness | taken, ratified by Glen 2026-11-12 ("go for all of your recommendations") | chat 2026-11-12 |
| 49 | 2026-11-13 | Pre-submission tightening: further tables and the capability appendix moved to the supplementary document; a second out-of-corpus benign sample registered as amendment B10 (P52). | do / defer | Glen: "do 4 and 6" (2026-11-13) | taken | chat 2026-11-13 |
| 50 | 2026-11-13 | Sixth external review (AI-generated, at Glen's request): verdict (c) on the cadence detector being untested against an attacker who knows it. The jitter sweep it asks for is attacker design and is not run. Amendment B11 registers the defender-side items (P53, P54); the manuscript stops presenting recalibrated cadence as a tested defence, removes the ethics claim that rested on it, and describes the pre-submission reviews as what they were: AI-generated reviews. | sweep / defender-side only | agent, under the standing scope; for Glen's ratification | taken, ratified by Glen 2026-11-13 ("agreed on your points") | chat 2026-11-13 |
| 51 | 2026-11-13 | A second benign baseline from public production API traffic (ServeGen per-client traces) for the rate and cadence detectors, registered as amendment B12 (P55, P56). Recalibrated cadence moves out of the abstract and the first introduction result pending that baseline. The earlier statement that no public trace carries a client identifier is corrected: two were checked, a third was not found until now. | run / skip | Glen: "go. keep me updated" (2026-11-13) | taken | chat 2026-11-13 |
| 52 | 2026-11-13 | Framing of the central claims changed to rest on two benign baselines (F92): the per-account rate result is stated as a property of the chat baseline and shown to vanish on large API clients; cadence regularity, calibrated on real sessions, is reported as the content-blind signal that flags fixed-interval pacing on both, and returns to the abstract. Cross-account and content results remain single-corpus and say so. | reframe / add as a section only / leave out | Glen: "go with option 1" (2026-11-13) | taken | chat 2026-11-13 |
