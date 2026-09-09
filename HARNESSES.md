# Harnesses

Two very different things get called a "harness": the **inference engine** that serves a model, and the
**agent harness/runtime** that drives a model to read files, run commands, and use tools. We tested both.

## Inference harnesses (serve the model)

| Harness | Best for | Notes from this box |
|---|---|---|
| **Ollama** (what we use) | Single-user, quick start | GPU-accelerated on Blackwell, one-line pulls, OpenAI-compatible API at :11434. Auto-updates. Every agent tool below plugs into it. MoE-on-sm_120 crash fixed since 0.31.1. |
| **LM Studio** | GUI explorers | Native Windows app, easy model discovery. Good alternative if you prefer a UI over a terminal. |
| **llama.cpp** | Max control / performance | The C++ engine under most tools. Aggressive quantization, runs as a server. More setup. |
| **vLLM / SGLang** | Many concurrent users | ~16-20x Ollama throughput under load via PagedAttention + continuous batching. Wants Docker + more VRAM; overkill for one user. |

Verdict for 12 GB single-user: **Ollama** (or LM Studio if you want a GUI). vLLM is a production-serving
tool, not a desktop one.

## Agent harnesses (drive the model to do work)

| Harness | Model source | Our finding |
|---|---|---|
| **Claude Code** (cloud) | Frontier Claude | Best overall agentic reliability. The "conductor" for hard tasks. Not local. |
| **Aider** | local via Ollama | Works great on local models. Clean git-aware edits; auto-picks "whole" edit format for smaller models. Best **local coding** agent we tested. |
| **Open Interpreter** | local via Ollama | Executes shell/Python as tools; best **local shell/automation** agent. We also gave it a DuckDuckGo web-search tool so it researches instead of guessing. |
| **DeepSeek Harness (dsh)** | DeepSeek API / others | DeepSeek's open-source Claude Code rival, plugin-based ("everything is a plugin"). Works via the DeepSeek API. Dev preview: TUI not shipped yet (use `dsh web`), and on Windows its sandbox needs TMP/TEMP relocated outside the workspace. |
| **opencode** | local or cloud | Good with cloud providers, but **hangs on local Ollama** (known upstream bug); avoid for local. |

Verdict: **cloud Claude Code for the hard reasoning; Aider + Open Interpreter for local, private, offline
work.** A hybrid (cheap/bulk local, hard reasoning cloud) is the pragmatic setup.

## Hybrid routing (why)
Sending every task to a frontier model is expensive; sending everything to a local 8B is unreliable.
Route by difficulty: local models for scaffolding, boilerplate, mechanical passes, and quick lookups;
cloud for planning, complex logic, and review. Reported cost savings of that split are large without a
visible quality drop.
