Pattern statistics on comparable sessions: 1170 benign sessions of at least 10 records from 924 accounts; campaign sessions cut to benign sizes: {"pilot_baseline": 90, "c_real_v2:20": 90, "c_real_v2_s1": 90, "c_instr_v2": 90}. P60 fails; stop rule not triggered.

(i) Two-sided thresholds at 1% total (in sample). Flagged fraction, either side (low side alone).
| Statistic | Low | High | Benign exceed | pilot_baseline | c_real_v2:20 | c_real_v2_s1 | c_instr_v2 |
|---|---|---|---|---|---|---|---|
| D3 | 0.243 | 2.88 | 10 | 0.03 (0.02); AUC 0.54 | 0.02 (0.02); AUC 0.49 | 0.00 (0.00); AUC 0.49 | 0.01 (0.01); AUC 0.50 |
| D4 | 0.105 | 0.904 | 10 | 0.00 (0.00); AUC 0.73 | 0.08 (0.08); AUC 0.11 | 0.02 (0.02); AUC 0.09 | 0.00 (0.00); AUC 0.25 |
| D5nt | 0.219 | 0.959 | 10 | 0.00 (0.00); AUC 0.96 | 0.00 (0.00); AUC 0.57 | 0.00 (0.00); AUC 0.57 | 0.00 (0.00); AUC 0.70 |
| D6 | 0.132 | 0.866 | 10 | 0.00 (0.00); AUC 0.65 | 0.00 (0.00); AUC 0.70 | 0.00 (0.00); AUC 0.69 | 0.00 (0.00); AUC 0.81 |
| D7 | 0 | 0.894 | 5 (below res.) | 0.02 (0.00); AUC 0.06 | 0.00 (0.00); AUC 0.01 | 0.00 (0.00); AUC 0.01 | 0.00 (0.00); AUC 0.01 |
| D9 | 0.0286 | 1 | 5 (below res.) | 0.00 (0.00); AUC 0.92 | 0.00 (0.00); AUC 0.92 | 0.00 (0.00); AUC 0.92 | 0.00 (0.00); AUC 0.92 |

(ii) Benign-fit joint score and (iii) upper bound, held out over 20 account splits: median flagged [min, max].
| Score | Held-out FPR mean [min, max] | pilot_baseline | c_real_v2:20 | c_real_v2_s1 | c_instr_v2 |
|---|---|---|---|---|---|
| joint (benign only) | 0.0149 [0.0017, 0.0311] | 0.04 [0.03, 0.04] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| upper bound, trained on pilot_baseline | 0.0121 [0.0034, 0.0226] | 1.00 [0.87, 1.00] | 0.01 [0.00, 0.06] | 0.00 [0.00, 0.01] | 0.08 [0.01, 0.18] |
| upper bound, trained on c_real_v2:20 | 0.0138 [0.0017, 0.0224] | 0.03 [0.01, 0.09] | 0.86 [0.77, 0.94] | 0.89 [0.77, 0.97] | 0.52 [0.34, 0.67] |
| upper bound, trained on c_real_v2_s1 | 0.0142 [0.0017, 0.0237] | 0.01 [0.00, 0.02] | 0.84 [0.70, 0.92] | 0.89 [0.80, 0.94] | 0.43 [0.31, 0.58] |
| upper bound, trained on c_instr_v2 | 0.0119 [0.0017, 0.0228] | 0.84 [0.80, 0.92] | 0.53 [0.12, 0.79] | 0.53 [0.14, 0.79] | 0.58 [0.34, 0.83] |
