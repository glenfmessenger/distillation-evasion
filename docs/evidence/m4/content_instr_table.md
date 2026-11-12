M4 content level (benign `m3_v1`, model `BAAI/bge-small-en-v1.5`, 1061 benign identities at matched n = 30, block session). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
| pilot_baseline | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.742 | 0.622 |
| pilot_baseline | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.07363 | 0.436 |
| pilot_baseline | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 0.00 | 0.00 | yes | 0.07363 | 0.564 |
| pilot_baseline | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.4099 | 0.589 |
| pilot_baseline | identity | 1 (1) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.92 | 1.000 |
| pilot_baseline | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | block100 | 20 (20) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.7659 | 0.678 |
| pilot_baseline | block100 | 20 (20) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.07673 | 0.459 |
| pilot_baseline | block100 | 20 (20) | C2low (post-hoc) | 0.02108 | 0.00 | 0.00 | yes | 0.07673 | 0.541 |
| pilot_baseline | block100 | 20 (20) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.4076 | 0.576 |
| pilot_baseline | block100 | 20 (20) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.915 | 1.000 |
| pilot_baseline | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | identity_split_n10 | 50 (50) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.7597 | 0.671 |
| pilot_baseline | identity_split_n10 | 50 (50) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.07646 | 0.460 |
| pilot_baseline | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02108 | 0.00 | 0.00 | yes | 0.07646 | 0.540 |
| pilot_baseline | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.4081 | 0.580 |
| pilot_baseline | identity_split_n10 | 50 (50) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.9275 | 1.000 |
| pilot_baseline | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | identity_split_n100 | 500 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n100 | 500 (500) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.95 | 1.000 |
| pilot_baseline | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.949 |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| pilot_baseline | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.99 | 0.99 | yes | 1 | 0.996 |
| pilot_baseline | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.630 |
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
| c_real_v2_s1 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4734 | 0.021 |
| c_real_v2_s1 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001989 | 0.000 |
| c_real_v2_s1 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001989 | 1.000 |
| c_real_v2_s1 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5139 | 0.975 |
| c_real_v2_s1 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.001 | 0.979 |
| c_real_v2_s1 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.029 | 0.228 |
| c_real_v2_s1 | block100 | 20 (20) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4779 | 0.026 |
| c_real_v2_s1 | block100 | 20 (20) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001903 | 0.000 |
| c_real_v2_s1 | block100 | 20 (20) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001903 | 1.000 |
| c_real_v2_s1 | block100 | 20 (20) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5168 | 0.972 |
| c_real_v2_s1 | block100 | 20 (20) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.539 |
| c_real_v2_s1 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.03 | 0.207 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4775 | 0.028 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001621 | 0.000 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001621 | 1.000 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5154 | 0.974 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.588 |
| c_real_v2_s1 | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.0275 | 0.228 |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.02 | 0.00 | yes | 0 | 0.500 |
| c_real_v2_s1 | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.139 |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| c_real_v2_s1 | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.491 |
| c_real_v2_s1 | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.114 |
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
| control:uniform_firstturns | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4851 | 0.027 |
| control:uniform_firstturns | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001258 | 0.000 |
| control:uniform_firstturns | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001258 | 1.000 |
| control:uniform_firstturns | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.516 | 0.978 |
| control:uniform_firstturns | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.03367 | 0.228 |
| control:uniform_firstturns | block100 | 30 (30) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4779 | 0.027 |
| control:uniform_firstturns | block100 | 30 (30) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001582 | 0.000 |
| control:uniform_firstturns | block100 | 30 (30) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001582 | 1.000 |
| control:uniform_firstturns | block100 | 30 (30) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5179 | 0.977 |
| control:uniform_firstturns | block100 | 30 (30) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | block100 | 30 (30) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.183 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.482 | 0.029 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001597 | 0.000 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001597 | 1.000 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5155 | 0.978 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | identity_split_n10 | 50 (50) | B2 | 1 | 0.00 | 0.00 | yes | 0.02167 | 0.228 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4791 | 0.041 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001523 | 0.000 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001523 | 1.000 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | C3 (post-hoc) | 0.5314 | 0.18 | 0.00 | yes | 0.5162 | 0.973 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | identity_split_n100 | 500 (500) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.144 |
| control:uniform_firstturns | identity_split_n1000 | 5000 (0) | C1 | 0.9355 | n/a | n/a | yes | n/a | n/a |
| control:uniform_firstturns | identity_split_n1000 | 5000 (0) | C2 | 0.2966 | n/a | n/a | yes | n/a | n/a |
| control:uniform_firstturns | identity_split_n1000 | 5000 (0) | C2low (post-hoc) | 0.02108 | n/a | n/a | yes | n/a | n/a |
| control:uniform_firstturns | identity_split_n1000 | 5000 (0) | C3 (post-hoc) | 0.5314 | n/a | n/a | yes | n/a | n/a |
| control:uniform_firstturns | identity_split_n1000 | 5000 (5000) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| control:uniform_firstturns | identity_split_n1000 | 5000 (5000) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.115 |
