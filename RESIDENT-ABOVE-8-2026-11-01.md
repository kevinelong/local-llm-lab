# The resident budget above 8 GiB: +11.4 tok/s per GiB to 8, +15.8 above it, and no ceiling reached at 16

**One session, 2026-11-01, 07:38-08:00 local.** The 2026-10-31 and 2026-11-01-01:07 ladders both stopped at **8 GiB**,
not because 8 was an optimum but because the commit gate could not honour more. This run pushes the same design to
**16 GiB** and answers two questions: does the prefill slope hold above the old top rung, and does the engine's
per-allocation pinning ceiling (#4860: ~23 GiB) bite below it?

**Answer: the slope steepens (+15.8 against +11.4 tok/s per GiB) and nothing clamps - `granted == declared` and
`resident_pinned: true` at every rung from 2 to 16 GiB.** Prefill at 16 GiB is **+20.5 %** over 8 GiB and **+34.8 %** over
2 GiB, on an identical prompt and flags. The package is **engine 0.1.47** (staged harness `staged-strata-0.1.47`), pack
`q2_0`, `--prefill 2048 --spec 4 --spec-min-p 0.5 --kv int8 --pool-workers 15 --max-context 65536`, model
`Qwen3.8-Flash-Next-GSQ-RCO-Q2_0`, one process per arm, prompts of **19,769 tokens**, 64 generated.

## Design, unchanged from 2026-10-31 except the rungs

`resident_ladder_seq.py --rungs 8,10,12 --reps 2` then `--rungs 12,14,16 --reps 2`, `--reserve 900 --cache 1500`,
port 8091, ComfyUI polled at `127.0.0.1:8006`. Each arm is a fresh process, waits for the card and for commit, and is
gated at `rung + 18.35 GiB` free commit (process 13.60 + engine overhead 4.25 + slack 0.5). Order alternates by
repetition, so a warm card cannot favour one rung.

**Gates at start:** free physical **37.3-44.5 GiB**, commit free **34.3-35.3 GiB**, VRAM free **9,876-10,932 MiB**,
ComfyUI idle. Total wall: **559 s for six arms** (the first batch waited 22-148 s per arm for a ComfyUI render), then
**309 s for six** on an idle card.

## The arms

| resident | n | prefill tok/s | decode tok/s | granted | pinned | cache | lend in RAM | commit left |
|---|---|---|---|---|---|---|---|---|
| 2 GiB | 5 | **578.0** | 62.2 | 2.0 | true | 1.93 GiB / 1500 | 0 of 790 | 20.4 |
| 4 GiB | 5 | **600.4** | 66.6 | 4.0 | true | 1.93 / 1500 | 0 of 790 | 18.4 |
| 6 GiB | 5 | **622.6** | 69.5 | 6.0 | true | 1.93 / 1500 | 0 of 790 | 16.4 |
| 8 GiB | 7 | **646.5** | 69.4 | 8.0 | true | 1.93 / 1500 | 0 of 790 | 14.4 |
| 10 GiB | 2 | **683.2** | 69.6 | 10.0 | true | 1.93 / 1500 | 0 of 790 | 16.2 |
| 12 GiB | 2 | **692.8** | 64.2 | 12.0 | true | 1.93 / 1500 | 0 of 790 | 14.3 |
| 14 GiB | 2 | **733.1** | 63.9 | 14.0 | true | 1.93 / 1500 | 0 of 790 | 12.3 |
| 16 GiB | 2 | **779.2** | 75.8 | 16.0 | true | 1.93 / 1500 | 0 of 790 | 10.3 |

Rows 2-8 are the **2026-11-01T01:07** idle ladder (5 reps each) plus the two 8 GiB arms from tonight, which is why that
row has n=7; the rest are new. Every arm answered **`42`** and decode acceptance sat at **20-25** with no trend, so the
speed change is not a different answer.

**Two arms are excluded and both are named, not silently dropped:** `q12-r1` was granted **220 of 1500** expert-cache
slots (0.28 GiB instead of 1.93) and is **void by the declared-cache rule**; `q12-r2` decoded at **16.8 tok/s** with the
card **contended** by the ComfyUI render that was running at the time. The 12 GiB rung is therefore reported from the
clean re-run (691.0 and 694.5 tok/s), not from the batch it first appeared in.

## The curve, and the thing it changes

- **2 -> 8 GiB: +11.39 tok/s per GiB, R^2 = 1.000** over 22 arms; the three 2 GiB segments read **+11.2, +11.1, +11.3**,
  which reproduces the 2026-10-31 file's **+11.2** from an independent night.
- **8 -> 16 GiB: +15.77 tok/s per GiB, R^2 = 0.963** over 13 arms. The single weakest segment is 10 -> 12 (+4.8), and the
  two strongest are 12 -> 14 (**+20.2**) and 14 -> 16 (**+23.1**); at n=2 per rung the 10 GiB pair is the only point
  more than 1.2 % off the fit (+1.2 %, while 12 GiB sits -2.0 %).
- **Nothing clamps.** `resident_granted_gib` equals the declared value at every rung and `resident_pinned` is **true**
  throughout: no `page-locking refused` line, no pageable fallback, no silent shrink. #4860's ~23 GiB
  per-allocation ceiling is **not reached and therefore not tested** by this run.

**What this changes for how we quote numbers.** Every prefill figure in this lab so far was measured between 2 and 8 GiB
resident, where the lever looks like +11 tok/s per GiB and is worth 12 %. Above 8 GiB it is worth **+15.8 per GiB and
20.5 % in total**, so a prefill number that does not declare its resident rung is under-specified by up to a fifth - the
same class of error as quoting a decode rate without a numerator. **Rule: a prompt/prefill number carries
`resident=`, `prefill=`, `cache=` and `reserve=`, or it is not comparable.**

**Why it might steepen `[INFERENCE]`.** The engine's own lend line says the prompt path borrows 790 cache slots and that
**0 of them** keep experts in RAM at every rung (sec. below), so the prompt read is served through the file cache rather
than from the resident copy. A larger resident region shrinks what the prompt path has to reach for *in the pack*, and
the 19,769-token prompt is long enough for that to dominate. Not measured - the file-cache/SSD split is not split out
per arm.

**What is not quotable:** **decode**. Same rung, same flags, two nights: 8 GiB reads **72.5** on 2026-11-01T01:07 and
**61.6** tonight (-15 %), while prefill moves **645.3 -> 649.5 (+0.6 %)**. The 2026-10-31 file recorded a 12 % day-to-day
offset; it is real, it is now known to be **decode-side**, and until it is characterised decode stays **within-run only**.
The 16 GiB decode row (75.8) is two arms and must not be quoted as a rung advantage.

## The lend region: still 0 of 790, and the engine says why

At **every** rung from 2 to 16 GiB the engine prints the same three lines, so this is a property of the box and the pack,
not of the budget:

```
FileExpertSource: the prompt path's lend region: 0 of its 790 slots keep their experts in RAM too
                  (0.00 GiB of the budget's remaining 0.00 GiB)
FileExpertSource: WARNING: 790 of 790 lendable slots (100%) will read their experts from the pack during a long prompt;
                  expect a slower prompt read on 50K+ token prompts (one measurement: 18% uncovered cost 26%).
                  Raise --resident-budget-gib (the lend region comes after the ranked experts) and restart
strata generate: WARNING: a prompt chunk of 2048 tokens lends 790 cache slots to the prompt path, but only 0 of their
                  experts fit in RAM ... A larger --resident-budget-gib ..., or a smaller --prefill, keeps them all in RAM
```

**The budget is fully spent before the lend region is served:** *"0.00 GiB of the budget's remaining"* at 2, 8, 10 and
16 GiB alike. The ranked expert set is **24,576 pairs** and consumes whatever is declared, so the lend region never sees
a remainder - which means the engine's suggested fix ("raise `--resident-budget-gib`") cannot be reached on this box:
covering the lend region needs a budget with a remainder *after* 24,576 ranked pairs, and the commit gate caps us at
~17 GiB.

**The other suggested lever was tested and it fails in the useful direction.** Two arms at resident 8 GiB, one process
each, reading the lend line back:

| `--prefill` asked | granted | lend slots | of those in RAM | prefill tok/s |
|---|---|---|---|---|
| 1024 | 1024 | **498** | **0** | **494.9** |
| 2048 | 2048 | 790 | 0 | **646.5** (n=7) |
| 4096 | **2048** (clamped) | 790 | 0 | 661.4 (void: prefill clamped) |

A halved chunk halves the lend *count* (790 -> 498) and moves **nothing** into RAM, while costing **-23.4 %** prefill
(494.9 against 646.5). So "a smaller `--prefill` keeps them all in RAM" is **not true here** - the coverage is a function
of the budget remainder, and the chunk only changes how many slots are exposed. The `4096` request is refused at this
cache and resident (**"prompt chunk 4096 -> 2048 tokens so its buffers fit in every expert cache"**), which reproduces the
2026-10-31 clamp from a different night.

**What this means for the numbers above, stated as a limit rather than a correction.** Every prefill row in this file,
including the 16 GiB one, was measured with the lend region **100 % uncovered**. The engine's own note prices an 18 %
uncovered region at **26 %** of prompt time; ours is 100 % uncovered, so the absolute prefill values here carry an
unquantified penalty of that family `[INFERENCE - the 18 %/26 % row is not linear and is not extrapolated here]`. What is
*not* affected is the **comparison between rungs**: coverage is 0 % at every rung, so the +15.8 per GiB slope is measured
with that tax held constant. What *is* affected is any cross-source prefill comparison, ours included.

## Open questions this run creates

1. **The 24 GiB ceiling test is out of reach on commit, not on RAM.** 24 GiB needs **42.35 GiB** free commit; the box
   peaks at ~35.3 GiB with the desktop as it is. Raising the page file would change that, and it is a system change, so it
   is Kevin's call. Until then #4860 stays a third-party measurement we cite rather than one we hold.
2. **Where the slope breaks between 16 and 24 GiB is unknown**, and 16 is the highest rung the box can honour today
   (`rung + 18.35 <= 35.3` -> **17.0 GiB** is the arithmetic ceiling).
3. **Decode needs n>=5 per rung inside one run** before the 8-16 range says anything about decode; tonight's two-rep
   rows are noise, as the 63.9/75.8 spread shows.
4. **The lend region is unfixable on this box today**, and that is now a measured statement rather than a guess: the only
   levers the engine names are a resident budget with a remainder after 24,576 ranked pairs (out of commit reach) and a
   smaller `--prefill` (tested, -23.4 % prefill, 0 % coverage gained). The remaining question is whether a **different
   pack** with fewer ranked pairs would leave a remainder at 16 GiB - cheap to check by reading the ranked count from the
   profile line, no arm needed.

## Evidence

- `C:/Users/kevin/ai_bench/resident-ladder-idle-20261101/` - the 01:07 ladder, 2/4/6/8 GiB, 5 reps (frozen).
- `C:/Users/kevin/ai_bench/resident-ladder-commit-20261101/` - tonight, 8/10/12 GiB, 2 reps, includes the two excluded
  12 GiB arms with their void reasons.
- `C:/Users/kevin/ai_bench/resident-ladder-commit2-20261101/` - tonight, 12/14/16 GiB, 2 reps, the clean upper curve.
- `C:/Users/kevin/ai_bench/lend-chunk-1024-20261101/` and `lend-chunk-4096-20261101/` - the two chunk arms, one process
  each, including the clamp line and the void reason for the 4096 request.
- Engine logs: `staged-strata-0.1.47/logs/chunk-q<rung>-r<n>-a1.log`, one per arm, with the argv echo, the grant lines,
  the lend region, and the commit readback. **Caveat found the hard way:** the log name is keyed on the arm label, not the
  outdir, so two runs that both use `q8-r1` overwrite each other's log - the second chunk arm overwrote the first one's.
  The parsed readback in each arm JSON survived, which is why the numbers here are complete; the next runner change is to
  put the outdir in the log name.
- Latest summary JSONs: `summary-20261101-010757.json`, `summary-20261101-074925.json`, `summary-20261101-075451.json`,
  `summary-20261101-075656.json`, `summary-20261101-075751.json`.
