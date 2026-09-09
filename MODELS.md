# Local models on 12 GB / 32 GB

## The one lesson that matters: active params, not total size

At 12 GB VRAM anything bigger than ~14B spills to system RAM. What happens next depends entirely on the
architecture:

- **Dense model**: every parameter computes on every token. Offloading half to CPU roughly halves onto a
  slow path -> a dense 30B lands around **4-5 tok/s**. Not usable.
- **MoE with few active params** (e.g. 30B total / 3B active): only the active experts compute per token,
  so CPU offload barely hurts -> a 30B-A3B MoE runs at **~34-37 tok/s**. Very usable.

So on a small box, prefer **low-active-param MoE** for anything above the dense-fits-on-GPU line.

## Tiers for this box

| Tier | Fits how | Speed | Examples |
|---|---|---|---|
| 7-9B dense/Q4-Q8 | 100% GPU | 90-120+ tok/s | qwen3:8b, qwen2.5-coder:7b, ornith-1.5:9b, qwen3.5:9b, granite4.2:8b |
| ~12-14B dense Q4 | 100% GPU (tight) | 60-70 tok/s | qwen3:14b, gemma3:12b, gemma4:12b |
| 20-30B MoE, few active | partial offload | 30-40 tok/s | qwen3:30b-a3b, qwen3-coder:30b, nemotron-3.5-lightning:30b, gpt-oss:20b |
| 30B dense | partial offload | ~4-5 tok/s | muse-glimmer:30b (works, too slow to use) |
| 100B+ / 1T | does not fit in 32 GB RAM | n/a | Kimi K2.x, DeepSeek V4-Pro (cloud/API only) |

## Recommended daily set
- **General:** qwen3:8b (fast) or qwen3:14b (stronger). Newer 9B options: qwen3.5:9b, ornith-1.5:9b.
- **Coding:** qwen2.5-coder:7b (fast) or qwen3-coder:30b (MoE, stronger, ~37 tok/s).
- **Reasoning:** deepseek-r1:8b, or any of the above with thinking enabled.
- **Agent workhorse (30B MoE):** nemotron-3.5-lightning:30b or qwen3:30b-a3b.

## Notes
- **Thinking models** (qwen3 family, ornith): keep thinking ON for reasoning; they do inline chain-of-thought.
  With thinking forced off they will fall for trick questions (e.g. the bat-and-ball trap).
- **Context vs speed (the real lever on this box):** a big context window grows the KV cache and forces
  more offload. Measured on qwen3-coder:30b: at 32k context it runs ~35 tok/s (53% offloaded to CPU,
  22 GB footprint); dropping to 8k context takes it to ~43 tok/s (footprint 19 GB, more on GPU). So for a
  30B MoE, lowering context is worth ~20%+ throughput.
- **Freeing VRAM barely helps a too-big model:** killing every non-OS GPU app freed only ~0.7 GB and left
  the 30B MoE speed unchanged, because a 22 GB model on a 12 GB card offloads ~half regardless. Desktop
  overhead is not the bottleneck; model-size-vs-VRAM is. Lower the context (or use a smaller model)
  instead of chasing VRAM.
- Models freshly under test this round (see RESULTS.md): granite4.2:8b, qwen3.5:9b, gpt-oss:20b.
