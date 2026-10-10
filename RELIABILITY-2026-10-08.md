# Reliability by ending, not by score: how often does each model declare victory wrongly?

2026-10-08, overnight. `census_endings.py` classifies every task session on disk (223 sessions, all root
families) by how its final assistant turn read, then asks the question the scores cannot: **when a model
writes a completion summary, how often has it actually passed every check?**

"Honest" below is `summary-all-passed / (summary-all-passed + summary-with-failures)` over the sessions
that produced an evaluation (smoke sessions are excluded - 53 of them have no evaluation at all, and the
first version of this census wrongly counted them as failures).

| model | sessions judged | honest | truncated | killed | checks passed |
|---|---|---|---|---|---|
| Kolibri-1 78B | 16 | **75 %** | 3 | 5 | 2029/2050 = **99.0 %** |
| Qwen3.6-35B-A3B | 29 | **62 %** | 3 | 1 | 2661/2713 = 98.1 % |
| Nemotron-3.5-Lightning-30B | 13 | **62 %** | 1 | 5 | 1716/1753 = 97.9 % |
| Swift Bonsai 2 PQ2 | 4 | 100 % (n=4) | **4** | 2 | 794/892 = 89.0 % |
| MiniCPM5-2B | 25 | **52 %** | 4 | 3 | 2208/2753 = 80.2 % |
| gpt-oss-20b | 18 | **28 %** | 0 | 0 | 1221/1449 = 84.3 % |
| Qwen3-Coder-30B | 9 | **11 %** | 0 | 0 | 603/663 = 91.0 % |
| Gemma / Qwen3-Thinking | 3 each | 0 % | 1 / 0 | 4 / 0 | poor |

Whole history: **61 honest completions, 59 premature ones, 25 truncated, 20 killed, 3 error.**

## What this says that the scores do not

1. **The score hides the modelling failure that matters most.** `qwen3-coder-30b` passes 91 % of its
   checks and is honest only **11 %** of the time - it summarises after nearly every incomplete attempt.
   `gpt-oss-20b` - the fastest configuration in the lab - is honest **28 %** of the time at 84 % checks.
   Both would look "fine" in a table of scores.
2. **The top three separate on this axis too, in the same order as the extended suite**: Kolibri 75 %,
   Qwen3.6 62 %, Nemotron 62 %. Qwen3.6's 62 % comes with only **1 killed session** out of 33, against
   Kolibri's 5 of 24 and Nemotron's 5 of 20 - it is the cheapest of the three in harness terms as well.
3. **Swift's 100 % honesty rests on four sessions** and comes with the worst truncation rate in the set
   (4 of 10 sessions died mid-thinking) - the reply-cap class, now fixed by the raised cap and the
   thinking budget, which is why its newest runs are clean.
4. **`spark` and `ling` never produced a usable session** (6 of 6 and 3 of 3 truncated), so their low
   scores are a harness story rather than a model verdict - exactly the class the cap fix addresses.

## How to use it

- Quote **honesty** beside the checks total for any model we describe as usable: "99 % of checks" without
  it can mean a model that finishes correctly, or one that stops early and says it is done.
- Treat a low honesty score as the signature to investigate first on a new model: it costs one census
  run (5 s, read-only) and no GPU time.
- The metric is retrospective - it reads `events.jsonl` and `result.json` only - so it can be recomputed
  for any new root as soon as its sessions land.
