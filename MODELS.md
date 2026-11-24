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
| ~12-14B dense Q4 | **not** 100 % GPU at 32K; 100 % at 8K or below | 62 tok/s at 8K, **19 tok/s at 32K** (measured, qwen3:14b) | qwen3:14b, gemma3:12b, gemma4:12b |
| 20-30B MoE, few active | partial offload | 30-40 tok/s | qwen3:30b-a3b, qwen3-coder:30b, nemotron-3.5-lightning:30b, gpt-oss:20b |
| 30B dense | partial offload | ~4-5 tok/s | muse-glimmer:30b (works, too slow to use) |
| **26B / 3.4B-active MoE, IQ2_XXS, vision** | **100 % GPU + 32K** | **~52 tok/s** | Inkling 2 Mini (llama.cpp, not Ollama - see `RESULTS-2026-11-22.md`) |
| **27B dense, 3.0 bpw (NariQ)** | **100 % GPU, 11.8 of 12.2 GiB** | **41.1 tok/s** | `nari-labs/Qwen3.8-27B-NariQ-GGUF` on its prebuilt Windows build; 30/30 battery, 26/30 reasoning |
| 26B/3.4B uncensored, IQ2_XXS | 100 % GPU | ~similar | `dealignai/Inkling-2-Mini-UNCENSORED-GGUF`; 27/30 twice, the miss a deterministic non-answer |
| 100B+ / 1T | does not fit in 32 GB RAM | n/a | Kimi K2.x, DeepSeek V4-Pro (cloud/API only) |

## Recommended daily set
- **General:** qwen3:8b (fast) or qwen3:14b (stronger). Newer 9B options: qwen3.5:9b, ornith-1.5:9b.
- **Coding:** qwen2.5-coder:7b (fast) or qwen3-coder:30b (MoE, stronger, ~37 tok/s).
- **The 2026-11-22 quality pass changed the shortlist** (`RESULTS-2026-11-22.md`): on ten mechanical tasks,
  `qwen3.5:9b` and Inkling 2 Mini both score **30/30**, `qwen3:8b` and `qwen3:14b` **27/30** each (both miss only the
  twenty-word ceiling), and **`gemma4:12b` scores 24/30 with six non-answers** - asked for five words or twenty it
  reasons for 25,000-50,000 characters and never answers, at any budget tried up to 16,384 tokens; on the harder
  BBH/GSM8K suite it produced only 4 of 30 answers (all four correct) and 26 empty `finish=length` rows. As served
  here it is not a candidate for anything that needs a short answer. `qwen3.5:9b` is
  the strongest daily option of the five if speed matters (89.6 tok/s on 6.1 GiB); Inkling is what you take when you
  need 32K or an image read on the card.
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
- **Inkling 2 Mini (2026-11-22) is the first model here that is 26B-class and runs entirely on the 12 GB card**, because
  it is IQ2_XXS (2.06 bpw): 7.9 GiB of weights, 11.6 GiB resident with a 32K context, ~52 tok/s generation. It is also
  the only vision model in the store that fits, and the only one serving 32K. On a ten-task mechanical quality pass it
  scored **30/30 against qwen3:8b's and qwen3:14b's 27/30** - the references miss only the twenty-word summary. Read
  that as "no measured penalty from the quantisation on checkable work", not as "beats a 14B dense": see
  `RESULTS-2026-11-22.md` for what the battery does not measure (prose, long context beyond 4K on the Ollama side,
  and speed, which was contaminated in the first pass). Two practical notes: it thinks whether asked or not, so
  `max_tokens` must be in the hundreds or the reply comes back empty; and it needs llama.cpp `>= b12611`, which is
  built at `D:/build/llamacpp-b12611`. It is not served by Ollama.
