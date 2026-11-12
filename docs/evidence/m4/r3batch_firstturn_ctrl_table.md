R3 batch design (first-turn-matched pools; batch 1500, 1000 null draws, 20 windows per condition, sigma 0.9866). Thresholds: R3 95th 0.0001891; 1% 0.0002879; 0.1% 0.0003643.

| Window | Median MMD² | Flagged at R3 95th | at 1% | at 0.1% |
|---|---|---|---|---|
| benign held-out | 1.236e-05 | 0.00 | 0.00 | 0.00 |
| benign held-out, first turns only (control, pool 2224) | -1.057e-05 | 0.00 | 0.00 | 0.00 |
| control uniform_firstturns (benign prompt file, pure window) | 0.01121 | 1.00 | 1.00 | 1.00 |
| pilot_baseline pure campaign | 0.1092 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.05 | 0.0002282 | 0.75 | 0.15 | 0.05 |
| pilot_baseline mixed, campaign share 0.1 | 0.00109 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.25 | 0.006782 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.5 | 0.0272 | 1.00 | 1.00 | 1.00 |
| c_real_v2 pure campaign | 0.01128 | 1.00 | 1.00 | 1.00 |
| c_real_v2 mixed, campaign share 0.05 | 2.363e-05 | 0.00 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.1 | 0.0001204 | 0.35 | 0.10 | 0.00 |
| c_real_v2 mixed, campaign share 0.25 | 0.0008593 | 1.00 | 1.00 | 1.00 |
| c_real_v2 mixed, campaign share 0.5 | 0.002908 | 1.00 | 1.00 | 1.00 |
