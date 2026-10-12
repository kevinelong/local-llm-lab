# strata-warmcache-20261011: does warming the expert cache buy speed on our own engine?

Three independent sources say the *expert cache* is the lever, not the engine: Colibrì fills its device tier
"from the experts your past conversations used" and measured a first run going from ~6 to 11 tok/s once the
tier was pre-filled (#1919); the unmerged llama.cpp proposal measured a calibrated hot set at a **42 %** hit
rate against **6 %** uncalibrated; and our own Strata already ships `--expert-cache auto` plus an
`--expert-profile` artifact, so the mechanism exists in the engine we run. The open question was whether
*our* workload matches what that profile knows.

## Design

One engine process, the lab's declaration unchanged (`strata-q2_0.json`: `--expert-cache auto`, `--spec 4`,
`--mtp`, `--kv int8`, `--max-context 65536`, **`--resident-budget-gib 2`**, `--vram-reserve-mib 2000`):

1. **cold** - a fixed probe prompt (160 tokens, temperature 0), three times, immediately after load;
2. **warm-up** - four to eight prompts drawn from the same domain (our own frozen astronomy knowledge items,
   so their hot experts should overlap the probe's);
3. **warm** - the same probe, three times again.

Reported: per-probe wall time and tokens/second, time to first byte, whether the three probe outputs within a
phase are identical (a placement/output check), and the `expert-profile.bin` size and mtime before and after.

## Results, two runs

| run | phase | probe totals (ms) | median | tok/s | identical outputs |
|---|---|---|---|---|---|
| 1 (8 warm-ups) | cold | 35109 / 23391 / 22297 | 23391 | 6.84 | yes (vacuous - see the bug) |
| 1 | warm | 28079 / 21968 / 21860 | 21968 | 7.28 | yes (vacuous) |
| 2 (4 warm-ups) | cold | 34391 / 26422 / 22421 | 26422 | 4.65 / 6.06 / 7.14 | **yes, 657/703/669 chars** |
| 2 | warm | 28328 / 22531 / 23109 | 23109 | 5.65 / 7.10 / 6.92 | **yes, prefix-identical** |

## What it shows

- **The warm-up does not measurably help.** In each run the *first* probe is the outlier (~1.5x slower than
  its own phase's steady state), and after excluding it, cold and warm sit in the same 22-23 s band. The
  spread *within* a phase (4.65 to 7.14 tok/s) is larger than the difference between phases. A same-domain
  warm-up of 4-8 prompts changes nothing at this resident budget.
- **The engine does not persist a learned profile.** `expert-profile.bin` is byte-for-byte unchanged after
  both runs (size 196632, mtime 1791401663.71 == the pack's own file, dated 2026-10-07). Whatever calibration
  exists is in-process only, which is consistent with the warm-up having no carry-over.
- **Our engine is deterministic for this prompt and length**: the three cold probes produced byte-identical
  text, three times, in run 2. That is worth stating next to the earlier finding that long *free-form* outputs
  varied across repeats (the documents/reasoning path) - so the instability is prompt- and length-dependent,
  not a property of the engine as such.
- **Steady-state decode here is 6-7 tok/s**, matching the 6.5-9.6 tok/s this lab recorded for the same engine
  and pack on the same card - a useful consistency check on a much smaller instrument.

## A trap worth remembering

The first run logged **0 characters** on every probe and "identical outputs: true". This engine puts its
tokens in `reasoning_content`, a behaviour this lab recorded earlier and which the collector did not
implement, so the identity check was comparing empty strings to each other. Any tool that reads this
endpoint must collect `delta.reasoning_content` (and `content`) or it will silently measure nothing. The
second run fixed that: 657-703 characters per probe.

## Limits and what a real calibration test would need

- n=3 probes per phase, one prompt, one model, one resident budget (2 GiB - note the 2026-10-08 work used
  12 GiB for a different question), and a warm-up of only 4-8 prompts. A negative at this scale is not a
  general negative about calibration.
- The honest next levers, in order of cost: (a) a much larger warm-up (hundreds of prompts) to fill a 2 GiB
  tier many times over; (b) a larger `--resident-budget-gib`, where a bigger cache makes a better hot set
  matter more; (c) the llama.cpp route once `-ehs`/`--expert-hot-s` merges, since that proposal quantifies
  the effect on the same model family. None of them is started.
- No gate, floor or frozen artifact was touched. The engine was stopped after each run; verification shows
  no listener on 8080 and no `strata` process.
