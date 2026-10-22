# Strata 0.1.47: our GGUF is not a Strata model, and an existing pack serves on the new engine
## 2026-10-22 — items 1 and 5 of the priority list

## Item 1: #3699 cannot apply to our file, and the reason is upstream of the expert kernels

Strata's own importer settles it without any load:

```
$ strata models import --plan ...\staged-qwen36-20261007\Qwen3.6-35B-A3B-Q4_K_M.gguf
These files cannot be used as they are: Qwen3.6-35B-A3B-Q4_K_M.gguf: this model type is not supported by the
Strata engine (add it as a Custom model API with llama-server instead); this is not a model size Strata knows.
```

So the whole Q4_K-versus-Q6_K question is **not reachable for our reference** - not because our 40/40 Q4_K down
projections would pass, but because a plain `ggml-org` Qwen3.6 Q4_K_M GGUF is not something the Strata engine accepts
at all. **#3699's reporter must have been loading a Strata pack**, where `blk.N.experts` and `STRATA_D_FMTS` are the
relevant layers; the message we can produce names a different failure first.

Consequence: the 2026-10-21 note that Qwen3.6 "loads and serves on Strata 0.1.46 at 32K" **cannot have been this
file** - it must have been a pack. And nothing about our staged GGUF's quantisation can bite us on Strata, because the
engine never gets far enough to look.

## Item 5, first step: an existing pack runs on engine 0.1.47

Staged without touching Kevin's AppData: the release's engine package was placed at
`ai_bench/staged-strata-0.1.47/components/engine/0.1.47-windows-x86_64-cuda/` and pointed at with
**`STRATA_COMPONENTS_DIR`**, which the control honours. Strata's own inventory then reports:

```
component folder  C:\Users\kevin\ai_bench\staged-strata-0.1.47\components
this PC           windows-x86_64, cuda (nvidia-smi)
  installed       0.1.47 windows-x86_64-cuda
engine            ...\0.1.47-windows-x86_64-cuda\strata.exe  (version 0.1.47)
nothing was downloaded or changed
```

The existing `q2_0` run config (Qwen3.8-Flash-Next, Q2_0 + PLE) was copied with **only `exe` and `port` changed** - to
the 0.1.47 binary and 8082 - and `serve --plan` produced the same 28 engine arguments with no notes. It then started:

```
[strata] loading the most-used experts into RAM (up to 2 GiB ...) and locking part of them for the GPU.
[strata] filling the GPU's expert cache (2135 experts, 2.75 GiB of VRAM) ...
ready: http://127.0.0.1:8082/v1   (context 65536 tokens)
```

One chat request, `temperature 0`, 24 max tokens:

| measure | value |
|---|---|
| wall | 1.45 s |
| prompt | 57 tokens, **52 cached** |
| `prompt_ms` | 426.5 (5 uncached tokens) |
| decode | **14.0 tok/s** |
| **drafts** | **11 offered, 9 accepted** |
| VRAM | 10,277 / 12,227 MiB |
| WDDM shared segment | **2.93 GiB** on the NVIDIA adapter |
| free physical | 28.1 GiB |
| **commit headroom** | **7.0 GiB - below the lab's 8 GiB gate** |

So: the pack format is compatible across 0.1.40.3 -> **0.1.47** with a config that changes nothing but the binary, and
**MTP is firing on Windows here** (9 of 11 drafts accepted), which is worth setting against the earlier "MTP never
fires on Windows" finding - that was the *qwen36 GGUF path*, this is the q2_0 pack, and the two are not the same path.

## The gate finding that matters

Serving this pack leaves **7.0 GiB of commit headroom, under the 8 GiB floor**, while free physical memory reads
28.1 GiB. The lab's gate is commit-based for exactly this reason, and this configuration would **trip it** - so any
bump measurement on this pack must either raise nothing and record the trip, or free commit first. Declaring it.

## What this does not establish

- Nothing about Qwen3.6-on-Strata speed; that path needs a Strata pack of that model, which we do not have.
- Nothing about #3699's patch: an unpatched 0.1.47 would refuse a *pack* whose experts are Q4_K, and we did not build
  or load such a pack.
- Nothing about decode on the qwen36 path; 14.0 tok/s here belongs to the Q2_0 pack with MTP accepting 9/11 drafts.
