# OpenJev single-question and real-history follow-up - September 25, 2026

Completed offline, observation-only. No global hook or automatic intervention enabled. No reboot or startup changes.

Single-question scoring preserved all 46 original stuck probabilities exactly. Paired median latency changed from 4.04s to 3.03s. Warm p95 is 3.34s: the fixed 3-second gate failed.

## Natural-history screen

18 windows from 34 archived coding traces, selected before scoring (first per repeated key, at most 3 per source). These are real recorded histories newly used for this judge, not fresh coding runs. Four stalls and 14 legitimate retries/progress windows were labeled by one reviewer before inference; labels and rationales are frozen. No independent annotator, no threshold tuning, and correlated windows limit confidence. Labels concern stalled progress, not overall code correctness or policy compliance.

| Judge | Caught stalls / 4 | Missed stalls | False alarms / 14 | Correct / 18 |
|---|---:|---:|---:|---:|
| OpenJev, frozen threshold 0.85 | 0 | 4 | 0 | 14 |
| Failure-only repeat rule | 1 | 3 | 0 | 15 |
| Never flag | 0 | 4 | 0 | 14 |
| Always flag | 4 | 0 | 14 | 4 |

Natural-history model latency: median 11.26s, p95 18.05s; 18/18 exceed three seconds.

The deterministic rule requires two identical failed outputs before the third identical call and no intervening successful edit or recognized mutation. Failed edits do not reset it. Successful read/diagnostic loops are outside its scope. It uses exact full-input/output identity, not clipped-text equality; six regression checks cover successful edits, failed edits, changed errors, successful polling, and data changes.

Model and rule share mutation metadata. Model states retain all 12 calls but shorten input/output excerpts to 160/120 characters and task to 400; integer equality IDs replace long hashes. Maximum formatted input is 1,888 tokens, below the unchanged 2,048-token cap. Full source and audit hashes remain available. This representation differs from the synthetic control, so natural results are not a pure dataset-only comparison.

Offline extraction allows multiple keys per source; the existing online observer emits at most once per user turn. These are screen metrics, not predicted live intervention counts.

| Case | Reviewed stuck | OpenJev p | Rule flag | Rationale |
|---|---|---:|---|---|
| natural-1 | False | 0.2563 | False | Dependency diagnostic rerun after a successful, relevant test repair. |
| natural-2 | False | 0.4091 | False | Missing-dependency retest after fixing the deps normalization in solution.py. |
| natural-3 | False | 0.3229 | False | Edge-case test rewritten after diagnostic probes; failures change. Separate test-file policy violation is not a loop label. |
| natural-4 | True | 0.5389 | False | Three identical local scalar diagnostics, same successful output, no intervening change or polling requirement. |
| natural-5 | True | 0.6925 | False | Repeated merge probes with unchanged results and then three identical calls, no intervening edits. |
| natural-6 | False | 0.5012 | False | Malformed-input retest after changing validation and unpacking in solution.py. |
| natural-7 | True | 0.3218 | False | Three empty directory listings of harness files while implementation remains absent; no intervening change. |
| natural-8 | False | 0.3942 | False | Self-test rerun after a successful repair of the import assertion. |
| natural-9 | False | 0.3579 | False | Self-test rerun amid successful edits with a changed failure. |
| natural-10 | True | 0.4290 | True | Third identical edit after two identical no-change failures; a reread does not change the replacement. |
| natural-11 | False | 0.3439 | False | Public tests rerun after successful edits, with changing failing assertions. |
| natural-12 | False | 0.3105 | False | Public tests rerun after successful edits, with changing failing assertions. |
| natural-13 | False | 0.3361 | False | Self-test rerun after repairs; earlier failures and passed-test output differ. |
| natural-14 | False | 0.3379 | False | List requested after successful task removal and dependency mutation; outputs change. |
| natural-15 | False | 0.4476 | False | Plan requested after adding tasks; state and output change. |
| natural-16 | False | 0.3437 | False | Public tests rerun after successful solution edits. |
| natural-17 | False | 0.3224 | False | Public tests rerun after successful solution edits. |
| natural-18 | False | 0.3138 | False | Public tests rerun after successful solution edits and inspection. |

## Runtime and evidence

Pinned OpenJev 0.8B v5, CPU float32, four threads, batch size one. Same model and upstream wrapper as the prior trial; only the unused second question was removed in the timing control. Warm latency excludes the first request; model load is separate. Timing was not randomized or replicated, so speedup is descriptive.

64 model requests: 46 repeated synthetic controls plus 18 archival windows. No concurrent inference. Initial gates remained 9 GiB free RAM / 8 GiB commit / 0.5 GiB VRAM; runtime floors 3 / 2 / 0.5 GiB, sustained paging guard, 6 GiB process-tree private cap, 900-second deadline, and STOP file.

| Run | Peak process-tree private GiB | Minimum free RAM GiB | Minimum commit GiB |
|---|---:|---:|---:|
| timing | 4.50 | 10.99 | 49.02 |
| natural | 4.78 | 11.04 | 48.65 |

Both runs completed without a resource abort. All 10 owned process identities are absent, port 8098 is closed, and the lock is removed. Prior worker provenance and all frozen follow-up input/label/baseline hashes verified.

All 19 previously recorded source-file hashes and all 34 archived source hashes match. Every natural prediction matches its frozen state hash and pre-counted token length.

Evidence: protocol.json; natural-labels.json; natural-candidates.json; baseline-predictions.json; evidence/natural-sources.json; evidence/natural-token-check.json; evidence/baseline-tests.json; evidence/summary.json; and both evidence/openjev-* run directories.

## Decision

Do not promote OpenJev to automatic interruption. Its fixed latency gate failed, and these natural states are slower still. Keep the failure-only rule as an observation-only candidate. Next useful step: a cheap logging hook that records unchanged failures and successful-output loops separately, followed by independent labels from new sessions before considering intervention. Do not broaden the rule on these labels and call the same cases validation.
