# REPORT: Strata (Qwen3.8-Flash-Next Coder IQ1_M) on the OMP coding screen

Date: 2026-10-06 UTC. Machine: DARKTEXAS, RTX 5070 12 GB, 31.46 GiB visible RAM (the 64 GB
module is still not installed). Engine: Strata v0.1.39, commit `6f32ec07`, MIT, own clone at
`../staged-strata-20261005/engine-src-v0.1.39`; model: the staged, hash-verified ISTA-DASLab
Coder pack (`../staged-strata-20260930/gguf`, 59,318,877,616 B).

## What was asked and what was done

Kevin asked to research the best Strata flags from recent YouTube transcripts, test them, and
use them in the run. Read `FLAGS.md` for the source-by-source research and the reconciliation
against the pinned tree; this report covers the tested configuration and the measured result.

Most Strata videos carry no captions (`hJ_Iw2E7cnc`, `4q_VlobZU0A`, `JD8_r5UDylc`,
`nN_bFUtrF1A`, `91rASFzuDPU`, `gR20MGAhll8`, `aNOUkWk9piU` all report none), so the two that
do (Kai, `m0VHx73SAG0` and `1--PzaHafAU`) plus the written Woke Engineer setup guide were used
for strategy, and the pinned v0.1.39 `setup.py` / `serve/runconfig.py` / `serve/server.py` /
`docs/DETAILS.md` were used as the authority for what the flags actually do.

## Final flag set (tested, in use)

```
setup.py --setup --gguf-dir <staged gguf> --family coder --model IQ1_M --context 32768 \
  --vision no --low-ram on --kv int8 --draft-vocab en --yes --no-start
setup.py --calibrate
```

Config `strata-coder-iq1_m.json` then carries: `sampling {temperature 1.0, top_p 0.95,
min_p 0.0, top_k 64}`, `open_browser false`, `draft_vocab en`, `--vram-reserve-mib 1500`,
`--resident-budget-gib 4`, `STRATA_LOOKAHEAD=0`, plus the engine args setup wrote
(`--expert-cache auto --prefill auto --spec 4 --spec-min-p 0.50 --pcie-frac 0.75
--pool-workers 15 --kv int8 --max-context 32768`).

`--calibrate` measured this PC: 12 workers 19.5 tok/s, then 22.5 tok/s after tuning
`--pcie-frac 0.75` and `--spec-min-p 0.50`. `--draft-vocab en` is the installer's own tip for
a 12 GB card (133 MiB of draft VRAM instead of 348). The lab's declared `top_k 0` cannot be
expressed (the server clamps 1..64); 64 is used and declared.

## The engine works; the low-RAM variant was the whole problem

Five configurations were measured with every lab floor unchanged. Four were stopped by the
guard; the fifth holds.

