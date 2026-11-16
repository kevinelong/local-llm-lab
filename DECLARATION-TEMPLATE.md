# The declaration template

**Created 2026-11-09.** One canonical list of the fields a measured row must carry, and the rules that make an
arm void. Until today this list existed only as prose inside the daily scans, where it grew from **five fields**
on 2026-10-23 to **eighteen** by 2026-11-08, and three different scans asked for "an edit to the declaration
template" without one file to edit. This is that file. A row that is missing a field here is not comparable to a
row that has it, and the scan rule stands: **the undeclared variable is worth up to a fifth of the number**
(`RESIDENT-ABOVE-8-2026-11-01.md`: `resident=` changes prefill by 20.5 %).

**How to use it.** Copy section 11 into the protocol before the load, fill every field from the readback named
beside it, record the filled block with the arm's result JSON, and check section 9 before starting and after
finishing. Where a readback does not exist on our engine line, the field is written `unreported` and that fact is
part of the row - never blank, never guessed.

**Provenance convention.** Each field names the scan or measurement that created it, because a field without an
incident behind it gets dropped. `[INFERENCE]` marks a claim this lab has not measured.

---

## 1. Who produced the row

| Field | Why it exists | Readback |
|---|---|---|
| `engine_version` | Every row. `0.1.47` is our staged line; 0.1.55+ changed the chunk default and the file tier. | `strata.exe --version` -> `strata 0.1.47` (**prints no build id**) |
| `engine_build_id` | 0.1.47 prints no commit, so the feed's own id is the only quotable identifier (2026-11-05). | release feed `strata-feed.json` -> `build id` per asset |
| `engine_binary_sha256` | A locally compiled engine is not a qualified build (2026-11-01, `#4879`: a source build scored 0/10 on a tool-call probe where the prebuilt scored 10/10). | `sha256sum strata.exe`; our 0.1.47 staged copy is 203,623,936 B |
| `engine_arch_list` | The Windows CUDA 13 asset names `sm_75/86/89/120/compute_120`; the CUDA 12 asset stops at `compute_89`. Ours is sm_120, so only the CUDA 13 asset is ours. | feed asset metadata |
| `toolchain` | 2026-11-01: a build's `--list-devices` must name the backend you think you are measuring; local nvcc minor changes behaviour. | `--list-devices`, `nvcc --version` |
| `llama_cpp_version` | llama.cpp rows only. **The build gate is `>= b12383`, published 2026-11-14T14:43:25Z** (set 2026-11-15) - the first tag containing `#31775`: `compare/c56be864f...b12383` reads **behind 0**, no `b12382` exists, and `b12390`/`b12400`/`b12406`/`b12413` were re-read behind 0. **This supersedes the 2026-11-13 gate `v1.0.0` = `b1b770d`**: that release is still the only versioned one and still carries FP8 KV caches and the MoE expert cache, but its tree *is* nightly **`b12359`** (`compare/b12359...v1.0.0` identical, 11-13), which contains `#31533` and does **not** contain `#31775` - so it sits below the gate. Newest rolling tag `b12413` (2026-11-15T12:38:58Z), 38 assets; `master` is `de32b268c`, **ahead 35** of `b12381`. **Consequence, and the line to quote: an arm that adds `-nkvo` to `--moe-cache-mib` is legal from `b12383` and VOID below it** (§12) - below it the load aborts at `src/llama-moe-cache.cpp:560` and measures nothing. **`#32245`**, filed within a day of the release: *"significant prefill performance drop on V100 (sm_70) in v1.0.0"* - not our sm_120, and the reason a versioned release is a **name** for a gauntlet, not a qualification for a row. | `--version` -> build id, read against §12 (`gh api repos/ggml-org/llama.cpp/compare/c56be864f...<tag>` -> `behind 0`); release feed; `git rev-parse v1.0.0` names the release only |

## 2. Pack identity

| Field | Why it exists | Readback |
|---|---|---|
| `pack_repo` | Two packs share a name shape and a quant name (`UD-IQ4_XS-v31` is Strata's own pinned 09-30 copy, not the Hub's current layout, 2026-11-05). | `staged.json` -> `repo` |
| `pack_revision` | **The reference pack was re-converted twice after we staged it** (`7878dc9a90 -> eb0b3cc97f`, 2026-11-08) with Q4_K_M **+118 MiB**: a fresh download is different bytes under the same name. | `staged.json` -> `revision` |
| `pack_src_sha` | `.src_sha` moved `995ad96e -> 345d467b` in the same window, i.e. the **source model** moved, not only the GGUF. | Hub file `.src_sha` -> `PRIMARY=...`; `unreported` for packs that ship none |
| `pack_file_digest` | A size check cannot see a re-conversion; only the digest can. Per file: `name`, `bytes`, `sha256`. | `staged.json` -> `items[]`; re-verify with `sha256sum` before any row that claims identity |
| `pack_tensor_types` | The expert **down projection** type decides whether Strata's native kernels accept the pack (`#3699`: Q4_K downs are refused; our Qwen3.6 Q4_K_M has all 40 at Q4_K). | one GGUF header read |
| `sidecars` | mmproj / MTP / DFlash each add bytes and can be the failure: `-md` + `--mmproj` aborts every build after `#30257` (2026-11-02). | `staged.json` `items[]` for the sidecars |
| `pack_calibration_text` | **New 2026-11-15, and the reason is a number we can no longer ignore.** `2611.11079` (task-informed calibration, FragCal-DC, 2-4 bit, six dense models 1.7-8B, ten tasks, four seeds): **at two bits, task-informed calibration is worth +1.83 pp mean ten-task accuracy** over generic-text calibration; single-pass GPTQ and AWQ show only small responses at 3 bits, and at 70B both improve at 2 bits. The two controls are the load-bearing part: recovery concentrates on families included in calibration, and **deliberately incorrect answer designations retain about 90 % of the gain** (so it is real and partly circular), while **changes in reconstruction error do not consistently track accuracy gains**. That last pair is what makes this a *pack* field rather than a footnote: a size or a quant name cannot stand in for it. **Our own null is the case in point** - the 1,100-item comparison read **974/1,100 = 88.5 %** (Qwen3.6 Q4_K_M, llama.cpp) against **987/1,100 = 89.7 %** (Qwen3.8-Flash-Next Q2_0, Strata) at a **1.33 pt paired SE**, and **neither publisher declares its calibration text**, so an effect larger than both the 1.2-pt gap and the error bar sits undeclared under the tie. | the pack's own metadata (`quantize`/`imatrix` dataset field, or the card's sentence naming the calibration set); **`UNVERIFIED`** when the publisher states none - which is the record for both packs above |

