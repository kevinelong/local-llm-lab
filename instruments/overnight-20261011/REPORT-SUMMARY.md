# Overnight summary, from the queue artifacts

Queue: 2026-10-11, overnight (queue complete)

| item | exit | seconds | prediction recorded before the run |
|---|---|---|---|
| `i1-strata-placement` | 0 | 696 | replies differ on 20-60% of items; letters differ on at most 3 of 93; correctness within 2 |
| `i2-kolibri-knowledge` | 0 | 1658 | within 3 points of the two leaders (85-92%); GSM8K not worse than MMLU |
| `i3-colibri-qwen36` | -9 | 7200 | accuracy inside 2 points of 88.5%; wall time is the interesting number |
| `i4-reason-repeat` | 0 | 1109 | 90/93 and 92/93 again |
| `i5-papers-repeat` | 0 | 323 | Qwen3.6 one distinct topic, Strata two or three |
| `i6-gliner-replay` | 1 | 1852 | warm p95 20-35 s, 0/4 stalls caught |

## i1 placement versus output (Strata, 2 GiB vs 8 GiB resident)
Same 93 shared-correct items, everything else identical: **65 of 93 replies differ**, chosen letters differ on **0**, correctness **92 vs 92** ({'2': 0, '8': 0}).
Differing item ids: mmlu/astronomy/10, mmlu/astronomy/11, mmlu/astronomy/12, mmlu/astronomy/13, mmlu/astronomy/14, mmlu/astronomy/15, mmlu/astronomy/16, mmlu/astronomy/17, mmlu/astronomy/19, mmlu/astronomy/2, mmlu/astronomy/23, mmlu/astronomy/24, mmlu/astronomy/26, mmlu/astronomy/29, mmlu/astronomy/3, mmlu/astronomy/30, mmlu/astronomy/31, mmlu/astronomy/32, mmlu/astronomy/34, mmlu/astronomy/37, mmlu/astronomy/38, mmlu/astronomy/39, mmlu/astronomy/40, mmlu/astronomy/41, mmlu/astronomy/42, mmlu/astronomy/44, mmlu/astronomy/46, mmlu/astronomy/47, mmlu/astronomy/48, mmlu/astronomy/49, mmlu/astronomy/5, mmlu/astronomy/50, mmlu/astronomy/51, mmlu/astronomy/52, mmlu/astronomy/53, mmlu/astronomy/54, mmlu/astronomy/55, mmlu/astronomy/56, mmlu/astronomy/58, mmlu/astronomy/59, mmlu/astronomy/6, mmlu/astronomy/60, mmlu/astronomy/61, mmlu/astronomy/62, mmlu/astronomy/65, mmlu/astronomy/66, mmlu/astronomy/67, mmlu/astronomy/68, mmlu/astronomy/69, mmlu/astronomy/70, mmlu/astronomy/72, mmlu/astronomy/73, mmlu/astronomy/75, mmlu/astronomy/82, mmlu/astronomy/83, mmlu/astronomy/84, mmlu/astronomy/85, mmlu/astronomy/89, mmlu/astronomy/9, mmlu/astronomy/90, mmlu/astronomy/92, mmlu/astronomy/94, mmlu/astronomy/96, mmlu/astronomy/98, mmlu/astronomy/99

## i2 Kolibri-1 78B on the 1,100-item knowledge set
**901/1100 = 81.9%** in 1607 s (1.46 s per item), 199 failures.
- per_subject: {'high_school_world_history': {'n': 100, 'passed': 86}, 'high_school_geography': {'n': 100, 'passed': 81}, 'astronomy': {'n': 100, 'passed': 82}, 'world_religions': {'n': 100, 'passed': 81}, 'philosophy': {'n': 100, 'passed': 80}, 'prehistory': {'n': 100, 'passed': 71}, 'virology': {'n': 100, 'passed': 51}, 'international_law': {'n': 100, 'passed': 84}, 'grade_school_math': {'n': 300, 'passed': 285}}
- for reference: Qwen3.6-35B-A3B Q4 88.5%, Strata Q2_0 89.7%

## i3 Colibri Qwen3.6-35B-A3B (same 1,100 items, second engine)
no result - the item timed out at 7200 s; see logs/i3-colibri-qwen36.log

## i4 reasoning repeat
- first run was qwen36 90/93 and strata 92/93

## i5 paper form repeated
- qwen36-deep-rep1: 3 papers, **1 distinct topics**, 408 mean words
  - The Case for Preserving Mars: A Scientific Imperative for Planetary Protection
  - The Case for Preserving Mars: A Scientific Imperative for Planetary Protection
  - The Case for Preserving Mars: A Scientific Imperative for Planetary Protection
- strata-deep-rep1: 3 papers, **1 distinct topics**, 429 mean words
  - The Case for In Situ Resource Utilization as the Primary Driver of Mars Exploration
  - The Case for In Situ Resource Utilization as the Primary Driver of Mars Exploration
  - The Case for In Situ Resource Utilization as the Primary Driver of Mars Exploration
- first run: qwen36 1 distinct topic, strata 2

## i6 GLiNER2.5-Decide on Colibri
no result - the item exited 1; see logs/i6-gliner-replay.log

