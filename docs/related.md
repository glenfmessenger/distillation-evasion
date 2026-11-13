# Related work (verified citations only)

Every entry below was resolved on 2026-10-08 by fetching the arXiv abstract page or the primary
source. "Full text checked" means the HTML full text was read for the specific questions noted.
Nothing from secondary blogs is cited.

## Novelty verdict

No published work specifies content-blind serving-layer detectors for a distillation campaign,
calibrates them against replayed benign traffic, sweeps adaptive evasion levers (identity
splitting, coverage reduction, decoys), and prices evasion in student capability **after a repair
stage**. Two preprints are adjacent and must be credited explicitly (R3, R6). Two charter
sentences are weakened by what was found (see "Charter corrections").

## Directly adjacent (must be cited and positioned against)

**R3. Liu, Guo, Dong. "An Embarrassingly Simple Detector for Model Extraction Attacks in Large
Language Model API Traffic." arXiv:2606.05725 (v1 2026-06-04, v3 2026-08-29). EMNLP 2026 main.**
Full text checked. Detector: MMD over `bge-small-en-v1.5` query embeddings in a traffic window,
threshold from benign-vs-benign only. Reports 0.3% FPR / 100% TPR on pure-attacker windows across
14 attacker–benign pairs. Includes an adaptive attacker (MMD-regularised and projection query
selection on an SST-2 extraction task): TPR at 5% attacker share falls 84.0% → 70.0% / 78.0%, and
student accuracy falls 76.38% → 67.43% / 67.09%. The paper states the detector "uses only query
text and is evaluated in an offline traffic-window setting", that timestamps, account metadata and
rate limits are left for deployments, that multiple accounts are a discussed but unsimulated
scenario, and that attacker cost is not quantified. No RL/repair stage. **Position:** first
published detectability–utility trade-off for extraction traffic, but content-reading, offline,
classifier-distillation, pre-repair. Ours is content-blind, live serving stack, reasoning
distillation, post-repair, with Sybil and coverage levers.

**R6. Javaheri, Panfilov, Britton, Gal, Gideoni. "Distillation Defenses Easily Break After
Reinforcement Learning." arXiv:2609.35699 (2026-09-28).** Full text checked. GRPO (SimpleRLZoo)
with binary verifiable rewards (math-verify) after SFT distillation. Students 0.5B–7B, RL on ≤3B;
main teacher Qwen2.5-14B-RL, student Llama-3.2-3B-Base; antidistillation arm Qwen2.5-0.5B student,
Qwen2.5-1.5B-RL teacher. Finds low/mild antidistillation poisoning is mostly recovered by RL;
expanded reasoning summaries from closed APIs match full-trace distillation after RL. Discusses
"batch-level" defences over sets of related queries as a direction, notes attackers "use multiple
accounts operating from different locations", builds no detector. **Position:** validates our
repair stage (GRPO + verifiable rewards) as the attacker's standard move and motivates measuring
cost after it; leaves serving-side detection and its evasion cost untouched.