**2026-11-14: the reference pack moved again, twice, and the copy on disk is now three conversions old.**
`ggml-org/Qwen3.6-35B-A3B-GGUF` -> **`52f9f9b805`** (lastModified 2026-11-12T11:11:39Z, 14 files);
`ggml-org/Qwen3.8-Flash-Next-GGUF` -> **`a3e717e662`** (11-12T11:11:49Z, 17 files);
`unsloth/Qwen3.8-Flash-Next-GGUF` -> **`f5d175de2c`** (11-13T10:49:42Z, 77 files). The staged
`baec3ebee244827cda0f4557eafa8b28f7545fa6` therefore describes bytes a fresh download no longer has, and the
11-08 measurement of what one re-conversion can do - **33 of 48 down layers moved to Q5_0, -56 % prompt throughput
at 2.5K** - is the reason `pack_file_digest` is per file. A re-stage names the new sha **and** the expert histogram.

Recorded, both re-verified on disk 2026-11-09 (sizes match `staged.json` byte for byte):

| Pack | Repo @ revision | Files |
|---|---|---|
| Reference (llama.cpp) | `ggml-org/Qwen3.6-35B-A3B-GGUF` @ `baec3ebee244827cda0f4557eafa8b28f7545fa6` | Q4_K_M 20,419,565,568 B `671e47e0…`; dflash Q8_0 421,060,800 `339030c9…`; mtp Q4_0 1,060,038,432 `606fca33…` |
| Strata (q2_0) | `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF` @ `ed59f92082b1e93c0e96d60a8b11aab089b52f09` | Q2_0 shard 1 37,623,740,192 `69820c02…`; shard 2 28,800,138,432 `316b46f3…`; mmproj BF16 907,543,008 `b1a82259…` |

## 3. Memory contract

The reserve, the resident budget and the cache are **requests**, not conditions: the engine clamps or grants a
different number and still reports itself healthy. Every one of these needs the declared value *and* the granted
value.

