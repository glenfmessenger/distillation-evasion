M4 content level (benign `m3_v1`, model `BAAI/bge-small-en-v1.5`, 1061 benign identities at matched n = 30, block session). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
| c_real_v2:20 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4817 | 0.026 |
| c_real_v2:20 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001903 | 0.000 |
| c_real_v2:20 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001903 | 1.000 |
| c_real_v2:20 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5219 | 0.987 |
| c_real_v2:20 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0305 | 0.228 |
| c_real_v2:20 | block100 | 20 (20) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4717 | 0.025 |
| c_real_v2:20 | block100 | 20 (20) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.00193 | 0.000 |
| c_real_v2:20 | block100 | 20 (20) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.00193 | 1.000 |
| c_real_v2:20 | block100 | 20 (20) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5179 | 0.977 |
| c_real_v2:20 | block100 | 20 (20) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.199 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4736 | 0.026 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001511 | 0.000 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001511 | 1.000 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5158 | 0.978 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.025 | 0.228 |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.134 |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| c_real_v2:20 | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.115 |
| control:no_robots | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.5711 | 0.133 |
| control:no_robots | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.01708 | 0.003 |
| control:no_robots | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 0.00 | yes | 0.01708 | 0.997 |
| control:no_robots | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5178 | 0.981 |
| control:no_robots | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:no_robots | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.001667 | 0.228 |
| control:no_robots | block100 | 30 (30) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.5649 | 0.123 |
| control:no_robots | block100 | 30 (30) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.01848 | 0.006 |
| control:no_robots | block100 | 30 (30) | C2low (post-hoc) | 0.02108 | 0.87 | 0.20 | yes | 0.01848 | 0.994 |
| control:no_robots | block100 | 30 (30) | C3 (post-hoc) | 0.5314 | 0.07 | 0.00 | yes | 0.5188 | 0.980 |
| control:no_robots | block100 | 30 (30) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:no_robots | block100 | 30 (30) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| control:no_robots | identity_split_n10 | 50 (50) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.564 | 0.120 |
| control:no_robots | identity_split_n10 | 50 (50) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.01828 | 0.005 |
| control:no_robots | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02108 | 0.94 | 0.18 | yes | 0.01828 | 0.995 |
| control:no_robots | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5314 | 0.06 | 0.00 | yes | 0.518 | 0.981 |
| control:no_robots | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:no_robots | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| control:no_robots | identity_split_n100 | 500 (500) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.5683 | 0.141 |
| control:no_robots | identity_split_n100 | 500 (500) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.01803 | 0.009 |
| control:no_robots | identity_split_n100 | 500 (500) | C2low (post-hoc) | 0.02108 | 0.77 | 0.34 | yes | 0.01803 | 0.991 |
| control:no_robots | identity_split_n100 | 500 (500) | C3 (post-hoc) | 0.5314 | 0.25 | 0.00 | yes | 0.52 | 0.972 |
| control:no_robots | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:no_robots | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| control:no_robots | identity_split_n1000 | 5000 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| control:no_robots | identity_split_n1000 | 5000 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| control:no_robots | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| control:no_robots | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| control:no_robots | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:no_robots | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
