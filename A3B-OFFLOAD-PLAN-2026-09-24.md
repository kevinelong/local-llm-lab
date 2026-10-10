# Serial A3B offloading experiment

Prepared 2026-09-24. Research and resource inspection are complete; model inference is held for RAM. This is separate from the frozen Bonsai CPU experiment and does not change its gates.

## First test and prerequisites

Use installed Qwen3-Coder-30B-A3B-Instruct, isolated llama.cpp b10883 CUDA 13.3, 8k context, f16 KV, flash attention on, one slot, temperature zero for deterministic correctness probes. The first placement is 36 CPU expert layers; compare 32/40/48 only when their own fresh estimates pass. Start with 8 CPU threads, then test 16, then 24; performance may saturate below the hardware thread count.

Run the resource-only check (it never loads model tensors):

```powershell
python C:\Users\kevin\local-llm-lab\benchmarks\a3b_preflight_20260924.py --output C:\Users\kevin\ai_bench\a3b-offload-20260924-v1\preflight-next.json
```

The output path must be new. Check physical RAM, commit headroom and VRAM independently; require no resident Ollama models, no other inference processes, and no run locks. The JSON resource eligibility is not permission to skip process or runtime verification. A process name alone does not establish that an unrelated server is idle.

Capture runtime version, SHA256, `--list-devices`, CLI help and actual model placement. Require CUDA0 to be the RTX 5070. Never silently accept a CPU-only fallback or let automatic fitting alter context/placement during a controlled comparison. Use loopback only. Acquire a run lock before loading; close only the process created for this run in a `finally` cleanup path. Unload between configurations and verify GPU/host memory returns near baseline.

The planned first server command is below; **do not run while the memory check is held**:

```powershell
& C:\Users\kevin\ai_bench\a3b-offload-20260924-v1\runtime\llama-server.exe --model C:\Users\kevin\.ollama\models\blobs\sha256-1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a --host 127.0.0.1 --port 8097 --ctx-size 8192 --parallel 1 --n-gpu-layers 999 --n-cpu-moe 36 --fit off --threads 8 --threads-batch 8 --batch-size 512 --ubatch-size 128 --flash-attn on --cache-type-k f16 --cache-type-v f16
```

This is a prepared configuration, not a tested successful load. Default memory mapping is retained. Do not force mlock/pinning in a RAM-constrained session. Inference harness preparation, live monitoring and cleanup must precede the actual launch; no server is left running by this research task.

## Small adaptive matrix

1. **Placement screen:** same Coder GGUF, 36/32/40/48 CPU expert layers, 8 threads. Reject ineligible rows without loading. For 48 layers, `--cpu-moe` is the semantic equivalent to compare once.
2. **Thread screen:** best eligible placement at 8/16/24 threads, keeping batch settings fixed. Measure wall time as well as server token timings.
3. **Operation placement:** compare stock behavior with `--no-op-offload` only after confirming support in the pinned binary. This can change prefill as well as decode; neither is assumed faster.
4. **Cache fork:** exact same GGUF, prompts and base settings, pinned source SHA; cache capacity 8/16/32 per-layer slots where supported. Measure cache hits, transfer bytes and peak memory. Do not invent equivalent flags across forks. Full backing retained in RAM requires a fresh higher host estimate.
5. **Family comparison:** installed Thinking-2507; optional Instruct-2507; Qwen3.5 and Qwen3.6 selected quantizations. Parse each downloaded file and derive architecture-specific KV/recurrent-state and weight placement sizes. The current Qwen3 estimator deliberately rejects unsupported architectures.
6. **EXL3 comparison:** separate EXL3 model artifact and runtime pin; unpinned control before pinned arena. Include conversion/quantization identity in results. KTransformers and ik_llama remain later candidates if the simpler paths miss latency/quality targets.

Avoid a full Cartesian product. Screen placement, then threads, then cache capacity. Keep each change attributable and stop unproductive rows early.

## Measurements and correctness

For each viable setup, record one load, one warmup and three measured repetitions of short (~512 tokens) and long (~4096 tokens) prompts with 256 generated tokens. Save exact token IDs, seeds, templates, prompt hashes, CLI/environment, model digest, runtime digest and raw timings outside candidate workspaces. Distinguish cold load, prompt processing, time to first token, decode throughput and full response latency. Prefix reuse must be disabled or reset between comparison repetitions, or explicitly labeled as a separate warm-cache test.

Record host physical availability, commit headroom, server working set/private bytes, GPU memory, CPU/GPU utilization, and hard page faults or disk paging where accessible. Host backing and duplicated GPU caches must be accounted for separately. Abort a running test if free physical RAM falls below 3 GiB, commit below 2 GiB, or free GPU memory below 512 MiB; a monitoring harness must enforce these thresholds, not merely log them. Stop on sustained paging, timeout, OOM, device fallback, malformed streams, or incorrect expert selection. Preserve failed logs.

Before ranking an experimental expert cache, compare reference logits or a fixed perplexity set at the same quantization and context. Investigate discrepancies beyond normal numerical tolerance; text that merely looks coherent is insufficient. No exact token equality promise across different kernels or quantizations. The documented cache mapping bug is a reason to include routing correctness checks.

For coding usefulness, reuse the existing independent evaluator-v2 and isolated candidate workspace principles. Run six bounded repair tasks as a development screen, then a separately declared untouched task set for confirmation. Score correctness, tool-call validity, safe file behavior, complete stream termination, timeouts and elapsed time separately. Thinking models get an explicitly recorded reasoning/output budget; do not force a thinking-only model into a purported no-thinking condition. A 256-token throughput probe is not a coding benchmark.

No promotion on speed alone. Select a configuration only if correctness survives, latency improves for the intended workload, and memory stays within its reserves. Do not merge these results into historical scores.

## Current hold and next action

Normal unused-app closure found no eligible windows. A clean Windows session with sufficient free RAM is the practical next step. Rebooting or closing the active assistant was not performed. Rerun preflight, build the monitored serial runner, and launch only passing configurations. The authorized GoProverbs ten-feature weight sweep remains queued after this local-model investigation.
