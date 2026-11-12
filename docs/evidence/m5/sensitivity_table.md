Benign volume sensitivity (B6 item 4): D10 and D11 recalibrated on a fraction f of benign accounts; 50 placements per cell; medians over draws.

| f | Accounts | D10 thr | D11 thr | Radius | 10 acc: D11 median, P(any D11) | 100 acc: D10 median, D11 median, P(any D10) |
|---|---|---|---|---|---|---|
| 0.1 | 11846 | 13 | 3 | 1.357 | 1.00, 1.00 | 1.00, 1.00, 1.00 |
| 0.25 | 29616 | 19 | 5 | 0.810 | 1.00, 1.00 | 1.00, 1.00, 1.00 |
| 0.5 | 59232 | 25 | 8 | 0.550 | 1.00, 1.00 | 1.00, 1.00, 1.00 |
| 1 | 118465 | 35 | 15 | 0.381 | 0.00, 0.10 | 1.00, 1.00, 1.00 |

P33: {"thr_d11_median_at_0.25": 5.0, "ten_account_p_any_d11_median_at_0.25": 1.0, "holds": true}

D10 scale sensitivity (B6 item 6): MAD per feature log_requests 0.405, log_sessions 0, session_len_median 1, log_gap_median 2.18, log_span 3.76, start_sin 0.665, start_cos 0.655, single_turn_frac 0.143.
| Variant | Features | Radius | Threshold | Exceed | Round-robin 100 | Organisation | Batch job | Eval fleet | P36 |
|---|---|---|---|---|---|---|---|---|---|
| registered | 8 | 0.381 | 35 | 1543 | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.01] | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | yes |
| drop_constant | 7 | 0.381 | 35 | 1535 | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | yes |
| floor_1 | 8 | 0.298 | 40 | 1726 | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | yes |
| iqr | 8 | 0.231 | 33 | 1631 | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | yes |
