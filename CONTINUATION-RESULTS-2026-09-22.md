# September 22 continuation evidence

Generated from saved records; running and completed studies are distinguished.

## Go smoke-v2: complete

| Matchup | NH wins | As Black / White | Finished | Unfinished |
|---|---:|---:|---:|---:|
| NH-vs-NN | 0 | 0 / 0 | 2 | 0 |
| NH-vs-policy | 0 | 0 / 0 | 2 | 0 |
| NH-vs-search | 0 | 0 / 0 | 2 | 0 |

Smoke is diagnostic only. The first smoke-v1 search results are invalid and excluded.

NN complete-round retention: 279/356 (78.4%). Prespecified expansion gate: 80%.

## Go expansion-v2: complete

| Matchup | NH wins | As Black / White | Finished | Unfinished |
|---|---:|---:|---:|---:|
| NH-vs-policy | 3 | 0 / 3 | 20 | 0 |
| NH-vs-search | 0 | 0 / 0 | 20 | 0 |

Smoke is diagnostic only. The first smoke-v1 search results are invalid and excluded.

## Go cpu-small-v2: complete

| Matchup | NH wins | As Black / White | Finished | Unfinished |
|---|---:|---:|---:|---:|
| NH-vs-HH | 3 | 1 / 2 | 4 | 0 |

Smoke is diagnostic only. The first smoke-v1 search results are invalid and excluded.

## Fixed-model budget probes

| Budget ms | Mode | Decisions | Median ms | Neural complete | Root timeouts |
|---:|---|---:|---:|---:|---:|
| 50 | NH | 8 | 50.3 | 0 | 0 |
| 50 | NN | 8 | 51.5 | 3 | 0 |
| 100 | NH | 8 | 100.4 | 0 | 0 |
| 100 | NN | 8 | 101.8 | 6 | 0 |
| 200 | NH | 8 | 200.1 | 0 | 0 |
| 200 | NN | 8 | 201.4 | 7 | 0 |
| 400 | NH | 8 | 400.4 | 0 | 0 |
| 400 | NN | 8 | 401.5 | 8 | 0 |

Same eight development histories, b10/OpenCL model and profile. These measure throughput, not playing strength.

## LLM smoke-v3: 1 recorded runs

| Task/treatment | Success | Correct | Runs | Timeouts |
|---|---:|---:|---:|---:|
| graph/staged | 0 | 0 | 1 | 0 |

Pretrial failures (no agent phase): 1.
Success requires correctness and clean completion within both budgets. Smoke is excluded from main results.

## LLM smoke-v4: 2 recorded runs

| Task/treatment | Success | Correct | Runs | Timeouts |
|---|---:|---:|---:|---:|
| graph/staged | 0 | 0 | 1 | 1 |
| graph/one-shot | 0 | 1 | 1 | 1 |

Pretrial failures (no agent phase): 0.
Success requires correctness and clean completion within both budgets. Smoke is excluded from main results.

## Limits

- No Elo estimate or default promotion.
- Smoke and incomplete comparisons are excluded from confirmation claims.
- Budget probes are development-position throughput diagnostics, not strength tests.
- Staging includes separate contexts/processes and plan transfer, not wording alone.

No main staging comparison has run. The clean-completion smoke gate remains unmet; see the [staging diagnosis](STAGING-RESULTS-2026-09-22.md).

The separate [Bonsai packing report](PACKING-RESULTS-2026-09-22.md) records corrected API controls, GPU measurements, and CPU control outcomes.
