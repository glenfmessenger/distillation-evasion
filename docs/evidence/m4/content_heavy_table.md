M4 content level (benign `heavy_v1`, model `BAAI/bge-small-en-v1.5`, 3261 benign identities at matched n = 30, block session). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
| pilot_baseline | identity | 1 (1) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.6741 | 0.389 |
| pilot_baseline | identity | 1 (1) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.08152 | 0.471 |
| pilot_baseline | identity | 1 (1) | C2low (post-hoc) | 0.02157 | 0.00 | 0.00 | yes | 0.08152 | 0.529 |
| pilot_baseline | identity | 1 (1) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.405 | 0.600 |
| pilot_baseline | identity | 1 (1) | B1 | 0 | 1.00 | 1.00 | yes | 0.92 | 1.000 |
| pilot_baseline | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.965 |
| pilot_baseline | block100 | 20 (20) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.6905 | 0.438 |
| pilot_baseline | block100 | 20 (20) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.08262 | 0.473 |
| pilot_baseline | block100 | 20 (20) | C2low (post-hoc) | 0.02157 | 0.00 | 0.00 | yes | 0.08262 | 0.527 |
| pilot_baseline | block100 | 20 (20) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.4076 | 0.613 |
| pilot_baseline | block100 | 20 (20) | B1 | 0 | 1.00 | 1.00 | yes | 0.915 | 1.000 |
| pilot_baseline | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.965 |
| pilot_baseline | identity_split_n10 | 50 (50) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.694 | 0.448 |
| pilot_baseline | identity_split_n10 | 50 (50) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.08289 | 0.477 |
| pilot_baseline | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02157 | 0.00 | 0.00 | yes | 0.08289 | 0.523 |
| pilot_baseline | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.4081 | 0.616 |
| pilot_baseline | identity_split_n10 | 50 (50) | B1 | 0 | 1.00 | 1.00 | yes | 0.9275 | 1.000 |
| pilot_baseline | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.965 |
| pilot_baseline | identity_split_n100 | 500 (0) | C1 | 0.9275 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C2 | 0.2895 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.02157 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5338 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (500) | B1 | 0 | 1.00 | 1.00 | yes | 0.95 | 1.000 |
| pilot_baseline | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.951 |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C1 | 0.9275 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C2 | 0.2895 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02157 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5338 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (5000) | B1 | 0 | 0.99 | 0.99 | yes | 1 | 0.996 |
| pilot_baseline | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.622 |
| c_real_v2:20 | identity | 1 (1) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4421 | 0.001 |
| c_real_v2:20 | identity | 1 (1) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002492 | 0.000 |
| c_real_v2:20 | identity | 1 (1) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002492 | 1.000 |
| c_real_v2:20 | identity | 1 (1) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5224 | 0.985 |
| c_real_v2:20 | identity | 1 (1) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.496 |
| c_real_v2:20 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0305 | 0.202 |
| c_real_v2:20 | block100 | 20 (20) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4315 | 0.001 |
| c_real_v2:20 | block100 | 20 (20) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002153 | 0.000 |
| c_real_v2:20 | block100 | 20 (20) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002153 | 1.000 |
| c_real_v2:20 | block100 | 20 (20) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5179 | 0.981 |
| c_real_v2:20 | block100 | 20 (20) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.496 |
| c_real_v2:20 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.173 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4404 | 0.002 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002291 | 0.000 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002291 | 1.000 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5154 | 0.981 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.496 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.025 | 0.194 |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C1 | 0.9275 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C2 | 0.2895 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.02157 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5338 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (500) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.496 |
| c_real_v2:20 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.111 |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C1 | 0.9275 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C2 | 0.2895 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02157 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5338 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (5000) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.496 |
| c_real_v2:20 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.092 |
| c_real_v2 | identity | 1 (1) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4428 | 0.001 |
| c_real_v2 | identity | 1 (1) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.001201 | 0.000 |
| c_real_v2 | identity | 1 (1) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.001201 | 1.000 |
| c_real_v2 | identity | 1 (1) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5112 | 0.978 |
| c_real_v2 | identity | 1 (1) | B1 | 0 | 1.00 | 0.00 | yes | 0.000125 | 0.993 |
| c_real_v2 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0405 | 0.229 |
| c_real_v2 | block100 | 80 (80) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.436 | 0.002 |
| c_real_v2 | block100 | 80 (80) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002262 | 0.000 |
| c_real_v2 | block100 | 80 (80) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002262 | 1.000 |
| c_real_v2 | block100 | 80 (80) | C3 (post-hoc) | 0.5338 | 0.01 | 0.00 | yes | 0.5154 | 0.981 |
| c_real_v2 | block100 | 80 (80) | B1 | 0 | 0.01 | 0.00 | yes | 0 | 0.503 |
| c_real_v2 | block100 | 80 (80) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.173 |
| c_real_v2 | identity_split_n10 | 50 (50) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4399 | 0.001 |
| c_real_v2 | identity_split_n10 | 50 (50) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002452 | 0.000 |
| c_real_v2 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002452 | 1.000 |
| c_real_v2 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5165 | 0.982 |
| c_real_v2 | identity_split_n10 | 50 (50) | B1 | 0 | 0.10 | 0.00 | yes | 0 | 0.546 |
| c_real_v2 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.025 | 0.197 |
| c_real_v2 | identity_split_n100 | 500 (500) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4387 | 0.002 |
| c_real_v2 | identity_split_n100 | 500 (500) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002471 | 0.000 |
| c_real_v2 | identity_split_n100 | 500 (500) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002471 | 1.000 |
| c_real_v2 | identity_split_n100 | 500 (500) | C3 (post-hoc) | 0.5338 | 0.02 | 0.00 | yes | 0.5167 | 0.980 |
| c_real_v2 | identity_split_n100 | 500 (500) | B1 | 0 | 0.01 | 0.00 | yes | 0 | 0.501 |
| c_real_v2 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0.025 | 0.165 |
| c_real_v2 | identity_split_n1000 | 5000 (0) | C1 | 0.9275 | n/a | n/a | yes | n/a | n/a |
| c_real_v2 | identity_split_n1000 | 5000 (0) | C2 | 0.2895 | n/a | n/a | yes | n/a | n/a |
| c_real_v2 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02157 | n/a | n/a | yes | n/a | n/a |
| c_real_v2 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5338 | n/a | n/a | yes | n/a | n/a |
| c_real_v2 | identity_split_n1000 | 5000 (5000) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.497 |
| c_real_v2 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.100 |
| c_real_v2_s1 | identity | 1 (1) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4534 | 0.002 |
| c_real_v2_s1 | identity | 1 (1) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002785 | 0.000 |
| c_real_v2_s1 | identity | 1 (1) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002785 | 1.000 |
| c_real_v2_s1 | identity | 1 (1) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5184 | 0.983 |
| c_real_v2_s1 | identity | 1 (1) | B1 | 0 | 1.00 | 0.00 | yes | 0.001 | 0.993 |
| c_real_v2_s1 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.029 | 0.199 |
| c_real_v2_s1 | block100 | 20 (20) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.441 | 0.002 |
| c_real_v2_s1 | block100 | 20 (20) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002374 | 0.000 |
| c_real_v2_s1 | block100 | 20 (20) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002374 | 1.000 |
| c_real_v2_s1 | block100 | 20 (20) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5165 | 0.977 |
| c_real_v2_s1 | block100 | 20 (20) | B1 | 0 | 0.10 | 0.00 | yes | 0 | 0.546 |
| c_real_v2_s1 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.03 | 0.179 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4393 | 0.001 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002332 | 0.000 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002332 | 1.000 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.516 | 0.979 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | B1 | 0 | 0.20 | 0.00 | yes | 0 | 0.596 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.0275 | 0.195 |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C1 | 0.9275 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C2 | 0.2895 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.02157 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5338 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (500) | B1 | 0 | 0.02 | 0.00 | yes | 0 | 0.507 |
| c_real_v2_s1 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.116 |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C1 | 0.9275 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C2 | 0.2895 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02157 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5338 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (5000) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.497 |
| c_real_v2_s1 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.091 |
