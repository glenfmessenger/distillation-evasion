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

**B7 — 2026-11-12 — Second-round revision, registered before any run (decision 46; Glen: "go").**
Scope as B6: defender-side re-analysis of data in hand; no lever is changed or added, and lever
cells are not re-scored against cadence. All runs on the Mac; no GPU.

1. *Cadence threshold and session size.* D3 recalibrated on benign sessions of at least five and
   at least ten requests; the unevaded campaigns re-scored under each threshold with declared,
   idle-gap and size-matched sessions. Prediction P37: the unevaded campaigns remain unflagged
   under both thresholds.
2. *Reasoning share without truncation.* D5 recalibrated with records cut off at the generation
   cap excluded from the benign sessions; the campaigns re-scored the same way; each campaign's
   own truncation rate reported. Prediction P38: the threshold falls and the benchmark campaign's
   flagged fraction rises from zero to at least 0.10; the ordinary-prompt campaigns stay at zero.
3. *D10 scaling on every reported cell.* Each cross-account-table cell and each of the 62
   clearing cells re-scored under the three B6 scalings on the five registered placements, and
   the ten-account and 50-account cells on all placement days. Prediction P39: at least 80% of
   cells keep their clear/not-clear verdict under each alternative, and the two all-day cells'
   share of days over 10% moves by at most 0.05.
4. *Content controls.* (a) The uniform control and the pooled-account control under the second
   encoder, primary calibration. (b) C3 for both controls across the B6 calibration splits,
   tabulated from the existing held-out run. (c) The pooled-window check with the campaign's
   prompt filter (deduplication and benchmark n-gram exclusion) applied to the benign reference
   and held-out pools. Prediction P40: under the second encoder C3 flags at least 0.10 of the
   pooled-account control units at m ≥ 20; with the filtered pools the uniform control and the
   ordinary-prompt campaign are still flagged alike.
5. *Benign volume upward.* The timeline overlaid onto itself with calendar offsets of one and
   three days (two and four times the daily account volume), D10 and D11 recalibrated, the
   ten-account and 100-account cells re-scored on fifty placements. Prediction P41: the creation
   threshold at least doubles at four times the volume; the 100-account split stays flagged
   completely; the ten-account cell's share of placements with any account flagged does not rise.
6. *All-day controls.* The three B4 populations and the three D10 scalings' 100-account cell
   re-scored on every placement day. Prediction P42: medians unchanged from the five-placement
   values within 0.05.

**B8 — 2026-11-12 — Adversary-pass revision, registered before any run (decision 47; Glen: "go").**
Scope as B6 and B7: defender-side re-analysis of data in hand plus one public prompt sample; no
lever is changed, added or searched; lever cells are not re-scored against cadence.

1. *Decomposition of flags.* For the reported headline cells and the constructed organisation, on
   every placement day, which detector produces the first flagged unit and the largest flagged
   fraction (from the existing all-day evidence; no run). Prediction P43: in the 50-account cell
   the first flagged unit comes from a per-account detector, not from D10 or D11, on most of the
   days on which any unit is flagged.
2. *Benign volume further upward.* Overlay factors eight and sixteen. Prediction P44: at sixteen
   times the volume the 100-account round-robin split is no longer flagged completely (D10 or
   D11 median below 0.95).
3. *Budgets and campaign size.* Thresholds at 1%, 0.1% and 0.01% for the timeline-calibrated
   detectors (D1, D2, D3, D9, D10, D11); the price-table cells and the ten-, 50- and 100-account
   cells re-scored at each budget (five registered placements); the ten- and 50-account cells
   re-scored on the 8,000-request run at 1%. Prediction P45: at 0.1% the rate threshold at least
   doubles and the one-account price at least halves; the 100-account split stays flagged
   completely by both cross-account detectors at 0.1%; at 8,000 requests the ten- and
   50-account cells keep their cross-account verdicts and their schedules lengthen fourfold.
4. *Replay-calibrated pattern detectors.* (a) D5 and D7 recalibrated on sessions of at least ten
   requests, campaigns re-scored with declared and size-matched sessions. (b) D4 to D8b
   recalibrated with the 120 constructed accounts removed. (c) A two-sided (low-side) threshold
   at 1% for D4, D6 and D7, post hoc. Predictions P46: under (a) and (b) every campaign's flagged
   fraction stays at most 0.10 for every replay-calibrated detector; P47: under (c) the
   ordinary-prompt campaign's output-length statistic (D4, AUC 0.01) is flagged on at least half
   its sessions.
