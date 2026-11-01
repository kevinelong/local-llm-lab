# Hardware (the box these notes are from)

"DARKTEXAS" - a Dell Tower Plus EBT2250, used as a deliberately modest local-AI test bench.

| Component | Detail | Implication for local LLMs |
|---|---|---|
| GPU | NVIDIA RTX 5070, **12 GB** GDDR7 (Blackwell, compute 12.0) | Binding constraint. ~11.5 GB usable. Fits 7-14B at Q4/Q8 fully on GPU. |
| CPU | Intel Core Ultra 9 285 (24 cores) | Handles CPU offload for MoE experts; fine for dense offload only at small scale. |
| RAM | **64 GB** DDR5-5600 (2 x 32 GB, both slots full; board max 64 GB), upgraded from 32 GB part-way through the lab - see README "The box". Measured 2026-11-01: **63.46 GiB visible, 67.46 GiB commit limit** | Caps how much can offload. Cannot hold 100B+ models even quantized. |
| Disk | C: ~600 GB free, D: ~950 GB, G: | Big weights (100B+) go on D:. |
| OS / shell | Windows 11, PowerShell primary | Watch encoding: keep scripts pure ASCII (PS 5.1 mangles non-ASCII). |

## The ceilings that shaped every decision
- **12 GB VRAM**: model + KV cache must fit or it offloads to system RAM (slower). At 32k context the KV
  cache is non-trivial; dropping context to 8k keeps more layers on GPU.
- **64 GiB RAM**: the wall for offload. Measured 2026-11-01: **63.46 GiB visible, 67.46 GiB commit limit**.
  The 63.2 GiB expert set we never loaded therefore *almost* fits and still does not, once the OS, the pinned
  resident region and file-cache headroom are paid - which is why 100B+ dense and 1T MoE stay out, and why
  the **page cache**, not capacity, is the live question on this box.
- **Blackwell (sm_120)**: needed a modern CUDA build. Early Ollama (0.30.x) crashed on MoE kernels on
  sm_120; fixed from 0.31.1. If you are on a 50-series card, keep the harness current.
- **A RAM upgrade did happen, and it did not unlock the big models**: the board is now at its 64 GB maximum
  and still cannot run the smallest usable Kimi/DeepSeek-V4-Pro quant (344 GB+). Only a different class of
  machine can. What the second 32 GB bought is headroom for the resident ladder and the file cache.
