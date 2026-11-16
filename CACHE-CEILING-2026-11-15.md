# The cache ceiling was the build's, not the pack's (2026-11-15)

Measured on **`b12383`** (`1.0.0-dev`, commit `c56be864f`), our own pack `Qwen3.6-35B-A3B-Q4_K_M` with its
`--cpu-moe --load-mode none -t 8 -c 8192 -b 512 -ub 512`, MTP off, **19,717-token prompt** (the 2026-10-27 ladder's
own text, reconstructed from `chunk_ladder.py`'s `LONG_BODY`; Strata counted 19,769 on its tokenizer). Fourteen server
starts, seven rungs **ascending then descending**, plus one `llama-cli` companion per rung for the hit rate. Artifacts in
`C:\Users\kevin\ai_bench\cache-ladder-20261115\`.

| `--moe-cache-mib` | decode tok/s (asc / desc) | vs its own control | engine's `slots` line | hit rate | prefill tok/s |
|---|---|---|---|---|---|
| 0 | **45.42 / 45.70** | - | *no line - disabled* | - | 1212.7 / 1215.1 |
| 512 | **59.61 / 58.42** | **+31.2 % / +27.8 %** | `302 slots (2.9 %, 0.9 tokens worth)` | **28.95 %** | 1090.6 / 1085.3 |
| 1024 | 74.22 / 71.70 | +63.4 / +56.9 % | `605 slots (5.9 %, 1.9 tokens worth)` | 43.85 % | 996.0 / 995.3 |
| 2048 | 85.79 / 85.30 | +88.9 / +86.6 % | `1212 slots (11.8 %, 3.8 tokens worth)` | 57.36 % | 908.5 / 908.3 |
| 4096 | **89.67 / 88.88** | +97.4 / +94.5 % | `2426 slots (23.7 %, 7.6 tokens worth)` | 74.08 % | 902.0 / 899.1 |
| 5376 | 89.91 / 89.57 | +98.0 / +96.0 % | `3184 slots (31.1 %, 9.9 tokens worth)` | 80.32 % | 904.1 / 905.3 |
| 6144 | 89.94 / 90.96 | +98.0 / +99.0 % | `3639 slots (35.5 %, 11.4 tokens worth)` | 82.63 % | 903.8 / 905.0 |

**No rung was clamped**: the granted size tracks the declaration at every rung (511.31 / 1022.62 / 2046.94 / 4095.56 /
5374.69 / **6142.50** MiB), and 6144 was **admitted**, not shrunk. Within-rung spread 0.4-3.5 %, smallest between-rung
step that matters 4.4 %, so the curve is resolvable at n = 2.

## What this reverses

1. **"512 MiB is a dead zone" is a `b11480` fact, not a property of this pack.** On `b12383` the same rung reads
   **+29.5 % over its own control** at **0.9 tokens worth** - a cache that cannot hold a single token's working set
   still gets **28.95 % hits**. The 2026-10-20 ladder put 256/512 MiB *at or below* the no-cache control; that shape
   does not exist here.
2. **The ceiling was the build's.** The elbow is **4096** (+96.0 % on the mean) and nothing above it beats its own
   spread; the **5376 MiB "admissible maximum"** from 2026-10-20 is the same curve, read on a build whose policy capped
   it. On this build 6144 is admitted and buys nothing measurable over 4096.

The mechanism the numbers are consistent with, and which is **not** demonstrated: `#30637` moved LRU -> 50/50 SLRU at
`b11732`, and upstream reports the collapse at **1.0x a token's worth** (240 slots: 0.6 % hits / 8.8 tok/s against
LRU's 37.5 % / 12.9). Our rungs convert to 0.47 / 0.95 / 1.90 / 3.79 / 7.59 / 9.96, so the old dead zone sat in that
band. **No `b11480` arm ran today**, so the attribution stays a hypothesis with a measurement consistent with it.

## The trade nobody had priced: the cache costs prefill

Prefill falls **monotonically to -25.8 %** (1213.9 -> 900.6 tok/s) and is fully spent by 2048. So a cache rung is a
**decode-for-prefill trade**, not a free win, and any prefill row that carries a cache must declare it - which the
template already required for other reasons and now has a number behind.

## Three instrument facts, each found by failing first

- **`-lv 4` is required.** At default verbosity this build prints **nothing** about the cache; at `-lv 4` it prints
  `N slots (x %, Y tokens worth)` and `CUDA0 MoE cache size = X MiB for 17280.00 MiB of host experts`. **The control
  prints neither line**, which is the proof of absence rather than a guess.
- **The hit-rate line is emitted only when the context is freed.** Force-stopped servers never print it, so every hit
  rate here comes from a per-rung `llama-cli` companion (same flags, prompt, sampler, `n=128`, `ignore_eos`). Its decode
  is lower (45.36 against the server's 59.61 at 512 MiB) because it does not reuse graphs - so the two are kept in
  separate columns and never mixed.
- **`LLAMA_MOE_CACHE_TRACE` is not a text channel**: it writes a binary `MCT1` file. Set for every rung so the observer
  is uniform; kept as evidence that it is the wrong instrument for a log line.

## The gate finding, now a field

Every admission was green (physical 38.86-39.20 GiB, commit 27.72-28.03 GiB, VRAM >= 10,368 MiB free) and **every
post-load reading is under the commit floor**: commit at ready falls **6.18 GiB -> 0.63 GiB** and used VRAM rises
**4,537 -> 10,389 MiB** across the ladder. So a rung above 6144 MiB is **VRAM- and commit-limited, not
admission-limited**, and `DECLARATION-TEMPLATE.md` sect. 3 now carries `commit_at_ready` for exactly this reason.

## What may not be quoted from this

- Not "the cache ceiling is 4096" as a property of the pack: it is the ceiling **on this build, this prompt, this
  sampler and n = 2**, with the companion hit rates from a different binary path.
- Not the left column of the 2026-10-20 ladder as comparable: 47.4 -> 78.3 tok/s is the **control** for this
  experiment, not a result of it, and it was taken on LRU.
- The plateau past 4096 is **not explained by the hit rate**, which keeps rising (74.08 -> 82.63 %). This ladder does
  not name that bound.
