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
| `llama_cpp_version` | llama.cpp rows only. **`v1.0.0` = commit `b1b770d`, published 2026-11-13T10:20:19Z** - the first non-0.x release, carrying **FP8 KV caches** and the MoE expert cache in a stable tag; newest rolling tag `b12376` (2026-11-14T08:42:49Z). **`#32245`**, filed within a day of the release: *"significant prefill performance drop on V100 (sm_70) in v1.0.0"* - not our sm_120, and the reason a versioned release is a **name** for a gauntlet, not a qualification for a row. | `--version` -> build + commit (`git rev-parse v1.0.0`); release feed |

## 2. Pack identity

| Field | Why it exists | Readback |
|---|---|---|
| `pack_repo` | Two packs share a name shape and a quant name (`UD-IQ4_XS-v31` is Strata's own pinned 09-30 copy, not the Hub's current layout, 2026-11-05). | `staged.json` -> `repo` |
| `pack_revision` | **The reference pack was re-converted twice after we staged it** (`7878dc9a90 -> eb0b3cc97f`, 2026-11-08) with Q4_K_M **+118 MiB**: a fresh download is different bytes under the same name. | `staged.json` -> `revision` |
| `pack_src_sha` | `.src_sha` moved `995ad96e -> 345d467b` in the same window, i.e. the **source model** moved, not only the GGUF. | Hub file `.src_sha` -> `PRIMARY=...`; `unreported` for packs that ship none |
| `pack_file_digest` | A size check cannot see a re-conversion; only the digest can. Per file: `name`, `bytes`, `sha256`. | `staged.json` -> `items[]`; re-verify with `sha256sum` before any row that claims identity |
| `pack_tensor_types` | The expert **down projection** type decides whether Strata's native kernels accept the pack (`#3699`: Q4_K downs are refused; our Qwen3.6 Q4_K_M has all 40 at Q4_K). | one GGUF header read |
| `sidecars` | mmproj / MTP / DFlash each add bytes and can be the failure: `-md` + `--mmproj` aborts every build after `#30257` (2026-11-02). | `staged.json` `items[]` for the sidecars |

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
| `engine_memory_report` | `#5570` decomposes a 16 GB card and finds a **2.03 GB `scratch`** region the layered line omits - 12 % of the budget, invisible to both `nvidia-smi` and the gate. Three engines now disagree with the OS by 4-8x, 100 % and 12 %. | **`unreported` on our line**: the 0.1.47 binary has no user-facing memory report and no `scratch` line (§8). Record `nvidia-smi` in-use, the `Shared Usage` counter delta and the engine's own sizing lines instead |
| `free_vram_per_request` | 0.1.46 drove a card to 0 MiB free and spiralled verify windows 61/49/28/13/0 MiB (`#3952`); `#4474` shows auto-sizing and grant disagreeing in one process. | `strata serve: VRAM %lld MiB kept free: … %lld MiB free now, prompt chunk %lld` |
| `wddm_shared_usage` | Under WDDM every page-locked GPU-mapped buffer is charged to a ~half-of-RAM segment that commit cannot see; 17.8 GiB measured on this box (2026-10-22), and registration succeeding is not residency acquired (2026-11-04). | perf counter `GPU Adapter Memory\Shared Usage` before and under load |

## 4. Prompt path

| Field | Why it exists | Readback |
|---|---|---|
| `prompt_tokens` | The chunk optimum is a function of prompt length; `--prefill auto` cannot exceed 8192 by construction (`#4683`) and a rung that does not name its prompt length is unreadable (2026-10-30). | the request's own token count |
| `prefill_declared` / `chunk_granted` / `clamp_line` | Rule 1 of the gate. The chunk bends to fit the cache: `WARNING: prompt chunk 5376, not 8192: CUDA1 has 1128 expert-cache slots` (`#4261`). | `strata generate: prompt chunk auto: %lld tokens`; clamp line as quoted |
| `prefill_borrow` | The loan our 10-27 and 10-31 ladders measured from the outside is a **switch**: `--no-prefill-borrow` is a literal in the 0.1.47 binary (2026-11-09). | argv; `--help` does not list it |
| `prefill_cpu_share` | **New 2026-11-09.** The 0.1.47 binary states that the CPU share is **ON by default for prompt chunks below 1024 tokens** and that *"answers can differ slightly from 0.1.40.3, mean KL ~0.004"*; `STRATA_PREFILL_CPU_SHARE=0` turns it off. Any arm whose chunk clamps to 512 is a different-text arm. | binary string `prefill: the CPU share is ON by default for prompt chunks below 1024 tokens …`; value from the environment |
| `lend_region` | Rule 2 of the gate. `0 of 790` in RAM at every rung 2-16 GiB because the ranked set eats the whole budget; 1.02 GiB of lend needs ~31.7 GiB resident (`RESIDENT-ABOVE-8-2026-11-01.md`). | `strata generate: WARNING: a prompt chunk of %lld tokens lends %lld cache slots to the prompt path, but only %lld of their experts fit in RAM … (#669)` |
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

