# Queue, 2026-10-16, from the news scan's ranked shortlist

Execute local-llm-lab/NEWS-2026-10-16.md section 8 in order: the Strata KV-residency A/B, the llama.cpp --moe-cache-mib ladder on a staged b11480 build, a per-workload noise floor, a calibrated expert-cache warm test, Ollama 0.40.4's native decision-model path, Coder IQ1_M, and the reference model on Strata 0.1.44 (gated). Serial, one inference workload at a time, gates checked and never lowered, predictions recorded before each run and scored after.

## q1-strata-kv-residency - Does KV residency change the numbers at fixed capacity?

Strata pinned at --kv int8 --max-context 65536 --resident-budget-gib 2, --kv-resident versus --kv-streaming: do the answers move, or only the rate?

Prediction recorded before the run: Letters unchanged; rate better with residency; if letters move, determinism outranks speed.

- dry run: not started.

## q2-moe-cache-mib-ladder - Ladder --moe-cache-mib on the staged b11480 build

On --cpu-moe Qwen3.6-35B-A3B Q4_K_M with 12 GB VRAM, what does each rung buy?

Prediction recorded before the run: Non-monotonic, peaking in the low thousands of MiB: 0 -> ~35-40 tok/s, a rung at 256-2048 best, the top rung at or below the control.

- dry run: not started.

## q3-noise-floor - A per-workload noise floor before trusting any tune

How much do two identical runs differ, in wall time and in checks?

Prediction recorded before the run: Small in checks for the deterministic tasks, large enough in wall time to swallow a 5% speed claim.

- dry run: not started.

## q4-calibrated-warm-cache - Warm the expert cache from a calibrated hot set at fixed capacity

Our 2026-10-11 warm test warmed with prompts and persisted nothing; does a calibrated hot set raise the hit rate and move decode, and does it move the letters?

Prediction recorded before the run: Hit rate up (toward the 42% the calibration literature reports from 6% random) and decode better; letters unchanged.

- dry run: not started.

## q5-ollama-decision-path - Ollama 0.40.4's native decision-model path

Does the native path change the 0/4 stall catch rate or the latency on the frozen 18 windows?

Prediction recorded before the run: Catch rate stays 0/4 (the model is the failure, now measured on two engines); latency nearer Colibri's 1.7-2.1 s median than our 27.56 s p95.

- dry run: not started.

## q6-coder-iq1-m - SKIPPED

Declared not runnable: parked

## q7-reference-on-strata-0144 - SKIPPED

Declared not runnable: open issue Niko1221/Strata#2747 (2026-10-16T09:31:46Z): Qwen3.6A3B fails with out of memory with recommended configs


**Dry run complete** at 2026-10-16 09:28:28.

**Not started:** inference slot busy: an engine is listening on port 8000, so a measured run is still in flight. Wait for it, then run this queue unchanged.

## q1-strata-kv-residency - Does KV residency change the numbers at fixed capacity?

Strata pinned at --kv int8 --max-context 65536 --resident-budget-gib 2, --kv-resident versus --kv-streaming: do the answers move, or only the rate?

Prediction recorded before the run: Letters unchanged; rate better with residency; if letters move, determinism outranks speed.

- finished in 3585 s: ok

  - 2026-10-16 12:09:07  arm kv-resident-32768: config strata-cfg-kv-resident-32768.json
  - 2026-10-16 12:09:16  healthy
  - 2026-10-16 12:09:39  run: C:\Program Files\Python311\python.exe C:\Users\kevin\ai_bench\new-items-20261007\knowledge_deep.py --url http://127.0.0.1:8080 --model strata-coder --label q1-kv-resident-32768 --forms reason --limit 93 --pool shared --seeds 1 --timeout 300
  - 2026-10-16 12:37:21    | strata-coder             -> knowledge-deep-result-q1-kv-resident-32768.json
  - 2026-10-16 12:37:21    |   reason : letters 92/93  mean distractors addressed 1.96
  - 2026-10-16 12:37:21  arm kv-resident-32768: letters 92, wall 22.5s, engine says 8.4
  - 2026-10-16 12:37:34  port 8080 cleared
  - 2026-10-16 12:37:34  wrote result-q1-strata-kv-residency.json

## q2-moe-cache-mib-ladder - Ladder --moe-cache-mib on the staged b11480 build