**R4. Libon, Peetathawatchai, Aerni, Paleka, Tramèr. "What Does It Mean to Break a Distillation
Defense?" arXiv:2606.25059 (v1 2026-06-23, v2 2026-07-13).** Full text checked. Threat-model
framework: query budget ("total number of API calls to the teacher"), data budget ("number of
distinct input prompts available"), interface profile ("structured, qualitative description of
how the attacker can observe and interact with the API"). Section 4.2: distributing queries across
multiple accounts "obtains a larger effective query budget while operating on the same fixed pool
of prompts". Section 3.3 lists "usage quotas, rate limits, behavioral fingerprinting, coordinated
activity monitoring" as provider system-level mechanisms, evaluates none. SFT via LoRA, no RL.
Teacher DeepSeek-R1-Distill-Qwen-7B, student Llama-3.2-3B. **Position:** supplies the vocabulary
(query/data budget, interface profile) we should adopt; our levers are concrete instances of
interface-profile variation, and our D1/D2 results are the first measurement of the "multiple
accounts" remark.

## Output-side distillation defences (contrast only; out of scope)

**R2. Savani, Trockman, Feng, Xu, et al. "Antidistillation Sampling." arXiv:2504.13146 (v5
2025-10-26). NeurIPS 2025 main.** Modifies next-token distribution to poison traces while keeping
teacher utility.

**R7. Ma, Yeoh, Zhang, Vorobeychik. "Protecting Language Models Against Unauthorized Distillation
through Trace Rewriting." arXiv:2602.15143 (v2 2026-04-16).** Rewrites traces; embeds detectable
watermarks in students. Output-side; detection is of the student, not the traffic.

**R8. Jiang. "DistillGuard: Evaluating Defenses Against LLM Knowledge Distillation."
arXiv:2603.07835 (2026-03-08).** Nine output-level configurations, Qwen3-14B teacher,
Qwen2.5-7B-Instruct student, MATH-500/HumanEval+/MT-Bench; naive attacker; excludes input-level
defences (query detection, rate limiting) from scope.

**R9. Hartman, Jayaraman, Choraria, Savani, Varshney. "Hiding in Plain Sight: Detectability-Aware
Antidistillation of Reasoning Models." arXiv:2604.23238 (v2 2026-05-08).** "Detectability" means
the attacker detecting the defence, not the provider detecting traffic. Not a traffic detector.

**R10. Liu, Zhao, Xu, Chen, Wu, Wang, Dong. "Do Defenses Against LLM Extraction Work Across
Attacks? A Lifecycle Benchmark of Black-Box Model Extraction." arXiv:2610.00839 (v2 2026-10-07).**
Six attacks, ten defences, two adaptive attacks (paraphrase / back-translate responses). No
traffic detector among the defences on the abstract page; provenance detectors only.

## Attack-side context

**R11. Panfilov, Schmotz, Shumailov, Beurer-Kellner, Schaeffer, Prabhu, Geiping, Andriushchenko.
"Stealing Reasoning Traces from Proprietary LLM APIs." arXiv:2608.09867 (2026-08-10).** Encrypted
reasoning blocks are interchangeable across sessions; decryption jailbreak recovers hidden traces.
No repair stage, no traffic detection.

## Adaptive-attack methodology

**R1. Nasr, Sitawarin, Hayes, Schulhoff, Ilie, Pluto, Song, Chaudhari, Shumailov, Thakurta, Xiao,
Terzis, Tramèr, Carlini. "The Attacker Moves Second: Stronger Adaptive Attacks Bypass Defenses
Against LLM Jailbreaks and Prompt Injections." arXiv:2510.09023 (2025-10-10).** Full text checked
for cost language. Found: Section 3 assumes "a large amount of computational resources" and argues
"a defense that can be overcome with a fixed budget of commodity hardware" is not secure; an open
question on achieving strong attacks more efficiently; Appendix F.1 "Cost of an attempt differs
greatly between human and automated attacks". **NOT found:** any sentence naming attacker/defender
cost modelling as an explicit open problem. See charter correction C2.

## Classical query-distribution detection

**R12. Juuti, Szyller, Marchal, Asokan. "PRADA: Protecting against DNN Model Stealing Attacks."
arXiv:1805.02628. IEEE EuroS&P 2019.** Distribution of successive query distances per client;
image classifiers; no adaptive LLM-setting evaluation. Baseline lineage for R3.

## 2026 context (primary source)

**R13. Anthropic, "Detecting and preventing distillation attacks", 2026-02-23.** Names DeepSeek,
Moonshot, MiniMax; "more than 16 million exchanges" via "approximately 24,000 fraudulent
accounts"; one proxy network "more than 20,000 fraudulent accounts simultaneously". Signals
described: cross-account coordination (identical patterns, shared payment methods, coordinated
timing), synchronised load suggesting load balancing, volume concentration, repetitive prompt
structures, chain-of-thought elicitation classifiers, behavioural fingerprinting, IP/metadata
correlation. Detection was account- and pattern-level, not output-side defence.

## Models and data (cards fetched 2026-10-08)

- **Qwen3 Technical Report**, arXiv:2505.09388. Post-trained thinking/non-thinking: Qwen3-8B
  MATH-500 97.4/87.4, AIME'24 76.0/29.1, LiveCodeBench v5 57.5/22.8; Qwen3-4B 97.0/84.8,
  73.8/25.0, 54.2/21.3; Qwen3-1.7B 93.4/73.0, 48.3/13.4, 33.2/11.6 (Tables 17–20). Base: GSM8K
  89.84/87.79/75.44, EvalPlus 67.65/63.53/52.70, MBPP 69.80/67.00/55.40, MATH 4-shot
  60.80/54.10/43.50 (Tables 6–8).
- **Qwen/Qwen3-8B**, **Qwen/Qwen3-1.7B**, **Qwen/Qwen3-1.7B-Base**: Apache-2.0; `<think>` traces;
  32,768 context; 1.7B-Base is pretraining-only.
- **deepseek-ai/DeepSeek-R1-Distill-Qwen-7B**: MIT; base Qwen2.5-Math-7B; MATH-500 92.8, AIME24
  55.5, LiveCodeBench 37.6; 1.5B sibling 83.9/28.9/16.9.
- **meta-llama/Llama-3.2-1B-Instruct**: Llama 3.2 Community License; 1.23B; GSM8K CoT 44.4, MATH
  CoT 30.6.
- **allenai/WildChat-1M**: ODC-BY; ungated; per-conversation `timestamp` (µs schema), `hashed_ip`,
  `turn`, `header` (user-agent, accept-language), `model`, `language`, moderation flags; dataset
  paper arXiv:2405.01470 (ID taken from the card, abstract not separately fetched).
- **lmsys/lmsys-chat-1m**: custom licence, gated, **no timestamps, no user IDs** on the card.
  Unusable for timing or session structure.

## Charter corrections arising

- **C1.** Charter §1 says output-side defences "stop before the attacker's cheap repair step".
  R6 (2026-09-28) publishes exactly that repair step. Rewrite: the repair step is published; what
  it costs the attacker *at the serving layer* is not.
- **C2.** Charter §1 says R1 "names the absence of attacker/defender cost modelling as an explicit
  open problem". Not verified verbatim. Rewrite to the passages actually found, or supply the quote.
- **C3.** R3's adaptive-attacker result must be credited as the first detectability–utility
  trade-off measurement; our contribution is content-blind, serving-side, post-repair, with Sybil
  and coverage levers.

## Not cited (could not verify)

- SSRN 6298138 ("Industrial-Scale API-Based Model Distillation Attacks …"): HTTP 403; unread.
- Google Threat Intelligence and OpenAI distillation disclosures: secondary reporting only.
- Anthropic June 2026 letter to the Senate Banking Committee (Alibaba/Qwen allegation): secondary
  reporting only.

## Open-source tooling (checked 2026-11-10 via GitHub API and READMEs)

No mature or adopted open-source detector for distillation campaigns exists. What exists:

- **noisyloop/Glasswally** (Rust, MIT; created 2026-02-27, last push 2026-10-19, 1 star, 26
  commits). 16 fused signals per account: TLS/JA3 and HTTP/2 fingerprint mismatch, ASN, payment
  and subnet clustering, velocity (requests/hour, inter-arrival CV, token-count uniformity),
  session-gap regularity, cross-account synchronised bursts, `max_tokens` sweeps, plus
  content-reading workers (chain-of-thought phrase matching, n-gram embedding archetypes,
  system-prompt hash reuse, refusal-probe density, prompt-topic Markov chain). README states
  plainly: evaluated only on its own synthetic generator "written with full knowledge of the
  detectors"; "No benchmarks against real traffic exist yet"; the adversarial-evasion harness
  (`redteam.rs`) is "not wired". Design cites the Anthropic 2026-02-23 post. **Relevance:** the
  nearest thing to a deployable serving-side detector; its metadata workers overlap our D1, D3,
  D6 and D7; it has no benign calibration, no FPR floor, and no measured evasion cost. Cite as the
  state of open tooling.
- **LabRAI/mmd-llm-mea-detection** (Python, MIT; 2026-06-04, 5 stars). Artifact for R3
  (arXiv:2606.05725). Content-embedding MMD; offline query sets.
- **lodetomasi/model-extraction ("mxd")** (0 stars, last push 2026-08-01; unpublished). The most
  useful of the three despite its size. Semantic-coverage detector over Amazon Titan embeddings,
  aggregated across identities, no timing or volume features by design. Measured against a
  white-box adaptive attacker and a real trace of 14,943 legal questions. README reports: AUC
  0.598 across the attack × evasion matrix; an attacker diluting itself 4:1 in organic traffic and
  spending 10% of budget on repetition "evades every alert across 53 windows" while extracting
  74.7% of the corpus; round-robin across 40 identities made the attacker *easier* to catch
  (recall 29% → 57%); **Jensen–Shannon divergence was anti-correlated** because a concentrated
  attacker gets more samples per topic and so a better distribution estimate than a real user, and
  was replaced by a sample-size-independent U-statistic ("coincidence deficit"); "coverage and
  exploration have the wrong sign" (sixty diverse users cover more cells than one attacker
  sweeping a subdomain); on a benign trace with 0% repetition, 24% of benign windows crossed
  threshold. Content-reading, no repair stage, no capability measurement. **Relevance:** three
  measured warnings for our D8 design (sign of coverage, sample-size bias of JSD, benign
  exploration as a false-positive source), and a measured instance of identity splitting raising
  detectability, which bears on H1. Unreviewed single-author repo; cite as a measured negative
  result with that caveat.
