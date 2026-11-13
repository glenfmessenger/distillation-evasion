M4 content level (benign `m3_v1`, model `BAAI/bge-base-en-v1.5`, 1061 benign identities at matched n = 30, block session). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
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
| c_real_v2:20 | identity_split_n10 | 50 (50) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001591 | 0.000 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001591 | 1.000 |
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
| control:uniform_firstturns | identity | 1 (1) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5233 | 0.063 |
| control:uniform_firstturns | identity | 1 (1) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001187 | 0.000 |
| control:uniform_firstturns | identity | 1 (1) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001187 | 1.000 |
| control:uniform_firstturns | identity | 1 (1) | C3 (post-hoc) | 0.5678 | 0.00 | 0.00 | yes | 0.5661 | 0.990 |
| control:uniform_firstturns | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.03367 | 0.228 |
| control:uniform_firstturns | block100 | 30 (30) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5147 | 0.046 |
| control:uniform_firstturns | block100 | 30 (30) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001465 | 0.000 |
| control:uniform_firstturns | block100 | 30 (30) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001465 | 1.000 |
| control:uniform_firstturns | block100 | 30 (30) | C3 (post-hoc) | 0.5678 | 0.43 | 0.00 | yes | 0.5654 | 0.987 |
| control:uniform_firstturns | block100 | 30 (30) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | block100 | 30 (30) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.183 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.51 | 0.046 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001398 | 0.000 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001398 | 1.000 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5678 | 0.30 | 0.00 | yes | 0.5652 | 0.988 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.02167 | 0.228 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | C1 | 0.9315 | 0.00 | 0.00 | yes | 0.5077 | 0.057 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | C2 | 0.3142 | 0.00 | 0.00 | yes | 0.001579 | 0.000 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | C2low (post-hoc) | 0.01972 | 1.00 | 1.00 | yes | 0.001579 | 1.000 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | C3 (post-hoc) | 0.5678 | 0.44 | 0.00 | yes | 0.5658 | 0.985 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.144 |
| control:uniform_firstturns | identity_split_n1000 | 5000 (0) | C1 | 0.9315 | n/a | n/a | yes | n/a | n/a |
| control:uniform_firstturns | identity_split_n1000 | 5000 (0) | C2 | 0.3142 | n/a | n/a | yes | n/a | n/a |
| control:uniform_firstturns | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.01972 | n/a | n/a | yes | n/a | n/a |
| control:uniform_firstturns | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5678 | n/a | n/a | yes | n/a | n/a |
| control:uniform_firstturns | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.115 |
