# How we test

Small, repeatable, and honest. Every model gets the same treatment against the Ollama API.

## What we measure
Before each test: inspect GPU processes and loaded models, unload resident models, stop confirmed idle VRAM hogs, and record GPU memory before/after cleanup. Preserve active work and Windows/assistant processes. Run one model at a time; unload it afterward. For CPU-only tests, explicitly disable GPU execution and verify the backend log and GPU memory. See AGENTS.md for the user's standing preference.

1. **Placement** - `ollama ps` after the model loads: is it `100% GPU` or a `NN%/NN% CPU/GPU` split?
   This is the single best predictor of whether it will be fast.
2. **Generation speed** - tokens/sec from the API timing fields: `eval_count / (eval_duration / 1e9)`.
   We use a fixed ~150-200 token generation at temperature 0 for a stable number.
3. **VRAM** - `nvidia-smi --query-gpu=memory.used` while the model is hot.
4. **Correctness probes** - a few quick checks:
   - Reasoning trap: the bat-and-ball question (answer $0.05). Run with **thinking enabled**, because
     forcing thinking off is what makes models fall for the trap - that would test the wrong thing.
   - Code: write a small function (fizzbuzz / is_prime / roman numerals) and we execute it to verify.
   - Factual/instruction: list the eight planets in order (checks basic accuracy + instruction-following).

## Why these choices
- **temperature 0** so the numbers are reproducible.
- **placement first** because on a 12 GB box speed is decided by how much offloads, which is decided by
  model size + context, not by the GPU's raw throughput.
- **execute the code**, do not eyeball it. A model that writes plausible-but-wrong code fails here.
- **thinking on for reasoning**: we learned the hard way that forcing thinking off changes the result of
  the bat-and-ball probe entirely; we report the model's real capability, not a gotcha.

## Gotchas we hit (so you do not have to)
- **Blackwell + MoE**: Ollama < 0.31.1 crashed loading MoE on sm_120 (`shared object initialization
  failed`). Fix was upstream; keep the harness current on 50-series cards.
- **hf downloads dropping**: huggingface_hub `snapshot_download` aborts the whole pull on one connection
  reset and can falsely report success. For giant repos we download file-by-file with `curl --retry ...
  -C -` and verify each file's size against the HF API. A token does not fix connection resets.
- **PowerShell 5.1 encoding**: a stray em-dash in a `.ps1` read as ANSI becomes garbage and breaks the
  parse. Keep scripts pure ASCII.

## The benchmark script
The September 15 round uses `benchmarks/round_20260915.py`: 16k context, three short correctness checks, a throughput prompt, and the existing dependency-task-manager spec. Its short probes explicitly disable thinking; these results describe that operating mode, not maximum reasoning capability. Agent runs record thinking configuration separately. See RESULTS-2026-09-15.md for configuration changes and limitations.

See `benchmarks/bench-model.ps1`. It takes a model name, warms it, prints tok/s + placement, and runs the
probes. Point it at any local Ollama model.