- Gateways (LiteLLM, Portkey, Kong AI Gateway): no distillation- or extraction-specific detection
  found in search results; not verified against their docs.
- Name collision: two unrelated "DistillGuard" papers (npm malware; output-side defence
  evaluation). Neither is a traffic detector.

## Re-verification of 2026-11-11 (for the manuscript bibliography)

Fetched from arXiv abstract pages on 2026-11-11: 1609.02943 (Tramèr et al., USENIX Security 2016),
1812.02766 (Orekondy, Schiele, Fritz), 2403.06634 (Carlini et al.), 1910.12366 (Krishna et al.,
ICLR 2020), 1503.02531 (Hinton, Vinyals, Dean), 2301.10226 (Kirchenbauer et al., ICML 2023),
2309.06180 (Kwon et al., SOSP 2023), 2309.07597 (Xiao et al., SIGIR 2024), 2402.03300 (Shao et
al.), 2405.01470 (Zhao et al., ICLR 2024), 2505.09388 (Qwen3), 2606.25059, 2504.13146, 2602.15143,
2603.07835, 2604.23238, 2610.00839, 2608.09867, 2510.09023, 2103.03874, 2110.14168, 2107.03374,
2108.07732, 2105.09938, 0805.2368, 2611.06661 (Khilar, concurrent). Corrections to entries above:
R9's authors are Hartman, Jayaraman, Choraria, Varshney (now v3, 2026-10-10); R1's author order
is Nasr, Carlini, Sitawarin, Schulhoff, Hayes, Ilie, Pluto, Song, Chaudhari, Shumailov, Thakurta,
Xiao, Terzis, Tramèr; R2's arXiv page lists no venue, so it is cited as a preprint. The classic
extraction papers are cited for what their titles and abstracts state only.


