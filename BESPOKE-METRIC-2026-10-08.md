# The Bespoke civil_comments anomaly is solved - it is a metric artifact, and the metric flips the ranking

*(2026-10-10: the anomaly diagnosis holds, but "flips the ranking" does not - that came from comparing a
5-subset average against a 13-subset macro. See the correction at the end of this file.)*

2026-10-08, overnight. Read with `bespoke-suite-20261005-v1/REPORT.md` and
`bespoke-suite-20261007-v1/REPORT.md`, which both recorded this as unexplained: our nimble run scored
**91.0 %** on `civil_comments` against a published **70.3 %**. The 2026-10-05 note guessed "rendering or
positive-class handling"; the 2026-10-07 note left it alone. Neither was right, and no inference was
needed to settle it - the answer is in the rows already on disk.

## What `civil_comments` is, in this suite

It is a **`noul`** subset: the model returns a scalar probability `noul`, the scorer expands it to
`{'false': 1-p, 'true': p}`, and the prediction is `p > 0.5`
(`suite_worker.py: probabilities()`, `assess()`). So the subset's accuracy is a **threshold at 0.5 on a
binary label**, and its value therefore depends almost entirely on the label balance.

## The balance, measured from our own rows

| | targets | majority baseline | our accuracy | our **balanced** accuracy | published |
|---|---|---|---|---|---|
| `civil_comments` (300 rows) | **32 positive, 268 negative** | **89.3 %** | 91.0 % | **72.9 %** | 70.3 % |

- Our 91.0 % is the majority baseline **+ 1.7 points** - almost no signal.
- Our **balanced accuracy is 72.9 %**, which matches the published 70.3 % to 2.6 points - the same
  agreement band as every other subset where our run and the published table track each other
  (aegis2 -5.6, boolq +0.3, paws -3.6, squad2 +1.3).
- The other five binary subsets are near-balanced (majority 50.2-58.0 %), which is exactly why they never
  showed the anomaly. `civil_comments` is the only `noul` subset in the suite with a 90/10 skew.

**Conclusion: the published figure is a class-balanced metric, ours was plain accuracy on a 90/10
subset.** The anomaly is closed as a metric mismatch, not rendering, not positive-class handling, and
not a better local model.

## The consequence is bigger than the anomaly: the ranking depends on the metric

Recomputed from the stored rows, all five local models, 13 subsets each (balanced accuracy over the
binary subsets; plain accuracy over the rest as before):

| model | accuracy macro | rank | **balanced macro** | rank | civil_comments |
|---|---|---|---|---|---|
| **kev4 4B** | 0.744 | 2 | **0.805** | **1** | 0.833 |
| nimble 9B | **0.757** | 1 | 0.797 | 2 | 0.910 |
| lev | 0.684 | 3 | 0.790 | 3 | 0.750 |
| kev0 | 0.612 | 4 | 0.694 | 4 | 0.840 |
| laya | 0.580 | 5 | 0.651 | 5 | 0.937 |

- **The 4B model takes the top spot from the 9B** when the binary subsets are scored class-balanced
  (0.805 vs 0.797), and the two are inside 1 point either way.
- `lev` moves **+10.6 points** (0.684 -> 0.790) and closes to within 1.5 of the leader, so its earlier
  distance from nimble was mostly a majority-class artifact.
- `laya` is the *best* model on `civil_comments` by accuracy (0.937) purely because it predicts the
  majority class hardest; balanced, it is last.
- The honest statement about this suite is therefore: **kev4, nimble and lev are within ~1.5 points of
  each other on class-balanced accuracy**, and any "4B is close to 9B" or "9B leads" claim from the
  accuracy macro alone is metric-dependent.

## Two further measurement points from the same rows

1. **The macro mixes metrics with different baselines.** `noul` and `choice` subsets are scored as
   accuracy, but `score` subsets (helpsteer2, summeval-*) are scored as **argmax-rounded accuracy on a
   5-point scale** (36-43 % for helpsteer2, 34-39 % for summeval-relevance). Those are legitimately hard,
   but averaging them with binary accuracy means the macro is a blend of scales with different chance
   floors. The scorer already computes the better primitive for them - `expected_score` and
   `absolute_score_error` - which should be reported and averaged separately.
2. **Prediction rates expose the failure mode directly.** On `civil_comments` the positive-prediction
   rate is 0.09 (nimble) and 0.21 (kev4) against a 0.107 positive base rate: nimble is close to a
   constant-majority classifier, kev4 tries more and pays accuracy for it. Reporting the prediction rate
   next to accuracy would have made this visible in the original table.

## Recommendation for how this suite is reported from now on

- Report **balanced accuracy (or per-class recall) for every binary subset**, alongside the prediction
  rate; keep plain accuracy only as a secondary number.
- **Separate the metric families** in the macro: one macro over choice/noul subsets (accuracy or
  balanced accuracy), one over score subsets (expected-score error). Do not average them together.
- Treat `civil_comments` as near-uninformative under accuracy (89.3 % majority); if it is kept, score it
  balanced.
- No re-run is needed for any of this: every number above is recomputed from the stored rows, so the
  existing roots stay frozen and the ranking can be restated in the corrected metric.

## Correction, 2026-10-10: the flip was an averaging artifact

Re-derived from the frozen `rows.jsonl` in `ai_bench/bespoke-metric-20261010/` (`recompute.py`, no
inference). The table above compares two different things: its "balanced macro" column is the mean over
the **5 binary subsets only**, set beside a **13-subset** accuracy macro.

| view | kev4 4B | nimble 9B | lev | kev0 | laya |
|---|---|---|---|---|---|
| 13-subset accuracy macro (the original metric) | 0.7442 | **0.7565** | 0.6841 | 0.6121 | 0.5801 |
| 13-subset balanced macro (balanced for the 5 `noul` subsets, accuracy elsewhere) | 0.7395 | **0.7445** | 0.6814 | 0.5997 | 0.5687 |
| 5 binary subsets (`noul`), balanced accuracy | **0.8049** | 0.7969 | 0.7897 | 0.6939 | 0.6505 |

The note's "0.805 / 0.797" is the third row. Like-for-like, **the ranking does not flip**: nimble stays
0.5 points ahead on both 13-subset macros, and kev4 leads by 0.8 points on the binary subsets alone. The
defensible claim is the weaker one - the 4B `kev4` is within a point of the 9B `nimble` on every view and
leads on the binary view, so they are a tie at this sample size.

Everything else here is confirmed to the digit: all five recorded accuracies reproduce (75.65 / 74.42 /
68.41 / 61.21 / 58.01); nimble's `civil_comments` is 0.910 against a 0.893 majority baseline (+1.7
points) with balanced accuracy 0.730; and `laya` tops that subset on accuracy (0.937) while predicting
the positive class only 5.0 % of the time (nimble 9.0 %, kev4 21.3 %, kev0 14.7 %, lev 28.3 %). The
artifact diagnosis and every reporting recommendation below stand; only the rank reversal was overstated.
