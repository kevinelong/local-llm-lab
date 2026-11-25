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
| **26B / 3.4B-active MoE, IQ2_XXS, vision** | **100 % GPU, 32K (11.7 GiB)** | **67.4 tok/s at 32K** | Inkling 2 Mini on llama.cpp `b12611`, not Ollama (`RESULTS-2026-11-22.md`, `INKLING-2-MINI-2026-11-21.md`) |
| **27B dense, 3.0 bpw (NariQ)** | **100 % GPU, 11.8 of 12.2 GiB** | **41.1 tok/s** | `nari-labs/Qwen3.8-27B-NariQ-GGUF` on its prebuilt Windows build; 30/30 battery, 26/30 reasoning |
| 26B/3.4B uncensored, IQ2_XXS | 100 % GPU | ~similar | `dealignai/Inkling-2-Mini-UNCENSORED-GGUF`; 27/30 twice, the miss a deterministic non-answer |
| 100B+ / 1T | does not fit in 32 GB RAM | n/a | Kimi K2.x, DeepSeek V4-Pro (cloud/API only) |

## One file, five engine rows (measured 2026-11-23/24)

The engine is worth more than the quantisation here. `Inkling-2-Mini` unsloth `UD-IQ2_XXS` (7.9 GB,
`inkling2_loop`) on this card, one engine loaded at a time, same prompt, 400-token budget:

| engine / file | generation tok/s | ten-task battery | evidence |
|---|---|---|---|
| **llama.cpp `b12611`, CUDA 13.5, our file** | **67.4** | **30/30** | `README.md` §0.3, `INKLING-2-MINI-2026-11-21.md` §Cross-engine |
| **Strata 0.1.66, our file** | **28.3** | 27/30 | `INKLING-2-MINI-2026-11-21.md` §Strata, `results/quality-strata-2026-11-24.json` |
| Colibri v2.2.0, Vulkan | 23.5 | 24/30 | `INKLING-2-MINI-2026-11-21.md` §Cross-engine, `results/quality-colibri-2026-11-23.json` |
| Colibri v2.2.0, CUDA | 17.4 | - | same section (its CUDA path is slower than its Vulkan path) |
| **Strata 0.1.66, their own SQ-10 pack** | **17.1** | 24/30, **one fabricated year** | `results/quality-strata-sq10-2026-11-24.json` |

Two findings, both of which outrank the speeds. **llama.cpp wins on every file tried on this card**: Strata streams
experts to a CPU pool beside the GPU and 12 GB is not where that pays off (its own hardware row is 24 GB), and
Colibri's published 40.9 tok/s is UD-Q4_K_XL on a 24 GB RTX PRO 4000, not IQ2_XXS on 12 GB. And **a bigger
quantisation bought a confident fabrication**: Strata's own SQ-10 pack (9.75 GiB, ~0.4 GiB left for KV and expert
slots) put the first crewed landing on a moon of Kepler-9d *"in 2021"*, where our two-bit file on the same engine
refused correctly - one item, three runs, and the opposite of what extra bits are supposed to buy. `README.md` §0.4
is the record of the correction that made these rows possible.

## What the box can code (n = 30 per APPS tier, 2026-11-24/25)

Grading is execution: a problem counts only when every test case passes. This is the limit to route on, because a
local coder at this size fails by returning a plausible constant (`1` where 3 was wanted), which ships silently where
a syntax error would not.

| band | `qwen3.5-27B` IQ4_XS, ~7 tok/s | `qwen3.5:9b`, 100 % GPU |
|---|---|---|
| APPS introductory | 18/30 = **60 %** (42-75 %) | 16/30 = **53 %** (36-69 %) |
| APPS interview | 21/30 = **70 %** (52-83 %) | 18/30 = **60 %** (42-75 %) |
| APPS competition | 6/30 = **20 %** (10-37 %, bounded: 4 of 30 hit the token budget) | 5/30 = **17 %** (7-34 %) |
| LCB v6 easy | **24/24 = 100 %** | 19/24 = 79 % (p = 0.05, at the edge) |
| LCB v6 medium | 24/37 = **65 %** (68 % stdin, 60 % functional) | 22/37 = **59 %** |
| LCB v6 hard | not run | 1/20 = 5 % (16 of 20 truncated: budget, not capability) |

**The routing rule this implies:** the cliff is *inventing the algorithm*, not program size or the interface - both
models parse input, write runnable programs and pass multi-case tests where the approach is recognisable, then fall to
about one in five when it must be derived. The 27B buys one to three problems in thirty for **13x the wall time**, so
**the fast 9B is the local default for coding** and the 27B is for work where a silent wrong constant is expensive
enough to pay 13x. Evidence: `README.md` §0.1-0.2, `INKLING-2-MINI-2026-11-21.md` §LiveCodeBench,
`benchmarks/coding-ladder-2026-11-24.py`, `benchmarks/lcb-ladder-2026-11-24.py`, and the per-run JSON under
`results/coding-apps-*-2026-11-24.json` and `results/lcb-*-2026-11-25.json`. Both halves were repaired before being
believed - eight problems do not locate a level (n=8 read 50 % where n=30 read 70 %) and a functional-problem parser
faulted as a model failure.

## Recommended daily set
- **General:** qwen3:8b (fast) or qwen3:14b (stronger). Newer 9B options: qwen3.5:9b, ornith-1.5:9b.
- **Coding:** qwen2.5-coder:7b (fast) or qwen3-coder:30b (MoE, stronger, ~37 tok/s). For real problem-solving the
  measured limit and the routing rule are in *What the box can code* above - the short version is that `qwen3.5:9b` is
  the default and a 27B earns its 13x only where a silent wrong answer is expensive.
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
  it is IQ2_XXS (2.06 bpw): 7.9 GiB of weights, 11.7 GiB resident with a 32K context, **67.4 tok/s at a 32,768 window**
  (llama-server, median of 3; flat within 3 % from 4K to 32K, `RESULTS-2026-11-22.md` §"the same question for
  Inkling"). It is also the only vision model in the store that fits, and the only one serving 32K. On a ten-task
  mechanical quality pass it scored **30/30 against qwen3:8b's and qwen3:14b's 27/30** - the references miss only the
  twenty-word summary. Read that as "no measured penalty from the quantisation on checkable work", not as "beats a 14B
  dense": see `RESULTS-2026-11-22.md` for what the battery does not measure (prose, long context beyond 4K on the
  Ollama side, and speed, which was contaminated in the first pass). Two practical notes: it thinks whether asked or not, so
  `max_tokens` must be in the hundreds or the reply comes back empty; and it needs llama.cpp `>= b12611`, which is
  built at `D:/build/llamacpp-b12611`. It is not served by Ollama. **The engine is the larger variable**: 67.4 tok/s on
  llama.cpp against 28.3 on Strata 0.1.66, 23.5 on Colibri's Vulkan path and 17.1 on Strata's own pack (*One file, five
  engine rows* above). One qualification on the 67.4: a `llama-cli` probe on the same build with `-ub 512 -fa on` and
  `-n 32` read **27.6 tok/s at ctx 32768** (`INKLING-2-MINI-2026-11-21.md` §"The 1.2 t/s was the default ubatch"), a
  2.4x disagreement with the server figure that no one has explained - so quote the server number, and name the
  harness beside it, because on this model the harness moved the rate by 45x once already.
