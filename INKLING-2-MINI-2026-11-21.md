# Inkling 2 Mini ("Inkling mini"): the release, the GGUFs, and what 12 GB buys - 2026-11-21

Read-only research. **Nothing downloaded as a model, no engine started, no inference, no benchmark,
`ai_bench` untouched.** Methods: HF REST API (`/api/models?...&blobs=true`, tree sizes), **two HTTP range
GETs of the first 6-12 MiB of a GGUF** parsed locally for metadata (no engine involved), `gh api` /
`gh pr view`, the vendor card, one model card per quantiser, one Reddit thread (archive), one third-party
VRAM article. Gates at writing time: **D: 474.56 GiB free** (479.18 used of 953.74), **C: 82.53 GiB free**,
`D:/models` **193 GB** in five directories, **no Inkling directory anywhere on D:**.

## 0. The answer in six lines

1. **"Inkling mini" is `thinkingmachines/Inkling-2-Mini`** - Thinking Machines' 26.4B-total / 3.4B-active
   (5.4B effective per token) **looped** MoE, **Apache-2.0**, released **2026-11-20**. Not vision-only, not
   audio: it is text+image in, text out.
2. **GGUFs exist and are on three reputable mirrors** - Unsloth (10 dynamic quants + an MTP/DSpark drafter),
   ggml-org (IQ4_NL / Q8_0 / BF16), bartowski (20 quants), plus lmstudio-community. Revisions in section 3.
3. **On this box only the very small end fits the card**: `UD-IQ1_S` **7.23 GiB**, `UD-IQ1_M` **7.47**,
   `UD-IQ2_XXS` **7.90 GiB** fit 12 GB at 32K with `-ub 128`; `UD-Q2_K_XL` 8.51 GiB is edge; **everything at
   4-bit and above is 13.7-28.7 GiB of peak VRAM and needs expert/CPU offload** (12 GB card, 63.5 GiB RAM).
