M4 content level (benign `m3_v1`, model `BAAI/bge-small-en-v1.5`, 1273 benign identities at matched n = 10, block session). C2low and C3 are post-hoc (amendment B1). Flagged = fraction of campaign units over the benign threshold; per-identity cells under identity splitting are n/a below matched n.

| Campaign | Unit | n units (scoreable) | Detector | 1% threshold | Flagged 1% | Flagged 0.1% | Below res. 0.1% | Campaign median | AUC |
|---|---|---|---|---|---|---|---|---|---|
| pilot_baseline | identity | 1 (1) | C1 | 0.9332 | 0.00 | 0.00 | yes | 0.8174 | 0.688 |
| pilot_baseline | identity | 1 (1) | C2 | 0.3007 | 0.00 | 0.00 | yes | 0.07721 | 0.465 |
| pilot_baseline | identity | 1 (1) | C2low (post-hoc) | 0.01865 | 0.00 | 0.00 | yes | 0.07721 | 0.535 |
| pilot_baseline | identity | 1 (1) | C3 (post-hoc) | 0.5312 | 0.00 | 0.00 | yes | 0.401 | 0.566 |
| pilot_baseline | identity | 1 (1) | B1 | 0.01235 | 1.00 | 1.00 | yes | 0.92 | 1.000 |
| pilot_baseline | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| pilot_baseline | block100 | 20 (20) | C1 | 0.9332 | 0.00 | 0.00 | yes | 0.809 | 0.633 |
| pilot_baseline | block100 | 20 (20) | C2 | 0.3007 | 0.00 | 0.00 | yes | 0.07657 | 0.447 |
| pilot_baseline | block100 | 20 (20) | C2low (post-hoc) | 0.01865 | 0.00 | 0.00 | yes | 0.07657 | 0.553 |
| pilot_baseline | block100 | 20 (20) | C3 (post-hoc) | 0.5312 | 0.00 | 0.00 | yes | 0.4063 | 0.596 |
| pilot_baseline | block100 | 20 (20) | B1 | 0.01235 | 1.00 | 1.00 | yes | 0.915 | 1.000 |
| pilot_baseline | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 1 | 0.963 |
| c_real_v2:20 | identity | 1 (1) | C1 | 0.9332 | 0.00 | 0.00 | yes | 0.6553 | 0.031 |
| c_real_v2:20 | identity | 1 (1) | C2 | 0.3007 | 0.00 | 0.00 | yes | -0.0003186 | 0.000 |
| c_real_v2:20 | identity | 1 (1) | C2low (post-hoc) | 0.01865 | 1.00 | 1.00 | yes | -0.0003186 | 1.000 |
| c_real_v2:20 | identity | 1 (1) | C3 (post-hoc) | 0.5312 | 0.00 | 0.00 | yes | 0.5218 | 0.982 |
| c_real_v2:20 | identity | 1 (1) | B1 | 0.01235 | 0.00 | 0.00 | yes | 0 | 0.491 |
| c_real_v2:20 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0305 | 0.267 |
| c_real_v2:20 | block100 | 20 (20) | C1 | 0.9332 | 0.00 | 0.00 | yes | 0.6627 | 0.049 |
| c_real_v2:20 | block100 | 20 (20) | C2 | 0.3007 | 0.00 | 0.00 | yes | 0.001103 | 0.000 |
| c_real_v2:20 | block100 | 20 (20) | C2low (post-hoc) | 0.01865 | 1.00 | 1.00 | yes | 0.001103 | 1.000 |
| c_real_v2:20 | block100 | 20 (20) | C3 (post-hoc) | 0.5312 | 0.00 | 0.00 | yes | 0.5185 | 0.977 |
| c_real_v2:20 | block100 | 20 (20) | B1 | 0.01235 | 0.00 | 0.00 | yes | 0 | 0.491 |
| c_real_v2:20 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.231 |
| c_real_v2 | identity | 1 (1) | C1 | 0.9332 | 0.00 | 0.00 | yes | 0.6492 | 0.016 |
| c_real_v2 | identity | 1 (1) | C2 | 0.3007 | 0.00 | 0.00 | yes | 0.002244 | 0.000 |
| c_real_v2 | identity | 1 (1) | C2low (post-hoc) | 0.01865 | 1.00 | 1.00 | yes | 0.002244 | 1.000 |
| c_real_v2 | identity | 1 (1) | C3 (post-hoc) | 0.5312 | 0.00 | 0.00 | yes | 0.5059 | 0.962 |
| c_real_v2 | identity | 1 (1) | B1 | 0.01235 | 0.00 | 0.00 | yes | 0.000125 | 0.983 |
| c_real_v2 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.0405 | 0.267 |
| c_real_v2 | block100 | 80 (80) | C1 | 0.9332 | 0.00 | 0.00 | yes | 0.6648 | 0.055 |
| c_real_v2 | block100 | 80 (80) | C2 | 0.3007 | 0.00 | 0.00 | yes | 0.001081 | 0.000 |
| c_real_v2 | block100 | 80 (80) | C2low (post-hoc) | 0.01865 | 1.00 | 1.00 | yes | 0.001081 | 1.000 |
| c_real_v2 | block100 | 80 (80) | C3 (post-hoc) | 0.5312 | 0.06 | 0.00 | yes | 0.5178 | 0.976 |
| c_real_v2 | block100 | 80 (80) | B1 | 0.01235 | 0.00 | 0.00 | yes | 0 | 0.498 |
| c_real_v2 | block100 | 80 (80) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.230 |
| c_real_v2_s1 | identity | 1 (1) | C1 | 0.9332 | 0.00 | 0.00 | yes | 0.6634 | 0.049 |
| c_real_v2_s1 | identity | 1 (1) | C2 | 0.3007 | 0.00 | 0.00 | yes | 0.003624 | 0.000 |
| c_real_v2_s1 | identity | 1 (1) | C2low (post-hoc) | 0.01865 | 1.00 | 1.00 | yes | 0.003624 | 1.000 |
| c_real_v2_s1 | identity | 1 (1) | C3 (post-hoc) | 0.5312 | 0.00 | 0.00 | yes | 0.5026 | 0.951 |
| c_real_v2_s1 | identity | 1 (1) | B1 | 0.01235 | 0.00 | 0.00 | yes | 0.001 | 0.983 |
| c_real_v2_s1 | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.029 | 0.267 |
| c_real_v2_s1 | block100 | 20 (20) | C1 | 0.9332 | 0.00 | 0.00 | yes | 0.665 | 0.067 |
| c_real_v2_s1 | block100 | 20 (20) | C2 | 0.3007 | 0.00 | 0.00 | yes | 0.001639 | 0.000 |
| c_real_v2_s1 | block100 | 20 (20) | C2low (post-hoc) | 0.01865 | 1.00 | 1.00 | yes | 0.001639 | 1.000 |
| c_real_v2_s1 | block100 | 20 (20) | C3 (post-hoc) | 0.5312 | 0.10 | 0.00 | yes | 0.5156 | 0.971 |
| c_real_v2_s1 | block100 | 20 (20) | B1 | 0.01235 | 0.00 | 0.00 | yes | 0 | 0.541 |
| c_real_v2_s1 | block100 | 20 (20) | B2 | 1 | 0.00 | 0.00 | yes | 0.03 | 0.240 |
