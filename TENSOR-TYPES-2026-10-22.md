# Our staged Qwen3.6 has Q4_K expert-down tensors — and our engines load it anyway
## 2026-10-22, from `NEWS-2026-10-22.md` §8 item 1 (declared "one minute, no download, no engine")

Tool: `local-llm-lab/gguf_tensors.py` (header parse only — no weights, no engine, no network).

## The reading

`staged-qwen36-20261007/Qwen3.6-35B-A3B-Q4_K_M.gguf`, 20,419,565,568 B, **GGUF v3, 733 tensors, 43 metadata keys**:

| tensor family | count | types |
|---|---|---|
| `ffn_down_exps` | 40 | **Q4_K (all 40)** |
| `ffn_up_exps` | 40 | Q4_K (all 40) |
| `ffn_gate_exps` | 40 | Q4_K (all 40) |
| `attn_q` / `attn_qkv` | 50 | Q8_0 × 40, F32 × 10 |
| whole file | 733 | Q8_0 310, F32 301, Q4_K 121, Q6_K 1 |

## Why this matters, and the contradiction it creates

The scan ranked this first because **#3699 reports that the qwen36 path refuses Q4_K expert *down*
projections**, and that Unsloth's UD quants "skirt" that case — which would explain how such a file loads at all.

**Our file does not skirt it: all 40 down projections are Q4_K.** And our engines load and serve it: b11480 and
b11810 both come up on the declared `--cpu-moe --load-mode none` workload, and yesterday's q6 arms ran four loads
at **77–81 tok/s with 90/93 letters identical**.

So the open question is now narrower and better posed: **the refusal's stated precondition is present in our file
and does not reproduce on b11480 or b11810.** Candidate explanations, none tested:

1. #3699's refusal is version-specific — older or newer than both our builds;
2. it applies to a path we do not use (adaptive scaling / #30861, or the MTP block, rather than the plain
   `--cpu-moe` route);
3. the reporter's file differed in a way the header alone does not show (a mix of Q4_K and Q6_K per layer; ours is
   uniform across all 40).

## What this changes in the queue

- **The cheapest item is answered**: nothing about our quantisation blocks the current engines, so a re-stage of
  the newer upstream revision is *not* motivated by #3699.
- It does **not** answer whether the newer upstream revision (`7878dc9a`, 2026-10-19, vs our `baec3ebe`, 2026-10-07)
  changed tensor types: sizes are unchanged, but the header of the upstream file is a download away and that is a
  decision, not a step.
- It sharpens item 3 (the context ladder): if a refusal exists anywhere on this path it will show as a load failure
  at a specific context, and the stack now has a documented baseline that loads cleanly at 131,072.

## Method note

The GGUF reader skips metadata by seeking rather than materialising it (the tokenizer arrays dominate the header),
so the whole 20 GB file is read to a few hundred KB of seeks. 733 tensor descriptors were enumerated in one pass.
