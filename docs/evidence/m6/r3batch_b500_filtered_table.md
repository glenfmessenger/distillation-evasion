R3 batch design (first-turn-matched pools; batch 500, 1000 null draws, 20 windows per condition, sigma 1.0299). Thresholds: R3 95th 0.0003122; 1% 0.0005026; 0.1% 0.0006833.

| Window | Median MMD² | Flagged at R3 95th | at 1% | at 0.1% |
|---|---|---|---|---|
| benign held-out | -1.104e-05 | 0.00 | 0.00 | 0.00 |
| benign held-out, first turns only (control, pool 849) | 1.586e-05 | 0.00 | 0.00 | 0.00 |
| control uniform_firstturns (benign prompt file, pure window) | 0.00283 | 1.00 | 1.00 | 1.00 |
| pilot_baseline pure campaign | 0.09361 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.05 | 0.0002947 | 0.45 | 0.05 | 0.00 |
| pilot_baseline mixed, campaign share 0.1 | 0.001201 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.25 | 0.006361 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.5 | 0.02391 | 1.00 | 1.00 | 1.00 |
| c_real_v2 pure campaign | 0.002649 | 1.00 | 1.00 | 1.00 |
| c_real_v2 mixed, campaign share 0.05 | -2.035e-05 | 0.00 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.1 | 2.76e-05 | 0.00 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.25 | 0.0002048 | 0.10 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.5 | 0.0007326 | 1.00 | 1.00 | 0.65 |
