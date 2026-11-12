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
| control:uniform_firstturns | identity | 1 (1) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.4406 | 0.001 |
| control:uniform_firstturns | identity | 1 (1) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002147 | 0.000 |
| control:uniform_firstturns | identity | 1 (1) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002147 | 1.000 |
| control:uniform_firstturns | identity | 1 (1) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5222 | 0.985 |
| control:uniform_firstturns | identity | 1 (1) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.496 |
| control:uniform_firstturns | identity | 1 (1) | B2 | 1 | 0.00 | 0.00 | yes | 0.03367 | 0.207 |
| control:uniform_firstturns | block100 | 30 (30) | C1 | 0.9275 | 0.00 | 0.00 | yes | 0.439 | 0.002 |
| control:uniform_firstturns | block100 | 30 (30) | C2 | 0.2895 | 0.00 | 0.00 | yes | 0.002303 | 0.000 |
| control:uniform_firstturns | block100 | 30 (30) | C2low (post-hoc) | 0.02157 | 1.00 | 1.00 | yes | 0.002303 | 1.000 |
| control:uniform_firstturns | block100 | 30 (30) | C3 (post-hoc) | 0.5338 | 0.00 | 0.00 | yes | 0.5183 | 0.980 |
| control:uniform_firstturns | block100 | 30 (30) | B1 | 0 | 0.00 | 0.00 | yes | 0 | 0.496 |
| control:uniform_firstturns | block100 | 30 (30) | B2 | 1 | 0.00 | 0.00 | yes | 0.02 | 0.160 |
