R3 batch design (first-turn-matched pools; request-weighted pools over all replayed identities; batch 1500, 1000 null draws, 20 windows per condition, sigma 0.9835). Thresholds: R3 95th 0.0001947; 1% 0.0003888; 0.1% 0.000649.

| Window | Median MMD² | Flagged at R3 95th | at 1% | at 0.1% |
|---|---|---|---|---|
| benign held-out | -1.798e-05 | 0.00 | 0.00 | 0.00 |
| benign held-out, first turns only (control, pool 2777) | -2.781e-05 | 0.00 | 0.00 | 0.00 |
| control uniform_firstturns (benign prompt file, pure window) | 0.01346 | 1.00 | 1.00 | 1.00 |
| pilot_baseline pure campaign | 0.1131 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.05 | 0.0002816 | 0.95 | 0.30 | 0.00 |
| pilot_baseline mixed, campaign share 0.1 | 0.001211 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.25 | 0.007204 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.5 | 0.02831 | 1.00 | 1.00 | 1.00 |
| c_real_v2 pure campaign | 0.01377 | 1.00 | 1.00 | 1.00 |
| c_real_v2 mixed, campaign share 0.05 | 4.528e-05 | 0.00 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.1 | 0.0001903 | 0.50 | 0.05 | 0.00 |
| c_real_v2 mixed, campaign share 0.25 | 0.001028 | 1.00 | 1.00 | 1.00 |
| c_real_v2 mixed, campaign share 0.5 | 0.003606 | 1.00 | 1.00 | 1.00 |
