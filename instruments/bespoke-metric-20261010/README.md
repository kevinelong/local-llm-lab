# bespoke-metric-20261010: independent re-derivation of the decision-suite metric

No inference. This root exists to check the claim in `local-llm-lab/BESPOKE-METRIC-2026-10-08.md` before
it was propagated into the front-page recommendations, and to state the decision-suite ranking on a
like-for-like basis. It reads only the frozen `rows.jsonl` files of the two suite roots; nothing in
those roots was touched.

```
python recompute.py            # reads the frozen rows, writes recomputed.json
```

## What is confirmed

Every recorded accuracy reproduces exactly, which is what validates the row loading:

| model | root | subsets | records | accuracy macro (recorded) |
|---|---|---|---|---|
| nimble | bespoke-suite-20261005-v1 | 13 | 3,880 | 0.7565 (75.65) |
| kev4 | bespoke-suite-20261005-v1 | 13 | 3,880 | 0.7442 (74.42) |
| lev | bespoke-suite-20261007-v1 | 13 | 3,880 | 0.6841 (68.41) |
| kev0 | bespoke-suite-20261007-v1 | 13 | 3,880 | 0.6121 (61.21) |
| laya | bespoke-suite-20261007-v1 | 13 | 3,880 | 0.5801 (58.01) |

The `civil_comments` diagnosis is also confirmed to the digit: **nimble scores 0.910 against a 0.893
majority baseline** (+1.7 points of signal) with balanced accuracy **0.730**, and **laya tops that subset
on accuracy (0.937) while predicting the positive class only 5.0 % of the time** (nimble 9.0 %, kev4
21.3 %, kev0 14.7 %, lev 28.3 %). Plain accuracy on a 90/10 subset is the majority class plus noise;
the Oct 8 note was right about that and about the fix.

## What does not reproduce: the ranking flip

The Oct 8 table sets a **5-subset** average beside a **13-subset** macro. Re-derived, both views exist
and they disagree:

| view | kev4 4B | nimble 9B | lev | kev0 | laya |
|---|---|---|---|---|---|
| 13-subset accuracy macro (original metric) | 0.7442 | **0.7565** | 0.6841 | 0.6121 | 0.5801 |
| 13-subset balanced macro (balanced for the 5 `noul` subsets, accuracy elsewhere) | 0.7395 | **0.7445** | 0.6814 | 0.5997 | 0.5687 |
| 5 binary subsets (`noul`), balanced accuracy | **0.8049** | 0.7969 | 0.7897 | 0.6939 | 0.6505 |

The note's "0.805 / 0.797" is the third row. Like-for-like, **the ranking does not flip**: nimble stays
ahead by 0.5 points on both 13-subset macros, and kev4 leads by 0.8 points on the binary subsets alone.

**Defensible claim:** the 4B `kev4` is within one point of the 9B `nimble` on every view and leads on the
binary view, so the two are a tie at this sample size - the weaker reading, not a rank reversal.

**Method that should survive:** report balanced accuracy, the positive prediction rate *and* the
majority baseline for skewed binary subsets, and do not average a 5-subset metric into a 13-subset one.

## Is the gap real? Paired test on the frozen rows (`paired.py`)

Both models answer the same 3,880 records, so their difference is paired and the uncertainty comes from
the discordant pairs - no new inference, and sharper than another full pass would be.

| test | difference (kev4 - nimble) | 95 % CI | verdict |
|---|---|---|---|
| macro accuracy | -0.0123 | [-0.0257, +0.0015] | crosses zero |
| macro balanced | -0.0050 | [-0.0189, +0.0092] | crosses zero |
| pooled, record-level | -0.0183 | McNemar exact p = 0.0058 | nimble ahead |

The macro gaps are not established; the record-level pooled difference is, because record pooling weights
`vitaminc-dev` (599 records) and `massive-*` (350 each) far above the 144-record subsets. Both statements
are true and they answer different questions - macro = "on a typical task", pooled = "on a typical call".

They are not uniformly equal, they **trade subsets**: kev4 leads `aegis2` (p = 0.0175), `multinli`
(p = 0.0522), `massive-de-DE` and `summeval-consistency`; nimble leads `squad2` (p = 0.0226),
`vitaminc-dev` (p = 0.0001), `helpsteer2` and `pubmedqa`. The `civil_comments` artifact is re-confirmed
per record: nimble wins it on accuracy (p = 0.0006) with a positive recall of 0.50 against kev4's 0.72 -
it wins by predicting the majority class more often.

**Caveat that limits this test, and why `bespoke-suite-20261010-v1` exists:** the kev4/nimble rows were
measured before the RAM upgrade, while lev/kev0/laya were measured after, so these confidence intervals
describe "this run on that platform", not "the model". A platform-consistent pass is the remaining step.

### Resolved 2026-10-10: the suite is platform-invariant

`bespoke-suite-20261010-v1` re-ran kev4 and nimble after the upgrade. Result: **all 7,760 records are
identical** to the pre-upgrade run - same predictions, same correctness, every subset. Macro accuracy
0.744204 (kev4) and 0.756531 (nimble), matching the frozen numbers to six decimals. So the mixed-platform
concern was unfounded for this suite, the legacy rows stand as references, and the paired test above holds
as written.

### By metric family (never average these into one macro)

| family | subsets | records | kev4 | nimble | difference | paired p |
|---|---|---|---|---|---|---|
| `noul` (binary) | 5 | 1,399 | 0.8170 | 0.8320 | -0.0150 | 0.196 |
| `choice` | 5 | 1,848 | 0.8063 | 0.8220 | -0.0157 | 0.063 |
| `score` (argmax) | 3 | 633 | 0.4550 | 0.4882 | -0.0332 | 0.135 |

Nimble is nominally ahead in all three families and none is significant. The `noul` family splits by
metric, which is the `civil_comments` effect again: on accuracy nimble leads by 1.1 points, on balanced
accuracy kev4 leads by 0.8 (0.8048 vs 0.7969).

For the `score` family, argmax accuracy is a weak primitive, so the proper one is reported too -
`mean |prediction - target|`, lower is better: nimble 0.727, kev4 0.787, lev 0.856, kev0 1.090, laya 1.224.
The ordering is the same, so the score-family conclusion does not depend on the primitive. Every model
over-predicts the 5-point scale (mean prediction 2.58-3.50 against a mean target of 2.938).
