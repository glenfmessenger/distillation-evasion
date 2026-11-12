M4 content level (benign `m3_v1`, model `BAAI/bge-small-en-v1.5`, 1061 benign identities at matched n = 30, block 50). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
| pilot_baseline | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.742 | 0.622 |
| pilot_baseline | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.07363 | 0.436 |
| pilot_baseline | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 0.00 | 0.00 | yes | 0.07363 | 0.564 |
| pilot_baseline | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.4099 | 0.589 |
| pilot_baseline | identity | 1 (1) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.92 | 1.000 |
| pilot_baseline | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | block50 | 40 (40) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.758 | 0.667 |
| pilot_baseline | block50 | 40 (40) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.07622 | 0.459 |
| pilot_baseline | block50 | 40 (40) | C2low (post-hoc) | 0.02108 | 0.00 | 0.00 | yes | 0.07622 | 0.541 |
| pilot_baseline | block50 | 40 (40) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.4085 | 0.578 |
| pilot_baseline | block50 | 40 (40) | B1 | 0.01626 | 1.00 | 1.00 | yes | 0.92 | 1.000 |
| pilot_baseline | block50 | 40 (40) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.958 |
| c_real_v2:20 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4817 | 0.026 |
| c_real_v2:20 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001903 | 0.000 |
| c_real_v2:20 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001903 | 1.000 |
| c_real_v2:20 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5219 | 0.987 |
| c_real_v2:20 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0305 | 0.228 |
| c_real_v2:20 | block50 | 40 (40) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4734 | 0.026 |
| c_real_v2:20 | block50 | 40 (40) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001659 | 0.000 |
| c_real_v2:20 | block50 | 40 (40) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001659 | 1.000 |
| c_real_v2:20 | block50 | 40 (40) | C3 (post-hoc) | 0.5314 | 0.07 | 0.00 | yes | 0.5164 | 0.975 |
| c_real_v2:20 | block50 | 40 (40) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0 | 0.490 |
| c_real_v2:20 | block50 | 40 (40) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.169 |
| c_real_v2 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4781 | 0.025 |
| c_real_v2 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001099 | 0.000 |
| c_real_v2 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001099 | 1.000 |
| c_real_v2 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5116 | 0.971 |
| c_real_v2 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.000125 | 0.979 |
| c_real_v2 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0405 | 0.228 |
| c_real_v2 | block50 | 160 (160) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4702 | 0.027 |
| c_real_v2 | block50 | 160 (160) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.00153 | 0.000 |
| c_real_v2 | block50 | 160 (160) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.00153 | 1.000 |
| c_real_v2 | block50 | 160 (160) | C3 (post-hoc) | 0.5314 | 0.07 | 0.00 | yes | 0.5161 | 0.975 |
| c_real_v2 | block50 | 160 (160) | B1 | 0.01626 | 0.01 | 0.00 | yes | 0 | 0.493 |
| c_real_v2 | block50 | 160 (160) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.169 |
| c_real_v2_s1 | identity | 1 (1) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4734 | 0.021 |
| c_real_v2_s1 | identity | 1 (1) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001989 | 0.000 |
| c_real_v2_s1 | identity | 1 (1) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001989 | 1.000 |
| c_real_v2_s1 | identity | 1 (1) | C3 (post-hoc) | 0.5314 | 0.00 | 0.00 | yes | 0.5139 | 0.975 |
| c_real_v2_s1 | identity | 1 (1) | B1 | 0.01626 | 0.00 | 0.00 | yes | 0.001 | 0.979 |
| c_real_v2_s1 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.029 | 0.228 |
| c_real_v2_s1 | block50 | 40 (40) | C1 | 0.9355 | 0.00 | 0.00 | yes | 0.4755 | 0.031 |
| c_real_v2_s1 | block50 | 40 (40) | C2 | 0.2966 | 0.00 | 0.00 | yes | 0.001808 | 0.000 |
| c_real_v2_s1 | block50 | 40 (40) | C2low (post-hoc) | 0.02108 | 1.00 | 1.00 | yes | 0.001808 | 1.000 |
| c_real_v2_s1 | block50 | 40 (40) | C3 (post-hoc) | 0.5314 | 0.05 | 0.00 | yes | 0.5141 | 0.972 |
| c_real_v2_s1 | block50 | 40 (40) | B1 | 0.01626 | 0.05 | 0.00 | yes | 0 | 0.515 |
| c_real_v2_s1 | block50 | 40 (40) | B2 | 1 | 0.00 | 0.00 | yes | 0 | 0.179 |
