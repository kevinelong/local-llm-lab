# Magnitude: trying the new engine, 2026-10-17

Kevin: "proceed now including magnitude which you can try first". This file records what it took to get
it running on this box, what it claims, and the measurement it was tried for. **A prediction is written
below before its result** - the lab's rule.

## What it claims

`magnitudedev/magnitude`, Apache-2.0, 7,056 stars, pushed 2026-10-17T18:41Z. *"Open source inference
engine that tunes its kernels on your hardware... over 2x faster than Ollama"*; its own benchmark table
says **1.32x prefill / 2.19x decode on Mac and 1.34x / 2.17x on NVIDIA, averaged over 11 popular local
models**. The mechanism is per-model kernel tuning on the actual chip (up to a minute at download), and
per-model speculative drafters ("DSpark", "DFlash", "MTP"). `status: vendor claim`.

## What it took to run it, and the four things that cost time

1. **The CLI tarball alone is not an installation.** `magnitude-cli-windows-x64-msvc.tar.gz` (41,531,641 B,
   sha256 `f823a737...994b9`, verified) extracts one binary, and `serve` refuses it: *"This command is not
   inside a complete Magnitude installation."* The condition is in the repo, not guessable from the docs:
   `packages/daemon-management/src/desktop-native/application-bootstrap.ts` requires the executing file to
   be named `magnitude.exe` **and** its parent directory to be named `resources` on Windows.
2. **On Windows, `serve` additionally requires process containment.** `headless-application.ts` calls
   `native.guardParent(0)` before anything else and fails with the `%LOCALAPPDATA%\Programs\Magnitude CLI`
   message if it does not hold - *"Only the Magnitude command launcher contains a Windows server's process
   tree."* A hand-assembled layout from the release assets passes check 1 and fails check 2, so the honest
   path is the installer (`RequestExecutionLevel user`, installs to `%LOCALAPPDATA%\Programs\Magnitude`, no
   UAC, and its `MagnitudeInstallGuard.dll` creates the `Magnitude CLI` launcher).
3. **The supported install is silent:** `magnitude-desktop-windows-x64-0.2.9.exe /S`
   (191,387,992 B, sha256 `d112a7bd...127a615`, verified) completed in 23 s and laid down
   `Programs\Magnitude` (Electron app, `resources\magnitude-launcher.exe`) plus
   `Programs\Magnitude CLI\magnitude.exe` (169 KB - the launcher). Model store: `~\.magnitude\models`.
   Uninstall is theirs (`Uninstall Magnitude.exe` in that directory).
4. **Discovery does not take a synthetic HF-cache entry.** The CLI docs say *"discovery scans existing
   local Hugging Face caches for usable GGUF models without downloading or contacting the Hub"*, so the
   first attempt was to expose **our own** Qwen3.6-35B-A3B Q4_K_M through
   `~\.cache\huggingface\hub\models--kevinlab--qwen36-35b-a3b-q4-k-m\snapshots\<rev>\...gguf` as a
   **hardlink** (zero extra bytes, `os.path.samefile` true). After two service restarts `models status`
   still said *"No local models are on this computer"*, so discovery does not accept an entry whose repo
   does not resolve - or it needs the `blobs/` + symlink layout. **Our model is therefore not testable on
   this engine without either its catalog or a Hub-shaped repo**, which is the same wall the catalog
   description implies: *"We write optimized kernels for the most popular open-weight families."*

## What its own assessment says about this box, before any token

`magnitude hardware` reads the box correctly - Intel Core Ultra 9 285, 24 logical cores, 63.5 GB, RTX 5070
11.9 GB, CUDA + Vulkan. Of **73** catalog models, **22** are compatible here, and every one is small
(Gemma 4 12B/E4B/E2B, LFM2.5 2.6-8B, MiniCPM5 1-2B, MiniCPM-V 4.7 1B, Qwen3.5 4B). **Nothing in the
35B-A3B class appears**, so the model this lab's whole ranking rests on cannot be served by the engine's
own catalog on this hardware.

## The experiment: one model we have already measured

The one catalog entry that overlaps our own record is **`minicpm5-2b:gguf:q4`** - MiniCPM5 2B, Q4,
DSpark, 4.9 GB resident, 2.21 GB download. This lab measured the same model at **122 tok/s** (and 188/174
tok/s decode at 1k/4.9k prompts in a separate rate probe).

**Prediction, recorded before the probe:** Magnitude's own assessment predicts **94-135 tok/s** for this
model on this hardware, so its measured rate will land **inside or near that band** - i.e. **the 2x claim
will not survive on this box for this model**, because the vendor's own predicted band brackets the number
our existing stack already produces. It would be refuted by a decode rate at or above **~244 tok/s**.

