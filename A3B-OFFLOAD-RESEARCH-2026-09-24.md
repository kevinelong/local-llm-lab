# A3B models and RAM expert offloading

Research date: 2026-09-24. Local measurements are resource/header checks, not new inference benchmarks.

The most useful next experiment is a controlled CUDA llama.cpp baseline on the already installed Qwen3-Coder-30B-A3B. Then compare selective expert caching, and finally the newer Qwen3.6-35B-A3B. On this 32 GB RAM / RTX 5070 12 GB machine, available system RAM is the immediate constraint. A3B means roughly three billion parameters participate per token; all model weights must still be accessible.

## Models to compare

| Model | Expert architecture | Role in this comparison |
|---|---|---|
| Qwen3-Coder-30B-A3B-Instruct | 30.5B total, 3.3B active; 48 layers, 128 experts, 8 selected | First baseline; installed GGUF; coding focus |
| Qwen3-30B-A3B-Thinking-2507 | 30.5B total, 3.3B active; 48 layers, 128 experts, 8 selected | Installed general reasoning control; thinking-only |
| Qwen3-30B-A3B-Instruct-2507 | Same broad 30B architecture | Optional non-thinking general control; not currently installed |
| Qwen3.5-35B-A3B | Hybrid attention / recurrent architecture | Previous-generation control for the 35B family; EXL3 candidate |
| Qwen3.6-35B-A3B | 35B total, 3B active; 40 layers, 256 routed experts, 8 selected plus shared expert | Main new model candidate; requires a separate memory calculation |