On --cpu-moe Qwen3.6-35B-A3B Q4_K_M with 12 GB VRAM, what does each rung buy?

Prediction recorded before the run: Non-monotonic, peaking in the low thousands of MiB: 0 -> ~35-40 tok/s, a rung at 256-2048 best, the top rung at or below the control.

- finished in 2069 s: ok

  - 2026-10-16 13:07:28    |   reason : letters 90/93  mean distractors addressed 2.48
  - 2026-10-16 13:07:28  rung 2048 MiB: 61.3 tok/s (engine), wall 3.0s, letters 90
  - 2026-10-16 13:07:53  healthy
  - 2026-10-16 13:07:56  run: C:\Program Files\Python311\python.exe C:\Users\kevin\ai_bench\new-items-20261007\knowledge_deep.py --url http://127.0.0.1:11436 --model qwen3.6-35b-a3b --label q2-cache-4096 --forms reason --limit 93 --pool shared --seeds 1 --timeout 300
  - 2026-10-16 13:12:03    | qwen3.6-35b-a3b          -> knowledge-deep-result-q2-cache-4096.json
  - 2026-10-16 13:12:03    |   reason : letters 90/93  mean distractors addressed 2.48
  - 2026-10-16 13:12:03  rung 4096 MiB: 73.6 tok/s (engine), wall 2.6s, letters 90
  - 2026-10-16 13:12:12  wrote result-q2-moe-cache-mib-ladder.json

## q3-noise-floor - A per-workload noise floor before trusting any tune

How much do two identical runs differ, in wall time and in checks?

Prediction recorded before the run: Small in checks for the deterministic tasks, large enough in wall time to swallow a 5% speed claim.

- finished in 52 s: ok

  - 2026-10-16 13:12:37  healthy
  - 2026-10-16 13:12:50  control run 1: 47.8 tok/s, wall 3.7s
  - 2026-10-16 13:13:02  healthy
  - 2026-10-16 13:13:15  control run 2: 47.5 tok/s, wall 3.7s
  - 2026-10-16 13:13:15  wrote result-q3-noise-floor.json
  - 2026-10-16 13:13:15  spread: {"rate_tok_s": [47.80494140737747, 47.53199815252988], "rate_spread_pct": 0.5709519702611079, "wall_s": [3.73, 3.73], "wall_spread_pct": 0.0}

## q4-calibrated-warm-cache - Warm the expert cache from a calibrated hot set at fixed capacity

Our 2026-10-11 warm test warmed with prompts and persisted nothing; does a calibrated hot set raise the hit rate and move decode, and does it move the letters?

Prediction recorded before the run: Hit rate up (toward the 42% the calibration literature reports from 6% random) and decode better; letters unchanged.

- finished in 62 s: ok

  - 2026-10-16 13:14:00  warm-up 3/8 sent
  - 2026-10-16 13:14:03  warm-up 4/8 sent
  - 2026-10-16 13:14:05  warm-up 5/8 sent
  - 2026-10-16 13:14:08  warm-up 6/8 sent
  - 2026-10-16 13:14:10  warm-up 7/8 sent
  - 2026-10-16 13:14:13  warm-up 8/8 sent
  - 2026-10-16 13:14:27  port 8080 cleared
  - 2026-10-16 13:14:27  wrote result-q4-calibrated-warm-cache.json

## q5-ollama-decision-path - Ollama 0.40.4's native decision-model path

Does the native path change the 0/4 stall catch rate or the latency on the frozen 18 windows?

Prediction recorded before the run: Catch rate stays 0/4 (the model is the failure, now measured on two engines); latency nearer Colibri's 1.7-2.1 s median than our 27.56 s p95.

- finished in 1 s: exit 3

  - 2026-10-16 13:14:38  wrote result-q5-ollama-decision-path.json
  - BLOCKED: no decision model is present in Ollama. Pull one first:
  -     ollama run nimble
  - then re-run this item. Nothing was downloaded by this queue.

## q6-coder-iq1-m - SKIPPED

Declared not runnable: parked

## q7-reference-on-strata-0144 - SKIPPED

Declared not runnable: open issue Niko1221/Strata#2747 (2026-10-16T09:31:46Z): Qwen3.6A3B fails with out of memory with recommended configs


