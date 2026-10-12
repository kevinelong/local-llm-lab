# RESUME: bespoke-suite-20261010-v1

State: COMPLETE. kev4 and nimble re-measured on the 64 GB platform; both runs clean, `audit` passed (no run
lock, no resident server, 8 staged files verified). No gate changed, no app killed, no reboot, no model
deleted (nothing needed room: 103 GiB free, models already staged).

## Done (2026-10-10)

Runner and worker copied byte-identical from `bespoke-suite-20261007-v1`, sha256-verified
(`run.py` 4fd31f06…, `suite_worker.py` 36d2ad1a…). Preflight: 38.47 GiB physical free, 30.43 GiB commit
headroom, 9.84 GiB GPU free, no Ollama models resident.

| model | samples | macro accuracy | micro accuracy | wall |
|---|---|---|---|---|
| kev4 | 442 | 0.744204 | 0.752835 | - |
| nimble | 752 | 0.756531 | 0.771134 | - |

Whole job (preflight, both screens, audit) 990.8 s.

## The finding: the suite is platform-invariant

Compared record by record against `bespoke-suite-20261005-v1`: **7,760 rows compared, 0 differing** - same
prediction and same correctness for every record of all 13 subsets. Macro accuracy reproduces to six
decimals (0.744204 vs 74.42, 0.756531 vs 75.65). So the pre-upgrade kev4/nimble rows are valid references,
and the paired analysis in `../bespoke-metric-20261010/paired.py` stands unchanged.

## Next actions

1. Nothing is owed here. The decision-track recommendation in `local-llm-lab/README.md` is updated with the
   platform check, the family breakdown and the proper `score`-family primitive.
2. If a stronger local decision model is wanted, the published 9B-class level to beat remains nimble
   (0.7565 macro / 0.7711 micro) and published Jev 1.13.0 at 76.0; nothing local beats it, and nothing
   local is more than 1.2 points behind except at 4B.
3. Position bias stays unmeasured for this suite (it is measured for the knowledge MCQ: both stacks'
   answer-letter distributions match the gold distribution).

Boundaries: one inference workload at a time, no second agent, no app kills, no gate change, no reboot,
no threshold tuning, no promotion. Preserve every run folder.
