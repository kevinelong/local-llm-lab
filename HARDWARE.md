# Hardware (the box these notes are from)

"DARKTEXAS" - a Dell Tower Plus EBT2250, used as a deliberately modest local-AI test bench.

| Component | Detail | Implication for local LLMs |
|---|---|---|
| GPU | NVIDIA RTX 5070, **12 GB** GDDR7 (Blackwell, compute 12.0) | Binding constraint. ~11.5 GB usable. Fits 7-14B at Q4/Q8 fully on GPU. |
| CPU | Intel Core Ultra 9 285 (24 cores) | Handles CPU offload for MoE experts; fine for dense offload only at small scale. |
| RAM | **32 GB** DDR5-5600 (2 UDIMM slots, 1 free; board max 64 GB) | Caps how much can offload. Cannot hold 100B+ models even quantized. |
| Disk | C: ~600 GB free, D: ~950 GB, G: | Big weights (100B+) go on D:. |
| OS / shell | Windows 11, PowerShell primary | Watch encoding: keep scripts pure ASCII (PS 5.1 mangles non-ASCII). |

## The ceilings that shaped every decision
- **12 GB VRAM**: model + KV cache must fit or it offloads to system RAM (slower). At 32k context the KV
  cache is non-trivial; dropping context to 8k keeps more layers on GPU.
- **32 GB RAM**: hard wall for offload. A model whose weights exceed ~28-30 GB (after the OS take) cannot
  even be held, let alone run. This is why 100B+ dense and 1T MoE are out.
- **Blackwell (sm_120)**: needed a modern CUDA build. Early Ollama (0.30.x) crashed on MoE kernels on
  sm_120; fixed from 0.31.1. If you are on a 50-series card, keep the harness current.
- **RAM upgrade would not help the big models**: maxing this board to 64 GB still cannot run the smallest
  usable Kimi/DeepSeek-V4-Pro quant (344 GB+). Only a different class of machine can.
