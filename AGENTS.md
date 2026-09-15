# Local AI lab working instructions

- Read README.md, METHODOLOGY.md, RESULTS.md, and RESEARCH-2026-09-15.md before selecting new experiments.
- Read RESULTS-2026-09-15.md for the latest executed round and Pi configuration corrections. Preserve failed runs and distinguish a CLI exit code from agent or program success.
- User preference, 2026-09-15: free VRAM before tests. Inspect nvidia-smi and ollama ps; unload resident models and stop confirmed idle model servers or other identified VRAM hogs before loading a benchmark model. Recheck GPU memory and record the before/after values. Do not indiscriminately kill Python, Node, browsers, the active assistant, Windows shell processes, or applications with unsaved work.
- Run one inference workload at a time. Unload the model after each experiment, including failures. Record context, quantization, server version, placement, and available RAM.
- Include popular Hugging Face variants, CPU-only approaches, and agent-harness comparisons (especially Pi). Downloads and likes indicate interest, not correctness.
- A model server (Ollama/llama.cpp), coding agent (Pi/Aider/OpenCode), and evaluator are separate experimental variables. Hold the others fixed when comparing one.
- Keep scripts and new notes ASCII. Windows and PowerShell are the primary environment.
- Preserve existing work. Do not commit or publish changes unless requested.
