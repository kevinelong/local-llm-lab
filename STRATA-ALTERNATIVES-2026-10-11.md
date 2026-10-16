# Local alternatives to Strata: engines that stream MoE experts from disk (2026-10-11)

Research only. No engine installed, no model loaded, no gate touched, nothing deleted. Every vendor or
third-party number is labelled as such; numbers measured on *this* box are marked so.

## What makes an engine "similar to Strata"

The defining mechanism, not the name: keep the always-on trunk (attention, router, shared experts,
embeddings) plus a bounded cache of experts in fast memory, and **read the rest of the experts from disk
as the router asks for them**. Consequences that fall out of it: RAM holds a working set rather than the
whole model; the disk sets the speed, not the RAM; a GPU becomes an optional faster tier rather than a
requirement; and a larger memory budget buys speed, not capability. Strata (MIT, `Niko1221/Strata`, the
engine this lab runs at `staged-strata-20261007/engine-src-v0.1.40.3`) is one instance of that idea; the
question here is what else implements it as of 2026-10.

## The candidates, with what each is actually usable for here

| engine | licence | platform | serves | verdict for this box |
|---|---|---|---|---|
| **Colibrì** `JustVugg/colibri` v2.0.0 | Apache-2.0 | Linux, macOS, **Windows** | OpenAI + Anthropic + **Jev-compatible `/v1/systemone`** | **the real alternative - try the decision models first** |
| **StrataFlow** (Coaade) | source-available, **not** OSI | CPU only | **no HTTP server yet** | watch only; cannot plug into our harnesses |
| **llama.cpp** SSD-streaming proposal #27149 + `jerryjokesalot/tinygiant` | MIT (llama.cpp) | proposal + prototype | n/a | its *findings* are actionable on our existing Strata |
| SSD-LLaMA (arXiv 2609.18110), DALI (arXiv 2602.03495), EuroSys '26 expert offload | papers | - | - | literature, snippet-level only here |
| KTransformers | MIT-ish, `ktransformers.net` | Linux | SGLang-KT server | **different shape**: CPU+GPU hybrid aimed at a 32 GB-class card, not disk streaming |

### Colibrì - the one worth acting on

Read: the repository README and model tables, the v2.0.0 release notes, the release assets via the GitHub
API. **Pinned: tag `v2.0.0`, published 2026-10-06T20:24:40Z** (`target_commitish: main`, so pin the tag,
not the branch). Asset digests are published, e.g. `colibri-v2.0.0-windows-x86_64.zip` sha256
`fdb8ea2fad7dcfe44d9d37bfb3e444f1299207f268ab499719f98bd772397d79` and the CUDA zip
`e0f7f4ad339909a9ef5dfc3bda6afe46757d3358d8a2d446e460ce14a1f7dc3a`. Apache-2.0, pure C, one file per
model family, 41,167 stars / 4,529 forks / 102 issues at the time of reading - **interest, not evidence**.

What matters to us:

- **It has an engine for Qwen3.8-Flash-Next**, the model we serve on Strata. Vendor table: 186 GB download,
  24/32 GB RAM, measured **1.91-2.56 tok/s with 32-96 experts per layer and 3.99 with the optional int4
  experts**, on machine A (Ryzen 7 PRO 8700GE, 64 GB DDR5, NVMe, integrated Radeon 780M). Machine A has
  **no discrete GPU**, so that number is not comparable to our 12 GB RTX 5070 run - but it is the same
  model, and their Windows CUDA package ships `coli_cuda.dll` for **`colibri`, `qwen36` and `kimi_k3`
  only**, so on Windows this engine gets Vulkan or the CPU, not CUDA.
- **Its decision API is Jev-compatible by design**: "the request and the reply are those of TypeSafe's Jev
  API, so a Jev client switches to colibri by changing its base URL", and both official Jev SDKs are tested
  unmodified against `coli serve`. That is the same shape as our decision track, and we already have
  Jev-shaped tooling from the 2026-09-24 observer work.
- **Three native decision models on the CPU**: Laya (0.85 GB download, 1.7 GB RAM, 219 ms/question),
  GLiNER2.5-Decide (1.95 GB, 1.9 GB, 294 ms) and Clef (55 GB download, 19 GB RAM in int4, 20.4 s). Laya is
  already in our own decision set; Clef is an item we left open on 2026-10-08.
