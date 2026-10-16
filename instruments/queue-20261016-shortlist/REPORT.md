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