**Method:** `catalog pull` → `models load` → one `POST /inference/v1/chat/completions` with the same fixed
160-token prompt the `--moe-cache-mib` ladder used, temperature 0, tokens/second from the response's own
usage and our wall clock. Same prompt as the ladder keeps it comparable with llama.cpp's 47.2-73.6 tok/s
range for a 35B-A3B, with the caveat that the model is 2B and dense, so the honest cross-engine comparison
is against our own MiniCPM5-2B number.

## Result

### The Q4 measurement, and my prediction failed

`minicpm5-2b:gguf:q4` (2.21 GB download, 4.9 GB resident, DSpark), same fixed 160-token prompt,
temperature 0, on this box:

| run | wall | tokens | rate | engine's own timings |
|---|---|---|---|---|
| 1 | 0.53 s | 160 | **300.8 tok/s** | ttft 10 ms, prompt 34 tok in 90 ms |
| 2 (warm) | 0.42 s | 160 | **379.1 tok/s** | ttft 4 ms, prompt 34 tok in 23 ms |

**The prediction is refuted.** I wrote "it will land inside or near 94-135 tok/s, so the 2x claim will not
survive on this box" and said it would be refuted at or above ~244 tok/s. Measured 300.8 and 379.1 - above
the refutation threshold on the first run already. Two separate things are true and worth keeping apart:
the engine is fast here, **and its own assessment tool underestimates it by about 2.7x** (340 measured
against its 94-135 prediction), which matters for anyone using that tool to choose a model.

### The comparison that decides the claim, and its confound

The first cross-engine pair, same prompt, one workload at a time:

| engine | quant | wall | tokens | rate |
|---|---|---|---|---|
| Magnitude 0.2.9 | **Q4** | 0.53 / 0.42 s | 160 | **300.8 / 379.1** |
| llama.cpp b11461 (`-ngl 99`, 32k, greedy) | **Q8_0** | 0.91 / 0.86 s | 148 | **163.4 / 172.3** (engine: 174.9 / 176.9) |

That is ~1.8-2.2x - the vendor claim's shape - **but it compares Q4 against Q8_0, which flatters Magnitude**:
the smaller quantisation is faster in any engine. llama.cpp's own `predicted_per_second` (175-177) also
matches this lab's earlier MiniCPM5-2B figure of 188/174 tok/s, so the local side of the pair is
consistent with the record rather than a one-off.

Two smaller notes from the pair: llama.cpp stopped at 148 tokens (EOS) where Magnitude filled all 160, so
the generated text is not identical - the rate comparison stands, but this is not a determinism claim; and
llama.cpp's prefill on a warm prompt was 178.6 tok/s against Magnitude's 34-token prompt in 23 ms
(~1,480 tok/s), which is where a tuned kernel shows up.

**The quant-controlled pair settled it** - their Q8 against our Q8_0, same model, same prompt, one
workload at a time:

| engine | model | quant | wall | tokens | rate |
|---|---|---|---|---|---|
| Magnitude 0.2.9 | MiniCPM5-2B | **Q8** | 0.48 / 0.45 s | 144 | **297.5 / 317.9** (mean 307.7) |
| llama.cpp b11461 (`-ngl 99`, 32k, greedy) | MiniCPM5-2B | **Q8_0** | 0.91 / 0.86 s | 148 | **163.4 / 172.3** |

**Verdict: the vendor's claim survives, at about 1.8x.** 307.7 against 167.9 wall-clock is **1.83x**, and
against llama.cpp's own reported decode rate (175-177) it is **1.75x** - not the "over 2x" of the headline,
but the same shape, and measured rather than repeated. My prediction was refuted twice: I expected 94-135
and set ~244 as the refutation threshold, and the measurement cleared it on both quantisations. Two further
observations worth keeping:

- **Their assessment tool underestimates their own engine by about 3x** here (it predicted 81-110 for the
  Q8 against 298-318 measured). Anyone choosing a model with that tool is being told the wrong number.
- **Quantisation barely moves it**: their Q8 (307.7) is within ~10% of their Q4 (339.9), where llama.cpp's
  own Q8 sits at 168. Whatever their tuning does, it is not the usual "smaller quant, more speed" curve.

## Accuracy: the first number, and the landmine that had to be cleared first

Kevin: "how accurate was magnitude?" Speed and accuracy are different questions, and the accuracy one
needed two engine-behaviour fixes before it could be asked at all:

- **Magnitude ignores llama.cpp's nested `chat_template_kwargs`** and only honours a **top-level**
  `reasoning_effort`. As written, this instrument would have measured *thinking mode*: `content: null`,
  117 characters of `reasoning_content`, `finish_reason: length`.
- **Telling it both ways is a 400** - `reasoning_effort conflicts with reasoning controls in
  chat_template_kwargs`. Strict and correct on their side; a real landmine for an instrument shared between
  engines.

So `EngineResponder` gained `reasoning_knob = nested | top | none` (CLI `--reasoning-knob`), default
`nested` so every recorded run keeps its meaning. With `top`, MiniCPM5-2B Q8 through Magnitude:

