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
