# bespoke-suite-20261010-v1: kev4 and nimble on the 64 GB platform

Same published suite (3,880 records, 13 subsets) and the same runner as the two earlier roots, in a new
root for one reason: **the existing kev4 and nimble rows were measured on 2026-10-05/06, before the RAM
upgrade to 64 GB on 2026-10-07.** lev, kev0 and laya were measured after it, so the current five-model
table mixes platforms - exactly what the lab's platform-change rule says not to do.

`run.py` and `suite_worker.py` are byte-identical to `bespoke-suite-20261007-v1` (and therefore to
`bespoke-suite-20261005-v1`), sha256-verified on copy:

- run.py          4fd31f06bfc1af025bb1624ea4deb6aa297bfe9e6b048e30dd1613d2a3c13eac
- suite_worker.py 36d2ad1a20dbc17abc3806671fc0f2b78e8f9a65f400d3bc9db07cef93aa893d

Inherited declarations, unchanged: llama.cpp b11429 over `/v1/systemone`, the 8.0 GiB worker-private cap
declared in `decisions-20261005-v3/run.py`, runtime floors 3 / 2 / 0.5 GiB, per-model batch/slot flags
from that registry (`kev4` and `nimble` both `-np 1 -b 512 -ub 512`), wall 7200 s per model.

Scope: `kev4` and `nimble`, one at a time.

```
python C:/Users/kevin/ai_bench/bespoke-suite-20261010-v1/run.py preflight
python C:/Users/kevin/ai_bench/bespoke-suite-20261010-v1/run.py screen kev4|nimble
python C:/Users/kevin/ai_bench/bespoke-suite-20261010-v1/run.py audit
```

## Reporting, and what will be done with the numbers

The 2026-10-08 note established (and `../bespoke-metric-20261010/` re-derives from the frozen rows) that
plain accuracy on a skewed subset is a majority-class measurement: `civil_comments` is 32 positive of
300, so 89.3 % is the baseline. Every subset here is therefore reported as **accuracy, balanced accuracy,
positive prediction rate and majority baseline**, and the two metric macros are kept apart.

Plan, in order:

1. One pass each, to place kev4 and nimble on the 64 GB platform.
2. If the paired picture still leaves the two within noise, a second pass each - which doubles as the
   suite-scale determinism check the lab has so far only run on the 18-window set (two bit-identical
   passes there).
3. Comparison against the frozen rows with a paired test (`../bespoke-metric-20261010/paired.py`), not by
   eyeballing two macros: both models answer the same records, so the difference is paired.
4. A platform-consistent five-model table (kev4, nimble here; lev, kev0, laya from
   `bespoke-suite-20261007-v1`) under one metric.

Boundaries: one inference workload at a time, no second agent, no app kills, no gate change, no reboot,
no threshold tuning, no promotion. No deletion: the models are already staged and the disk has ~103 GiB
free, so nothing is removed to make room.