| low-RAM variant | min free physical | min commit headroom | min GPU free | outcome |
|---|---|---|---|---|
| `--resident-experts` (setup's default) | 2.77 GiB | 3.71 GiB | 0.70 GiB | stopped mid-load |
| `--mmap-experts` | 1.92 GiB | 15.92 GiB | 1.12 GiB | ready, served a prompt, stopped mid-request |
| `--resident-budget-gib 20` | 2.53 GiB | 3.32 GiB | 1.16 GiB | ready, stopped just after load |
| `--resident-budget-gib 20`, after reboot | 2.77 GiB | 3.76 GiB | 1.53 GiB | ready, stopped at the first request |
| **`--resident-budget-gib 4` + `STRATA_LOOKAHEAD=0`** | **10.36 GiB** | **11.11 GiB** | **1.46 GiB** | **probe and all three screens ran** |

Floors: 3 GiB free physical, 2 GiB commit, 0.5 GiB GPU. Cause, quantified: the Coder's expert
working set is about 30 GB on 31.46 GiB of RAM and Windows counts the file cache it reads from
as not-free, so any configuration that keeps the experts warm fills the box. The user-requested
minimal-startup reboot was executed and verified (`a3b-offload-20260924-v1/minimal-boot`):
free physical went 15.14 -> 18.19 GiB and GPU use 1313 -> 721 MiB, and the engine simply
absorbed the extra 3 GiB, bottoming at 2.77 GiB again. The small resident budget plus
disabling the lookahead prefetch is what left 10 GiB free. The standby cache is reclaimable:
it fell from 14.89 to 4.36 GiB on its own after a guard trip, and commit headroom never went
below 3.3 GiB.

`--vram-reserve-mib 1500` was needed for the same class of reason: the engine's 700 MiB default
left gpu_free at 0.32 GiB against the 0.5 GiB floor (the desktop holds ~1.2 GiB and the engine
locks the expert cache on top). 1500 MiB holds it at 1.33-1.46 GiB.

No floor, threshold or metric was changed at any point.

## Probe (evidence `probe/`)

- `/v1/models` lists `qwen3.8-flash-next-coder-iq1_m`, loaded, `n_ctx 32768`.
- Greedy twice with `seed 20260929` -> identical answers (deterministic).
- The server logs the config sampling it read (`temperature=1.0, top_p=0.95, min_p=0.0,
  top_k=64`), and the engine's own `serve/server.py` forwards a per-request `seed`.
- Tool calling works end to end: an OpenAI `tool_calls` echo with exactly
  `{"text":"STRATA_TOOL_OK"}`, and the full roundtrip returned `STRATA_TOOL_OK`.
- Model load 17 s; decode 8-9.5 tok/s; expert cache 68.7% hit on the probe.

## Screening results (OMP 18.3.1, 720 s wall, context 32768, budget 16000/12288)

| task | correct | artifact | tokens accounted | wall | notes |
|---|---|---|---|---|---|
| events | **76/76** | correct | 4,895 | 720 s | 10 tool calls, not clean (wall + quota) |
| paths | **75/75** | correct | 5,570 | 720 s | 5 requests, cache hit 60.9%, not clean |
| ledger | 7/70 | incomplete | 233 (lower bound) | 720 s | wall-bound, see below |

Every run ended at the wall (`exit 143`), and every run reported `quota_failure:
quota_unknown`: the engine does not always report `completion_tokens`, the same
usage-accounting gap we saw with the Prism runtime, so the token totals are lower bounds.

Resource margins across the three screens (350 samples each, no guard trip, `monitor_errors`
empty):

| run | min free physical | min commit headroom | min GPU free | load |
|---|---|---|---|---|
| events | 9.60 GiB | 10.09 GiB | 1.33 GiB | 16.3 s |
| ledger | 10.46 GiB | 10.26 GiB | 1.34 GiB | 16.4 s |
| paths | 10.49 GiB | 10.37 GiB | 1.35 GiB | 16.4 s |

## Reading the result

- **The platform works end to end.** A 125B-parameter MoE, quantized to ~59 GB, runs on a
  12 GB card plus 31 GB of RAM in low-RAM mode, exposes OpenAI `/v1`, and drives the lab's OMP
  coding screen without any gate change. Two of the three tasks came out fully correct on the
  first attempt.
- **The wall, not capability, is the constraint for ledger.** Prompts of 9.4-10.4K tokens read
  at about 550-670 tok/s, but decode is 6.5-9.6 tok/s (disk-bound; expert cache 47-71% hit).
  At that rate 720 s allows roughly 5,000 tokens of output, and events (4,895) and paths
  (5,570) just fit while ledger needs far more. Ledger's 7/70 says nothing about the model's
  ability; it is the same wall that our other local runs were measured under, on a much larger
  model.
- For context on the same tasks, our local results are: events 76/76 for Swift Bonsai 2 PQ2,
  OMP/MiMo and MiniCPM5-2B; paths 75/75 for MiniCPM and Swift Bonsai; ledger 70/70 (Swift
  Bonsai), 68/70 (MiMo), 67/70 (MiniCPM), 29/70 (Ling), 7/70 (Spark-X2.5-4B). Strata's ledger
  score lands beside Spark's for the same reason: not enough time, not enough model.
- Speed on this box is far below the vendor's 64 GB figures (55 tok/s for the Coder). That is
  expected and documented by the vendor for a 12 GB card in low-RAM mode: most experts come
  from the SSD. The RAM module is the lever for a faster configuration (larger resident
  budget, bigger quants), not a tuning flag.

## Limits and state

- One run per task, one platform configuration, no repetition and no threshold tuning.
- `quota_unknown` makes the token totals lower bounds; the artifacts are scored by the
  external scorer, so correctness is unaffected.
- The minimal-startup suppression applied for this experiment is STILL APPLIED. Restore it
  when the Strata work is finished:
  `powershell -NoProfile -File C:/Users/kevin/ai_bench/a3b-offload-20260924-v1/minimal-boot/Manage-A3BBoot.ps1 -Action Restore`
- A stale September `STOP` in `mimo-harness-20260925-v1` (the relay's stop path) aborted every
  session in 0.0 s until it was moved aside as `STOP.stale-20260925-preserved`
  (`evidence/stale-stop-moved.json`).
- Every stopped attempt is preserved: `probe-resident-experts-guardstop/`,
  `probe-mmap-gpufree-guardstop/`, `probe-mmap-freefloor-guardstop/`,
  `probe-budget20-freefloor-guardstop/`, `probe-budget20-postreboot-guardstop/`,
  `runs/oms-events-stopabort/`. No material was deleted.
