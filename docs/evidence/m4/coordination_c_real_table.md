D10 coordination (benign `m3_v1`, 180288 benign identity-days, r = 0.381; 1% threshold 35 neighbours, 0.1% 45; campaign `c_real_v2`, 5 re-schedulings). Flagged = fraction of campaign identity-days over the threshold, median [min, max]; identities = fraction of campaign identities with at least one flagged day.

| Split | n | Shaped | Stagger h | Identity-days | Median density | Flagged 1% | Flagged 0.1% | Identities flagged | AUC | Wall-clock h |
|---|---|---|---|---|---|---|---|---|---|---|
| roundrobin | 10 | no |  | 10 | 9 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.724 | 0.3 |
| roundrobin | 10 | yes |  | 10 | 9 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.724 | 8.0 |
| roundrobin | 100 | no |  | 100 | 99 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.000 | 0.3 |
| roundrobin | 100 | yes |  | 100 | 99 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.000 | 0.8 |
| roundrobin | 1000 | no |  | 1000 | 999 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.000 | 0.3 |
| roundrobin | 1000 | yes |  | 1000 | 999 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 | 1.000 | 0.1 |
| heterogeneous | 100 | yes | 0 | 103 | 1 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.454 | 67.1 |
| heterogeneous | 100 | yes | 1 | 103 | 1 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.454 | 67.5 |
| heterogeneous | 100 | yes | 6 | 104 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.367 | 69.5 |
| heterogeneous | 100 | yes | 24 | 122 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.304 | 76.5 |
| heterogeneous | 100 | yes | 72 | 121 | 0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 | 0.278 | 101.7 |
| heterogeneous | 1000 | yes | 0 | 1000 | 821 | 0.84 [0.81, 0.85] | 0.81 [0.79, 0.85] | 0.84 | 0.946 | 18.5 |
| heterogeneous | 1000 | yes | 1 | 1000 | 824 | 0.84 [0.81, 0.85] | 0.81 [0.79, 0.85] | 0.84 | 0.945 | 18.9 |
| heterogeneous | 1000 | yes | 6 | 1000 | 271 | 0.79 [0.75, 0.85] | 0.79 [0.75, 0.85] | 0.79 | 0.914 | 21.1 |
| heterogeneous | 1000 | yes | 24 | 1011 | 86 | 0.79 [0.75, 0.85] | 0.79 [0.75, 0.85] | 0.79 | 0.886 | 28.7 |
| heterogeneous | 1000 | yes | 72 | 1009 | 45 | 0.25 [0.11, 0.71] | 0.04 [0.00, 0.49] | 0.25 | 0.860 | 74.3 |