5. *D10's benign tail and the full timeline compounding.* The benign account-days above the D10
   threshold described (requests, sessions, start hour, single-turn share) against the median
   account-day; the any-detector rate on timeline accounts recomputed with D10 and D11.
   Prediction P48: that rate is at most 3.5%.
6. *Real profiles, simultaneous creation.* Fifty real heavy accounts as in the organisation
   control, with their first requests collapsed into one ten-minute window, fifty placements.
   Prediction P49: D11 flags at least 0.9 of them and D10 at most 0.10.
7. *Out-of-corpus benign sample.* Three thousand English first user turns of the public
   OpenAssistant conversations (oasst1, Apache-2.0), sampled with seed 0, scored by the
   per-account content detectors (blocks of 100) and by the pooled-window design as a control,
   prompts only, no teacher. Prediction P50: C2low flags at least 0.9 of its blocks and the
   pooled design flags every window, i.e. the content detectors flag any uniform draw from a
   public corpus, in or out of the calibration corpus.
8. *Pilot truncation.* The share of student samples cut off at the generation cap, per arm, from
   the existing scores; no prediction.

**B9 — 2026-11-12 — Registered before any run (decision 48).** Defender-side scoring of the
recorded lever cells under the two recalibrated cadence thresholds of B7 item 1 (sessions of at
least five and at least ten requests), with the cells' own sessions and with sessions re-derived
by the idle-gap rule; joint maximum and share of days with any unit flagged reported beside the
registered figures. No lever is changed. Prediction P51: at least one of the three headline cells
(one account at the cap, ten rate-capped accounts, the 50-account reliable cell) is flagged at
more than 0.10 of its sessions under the ten-request threshold. Also: the mean within-unit kernel
value of the per-account discrepancy statistic for benign accounts and the campaigns, to show
what the matched-count statistic measures (no prediction).

**B10 — 2026-11-13 — Registered before any run (decision 49; Glen: "do 4 and 6").** A second
out-of-corpus benign sample, to test whether the provenance result of B8 item 7 rests on one
corpus: three thousand prompts of the public No Robots instruction set (HuggingFaceH4/no_robots,
CC BY-NC 4.0; prompts written by human annotators, not chat logs), train split, sampled with
seed 0, scored exactly as the OpenAssistant sample was (per-account content detectors in blocks
of 100, primary configuration; pooled-window design with first-turn-matched pools), prompts
only, no teacher. Prediction P52: the diversity statistic C3 flags at least 0.9 of its blocks
and the pooled design flags every window; C2 and B1 flag at most 0.10. No prediction for C2low
(the instruction-corpus campaign and the OpenAssistant sample disagreed on it).

**B11 — 2026-11-13 — Registered before any run (decision 50).** Defender-side follow-up to a sixth
pre-submission review; no lever is changed, added or swept. (1) The recalibrated cadence detector
(sessions of at least ten requests) characterised: held-out false-alarm rate over 20 account
splits with an exact interval; the benign sessions it flags described (size, single-turn share,
accounts); and every one of the 62 clearing cells of the search scored under it, with the share
of each cell's sessions that have ten or more requests reported for every cell of B9.
Prediction P53: at least 0.9 of the scoreable sessions are flagged in every one of the 62 cells,
and in at least half the cells fewer than half the sessions are scoreable. (2) A benign reference
for the any-account-flagged measure: groups of 10, 50 and 100 benign accounts drawn at random
from the timeline (1,000 draws each), the share of groups with at least one account flagged by
any of the six timeline-calibrated detectors over the account's history. Prediction P54: for
groups of 50 that share is at least 0.5, above the 50-account cell's 0.36.