4. **The trap is not the file size, it is a 32-bit position-bias table llama.cpp builds per ubatch**:
   `2 x 24 heads x ctx x ubatch x 4 B` = **0.75 GiB at 32K/ub128**, 3.00 GiB at 32K/**default ub 512**,
   12.0 GiB at 128K/default. It is why every 128K setup fails to load on 24 GB cards down to 2-bit files,
   and why `-ub` is the first flag to set on 12 GB.
5. **Mainline llama.cpp needs `>= b12611`** (that tag is the `#32704` merge itself). `b12606`, our 11-20/11-21
   gate, does **not** contain it, and without it the second and third loop passes lose their per-expert
   scales: **perplexity ~130 instead of 7.65**, i.e. gibberish.
6. **Not downloaded** - reasoning and the exact next step in section 6. D: has 474.56 GiB free, so space was
   never the constraint; **a loader is**.

## 1. Naming: four "Inkling" families, and the sub-name runs the wrong way

The lab's 11-21 scan already had "Inkling 2 Mini" as an Ollama line item. What "mini" collides with:

| Repo | What it is | Note |
|---|---|---|
| `thinkingmachines/Inkling` | first-gen, **1,221,755 downloads** | `image-text-to-text`; the name people type |
| `thinkingmachines/Inkling-Small` | first-gen small, 860,032 dl | unrelated to the Inkling 2 family |
| `thinkingmachines/Inkling-2-Small` | **48 layers, 384 experts, hidden 4608** | the **big** one (the 594B tier per the third-party article); llama.cpp `#32217` "add Inkling 2 support (text + vision)" merged 2026-11-14T23:51:32Z for the family, `#32268` followups still open |
| **`thinkingmachines/Inkling-2-Mini`** | **24 layers, 128 experts, hidden 2304** | **this note**; llama.cpp `#32694` |

So **"Small" is bigger than "Mini"** in the Inkling 2 generation, and the two older `Inkling` /
`Inkling-Small` repos are a different architecture again. Spellings that resolve here: `inkling2_loop`
(the llama.cpp arch string), `inkling2` (the older, non-looped arch), `inkling2v` (its vision projector),
`Inkling2LoopForConditionalGeneration`, `inkling-2-mini` (Ollama library). Strings that resolve to **nothing
loadable**: `Inkling-mini`, `Inkling-mini-GGUF`, `inkling2-mini`.

## 2. What the model actually is (config + GGUF metadata, read first-hand)

`thinkingmachines/Inkling-2-Mini`, **sha `b85c3cfa615fc413cc9af3379f491b963f3b586a`**, last modified
2026-11-21T22:23:18Z, created 2026-11-17T00:26:57Z, 7,944 downloads, 3,271 likes, `pipeline_tag
image-text-to-text`, **`license: apache-2.0`**, card release date **November 20, 2026**.

| field | value |
|---|---|
| params | **26.4B total, 3.4B active, 5.4B effective per token** (each extra loop pass adds ~1.0B active) |
| layers | **24 stored**, loop core **6..18 (12 layers) x 3 passes** -> **48 layer applications per token** |
| MoE | **128 experts, 8 active**, expert FFN 1152, shared experts 0, route scale 8.0, gate bias |
| attention | 24 heads / **8 KV heads** / head_dim 128; **hybrid local/global** - `sliding_window 1024`, global layers **5, 11, 17, 23** |
| extras | shortconv kernel 4 (`l_cache` 4), attn-res block 6, qk L2 clip, final logit softcap 30.0 |
| vocab | 201,024 (unpadded 200,058), gpt2-style BPE, **eos 200006** |
| context | **1,048,576 claimed** (config `model_max_length` and `inkling2_loop.context_length` both) |
| vision | separate tower, 23 layers, hidden 1024, patch 20; needs an `mmproj` file |
| MTP | `mtp_config`, 3 layers, block 8, **shipped as `mtp.safetensors` in the base repo** |
| original quant | **mixed NVFP4 (layers 0-19 experts) + MXFP8 (20-23)**, ~20 GB checkpoint |

Vendor figures quoted on the card (their numbers, not measured here): **SWE-bench Verified 79.2**, SWE-bench
Pro v2 (Hard) 77.9, DeepSWE v1.1 48.2, Terminal Bench v2.1 71.6, MCP Atlas 82.7, LongBench v2 66.9,
BrowseComp 79.0, MMMU Pro 74.9, AA Index v5.0 20.1. Vendor hardware line: DGX Spark, **32 GB Apple silicon**,
*"other GPUs ... with 32 GB or more VRAM recommended"* - i.e. **12 GB is below the vendor's own floor**, which
is exactly why section 5 matters.

Two consequences of the loop that decide everything below: **each pass keeps its own KV cache and conv
state** (24 stored layers become 48 cache slots: **8 full-context, 40 with a 1,024 window**), and the
per-layer attention-bias table in llama.cpp scales with context x ubatch.

## 3. The GGUFs that exist (revision = repo head sha at read)

| repo | revision | lastModified | dl | licence | what is in it |
|---|---|---|---|---|---|
| **`unsloth/Inkling-2-Mini-GGUF`** | **`45fd08764f2b0bf16b03a5483a80e5c7aaec8772`** | 2026-11-22T04:22:49Z | 238,152 | **apache-2.0** | 10 UD dynamic quants (IQ1_S .. UD-Q8_K_XL), imatrix, 3 mmproj (F32/F16/BF16), **DSpark drafter** (Q8_0 0.37 GiB, BF16 0.60), and a **`Mainline_Support/` mirror in mainline tensor layout** (`.gguf_file`, rename after download) |
| **`ggml-org/Inkling-2-Mini-GGUF`** | **`e8a2cecf0e78914f07cc27b9be711a9b2c7561d9`** | 2026-11-21T15:47:32Z | 61,987 | card declares **no** `license` key (base is Apache-2.0) | **IQ4_NL, Q8_0, BF16**, imatrix 0.085 GiB, mmproj Q8_0/BF16, KL table on card |
| **`bartowski/thinkingmachines_Inkling-2-Mini-GGUF`** | **`76d57028717ed7c63f5e90de75234cae0bc9b360`** | 2026-11-21T06:59:31Z | 5 | **apache-2.0** | **20 static quants IQ2_XXS .. bf16**, imatrix, 2 mmproj, per-quant tensor-layout json |
| **`lmstudio-community/Inkling-2-Mini-GGUF`** | `23c938b028945d4b0fa9f71fb603b5cd1a683e71` | 2026-11-21T00:26:23Z | 7,148 | apache-2.0 | Q4_K_M, Q6_K, Q8_0, mmproj |
| `robcowart/Inkling-2-Mini-GGUF` | `a8afe857337fe34561fc9a6d1f3e49af35346f09` | 2026-11-21T15:43:14Z | 0 | apache-2.0 | Q4_K_M 15.86 GiB, BF16 48.64 GiB, **no mmproj** |
| `askthesultans/Inkling-2-Mini-GGUF` | `faa8606835daa35dec6d47bd9a8ef2ca29a71f5d` | 2026-11-21T10:06:49Z | 0 | - | q4_k_m 16.28 GiB, q8_0 25.91 GiB |

**The last two were recorded as EMPTY repos by the 11-21 scan and are not empty now.** `robcowart` was read
empty at 13:43Z and held a Q4_K_M + BF16 by 15:43Z; `askthesultans` (read at 09:07Z) had two files by 10:06Z.
That is the 10-23/10-24 "an empty repo cannot become a fact" rule failing in the *other* direction - a repo
can also stop being empty inside the same window. `robcowart`'s Q4_K_M was **header-verified here**: GGUF v3,
**704 tensors** (same count as ggml-org's pack), `general.architecture inkling2_loop`, 24 blocks, loop 6..18
x3, 128/8 experts, `general.license apache-2.0` - a real conversion, but **0 downloads** and no mmproj.

**Not sized, named only**: `AtomicChat/Inkling-2-Mini-{GGUF,Uncensored-GGUF}` (11,888 / 9,540 dl),
`InterpreticAI/Inkling-2-Mini-{IQ3_XXS-,}GGUF` (852 / 726), `nokeepai/Inkling-2-Mini-Unbound` (0 dl, quantised
by bartowski as `bartowski/nokeepai_Inkling-2-Mini-Unbound-GGUF`, `58ca4910862c...`, apache-2.0, IQ2_XXS
**9.61 GiB**), plus ~60 more repos created in 40 hours. The 100-repo page cap makes that a floor.

## 4. File sizes, exactly (GiB = bytes / 1024^3)

Unsloth UD (dynamic; `Mainline_Support` files hold the same bytes):

| quant | GiB | mean KLD vs UD-Q8_K_XL | same top token |
|---|---|---|---|
| UD-IQ1_S | **7.23** | 0.0911 | 89.4 % |
| UD-IQ1_M | **7.47** | 0.0867 | 90.2 % |
| UD-IQ2_XXS | **7.90** | 0.0726 | 90.6 % |
| UD-Q2_K_XL | **8.51** | 0.0595 | 91.6 % |
| UD-IQ3_XXS | 10.86 | 0.0269 | 94.7 % |
| UD-Q3_K_XL | 12.70 | 0.0174 | 96.3 % |
| UD-IQ4_XS | 14.65 | 0.0109 | 97.7 % |
| UD-Q4_K_M | 15.47 | 0.0108 | 97.9 % |
| UD-Q4_K_XL | 16.42 | 0.0107 | 98.0 % |
| UD-Q8_K_XL | 21.30 | reference | - |

Also in that repo: mmproj **F32 1.19 / F16 0.60 / BF16 0.60 / Q8_0 0.32 GiB**, DSpark drafter **Q8_0 0.37**,
dspark BF16 0.60. ggml-org: **IQ4_NL 16.42**, Q8_0 25.91, BF16 **48.64**, mmproj Q8_0 0.32, mmproj BF16 0.60.
bartowski spans **IQ2_XXS 9.61** -> IQ2_S 10.31 -> Q2_K 11.06 -> IQ2_M 11.12 -> IQ3_XXS 12.39 -> Q3_K_S 12.51
-> IQ3_XS 12.82 -> Q4_0 14.03 -> IQ4_XS 14.05 -> IQ3_M / Q3_K_L 14.21 -> IQ4_NL 15.00 -> Q4_1 15.45 ->
Q4_K_S 15.71 -> **Q4_K_M 17.38** -> Q5_K_M 19.76 -> Q6_K 23.00 -> Q8_0 25.91 -> bf16 48.64. His static quants
cost 1.5-2 GiB over Unsloth's dynamic twin at the same name (Q4_K_M 17.38 against UD-Q4_K_M 15.47).
ggml-org's card gives KL against BF16 on wikitext-2: **Q8_0 0.0030 (97.6 %), IQ4_NL 0.0095 (95.5 %)**.

## 5. What fits 12 GB (12,227 MiB, ~11.3 GiB usable with a display attached)

Peak VRAM = file + KV + bias table + mmproj + ~0.6 GiB of buffers, at **32K context, `-ub 128`, f16 KV,
mmproj Q8_0**. KV and bias are **derived here from the GGUF metadata** (arithmetic, not measured):
KV = 8 full slots x 4 KiB/token + 40 x 1,024 x 4 KiB = **1.16 GiB** at 32K (a third party's independent
number for the same thing is 1.19 GiB - the loop is why 24 layers cost 48 slots); bias = 2 x 24 x 32,768 x
128 x 4 B = **0.75 GiB**.

| pack | file GiB | peak @32K ub128 | verdict on 12 GB |
|---|---|---|---|
| unsloth UD-IQ1_S | 7.23 | **10.06** | fits, best margin |
| unsloth UD-IQ1_M | 7.47 | **10.30** | fits |
| **unsloth UD-IQ2_XXS** | **7.90** | **10.73** | **fits - the sweet spot** |
| unsloth UD-Q2_K_XL | 8.51 | 11.34 | edge: fits only text-only or at 16K |
| unsloth UD-IQ3_XXS | 10.86 | 13.69 | no |
| unsloth UD-Q3_K_XL | 12.70 | 15.52 | no |
| unsloth UD-Q4_K_XL / ggml-org IQ4_NL | 16.42 | 19.25 | no - needs ~9 GiB of experts on CPU |
| unsloth UD-Q4_K_M | 15.47 | 18.30 | no |
| bartowski IQ2_XXS | 9.61 | 12.44 | no (static 2-bit is *bigger* than UD 2-bit) |
| bartowski Q4_K_M | 17.38 | 20.21 | no |
| lmstudio / askthesultans Q4_K_M | 16.28 | 19.11 | no |
| ggml-org Q8_0 | 25.91 | 28.74 | no |
| any BF16 | 48.64 | 51.47 | no (RAM-only, and above the 20 GB dense rule) |

**Everything at 4-bit and above needs more VRAM than 12 GB, by 6-17 GiB.** Raise `-ub` and the whole column
moves: at the **default ub 512** the bias alone is **3.00 GiB at 32K**, 6.00 at 64K, 12.00 at 128K - so
UD-IQ2_XXS at 32K becomes 12.98 GiB and stops loading. `-fa on` shrinks the buffer but not the table.
`-ub 64` buys another 0.38 GiB back at 32K (0.75 at 64K) at prefill cost.

Two real 12 GB-class data points, both second-hand, both with the 17.6 GiB IQ4_NL that does *not* fit:

- **RTX 3060 12 GB, llama.cpp CUDA `-ngl 18`** (12/16/20 layers identical, `-ngl 99` OOM): **8.7 tok/s**
  decode, **384 tok/s** prefill at 512 tokens, 323 at 2,048; at a **40,960-token prompt 2.86 tok/s**, and
  the default batch does not even start there (**13.2 GB compute buffer, 11.3 GB with `-fa on`**, fits only
  at `-ub 128`). CPU-only: 11.6 / 50.
- **Same card, `RustingStrata`** (a Rust GGUF engine, `github.com/RustingStudio/RustingStrata`): **31.2 tok/s**
  CUDA, 27.5 Vulkan, 11.6 CPU-only, **16.7 tok/s at 40K** - it keeps the hot experts resident in VRAM and
  moves the split at runtime, which is the only reason a 17.6 GiB file writes at 31 tok/s on 12 GB.
- Context for scale, other cards (all third-party): RTX 3090 24 GB llama.cpp `b12606` **Q4_K_M 32K: 48.4
  tok/s / 655 prefill**, Q3_K_M 128K `-ub 128` 18.98 GiB; T4 16 GB 22.3 tok/s; 2x Titan V 20-30 tok/s.

## 6. What the lab would need, and the next concrete step

**Chat template: yes, it is in the file.** Header-parsed from `ggml-org`'s IQ4_NL: `tokenizer.chat_template`
present, **6,868 chars**, `reasoning_effort` map `none 0.0 / minimal 0.1 / low 0.2 / medium 0.7 / high 0.9 /
xhigh 0.99 / max 0.99`, roles `<|message_user|> <|message_model|> <|message_system|> <|message_tool|>`,
i.e. tool calling is in the template. Load with **`--jinja`**. The template does **not** come from
`tokenizer_config.json` - that file has **no `chat_template` key** (it carries `response_template`, and the
card points at the `tml-renderers` package). What the base repo does carry is a separate
**`chat_template.jinja`** file, and llama.cpp ships `models/templates/thinkingmachines-Inkling.jinja`.
Embedded sampling defaults in the GGUF: **temp 1.0, top_k 50, top_p 1.0, min_p 0.0**; Unsloth's run guide
says temp 1.0 with **no truncation** (top-k off, top-p 1, min-p 0) - the two disagree on top_k, so a first
run should declare one.

**Engine gates (these are the blockers, not disk):**

- **llama.cpp `>= b12611`.** `#32694` "model : Inkling 2 Mini" merged **2026-11-20T22:01:08Z** (commit
  `29b52d398b`, confirmed present in `b12606`'s commit list; a third-party article dates its appearance to
  `b12600`). `#32704` "re-share the loop slots after the scale pass" merged
  **2026-11-21T11:10:39Z**, merge commit **`690b87d88151dbd775bb6eff5581663688785928`**; by `compare`,
  **`b12608` and `b12609` are behind it (3 and 2 commits), `b12611` is identical to it, `b12620` is ahead 9**,
  newest tag seen `b12627`. **`b12606`'s newest commit is 2026-11-21T08:26:55Z, so our 11-20/11-21 gate
  `>= b12606` does NOT contain the fix** - Unsloth's own notice: without `#32704` the second and third loop
  passes lose their per-expert NVFP4 scales and **perplexity is ~130 against 7.65**.
- **Layout split.** Unsloth's root `UD-*` files use Unsloth's looped layout and need Unsloth's fork
  (`b12588-mix-c0c3de8`) or Studio; **mainline must use `Mainline_Support/*.gguf_file`, renamed to `.gguf`**
  (same bytes, mainline tensor naming; on UD-Q8_K_XL mainline gives perplexity 7.653 against 7.651, KLD
  0.0006). ggml-org and bartowski packs are already mainline-layout.
- **DSpark / MTP drafter: not in mainline.** `#32218` open since 2026-11-13T16:15:43Z; the drafter (0.37 GiB)
  is worth 0 in mainline today, so the lab's MTP lever cannot be used on this family yet.
- **Ollama**: library page `inkling-2-mini` is live (23.1K downloads, caps `vision tools thinking`, the
  NVFP4 ~20 GB checkpoint - **not a 12 GB object**). The Windows GGUF failure the 11-21 scan recorded,
  **`#19817` "unknown architecture (inkling2_loop/inkling2) and projector (inkling2v)"**, opened
  2026-11-21T13:52:30Z, was **closed 2026-11-21T15:08:01Z** - so a fixed Windows path exists only above our
  **`v0.40.17`** pin.
- **Strata**: no evidence of `inkling2_loop` support in any version we track; `RustingStrata` (a different
  project) is the only 12 GB-optimised engine with a row.

**Why nothing was downloaded.** D: has **474.56 GiB free** and the recommended pack is **8.2 GiB**, so space
never decided it. Three things did: (1) **no engine on this box can load the architecture** - the llama.cpp
gate is `>= b12611` and unbuilt, Strata has no support, and the Ollama fix postdates our pin; (2)
MODEL-STORE's standing rule wants **uncensored**, and the uncensored variants (nokeepai Unbound IQ2_XXS
9.61 GiB, AtomicChat, Derisked) are **static-quant, non-mainline-verified, 0-download** repos - a first run
on them is a task check, not a load check; (3) a file with no loader is inventory.

**Next concrete step, cheapest first.**

1. **Build the loader, not the model**: llama.cpp at **`>= b12611`**, `-DGGML_CUDA=ON` for sm_120, same
   target list as always (`llama-cli llama-server llama-mtmd-cli`).
2. **Then** pull the smallest mainline-layout pack that fits, with its projector:
   `hf download unsloth/Inkling-2-Mini-GGUF --include "Mainline_Support/Inkling-2-Mini-UD-IQ2_XXS.gguf_file" "mmproj-F16.gguf"` -
   **7.90 + 0.60 = 8.50 GiB, revision `45fd08764f2b0bf16b03a5483a80e5c7aaec8772`**, then `mv` to `.gguf`.
   Drop `mmproj` (0.60) and use the Q8_0 projector (0.32) if the fit is tight.
3. **One measurement, text only, 32K, `-ub 128`, `-fa on`, `--jinja`**: `llama-bench -p 512,2048 -n 64`.
   Declare it as a first row, not a benchmark. The bar to beat is the 3060's **8.7 tok/s decode / 384
   prefill** at IQ4_NL with 18 layers resident - an IQ2_XXS that fits entirely should beat decode and lose
   quality (KLD 0.0726, 90.6 % top-token agreement, which is a real risk for an agentic coding model).
4. **If decode and a task check both hold**, then price `UD-Q4_K_XL` (16.42 GiB, KLD 0.0107) with experts
   offloaded - the 12 GB card holds ~9 GiB of weights, 63.5 GiB of RAM holds the rest, and every 4-bit
   configuration on this box is that trade. **DSpark** waits for `#32218`.

## 7. What was searched, and what this note does not claim

Searched: HF `?search=inkling` sorted by createdAt **and** by downloads (100 per page, ~100+ repos seen),
author `thinkingmachines`, exact repo lookups for unsloth / ggml-org / bartowski / lmstudio-community /
robcowart / askthesultans / AtomicChat / nokeepai, the vendor card and `config.json`, base
`tokenizer_config.json`, the GGUF header of ggml-org's IQ4_NL (range GET, metadata parsed), the GGUF header
of robcowart's Q4_K_M, `gh pr view 32694 / 32704 / 32218`, tag `compare` arithmetic, `ollama.com/library/
inkling-2-mini`, `thinkingmachines.ai/news/inkling-2-mini/` (200), one Reddit thread and one VRAM article.

**Not claimed here.** No number in section 5 was measured on this box: the KV and bias figures are
**arithmetic from the GGUF metadata**, and the two 12 GB-class throughput rows are **other people's cards**.
The 1M context is the **card's claim**; the largest verified run seen is 40K on 12 GB and 128K on 24 GB.
Reddit needed the **Arctic Shift archive** to read at all - the direct HTML still fails, so the
"25 consecutive 403s" rule in AGENTS.md now has a workaround rather than an exception.

**Three-line summary.** Inkling 2 Mini is Thinking Machines' Apache-2.0 26.4B/3.4B looped MoE (24 layers,
core 6-18 run 3x, 128 experts, 1M claimed context, image input), released 2026-11-20, with real GGUFs from
unsloth `45fd08764f2b`, ggml-org `e8a2cecf0e78`, bartowski `76d57028717e` and lmstudio `23c938b02894`. On
12 GB only `UD-IQ1_S` 7.23 / `UD-IQ1_M` 7.47 / **`UD-IQ2_XXS` 7.90 GiB** fit at 32K with `-ub 128` (peak
10.1-10.7 GiB); everything from `UD-IQ3_XXS` 10.86 up needs 13.7-28.7 GiB and expert/CPU offload. The gate is
the loader, not disk: llama.cpp must be **`>= b12611`** (else perplexity ~130), mainline needs Unsloth's
`Mainline_Support` files, DSpark is still `#32218`.

## Acquired 2026-11-22: the loader source and the pack

**Downloaded (permission stands: models on D:, space stated, revision and hash recorded).**

| what | from | revision | bytes | sha256 |
|---|---|---|---|---|
| `Inkling-2-Mini-UD-IQ2_XXS.gguf` (was `Mainline_Support/...gguf_file`) | `unsloth/Inkling-2-Mini-GGUF` | `45fd08764f2b0bf16b03a5483a80e5c7aaec8772` | 8,486,237,632 | `2f953a44281cf861b19ccfdb2ce65f7648e1e92bda4af3729893604fd907c544` |
| `mmproj-F16.gguf` | same repo, same revision | as above | 639,348,160 | `3bff75ffeb2d6e0371ba7bd42e30d26a7d98aea681fa44b03b5a20891cfa2c5f` |

Both hashes were checked with `sha256sum` against the LFS oids the HF API reports for that revision - equal.
Total **8.50 GiB** in `D:/models/inkling-2-mini` (**8.5 GB** on disk); D: was **474 GiB free** before, **465 GiB** after.
The `Mainline_Support/` copy was renamed to `.gguf` (same bytes, mainline tensor naming); the root `UD-*` file of that
repo was **not** taken, because it needs Unsloth's fork rather than mainline llama.cpp.

**The header, read from the file itself** (first 4 MB, GGUF v3): `general.architecture = inkling2_loop`,
`general.name = Inkling-2-Mini`, `general.size_label = 128x1.8B`, 744 tensors, 63 key/value pairs. So the pack is the
mainline-layout conversion and its architecture name is the one `#32694` added.

**The loader.** `ggml-org/llama.cpp` cloned to `D:/build/llamacpp-b12611`, `git checkout b12611` -> HEAD
`690b87d88 model : inkling2_loop share the loop slots after the scale pass (#32704)`, which is the fix itself.

**The toolchain, without an installer.** The CUDA toolkit is **not** installed on this box and the shell is not
elevated, so the 3.56 GB `.exe` was rejected in favour of NVIDIA's **redist archives** (`redistrib_12.9.1.json`),
unpacked into `D:/tools/cuda-12.9` (1.1 GiB on disk): `cuda_nvcc` 12.9.86, `cuda_cudart` 12.9.79, `cuda_cccl`
12.9.27, `libcublas` 12.9.1.4 - all four sha256s verified against the manifest. `ninja` 1.13.2 in `D:/tools/ninja`.
**Configure lesson:** the Visual Studio generator fails with *"No CUDA toolset found"* because it wants the VS CUDA
integration, which a hand-assembled toolkit does not have; `-G Ninja` with `-DCMAKE_CUDA_COMPILER=<nvcc.exe>` and
`cl` from `vcvars64.bat` configures cleanly (OpenSSL absent, so the server has no HTTPS - irrelevant locally).

## Measured 2026-11-22: the loader works, the pack loads, and it is slow

Built `D:/build/llamacpp-b12611/build-cuda` (`llama-cli`, `llama-server`, `llama-mtmd-cli`), `-DGGML_CUDA=ON`,
`CMAKE_CUDA_ARCHITECTURES=120`, MSVC 19.44 + nvcc 12.9.86 + Ninja 1.13.2. `llama-cli --version`:
`1.0.0-dev (build 12611, commit 690b87d88)`; `--list-devices`: `CUDA0: NVIDIA GeForce RTX 5070 (12199 MiB,
11035 MiB free)`.

**Load, 4K context, `-ngl 99`, IQ2_XXS + no projector:**
`arch = inkling2_loop`, `n_embd 2304`, `n_layer 48` (48 applications: 24 stored, core looped 3x), `n_expert 128`.
`offloaded 49/49 layers to GPU`, `CUDA0 model buffer = 7847.07 MiB`, `CUDA0 compute buffer = 584.22 MiB`,
`CPU_Mapped model buffer = 234.65 MiB`. Second load in the same run is the one that offloads - the first pass
logged `CUDA0 model buffer size = 0.00 MiB`, so read the **second** block when judging offload.

**Speed at 4K, 12 GB card, defaults:** prompt **3.1 t/s**, generation **1.2 t/s** for a 3.4B-active MoE. That is
not explainable by the card (7.85 GiB resident) and is the next thing to chase: `-ub 128`, `-fa on`, and whether
the looped layers fall back to CPU in the CUDA path are the three suspects. Nothing faster was claimed and no
benchmark was run - this is one 4-token greeting and one 8-token one.

**Not tried yet:** the projector (`mmproj-F16.gguf`, 0.60 GiB) needs `llama-mtmd-cli` and an image; 32K context
(the note's estimate is 10.7 GiB peak, which the measured 7.85 + 0.58 model/compute buffers leave room for);
`llama-server` under the lab's usual gates.

Gates at the load: **37.41 GiB free physical, 33.27 GiB commit free**, GPU 11.0 GiB free of 12.2.

### The 1.2 t/s was the default ubatch, and it costs 45x

Same model, same card, same build, only the flags changed (`-ngl 99`, 4K, `-n 32`, one prompt):

| flags | prompt t/s | generation t/s |
|---|---|---|
| defaults (ub **2048**) | 3.1 | **1.2** |
| `-ub 128` | 32.8 | 54.2 |
| `-ub 128 -fa on` | 39.5 | 53.7 |
| `-ub 512 -fa on` | 39.9 | 54.5 |

`llama-cli`'s `-ub` defaults to the batch size (2048), and on `inkling2_loop` that default is catastrophic - it is
the whole 45x, not the card and not the architecture. **512 is as fast as 128**, so the note's earlier `-ub 128` is a
VRAM habit rather than a speed rule.

**Context cost, `-ub 512 -fa on`, measured, not derived:**

| ctx | CUDA0 compute buffer | prompt t/s | generation t/s |
|---|---|---|---|
| 4096 | 584.22 MiB | 34.6 | 32.1 |
| 32768 | **3356.22 MiB** | 32.9 | **27.6** |

With the model buffer at 7847 MiB, 32K is ~11.2 GiB of buffers plus overhead: it loaded and generated on the 12 GB
card, which is tighter than this note's own earlier arithmetic (10.7 GiB) suggested. GPU idle after the runs: 1,362
of 12,227 MiB, so nothing was left resident.

### Vision, 2026-11-22: the projector works in `llama-cli`, and `llama-mtmd-cli` is the broken tool

`llama-cli.exe -m <IQ2_XXS> --mmproj mmproj-F16.gguf --image <png> -p "Describe this image in one short sentence."
-n 160 -c 2048 -ub 512 -fa on --no-warmup -ngl 99 -st`

- `Loaded media from '...20261022-154057_1024x1024_seed1235.png'`, **prompt 415.5 t/s, generation 60.4 t/s**
  (the image is inside that prompt rate).
- Answer, complete: *"a green dragon figurine/statue with wings, fangs, standing on a rocky base against a neutral
  gray background"* - checked against the picture itself: green dragon figurine, wings, fangs, rocky base, grey
  backdrop. Every element right, nothing invented.
- Projector load: `422 tensors`, `609.71 MiB`, `vision hparams: image_size 640, patch 20, n_merge 2,
  projection_dim 2304, image_min_pixels 1600, image_max_pixels 6553600`, `mtmd_backends: using CUDA0 backend`.

**`llama-mtmd-cli` is the one that fails, and not on the model.** It fast-fails (`0xC0000409`) right after
`get_dummy_batch: warmup with image size = 1280 x 1280` and `Using specialized template: Inkling`, and it does the
same with **no image at all**, with `-dev none` (CPU only), with `--no-op-offload`, at 2048 ctx and at ub 256. So the
crash is in that tool's own init, not in the projector, the picture, the GPU or memory. Use `llama-cli` (or
`llama-server`) for vision on this build until upstream fixes it.

**Context worth knowing before blaming our setup:** the Inkling 2 Mini bugs open upstream on 2026-11-22 include
`#32778` (prompts over ~96 tokens give all-`?` output), `#32785` (KV cache locality does not match layer placement),
`#32755` (`--n-cpu-moe` with long prompts produces garbage), `#32777` (fit should prioritise looped MoE layers) and
`#32773` (DSpark drafter on 16 GB). The architecture is days old; the notes above are one box's measurements, not a
verdict on the model.

### `llama-mtmd-cli` fixed: it was an uncaught exception, not the projector

The tool died with `0xC0000409` and no message. With stdout made unbuffered (a CLI that can die must not lose
the lines that lead to the fault) the log ended at `Using specialized template: Inkling`, and a trace inside
`common_chat_params_init_inkling` never ran - so the crash was not in the vision path at all. Wrapping the
context construction in `try/catch` printed the whole story on the first try:

    E main: the chat template could not be built: this custom template is not supported, try using --jinja

The built-in C++ Inkling template **throws**, nothing catches it in `mtmd-cli`, and MSVC turns that into
`abort()` -> `__fastfail` -> `0xC0000409`. `--jinja` (the template inside the GGUF, 6,868 chars) works, which is
why `llama-cli --mmproj --image` had been fine while `mtmd-cli` never was.

**The fix, 29 lines in `tools/mtmd/mtmd-cli.cpp`:**
1. `setvbuf(stdout|stderr, _IONBF)` in `main`, so a crash cannot swallow its own log.
2. The context is built inside `try/catch`; on an exception it logs the reason and **retries once with
   `params.use_jinja = true`**, announcing the retry. A model whose built-in template is unsupported now loads
   instead of killing the process.

Verified: `rc=0`, and `llama-mtmd-cli` answered *"a fantasy dragon figurine, green with tan belly, large wings,
horns, standing on rocky base"* - the same picture `llama-cli` described correctly. Patch kept at
`patches/llama-mtmd-cli-jinja-fallback-2026-11-22.patch` (applies on top of `b12611`); not sent upstream, and the
root cause - the built-in Inkling template claiming a template it cannot render - is theirs to fix.

### Workstation, same day: four elevated taskbar pins

There were **no** Terminal, PowerShell or WSL shortcuts on the taskbar at all, so there was nothing to flag; the
four were created in `%APPDATA%\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar` and given
`SLDF_RUNAS_USER` (bit 13 of the LinkFlags DWORD at 0x14 in the `.lnk`):

| shortcut | target | flags |
|---|---|---|
| `Windows Terminal (Admin).lnk` | `%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe` | `0x60DF`, runas=True |
| `Windows PowerShell (Admin).lnk` | `%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe` | `0x60DF`, runas=True |
| `PowerShell 7 (Admin).lnk` | `%LOCALAPPDATA%\Microsoft\WindowsApps\pwsh.exe` | `0x60DF`, runas=True |
| `WSL (Admin).lnk` | `%SystemRoot%\System32\wsl.exe` | `0x60DF`, runas=True |

The flag is written as a byte patch because `IShellLinkDataList` does not survive PowerShell's COM casts
(`-as` returns null); Explorer was restarted so the pins render. Each one now raises UAC on launch - that is what
the flag means, and it is why the earlier CUDA *installer* would not have needed it either: the redist route
never needed elevation.

### llama-server at 32K, 2026-11-22: up, resident, and both text and vision answer over HTTP

Gates at start: **35.88 GiB free physical** (floor 9), **32.88 GiB commit free** of 71.96 (floor 8), GPU **1,608 of
12,227 MiB**, WSL **Stopped**, no engine running, port 8080 free. Ollama on 11434 was the only listener and holds no
model.

    llama-server.exe -m Inkling-2-Mini-UD-IQ2_XXS.gguf --mmproj mmproj-F16.gguf \
      --host 127.0.0.1 --port 8080 -c 32768 -ub 512 -fa on -ngl 99 -np 1 --jinja

- `loaded multimodal model`, `n_slots = 1, n_ctx_slot = 32768`, `listening on http://127.0.0.1:8080`.
  `/props` confirms `n_ctx=32768`, `slots=1`, `chat_template_chars=6867` (the GGUF's own template, so `--jinja` is
  what is in force).
- **VRAM resident: 11,567 of 12,227 MiB.** That is the 7847 MiB model + 3356 MiB compute + the projector, and it
  leaves about 660 MiB - it fits and nothing else should be loaded beside it.
- `common_fit_params: failed to fit params to free device memory: n_gpu_layers already set by user to 99, abort` is
  the fitter declining to second-guess an explicit `-ngl 99`, not an error.
- Text, `/v1/chat/completions`: *"A lighthouse stands tall on the rocky coast, sweeping its steady beam across the
  dark sea to guide ships safely home."* (`finish=stop`).
- Vision over the same endpoint, image as base64 `image_url`: **`Dragon`** (`finish=stop`) - the projector answers
  through the server, not only through `llama-cli`.

**One behaviour to know: the thinking block eats a short budget.** With thinking on (the default) a 64-token request
returns `finish_reason: length` with `content` **empty** and the whole budget in `reasoning_content`. `"reasoning_effort":
"none"` in the request produces the answer directly - the same lever as the closed upstream `#32763`. Any harness
that asks this model for short answers must send that field or budget for the thinking tokens.

### CUDA 13.5.0 adopted, 2026-11-22: the prompt-processing gain is real, generation is noise

The plan in `PLAN-CUDA-13-2026-11-22.md` was run after the restart. Eight redist archives
(`redistrib_13.5.0.json`: nvcc 13.5.37, cudart 13.5.37, cccl 13.3.5, cuda_crt, nvml dev, cublas 13.10.0.20,
nvjitlink 13.5.37, nvvm 13.5.37, **794 MiB**) verified sha256-against-manifest and assembled into
`D:/tools/cuda-13.5` (2.0 GiB). Second build dir `build-cuda135`, same source (`b12611`), Ninja + `cl` + nvcc 13.5,
`CMAKE_CUDA_ARCHITECTURES=120`. The 12.9 tree and its binaries were left untouched as the baseline.

**A/B, same prompt, same flags (`-ub 512 -fa on -ngl 99`, `-n 32`), three passes each, medians:**

| toolchain | ctx | prompt t/s | generation t/s |
|---|---|---|---|
| 12.9.86 | 4K | 35.9 | 49.6 |
| 12.9.86 | 32K | 34.2 | 51.8 |
| **13.5.0** | 4K | **43.6** | 52.3 |
| **13.5.0** | 32K | **44.5** | 52.2 |

- **Prompt processing: +21 % at 4K, +30 % at 32K**, and every one of the three passes ordered the same way
  (12.9: 31.0/36.7/35.9 and 34.2/36.4/33.7; 13.5: 39.9/43.6/44.5 and 43.9/46.8/44.5). That is the newer cuBLAS
  heuristics on the GEMM path, which is exactly where the earlier reasoning put the only plausible gain.
- **Generation: inside the noise** (+5 % at 4K, +0.8 % at 32K) - not a claim.
- **VRAM unchanged in kind:** buffers are byte-identical (`7847.07` model, `3356.22` compute at 32K), the resident
  server moved 11,567 -> **11,648 MiB** of 12,227.
- **Vision is faster too:** the same picture through `llama-cli --mmproj` went 415.5 -> **489.4 t/s** prompt
  (60.4 -> 63.8 generation), and `mtmd-cli`'s jinja fallback still answers.

**Server now runs 13.5.0**: `/props` `n_ctx=32768`, 1 slot, template 6867 chars; text answers
(*"The sea stretches endlessly, its restless blue breathing in and out like a living, ancient rhythm."*) and the
image answers **Dragon**, both `finish=stop` with `"reasoning_effort": "none"`.

**The trap that cost a cycle: CUDA 13 keeps its runtime DLLs in `bin\x64`, not `bin`.** A 13.5 build run with only
`D:/tools/cuda-13.5/bin` on `PATH` dies with *no output at all* (`llama-cli --version` returns 0xC0000135-ish silence),
which reads like a broken build rather than a missing `cudart64_13.dll`. Both directories go on `PATH`;
`serve-inkling-32k.bat` now does.

**Decision rule applied:** adopt only beyond ~3 % at equal or lower VRAM - prompt processing cleared it at both
contexts, VRAM moved 81 MiB, so 13.5.0 is the default and 12.9 stays on disk as the measured baseline.

### Thinking eats the budget even with `reasoning_effort: none`, 2026-11-22

Three requests against the running server, same endpoint:

| prompt | max_tokens | result |
|---|---|---|
| ~443 tokens (long passage) | 128 | **empty content**, `finish=length` - then the *identical* request returned an 81-char answer, so it is flaky, not a threshold |
| ~64 tokens (short summary task) | 64 | **empty content**, `finish=length`, `reasoning_length=444` |
| the same | **512** | `finish=stop`, **"The keeper kept the lamp lit for thirty years."**, `reasoning_length=593` |

So `reasoning_effort: none` does **not** switch thinking off on this model in `llama-server`; the thinking block runs
anyway and a small budget is spent entirely on it. Anything driving this model needs **`max_tokens` in the hundreds**
(or `--reasoning-budget 0`), otherwise it returns nothing and looks broken. Upstream `#32778` claims prompts over
~96 tokens produce all-`?` output; that did **not** reproduce here - the long prompt answered correctly once and
returned empty once, which is a budget/thinking effect rather than the reported one, and worth re-testing when the
architecture settles.

### Cross-engine, 2026-11-23: Colibri v2.2.0 on our own file

`JustVugg/colibri` v2.2.0 (released 2026-11-22) advertised support for this model from unsloth's GGUFs, including
**`UD-IQ2_XXS` - the exact file this lab stages**. It is the first second engine that needs no conversion and no source
build: a `windows-x86_64-cuda.zip` overlay (70 MB, sha256 verified against `SHA256SUMS.txt`) on the 22.6 MB main
archive, `coli import` our GGUF, `coli doctor` (all checks ok, one `placement.plan` warning: *VRAM tier clamped*), then
`coli serve` on a spare port.

| | engine / path | generation tok/s | ten-task battery | aggregation at 8K (5 reps, 4,096 budget) |
|---|---|---|---|---|
| **llama.cpp `b12611`, CUDA 13.5** | CUDA | **67.4** | **30/30** | 1/5 |
| Colibri v2.2.0 | **Vulkan** (its own choice) | 23.5 | 24/30 | **2/5** |
| Colibri v2.2.0 | CUDA (`COLI_VULKAN=0`) | **17.4** | - | - |

Same prompt, same 400-token budget, same model file, one engine loaded at a time.

**Three results worth keeping:**

1. **llama.cpp is 2.9x Colibri on its Vulkan path and 3.9x on its CUDA path** - for this file, on this card. Colibri
   streams MoE experts into a 6.3-6.6 GiB tier (2,804-2,901 experts) and runs the dense part beside it, a different
   design from llama.cpp's full offload; it is slower here, and its published 40.9 tok/s is at UD-Q4_K_XL on a 24 GB
   RTX PRO 4000, not at IQ2_XXS on 12 GB.
2. **Colibri's CUDA path is slower than its Vulkan path** (17.4 vs 23.5), which is presumably why the engine routes
   Inkling-2 to Vulkan even in the CUDA build - worth knowing before anyone "fixes" it with `COLI_VULKAN=0`.
3. **The same weights lose two length constraints on the other engine.** 24/30: `exactly_five_words` returns six words
   ("soft silver curtains falling gently down", every run) and `summary_20` 23-25 against a limit of 20, while every
   checkable item - the arithmetic trap, the JSON shape, the executed `is_prime`, the needle, the refusal - is 3/3.
   Identical file, identical items, 30/30 on llama.cpp. So on this model, instruction compliance is an **engine and
   prompt-template** property, not a weight property, and a score is only comparable within one engine.

Practical notes: Colibri requires the `model` field on every request (without it: `The model None does not exist`), it
picked up the vision tower from `mmproj-F16.gguf` automatically, and `coli stop` did not free port 8090 - a `python.exe`
still held it, so the port had to be cleared by hand before restarting.

### The two shortlist packs, 2026-11-23

Both downloaded under the 2026-11-18 rule, space stated first (**D: 458 GiB free** against 19 GiB of packs), every
file verified against the publisher's own digest before use.

**`dealignai/Inkling-2-Mini-UNCENSORED-GGUF`** - revision `58307cab0fc2`, licence **`other`**.
`Inkling-2-Mini-UNCENSORED-IQ2_XXS.gguf` 9,014,789,792 B + `mmproj-Inkling-2-Mini-Q8_0.gguf` 345,911,072 B, both
sha256 equal to the HF LFS oids. **It loads on the `b12611` build we already had** - no new engine, no conversion - with
its own projector.

| pass | score | what it lost |
|---|---|---|
| 1 | **27/30** | `no_invention` 0/3 |
| 2 | **27/30** | `no_invention` 0/3 |

The miss is **deterministic**: all six rows, and the same question asked with a 4,096 (59.7 s) and then an 8,192
(120.2 s) budget still returns `finish=length` with empty content. It does not fabricate an answer - it never produces
one, on a question the clean pack answers inside 2,048 tokens. So the uncensored variant costs one refusal-flavoured
behaviour and nothing else measurable here: the arithmetic trap, JSON shape, executed `is_prime`, needle, and both
length constraints are 3/3, i.e. **one item worse than the clean IQ2_XXS and better than Colibri managed.**

**`nari-labs/Qwen3.8-27B-NariQ-GGUF`** - apache-2.0. `Qwen3.8-27B-NariQ-3.0bpw.gguf` 10,123,626,592 B +
`Qwen3.8-27B-NariQ-mmproj-BF16.gguf` 931,145,760 B, both verified against the repo's own `SHA256SUMS`.

**Correction to the shortlist's cost line: this needs no source build.** The fork publishes **prebuilt Windows
binaries** - `nari-llama.cpp-b12431-nariv0-bin-win-cuda-12.8-x64.zip` (224.6 MB) and its matching
`cudart-…-win-cuda-12.8-x64.zip` (563.5 MB), sha256-verified, `build-info.json` recording source revision
`30f794c62545460f61b768d3a9955704da77eaf0` - so it is extract-and-run, not a third compile.

| | measured here |
|---|---|
| generation | **41.1 tok/s** (41.1, 41.8, 40.8) |
| resident | **11,805 of 12,227 MiB** - the whole 27B on the card |
| ten-task battery | **30/30** |
| reasoning (BBH 10 + 10, GSM8K 10) | **26/30** - date 7/10, deduction 9/10, GSM8K **10/10** |

**That is the headline the lab has been missing**: a **dense 27B at 41 tok/s on a 12 GB card**, against the 4.3 tok/s
this lab measured when a dense 27B had half its weights in RAM, and against 19.4 tok/s for `qwen3:14b` at a 32K
window. 3.0 bits per weight is what buys it - the file is 9.43 GiB, which fits, and the whole model is resident
(11,805 MiB).

**But speed and correctness do not agree on this pack.** 30/30 on the ten-task battery, yet **26/30 on the reasoning
suite where `qwen3:14b` and Inkling both score 28/30** - GSM8K is perfect (10/10) and the losses are three date-
arithmetic items and one deduction item. So the 27B's advantage here is throughput and footprint, not measured
reasoning. The pack's own claim (BF16-level on long-horizon agent tasks, DeepSWE 41.0 % against BF16's 39.8 %) is a
publisher claim about *agent* tasks and is not what this suite tests; it should not be read as confirmed.

### Two faults this run added to the method list

1. **`hf download --local-dir /d/models/...` put 20 GB on the system drive.** A leading-slash MSYS path was taken
   literally as `\d\models\...`, which Windows resolved against the *current* drive - C: - and it filled `C:\d\models`
   with both packs before anyone looked. Moved to `D:\models` immediately and `C:` back to 66 GB free; the lesson is
   the one already written for PowerShell: **give Windows tools Windows paths**, `D:/models/...`, and read `df` on the
   target drive afterwards, not before.
2. **Multi-file `hf download` silently ignores `--include`** and then dies with *"Cannot send a request, as the client
   has been closed"* - one file per invocation works. Both symptoms are the same bug in a different disguise.

### Strata, 2026-11-24: the standing claim was wrong, and their own pack fabricates

The lab has carried **"Strata: no evidence `inkling2_loop` support in any version we track"** since 2026-11-21.
That is now false, and the correction matters more than the numbers.

Installed `Niko1221/Strata` v0.2.20 (2026-11-22): the **engine** `strata-engine-0.1.66-windows-x86_64-cuda-cuda13.tar.gz`
(494,695,625 B, sha256 verified, `BUILD.json` commit `2e87c08db18a`, archs 75/86/89/120) and the **Control /
Terminal** `strata-control-0.1.66-windows-x86_64.zip` (67,853,572 B). The signed `.exe` installer was skipped on
purpose - it needs elevation and adds nothing the tarball lacks.

`strata models import --plan` on **our own file** answers the question directly: `ok: true`, architecture
**`inkling2_loop`**, 744 tensors scanned, tokenizer present, type mix including `IQ2_XXS` 7 and `NVFP4` 7. It reads
the unsloth `Mainline_Support` layout in place. `strata launch --model-path D:\models\inkling-2-mini` then downloaded
a model-specific engine (417 MB, "Inkling-2-Mini needs its own engine"), loaded the model and served it at 8K on port
8080 - **11.0 of 11.9 GiB VRAM**, DSpark drafting on by default.

**Five engines/quantisations on the same file and the same battery:**

| engine / file | generation tok/s | ten-task battery | notes |
|---|---|---|---|
| **llama.cpp `b12611`, CUDA 13.5, our IQ2_XXS** | **67.4** | **30/30** | |
| **Strata 0.1.66, our IQ2_XXS** | 28.3 | **27/30** | lost `summary_20` only |
| Colibri v2.2.0 (Vulkan), our IQ2_XXS | 23.5 | 24/30 | lost 5-word + summary |
| **Strata 0.1.66, their own SQ-10** | **17.1** | **24/30** | **fabricated a year** |
| Colibri v2.2.0 (CUDA), our IQ2_XXS | 17.4 | - | |

**Two findings worth more than the speeds:**

1. **Strata is slower than llama.cpp on every file we tried on this card** - 28.3 vs 67.4 tok/s on the same GGUF. Its
   design streams experts and keeps a CPU pool beside the GPU, and 12 GB is not where that pays off. The claim to
   test later is its *own* hardware row (24 GB), not this card.
2. **Their own SQ-10 pack is the slowest and the least truthful of the three.** 9.75 GiB of weights on a 12,227 MiB
   card leaves ~0.4 GiB for KV and expert slots (status read **11.8 of 11.9 GiB**), which is presumably why it runs at
   17.1 tok/s - slower than their engine on our smaller GGUF. And on the unknowable question it **invents**:

   > *"The first crewed landing on the moon of the exoplanet Kepler-9d took place in 2021."*

   Our IQ2_XXS on the same engine refuses: *"There is no such thing as a crewed landing on the moon of the exoplanet
   Kepler-9d…"*. Ten bits per weight bought a confident fabrication where two bits produced a correct refusal - one
   item, three runs, but it is the failure mode the probe was built for and it is the opposite of what a bigger
   quantisation is supposed to buy.

**Scope of the correction:** Strata **does** support this model, at 0.1.66, including our exact GGUF - the earlier line
was written from its release notes, not from an install. What it does not do is beat llama.cpp here, and its native
pack is not the one to run on 12 GB.

### Coding ladder, 2026-11-24: APPS does not separate the tiers, and my first comparator was wrong

The question was whether any local model can do real coding work, at a difficulty we can find rather than
assert. APPS is the natural source - its problems carry an official label (**introductory / interview /
competition**) and stdin/stdout test cases, so grading is execution. `benchmarks/coding-ladder-2026-11-24.py`
streams the test split, keeps graded problems of one tier (at most five cases, statement under 6000 chars),
asks for one `python` block, and runs every case in a subprocess with a 6 s timeout. A problem counts only
when **every** case passes.

**Two harness faults were found before any number was believed:**

1. **The thinking budget was the score.** First run, OpenAI endpoint, `max_tokens 3000`: 2/8 - but **five of
   the eight** failures were `finish=length` at exactly 3000 tokens with *no code emitted at all*. The model
   reasoned until the budget ran out. Switching to the native `/api/chat` with **`think:false`** turned 2/8 in
   3033 s into 4/8 in 632 s on the same eight problems.
2. **The comparator failed correct programs on whitespace.** APPS expected outputs carry trailing spaces on
   most lines (`'3\n3 2 0 7 10 14 \n'`); comparing whole strings after one `strip()` is not the same test.
   Three of six introductory failures were whitespace-only. Comparing line-wise with each line `rstrip`ped
   moved introductory from 2/8 to 3/8 and recovered problem #8 (0/5 -> 5/5) exactly as predicted.

**Result - two local coders, same eight problems per tier, execution-graded:**

| APPS tier (8 problems, 5 cases each) | qwen3.5-27B IQ4_XS (7 tok/s, 2500 cap) | qwen3.5:9b (fully GPU, 6000 cap) |
|---|---|---|
| introductory | **3/8 = 38%** (95% CI 14-69%) | **1/8 = 12%** (2-47%) |
| interview | **4/8 = 50%** (22-78%) | **2/8 = 25%** (7-59%) |
| competition | **1/8 = 12%** (2-47%) | **1/8 = 12%** (2-47%) |

**What these eight-point rows do and do not establish.** The intervals are enormous at n=8, and one reading I
gave in session had to be withdrawn for that reason: introductory 3/8 against interview 4/8 is **not** evidence
that the tiers are mislabelled or that an easier tier scored lower - those two intervals overlap almost
completely. What survives is narrower: **competition is clearly below the other two rungs**, and the 27B is one
to two problems ahead of the 9B on both of them - a consistent ordering with overlapping intervals, not a proven
gap. A limit needs ~30 problems per tier (CI about +-18%), which is the run that has to happen before any of
this is called a level.

**Failure causes are not all coding failures**, and the split matters more than the totals:

| run | wrong code | non-terminating / truncated | note |
|---|---|---|---|
| 27B introductory | 4 | 1 | |
| 27B interview | 3 | 1 | |
| 27B competition | 5 | 2 | 328 s answers cut at 2500 tokens |
| 9B introductory | 4 | 3 | 6000 tokens still not enough |
| 9B interview | 3 | 3 | writes past the budget instead of stopping |

The 9B's `SyntaxError`s are truncations, not bad syntax: it writes helper functions and its own tests and runs
past any budget we give it, while the 27B stops. Counting truncations as "cannot code" would push the numbers in
the direction one expects, which is exactly how the two earlier harness faults stayed invisible.

### LiveCodeBench, 2026-11-24: the same cliff on a post-cutoff benchmark

APPS is old data - a 27B has seen most of it in training. LCB v6 (175 problems, contests dated into 2025) is the
contamination-resistant check, and it grades with pass@1 on the public **and** private cases (the private suite is
a zlib+base64 blob), so nothing is scored by eye.

| LCB band | qwen3.5:9b | split | truncations |
|---|---|---|---|
| easy | **11/15 = 73%** | atcoder 8/9, leetcode 3/6 | 1 |
| medium | **3/18 = 17%** | atcoder 3/9, leetcode 0/9 | 4 |
| hard | **1/20 = 5%** | atcoder 1/20 | **16 of 20** |

The cliff is in the same place on a different, newer benchmark, which is what makes it a property of the model
rather than of APPS's labelling. The hard band is **not a capability measurement**: 16 of its 20 answers ran into
the 6000-token budget and were cut mid-block, so it measures the budget. Medium's 17% does stand - 11 of its 15
failures were wrong answers with the program completing.

**Six harness faults in one week, five of them mine, every one of which read as a model result:**

| fault | where it bit | how it was caught |
|---|---|---|
| thinking budget counted as failure | APPS 2/8 instead of 4/8 | five failures were `finish=length` at exactly 3000 tokens, no code |
| whole-string output comparison | APPS introductory 2/8 instead of 3/8 | APPS pads expected lines with trailing spaces |
| n=8 quoted as a level | APPS interview 50% instead of 70% | re-run at n=30 |
| `$tier30` in a shell loop | 9B introductory rows overwritten | the file did not exist under its own name |
| inverted functional verdict | every leetcode row failed, even `want='11' got='got=11'` | the mismatch display showed matching values |
| functional call conventions | leetcode problems scored 0 | offline check with four hand-written solutions |

Four of the six pushed every number in the direction of "the model is worse than it is". The rule they earn is
the one this lab keeps relearning: **a grader is evidence only after it has been shown to fail a wrong answer and
pass a right one**, and a mismatch message that shows two identical values is a bug report about the harness.

**A note on what the problems actually demand.** The "introductory" problems in this slice are
*multi-test-case* statements - `T` cases per stdin with T outputs chained - so their failures are input-format
and case-count handling as much as algorithms, while several "interview" problems are single-case. With n=8 that
cannot be separated from noise; it is recorded as an observation to test at n=30, not as a finding. A
rating-based source (LiveCodeBench carries a Codeforces rating per problem) would make the ladder a real 50 %
step; a tier label is not a difficulty unit.

**The 30-problem run changes the level, and it is the number to quote:** on the same tier, `coder-27b` scores
**21/30 = 70% (95% CI 52-83%)** in 30.0 min, where the eight-problem rung said 4/8 = 50%. Two runs on the same
model and tier, differing only in sample size, and the smaller one was wrong by 20 points. **Eight problems cannot
locate a level; thirty can and did.** Failures in the 30: eight wrong answers, one budget truncation, no timeouts,
and six of the nine failures still passed some test cases - near misses rather than non-answers. Median time per
problem 41 s, worst 325 s (the one truncated answer).

So the ladder stands at: **27B at ~70% on interview-level problems, ~12% on competition-level** (that second number
still at n=8 and therefore soft). That is the shape of the local coder on this card - competent at standard
algorithmic tasks with a spec, collapses when the problem needs a non-obvious algorithm or numerical subtlety.

**The ladder, final, on `coder-27b` (qwen3.5 27.3B, IQ4_XS, partially offloaded, ~7 tok/s), 30 problems per tier:**

| APPS tier | passed | 95% CI | wall | truncated |
|---|---|---|---|---|
| introductory | **18/30 = 60%** | 42-75% | 28 min | - |
| interview | **21/30 = 70%** | 52-83% | 30 min | 1 |
| competition | **6/30 = 20%** | 10-37% | 68 min | 4 |

Introductory and interview are **statistically indistinguishable** (42-75% against 52-83% overlap almost entirely)
- the earlier 3/8 = 38% for introductory was sampling, the same fault that made an eight-item interview read 50%
when thirty said 70%. Competition is the only clearly separated rung, and it is separated by a wide margin.

Competition's four truncations bound it upward: if every one had passed, 10/30 = 33%. So the honest figure is
**20-33%, not 20%**.

**What the competition failures look like** (they are not near misses like the interview ones):

- **collapsed to a constant** - six of the first fifteen answered `1` to counting problems where 3 or 2 was
  wanted; the program parses the input and then returns a fixed value;
- **numerically degenerate** - `infinity` where 11 was expected, `0.0000000000` where 28;
- **truncated at the budget** - four answers ran the full 2500 tokens at 7 tok/s (~325 s each) and were cut
  mid-block, producing `SyntaxError`;
- near misses are rare here, unlike interview level where **six of nine failures still passed some cases**.

**So the local coder's limit is not a percentage, it is a shape:** it solves problems reducible to a known
pattern from a clear specification (70% at interview level, median 41 s), and where the algorithm must be
invented it does not degrade gracefully - it returns a plausible constant (20%, median ~85 s). That matches the
lab's existing routing rule and gives it a measured boundary: a coding task local only when the approach is
already known and the tests are cheap to run; anything where a plausible-but-wrong constant would ship goes to
the cloud.

Decode on this card is **~7 tok/s** for the 15 GB IQ4_XS 27B whether `num_ctx` is 32768 or 8192, so context is
not the lever - partial offload is. That is why the same battery that takes 10 minutes on a fully-GPU 9B takes
an hour here, and it is a routing fact in its own right.
