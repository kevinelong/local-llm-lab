# The resident budget above 8 GiB: +11.4 prefill tok/s per GiB to 8, about +20 above it, no ceiling at 16, and decode moves too

**One session, 2026-11-01, 07:38-08:00 local.** The 2026-10-31 and 2026-11-01-01:07 ladders both stopped at **8 GiB**,
not because 8 was an optimum but because the commit gate could not honour more. This run pushes the same design to
**16 GiB** and answers two questions: does the prefill slope hold above the old top rung, and does the engine's
per-allocation pinning ceiling (#4860: ~23 GiB) bite below it?

**Answer: the slope steepens above 8 GiB and nothing clamps - `granted == declared` and `resident_pinned: true` at
every rung from 2 to 16 GiB.** The headline numbers come from the **second run in this file (n=5 per rung, sec. 3)**,
which is the strongest design here: prefill at 16 GiB is **+23.8 %** over 8 GiB in the same run and **+41.1 %** over 2 GiB,
at **+19.6 tok/s per GiB from 8 to 16** against **+11.4** below 8. See sec. 3 for why it supersedes the first pass's
+15.8 and +20.5 %. The package is **engine 0.1.47** (staged harness `staged-strata-0.1.47`), pack
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

## 3. Second run, n=5 per rung: a steeper slope, and decode does move

Eighteen minutes after the first run, the same design was re-run with **5 repetitions per rung at 8, 12 and 16 GiB**
(`resident-ladder-n5-20261101`, 15 arms, 1,752 s wall, commit free 36.3-39.7 GiB). **Three arms are excluded for a
contended card** (`q8-r2`, `q12-r5`, `q16-r5` - the last waited **800 s** for a ComfyUI render and still decoded at
10.9 tok/s), and **one is excluded as an unflagged outlier**: `q12-r1` read **536.2 prompt / 41.1 decode**, 26 % below its
two clean rung-mates and outside anything the contention check saw. Every grant is clean in all 15: `12.0`/`16.0` GiB as
declared, `resident_pinned: true`, cache `1.93 GiB / 1500`.

| resident | n | prefill tok/s | decode tok/s | prompt sd | decode sd |
|---|---|---|---|---|---|
| 8 GiB | 4 | **659.1** | **68.4** | 8.6 | 7.1 (58.3-75.0) |
| 12 GiB | 3 | **727.3** | **76.7** | 3.6 | 5.1 (70.6-80.0) |
| 16 GiB | 4 | **815.6** | **80.1** | 7.8 | 5.6 (73.5-85.0) |

- **Prefill: 8 -> 12 +17.1, 12 -> 16 +22.1, 8 -> 16 +19.6 tok/s per GiB**, all inside one run with an order that
  alternates by repetition. **8 -> 16 is +156.5 tok/s, Welch t = 26.9** on n=4 per rung - not a noise question.
- **This supersedes the first pass's 8 -> 16 slope of +15.77** in one respect only: the first pass pooled rungs measured
  in three separate batches with unequal n (n=2 above 8), and it is noisier for it. The direction is the same in both
  (+11.4 below 8, steeper above), and the n=5 single-run fit is the one to quote.
- **Batch offset is real at the upper rungs:** 16 GiB read **779.2** (n=2, 07:50) and **815.6** (n=4, 08:35), a **+4.7 %**
  drift in 45 minutes; 12 GiB moved **+5.0 %** and 8 GiB only **+1.9 %**. That is why a slope is taken **within a run**
  and never by subtracting across batches.
- **Decode DOES move with the rung, and the earlier "decode does not travel" reading was an n=2 artifact.**
  68.4 -> 76.7 -> 80.1 tok/s from 8 to 16 GiB (**+11.7, Welch t = 2.58**, n=4 each) - a direction rather than a magnitude,
  because within a single rung at identical flags decode spans **58.3-75.0 (28 %)**. So the honest rule is narrower than
  the one this file first wrote: **decode needs n>=5 per rung in one run and a reported sd; it cannot be compared across
  days or batches at n=1-2, and nothing here justifies a per-GiB decode coefficient.**

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

**What the first pass could not say about decode, and the second run fixed.** At n=2 the 8 GiB row read **72.5** at
01:07 (5 reps) and **61.6** at 07:38 (2 reps) while prefill moved +0.6 %, which looked like a day-side offset. With n=4-5
per rung inside one run (sec. 3) decode instead reads **68.4 at 8 GiB and 80.1 at 16 GiB** with a **28 % spread inside a
single rung**. **Correction to this file's own first reading: it is not a day offset, it is variance** - a 2-arm rung
cannot resolve a 12 % difference in either direction. Decode is quotable per rung with n>=5 and an sd; it is not quotable
across batches, and the 16 GiB decode row of the first pass (75.8, n=2) stays withdrawn.

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
- `C:/Users/kevin/ai_bench/resident-ladder-n5-20261101/` - the n=5 run, 15 arms at 8/12/16 GiB, with the three
  contended arms and the one unflagged outlier named above.
- `C:/Users/kevin/ai_bench/lend-chunk-1024-20261101/` and `lend-chunk-4096-20261101/` - the two chunk arms, one process
  each, including the clamp line and the void reason for the 4096 request.
- Engine logs: `staged-strata-0.1.47/logs/chunk-q<rung>-r<n>-a1.log`, one per arm, with the argv echo, the grant lines,
  the lend region, and the commit readback. **Caveat found the hard way, and fixed the same day:** the log name was keyed
  on the arm label, not the evidence directory, so two runs that both used `q8-r1` overwrote each other's log - the second
  chunk arm overwrote the first one's. The parsed readback in each arm JSON survived, which is why the numbers here are
  complete. The name now carries the evidence directory as a tag (`chunk-<tag>-<label>-a<n>.log`, with the config file
  renamed to match), verified by two same-label runs producing two distinct files.
- Latest summary JSONs: `summary-20261101-010757.json`, `summary-20261101-074925.json`, `summary-20261101-075451.json`,
  `summary-20261101-075656.json`, `summary-20261101-075751.json`.
