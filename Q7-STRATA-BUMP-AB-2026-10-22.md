# q7: engine 0.1.40.3 vs 0.1.47 on the same pack — text identical, no speed gain
## 2026-10-22, declared in the runner's docstring before the load

Same pack (`q2_0`, Qwen3.8-Flash-Next Q2_0 + PLE), same config, same flags; the arms differ only in `exe`.

| arm | model id served | load | decode tok/s (3 requests) | mean | drafts (offered/accepted) | commit after |
|---|---|---|---|---|---|---|
| **0.1.40.3** | `qwen3.8-flash-next-q2_0` | 50.4 s | 62.7, 68.4, 72.6 | **67.9** | 47/44, 46/43, 46/43 | 11.83 GiB |
| **0.1.47** | `qwen3.8-flash-next-q2_0-engine0147` | 47.0 s | 52.0, 68.3, 45.5 | 55.3 | 49/48, 46/45, 48/44 | 11.65 GiB |

Answers, `temperature 0`, three requests each: **`2, 3, 5, 7, 11` on every request in both arms.**

## Against the predictions

1. Both arms load and serve — **confirmed**.
2. Answers identical — **confirmed**, which is the result that matters: a patch-level engine change does not move
   greedy text on this pack.
3. Decode within noise, no speed gain — **confirmed in direction, not in significance.** 0.1.47's spread
   (45.5-68.3) overlaps the baseline's low end, so "the bump buys no speed" is supportable; "0.1.47 is slower" is
   **not** supportable at n=3.
4. MTP drafts offered and accepted on both — **confirmed** (43-48 accepted of 46-49 offered).
5. Commit headroom stays under 8 GiB — **wrong here**: 11.83 and 11.65 GiB. The 7.0 GiB reading came from an
   environment where other work held commit. Corrected: it is environment-specific, not a property of the pack.

## Three of my own numbers from earlier today were artefacts

- **14.0 tok/s** (the first-load test) was one request bounded at 24 max tokens, with the reply cut at the reasoning
  budget - not a steady-state rate.
- **10-11 tok/s** came from a run where a **stale 0.1.40.3 server was still listening** and answered for both arms.
- Steady state, once measured properly, is **45-73 tok/s** on this pack.

## The contamination, and the guards it forced

The first attempt reported `load=0.0s` for both arms and the same model id for both - because `proc.terminate()` kills
the `cmd /c strata.cmd` wrapper but **not the python/engine children it spawns**. A leftover server from the previous
attempt owned the port and answered both arms, which made "answers identical" trivially true.

Guards now in the runner, each of which would have caught it:

1. **a distinct port per arm** (8084, 8085), so one server cannot answer twice;
2. **a busy-port pre-flight** that refuses to measure rather than quietly measuring the wrong process;
3. **an assertion that the served model id equals the config's `model_name`** - the discriminating evidence, since the
   0.1.47 config renames the model to `...-engine0147`;
4. **tree teardown**: whoever still owns the port after the wrapper exits is killed with `taskkill /T /F`.

## What this establishes

**The engine bump is text-neutral and speed-neutral on the q2_0 pack**, so taking 0.2.2/0.1.47 is justified by the
0.1.47 issue fixes - `--pool-workers`, own-GGUF import, `--vram-reserve-mib`, the WDDM shared-segment patch - and not by
a throughput claim about this pack. It also means the pack does not need re-baselining for *answers*.

## What it does not establish

- Nothing about the qwen36 GGUF path (unreachable: Strata does not accept that model type).
- Nothing about Q4_K-expert packs (#3699) - none was built or loaded.
- n=3 requests per arm, one seed of prompts, one pack. The rate spread within 0.1.47 (45.5-68.3) is wider than the
  difference between arms.
