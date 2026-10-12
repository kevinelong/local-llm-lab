# decision-signal-20261011: the stall signal every decision model missed is readable by a rule

The decision track has screened six models for one question - *is this agent repeating itself without
progress?* - and every one of them caught **0 of 4** labelled stalls: Laya on llama.cpp (0/4), Laya on
Colibrì (0/4, reproduced today with a mechanism: no signal, not high probabilities), kev4 (0/4), kev0 (0/4),
julia-1 (0/4). The one exception was a deterministic rule the lab wrote on 2026-09-25, recorded as
"identical-failure / no-successful-mutation", which caught **1/4 with 0/14 false alarms**.

This root re-derives that from the frozen features and tests what the signal actually is. **No inference, no
network** - it reads `natural-candidates.json`, `natural-labels.json` and Colibrì's Laya results only.

```
python rule_vs_models.py
```

## What the features contain

Each window carries an `audit` trail (every tool call with its input key and outcome) and a `repeatOutcomes`
pair for the repeated action. The discriminating fact is not the error flag:

| window | label | repeated outcome |
|---|---|---|
| natural-4 | stall | same `sha256` (`4a97225c…`) twice, `isError` **False** |
| natural-5 | stall | same `sha256` (`3aecf8ec…`) twice, `isError` **False** |
| natural-7 | stall | same `sha256` (`efefc15c…`) twice, `isError` **False** |
| natural-10 | stall | same `sha256` (`80cb348b…`) twice, `isError` **True** |
| natural-1 | not a stall | two repeats, **different** `sha256` |

So three of the four stalls repeat a *successful* action with byte-identical output. A rule requiring an
**error** to call it a stall necessarily misses them - which is exactly what the 2026-09-25 rule did.

## Rules, scored on the frozen labels

| rule | stalls caught | false alarms |
|---|---|---|
| R1 identical **error** repeat (as I reconstruct the 2026-09-25 rule) | 1/4 | 2/14 |
| R2 identical outcome, error-agnostic | **4/4** | 2/14 |
| R3 trail-wide: any repeated identical outcome anywhere | 4/4 | 3/14 |
| R5 R2 + no successful mutation | 3/4 | **0/14** |
| **R6 R2 + no DISTINCT successful outcome** | **4/4** | **1/14** |

The two false alarms R2 makes are `natural-2` and `natural-6`, and reading their trails shows why: each
repeats a command but also performs a *successful* `write` and `edit` with **different** outcome hashes in
between - i.e. repetition *with* progress. That is what the lab's original clause was for, and the sharper
version (R6) is the one that works: `natural-10`'s stall consists of three **identical successful** edits,
which is no progress at all, and R6 keeps it while dropping R2's false alarms.

## What this means

- **The signal is in the transcript, and a three-line rule reads it.** 4/4 at 1/14 against 0/4 for every
  neural decision head we have tested. The task is solvable; the models are the problem.
- **The models add nothing on top.** Combining R2 with Laya's `noul` at any threshold from 0.85 down to
  0.60 adds **zero** catches ("Laya-only additions: none") and below 0.70 adds seven false alarms.
- **Cost differs by four orders of magnitude.** The rule is arithmetic over a transcript: microseconds
  against Laya's 1562 ms median at the context these windows need.
- **A rule cannot do everything.** It fires only when a repeat with an identical outcome exists; an agent
  that stalls by *doing nothing*, or by drifting through many *distinct* failing actions, is invisible to it.
  That is the honest boundary, and it is also the reason a rule and a model might eventually be complementary
  rather than alternatives - but on this evidence the model half is not carrying its weight.

## Limits

- **Descriptive, not validation.** The clauses and thresholds here were chosen while looking at these 18
  windows, so R2/R5/R6 are fitted to them; only R1 is a re-derivation of a rule frozen before this analysis.
  A real detector needs a fresh labelled set, and the lab's rule applies - do not tune on these labels and
  call the result validation.
- 4 positives and 14 negatives is a very small sample: one window is 25 points of catch rate.
- The windows were selected *because* they contain a repeated action, so the base rate here is far higher
  than in a live agent session, and precision would look worse in deployment.
- Nothing here was run against a live engine; it is an analysis of frozen artifacts, and no gate was touched.
