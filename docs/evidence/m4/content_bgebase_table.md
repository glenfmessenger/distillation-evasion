M4 content level (benign `m3_v1`, model `BAAI/bge-base-en-v1.5`, 1061 benign identities at matched n = 30, block session). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
| pilot_baseline | identity | 1 (1) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.7582 | 0.645 |
| pilot_baseline | identity | 1 (1) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.07127 | 0.434 |
| pilot_baseline | identity | 1 (1) | C2low (post-hoc) | 0.01972 | 0.00 | 0.00 | yes | 0.07127 | 0.566 |
| pilot_baseline | identity | 1 (1) | C3 (post-hoc) | 0.5678 | 0.00 | 0.00 | yes | 0.422 | 0.471 |
| pilot_baseline | identity | 1 (1) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.92 | 1.000 |
| pilot_baseline | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | block100 | 20 (20) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.7512 | 0.619 |
| pilot_baseline | block100 | 20 (20) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.07564 | 0.467 |
| pilot_baseline | block100 | 20 (20) | C2low (post-hoc) | 0.01972 | 0.00 | 0.00 | yes | 0.07564 | 0.533 |
| pilot_baseline | block100 | 20 (20) | C3 (post-hoc) | 0.5678 | 0.00 | 0.00 | yes | 0.4233 | 0.480 |
| pilot_baseline | block100 | 20 (20) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.915 | 1.000 |
| pilot_baseline | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | identity_split_n10 | 50 (50) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.7531 | 0.624 |
| pilot_baseline | identity_split_n10 | 50 (50) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.07536 | 0.464 |
| pilot_baseline | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.01972 | 0.00 | 0.00 | yes | 0.07536 | 0.536 |
| pilot_baseline | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5678 | 0.00 | 0.00 | yes | 0.4238 | 0.479 |
| pilot_baseline | identity_split_n10 | 50 (50) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.9275 | 1.000 |
| pilot_baseline | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | identity_split_n100 | 500 (0) | C1 | 0.9315 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C2 | 0.3142 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.01972 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5678 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (500) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.95 | 1.000 |
| pilot_baseline | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.949 |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C1 | 0.9315 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C2 | 0.3142 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.01972 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5678 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.99 | 0.99 | yes | 1 | 0.996 |
| pilot_baseline | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.630 |
| c_real_v2:20 | identity | 1 (1) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5199 | 0.060 |
| c_real_v2:20 | identity | 1 (1) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001727 | 0.000 |
| c_real_v2:20 | identity | 1 (1) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001727 | 1.000 |
| c_real_v2:20 | identity | 1 (1) | C3 (post-hoc) | 0.5678 | 0.00 | 0.00 | yes | 0.5676 | 0.990 |
| c_real_v2:20 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0305 | 0.228 |
| c_real_v2:20 | block100 | 20 (20) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5144 | 0.053 |
| c_real_v2:20 | block100 | 20 (20) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001828 | 0.000 |
| c_real_v2:20 | block100 | 20 (20) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001828 | 1.000 |
| c_real_v2:20 | block100 | 20 (20) | C3 (post-hoc) | 0.5678 | 0.40 | 0.00 | yes | 0.5623 | 0.986 |
| c_real_v2:20 | block100 | 20 (20) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.199 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5165 | 0.052 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001592 | 0.000 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001592 | 1.000 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5678 | 0.18 | 0.00 | yes | 0.5639 | 0.987 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.025 | 0.228 |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C1 | 0.9315 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C2 | 0.3142 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.01972 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5678 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.134 |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C1 | 0.9315 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C2 | 0.3142 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.01972 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5678 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.115 |
| c_real_v2 | identity | 1 (1) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.4924 | 0.027 |
| c_real_v2 | identity | 1 (1) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001424 | 0.000 |
| c_real_v2 | identity | 1 (1) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001424 | 1.000 |
| c_real_v2 | identity | 1 (1) | C3 (post-hoc) | 0.5678 | 0.00 | 0.00 | yes | 0.5673 | 0.990 |
| c_real_v2 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.000125 | 0.979 |
| c_real_v2 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0405 | 0.228 |
| c_real_v2 | block100 | 80 (80) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5064 | 0.045 |
| c_real_v2 | block100 | 80 (80) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.00152 | 0.000 |
| c_real_v2 | block100 | 80 (80) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.00152 | 1.000 |
| c_real_v2 | block100 | 80 (80) | C3 (post-hoc) | 0.5678 | 0.34 | 0.00 | yes | 0.563 | 0.987 |
| c_real_v2 | block100 | 80 (80) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.496 |
| c_real_v2 | block100 | 80 (80) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.199 |
| c_real_v2 | identity_split_n10 | 50 (50) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5091 | 0.045 |
| c_real_v2 | identity_split_n10 | 50 (50) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001474 | 0.000 |
| c_real_v2 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001474 | 1.000 |
| c_real_v2 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5678 | 0.24 | 0.00 | yes | 0.5654 | 0.988 |
| c_real_v2 | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.539 |
| c_real_v2 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.025 | 0.228 |
| c_real_v2 | identity_split_n100 | 500 (500) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5044 | 0.043 |
| c_real_v2 | identity_split_n100 | 500 (500) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.00149 | 0.000 |
| c_real_v2 | identity_split_n100 | 500 (500) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.00149 | 1.000 |
| c_real_v2 | identity_split_n100 | 500 (500) | C3 (post-hoc) | 0.5678 | 0.38 | 0.00 | yes | 0.5649 | 0.987 |
| c_real_v2 | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.495 |
| c_real_v2 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0.025 | 0.191 |
| c_real_v2 | identity_split_n1000 | 5000 (0) | C1 | 0.9315 | n/a | n/a | yes | n/a | n/a |
| c_real_v2 | identity_split_n1000 | 5000 (0) | C2 | 0.3142 | n/a | n/a | yes | n/a | n/a |
| c_real_v2 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.01972 | n/a | n/a | yes | n/a | n/a |
| c_real_v2 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5678 | n/a | n/a | yes | n/a | n/a |
| c_real_v2 | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.123 |
| c_real_v2_s1 | identity | 1 (1) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.4937 | 0.028 |
| c_real_v2_s1 | identity | 1 (1) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001529 | 0.000 |
| c_real_v2_s1 | identity | 1 (1) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001529 | 1.000 |
| c_real_v2_s1 | identity | 1 (1) | C3 (post-hoc) | 0.5678 | 0.00 | 0.00 | yes | 0.5667 | 0.990 |
| c_real_v2_s1 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.001 | 0.979 |
| c_real_v2_s1 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.029 | 0.228 |
| c_real_v2_s1 | block100 | 20 (20) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5061 | 0.047 |
| c_real_v2_s1 | block100 | 20 (20) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001597 | 0.000 |
| c_real_v2_s1 | block100 | 20 (20) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001597 | 1.000 |
| c_real_v2_s1 | block100 | 20 (20) | C3 (post-hoc) | 0.5678 | 0.30 | 0.00 | yes | 0.5629 | 0.986 |
| c_real_v2_s1 | block100 | 20 (20) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.539 |
| c_real_v2_s1 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.03 | 0.207 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5152 | 0.051 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001574 | 0.000 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001574 | 1.000 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5678 | 0.22 | 0.00 | yes | 0.564 | 0.986 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.588 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.0275 | 0.228 |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C1 | 0.9315 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C2 | 0.3142 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.01972 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5678 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.02 | 0.00 | yes | 0 | 0.500 |
| c_real_v2_s1 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.139 |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C1 | 0.9315 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C2 | 0.3142 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.01972 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5678 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.491 |
| c_real_v2_s1 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
