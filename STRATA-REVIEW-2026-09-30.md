# Strata engine review: running Qwen3.8-Flash-Next on a 12 GB card

Research date: 2026-09-30. Prepared from primary sources plus one video review.
No engine was installed, no model was loaded, and no measurement below was taken
on this machine. Vendor and third-party numbers are labelled as such.

## Sources read

- Video: "6x Faster Than llama.cpp - The New Way to Run 125B Models", Morgans
  Code, uploaded 2026-09-29, 10:19, about 6.3K views. Manual subtitles were
  retrievable, so the analysis below quotes the transcript rather than a summary
  of it. https://youtu.be/i7nSjm5tTRw
- Engine repository: https://github.com/Niko1221/Strata , MIT licence, C++,
  1,987 stars, 229 forks, 71 issues. Cloned here at commit
  a79080535d1b2a71a3419a0d97d8e7dca194b0f1 (shallow, tip of main on 2026-09-30).
- Engine detail doc: https://raw.githubusercontent.com/Niko1221/Strata/main/docs/DETAILS.md
- Engine paper: docs/paper/Strata-Paper.pdf in that repository.
- Model: ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF (apache-2.0), with the
  Coder pack described in the engine README.
- Third-party reports: an X post by ItsmeAjayKV (RTX 3090 + 64 GB DDR5, int8 KV,
  MTP n-max 4: 62 t/s average, 70 t/s peak at 16k context) and an r/LocalLLaMA
  thread reporting roughly 50 t/s generation on the same GGUF family. Both are
  third-party and unverified here.

## What the engine does

Qwen3.8-Flash-Next is 125B total with about 6B active per token, plus a 51B
n-gram embedding table and a 4B MTP layer (see RESEARCH-2026-09-29.md). Strata
serves it by splitting the model three ways:

- GPU: the parts used for every token (attention, routing, shared experts) plus
  the KV cache, plus an adaptive cache of the most-used experts in whatever VRAM
  is left.
- RAM: the expert pool, 24,576 experts across 48 layers.
- SSD: the roughly 29 GB n-gram lookup table, read a few rows per token.

Three mechanisms are claimed to make that fast: the adaptive expert cache, the
CPU computing uncached experts concurrently with the GPU working on cached ones,
and the model's own MTP layer guessing up to three tokens ahead (vendor claim:
1.6-1.8x over token-by-token, answers unchanged).

## Vendor numbers (not measured here)

Measured by the vendor on RTX 5070 12 GB, Ryzen 5 7600, 64 GB RAM:

| Build | RAM+VRAM | Short chat | 128K context | Quality (vendor) |
|---|---|---|---|---|
| Q2_0 | 37.6 GB | 93 t/s | 74 t/s | good |
| IQ2_XS | 39.2 GB | 79 t/s | 63 t/s | recommended |
| IQ3_XXS | 47.0 GB | 62 t/s | 49 t/s | great |
| IQ3_S | 54.8 GB | 53 t/s | 46 t/s | best, matches full model |
| Coder (IQ1_M) | 32 GB RAM class | 55 t/s | 43 t/s | 91% SWE-bench Verified, 98.7% LiveCodeBench v6 |

Prompt reading is 1,620-2,180 t/s at 32K, which the vendor summarises as about
one minute per 30,000 prompt tokens. It answers one request at a time.

The video's "6x faster than llama.cpp" is marketing arithmetic: it compares
llama.cpp at 15 t/s on one build against 93 t/s on the fastest build. The
engine's own table puts the comparable 3-bit build at 53-62 t/s, so the
defensible figure is about 4x, on the developer's machine, with the developer's
numbers.

## What is relevant to this lab

1. It independently confirms what we measured on 2026-09-30 with Gemma 4
   26B-A4B: on a 12 GB card the binding constraint is system RAM, not VRAM.
   Gemma consumed about 14.5 GiB of host RAM for a 10 GB model and bottomed at
   2.65-2.94 GiB against our 3 GiB runtime floor (see candidates-20260929-v8).
   Strata states the same law from the other direction: 35-55 GB resident for
   this model, and "with 32 GB, none of them fit" for the original.
2. It revises an earlier exclusion. BONSAI-REVIEW.md excluded Strata because
   "documented RAM setup exceeds ours". That holds for the original model, but
   the current engine documents a Coder pack whose shard 1 is 29.6 GB with 23 GB
   of experts and which is stated to run on 32 GB of RAM, plus a low-RAM mode
   (engine 0.1.26+, --mmap-experts) that maps experts from disk and drops the
   engine's committed memory on the Coder from about 36 GB to about 13 GB.
3. Three mechanism claims are testable on our existing pinned llama.cpp build
   even though the Strata binary is model-specific: adaptive expert caching in
   spare VRAM, CPU/GPU expert compute overlap, and MTP speculative decode. Our
   a3b-offload-20260924-v1 measured 33.90/32.72 t/s with static layer placement
   and no expert cache, so a cache-plus-overlap control is a real gap.

## Cautions

- Low-RAM mode on a 12 GB card is disk-bound: the vendor says most experts come
  from the SSD and "it is much slower", and setup warns about it. Any run here
  is a "does it start and produce correct answers" test, not a speed test.
- The project is days old: the README and video both describe a temperature
  handling bug fixed at 0.1.7 and a large-VRAM hang still being fixed on day
  four. Our harness substitutes sampling flags (temperature 1, top-p, seed) into
  the server command; a fork that ignores temperature would silently confound
  our declared sampling, so a probe that the endpoint honours those parameters
  is mandatory before any scored run.
- "Experimental speed projection" is a refusal-removal control vector, off by
  default, and the video reports it reduced code accuracy. Do not enable it.
- Naming trap: the Swift 1.5 fine-tune in this engine's installer is UkisAI's
  fine-tune of Qwen3.8-Flash-Next with its own licence. It is not the Swift
  Bonsai 2 PQ2 measured in candidates-20260929-v8.
- The video's claim that the repository had no licence file was accurate when
  checked and has since been fixed: the clone carries an MIT LICENSE.

## Staged for a pinned run

See queue-20260930-strata/RESUME.md and staged.json. Model revision and per-file
sha256 are pinned and every file is downloaded and verified; the engine is pinned
by commit and by binary digest (v0.1.27, asset sha256 cbb44dd8...5200b839, no
compiler needed). GGUF files are in staged-strata-20260930/gguf. The integration
is not free: Strata is an external server on 127.0.0.1:8080/v1 rather than a
runtime our harness launches, so the runner needs a new revision that skips the
llama-server launch, points the relay at Strata's endpoint, and verifies that the
endpoint honours our sampling parameters.
