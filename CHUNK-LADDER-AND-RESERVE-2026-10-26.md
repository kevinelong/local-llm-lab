# The chunk ladder on 12 GB, and the reserve that was buying speed: 2026-10-26

Two experiments from the untried list, run on the **staged 0.1.47** engine with the **q2_0** pack, one server per arm,
same prompts, seed 1234. No download, no bump.

## 1. Prompt chunk: flat on this card, and the 24 GB row does not transfer

19,769-token prompt, `--prefill CHUNK`, all three rungs measured with **10.3 GiB of VRAM free at start**:

| `--prefill` | prefill tok/s | decode tok/s | wall |
|---|---:|---:|---:|
| 4096 | 704.3 | 12.5 | 30.4 s |
| 8192 | 717.1 | 13.9 | 30.5 s |
| 16384 | 719.7 | 12.8 | 30.4 s |

**Flat within noise.** On a 24 GB 5090 D the same flag gave **4.2x** prefill and 12.04 -> 18.89 decode; here it gives
1.02x and 12.5-13.9 across the range, which is the vendor's `<16 GB -> 4096` rule being right for the wrong reason: the
auto chunk is already as big as this card's buffers allow, so asking for more changes nothing.

**The first pass said the opposite, and it was contamination.** Same three rungs, but started with only **5.54 GiB VRAM
free**: 4096 read prefill 460.5 / decode **4.1**, 16384 read 702.9 / 12.9, and the 8192 arm **failed to serve at all**
(`expert cache auto: 0.00 GiB free -> 0 slots`, then `verify: needs the profile-filled VRAM expert tier`). The expert
cache is sized from free VRAM at start, so a rung measured in a different memory state is not the same experiment. The
harness now records `vram_free_mib_before` per row and waits for the previous engine to release both port and VRAM.

## 2. `--vram-reserve-mib`: 900 beats the config's 2000, at the same chunk

Matched pair at `--prefill auto`, everything else identical:

| reserve | expert-cache slots | prefill tok/s | decode tok/s | wall (19.8k prompt) |
|---|---:|---:|---:|---:|
| 2000 (the q2_0 config) | ~2,000 | 825.4 | 13.5 | 26.7 s |
| **900** | **3,049** | **984.4** | **16.6** | **22.4 s** |

**+19 % prefill, +23 % decode, -16 % wall** from handing the reserve to the expert cache. This is the same lever our
2026-10-20 ladder found from the cache side (capacity -> 83 tok/s at 5,376 MiB), now visible from the reserve side on an
engine that had not been measured this way. The shipped default in 0.2.3+ is **1536**, which sits between the two arms
here and is **unmeasured on this pack**; #3952 is the reason it exists at all (0.1.46 spends the reserve at long
context, 0.1.43.1 does not).

## 3. Two of my own bugs, recorded because they cost runs

- The first reserve arm was launched with `--prefill r900` - the harness used the *rung label* as the chunk value, so
  the engine refused to serve (`needs --spec T and --prefill CHUNK`). The label is now only a chunk when it is a number.
- A retry failed because the previous engine still held port 8091 and its VRAM; the harness now waits for the port to
  close (up to 120 s) and for >= 4 GiB free before starting, and skips a rung rather than measuring it in the wrong
  state.

## What this changes

- **Drop the chunk ladder from the queue** for this card; it is measured flat. The rung to keep watching is whatever the
  engine picks automatically, read back from the log.
- **`--vram-reserve-mib 900` is a candidate default** for this pack (one arm, matched, +19-23 %), pending a repeat and a
  1536 row.
- **Free VRAM at start is a declared variable** for every engine measurement from now on, beside page file, commit and
  the cache size itself.

Evidence: `ai_bench/chunk-ladder-20261026.json` (contaminated first pass), `-rep2.json` (the table above),
`reserve-900-20261026.json`, `reserve-2000-20261026.json`; engine logs under
`ai_bench/staged-strata-0.1.47/logs/chunk-*.log`.
