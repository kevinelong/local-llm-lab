# Our staged Qwen3.6 has Q4_K expert-down tensors — and our engines load it anyway
## 2026-10-22, from `NEWS-2026-10-22a.md` §8 item 1 (declared "one minute, no download, no engine")

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

## CORRECTION: #3699 is Strata's refusal, not llama.cpp's

This document first read "#3699 says the qwen36 path refuses Q4_K expert downs" and then argued that our engines load
the file anyway — **comparing a Strata-side refusal against llama.cpp builds b11480/b11810.** That comparison is void:
llama.cpp wrote the Q4_K_M recipe and accepts it by construction. What #3699 actually reports is:

- **Strata issue #3699**, opened **2026-10-22T08:01:09Z**, 0 comments. Loading a Q4_K_M Qwen3.6-35B-A3B GGUF is
  **refused by Strata's own native expert kernels**:
  `strata-q36: blk.5.experts are Q4_K/Q4_K, which the native expert kernels do not take (build with
  -DSTRATA_Q6K_EXPERTS=ON for Q6_K)`
- Mechanism: `STRATA_D_FMTS` carries Q5_K and Q6_K but **no Q4_K**, so `native_expert_supported()` returns false.
  Adding Q4_K (type 12) to both variants loads and runs — on an RTX 5080 16 GB at 0.1.47, `hybrid experts: 112 of
  256 in VRAM (8.16 GiB)`, prompt 4.5-5.1k tok/s, decode **133.9-154.7 tok/s**, text identical to llama.cpp b11798
  for 380 characters on two of three prompts.

**And our file is worse off than the reporter's.** Theirs had 20 layers `Q4_K/Q4_K/Q4_K` and 21 layers
`Q4_K/Q4_K/Q6_K`, i.e. Q6_K downs in half the layers. Ours has **all 40 routed-expert down projections at Q4_K**;
the only Q6_K tensor in the entire file is `output.weight`, and the shared-expert downs are Q8_0. So on a pre-#3699
Strata there is **no layer that would be accepted** - not half, all.

## Why this matters, and the contradiction it creates

The scan ranked this first because **#3699 reports that the qwen36 path refuses Q4_K expert *down*
projections**, and that Unsloth's UD quants "skirt" that case — which would explain how such a file loads at all.

**Our file does not skirt it: all 40 down projections are Q4_K.** And our engines load and serve it: b11480 and
b11810 both come up on the declared `--cpu-moe --load-mode none` workload, and yesterday's q6 arms ran four loads
at **77–81 tok/s with 90/93 letters identical**.

The open question is now this: **the 2026-10-21 note records that Qwen3.6 "loads and serves on Strata 0.1.46 at a
32K context"** — which, if that path is the native expert kernel, should have been refused. Candidate resolutions,
none tested:

1. the build that served it already carries the type-12 patch, or a `STRATA_D_FMTS` that includes Q4_K;
2. the served path was not the native expert kernel (a VRAM-clamped expert cache / a fallback), so the check that
   #3699 describes never ran;
3. the artefact served on Strata was not this file (a UD variant whose downs are Q6_K would explain it).

**What I could not check from here:** the staged Strata source on this box is **v0.1.27 (2026-09-30)** and contains no
`STRATA_D_FMTS`, `native_expert_supported` or `STRATA_Q6K_EXPERTS` symbol at all, so it cannot speak for 0.1.46/0.1.47.
The decisive test is one load: run our staged Qwen3.6 GGUF on the current Strata and read the first expert line.

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
