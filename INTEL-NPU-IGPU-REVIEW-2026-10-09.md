# Intel NPU / Arc iGPU review, 2026-10-09

Kevin asked whether a generic "optimize your local AI on Intel hardware" write-up (NPU via
Ollama/LM Studio, Windows ML, OpenVINO, quantization, sparsity, driver updates) is worth acting on for
this lab. Short answer: **one item is already our practice, one item is a real idea in a different
shape than the write-up means, and the rest is wrong for this machine or a no-op.** The measured facts
are below so the next session does not re-derive them.

## What the machine actually has (read-only, 2026-10-09)

| Component | Evidence | Value |
|---|---|---|
| NPU | `Get-PnpDevice -Class ComputeAccelerator` | **Intel(R) AI Boost**, status OK, `PCI\VEN_8086&DEV_AD1D`, driver **32.0.100.4778** (2026-04-27) |
| Arc iGPU | `Win32_VideoController` | **Intel(R) Graphics**, driver **32.0.101.8860** |
| Discrete GPU | `nvidia-smi` | RTX 5070, driver **610.60**, 12,227 MiB; CUDA compute 12.0 |
| Ollama | `ollama --version` | **0.40.0** |
| Ollama's backends | its own `server.log` | `inference compute ... library=CUDA compute=12.0 name=CUDA0 description="NVIDIA GeForce RTX 5070" driver=13.3` **plus** `dropping integrated GPU; to enable, set OLLAMA_IGPU_ENABLE=1` for `Vulkan1 "Intel(R) Graphics"` |
| The lab's measured engine | `llama-server --list-devices` (b11461) | `CUDA0: NVIDIA GeForce RTX 5070 (12226 MiB)` - **and nothing else** |
| OpenVINO / IPEX-LLM | `find_spec` on Windows python and in WSL | **not installed** (WSL has `uv`, so installing is cheap) |

Two facts to hold on to: **Ollama 0.40.0 here has no NPU backend at all** - its GPU list is CUDA plus an
opt-in Vulkan iGPU path, and the NPU appears nowhere in it - and **the lab's measured runtime sees only
CUDA0**, so nothing in the current evidence set touches the NPU or the iGPU at all.

## The write-up, item by item

| Claim | Verdict for this box |
|---|---|
| "Ollama / LM Studio use the NPU" | **No for Ollama** (0.40.0 has no NPU/OpenVINO backend; proven by its own log). LM Studio's NPU support is a limited OpenVINO preview, not a general path. |
| "Windows ML auto-loads an NPU execution provider" | True of the framework, but it serves apps built on it; no lab harness consumes it, and CUDA already wins for models of this size. |
| "Use 4-bit quantized models" | **Already our practice** - Q4_K_M, Q8_0, IQ1_M, Q2_0, PQ2 are all in the measured set, and we have *measured* the trade (e.g. Strata's Q2_0 streamed matches the resident Q4_K_M 35B-A3B cell for cell; the 4B vs 9B decision models differ by 1.2 macro points). |
| "Update Intel/NVIDIA drivers" | **Already current** for the AI stacks (NVIDIA 610.60 / CUDA 13.3; NPU 32.0.100.4778; iGPU 32.0.101.8860). Changing a driver mid-series is a *new configuration* here (new root + declaration), not a tweak. |
| "Use OpenVINO / IPEX-LLM" | The only route that genuinely reaches the NPU (`ov_genai_llm`, `benchmark_app`). It is a **new engine arm**, not an optimization, and the predicted result is a large deficit: the iGPU shares DDR5 while the 5070 has ~7x the bandwidth and far more compute. |
| "Enable sparsity" | Not a free win: needs 2:4-structured sparse weights *and* sparse kernels. Nothing in our GGUF set qualifies. |
| "16 GB base, stick to 7-8B" | **Wrong for this machine**: 64 GB DDR5-5600 + 12 GB VRAM. We run a 78B MoE (Kolibri Q4) and a 30B-class MoE fully resident, and Strata streams a ~66 GB Q2_0 pack from disk. |

## What is actually worth doing, and in what shape

1. **The real idea hiding in the write-up is a second device for the *small* track, not acceleration
   for the big one.** `OLLAMA_IGPU_ENABLE=1` makes Ollama place work on the Arc iGPU via Vulkan, and
   the NPU is reachable through OpenVINO. That matters because our *decision/embedding* track (small
   models, e.g. Jev-class 0.8B, the 46 synthetic + 18 archived windows) was repeatedly blocked - by the
   6 GiB worker cap (now removed) and by GPU contention - and it does not need a 12 GB card. A
   **declared new track** could run it on iGPU/NPU while the RTX 5070 stays free for the suites.
   Caveat: the lab's *one inference workload at a time* rule exists for evidence reasons, so this must
   be a new declared track with its own root, not a change to any measured screen.
2. **An OpenVINO arm as a documented comparison**, i.e. the honest way to price the NPU/iGPU: same
   task, same prompts, OpenVINO GenAI on iGPU/NPU vs llama.cpp on CUDA, reported as a rate with the
   prediction stated first. Expected outcome: a large loss; the value is the number and the
   "it cannot do X" boundary, not speed.
3. **Nothing to do about drivers** - they are current, and moving them would invalidate comparability
   without a declaration.

Not proposed: replacing llama.cpp/Strata with an Intel stack. The measured path is CUDA on a discrete
card; the NPU's budget (13 TOPS INT8 for Arrow Lake-S NPU 3, per Intel's spec - not measured here) and
the iGPU's shared bandwidth put both well behind it for the
model sizes this lab actually runs.