| Field | Why it exists | Readback (0.1.47 log text) |
|---|---|---|
| `pagefile_mib` / `commit_limit` / `free_commit_at_start` / `free_commit_after_load` | Commit, not RAM, is the binding gate: 25.7 -> 0.84 GiB free commit under one resident arm while free physical read 15 GiB (2026-10-22). Strata `#4605` hit 93 MB of commit left. | CIM `Win32_OperatingSystem` `TotalVirtualMemorySize`/`FreeVirtualMemory` |
| `resident_declared_gib` / `resident_granted_gib` | `--resident-budget-gib 16` measured as **5.29-10.18 GiB granted**, and granted - not declared - is what moves prefill (+21.4 tok/s per GiB, 2026-10-27). | `FileExpertSource: --resident-budget-gib %.2f exceeds available %s (%.2f GiB minus %.0f GiB headroom and a 0.25 GiB margin): %.2f GiB` |
| `expert_cache_declared` / `cache_granted_slots` | Rule 3 of the gate: a declared `--expert-cache N` is not a cap (`#3693` overshoots to 5,118 slots, `#3692` under-fills). | `strata generate: expert cache %lld slots, %.2f GiB of VRAM; policy is …` and `expert cache auto: %.2f GiB free, %d MiB reserved (+%lld MiB for the draft head) -> %d slots` |
| `vram_reserve_mib` | A reserve is a ~1:1 tax on the cache (900 MiB bought 3,000 slots against 2,000 MiB's 2,168) and a **contract against WDDM paging** the engine never re-checks (`#4516`). | **not in `--help` on 0.1.47** (see §8); read from the argv echo and `strata serve: VRAM %lld MiB kept free: …` |
| `file_tier_line` | 0.2.12 stopped counting the engine's own memory as free and stopped switching 12 GB cards onto the file cache (3/3 starts on 0.2.11, 0/3 on 0.2.12). Rows on either side of that are different configurations. | 0.1.47: `strata generate: the file tier reads through the file cache (STRATA_UNBUFFERED_LOAD=%s ignored: …)` |
| `expert_read_mode` | **New 2026-11-15.** *File mapping* or *unbuffered*, declared, because two Windows measurements now point opposite ways and the variable they disagree over is free RAM against the working set. llama.cpp `#3059` (2026-10-18) **gained +26.3 %** decode by keeping the unbuffered initial load and then **reopening the shards so later expert reads are served by the Windows file cache** - a 64 GB-RAM box with a 16 GB card. Maya `#995` (11-15T12:42:16Z) is the other direction: misses read through the GGUF mapping stayed in the working set, the host thread sat in `GgufExpertSource::assemble`'s memcpy, so it reads misses **unbuffered** (`FILE_FLAG_NO_BUFFERING`, as its Linux `O_DIRECT` path already did), uses that for `copy_blob()` on the prompt path, and **releases the mapped pages after the RAM-tier copy** (`VirtualUnlock`, mirroring `posix_fadvise(DONTNEED)`; `MAYA_EXPERT_DIRECT=0` keeps the mapping). Result on that report's own box - RTX 3090 24 GB, 32 GB RAM, Q5_K_M **112 GB**, 65,536 context - a **27,908-token prompt stalled every time and now answers in 185 s**, follow-up turn 7 s, default answers unchanged; not tested on Linux, AMD or `--bench`. **This box is the boundary case: 63.46 GiB RAM against a ~66 GB pack**, so the two results stop contradicting each other once the mode and the free RAM above the working set are both written down. | the tier line above (`... reads through the file cache` vs unbuffered); the declared env value; free physical at start against the pack's on-disk bytes |
| `engine_memory_report` | `#5570` decomposes a 16 GB card and finds a **2.03 GB `scratch`** region the layered line omits - 12 % of the budget, invisible to both `nvidia-smi` and the gate. Three engines now disagree with the OS by 4-8x, 100 % and 12 %. | **`unreported` on our line**: the 0.1.47 binary has no user-facing memory report and no `scratch` line (§8). Record `nvidia-smi` in-use, the `Shared Usage` counter delta and the engine's own sizing lines instead |
| `free_vram_per_request` | 0.1.46 drove a card to 0 MiB free and spiralled verify windows 61/49/28/13/0 MiB (`#3952`); `#4474` shows auto-sizing and grant disagreeing in one process. | `strata serve: VRAM %lld MiB kept free: … %lld MiB free now, prompt chunk %lld` |
| `commit_at_ready` | **New 2026-11-15: admission is not residency.** A row that passes the 8 GiB commit floor can still
leave ~5 GiB once the engine is resident: five starts of a 20.4 GB pack with `--cpu-moe` admitted at **25.5-27.2 GiB
free** and fell to **4.43-5.80 GiB at ready**, with VRAM from 10,368 free to **6,701**. A gate read only before a load
cannot see this, and a second start straight after would be admitted into the remains of the first. Read commit **at
ready** and **at ready + 60 s**, and declare both. | `Get-CimInstance Win32_OperatingSystem` -> `FreeVirtualMemory`
before load, at ready and 60 s later |
| `wddm_shared_usage` | Under WDDM every page-locked GPU-mapped buffer is charged to a ~half-of-RAM segment that commit cannot see; 17.8 GiB measured on this box (2026-10-22), and registration succeeding is not residency acquired (2026-11-04). | perf counter `GPU Adapter Memory\Shared Usage` before and under load |
| `cast_buffer_pin` (ComfyUI arms) | **New 2026-11-15 - a covariate *and* a symptom.** `#17122` and its fix `#17123`: since `#14372`, `reset_cast_buffers()` runs only when `aimdo_enabled` is true (its only remaining call site is inside `if comfy.memory_management.aimdo_enabled:` in `execution.py`), so without aimdo **`LARGEST_CASTED_WEIGHT` holds the largest lowvram-cast weight until the end of the prompt** - and because safetensors are mmap'd, that one small weight keeps **the whole file mapping** resident. Measured, not theorised: LTX-2.5 on an RX 9070 XT / ROCm 7.2 / 32 GB RAM with a **15.4 GB int8** Gemma 4 text encoder loaded partially - **one 15 MB `Linear` stayed referenced and pinned ~13 GB of the encoder's mapping** (`/proc/<pid>/smaps`) while `current_loaded_models` was **empty**; the DiT then loaded at **~200 MB free** and stalled in `copy_` -> `memcpy_and_sync` with `page allocation failure` in `svm_range_restore_work [amdgpu]`, at **3 % GPU for 10+ minutes**. The fix runs `reset_cast_buffers()` after each node on the non-aimdo path too, and **its acceptance is pixel-identical output** - "Qwen-Image-2.1 t2i and edit: pixel-identical output" - beside LTX-2.5 going from stalled to **100 s** and LTX-2.3 112 -> 90 s on v0.41.3 / ROCm 7.2 / torch 2.14. **State the precondition: this report's is `aimdo_enabled=False` (ROCm), and our image arms run the aimdo-enabled path**, so it is not our failure mode by name. What transfers is the **symptom pair** - a stall at a few hundred MB free with near-zero GPU utilisation, and a pin whose size is the *file's mapping*, not the tensor's - and the reminder that three ComfyUI memory defects in one month each had a different mechanism and each passed our floor. | `aimdo_enabled` from the server log/argv; at the stall: free VRAM/commit, GPU utilisation, whether `current_loaded_models` is empty; Linux: largest `smaps` mapping against the largest cast weight - on Windows, process private bytes at ready against the file's on-disk size |

## 4. Prompt path

| Field | Why it exists | Readback |
|---|---|---|
| `prompt_tokens` | The chunk optimum is a function of prompt length; `--prefill auto` cannot exceed 8192 by construction (`#4683`) and a rung that does not name its prompt length is unreadable (2026-10-30). | the request's own token count |
| `prefill_declared` / `chunk_granted` / `clamp_line` | Rule 1 of the gate. The chunk bends to fit the cache: `WARNING: prompt chunk 5376, not 8192: CUDA1 has 1128 expert-cache slots` (`#4261`). | `strata generate: prompt chunk auto: %lld tokens`; clamp line as quoted |
| `prefill_borrow` | The loan our 10-27 and 10-31 ladders measured from the outside is a **switch**: `--no-prefill-borrow` is a literal in the 0.1.47 binary (2026-11-09). | argv; `--help` does not list it |
| `prefill_cpu_share` | **New 2026-11-09.** The 0.1.47 binary states that the CPU share is **ON by default for prompt chunks below 1024 tokens** and that *"answers can differ slightly from 0.1.40.3, mean KL ~0.004"*; `STRATA_PREFILL_CPU_SHARE=0` turns it off. Any arm whose chunk clamps to 512 is a different-text arm. | binary string `prefill: the CPU share is ON by default for prompt chunks below 1024 tokens …`; value from the environment |
| `lend_region` | Rule 2 of the gate. `0 of 790` in RAM at every rung 2-16 GiB because the ranked set eats the whole budget; 1.02 GiB of lend needs ~31.7 GiB resident (`RESIDENT-ABOVE-8-2026-11-01.md`). | `strata generate: WARNING: a prompt chunk of %lld tokens lends %lld cache slots to the prompt path, but only %lld of their experts fit in RAM … (#669)` |
| `prefill_ring` / `prefill_ring_auto` | **New 2026-11-15.** Our prefill arms have never recorded the ring size, and Strata `#6020` (11-15T11:15:04Z, *"Optional benchmark-based autotuning for prefill ring size"*) measures what that omission is worth: **`--prefill auto` chose a 96-slot ring, and `STRATA_PREFILL_RING=512` gave +23.1 % at 4K and +24.2 % at 16K** - medians **763.0 -> 939.5** and **974.9 -> 1210.9**, plus one 64K pair **992.0 -> 1219.1 (+22.9 %)**; decode 41.9 -> 43.6 with **no decode claim**. The method is the part to copy: **three interleaved A/B rounds, a fresh engine per arm, one variable**, Windows 11 26H2 build 26300.9974, RX 7800 XT HIP gfx1101, engine 0.1.59 `712fec6b4297`, UD-Q2_K_XL at 262,144 with `--kv int8`. **It is not our backend** (HIP on Windows AMD, not our CUDA card), so the number is a **predict-and-check**, not a result here - and 23 % prefill is larger than most effects this lab has chased, which is why the field costs one line now rather than after the bump. **The arm that sets it rides the gated engine bump** (0.1.59); until then both halves are `unreported` on 0.1.47, and the check before the first arm is `strings -a strata.exe` for a `STRATA_PREFILL_RING` literal - the same check that settled `--prefill-borrow` and `STRATA_KVA` (§8), not yet run for this string. | the log line giving the ring chosen under `--prefill auto` (96 in that report) and the environment's `STRATA_PREFILL_RING`; `unreported` on 0.1.47 until the strings check is run |
| `ubatch` / `batch` | llama.cpp rows: `#31504` makes a different `-ub` a different answer; the `-b 512 -ub 512` load fix was a ubatch change. | llama.cpp launch echo |
| `batch_slots` | `--batch N / --slots N` is opt-in and takes VRAM like a second session; our serving is one slot. | `--batch N / --slots N` in argv, `docs/BATCHING.md` |
| `prompt_cache_reused` / `checkpoints` | `--prompt-cache-every` is a no-op below the chunk size, and the deepest checkpoint carries the previous turn's tail, so reuse can silently be 0 (`#4206`, 2026-10-26). | per-request `reused = N`, `N checkpoints` |
| `first_request_ttft_before_warmup` | The first request after a load reports ~99 tok/s prefill and the second 50-60 because the second hits the prompt cache: **a warmed prefill row measures cache reuse** (2026-10-20, reproduced three times). | first probe, before any warm-up |

## 5. Speculation

| Field | Why it exists | Readback |
|---|---|---|
| `drafter` | Auto picks MTP on the all-cards split, DFlash2 is Auto for `UD-IQ4_XS-v31` only, and `mtp_ready()` silently strips `--mtp` when its probe fails (`#5395`, `#5388`: 43.4 vs 64.1 tok/s). | `Drafting: <mode>` line; a stripped flag must be caught in argv |
| `spec_n` / `draft_conf_in_force` | Auto picks 0.35 where the logged slot count prescribes 0.5 (66.7 -> 71.1 tok/s, 58.4 -> 67.0 % acceptance, `#5213`). **Declare the value in force, never "auto".** | `--spec N`; conf from the log or the launch file |
| `suffix_draft` / `lookup_chain` | Prompt lookup drafts grow the window by 2 and change what is compared. | argv |
| `drafts_accepted` / `offered` | **Every speculative row carries the pair.** Healthy turns sit at 65-85 %; a run stuck at 98.9-99.3 % for minutes preceded a collapse (`#4402`). Warn above ~98 %. | `%-24s %lld windows, drafts accepted %lld of %lld` |
| `mtp_dir_quant_bytes` | The drafter's own quant moves acceptance; the head is 1.06 GB at Q4_0 against 3.74 GB at BF16 on our reference pack. | `staged.json` sidecar entry |
| `verify_window_mib` | A 12-token verify window (110.2 MiB of device buffers) faults deterministically where 0.1.54's 5-token window (69.7 MiB) works (`#5449`). | VRAM readback at load |
| `spec_kernel` | **New 2026-11-15.** The verify step has a name, and it is what prices speculative decoding: `#31533` *"CUDA: few-row MMQ for BS 2-24"*, merged **2026-11-12T13:12:46Z**, commit **`0fb8f1577`**, **in `>= b12359` and not in `b12208`** (`b12208` -> behind 134; `b12359` and `b12383` -> behind 0). Steps of 2-24 tokens read each weight once; a one-token step takes a different kernel this PR did not touch, which is why the effect appears only with a drafter and shows nothing at one request. A speculative row therefore names its build **and** whether that build carries the kernel. | `--version` build id + `gh api repos/ggml-org/llama.cpp/compare/0fb8f1577...<tag>` -> `behind 0` / `behind N` |

**2026-11-15: our 2026-10-08 MTP row is re-priced as a pre-`#31533` row. It is not retracted - it is dated.**
The row read **+31.2 % per token, -7.3 % wall, +21.7 % tokens, accuracy unchanged** (letters only, which §6 already
bars from being quoted as determinism) on **b11461**, and b11461 predates the kernel: `#31533` merged
**2026-11-12T13:12:46Z**, and `b12208` is **behind it by 134 commits**. The published benchmark that prices the
kernel is properly interleaved - two builds taking turns, GPU cooled to 50 °C before every run, each figure the
median of five, RTX 3090 24 GB, temperature 0, one slot - and reads **27B with MTP: 45.1 -> 68.5 (+52 %) at the short
prompt and 46.5 -> 71.9 (+55 %) at the long one on `v1.0.0`, against +11 % / +17 % on pre-v1 (build 12199)**, with
**draft acceptance unchanged at 32-33 %** (9B: 96.5 -> 122.3, acceptance 27-28 %). Acceptance flat while wall clock
halves means the gain is the **verify step getting cheaper**, not the drafter guessing better - the opposite of where
our row looked for its value. So the honest re-pricing is: on a build **>= b12359**, an acceptance of ~33 % is
predicted to **pay** wall clock instead of costing it. That is a prediction about this box and it is not a result;
**the test is two starts on one build >= `b12383`** (also the first tag with `#31775`, §12), one model,
`--spec-type draft-mtp` off and on, the same prompt, reporting **accepted/offered** and wall clock. Two facts from
the same page bound what any row may claim: **one request at a time is unchanged** (within 2 %, and the runs of one
build spread wider than that), and the **14-22 % no-MTP gain needs four concurrent requests** - our arms are
`--parallel 1`, so that gain is out of reach and is a reason *not* to chase the version for a throughput ladder. MTP
cost **+1,490 MiB** on the 27B, and a **separate 0.8B drafter made that model slower** (30.7 against ~40 tok/s) at
under half its guesses accepted.

**MEASURED 2026-11-15, and the row inverts.** Five starts on `b12383` (`1.0.0-dev`, build 12383, commit
`c56be864f`), our own pack, **446-token prompt**, greedy, `n_predict 256`, one slot, `-ngl 99 --cpu-moe
--load-mode none -t 8 -c 8192 -b 512 -ub 512`:

| arm | wall s | gen tok/s | prefill ms | accepted / offered | graphs reused |
|---|---|---|---|---|---|
| MTP **off** (2 starts) | 5.9805 / 5.9955 | 46.78 / 46.66 | 527 | — | 254 |
| `draft-mtp` (3 starts) | 5.4269 / 5.3732 / **5.3534** | 53.72 / 53.36 / **54.68** | 643 | **161 / 279 = 57.71 %** | 90 |

**-10.08 % end-to-end wall, +11.21 % throughput, -13.35 % generation time, +15.42 % generation tok/s.** Within-arm
spread **0.25 %** (off) and **1.37 %** (on); the ranges do not overlap - the slowest `draft-mtp` start is still
**0.554 s** faster than the fastest MTP-off start - and the third start was the fastest of the three, so it is not a
warm-cache artefact. So the 2026-10-08 row (**+31.2 % per token, -7.3 % wall**, `b11461`) was **a property of that
build**, and the wall tax we quoted for five weeks is not a property of MTP on this card.

Three things this row also found, none of them in any earlier note:
- **The drafter costs prefill time: +21.9 %** (527 -> 643 ms on 446 tokens), which is why the end-to-end gain
  (-10.1 %) is smaller than the generation-phase gain (-13.4 %). A short prompt hides it; a long one would not.
- **The drafter costs ~1,043 MiB of VRAM** (4,201 -> 5,243 MiB at ready, 5,455 after) and ~1.1 GiB of commit.
- **Batching is visible**: `graphs reused` 254 -> **90**, i.e. 91 steps for 256 tokens = **2.81 tokens per step** -
  the first direct instrument we have had for "the verify step got cheaper", which is what `#31533` is.

**What this row may not claim.** Not an attribution to `#31533`: the commit is **contained** (`compare/0fb8f1577...b12383`
-> `ahead_by 41, behind_by 0`), but **no pre-`#31533` arm ran today with this prompt**, and the `b11461` row differs in
build, prompt, sampler and harness, so nothing is subtractable. Not the published **+52 % / +55 %** (27B on a 3090 at
32-33 % acceptance) - here acceptance is **57.71 %** with the family's own MTP head. Not a quality or determinism
claim: the two MTP-off starts are text-identical (1,289 chars) and the three `draft-mtp` starts are text-identical
(1,454 chars), but **off and on diverge within the first sentence**, so this is a §6 speed row and nothing else.

**Follow-up 2026-11-16: the win survives a long prompt, and the sign is set by ACCEPTANCE, not by length.** The 446-token
row above predicted that a long prompt would flip the sign, because the drafter's prefill tax grows with the prompt. On the
**19,717-token** prompt it did not: **-7.05 % wall** (21.075 -> 19.591 s), prefill **+6.03 % (+941 ms)**, decode
**-44.5 % (-2,420 ms)**. The prediction was wrong twice and both errors are the same error: **acceptance was 97.94 %
(190/194)** on that prompt against **57.71 %** on the prose one, because a numbered list is predictable and prose is not.
Two-point fit on the tax - **~97 ms + 0.0428 ms/token** - puts the crossover at ~**14,100** prefill tokens at prose
acceptance and ~**54,000** at 98 %. So: **every MTP row declares prompt length AND acceptance/offered**, because the two
together decide the sign, and "MTP pays" is meaningless without both.

## 6. Determinism

A "same flags, same answer" claim is a claim about **plain text at one chunk size** and nothing more.

| Field | Why it exists | Readback |
|---|---|---|
| `near_tie_statement` + `chunk=` on every KL row | Sparse block selection sits on near-ties (gap < 1e-3 on 75-93 % of queries) and any chunk change flips which blocks are picked on 70-90 % of queries: agent prompts get **O(1) KL** where plain text moves ~1e-5. The vendor's own earlier agent KL figures may be inflated by this and were not re-measured (2026-11-05). | analysis note |
| `moe_cache_cpu_share` | **Measured negative at 4096 MiB, 2026-11-16.** Cache fixed at the elbow, share 0 / 0.5 / 0.95:
**85.09 -> 68.48 -> 63.16 tok/s** (-19.5 % / -25.8 %), prefill flat (+-2 %). The mechanism, from the companions: hit rate
**unchanged** (74.08 -> 74.25 %), **`uploaded` down 39 %** (18,339.75 -> 11,162.81 MiB), but **4,178 of 10,793 misses
computed on the CPU** per 128 tokens on 8 threads - saving a third of the uploads costs a fifth of decode. The sign at
6144+ is untested; `#30966`'s published numbers are not ours. | `--help` (present, l.137 of `llama-cli`), the engine's
`N % of the misses on the CPU` in its cache line, and the companion's `hit rate`/`uploaded` |
| `moe_cache_tokens_worth` | **New 2026-11-15.** A cache rung is declared in **`tokens worth`**, not MiB: on `b12383` the rungs read
0.9 / 1.9 / 3.8 / 7.6 / 9.9 / 11.4 tokens' worth, and the elbow is **7.6** (+96 % decode) with nothing above it beating
its own spread. Read it with **`-lv 4`** (`N slots (x %, Y tokens worth)`); at default verbosity this build prints
nothing about the cache, and the control prints neither line. The hit rate prints **only when the context is freed**, so
a force-stopped server needs a `llama-cli` companion for it. `LLAMA_MOE_CACHE_TRACE` writes a binary `MCT1` file and is
not a text channel. **The cache costs prefill: -25.8 %, fully spent by 2048** - a decode-for-prefill trade, not a free
win. | `-lv 4` slots line; companion `llama-cli` `hit rate = N %`; `CACHE-CEILING-2026-11-15.md` |
| `expert_cache_on` || `expert_cache_on` | The vendor traced five-different-answers to the expert cache: `--no-expert-cache` restores repeats at **8-10 % decode (58 % on one card)** (2026-10-31). Our 2026-10-08 MTP row is **speed-and-letters only** and cannot be quoted as determinism. | `--no-expert-cache`, `DS4_ASYNC_T` |
| `prefill_cpu_share` | See §4: ON below a 1024-token chunk, mean KL ~0.004 against 0.1.40.3 - the largest declared text-change knob on our line. | environment + binary string |
| `adapt_async` | `--adapt-async 1` states **"Not bit-exact run to run"**; 0 is the blocking tier and the default. Declare it, because an asynchronous tier in any A/B voids text identity. | `--adapt-async` argv |
| `route_prior` | 0.1.52 printed the routing state, 0.1.55 prints nothing when the prior is off (`#5000`). So a row is **"prior absent by construction"** (pre-0.1.52) or **"prior 0"**, never both. Price at 1.5: **+22.9 % perplexity** and AIME **-10.0 pts for +45 %**. | engine log (pre-0.1.52 only); ours: absent by construction on 0.1.47 |
| `strata_kva` | `#5289`: `STRATA_KVA=1` + a `q2_0` native pack is **8/8 SIGSEGV** on the first long prefill on 0.1.58, clean without KVA. Not our engine: **0.1.47 has no `STRATA_KVA` string at all** (2026-11-09), so it cannot be set here. The rule arms when we move to >= 0.1.55. | strings check + environment |
| `fa_quants` / `kv_types` | A quantised-KV row names the **binary's `GGML_CUDA_FA_QUANTS`** and the K/V types: the default Windows CUDA build does not compile the `q8_0-q4_0` pair and **silently converts to f16** (2026-10-28), so the row measures f16 while claiming a quant. **2026-11-14**: `#31802` fuses **q8_0 / q4_0 / `f8_e4m3`** dequant in the MMA flash-attention kernels and is still open, while **v1.0.0 ships FP8 KV caches as `-ctk/-ctv f8_e4m3`** with optional static per-tensor scales (`#28392`) - so `f8_e4m3` joins the two types our KV rows had, the list is three, and the flag pair is what a row names. v1.0.0 also **removed `--defrag-thold`** and 35 deprecated functions: a stored command line from an older note is now an error rather than a no-op. | build configuration; engine log `no FlashAttention vector kernel compiled for K/V types ... converting K and V to f16 instead` |
| `top_k_impl` / `cccl_version` | `#31084`: tied-selection ran a **non-deterministic KLD 0.0004-0.011**, and `DeviceTopK` still serves single-token decode at CCCL >= 3.4.3. llama.cpp rows only. | build configuration |
| `expert_profile` | Our learned `.strp` is a 48-layer x 512-expert file; English-calibrated pruning costs **1.7 English points against 21.4 Lithuanian at 25 %** (`2611.07654`), so a routing instrument is task-specific and its calibration text is a declaration. | `.strp` sha256 + the text it was learned from |
| `compiled_locally` | A local build at the release tag, sm_120 only, nvcc 13.2, scored **0/10** on a tool-call probe where the packaged binary scored 10/10 (`#4879`). A tool-call workload's load check is a tool-call-shaped probe. | build record |

## 7. Sampler and client

| Field | Why it exists | Readback |
|---|---|---|
| `client_sent_samplers` | Ollama's `/v1` overwrote model-card sampler values with 1.0/0 until `#19432`; Strata `#2940` merges `presence_penalty: 1.5` into non-thinking requests. A row must say whether the client sent values or the server's defaults stood in. | request body vs the server's effective settings |

## 8. What reading the 0.1.47 binary settled (2026-11-09)

Three owed items, answered from the staged asset rather than from a run: `strata.exe --version` (no model, no
engine start) and `strings -a`.

1. **`--prefill-borrow` exists, undocumented.** `--help` prints **266 lines and 0 hits for `borrow`**; the binary
   contains the literal **`--no-prefill-borrow`**. So the loan is a real switch on our line, absent from the help
   text - the same class as `--vram-reserve-mib` and `--resident-budget-gib`, which are also accepted and also
   unlisted. `--help` describes the default behaviour instead: *"auto = the largest chunk up to 8192 whose buffers
   the expert cache can lend"*. **A flag being absent from `--help` is not evidence the engine lacks it**, and
   the check is `strings`, not the help text.
2. **`STRATA_KVA` does not exist in 0.1.47** - no string in the binary. The Q2_0 + KVA SIGSEGV (`#5289`) cannot
   fire on our line, which matches the scan's reading that KVA arrived with 0.1.55. The void rule is written now
   and armed for the next engine.
3. **The engine's own memory report is not available on this path.** No `memory report` string, no user-facing
   `scratch` field: `scratch` appears only as internal region names (`SessionLoopScratch`, `prefill gemm: scratch`,
   PLE scratch). The `2.03 GB scratch` decomposition is a DSV4-engine feature (`#5570`), so on the Qwen path the
   field is `unreported` and the substitute is OS-side plus the engine's own sizing lines, which the templates in
   §3 quote verbatim.

Two further facts fell out of the strings, both declaration-relevant:

- **`prefill: the CPU share is ON by default for prompt chunks below 1024 tokens`** … *"answers can differ
  slightly from 0.1.40.3, mean KL ~0.004"*, `STRATA_PREFILL_CPU_SHARE=0` to turn it off. That is a text-changing
  default on our line that the declaration list has never carried, and it fires on exactly the arms whose chunk
  clamps to 512.
- **`--mmap-experts` carries a measured cold/warm pair** the notes had never quoted: *"measured 71.97 vs 34.78
  ms/token cold vs warm"* - the engine's own version of our "a rate inherits the machine's prior workload" rule.

## 8b. A start can fail at warmup when post-load commit headroom is thin (2026-11-16)

`CUDA error: shared object initialization failed` in `ggml_cuda_flash_attn_ext_mma_f16_case` /
`cudaFuncSetAttribute(MaxDynamicSharedMemorySize)` killed **6 of 17 starts** across two suites today, against **0 of 20**
in the ladder and **0 of 5** the day before, with an identical scheduler graph and a clean retry each time. Every one of
those runs sat at **`commit_at_ready` 0.45-0.87 GiB**. The mechanism is the class recorded on 2026-10-30 (Ollama `#17380`:
a pinned-host-buffer allocation failing under commit pressure degrades silently and the first kernel launch dies) and on
2026-10-11 (our own `-b 512 -ub 512` workaround). Two consequences for a declaration:

- **`commit_at_ready` below ~1 GiB is a warning, not a fact to discover later**: record it, and prefer a start that leaves
  more. The admission gate cannot see this - that is why the field exists.
- **A start that dies in warmup is re-queued once before an arm is called broken**, and the attempt count is declared.
  Without that rule, a flake reads as a model or engine defect - the 2026-11-01 `#4879` class in a different costume.

## 9. Void rules

**Before start.** An arm is not started, and the reason is written, when any of these is true:

1. A **size check is the only pack check** on a pack whose repository has moved revision since staging.
2. `STRATA_KVA` is set on a `q2_0` native pack (**>= 0.1.55 only**; `#5289`, 8/8).
3. Free physical < 9 GiB, free commit < 8 GiB, or free VRAM < 0.5 GiB (the env gate, unchanged since 2026-09).
4. The card is not idle for the ladder's whole duration (`comfy` busy or WSL running): contention cost 4 of 12
   arms on 2026-10-31 and cannot be subtracted afterwards.

**Build boundary (added 2026-11-15, table in §12).** An arm is not started on a build below the boundary of a
feature its configuration uses, and an arm taken below one is void with the boundary quoted, not with "old build".
Today that is one line: **`-nkvo` added to `--moe-cache-mib` is legal from `b12383` and VOID below it** (`#31775`;
below it the load aborts at `src/llama-moe-cache.cpp:560` and measures nothing). The check is the build id from
`--version` against §12, **not the release name** - `v1.0.0` is still `b12359`'s tree and sits below it.

**After start, from the arm's own log** - the gate `ai_bench/staged-strata-0.1.47/control/chunk_ladder.py` already
enforces these mechanically:

5. The declared chunk differs from the granted chunk, **or** a clamp line appears (rule 1).
6. The lend region had 0 experts in RAM **and** the file tier was unbuffered (rule 2). 0-lend *with* "the file
   cache can keep them" is a warning, not a void - the engine fires `#669` before it builds the RAM copy.
7. The granted `expert cache N slots` differs from a declared `--expert-cache` (rule 3).
8. The engine ran a reserve other than the declared `--vram-reserve-mib` (rule 4).
9. `session state allocation failed` or `-> 0 slots`: a start failure, always void, re-queued.

**Never quotable, whatever the numbers say**

10. A rate from the app footer, monitor, model API or console: the vendor's own audit found those reading up to
    **632 tok/s where the per-request line read 50-75**, and "about half" where the denominator was the whole
    request (2026-10-21). Quote the per-request line and name numerator and denominator.
11. A prefill number without `resident=`, `prefill=`, `cache=` and `reserve=`.
12. A decode rate without a numerator, or a ranked comparison read off a distribution with overlapping ranges
    (our own 0.1.54/0.1.55 "regression" was retracted by its reporter as a warm-up artifact, 2026-11-02).
13. A KL row without `chunk=`, and an agent-prompt determinism claim at all.

## 10. Fields the catalog still lacks

Named so the next scan does not re-derive them: **engine-reported `scratch`** (§8 item 3, needs a newer engine or
a DSV4 path), **power draw** (`#5490`: decode halved while GPU power fell 400+ -> 300-330 W and cache hits stayed
99 % - a decay our token and VRAM instruments cannot see), **verify-window MiB from the log** (declared in §5 but
only measurable if the engine prints it), and **the `.strp` calibration text** for our learned profile (the *pack's*
calibration text is now a field, §2 `pack_calibration_text`). Two more were added on 2026-11-15 and are `unreported`
rather than missing: the **prefill ring** and the auto value it replaced (§4, needs >= 0.1.59 or a `strings` hit on
0.1.47), and the **expert-read mode** (§3, needs the tier line plus the declared value side by side).

## 11. Copy-paste block

```yaml
# identity
engine_version: ""          # strata.exe --version
engine_build_id: ""         # from the release feed; --version prints none
engine_binary_sha256: ""
engine_arch_list: ""        # sm_75, sm_86, sm_89, sm_120, compute_120
toolchain: ""
# pack
pack_repo: ""
pack_revision: ""
pack_src_sha: ""            # unreported if the pack ships no .src_sha
pack_files: []              # name, bytes, sha256
pack_tensor_types: ""       # expert down projection type, from one header read
sidecars: []                # mmproj / mtp / dflash: name, bytes, quant
pack_calibration_text: ""   # UNVERIFIED when the publisher declares none (both our packs)
# host before the load
host: {free_physical_gib: 0, free_commit_gib: 0, pagefile_mib: 0, commit_limit_gib: 0,
       free_vram_mib: 0, wsl: stopped, comfy: idle, prior_workload: ""}
# memory contract
resident_declared_gib: 0
resident_granted_gib: 0     # FileExpertSource: ... exceeds available ...
expert_cache_declared: 0
cache_granted_slots: 0      # expert cache N slots, X GiB of VRAM
vram_reserve_mib: 0         # accepted, not in --help
file_tier_line: ""
engine_memory_report: unreported   # no report on the Qwen path in 0.1.47
free_vram_per_request_mib: []      # one sample per request
wddm_shared_usage_mib: 0
expert_read_mode: ""        # file mapping | unbuffered (§3; this box is the boundary)
cast_buffer_pin: ""         # ComfyUI arms: aimdo_enabled + the pin's size if it stalls (§3)
# prompt path
prompt_tokens: 0
prefill_declared: ""        # auto | auto:16384 | N
chunk_granted: 0            # prompt chunk auto: N tokens
clamp_line: ""
prefill_borrow: ""          # present (--no-prefill-borrow) | absent-by-binary
prefill_cpu_share: ""       # ON below a 1024-token chunk, mean KL ~0.004
lend_region: ""             # #669 line
prefill_ring: {declared: "", auto: unreported}   # 0.1.59+: STRATA_PREFILL_RING and the auto value
ubatch: null                # llama.cpp rows
batch_slots: 1
prompt_cache: {reused: 0, checkpoints: 0}
first_request_ttft_s: null  # before any warm-up
# speculation
drafter: ""                 # Drafting: <mode>
spec_n: 0
draft_conf_in_force: ""     # never "auto"
drafts: {accepted: 0, offered: 0}
mtp_dir: {quant: "", bytes: 0}
verify_window_mib: null
spec_kernel: ""             # #31533 few-row MMQ: in >= b12359, not in b12208 (§12)
# determinism
chunk: 0                    # identical to chunk_granted, restated for KL rows
expert_cache_on: true
adapt_async: 0
route_prior: absent-by-construction   # 0.1.47 predates the printed state
strata_kva: absent-in-binary           # >= 0.1.55: void on q2_0
top_k_impl: null
cccl_version: null
expert_profile: {path: "", sha256: "", calibration_text: undeclared}
compiled_locally: false
# client
client_sent_samplers: true
```

---

## 12. What is VOID below which build

Added **2026-11-15** so that no line elsewhere has to carry a build boundary of its own, and so that a superseded
boundary reads as superseded. A row is **void** when its build sits below the boundary of a feature it uses; the
reason written in the row is the boundary's own line, never "old build". The check is always the **build id**, never
the release name.

| feature the row uses | boundary | why the boundary, and what happens below it | readback |
|---|---|---|---|
| **`-nkvo` added to `--moe-cache-mib`** | **`>= b12383`**, published 2026-11-14T14:43:25Z | `#31775` is the scheduler abort on this pairing, and `b12383` is the **first tag containing its merge commit** (`compare/c56be864f...b12383` -> **behind 0**; there is no `b12382`). Below it the load fails at `src/llama-moe-cache.cpp:560: the experts of layer 0 are selected in the same split as their MoE cache lookup` - a start failure that measures nothing, not a slow row. Payoff from the tag up, as the fix's commenter measured it: `-nkvo` prefill **pp512 397 -> 435** on Qwen3.6-35B-A3B and **264 -> 345** on Qwen3.8-Flash-Next, **tg unchanged**. | build id in `--version` >= `b12383`; `gh api repos/ggml-org/llama.cpp/compare/c56be864f...<tag>` -> `behind 0` |
| deterministic tied Top-K (§6 `top_k_impl`) | **`>= b12208`** | `#31084` *is* that merge commit (`compare/b12208...57d04820df` identical): mean KLD **0.0011 -> 0.000000**, same-top-p **99.48 -> 100.000 %**. Below it a "same flags, same answer" row is not one. Still route-dependent at **CCCL >= 3.4.3**, where single-token decode goes through `DeviceTopK` - so the row names the implementation beside the build. | build id + `cccl_version` |
| MTP / speculative rows - **a comparability boundary, not a void** | `#31533` is in **`>= b12359`**, not in `b12208` | A speculative row below the kernel is a **different configuration**, not a wrong one: our b11461 row (+31.2 % per token, -7.3 % wall) predates the kernel that makes the verify step cheap, so it may not be compared with a later MTP row in either direction. Declare `spec_kernel` (§5). | `gh api repos/ggml-org/llama.cpp/compare/0fb8f1577...<tag>` |
| ComfyUI cast-buffer reset on the non-aimdo path (§3) | **in no release we hold** | `#17122` / `#17123`: since `#14372`, `reset_cast_buffers()` runs only when `aimdo_enabled` is true, so `LARGEST_CASTED_WEIGHT` can pin ~13 GB of an encoder's mapping through a 15 MB tensor. `v0.45.0` is still the newest published release and `v0.45.1`/`v0.45.2` are still 404, so there is no version to pin to; whether `#17123` has merged is **UNVERIFIED** in the 2026-11-15 scan. An image arm on the non-aimdo path states the pin rather than calling the stall an OOM. | release feed (`v0.45.0`); PR state of `#17123` |
| GGUF tensor parsing - **not ours**, recorded so it does not silently become ours | the advisory's own range: vulnerable **< b7437**, patched **b7824**, leaving **b7437-b7823 unclassified** | `#32334` / **GHSA-96jg-mvhq-q7q7** (CVE-2026-33298), heap overflow in GGUF tensor parsing. Every build this lab pins is far above it, so it adds no boundary - it is a scanner problem (a gap in the advisory), not an engine one. | advisory text; build id |

**How this composes with §9.** The four before-start and five after-start rules there are unchanged; this table is the
*build* half of the same gate. Two consequences worth spelling out because both have been got wrong: a **versioned
release is a name, not a boundary** (`v1.0.0` is `b12359`'s tree - it contains `#31533` and **not** `#31775`), and a
**closed issue is not a moved boundary** (`#32170`, the lazy-KV PR, was closed unmerged at 2026-11-15T12:13:36Z, so
KV is still reserved before experts are placed and nothing in this table moved).

---

Provenance: `NEWS-2026-10-23` .. `NEWS-2026-11-08` (the field-by-field history), `CHUNK-LADDER-AND-RESERVE-2026-10-26.md`
(the gate's four rules), `RESIDENT-ABOVE-8-2026-11-01.md` (`resident=` and the lend arithmetic),
`RESIDENT-DECLARATION-2026-10-31.md` (declared vs granted), `WDDM-SHARED-SEGMENT-2026-10-22.md` (the shared segment),
and the 0.1.47 asset read on 2026-11-09 (`--help`, `--version`, `strings`) recorded in §8. **2026-11-15** added the
`b12383` gate (§1, §12), `spec_kernel` and the MTP re-pricing (§5), `STRATA_PREFILL_RING` (§4), the expert-read mode
and the cast-buffer pin (§3), and `pack_calibration_text` (§2) - all from `NEWS-2026-11-15.md`, with the 1,100-item
null it re-reads quoted from `README.md` and `KNOWLEDGE-DEEP-2026-10-10.md`.
