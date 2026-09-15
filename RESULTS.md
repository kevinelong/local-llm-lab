# Results

Latest experiment: [September 15 local agent and CPU round](RESULTS-2026-09-15.md), using 16k context and a separate probe set. Historical measurements below retain their original settings.

All numbers from DARKTEXAS (RTX 5070 12 GB / 32 GB RAM), Ollama, temperature 0, 32k context unless noted.
tok/s is generation speed. "Placement" is the GPU share reported by `ollama ps`. Except where the
"Correctness notes" section says otherwise, models passed the probes (bat-and-ball with thinking on,
planets in order, and a code probe where applicable).

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
| gemma4:26b | 26B MoE | n/a | crashed on load | pre-0.31.1 Blackwell MoE bug; deleted. Would run now, not re-tested. |
| Kimi-K2.7-Code | 1T MoE | n/a | does not fit | NO (cloud/API only) |
| DeepSeek V4-Pro | 1.6T MoE | n/a | does not fit | NO (cloud/API only) |

## Reading the table
- Everything at/above ~48 tok/s is comfortably interactive here.
- The cliff is muse-glimmer:30b at 4.5 tok/s - a **dense** 30B. Compare to the 30B **MoE** models at
  33-37 tok/s. Same total size, ~8x speed difference, entirely due to active-parameter count under offload.
- The 100B+ / 1T models are not a speed problem, they are a "does not fit in 32 GB RAM at all" problem.

## Correctness notes (per-model nuances)
- **Thinking-mode matters.** ornith-1.5:9b, the qwen3 family, and the small coders get the bat-and-ball
  trap RIGHT with thinking enabled (inline chain-of-thought to $0.05) but fall for the $0.10 trap if you
  force thinking off. Always leave thinking on for reasoning tasks. This is why the probe is run with
  thinking on: forcing it off tests the wrong thing.
- **gemma4:26b never produced a result** on this box in the crash-era round (see the crash row) - it is the
  one model that did not pass, because it would not load. All others listed produced correct probe answers.
- **muse-glimmer:30b was correct but unusable** - right answers, 4.5 tok/s. Correctness is necessary, not
  sufficient; speed is the gate at 12 GB.

## Agent-harness task results
Beyond raw model speed, we ran real agentic tasks through each harness and verified the output (executed
the code / checked the file). These are the measured outcomes:

| Harness | Model | Task | Result | Time |
|---|---|---|---|---|
| Aider | qwen2.5-coder:7b | write fizzbuzz.py | correct (executed, asserts pass) | 11.3 s |
| Aider | qwen3-coder:30b | write roman.py (int<->roman, both ways) | correct + robust (range check, verified round-trip) | 62.6 s |
| Open Interpreter | qwen2.5-coder:7b | find 3 largest files, write sizes.txt | correct order | 33.9 s |
| Open Interpreter (web search) | qwen2.5-coder:7b | "newest Node LTS?" via DuckDuckGo | searched + grounded, but 7B picked a near-latest version | ~20 s |
| Open Interpreter (web search) | qwen3:14b | same task | correct (24.18.0) with source cited | - |
| opencode (localhost, no apiKey) | qwen2.5-coder:7b | write fizzbuzz.py | HUNG - request never reached Ollama (config: localhost->IPv6 + no apiKey) | killed >12 min |
| opencode (127.0.0.1 + apiKey) | qwen2.5-coder:7b | write fizzbuzz.py | reaches Ollama, responds, but tool-call returned as text, not executed | 13.8 s |
| opencode (127.0.0.1 + apiKey) | qwen3-coder:30b | write fizzbuzz.py | SUCCESS - file created, runs correctly | 40 s |
| DeepSeek Harness (dsh) | DeepSeek V4-Pro (API) | "what is 2+2" headless | correct ("4") | - |

Reading it: local coding via **Aider** works and is grounded (it executes/tests); **Open Interpreter**
handles shell + web-search but the 9-14B tier synthesizes better than 7B; **opencode** is unusable on
local Ollama; **dsh** works against the DeepSeek cloud API. See HARNESSES.md for the qualitative writeup.

## Takeaways
- Newest sweet spot on this box: **qwen3.5:9b** (fast general) and **granite4.2:8b**, plus **gpt-oss:20b**
  when you want a bigger MoE that still runs.
- For 30B-class, stick to low-active MoE (qwen3-coder:30b, nemotron-3.5-lightning:30b, qwen3:30b-a3b).
- Keep the harness (Ollama) current for Blackwell MoE support.
