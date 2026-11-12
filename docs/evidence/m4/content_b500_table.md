M4 content level (benign `m3_v1`, model `BAAI/bge-small-en-v1.5`, 1061 benign identities at matched n = 30, block 500). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
| pilot_baseline | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.742 | 0.622 |
| pilot_baseline | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.07363 | 0.436 |
| pilot_baseline | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 0.00 | 0.00 | yes | 0.07363 | 0.564 |
| pilot_baseline | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.4099 | 0.589 |
| pilot_baseline | identity | 1 (1) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.92 | 1.000 |
| pilot_baseline | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | block500 | 4 (4) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.753 | 0.670 |
| pilot_baseline | block500 | 4 (4) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.07488 | 0.445 |
| pilot_baseline | block500 | 4 (4) | C2low (post-hoc) | 0.02108 | 0.00 | 0.00 | yes | 0.07488 | 0.555 |
| pilot_baseline | block500 | 4 (4) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.4098 | 0.586 |
| pilot_baseline | block500 | 4 (4) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.922 | 1.000 |
| pilot_baseline | block500 | 4 (4) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| c_real_v2:20 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4817 | 0.026 |
| c_real_v2:20 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001903 | 0.000 |
| c_real_v2:20 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001903 | 1.000 |
| c_real_v2:20 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5219 | 0.987 |
| c_real_v2:20 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0305 | 0.228 |
| c_real_v2:20 | block500 | 4 (4) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4636 | 0.015 |
| c_real_v2:20 | block500 | 4 (4) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001544 | 0.000 |
| c_real_v2:20 | block500 | 4 (4) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001544 | 1.000 |
| c_real_v2:20 | block500 | 4 (4) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5175 | 0.979 |
| c_real_v2:20 | block500 | 4 (4) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | block500 | 4 (4) | B2 | 1 | 0.00 | 0.00 | yes | 0.025 | 0.228 |
| c_real_v2 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4781 | 0.025 |
| c_real_v2 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001099 | 0.000 |
| c_real_v2 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001099 | 1.000 |
| c_real_v2 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5116 | 0.971 |
| c_real_v2 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.000125 | 0.979 |
| c_real_v2 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0405 | 0.228 |
| c_real_v2 | block500 | 16 (16) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4759 | 0.023 |
| c_real_v2 | block500 | 16 (16) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001602 | 0.000 |
| c_real_v2 | block500 | 16 (16) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001602 | 1.000 |
| c_real_v2 | block500 | 16 (16) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5146 | 0.974 |
| c_real_v2 | block500 | 16 (16) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.520 |
| c_real_v2 | block500 | 16 (16) | B2 | 1 | 0.00 | 0.00 | yes | 0.023 | 0.228 |
| c_real_v2_s1 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4734 | 0.021 |
| c_real_v2_s1 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001989 | 0.000 |
| c_real_v2_s1 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001989 | 1.000 |
| c_real_v2_s1 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5139 | 0.975 |
| c_real_v2_s1 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.001 | 0.979 |
| c_real_v2_s1 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.029 | 0.228 |
| c_real_v2_s1 | block500 | 4 (4) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4796 | 0.024 |
| c_real_v2_s1 | block500 | 4 (4) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.002123 | 0.000 |
| c_real_v2_s1 | block500 | 4 (4) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.002123 | 1.000 |
| c_real_v2_s1 | block500 | 4 (4) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5174 | 0.979 |
| c_real_v2_s1 | block500 | 4 (4) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.001 | 0.734 |
| c_real_v2_s1 | block500 | 4 (4) | B2 | 1 | 0.00 | 0.00 | yes | 0.028 | 0.228 |
