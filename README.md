# What a Serving Layer Must See

Harness, evidence and manuscript build for *What a Serving Layer Must See: Calibrated Detection
of LLM Distillation Campaigns at Three Levels of Visibility*. A locally served open model is the
only endpoint ever queried; no third-party service is involved.

## What is here

- `PROTOCOL_v2.md` — the pre-registered protocol the paper reports against (predictions P1 to P24,
  amendments B1 to B5 and A8). `PROTOCOL.md` is the superseded first protocol, kept because the paper's
  prediction register and its capability appendix report against it. `GATES.md` records the
  frozen commits of both.
- `DECISIONS.md`, `FINDINGS.md` — the decision log and the findings log, including every failed
  prediction and every defect found in the harness and in the manuscript during the study.
- `docs/evidence/` — the committed evidence files (JSON and tables) from which every number in
  the paper is generated. `docs/related.md`, `docs/ttv.md`, `docs/environment.md`,
  `docs/ai_use_log.md` are the related-work, threats, environment and AI-use records.
- `src/dev_harness/` — the harness: record schema, benign-traffic replay, content-blind detectors
  (D1 to D11), content detectors (C1, C2, lexical baselines), levers and the attacker search.
- `scripts/` — the runs as they were executed (campaigns, replay, scoring, analyses) and the
  paper build (`build_paper.py`, `build_figures.py`).
- `paper/` — the manuscript source and its build (`make` regenerates every macro, table and
  figure from `docs/evidence/` and compiles the PDF; the build fails on a missing source). It is
  withheld from the public release until the manuscript has cleared review.
- `tests/` — GPU-independent tests (`python -m pytest`).

## Reproducing

Raw data (campaign records, replayed benign traffic, scores) is not in the repository. Everything
reads from `HARNESS_HOST_REPO`, an explicit environment variable pointing at a data root; loaders
raise without it. The benign corpus is `allenai/WildChat-1M`; the teacher is `Qwen/Qwen3-8B`
served with vLLM; models and datasets are public. The scripts record every parameter and seed.

Setup: `uv venv --python 3.11 .venv && uv pip install -e ".[dev,paper]"`.

## Licence

Apache License 2.0; see `LICENSE`.