**B12 — 2026-11-13 — Registered before any statistic is computed (decision 51; Glen: "go").** A
second benign baseline from public production API traffic, defender-side. Source: the per-client
traces released with ServeGen (github.com/alibaba/ServeGen, Apache-2.0, commit d70c8b2): for each
client of three language-model tiers (m-large, m-mid, m-small; 314 clients in all) and one
reasoning model, fourteen days in ten-minute windows, each with the client's request rate and the
coefficient of variation of its inter-arrival times. Only the file layout and column names have
been read. The release does not say whether rates are rescaled or how clients were selected; both
are reported as limits, and the rate result is given in released units.
(1) *Hourly rate.* Per client and per client-day, the largest number of requests in any hour
(six consecutive windows, rate times window length). The 1% order-statistic threshold over
client-days (the per-client set is below resolution) and the quantiles of the per-client
maximum; the share of clients whose maximum exceeds the chat corpus's threshold of 26 an hour;
the hours one account would need for 2,000 requests at the API threshold. Prediction P55: more
than half the clients exceed 26 requests in their busiest hour, and the 1% client-day threshold
is at least 2,000 an hour, so the campaign as issued would not be flagged by a rate detector
calibrated on this traffic.
(2) *Cadence.* The distribution of the per-window coefficient of variation over windows with at
least ten requests (the unit differs from the paper's session statistic and is stated): its 1%
and 5% low-side quantiles, the share of windows below 0.305 (the recalibrated chat threshold)
and below 0.20 (the registered rate cap's cadence), and the share of clients with a median
below each. Prediction P56: fewer than 5% of active windows fall below 0.305, and the 1%
low-side quantile lies above 0.05; fixed-interval pacing at 0.20 is rare but not absent among
API clients.

**B13 — 2026-11-13 — Registered before any run (decision 53).** Defender-side corrections after a
seventh pre-submission review (AI-generated); no lever is changed. (1) *Time base.* The benign
cadence thresholds are computed on reply timestamps, which include generation latency, while the
lever cells were scored on scheduled send times. Every lever cell of B11 is re-scored on
completion times (scheduled time plus the record's own send-to-completion latency), sessions
ordered by completion, under the three cadence thresholds. Prediction P57: on the completion
time base fewer than half the scoreable sessions of the cells paced at the 26-per-hour interval
(the 1% cap cells, the heterogeneous cells and the search cells) are flagged under the
ten-request threshold, while the cells at the two stricter caps stay at 0.9 or more. (2) *API
baseline by tier and by client.* For each tier including the reasoning set: the share of clients
whose busiest hour is below the campaign's 2,000 requests; the number of distinct clients that
own the client-days above the 1% threshold and the windows below the cadence thresholds; a
by-client bootstrap interval on the pooled quantiles. Prediction P58: on the reasoning tier more
than a third of clients have a busiest hour below 2,000, and fewer than 20 clients own the
client-days above the pooled threshold.

**B14 — 2026-11-13 — Registered before any run (decision 54).** Four defender-side analyses after
an eighth pre-submission read (AI-generated, F94). No lever is added or changed, no campaign is
issued, and no schedule is designed against a detector; every item re-scores recorded cells or
recorded benign traffic.

(A) *Clearing with the corrected cadence detector.* For every recorded lever cell (the price
cells, the cross-account table's cells and the 62 clearing cells of the wider search), five
re-schedulings: the ten-request cadence detector on completion times (B13), with four
denominators: scoreable sessions (the rule used for every other detector), all sessions, accounts
(an account counts if any of its sessions is flagged), and requests (those in flagged sessions).
The corrected joint statistic of a cell is the larger of its recorded joint maximum on each
placement day and its cadence fraction; "clears" and "reliable" keep their definitions. Reported
under the scoreable-session denominator (primary) and the all-sessions denominator (secondary).
Prediction P59: under the primary denominator no cell that has a scoreable session clears (this
clause follows from F93 and is not a blind prediction); under the all-sessions denominator at
least half of the 62 search cells still clear, and neither the one-account nor the ten-account
cell at the 26-per-hour cap nor the 50-account reliable cell does.

(B) *Pattern statistics on comparable sessions.* Units: benign replay sessions with at least ten
completed records, and each campaign cut into sessions of benign sizes (the B5 rule, at least
ten records). Statistics: cadence variation, output-length distance, reasoning share without
truncated records, prompt-length distance, cached-prefix share, single-turn fraction. (i) Each
statistic with a two-sided threshold at a 1% total budget (resolution judged on total
exceedances). (ii) A joint score fitted on benign sessions only: squared Mahalanobis distance on
the standardised statistics (missing values set to the benign median, ridge 1e-6), threshold at
1%. (iii) As an upper bound that a defender without labelled campaigns cannot reach, a logistic
regression trained on benign sessions and one campaign and tested on the others. For (ii) and
(iii) the fit and threshold come from one half of the benign accounts and the false-alarm rate
from the other, 20 splits; the length reference distributions are those of the full replay, as
registered. Prediction P60: at a held-out false-alarm rate within half a point of 1%, the
benign-fit joint score flags more than 10% of the benchmark campaign's sessions and no more than
10% of the sessions of either ordinary-prompt campaign or of the instruction campaign (median
over splits).

(C) *Benign cohorts formed as a defender would form them.* Cohorts of 10 and of 50 benign
accounts first seen in the same six-hour window of the absolute timeline (every window with
enough first appearances; 1,000 draws), each account scored on the six content-blind timeline
and cross-account detectors at the registered thresholds over the 48 hours from its first
request. Reported: the share of cohorts with at least one account flagged, beside the recorded
50-account and ten-account cells. Prediction P61: for cohorts of 50 the share is at least the
50-account reliable cell's 0.36 and below the whole-history random-group figure of 0.82.

(D) *Content controls on observed units.* (i) Natural shared-address units: replayed real
accounts are grouped by the corpus's hashed address (the account key is a hash of address and
user agent; the address is read from the public corpus for this purpose only and is not
stored beyond a salted group label); every address with two or more replayed accounts and at
least 30 prompts between them is one unit, scored by the per-unit content statistics against the
registered thresholds with its constituents excluded from the reference draws. If fewer than 20
such units exist the item is reported as untested. Prediction P62: fewer than 10% of these units
are flagged by the low-side discrepancy statistic. (ii) The pooled-account control of B6 repeated
with merges drawn from real accounts only. Prediction P63: the low-side discrepancy statistic
flags at least half the merged units at m = 5 and at least 0.9 at m = 20 and m = 100.

Stop rule: if (B) flags more than half of an ordinary-prompt campaign's sessions at the held-out
budget, or if (D)(i) and (D)(ii) disagree in direction, stop and report before any manuscript
text changes.

**B15 — 2026-11-13 — Registered before any run (decision 56).** Two small defender-side checks
after a ninth pre-submission read (AI-generated), each needed to make a sentence already in the
manuscript either true or withdrawn. No lever, no campaign, no schedule. (1) *Small synthetic
merges.* The pooled-account control with merges of m = 2 and m = 3 real accounts (100 groups
each), to compare like with like against the observed shared-address units, which have a median
of two accounts. Prediction P64: the low-side discrepancy statistic flags between 0.05 and 0.40
of merges at m = 2, more at m = 3 than at m = 2, and more at m = 2 than the 0.03 of the observed
units. (2) *One-sided thresholds on the matched units.* On the units of B14 (B), each of the six
statistics with a 1% threshold on each side separately. Prediction P65: the largest flagged
fraction over statistics, sides and campaigns is at most 0.15 and is the low side of the
output-length distance on an ordinary-prompt campaign.

**B16 — 2026-11-13 — Registered before any run (decision 57).** Defender-side re-analyses of
recorded data after four external reads (AI-generated, F97). No lever, no campaign, no schedule.
(1) *Held-out profile detector within the half.* The held-out calibration of the profile detector
with standardiser, radius, neighbour counts and threshold all taken within the calibration half
and the false-alarm rate measured with neighbours counted within the test half. Prediction P66:
the half-population threshold lies between 15 and 25 and the held-out false-alarm rate within
half a point of 1%. (2) *The labelled-campaign classifier on constructed automation.* The
classifier of B14 (B) trained on the first-seed ordinary-prompt campaign with the constructed
accounts removed from the benign side, then applied to the constructed accounts' sessions of ten
or more records. Prediction P67: it flags at least half of the batch-summarisation sessions; no
prediction for the evaluation-harness or agent-loop sessions. (3) *API tiers per client-day.* The
share of client-days whose busiest hour is below the campaign's 2,000 requests, by tier.
Prediction P68: below 10% for the pooled language tiers. (4) *Content calibration on real
accounts only.* Thresholds of the six per-unit content statistics recomputed on the 1,000 real
calibration accounts from the stored per-unit values (the statistics themselves, and their
reference pools, unchanged), and every campaign and control re-scored. Prediction P69: apart
from the benchmark-membership baseline, whose change is on record (B9), no flagged fraction
changes by more than 0.05. The manuscript then reports the replay-calibrated detectors on real
accounts as its primary calibration and the registered thresholds beside them (decision 57).