## Re-verification 2026-11-12 (revision R1)
Sixteen references added after the external reviews; each was verified on 2026-11-12 by a web lookup of its arXiv page, publisher page or the USENIX/ACM programme (SynchroTrap, CopyCatch, EvilCohort, Xiao et al. AISec 2015, Chen–Carlini–Wagner 2019, Blacklight, Feng et al. CCS 2023, Kesarwani et al. ACSAC 2018, SEAT, Dziedzic et al. ICLR 2022, Axelsson 2000, Sommer & Paxson 2010, Arp et al. 2022, BurstGPT (KDD 2025), Splitwise (ISCA 2024), Lightman et al. 2023). Venue corrections: Knockoff Nets to CVPR 2019; Carlini et al. to ICML 2024; Gretton et al. to the JMLR 2012 version. Public LLM API traces checked for a second benign baseline: BurstGPT carries timestamp, model, token counts, log type and a conversation-mode session id only; the Azure LLM inference trace carries timestamp and token counts only. Neither has an account identifier, so neither can calibrate a per-account or cross-account detector.
- 2026-11-12: oasst2023 (Köpf et al., NeurIPS 2023 Datasets and Benchmarks; arXiv 2304.07327) verified by arXiv lookup; used as the out-of-corpus benign prompt sample of amendment B8.
- 2026-11-13: pal2021stateful (arXiv 2107.05166), atli2019extraction (arXiv 1910.05429), chu2012automation (IEEE TDSC 9(6)), cao2012sybilrank (NSDI 2012) verified by web lookup; added for the fifth review.
- 2026-11-13: norobots2023 (HuggingFaceH4/no_robots dataset card, CC BY-NC 4.0) read directly; used as the second out-of-corpus benign sample (B10).
