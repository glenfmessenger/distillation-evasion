R3 batch design (first-turn-matched pools; batch 1500, 1000 null draws, 20 windows per condition, sigma 0.9866). Thresholds: R3 95th 0.0001891; 1% 0.0002879; 0.1% 0.0003643.

| Window | Median MMD² | Flagged at R3 95th | at 1% | at 0.1% |
|---|---|---|---|---|
| benign held-out | 1.236e-05 | 0.00 | 0.00 | 0.00 |
| benign held-out, first turns only (control, pool 2224) | -1.057e-05 | 0.00 | 0.00 | 0.00 |
| control uniform_firstturns (benign prompt file, pure window) | 0.01121 | 1.00 | 1.00 | 1.00 |
| pilot_baseline pure campaign | 0.1092 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.01 | 1.063e-05 | 0.00 | 0.00 | 0.00 |
| pilot_baseline mixed, campaign share 0.02 | 2.958e-05 | 0.00 | 0.00 | 0.00 |
| pilot_baseline mixed, campaign share 0.05 | 0.0002737 | 0.85 | 0.30 | 0.05 |
| pilot_baseline mixed, campaign share 0.1 | 0.001075 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.25 | 0.006823 | 1.00 | 1.00 | 1.00 |
| pilot_baseline mixed, campaign share 0.5 | 0.027 | 1.00 | 1.00 | 1.00 |
| c_real_v2 pure campaign | 0.01138 | 1.00 | 1.00 | 1.00 |
| c_real_v2 mixed, campaign share 0.01 | -2.22e-05 | 0.00 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.02 | 9.513e-06 | 0.00 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.05 | 2.7e-05 | 0.10 | 0.00 | 0.00 |
| c_real_v2 mixed, campaign share 0.1 | 0.0001716 | 0.40 | 0.05 | 0.00 |
| c_real_v2 mixed, campaign share 0.25 | 0.0007158 | 1.00 | 1.00 | 1.00 |
| c_real_v2 mixed, campaign share 0.5 | 0.003027 | 1.00 | 1.00 | 1.00 |
| c_instr_v2 pure campaign | 0.04202 | 1.00 | 1.00 | 1.00 |
| c_instr_v2 mixed, campaign share 0.01 | -1.366e-05 | 0.00 | 0.00 | 0.00 |
| c_instr_v2 mixed, campaign share 0.02 | -1.511e-05 | 0.00 | 0.00 | 0.00 |
| c_instr_v2 mixed, campaign share 0.05 | 6.589e-05 | 0.00 | 0.00 | 0.00 |
| c_instr_v2 mixed, campaign share 0.1 | 0.0004077 | 1.00 | 0.85 | 0.80 |
| c_instr_v2 mixed, campaign share 0.25 | 0.002602 | 1.00 | 1.00 | 1.00 |
| c_instr_v2 mixed, campaign share 0.5 | 0.01066 | 1.00 | 1.00 | 1.00 |