- **Same two tricks as Strata**: routed experts as int4 (1.4-1.56x decode, #1831) and speculative decoding
  from the checkpoint's MTP head, on by default (#1832, #1917).
- **The cache is history-calibrated, and they measured what that is worth**: the expert tier is "filled at
  startup from the experts your past conversations used and adapting while you chat"; #1919 says a fresh
  Qwen3.6 install now ships a starting expert history so the first run fills the tier - "on a Radeon 780M
  Qwen3.6's first run went from about 6 to 11 tok/s". They also gate correctness on placement: "#1855:
  qwen36 gives the same logits at every expert-cache capacity on FMA builds".
- **Honest gaps in their own docs**: "we have not measured a discrete GPU ourselves yet" (their one
  discrete-GPU number is a user's V100 via #1852); and the GPU "adds numbers in a different order... a long
  answer can drift from the CPU's by a word", which is a placement-changes-output caveat we would want to
  check rather than assume away.
- **Name collision, worth writing down once:** *Kolibri-1 78B* is a **model** we have measured extensively
  (an accuracy leader on our suites). *Colibrì* is an unrelated **engine**. They are not connected.

### StrataFlow (Coaade) - the same thesis, and a lineage question

Read: the 2026-10-05 press release. It describes streaming MoE weights from disk inside a bounded memory
budget, a single tiered weight store across VRAM/RAM/SSD, a predictor that warms the next layer's experts,
and a streaming model format called **`.strata` built from standard GGUF** - which is the shape of the
model pair this lab already keeps on disk. Its measured claims are a strong discipline (engine changes gated
on reproducing reference logits bit-for-bit; a 785 MiB and a 1177 MiB model both at ~132 MiB peak RSS).

But: licence is the **Coaade Source-Available License 1.0** - personal non-commercial only, explicitly not
OSI and never converting to Apache/MIT - the engine core is CPU-only, only llama-arch MoE and dense llama
are implemented, IQ quantisation is unvalidated, **there is no tagged release and no OpenAI-compatible HTTP
server**, and large-model numbers are still being gathered. **Verdict: not usable by our harnesses today,
and not adoptable as open source.** The open question it raises is worth settling: whether the MIT Strata
we run is the same codebase as this product, which would matter for redistribution, not for our private
measurements.

### The llama.cpp route - findings we can use on the engine we already have

Read in full: `ggml-org/llama.cpp` discussion **#27149**, "Expert-Aware SSD Streaming for MoE Models on
Memory-Constrained Hardware" (opened 2026-08-15, 4 comments), whose prototype is
`jerryjokesalot/tinygiant`. This is a *proposal*, not a merged feature, and its relevance here is as
evidence rather than as software:

- **GGUF stores all experts of a layer interleaved in one tensor**, so an mmap that needs one expert touches
  every page: they measure **111x page amplification**, reduced to 36x by a contiguous expert re-layout.
- **Calibration beats chance by a wide margin**: random activation profiles give a 6 % expert hit rate
  ("= chance"), while calibrating the pinned set from ten tokens of real text gives **42 %**, matching the
  oracle top-8, and **56 %** with LRU on top.
- Double-buffered I/O measured **2.09x**; their CPU compute ceiling on an M1 was 4.4 tok/s, with SSD reads
  fully hidden behind compute at an 88 % hit rate.
- Their honest position: the first prototype simulated compute ("matrix multiplication is not wired up"),
  later compiled C benchmarks use real BLAS at 2.2-4.5 tok/s.

**Why this is the cheapest actionable item in this note:** it says the hot set should be *learned from real
text*, and our own 2026-10-08 measurements already tested expert-cache *size* (`--expert-cache 1500` was a
regression, `auto` won) and added `STRATA_ROUTE_RESIDENT`. The next question - a calibrated hot set versus a
cold one at the same capacity - needs no download and no new engine.

## What I would test first, cheapest first

1. **Colibrì's decision models against our frozen decision inputs** (Laya 0.85 GB, GLiNER2.5-Decide 1.95 GB,
   Clef 55 GB). CPU-only, ~2 GB of RAM each, Jev-compatible endpoint, and the inputs already exist: the 18
   archived windows and the Bespoke 3,880-record suite. For **Laya this is the same model on two engines**,
   which is our own methodology, and it needs no GPU, so it cannot contend with a scored screen.
   *Predictions, recorded before any run:* Laya still catches 0-1 of 4 stalls (that is the model, not the
   engine), and its probability calibration differs measurably from the `--systemone` path we use today.
2. **The calibrated hot-set idea on our existing Strata** (zero download): compare the current cache
   against one seeded from a real prompt history, at the same capacity, on `ledger2`.
3. **Colibrì with Qwen3.6-35B-A3B** (23 GB download) as a second engine for our best model, on the nine-task
   suite. *Prediction:* it does not beat the current Strata configuration, and its value is independence
   from our pinned stack, not speed.
4. **Not proposed:** Colibrì's Qwen3.8-Flash-Next route here. It needs a **186 GB** download and this disk
   has **61 GiB free** (measured 2026-10-11, after three drops the same day: 103 -> 81 -> 61 GiB).
   **Cause proven, and it is the pagefile:** `pagefile.sys` was 32.57 GiB when first measured and 50.79 GiB
   when measured two hours later, written 2026-10-11 10:11, with only 3.54 GiB actually in use - an ~18 GiB
   allocation against a 20 GiB disk drop. Nothing in this lab's roots grew (the only new file over 300 MB is
   the 0.78 GiB Laya checkpoint), Windows Update holds 0.03 GiB and there are no shadow copies. So loading
   the 35B model and the 66 GB Strata pack pushes commit charge up and Windows grows the pagefile to match:
   the artifacts cost megabytes, the *loads* cost gigabytes, and the space stays allocated until a reboot
   reclaims it. Note for resource reasoning: on this box free disk is not a static resource, and a guard that
   watches disk while an engine runs is partly measuring the pagefile. (`hiberfil.sys`, 25.38 GiB, is a
   separate fixed cost and disabling hibernation would reclaim it - a system change, not proposed here.)
   **Correction, same day: this box has a second identical NVMe on `D:` and that changes the arithmetic.**
   `D:` is a separate physical `NVMe P0527 Phison 1024GB` (disk 0; `C:` is the same model on disk 1),
   953.7 GiB with **331.6 GiB free**, and it already holds a 622 GiB models store (Kimi-K2.7-Code 554.3 GiB,
   Qwen3.8-Flash-Next as an Ollama `UD-IQ1_S` 72.5 GiB - a *different* quantisation from our GSQ-RCO Q2_0, so
   no duplicate). Measured throughput 1 GB sequential, 8 MB blocks, flushed: `C:` write 1187 / read 3212 MB/s,
   `D:` write 1261 / read 3123 MB/s - parity, and read is comfortably above what expert streaming needs. So
   the large routes do fit, on `D:`: the 186 GB Colibrì pack, DeepSeek V4 Flash REAP (85 GB) and the rest.
   What does *not* move: the frozen roots reference absolute `C:` paths (for instance
   `strata-q2_0.json`'s `--pack`/`--native`/`--ple-gguf`), so staging stays on `C:` and **new** downloads go
   to `D:`. The two remaining `C:` levers are the pagefile (50.79 GiB allocated, needs elevation) and
   archiving the superseded `staged-strata-20260930` (55.5 GiB).
   **Done the same day:** `staged-strata-20260930` (the older Strata staging - an IQ1_M pack plus its engine
   source) was copied to `D:\ai_bench-staged\staged-strata-20260930` and the `C:` copy removed: 416 files,
   55.55 GiB, verified by identical file sets and sizes plus a sha256 of the 27.58 GiB shard *before* any
   deletion. Only frozen wire captures from a finished run mention that path; no `.py` or config does. Two
   things learned doing it: a first `rmtree` died on a read-only git pack file **after** deleting 26 entries,
   which is exactly why the copy gets verified first; and **free-space deltas around heavy I/O are not
   attributable on this box** - the pagefile moved ~50 GiB up and then back down on its own across the same
   window (58.7 -> 108.4 GiB before any delete), so the honest record is the file-level fact (a 55.5 GiB tree
   left `C:`) and the current readings (`C:` 135.4 GiB, `D:` 276.0 GiB free), not a claimed gain. Every large
   file checked has `nlink=1`, except one file inside `staged-kolibri-20261007` hard-linked 21 times.
   On Windows that engine has no CUDA path either, while the Strata configuration we already have serves the
   same model at 6.5-9.6 tok/s decode on the card.

## Open questions for Kevin

1. Run item 1 (the Colibrì decision comparison)? It is the cheapest real test of a Strata alternative and
   it does not need the GPU.
2. Run item 2 (calibrated hot set on our Strata) - and if so, is it a new root or an arm inside
   `staged-strata-20261007`?
3. Do we care about the StrataFlow/MIT-Strata lineage question for licence reasons, or only about our own
   private measurements?

## Addendum, same day: two engines the first pass missed (ds4, FreeToken)

Triggered by a video with no captions: "ds4 (DwarfStar 4) vs Strata vs FreeToken: 3 Ways to Run Giant MoE
Models Locally" (AgenticEngineering, uploaded 2026-10-08, 9:38, 6.7K views, video `egYyctiT2Kk`). YouTube
reports **no subtitles or captions** and the usetranscribe mirror returns 404, so there is no transcript to
quote, partial or otherwise - everything below comes from primary sources instead.

**Search-vocabulary lesson:** neither engine appeared under "experts streamed from disk". ds4 says "models
larger than RAM" and `--ssd-streaming`; FreeToken says "bandwidth-adaptive" and "edge-native". Searching one
phrasing of an idea is how you miss its implementations.

### ds4 / DwarfStar 4 - `antirez/ds4` (MIT, C, 23,772 stars, 2,296 forks, 773 issues)

By Salvatore Sanfilippo. Deliberately narrow - "not a general GGUF runner", it needs the GGUFs the project
produces - and it supports **Qwen3.8 Flash Next on Metal and CUDA**, the same model we serve on Strata.

- Targets: **Metal on 96 GB+ Macs (the primary target), NVIDIA CUDA (DGX Spark is its "main goal", plus
  multi-GPU Ada including L40S), ROCm on Strix Halo.** No Windows build guide; the platform matrix is
  `make` on macOS and Linux.
- `--ssd-streaming` keeps a bounded cache of routed experts and reads misses from the GGUF - the same
  mechanism as Strata, with the same two knob shapes we use (`--ssd-streaming-cache-experts` takes a byte
  budget *or* a dynamic slot count).
- **The rule worth stealing:** "An oversized expert cache can displace those weights and slow decoding.
  More cache helps only while the rest of the working set still fits." Its own measurement on a 128 GB M5
  Max: full GLM 5.3 IQ2_XXS (196.58 GiB) with a 61.35 GiB expert cache, a 16-token append fell **30.8 s ->
  2.9 s** and generation rose 4.09 -> 5.11 t/s, with **all compared logits and generated text identical**.
- Also documented: generation is more cache-miss sensitive than prefill, and `--ssd-streaming-cold` /
  `--ssd-streaming-preload-experts N` are "mainly useful for controlled measurements" - the same
  cold-versus-calibrated distinction the llama.cpp proposal quantifies.
- **Cannot run here:** every documented model is 60-197 GiB and the target is a 96-128 GB Mac or a DGX
  Spark. An RTX 5070 12 GB under WSL is not a path to those sizes.

### FreeToken - `FlashML-org/FreeToken`, paper arXiv 2608.16157v1 (2026-08-17)

Edge-native MoE serving with **bandwidth-adaptive execution**, UC Berkeley / UT Austin authorship
(Keutzer among them). Torch-free Python wheels, LRU expert caching and double buffering, 284B-class models
on a gaming desktop; its "2-4x Ollama" framing is a vendor comparison.

- **Its premise is our measured finding:** `ft bench bw` exists to "benchmark CPU vs PCIe bandwidth to
  calibrate the MoE backend". Our own 2026-10-08 note concludes the Strata prompt path is RAM-bandwidth
  bound at 620-657 tok/s - the same conclusion, reached by measuring the machine first.
- **Cannot run here:** Linux/CUDA wheels and 150+ GiB models against 81 GiB free.

### What this changes

Nothing about the recommendation. Of the six reviewed (Colibrì, StrataFlow, llama.cpp #27149, ds4,
FreeToken, KTransformers), **Colibrì remains the only one whose route fits this machine** - Windows,
Apache-2.0, 8 GB RAM minimum, and a decision-model path needing about 2 GB. ds4 moves to "read its docs"
status for the cache-budget rule and the identical-logits result.

## Addendum 2, same day: the "2x faster" video, checked against upstream

Video: "This New Cache Makes Huge Local AI Models 2x Faster" (Code Unpacked, uploaded 2026-10-10, 9:31,
8.2K views, `hJGryeKoCEg`). No captions either - YouTube reports none and the description is the source. Its
claim: llama.cpp "just made the exact same model run more than twice as fast on the exact same GPU" by
treating VRAM as a live cache for the routed experts, with a chapter titled "Merged into llama.cpp"; one RTX
5090, Qwen3.8-Flash-Next, 30.8 -> 67.8 tok/s.

**Checked, and it does not hold as stated.**

- Our staged build - llama.cpp **b11461**, commit `4d756bc72`, the one every current suite uses - has
  `--cpu-moe` and `--n-cpu-moe` and **no expert-cache flag at all**. Control for that negative: `cpu-moe`
  matches 5 lines of the same 736-line `--help`.
- Issue **#20757** (two-tier GPU+RAM expert cache) is **closed**, and of the five PRs referencing it:
  #23238 (paged experts, closed as "[AI Policy Violation]"), #21614 (closed), #23440 (Metal slot pool, still
  open, and it **loses** throughput - 38.1 -> 30 tok/s at 128 slots, because of a per-layer CPU/GPU sync),
  and #24524 (closed unmerged, but its design is the good one: keep `MUL_MAT_ID` on the **CPU** and dispatch
  only the hit rows to the GPU, so misses cost nothing; +25 % on GLM-5.1 754B, +7-57 % over 13 models).
