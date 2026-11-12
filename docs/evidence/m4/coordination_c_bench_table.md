D10 coordination (benign `m3_v1`, 180288 benign identity-days, r = 0.381; 1% threshold 35 neighbours, 0.1% 45; campaign `pilot_baseline`, 5 re-schedulings). Flagged = fraction of campaign identity-days over the threshold, median [min, max]; identities = fraction of campaign identities with at least one flagged day.

| Split | n | Shaped | Stagger h | Identity-days | Median density | Flagged 1% | Flagged 0.1% | Identities flagged | AUC | Wall-clock h |
|---|---|---|---|---|---|---|---|---|---|---|
| roundrobin | 10 | no |  | 10 | 4 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.663 | 1.2 |
| roundrobin | 10 | yes |  | 10 | 4 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.663 | 8.0 |
| roundrobin | 100 | no |  | 100 | 94 | 0.95 [0.95, 0.95] | 0.95 [0.95, 0.95] | 0.95 | 0.983 | 1.2 |
| roundrobin | 100 | yes |  | 100 | 94 | 0.95 [0.95, 0.95] | 0.95 [0.95, 0.95] | 0.95 | 0.983 | 0.8 |
| roundrobin | 1000 | no |  | 1000 | 994 | 0.99 [0.99, 0.99] | 0.99 [0.99, 0.99] | 0.99 | 0.999 | 1.2 |
| roundrobin | 1000 | yes |  | 1000 | 994 | 0.99 [0.99, 0.99] | 0.99 [0.99, 0.99] | 0.99 | 0.999 | 0.1 |
| heterogeneous | 100 | yes | 0 | 104 | 1 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.470 | 67.1 |
| heterogeneous | 100 | yes | 1 | 105 | 1 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.469 | 67.4 |
| heterogeneous | 100 | yes | 6 | 106 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.360 | 68.9 |
| heterogeneous | 100 | yes | 24 | 116 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.302 | 74.4 |
| heterogeneous | 100 | yes | 72 | 121 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.283 | 99.6 |
| heterogeneous | 1000 | yes | 0 | 1001 | 822 | 0.85 [0.81, 0.85] | 0.81 [0.79, 0.85] | 0.85 | 0.948 | 23.2 |
| heterogeneous | 1000 | yes | 1 | 1001 | 825 | 0.85 [0.81, 0.85] | 0.81 [0.79, 0.85] | 0.85 | 0.947 | 24.1 |
| heterogeneous | 1000 | yes | 6 | 1001 | 274 | 0.79 [0.75, 0.85] | 0.79 [0.75, 0.85] | 0.79 | 0.913 | 28.7 |
| heterogeneous | 1000 | yes | 24 | 1013 | 87 | 0.79 [0.75, 0.85] | 0.79 [0.75, 0.85] | 0.80 | 0.883 | 35.2 |
| heterogeneous | 1000 | yes | 72 | 1007 | 46 | 0.25 [0.07, 0.71] | 0.03 [0.00, 0.51] | 0.25 | 0.860 | 74.3 |
