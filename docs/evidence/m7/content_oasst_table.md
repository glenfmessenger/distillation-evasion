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
| c_instr_v2 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4959 | 0.038 |
| c_instr_v2 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.02445 | 0.029 |
| c_instr_v2 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 0.00 | 0.00 | yes | 0.02445 | 0.971 |
| c_instr_v2 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 1.00 | 1.00 | yes | 0.6002 | 1.000 |
| c_instr_v2 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_instr_v2 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.01 | 0.228 |
| c_instr_v2 | block100 | 20 (20) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4814 | 0.027 |
| c_instr_v2 | block100 | 20 (20) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.02512 | 0.033 |
| c_instr_v2 | block100 | 20 (20) | C2low (post-hoc) | 0.02108 | 0.05 | 0.00 | yes | 0.02512 | 0.967 |
| c_instr_v2 | block100 | 20 (20) | C3 (post-hoc) | 0.5314 | 1.00 | 1.00 | yes | 0.6009 | 1.000 |
| c_instr_v2 | block100 | 20 (20) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_instr_v2 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| c_instr_v2 | identity_split_n10 | 50 (50) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4832 | 0.029 |
| c_instr_v2 | identity_split_n10 | 50 (50) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.02486 | 0.029 |
| c_instr_v2 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02108 | 0.06 | 0.00 | yes | 0.02486 | 0.971 |
| c_instr_v2 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5314 | 1.00 | 1.00 | yes | 0.5994 | 1.000 |
| c_instr_v2 | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_instr_v2 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.137 |
| c_instr_v2 | identity_split_n100 | 500 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| c_instr_v2 | identity_split_n100 | 500 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| c_instr_v2 | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| c_instr_v2 | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| c_instr_v2 | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_instr_v2 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| c_instr_v2 | identity_split_n1000 | 5000 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| c_instr_v2 | identity_split_n1000 | 5000 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| c_instr_v2 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| c_instr_v2 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| c_instr_v2 | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_instr_v2 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| control:oasst | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4545 | 0.008 |
| control:oasst | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.007641 | 0.000 |
| control:oasst | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.007641 | 1.000 |
| control:oasst | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 1.00 | 0.00 | yes | 0.5557 | 0.997 |
| control:oasst | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.0003333 | 0.979 |
| control:oasst | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.001333 | 0.228 |
| control:oasst | block100 | 30 (30) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4718 | 0.023 |
| control:oasst | block100 | 30 (30) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.007862 | 0.000 |
| control:oasst | block100 | 30 (30) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.007862 | 1.000 |
| control:oasst | block100 | 30 (30) | C3 (post-hoc) | 0.5314 | 1.00 | 0.03 | yes | 0.5558 | 0.997 |
| control:oasst | block100 | 30 (30) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.506 |
| control:oasst | block100 | 30 (30) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| control:oasst | identity_split_n10 | 50 (50) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4731 | 0.020 |
| control:oasst | identity_split_n10 | 50 (50) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.007442 | 0.000 |
| control:oasst | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.007442 | 1.000 |
| control:oasst | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5314 | 1.00 | 0.02 | yes | 0.5563 | 0.997 |
| control:oasst | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.539 |
| control:oasst | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| control:oasst | identity_split_n100 | 500 (500) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4785 | 0.033 |
| control:oasst | identity_split_n100 | 500 (500) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.007332 | 0.000 |
| control:oasst | identity_split_n100 | 500 (500) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.007332 | 1.000 |
| control:oasst | identity_split_n100 | 500 (500) | C3 (post-hoc) | 0.5314 | 0.97 | 0.14 | yes | 0.557 | 0.997 |
| control:oasst | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.01 | 0.00 | yes | 0 | 0.495 |
| control:oasst | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
| control:oasst | identity_split_n1000 | 5000 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| control:oasst | identity_split_n1000 | 5000 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| control:oasst | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| control:oasst | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| control:oasst | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:oasst | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
