# #30926 needs a buffer over 4 GiB, and our model has none
## 2026-10-22 — item 3 of the priority list

## Declared question

`#30926` ("Fix #30793") merged **2026-10-22T14:00:59Z**; #30793 is that `--load-mode mlock` **silently skipped host
buffers larger than 4 GiB** (because #30449 split them). Prediction recorded before the run: on identical flags,
**b11823** either reports locking buffers b11810 skipped, or shows a **lower first-request prompt time**.

## Staged build

`b11823` (2026-10-22T18:02:18Z) — **the first three tags after the merge are b11821/b11822/b11823, all containing
#30926**; b11819 still predates it. Both archives' sha256 match GitHub's published digests
(`9c6e59ec…` llama, `738f8c25…` cudart). `llama-server.exe --version` → **0.7.0-dev (build 11823, commit 5c19a5a75)**.

## Result: no difference, and the mechanism says why

| build | load | first-request `prompt_ms` | prompt tok/s | decode tok/s |
|---|---|---|---|---|
| b11810 | 14.6 s | **719.3** | 260.0 | 64.0 |
| b11823 | 16.1 s | **724.3** | 258.2 | 62.7 |

Flags identical: `--cpu-moe --load-mode mlock --moe-cache-mib 5120 -c 131072`, first request measured with no
warmup. Differences are ~1 %, i.e. noise. Neither build printed a lock line beyond echoing `(load_mode = mlock)`.

**Why: our file has no buffer over 4 GiB to skip.** From the GGUF header:

| tensor | type | size |
|---|---|---|
| `output.weight` | Q6_K | **397.9 MiB** |
| `token_embd.weight` | Q4_K | 272.8 MiB |
| `blk.N.ffn_down_exps` / `gate` / `up` | Q4_K | **144.0 MiB each** |

**Zero of 733 tensors exceeds 4 GiB**; estimated total 19.01 GiB. The >4 GiB mlock path that #30926 repairs is never
entered for this model, so the fix is a measured **no-op here** - not a null result about the fix, but a statement
that our workload cannot observe it.

## What this changes

- **b11823 supersedes b11810** as the staged modern build (it carries #30926 plus nine builds of drift), and it is
  the right build for the SLRU/policy axis when that runs.
- **The TTFT blocker is closed as "does not apply to this model"** rather than "waits for a merge". If a future file
  has a single host buffer over 4 GiB - a bigger model, a different tensor layout, or a merged embd/output - the
  test becomes worth repeating; until then it is answered.
- Prediction wrong on the day: recorded as such.

## What this does not establish

- Nothing about #30926 on a model whose buffers do exceed 4 GiB, which is the case it was written for.
- Nothing at other `--moe-cache-mib` values; both arms used 5,120.
- One request per arm, one seed, and the arms ran back to back rather than interleaved, so a slow drift in the box
  would appear as a build difference. The 1 % gap is smaller than the spread measured at the 5,376 rung today.
