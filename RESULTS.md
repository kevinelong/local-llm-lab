# Results

All numbers from DARKTEXAS (RTX 5070 12 GB / 32 GB RAM), Ollama, temperature 0, 32k context unless noted.
tok/s is generation speed. "Placement" is the GPU share reported by `ollama ps`. All models listed passed
the correctness probes (bat-and-ball with thinking on, planets in order, and a code probe where applicable).

## Fresh round (2026-09-09)

| Model | Size | tok/s | Placement | Notes |
|---|---|---|---|---|
| qwen3.5:9b | 6.6 GB | **94** | 100% GPU | Best new general 9B. Fast, fully on GPU, correct. |
| granite4.2:8b | 5.3 GB | **74.6** | 95% GPU | IBM Granite 4.2. Strong, slight offload at 32k ctx. |
| gpt-oss:20b | 14 GB | **48.9** | 68% GPU | OpenAI open-weight MoE (~3.6B active). Good speed for 20B via MoE. |

## Full history (all rounds)

| Model | Class | tok/s | Placement | Practical? |
|---|---|---|---|---|
| granite3-moe:3b | tiny MoE | 378 | 100% GPU | yes (very fast, light) |
| qwen2.5-coder:7b | 7B dense | 116 | 100% GPU | yes (fast coder) |
| qwen3:8b | 8B dense | 109 | 100% GPU | yes |
| deepseek-r1:8b | 8B reasoning | 103 | 100% GPU | yes |
| ornith-1.5:9b | 9B | 98 | 100% GPU | yes |
| qwen3.5:9b | 9B | 94 | 100% GPU | yes (new) |
| granite4.2:8b | 8B | 74.6 | 95% GPU | yes (new) |
| gemma3:12b | 12B dense | 68 | 100% GPU | yes |
| gemma4:12b | 12B dense | 63 | 100% GPU | yes |
| qwen3:14b | 14B dense | 63 | 100% GPU | yes (best dense all-rounder) |
| gpt-oss:20b | 20B MoE | 48.9 | 68% GPU | yes (new) |
| qwen3:30b-a3b | 30B MoE / 3B active | ~37 | ~50% GPU | yes |
| qwen3-coder:30b | 30B MoE coder | ~37 | ~50% GPU | yes (strong local coder) |
| nemotron-3.5-lightning:30b | 30B MoE / 3B active | 33.8 | 35% GPU | yes (agent-focused) |
| muse-glimmer:30b | 30B dense | 4.5 | 50% GPU | NO (too slow) |
| Kimi-K2.7-Code | 1T MoE | n/a | does not fit | NO (cloud/API only) |
| DeepSeek V4-Pro | 1.6T MoE | n/a | does not fit | NO (cloud/API only) |

## Reading the table
- Everything at/above ~48 tok/s is comfortably interactive here.
- The cliff is muse-glimmer:30b at 4.5 tok/s - a **dense** 30B. Compare to the 30B **MoE** models at
  33-37 tok/s. Same total size, ~8x speed difference, entirely due to active-parameter count under offload.
- The 100B+ / 1T models are not a speed problem, they are a "does not fit in 32 GB RAM at all" problem.

## Takeaways
- Newest sweet spot on this box: **qwen3.5:9b** (fast general) and **granite4.2:8b**, plus **gpt-oss:20b**
  when you want a bigger MoE that still runs.
- For 30B-class, stick to low-active MoE (qwen3-coder:30b, nemotron-3.5-lightning:30b, qwen3:30b-a3b).
- Keep the harness (Ollama) current for Blackwell MoE support.
