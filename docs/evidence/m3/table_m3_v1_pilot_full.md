M3 detector table (benign `m3_v1`, campaign `pilot_baseline`). Per-cell; nothing pooled. Benign replay records 49663 (in flight excluded: 0); campaign records 1995 (in flight excluded: 0).

| Detector | Grain | Benign source | Benign scoreable | Budget | Threshold | Benign exceed | Below resolution | Campaign units | Flagged | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | identity | timeline | 118465 | 1.0% | 26 | 1092 | no | 1/1 | 1.00 | 1642 | 1.000 |
| D1 | identity | timeline | 118465 | 0.1% | 57 | 115 | no | 1/1 | 1.00 | 1642 | 1.000 |
| D1 | identity (split view) | timeline | 118465 | 1.0% | 26 | 1092 | no | 20/20 | 1.00 | 100 | 1.000 |
| D1 | identity (split view) | timeline | 118465 | 0.1% | 57 | 115 | no | 20/20 | 1.00 | 100 | 1.000 |
| D2 | identity | timeline | 118465 | 1.0% | 48 | 108 | no | 1/1 | 1.00 | 394.3 | 1.000 |
| D2 | identity | timeline | 118465 | 0.1% | 48 | 108 | no | 1/1 | 1.00 | 394.3 | 1.000 |
| D2 | identity (split view) | timeline | 118465 | 1.0% | 48 | 108 | no | 20/20 | 0.00 | 24 | 0.595 |
| D2 | identity (split view) | timeline | 118465 | 0.1% | 48 | 108 | no | 20/20 | 0.00 | 24 | 0.595 |
| D3 | session | timeline | 95498 | 1.0% | 0.02259 | 954 | no | 20/20 | 0.00 | 0.9995 | 0.163 |
| D3 | session | timeline | 95498 | 0.1% | 0 | 0 | yes | 20/20 | 0.00 | 0.9995 | 0.163 |
| D4 | session | replay | 1170 | 1.0% | 0.8701 | 11 | no | 20/20 | 0.00 | 0.5016 | 0.681 |
| D4 | session | replay | 1170 | 0.1% | 0.9514 | 1 | yes | 20/20 | 0.00 | 0.5016 | 0.681 |
| D5 | session | replay | 10486 | 1.0% | 0.9909 | 104 | no | 20/20 | 0.00 | 0.8605 | 0.925 |
| D5 | session | replay | 10486 | 0.1% | 0.9999 | 0 | yes | 20/20 | 0.00 | 0.8605 | 0.925 |
| D6 | session | replay | 1170 | 1.0% | 0.8403 | 11 | no | 20/20 | 0.00 | 0.4766 | 0.559 |
| D6 | session | replay | 1170 | 0.1% | 0.9284 | 1 | yes | 20/20 | 0.00 | 0.4766 | 0.559 |
| D7 | session | replay | 10486 | 1.0% | 0.8085 | 104 | no | 20/20 | 0.00 | 0.0009639 | 0.345 |
| D7 | session | replay | 10486 | 0.1% | 0.9757 | 10 | no | 20/20 | 0.00 | 0.0009639 | 0.345 |
| D8 | identity | replay | 1020 | 1.0% | 0.811 | 10 | no | 1/1 | 0.00 | 0.6987 | 0.944 |
| D8 | identity | replay | 1020 | 0.1% | 0.8911 | 1 | yes | 1/1 | 0.00 | 0.6987 | 0.944 |
| D8 | identity (split view) | replay | 1020 | 1.0% | 0.811 | 10 | no | 20/20 | 0.00 | 0.6923 | 0.930 |
| D8 | identity (split view) | replay | 1020 | 0.1% | 0.8911 | 1 | yes | 20/20 | 0.00 | 0.6923 | 0.930 |
| D8b | identity | replay | 1020 | 1.0% | 3 | 1 | yes | 1/1 | 0.00 | 12.5 | 0.623 |
| D8b | identity | replay | 1020 | 0.1% | 3 | 1 | yes | 1/1 | 0.00 | 12.5 | 0.623 |
| D8b | identity (split view) | replay | 1020 | 1.0% | 3 | 1 | yes | 20/20 | 0.00 | 13.5 | 0.552 |
| D8b | identity (split view) | replay | 1020 | 0.1% | 3 | 1 | yes | 20/20 | 0.00 | 13.5 | 0.552 |
| D9 | session | timeline | 263826 | 1.0% | 1 | 0 | yes | 20/20 | 0.00 | 1 | 0.751 |
| D9 | session | timeline | 263826 | 0.1% | 1 | 0 | yes | 20/20 | 0.00 | 1 | 0.751 |

TOO-GOOD STOP RULE: AUC >= 0.95 for [('D1', 'campaign', 0.9999915586882201), ('D1', 'campaign_split', 0.9998512218798802), ('D2', 'campaign', 1.0)]
