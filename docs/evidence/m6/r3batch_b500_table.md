R3 batch design (first-turn-matched pools; batch 500, 1000 null draws, 20 windows per condition, sigma 0.9866). Thresholds: R3 95th 0.0004879; 1% 0.0009535; 0.1% 0.001381.

| Window | Median MMD² | Flagged at R3 95th | at 1% | at 0.1% |
|---|---|---|---|---|
| benign held-out | 4.931e-05 | 0.05 | 0.00 | 0.00 |
| benign held-out, first turns only (control, pool 2224) | -5.711e-05 | 0.00 | 0.00 | 0.00 |
| control uniform_firstturns (benign prompt file, pure window) | 0.01116 | 1.00 | 1.00 | 1.00 |
| pilot_baseline pure campaign | 0.1089 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.05 | 0.0002151 | 0.15 | 0.00 | 0.00 |
| pilot_baseline mixed, campaign share 0.1 | 0.001084 | 1.00 | 0.65 | 0.20 |
| pilot_baseline mixed, campaign share 0.25 | 0.006659 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.5 | 0.02698 | 1.00 | 1.00 | 1.00 |
| c_real_v2 pure campaign | 0.01124 | 1.00 | 1.00 | 1.00 |
| c_real_v2 mixed, campaign share 0.05 | 5.013e-05 | 0.05 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.1 | 0.0001532 | 0.05 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.25 | 0.0008542 | 0.85 | 0.35 | 0.00 |
| c_real_v2 mixed, campaign share 0.5 | 0.002914 | 1.00 | 1.00 | 1.00 |