| run | items | score | rate | wall | per item |
|---|---|---|---|---|---|
| Magnitude 0.2.9, MiniCPM5-2B **Q8**, `reasoning_effort: none` | 1,100 | **821 = 74.6 %** | 0.746 | **289.9 s** | **0.26 s** |

Per subject: grade-school math 269/300 (89.7 %), world history 77, astronomy 76, international law 75,
geography 69, prehistory 68, religions 70, philosophy 65, **virology 52** - the same virology floor the
35B and 78B models hit, so that is the item set, not this model.

The same 1,100 items are now running through llama.cpp b11461 on the **identical Q8_0 file** (nested knob,
as every recorded run used). The comparison that matters is not the two totals but the **per-item
agreement**: same weights, same items, greedy, so any discordance is engine numerics rather than model
knowledge.

## The two-engine comparison: equally accurate in total, differently wrong item by item

| | Magnitude 0.2.9 | llama.cpp b11461 | difference |
|---|---|---|---|
| overall | **821/1100 = 74.6 %** | **797/1100 = 72.5 %** | +24 checks (+2.2 pts) |
| MMLU (800) | 552 = 69.0 % | **571 = 71.4 %** | llama.cpp +19 |
| GSM8K (300) | **269 = 89.7 %** | 226 = 75.3 % | Magnitude +43 |
| wall | **289.9 s** | 2,859.7 s | **9.9x faster** |
| per item | **0.26 s** | 2.60 s | |

Per item on the same 1,100 items:

- **both right 687 (62.5 %)**, both wrong 169 (15.4 %);
- **Magnitude only 134** (80 MMLU, 54 GSM8K), **llama.cpp only 110** (99 MMLU, 11 GSM8K);
- **per-item agreement on correctness 77.8 %**, and **McNemar on the 244 discordant items gives
  chi-squared 2.17, p ~ 0.12** - the 2.2-point overall difference is *not* significant.

**So the honest one-liner is "equally accurate in total, differently wrong."** Two offerings of the same
model disagree on **22 % of items**, and the disagreement is not noise spread evenly: Magnitude is +43 on
grade-school arithmetic and -19 on recall, which cancels into a total inside 1.5 standard errors. That also
refutes the first explanation I reached for - I predicted the +43 was a token-budget artifact in llama.cpp
(the class that produced Swift's 7/70 and the reply-cap lesson), and checked it: **every arithmetic failure
in both runs parsed a real number (0 unparsed of 31 and 74)**, so these are genuine wrong answers, not
truncations.

**The caveat that keeps this honest:** these are two *independent Q8 conversions* of the model - Magnitude
pulls its own from its catalog, ours is `candidates-20260929-v1`'s - served through two different chat
templates. Magnitude will not ingest our file (discovery rejects it), so the 22 % discordance is a fact
about **the two offerings**, and attributing it to kernels rather than template or conversion is not
something this experiment can do. What it can say: an engine swap is not a like-for-like substitution, and
a single total hides a 22-point per-subject trade.

**For the record, MiniCPM5-2B's first knowledge numbers** on this instrument: 74.6 % (Magnitude) and 72.5 %
(llama.cpp), against Qwen3.6 88.5 %, Strata Q2_0 89.7 % and Kolibri-1 81.9 % - where a 2B model belongs.


## What this does and does not establish

- **Establishes:** on this box, for a model in its catalog, this engine is materially faster than llama.cpp
  b11461 on the same work - ~1.8x decode - which is the first engine in this lab's record to beat the
  reference stack on throughput at equal quantisation.
- **Does not establish anything about our workload.** Our reference configuration is Qwen3.6-35B-A3B
  (MoE, `--cpu-moe`, experts in RAM). It is **not in Magnitude's catalog** (22 compatible models, all
  Gemma-4-12B class or smaller), and **our GGUF is not discoverable** by it, so the 35B case - the one the
  whole ranking rests on, and the one where the bottleneck is expert streaming rather than kernels - is
  untested and currently untestable. A 2B dense model on a warm GPU is the best case for kernel tuning and
  the least relevant case for this lab.
- **Cost of finding out:** 390 MB of release assets (three tarballs + the installer, all sha256-verified
  against the release), a ~1 GB user-scope install under `%LOCALAPPDATA%\Programs\Magnitude`, and 2.1 GB
  of downloaded models in `~\.magnitude\models`. Uninstall is theirs (`Uninstall Magnitude.exe`).
- **Next step if it matters:** the claim is worth re-testing on a model we rank - their catalog's largest
  quantised entries (Gemma 4 12B) would say whether the gain survives a model that does not fit trivially
  in 12 GB, and a knowledge/`ledger` run on one of them would say whether speed came with any cost in
  answers. That is a download decision, not a step.


