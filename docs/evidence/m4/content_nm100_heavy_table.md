M4 content level (benign `heavy_v1`, model `BAAI/bge-small-en-v1.5`, 366 benign identities at matched n = 100, block session). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
| pilot_baseline | identity | 1 (1) | C1 | 0.9435 | 0.00 | 0.00 | yes | 0.656 | 0.456 |
| pilot_baseline | identity | 1 (1) | C2 | 0.3018 | 0.00 | 0.00 | yes | 0.08653 | 0.505 |
| pilot_baseline | identity | 1 (1) | C2low (post-hoc) | 0.02246 | 0.00 | 0.00 | yes | 0.08653 | 0.495 |
| pilot_baseline | identity | 1 (1) | C3 (post-hoc) | 0.527 | 0.00 | 0.00 | yes | 0.4078 | 0.585 |
| pilot_baseline | identity | 1 (1) | B1 | 0 | 1.00 | 1.00 | yes | 0.92 | 1.000 |
| pilot_baseline | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.975 |
| pilot_baseline | block100 | 20 (20) | C1 | 0.9435 | 0.00 | 0.00 | yes | 0.6474 | 0.441 |
| pilot_baseline | block100 | 20 (20) | C2 | 0.3018 | 0.00 | 0.00 | yes | 0.085 | 0.497 |
| pilot_baseline | block100 | 20 (20) | C2low (post-hoc) | 0.02246 | 0.00 | 0.00 | yes | 0.085 | 0.503 |
| pilot_baseline | block100 | 20 (20) | C3 (post-hoc) | 0.527 | 0.00 | 0.00 | yes | 0.4079 | 0.585 |
| pilot_baseline | block100 | 20 (20) | B1 | 0 | 1.00 | 1.00 | yes | 0.915 | 1.000 |
| pilot_baseline | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.975 |
| c_real_v2:20 | identity | 1 (1) | C1 | 0.9435 | 0.00 | 0.00 | yes | 0.3068 | 0.000 |
| c_real_v2:20 | identity | 1 (1) | C2 | 0.3018 | 0.00 | 0.00 | yes | 0.00144 | 0.000 |
| c_real_v2:20 | identity | 1 (1) | C2low (post-hoc) | 0.02246 | 1.00 | 1.00 | yes | 0.00144 | 1.000 |
| c_real_v2:20 | identity | 1 (1) | C3 (post-hoc) | 0.527 | 0.00 | 0.00 | yes | 0.5146 | 0.989 |
| c_real_v2:20 | identity | 1 (1) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.499 |
| c_real_v2:20 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0305 | 0.148 |
| c_real_v2:20 | block100 | 20 (20) | C1 | 0.9435 | 0.00 | 0.00 | yes | 0.3117 | 0.001 |
| c_real_v2:20 | block100 | 20 (20) | C2 | 0.3018 | 0.00 | 0.00 | yes | 0.001413 | 0.000 |
| c_real_v2:20 | block100 | 20 (20) | C2low (post-hoc) | 0.02246 | 1.00 | 1.00 | yes | 0.001413 | 1.000 |
| c_real_v2:20 | block100 | 20 (20) | C3 (post-hoc) | 0.527 | 0.00 | 0.00 | yes | 0.517 | 0.988 |
| c_real_v2:20 | block100 | 20 (20) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.499 |
| c_real_v2:20 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.114 |
| c_real_v2_s1 | identity | 1 (1) | C1 | 0.9435 | 0.00 | 0.00 | yes | 0.3393 | 0.000 |
| c_real_v2_s1 | identity | 1 (1) | C2 | 0.3018 | 0.00 | 0.00 | yes | 0.001324 | 0.000 |
| c_real_v2_s1 | identity | 1 (1) | C2low (post-hoc) | 0.02246 | 1.00 | 1.00 | yes | 0.001324 | 1.000 |
| c_real_v2_s1 | identity | 1 (1) | C3 (post-hoc) | 0.527 | 0.00 | 0.00 | yes | 0.5168 | 0.989 |
| c_real_v2_s1 | identity | 1 (1) | B1 | 0 | 1.00 | 0.00 | yes | 0.001 | 0.997 |
| c_real_v2_s1 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.029 | 0.145 |
| c_real_v2_s1 | block100 | 20 (20) | C1 | 0.9435 | 0.00 | 0.00 | yes | 0.3394 | 0.002 |
| c_real_v2_s1 | block100 | 20 (20) | C2 | 0.3018 | 0.00 | 0.00 | yes | 0.001294 | 0.000 |
| c_real_v2_s1 | block100 | 20 (20) | C2low (post-hoc) | 0.02246 | 1.00 | 1.00 | yes | 0.001294 | 1.000 |
| c_real_v2_s1 | block100 | 20 (20) | C3 (post-hoc) | 0.527 | 0.05 | 0.00 | yes | 0.5153 | 0.987 |
| c_real_v2_s1 | block100 | 20 (20) | B1 | 0 | 0.10 | 0.00 | yes | 0 | 0.548 |
| c_real_v2_s1 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.03 | 0.122 |