## 6. Determinism

A "same flags, same answer" claim is a claim about **plain text at one chunk size** and nothing more.

| Field | Why it exists | Readback |
|---|---|---|
| `near_tie_statement` + `chunk=` on every KL row | Sparse block selection sits on near-ties (gap < 1e-3 on 75-93 % of queries) and any chunk change flips which blocks are picked on 70-90 % of queries: agent prompts get **O(1) KL** where plain text moves ~1e-5. The vendor's own earlier agent KL figures may be inflated by this and were not re-measured (2026-11-05). | analysis note |
| `expert_cache_on` | The vendor traced five-different-answers to the expert cache: `--no-expert-cache` restores repeats at **8-10 % decode (58 % on one card)** (2026-10-31). Our 2026-10-08 MTP row is **speed-and-letters only** and cannot be quoted as determinism. | `--no-expert-cache`, `DS4_ASYNC_T` |
| `prefill_cpu_share` | See §4: ON below a 1024-token chunk, mean KL ~0.004 against 0.1.40.3 - the largest declared text-change knob on our line. | environment + binary string |
| `adapt_async` | `--adapt-async 1` states **"Not bit-exact run to run"**; 0 is the blocking tier and the default. Declare it, because an asynchronous tier in any A/B voids text identity. | `--adapt-async` argv |
| `route_prior` | 0.1.52 printed the routing state, 0.1.55 prints nothing when the prior is off (`#5000`). So a row is **"prior absent by construction"** (pre-0.1.52) or **"prior 0"**, never both. Price at 1.5: **+22.9 % perplexity** and AIME **-10.0 pts for +45 %**. | engine log (pre-0.1.52 only); ours: absent by construction on 0.1.47 |
| `strata_kva` | `#5289`: `STRATA_KVA=1` + a `q2_0` native pack is **8/8 SIGSEGV** on the first long prefill on 0.1.58, clean without KVA. Not our engine: **0.1.47 has no `STRATA_KVA` string at all** (2026-11-09), so it cannot be set here. The rule arms when we move to >= 0.1.55. | strings check + environment |
| `fa_quants` / `kv_types` | A quantised-KV row names the **binary's `GGML_CUDA_FA_QUANTS`** and the K/V types: the default Windows CUDA build does not compile the `q8_0-q4_0` pair and **silently converts to f16** (2026-10-28), so the row measures f16 while claiming a quant. **2026-11-14**: `#31802` fuses **q8_0 / q4_0 / `f8_e4m3`** dequant in the MMA flash-attention kernels and is still open, while **v1.0.0 ships FP8 KV caches** - so `f8_e4m3` joins the two types our KV rows had, and the list is three. | build configuration; engine log `no FlashAttention vector kernel compiled for K/V types ... converting K and V to f16 instead` |
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

## 9. Void rules

**Before start.** An arm is not started, and the reason is written, when any of these is true:

1. A **size check is the only pack check** on a pack whose repository has moved revision since staging.
2. `STRATA_KVA` is set on a `q2_0` native pack (**>= 0.1.55 only**; `#5289`, 8/8).
3. Free physical < 9 GiB, free commit < 8 GiB, or free VRAM < 0.5 GiB (the env gate, unchanged since 2026-09).
4. The card is not idle for the ladder's whole duration (`comfy` busy or WSL running): contention cost 4 of 12
   arms on 2026-10-31 and cannot be subtracted afterwards.

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
only measurable if the engine prints it), and **the `.strp` calibration text** for our learned profile.

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
# prompt path
prompt_tokens: 0
prefill_declared: ""        # auto | auto:16384 | N
chunk_granted: 0            # prompt chunk auto: N tokens
clamp_line: ""
prefill_borrow: ""          # present (--no-prefill-borrow) | absent-by-binary
prefill_cpu_share: ""       # ON below a 1024-token chunk, mean KL ~0.004
lend_region: ""             # #669 line
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

Provenance: `NEWS-2026-10-23` .. `NEWS-2026-11-08` (the field-by-field history), `CHUNK-LADDER-AND-RESERVE-2026-10-26.md`
(the gate's four rules), `RESIDENT-ABOVE-8-2026-11-01.md` (`resident=` and the lend arithmetic),
`RESIDENT-DECLARATION-2026-10-31.md` (declared vs granted), `WDDM-SHARED-SEGMENT-2026-10-22.md` (the shared segment),
and the 0.1.47 asset read on 2026-11-09 (`--help`, `--version`, `strings`) recorded in §8.