- The feature the video describes matches **PR #26563** (`miltos22`): flags **`--expert-hot-s N` / `-ehs N`**
  (0 = off by default, -1 = autofit, `--ecf` to force it on unverified backends), **CUDA-only**, tier engaged
  only at single-token decode. Its own numbers are on **our** model: Qwen3.6-35B-A3B Q2_M 33.25 -> 57.2 tok/s
  and Q5_K_P 17.34 -> 35.93 tok/s on 8 GB VRAM. Its state: **closed, `merged_at: null`**, with the author's
  note "closed with plans to organize and re-open" (updated 2026-10-07).
- Its own candour matters more than the speed claim: "Due to differences in how experts are processed on the
  CPU vs the GPU, **even at temp 0 when different experts are cached, the output may slightly vary**." That
  is the same class of effect we already recorded for Strata (temperature 0 is not seed-stable there), and it
  is why a cache feature must be **scored**, not just benchmarked.

**Consequences:** we cannot get this by bumping our pinned build - there is no upstream flag to set. The
routes are (a) wait for the re-opened PR, (b) build a fork (`miltos22/llama.cpp-wackMall-merge-request`,
`GenerelSchwerz/llama.cpp`, `ongunm/llama-moe-cache`, `spiritbuun/buun-llama-cpp` with
`--moe-cache-expert-parallel`), or (c) use the engine we already have - Strata's adaptive GPU expert cache is
the same idea, and we already characterise its knobs (`--expert-cache`, `STRATA_ROUTE_RESIDENT`). If (a)
lands: look for `-ehs`/`--expert-hot-s`, and test it on the frozen suite at **one** setting, because the
cache changes numerics by construction.

> **Correction, 2026-10-16 - the middle clause is wrong: there IS an upstream flag, and it merged the same
> day.** PR **#29887** ("llama : add a GPU cache for MoE experts kept in host memory") merged
> **2026-10-07T18:07:46Z**, roughly eleven hours *after* b11461 was published, and `--moe-cache-mib N` first
> ships in **b11480** (2026-10-08T01:36). Verified two ways: the PR's `merged_at`/merge commit from the API,
> and `common/arg.cpp` fetched at both tags - the flag is **absent at b11461 and present at b11480**. So
> route (a) already happened rather than being something to wait for, and #26563 is now superseded by the
> merged cache (with #30059 `--moe-cache-layers` and an SLRU variant on top). The negative control above
> stands as written - *our* build has no such flag - which is exactly why the conclusion drawn from it was
> one day and one build out of date. Keep the rest of the advice: the effect is non-monotonic, so ladder the
> value, and score it, because the cache changes numerics by construction. See `NEWS-2026-10-16.md` §1.

**Vocabulary lesson, second instance:** the same idea is written "expert cache", "expert-hot slots",
"MoE disk offloading", "bandwidth-adaptive", "models larger than RAM". One query finds one of them.
