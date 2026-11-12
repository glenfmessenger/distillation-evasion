# PROTOCOL v2.0 — frozen 2026-11-11 (commit hash in GATES.md; decisions 32 to 36)

Supersedes PROTOCOL.md v1.0 (frozen 3df33c3, amendments A1 to A6) on freeze. Every v1.0 result
(FINDINGS F1 to F43) is retained with its provenance and reported under v1.0's hypotheses as
tested or not tested; nothing is averaged across the two protocols. Decision 32.

Working title: *What a Serving Layer Must See: Calibrated Detection of LLM Distillation
Campaigns at Three Levels of Visibility.*

## 0. Question

What must a serving-layer defender observe to detect a model-distillation campaign at a fixed
false-alarm rate against real conversational traffic; what does each level of visibility add;
and what does the one level that fires on an unevaded campaign cost an attacker to get under?

Three visibility levels, measured on the same campaigns against the same benign baseline:

| Level | Defender sees | Detectors |
|---|---|---|
| V0 pattern | per-request metadata only: timing, token counts, turn structure, cache hits | D3 to D9 (v1.0 §5, unchanged) |
| V1 volume | V0 plus a stable account identity | D1, D2 (v1.0 §5, unchanged) |
| V2 content | V1 plus prompt text | C1 (v1.0, topic-cluster JSD), C2 (R3's embedding MMD, re-implemented from its public artefact), and the lexical baselines B1, B2 (§5) |

Boundary, stated once and binding: no evasion lever targets V2. The content level is measured
on the two baseline campaigns only, as a defender-side question (what does reading prompts add).
The only levers are the two already registered against V1 in v1.0 (identity splitting, rate
shaping), and they are evaluated at every level so that a lever that makes a campaign *more*
visible at another level is seen.

## 1. Hypotheses and numeric predictions (draft; Glen edits before freeze)

| ID | Statement | Prediction at 1% FPR unless stated |
|---|---|---|
| P1 | V0 does not detect an unevaded campaign whose prompts come from the benign population (C-real), replicating the C-bench pilot (F40). | Every D3 to D9 cell flags ≤ 10% of campaign sessions; AUC within 0.6 of chance for D4, D6. |
| P2 | V1 detects both unevaded campaigns, and identity splitting plus rate shaping brings it below threshold at a price denominated in identities and wall-clock only. | D1 and D2 flag the single-identity campaign; detection ≤ 10% at n ≥ 100 identities with rate cap q ≤ 0.9; zero extra teacher tokens. |
| P3 | V2 detects C-bench, and the lexical baseline matches the semantic detectors on it (global rule 6). | B1 (benchmark-membership) flags ≥ 95% of C-bench blocks; C2 flags ≥ 90%; C1 as in F36 (did not flag at 1%). |
| P4 | V2 adds little over V0 on C-real: content detectors calibrated on benign prompts do not separate a campaign drawn from the same population. | C2 and C1 flag ≤ 10% of C-real blocks; B1 and B2 ≤ 10%. |
| P5 | Ladder: content visibility helps only when campaign prompts are out of distribution relative to benign traffic. | Ordering of per-block detection: C-bench V1 ≥ V2 > V0; C-real V1 > V0 ≈ V2. |
| P6 | Identity splitting starves per-identity V2 statistics rather than changing content: per-identity C1/C2 go below resolution at n ≥ 100 while per-block detection is unchanged. | Per-block C2 on C-bench within 5 points across n; per-identity cells marked below resolution at n = 100 and 1,000. |

Secondary, already measured, reported with its limitation: at pilot scale with verifiable-reward
tasks, RL on the untouched student matched or exceeded copy-plus-RL (F43; one seed; scoring rule
per D-25). No further capability runs under v2.0.

Stop rules: v1.0 §0 and GATES.md apply unchanged.

## 2. Models, serving, records

Unchanged from v1.0 §1 and the record schema: teacher Qwen3-8B on the local vLLM 0.33.0 stack,
server-sourced token counts, write-ahead records with in-flight marking. No student is trained.

## 3. Campaigns

| Campaign | Prompts | N | Status |
|---|---|---|---|
| C-bench | v1.0 pool (MATH, GSM8K, APPS, MBPP) with the fixed reasoning suffix | 1,995 | exists (pilot_baseline, F24) |
| C-real | first-turn user messages from a held-out WildChat split: conversations whose pseudo-user is absent from the benign replay subset (the only calibration set whose prompt text is used; the timeline calibrates timing only and uses no text), English, non-toxic, 13-gram contamination check against the replay prompts, no system prompt, thinking on | sessions 0 to 19 (2,000 requests) of a single 8,000-request run; sessions 0 to 79 are the N = 8,000 sensitivity | to run, about 4 GPU-h for the whole run |

C-real is the general-capability distillation threat model (R13 describes harvested general
exchanges); it is a baseline, not a lever. Both campaigns are issued as the pilot was (single
identity, 100-request sessions, as fast as capacity allows); volume levers are applied by
re-scheduling the recorded responses (v1.0 §6: new identity assignment and timing, no new teacher
calls). Sensitivity (decision 36): the full 8,000-request run checks that the V2 result is not an
artefact of N; C-real proper is its first 20 sessions by session index, fixed here before the run.

## 4. Benign model

Amendment A3 as ratified (decision 23): full-corpus timeline for D1, D2, D3, D9; stratified
replay m3_v1 (49,663 completed records, F40) for D4 to D8 and for V2. Benign prompts for V2 are
the replay schedule's first user messages. The held-out split for C-real is disjoint from both.

## 5. Detectors

D1 to D9 and C1: definitions, grains, directions and FPR procedure unchanged from v1.0 §5.
- **C2, content MMD (R3, arXiv:2606.05725).** Per unit (identity at matched n = 30; 100-request
  block), MMD with the RBF kernel between the unit's bge-small-en-v1.5 prompt embeddings and a
  benign reference sample of the same size; threshold from benign-vs-benign at the budget;
  median over 20 seeded reference draws. Re-implemented from LabRAI/mmd-llm-mea-detection with
  the kernel bandwidth rule it ships; any deviation is logged.
- **B1, benchmark membership (lexical).** Share of a unit's prompts whose normalised text, or any
  13-gram of it, occurs in the public pools of v1.0 decision 13. Direction: high.
- **B2, template reuse (lexical).** Share of a unit's prompts sharing their longest common
  suffix of ≥ 8 tokens with another prompt in the unit. Direction: high. (Catches the fixed
  reasoning suffix of C-bench; expected near zero on C-real and benign.)
Rule 6: no V2 semantic claim is made unless the stronger of B1, B2 is reported beside it and
does not match it.

Budgets: 1% primary; 0.1% where resolved; below-resolution marking as in v1.0.

## 6. Levers (V1 only)

L1 identity split n ∈ {1, 10, 100, 1000}; L2 rate shaping, per-identity hourly cap at the benign
quantile q ∈ {0.99, 0.9, 0.5}; joint L1 × L2. Each cell is a re-scheduling of a recorded
campaign; 5 re-schedulings per cell (v1.0 decision 9). Price per cell: identities, campaign
wall-clock on the scheduled timeline, teacher tokens (constant by construction). Money as v1.0 §7
with p_gpu_hour = 4.19 USD (decision 31).

## 7. Analysis plan

Per cell and level: detection at 1%, 0.1% and the resolution floor, with AUC; thresholds located
per re-scheduling first, then pooled as median and range (charter 3.5). Ladder table: campaign ×
level × lever cell. V1 price: the smallest (n, q) at which detection ≤ 10%, per re-scheduling,
then pooled. V2 claims gated by rule 6. Capability side table: F28, F34, F39, F41 to F43 under the
rule chosen in D-25, with the registered-path numbers beside them once. All CIs BCa, 2,000
resamples, seeds committed.

## 8. Compute

| Item | GPU-h | USD at 4.19 |
|---|---|---|
| C-real campaign, 8,000 requests | about 4 | about 17 |
| V2 embeddings (benign + two campaigns) | about 0.5 | about 2 |
| D-26 control (untouched student, chat mode) | about 0.3 | about 1 |
| (C-real run above already includes the N = 8,000 sensitivity) | 0 | 0 |
| Re-schedulings and all detector analysis | CPU | 0 |

Node idle time dominates; the node can be released once C-real and the embeddings are on disk
and copied to the repo's evidence folder.

## 9. Resolved at freeze (Glen, chat 2026-11-11, "proceed with your recommendations")

1. P1 to P6 accepted as drafted (decision 33). 2. D-25: one scoring rule for every arm, the
   registered-path numbers shown beside it once (decision 34). 3. D-26 control run (decision 35).
4. N = 8,000 sensitivity included as the single run above (decision 36). 5. Title accepted.

## 10. Amendments

**B1 — 2026-11-11 — Breadth additions, registered before the data they are tested on exists
(reason: FINDINGS F48, F50 and the R3 batch check; Glen: "be not just thorough in depth but in
breadth").** Decision 37.
1. *Second generation seed of C-real* (seed 1, 2,000 prompts, conversations disjoint from seed 0):
   every v2 detection cell is reported for both seeds; the seed-1 campaign is also the held-out
   test for items 3 and 4.
2. *Content calibration on all heavy real users* (every WildChat pseudo-user with ≥ 30 user turns,
   C-real users excluded; no teacher calls, prompt text only): the content level is re-calibrated
   on about 5,000 identities so that the 0.1% budget is resolvable; the replay-subset calibration
   stays the primary table and the two are shown side by side.
3. *Post-hoc content statistics, labelled as such*: C3, within-unit diversity (mean pairwise
   cosine distance of the unit's prompts, direction high), motivated by F50's observation that
   the campaign is broader than any real user; and C2 two-sided (the unit is flagged when its
   MMD² is below the benign 1% lower quantile as well as above the upper one). Predictions on
   the seed-1 campaign, fixed now: C3 flags ≥ 90% of 100-request blocks at 1%; two-sided C2 flags
   ≥ 90%. Prediction on C-bench seed 0 (already observed for C2's direction, so not a test): C3
   reported only.
4. *Second embedding model* (BAAI/bge-base-en-v1.5): C1, C2, C3 recomputed; a conclusion that
   changes with the embedding model is reported as model-dependent.
5. *Sensitivity to matched n and block size*: n_match ∈ {10, 30, 100}, block ∈ {50, 100, 500}.
6. *R3 batch design*: the first-turn-only benign control (F51), and the campaign share curve at
   {0.01, 0.02, 0.05, 0.1, 0.25, 0.5}, read against the volume law so that each share maps to a
   campaign rate relative to the service's.
7. *Third campaign, C-instr* (pending Glen's approval of the GPU time): 2,000 prompts from a
   public instruction corpus not derived from chat logs (databricks-dolly-15k), the "ordinary but
   different source" case. Predictions: V0 and V1 as C-real; C2 per-identity ≤ 10% at 1%; B1 0;
   pooled-window pure detection 1.00.
Not added, stated as limits: a second teacher (the benign replay would have to be repeated, about
8 GPU-h) and response-side content.


**B2 — 2026-11-11 — D10, a content-blind cross-identity coordination detector, registered before
any run (reason: F47, F49, F53, F56; Glen: "i want the coordination detector").** Decision 39.

*Motivation.* Every detector of §5 scores one request, session or identity. The lever that clears
the volume level, splitting a campaign over n identities, defeats all of them and starves the
per-identity ones (P6 held). It also creates a population that benign traffic does not contain:
n identities active together whose content-blind statistics are near-identical.

*Unit.* An identity-day: one identity's requests within one UTC day of the scheduled timeline.
Only timeline fields are used, so the calibration population is every benign identity-day of
the full corpus (all real pseudo-users), not the replay subset.

*Features per identity-day* (content-blind; from timing and turn structure only): log request
count; log session count; median session length in requests; log median intra-session
inter-arrival; log active span within the day; start hour of day as sine and cosine; fraction of
single-turn requests. Each feature is standardised by the benign median and median absolute
deviation computed once over all benign identity-days.

*Statistic.* For identity-day i, D10 = the number of other identity-days of the same day whose
standardised feature distance from i is at most r, where r is the median, over benign
identity-days, of the distance to the nearest same-day neighbour (so a typical benign identity
has about one neighbour). Direction high. Threshold by the §5 procedure at 1% and 0.1% over benign
identity-days; with more than one hundred thousand units both budgets are resolvable.

*Campaign scoring.* The campaign's records, split and shaped by the §6 levers, are placed on the
benign timeline at a seeded calendar day drawn uniformly from the corpus span (one placement per
re-scheduling, 5 re-schedulings), and each campaign identity-day is scored against the benign
identity-days of the same day. Detection = fraction of campaign identity-days flagged; also
reported: the fraction of campaign identities with at least one flagged day.

*Adaptive split (the attacker's answer, registered now as lever L8).* The round-robin split is
replaced by a heterogeneous one: per-identity request counts drawn from the benign identity-day
count distribution (rejecting counts above the cap), per-identity start offsets spread uniformly
over a stagger window S ∈ {0, 1, 6, 24, 72} hours, and per-identity session sizes drawn from the
benign session-length distribution. Price: identities, wall-clock (which grows with S), tokens
constant.

*Predictions, fixed before any run.*
P7. Round-robin split, n ∈ {100, 1000}, unshaped and shaped at 26 per hour: D10 flags ≥ 90% of
campaign identity-days at 1%, on C-bench and on both C-real seeds alike (content-blind).
P8. n = 10 round-robin: ≥ 50% flagged (fewer clones, but still clones).
P9. Heterogeneous split with S = 0: detection falls but stays ≥ 50% at n = 100 (counts differ,
times coincide). With S ≥ 24 h at n = 100: detection < 10% at 1%; the price of escaping D10 is
therefore a stagger of at least a day, which at the volume cap multiplies wall-clock accordingly.
P10. Benign identity-days of the constructed components (eval harness, batch, agent) are not
flagged above the 1% rate as a group; if they are, the detector's false alarms on legitimate
coordinated traffic are reported as its main limit.
Stop rules of GATES.md apply. No content is read; no lever targets V2.

**B3 — 2026-11-11 — D11, account-birth burst, registered before any run (reason: F58; Glen:
"all four").** Decision 40.

*Unit and statistic.* An identity's birth is the scheduled time of its first request on the
absolute timeline. D11 for identity i = the number of other identities born within W of i's
birth, W = 10 minutes (W = 60 minutes reported as a sensitivity). Direction high. Calibrated on
every benign identity of the absolute timeline (118,465 births over 387 days), thresholds at 1%
and 0.1% by the §5 procedure; both budgets resolvable. Content-blind.

*Campaign scoring.* As D10: the split campaign placed at a seeded day, each campaign identity's
birth counted against benign births of the same timeline plus the other campaign identities.
Price: an attacker who does not want simultaneous births must either stagger (time, lever L8's S)
or use accounts born earlier (aged accounts), which is a cost in identities bought ahead of
time, priced per identity by §7's p_identity; the paper reports both.

*Predictions, fixed before any run.*
P11. Round-robin split, n ∈ {100, 1000}: ≥ 90% of campaign identities flagged at 1%. n = 10: ≥ 50%.
P12. Heterogeneous split, n = 100, S = 0: ≥ 90% (births coincide even when counts differ).
P13. Heterogeneous split, n = 100, S = 72 h: < 10%. S = 24 h: < 50%.
P14. Heterogeneous split, n = 1000, S = 24 h: ≥ 50%.
P15. The joint price: the cheapest cell with every content-blind detector (D1 to D11) under 10%
flagged is a heterogeneous split with S ≥ 24 h at n = 100, costing more than 70 hours, on every
campaign alike.

**B4 — 2026-11-11 — Post-review additions, registered before any run (reason: three external
reviews, FINDINGS F62 when logged; Glen: "go ahead with the proposed plan").** Decision 41. All
runs on the Mac from the copied data; no teacher calls; no GPU.

1. *Benign coordinated populations (controls for D10 and D11).* Three populations constructed
   from the real benign timeline and placed on it exactly as campaigns are, scored by D10 and
   D11 at the existing thresholds, 5 placements each:
   - *Organisation*: 50 real heavy identities, each keeping its own real identity-days, with
     births re-timed uniformly over a 30-day window and activity shifted to business hours.
   - *Batch job*: 50 keys born within one minute, each issuing 40 requests per day at a 90 s
     interval with jitter in one session, for 10 days.
   - *Evaluation fleet*: 20 keys born within one minute, each issuing one burst of 200 requests
     at native pace once a week for 4 weeks.
   Predictions: P16, the batch job and the evaluation fleet are flagged by D10 (≥ 50% of
   identity-days) and D11 (≥ 90% of identities): the detectors do not distinguish legitimate
   coordination from a split campaign, and their deployment false-alarm rate is set by how much
   such traffic a service carries. P17, the organisation is flagged ≤ 10% by both.
2. *Combined adaptive attacker (lever L9).* An exhaustive search over a fixed grid, each cell
   5 placements, against every content-blind detector D1 to D11 at once: identities n ∈ {50,
   100, 200, 500, 1000}; per-identity request counts drawn as in L8 but truncated at c ∈ {26,
   100, 300}; session lengths drawn as in L8 and multiplied by m ∈ {1, 3, 10}; stagger S ∈ {0,
   6, 24, 72, 168} h; pacing at the 26-per-hour interval with jitter. A cell "clears" when every
   detector's median flagged fraction is ≤ 10%. Reported: every clearing cell, and the cheapest
   by wall-clock and by identities. Predictions: P18, at least one cell clears; P19, the cheapest
   clearing cell costs at least 24 h of wall-clock and at least 100 identities; P20, no cell with
   S = 0 clears (D11).
3. *D3 on completion times.* The campaign's cadence statistic recomputed on response completion
   times, so that both the benign and the campaign inter-arrivals include generation latency,
   reported beside the registered send-time version. Prediction P21: no change of verdict (0
   flagged at 1%).
4. *Expected alert volume.* For every detector, the benign units per day at the 1% and 0.1%
   budgets, from the calibration counts and the 387-day corpus span; a table, no prediction.
5. *Request-weighted pooled reference (optional, last).* The pooled design repeated with a
   reference pool drawn by request over every replayed identity, light users included.
   Prediction P22: the C-real pure window is no longer flagged once the conversation-uniform
   control is matched; the control and the campaign move together.
Scope corrections carried with this amendment: the campaigns are collection workloads of the
kind distillation requires, and the manuscript says so; the concurrent work arXiv:2611.06661
(4 November 2026) is cited and positioned.

**A8 — 2026-11-11 — Capability scoring rule tightened after a verification audit (reason:
FINDINGS F65).** A sample cut off at the generation cap is creditable only if it carries a boxed
answer; the trailing text of a truncated trace is not mined for a gold number. Applies to the
capability side table only. A7 and the registered path are reported beside it once. Decision 42,
taken on the agent's judgement during the pre-submission audit and flagged for Glen.

**B5 — 2026-11-12 — Two consistency checks raised in author review, registered before running
(decision 43).** (1) *Session definition.* Benign sessions follow the 1,800 s idle-gap rule;
campaign sessions were client-declared blocks of 100. Every unevaded campaign is re-scored with
its sessions re-derived by the same gap rule on send times. Prediction P23: under the gap rule D2
no longer flags the unevaded single account (one session in under two hours), and D1 still does.
(2) *Session size.* D4 and D6 are Kolmogorov–Smirnov distances that shrink with session size, and
campaign blocks (100 requests) are larger than benign scoreable sessions. Every campaign is
re-scored with its requests cut into consecutive sessions whose sizes are drawn (seed 0) from
the benign scoreable session-size distribution. Prediction P24: 0 flagged at 1% is unchanged, and
the D4 AUC on the ordinary-prompt campaign rises from 0.01 to between 0.3 and 0.7, so the "more
typical than the typical user" reading is a size artefact and is withdrawn.

**B6 — 2026-11-12 — Revision after three external reviews, registered before any run (decision
44; Glen: "i agree with your recommendations. go").** Scope: defender-side measurement only. No
new attacker family and no finer lever grid are run; the cells re-scored below are the cells the
manuscript already reports. All runs on the Mac from the copied data; no teacher calls; no GPU.
Predictions were written before any of the analyses ran; where a prediction was informed by a
number already seen, the item says so.

1. *Held-out calibration.* For every detector, the benign units are split at random into two
   halves (seeded, 20 splits; session-level detectors split by account so that an account's
   sessions fall on one side). The threshold is set on one half at the 1% budget and the
   false-alarm rate measured on the other, with an exact (Clopper–Pearson) 95% interval; the
   campaign flagged fractions of Table II are recomputed under each held-out threshold. Also
   reported: the per-account rate at which benign traffic trips *any* content-blind detector at
   the 1% budget (an account is flagged if any of its sessions or any of its account statistics
   is flagged), on the timeline accounts (D1, D2, D3, D9) and on the replayed accounts (all ten
   pattern and volume detectors, plus D10 and D11 for the replayed accounts' timeline days).
   Predictions. P25: for every detector not below resolution, the mean held-out false-alarm rate
   over the 20 splits lies in [0.5%, 1.5%]. P26: no campaign flagged fraction in Table II moves
   by more than 0.05 (median over splits) under held-out thresholds. P27: the any-detector
   per-account benign rate is between 2% and 10% on timeline accounts and between 5% and 30% on
   replayed accounts (replayed accounts are heavy and carry many sessions).
2. *Placements.* Every cell of Table V and every clearing cell of the wider search (62 of 225)
   is re-scored on every eligible placement day of the timeline (a day is eligible when the
   cell's schedule ends before the timeline does), one re-scheduling per day, instead of five;
   reported per cell: the distribution of each detector's flagged fraction (median, 5th and 95th
   percentiles), the campaign-level detection probability (the fraction of placements in which
   at least one unit is flagged by any content-blind detector), and the same quantities with the
   five original placements excluded. The placement affects only D10 and D11; D1, D2, D3 and D9
   are re-scored alongside for completeness. Table IV's cells are re-scheduled 50 times to give
   the range of their prices and flags under the scheduler's jitter. Predictions. P28: for the
   ten-account rate-capped round-robin cell, the campaign-level D11 detection probability over
   all placements lies in [0.05, 0.40] (one of five placements flagged all ten; informed by that
   number). P29: at least 80% of the 62 clearing cells still clear (all-placement median joint
   max at most 0.10). P30: the 50-account cell reported in the abstract (draw cap 26, session
   multiplier 10, stagger 6 h) has a joint max above 0.10 in fewer than 10% of placements. P31:
   the 100-account cell with the shortest schedule (11.8 h) has a joint max above 0.10 in more
   than 10% of placements (its worst of five was 0.28; informed by that number).
3. *Content controls.* (a) The per-account uniform control already run (content_ctrl,
   content_ctrl_heavy) is tabulated beside Table VIII; no new run. (b) A pooled-account control:
   synthetic accounts each formed by merging the prompt streams of m real replayed accounts
   drawn at random without replacement (m ∈ {5, 20, 100}; 100 synthetic accounts per m, or as
   many as the replay affords), interleaved in time order, scored by every content statistic at
   matched count 30 and in blocks of 100 against the primary calibration, with the constituent
   accounts excluded from the reference pool. This is the legitimate aggregation key (an
   organisation behind one API key) that the uniform control does not represent. Prediction
   P32: at m ≥ 20, C2low flags at least half of the pooled units at 1% (an aggregate of many
   users is closer to the population than any one user, which is what C2low measures), and C1,
   C2, C3, B1 and B2 each flag at most 0.10. (c) P22 (request-weighted reference pool) is run if
   the embedding model can be installed locally; its prediction stands as registered in B4.
4. *Sensitivity to benign volume.* D10 and D11 are recalibrated on the timeline with the benign
   account population subsampled at random to fractions f ∈ {0.1, 0.25, 0.5, 1.0} (seeded, 5
   draws each), and the ten-account rate-capped cell and the 100-account round-robin cell are
   re-scored under each; reported: thresholds, radius and campaign-level detection probability
   against f. D1 and D2 threshold intervals come from item 1's splits. Prediction P33: at
   f = 0.25 the D11 threshold at 1% is at most 10 and the ten-account cell's campaign-level D11
   detection probability is at least 0.5.
5. *Benign tails.* (a) D5: for the benign sessions above the reasoning-share threshold, the
   share of records with finish reason "length", against the replay-wide share. Prediction P35:
   fewer than half of those records are truncated (informed by the replay-wide count of 710
   truncated records in 49,663, already seen while checking the data). (b) D3: the session-size
   distribution of benign sessions below the cadence threshold, and the threshold recomputed
   with minimum session sizes 5 and 10. Prediction P34: at least half of the sessions below the
   threshold have exactly three requests. (c) B2: the share of replayed accounts with B2 = 1.0,
   and the share of their prompts' common suffix that is a fixed instruction (reported, no
   prediction). (d) The accounts above the D1 threshold: request count, single-turn fraction,
   cadence CV and session count, as descriptive quantiles; no estimate of scripted traffic is
   claimed.
6. *D10 scale sensitivity.* The standardiser floors each feature's median absolute deviation
   at 0.001; a feature with zero deviation (session count, for most account-days) is thereby
   given a very large weight, which the manuscript does not state. D10 is re-run with three
   alternatives: the constant-deviation features dropped; the floor raised to one unit; and
   deviation replaced by the interquartile range divided by 1.349, floored at 0.001. Reported
   for each: radius, threshold, the 100-account round-robin split on the ordinary-prompt
   campaign, and the three B4 populations. Prediction P36: under every alternative the
   100-account split is flagged at 0.95 or more, the batch job at 0.5 or more, and the
   organisation at 0.10 or less (medians over the five B4 placements).