**Queue complete** at 2026-10-16 13:14:45.

## Scoring, 2026-10-16 (predictions were in queue.json before any of it ran)

**q1 - Strata KV residency: confirmed, and the mechanism is visible in the engine's own numbers.** The
prediction was "letters unchanged; rate better with residency; if letters move, determinism outranks
speed". At a fixed `--resident-budget-gib 2`, `--kv int8`, `--max-context 65536` on both arms:

| arm | letters | decode | prefill | expert-cache hit |
|---|---|---|---|---|
| base (`--expert-cache auto`, KV where the engine puts it) | 92/93 | 7.3 tok/s | 18.9 tok/s | 46.8 % |
| `--kv-resident 32768` | **92/93** | **8.4 tok/s** | **22.1 tok/s** | **56.5 %** |

The letters are identical, so the answers do not move; the rate does, and the engine's own hit-rate line
shows *why* - with the KV out of VRAM, ~10 points more of the routed experts fit in the cache. Note the
flag is not echoed in the log; the effect is what identifies it. One run per arm, so read the ~15 % rate
move as directional until repeated (that is what q3's floor is for).

**q2 - the `--moe-cache-mib` ladder: half refuted, and the interesting half is the other half.** The
prediction was "non-monotonic, peaking in the low thousands of MiB: 0 -> ~35-40 tok/s, a rung in
256-2048 best, the top rung at or below the control". Measured decode rate on the staged b11480 build,
same declared Qwen3.6 flags, letters as the guard:

| rung (MiB) | 0 | 256 | 512 | 1024 | 2048 | 4096 |
|---|---|---|---|---|---|---|
| decode tok/s | 47.2 | 42.3 | 41.9 | 54.5 | 61.3 | **73.6** |
| letters | 90/93 | 90/93 | 90/93 | 90/93 | 90/93 | 90/93 |

So the curve *is* non-monotonic - the 256 and 512 rungs sit below the control - but the best rung was the
**largest tested**, +56 % over the control, and still rising at the top of the ladder. The prediction's
direction was right and its shape was wrong: there is no peak in this range to find. The ladder should be
extended (8192, 16384 MiB) toward the 2 GiB `--vram-reserve-mib` region before any of this is quoted as
"the" cache setting. The letters are identical at every rung, which is the claim that matters for scoring:
**the cache does not change what the model answers**, at least on this battery.

**q3 - the noise floor: refuted for the rate, in the useful direction.** The prediction was that the wall
clock's spread would be "large enough to swallow a 5 % speed claim". Two identical control runs, same
config, back to back: **47.80 and 47.53 tok/s (0.57 % apart)**, 3.73 s and 3.73 s. A 5 % rate difference
is therefore about nine times this floor, and the 256/512 dip (~10 %) and the 4096 gain (+56 %) in q2 are
both outside it. Caveat, stated because it bounds the claim: this floor is for a 160-token probe on a warm
model, so it does not bound a multi-thousand-token task or a full battery - for those the recorded
`ledger2` spread of 19 checks still stands as the floor, and single-run differences below it are still
noise.

**q4 - the first attempt was a false success of my own making.** It exited 0 in 62 s having tested
nothing: the profile was never written (`profile_saved: false`), so the second half of the experiment
never ran, and the item reported green anyway. Two causes, both mine: the engine learns a profile through
the *config keys* `expert_profile_save` / `expert_profile_save_every` (default **ten minutes**, or QUIT
only), and `Engine.__exit__` stops an engine with `taskkill /F` - so a profile written at QUIT can never
appear. The item now uses the config keys, sets the interval to a minute, keeps the warm phase long enough
to cross it, and **fails** when the profile is absent. Re-run below.

**q5 - Ollama's decision path: the declared refusal, as designed** (exit 3, no decision model in the local
store, and no download attempted by the queue). **q6 parked, q7 gated** on `Niko1221/Strata#2747`, both
skipped by their declared status rather than attempted.

## q4-calibrated-warm-cache - Warm the expert cache from a calibrated hot set at fixed capacity

Our 2026-10-11 warm test warmed with prompts and persisted nothing; does a calibrated hot set raise the hit rate and move decode, and does it move the letters?

Prediction recorded before the run: Hit rate up (toward the 42% the calibration literature reports from 6% random) and decode better; letters unchanged.