Architecture and intended modes come from the official cards: [Coder](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct), [Thinking-2507](https://huggingface.co/Qwen/Qwen3-30B-A3B-Thinking-2507), [Instruct-2507](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507), [Qwen3.5](https://huggingface.co/Qwen/Qwen3.5-35B-A3B), [Qwen3.6](https://huggingface.co/Qwen/Qwen3.6-35B-A3B).

Local correction: the installed Ollama alias `qwen3:30b-a3b` contains **Thinking-2507**, according to GGUF metadata. Do not label it the original release or assume it supports a no-thinking mode. Both installed Qwen models have 579 tensors and about 17.28 GiB of tensor data, including 16.35 GiB of routed expert weights. This was measured from headers and tensor offsets; the large blobs were not rehashed in this preflight.

For Qwen3.6, Unsloth currently lists UD-IQ3_S at 13.7 GB, UD-Q3_K_M at 16.6 GB, UD-IQ4_XS at 17.7 GB and UD-Q4_K_M at 22.1 GB (decimal download sizes). Start with one selected file, not the entire repository. Smaller quantizations change model quality and must be reported as a separate variable. Download size is not peak RAM or VRAM usage. [Quantized files](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main).

## Four different meanings of offloading

| Design | System RAM | VRAM | Work on a cache miss |
|---|---|---|---|
| Static CPU expert layers | Expert weights for selected layers | Other layers, attention, KV cache | CPU computes the routed experts during ordinary decode |
| Mixed CPU/GPU expert cache | Full backing for offloaded layers | Attention, KV and frequently reused expert copies | CPU computes misses; selected experts can be uploaded for later reuse |
| GPU expert slot pool | Full expert backing | Attention, KV and a bounded expert working set | Transfer missing selected weights, then compute them on GPU |
| Whole model on GPU | Little active weight backing needed on CPU | All weights plus runtime buffers | No host expert transfer; installed Q4 models do not fit |

Stock llama.cpp exposes `--cpu-moe` and `--n-cpu-moe N`. These are placement controls, not a guarantee that every selected expert executes on GPU. Batched prefill can use different operation-offloading paths from one-token decode. Measure those phases separately and preserve the actual runtime logs. [Server options](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

The desired GPU working set is not a fixed set of eight experts for the entire model. Routing changes by layer, token, and input. A cache larger than top-k can retain recently used experts; a top-k-only cache may churn. Keeping the full backing in RAM plus GPU copies can increase total memory usage while reducing VRAM residency.

For the installed Qwen3 quantization, 8/16/32 cached expert slots per layer correspond to roughly 1.02/2.04/4.09 GiB of expert copies across all 48 layers, assuming the same average bytes per expert. A no-reuse stream of eight experts per layer would move about 1.02 GiB of weights per generated token. These are analytical estimates, not measured transfer volumes or speed predictions. Transfer latency and cache hit rate can dominate.

## Runtime evidence and priorities

1. **Stock llama.cpp CUDA: first baseline.** The existing `ai_bench/llamacpp` installation is b10883 / 91f6a6cf3 but CPU-only (`--list-devices` reported none). An isolated matching CUDA 13.3 release is now installed under this experiment. Both downloaded archives match the SHA256 digests in GitHub release metadata; the binary reports build 10883 and detects CUDA0 as the RTX 5070. No model was loaded. Both the old installation and the separately pinned Bonsai/Prism runtime remain unchanged. [Official release](https://github.com/ggml-org/llama.cpp/releases/tag/b10883).

2. **llama.cpp LRU cache PR: closest low-change research branch.** PR #27861 is still a draft. Its design uses GPU cache hits, CPU misses and asynchronous cache uploads; its documented initial path applies to single-token decode. Author benchmarks on two RTX 3090s are not evidence for this RTX 5070. Pin an exact commit, validate model/kernel support and correctness, then sweep cache capacity. Do not pass its flags to an unmodified release. [Draft PR](https://github.com/ggml-org/llama.cpp/pull/27861).

3. **Persistent GPU slot pool: closest match to selected-expert GPU execution.** Discussion #28248 describes transferring missing selected experts into reusable GPU slots. The author also documents a corrected expert-ID mapping bug, which makes reference-logit/perplexity testing essential before speed ranking. Report fork results separately; an advertised percentage improvement is not a local result. [Design and correctness discussion](https://github.com/ggml-org/llama.cpp/discussions/28248).

4. **ExLlamaV3: revisit on native Windows.** Version 1.5.1 explicitly fixes its pinned MoE arena on Windows and Conda; the earlier Linux-only assessment is stale. It needs EXL3 weights, so it is a separate deployment comparison rather than the same-GGUF backend test. [Release 1.5.1](https://github.com/turboderp-org/exllamav3/releases/tag/v1.5.1). Its documented CPU offload runs routed experts on CPU and streams hot experts during prefill. A pinned shared arena can remove an intermediate host copy, but needs physical RAM and commit headroom. Start unpinned, then compare pinned only after recording load peaks; do not disable host reserves to force a fit. [Offload controls](https://raw.githubusercontent.com/turboderp-org/exllamav3/master/doc/env_vars.md).

5. **KTransformers: useful later, more setup.** Current kt-kernel documentation includes AVX2, so lack of server-class AMX is not by itself disqualifying. It offers GPU expert counts, placement policies and dynamic updates. The AVX2 example uses Qwen3-30B-A3B GPTQ Int4, adding another weight format and software stack. Native Windows support for the complete current stack has not been verified here; WSL capacity must not be mistaken for extra physical RAM. [AVX2 tutorial](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/kt-kernel/AVX2-Tutorial.md), [Expert scheduling](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/kt-kernel/experts-sched-Tutorial.md).

6. **ik_llama.cpp: alternative optimized GGUF backend.** It has fork-specific fused MoE and operation-placement controls. Treat them as their own pinned experiment, not interchangeable stock llama.cpp flags. [Parameter reference](https://raw.githubusercontent.com/ikawrakow/ik_llama.cpp/main/docs/parameters.md).

## What this machine can currently accommodate

The initial saved preflight reported **4.83 GiB free physical RAM, 11.43 GiB commit headroom and 9.75 GiB free VRAM**. Ollama had no resident model and no run locks were found. The user authorized normal closure of unused apps; the selected app categories had no normally closable windows, so no closure was accomplished. No processes were force-killed.

| CPU expert layers, out of 48 | Expert weights in RAM | GPU weight upper bound | Required free RAM/commit* | Required free VRAM* |
|---:|---:|---:|---:|---:|
| 24 | 8.17 GiB | 9.10 GiB | 12.17 GiB | 12.35 GiB |
| 28 | 9.49 GiB | 7.79 GiB | 13.49 GiB | 11.04 GiB |
| 32 | 10.80 GiB | 6.47 GiB | 14.80 GiB | 9.72 GiB |
| 36 | 12.16 GiB | 5.11 GiB | 16.16 GiB | 8.36 GiB |
| 40 | 13.48 GiB | 3.80 GiB | 17.48 GiB | 7.05 GiB |
| 48 | 16.35 GiB | 0.93 GiB | 20.35 GiB | 4.18 GiB |

*Planning estimates for these installed GGUFs only: host weights + 1 GiB runtime scratch + 3 GiB margin; GPU weights + 0.75 GiB f16 KV at 8k + 1 GiB scratch + 1.5 GiB margin. Loader duplication/repacking can exceed these estimates. They screen candidates; successful loading and peak-memory observations remain required. The 32-layer row is close to current GPU headroom, so 36 is the preferred conservative first trial once RAM is available. The script computes its exact row too.

Windows reported large private commit in NVIDIA container processes, but their physical working sets were much smaller. Private commit is not recoverable physical RAM. Restarting graphics services is not part of normal unused-app closure. WSL reported a 15 GiB capacity but only about 0.5 GiB host working set; stopping it would not solve the missing 10+ GiB.

The practical unblock is a clean Windows session with enough free physical RAM and commit, followed by a fresh preflight. Additional pagefile capacity alone does not make RAM-resident expert inference fast. A RAM upgrade is a longer-term option, not a prerequisite being imposed or a purchase recommendation without checking the machine's supported configuration.

See [the experiment plan](A3B-OFFLOAD-PLAN-2026-09-24.md) for the serial matrix and correctness gates. No new A3B speed or coding-quality result is claimed.
