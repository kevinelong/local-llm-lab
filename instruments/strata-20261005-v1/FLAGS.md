# Strata flags: what the recent videos recommend, reconciled with the pinned engine

Sources, in the order they were used. Everything the videos say is a secondary claim; the
pinned v0.1.39 tree at commit `6f32ec07` is the authority, and the chosen flags were
verified against its `setup.py`, `serve/runconfig.py`, `serve/server.py` and `docs/`.

## What the videos actually say

Most Strata videos have no captions (`hJ_Iw2E7cnc`, `4q_VlobZU0A`, `JD8_r5UDylc`,
`nN_bFUtrF1A`, `91rASFzuDPU`, `gR20MGAhll8`, `aNOUkWk9piU` all report "no subtitles"), so
only the two that carry auto-captions could be read in full.

- **Kai, "The New Way to Run 125B Models 6x Faster Than llama.cpp (Strata)"** (2026-10-02,
  79K views, `m0VHx73SAG0`, full transcript). Configuration advice, not flags:
  - the "6x" is a slowest-baseline against fastest-result comparison; like-for-like it is
    2-2.5x;
  - 64 GB RAM is the real threshold for the fast builds; on 32 GB the **Coder** build (half
    the experts removed) is what runs. This matches our `--check` verdict exactly;
  - **3-bit for coding, 2-bit for chat** (LiveCodeBench 87.4 full vs 86.3 IQ3 vs 81.1 Q2);
  - the expert cache is the whole engine; MTP (guess-and-check) is on by default and tested
    identical token-for-token when guesses are forced wrong;
  - **RAM bandwidth is the limit on the CPU half**; enabling XMP/EXPO in the BIOS is free
    speed ("the test machine ran 5,200 MT/s with the profile off");
  - on IQ builds the GPU and CPU round expert math slightly differently; against llama.cpp
    on the same 4-bit file the same token was chosen at 97.5-99% of positions.
- **Kai, "Is Frontier Class Local AI Finally Possible?"** (2026-09-09, 171K views,
  `1--PzaHafAU`, full transcript). Not Strata, but the measured framing: the 51B n-gram
  table belongs on the SSD by design, decode is what the headlines quote, and **prefill is
  the number nobody publishes** (a 32K-token agent system prompt at ~50 tok/s prefill is
  ~10 minutes). Relevant to us because a disk-bound 12 GB card is a prefill problem.
- **Woke Engineer, "Strata Setup Guide"** (Oct 2026, 7-page PDF). Concrete flags:
  `--check` first, `--yes`, `--family`, `--model`, `--context`, `--low-ram on|off`,
  `--kv`, plus "32 GB -> Coder (IQ1_M)", "~80 GB free disk", "1-3 minutes of freeze on
  first start", and the driver/RAM/CPU tables.

## What the pinned engine supports (authority)

`setup.py` flags: `--family {qwen,swift,coder,unsloth}`, `--model {Q2_0,IQ2_XS,IQ3_XXS,IQ3_S,IQ1_M,UD-Q4_K_XL,UD-IQ4_XS}`,
`--context N`, `--kv {int8,q4_0,k8v4}`, `--vision {yes,no,none,gpu,cpu}`, `--low-ram {auto,on,off}`,
`--experimental-speed-projection`, `--calibrate`, `--check`, `--yes`, `--no-start`, `--gguf-dir`,
`--data-dir`, `--gpu/--gpus/--layer-split`, `--host`, `--api-key`, `--port`, `--backend`, `--build`.

Engine args that `setup.py` itself writes for the Coder in low-RAM mode (verified in the tree):

```
--pack <PACK> --native <SHARD0> --ple-gguf <SHARD_WITH_PLE> --expert-profile data/expert-profile.bin
--expert-cache auto --prefill auto --spec 4 --spec-min-p 0.5 --mtp <rt> --max-context <CTX>
--kv int8 --mmap-experts
```

Config keys the server accepts (`serve/runconfig.py`): `sampling.temperature`, `sampling.top_p`,
`sampling.top_k` (1..64), `sampling.min_p`, `reasoning_budget_tokens`, `fit_max_tokens`,
`anthropic_thinking`, `effort_position`, `aliases`, `idle_unload_s`, `lazy_load`,
`engine_silence_s`, `api_monitor`, `open_browser`, `vram_reserve_mib` (default 700 MiB).

`--calibrate` is documented as measuring a few engine settings on this PC and keeping the
fastest (about 5-10 minutes; +7% on the Coder on the author's machine).

## Chosen set for this run, and why

Installer:

```
setup.py --setup --gguf-dir C:/Users/kevin/ai_bench/staged-strata-20260930/gguf \
  --family coder --model IQ1_M --context 32768 --vision no --low-ram on --kv int8 \
  --yes --no-start
```

| flag | choice | reason |
|---|---|---|
| `--family coder --model IQ1_M` | Coder, 1-bit | the only size that fits 31 GB RAM, and the only size we already have staged (59.3 GB, hash-verified) |
| `--context 32768` | 32K | the installer default below 14 GB VRAM; KV streaming only matters from 64K, so 32K keeps the KV cache in VRAM |
| `--vision no` | text only | no image workload in the scoring task; saves VRAM and skips the vision engine |
| `--low-ram on` | forced on | `low_ram_needed()` is true (31 GB < 23.4 GB arena + 10 GB headroom) and `--check` says so; `auto` would pick the same |
| `--kv int8` | 8-bit | the default; `q4_0` costs 8-12% perplexity, and `k8v4` only pays off on large cards at long context (it also disables KV streaming) |
| speed projection | off | vendor control vector that changes answers; the staging record prohibits it |
| `--calibrate` | run after install | README-recommended, machine-specific, does not change the model |

Config additions written after install (declared, recorded in `evidence/config.json`):

```json
"sampling": {"temperature": 1.0, "top_p": 0.95, "min_p": 0.0, "top_k": 64},
"open_browser": false,
"draft_vocab": "en"
```

Deviation to declare: the lab's declared `top_k 0` (disabled) cannot be expressed; the
server clamps `top_k` to 1..64, so 64 is used and declared. `seed` is not a config key; it
is passed per request and is forwarded to the engine (`serve/server.py` sampling line).

`--draft-vocab en` comes from the installer's own tip for a 12 GB card: the default CJK
MTP draft subset needs up to ~348 MiB of VRAM, the English one up to ~133 MiB, and the
rest stays with the expert cache. The Coder pack is the English/code build, so this is the
subset the workload needs.

## What setup actually wrote (verified in `strata-coder-iq1_m.json`)

```
--pack <Strata-data>/packs/coder-iq1_m  --native <IQ1_M shard 1>
--ple-gguf <IQ1_M shard 2>  --expert-profile data/expert-profile-coder.bin
--expert-cache auto  --prefill auto  --spec 4  --spec-min-p 0.5  --mtp <Strata-data>/mtp/rt
--max-context 32768  --kv int8  --resident-experts  --pool-workers 15
```

Two corrections to the pre-install expectations:

- **The low-RAM variant ended as `--resident-budget-gib 4` plus `STRATA_LOOKAHEAD=0`.** Each
  step is measured, and every floor was unchanged throughout:

| variant | min free physical | min commit headroom | min GPU free | outcome |
|---|---|---|---|---|
| `--resident-experts` (setup's default) | 2.77 GiB | 3.71 GiB | 0.70 GiB | stopped mid-load |
| `--mmap-experts` | 1.92 GiB | 15.92 GiB | 1.12 GiB | ready, served, stopped mid-request |
| `--resident-budget-gib 20` | 2.53 GiB | 3.32 GiB | 1.16 GiB | ready, stopped just after load |
| `--resident-budget-gib 20`, after the reboot | 2.77 GiB | 3.76 GiB | 1.53 GiB | ready, stopped at the first request |
| **`--resident-budget-gib 4` + `STRATA_LOOKAHEAD=0`** | **10.36 GiB** | **11.11 GiB** | **1.46 GiB** | **probe completed, no guard trip** |

  Floors: 3 GiB free physical, 2 GiB commit, 0.5 GiB GPU. Cause of the earlier trips,
  quantified: the Coder's expert working set is about 30 GB on 31.46 GiB of RAM, and Windows
  counts the file cache it reads from as not-free; the reboot's extra 3 GiB were simply
  absorbed by that cache. The small resident budget plus disabling the lookahead prefetch is
  what keeps the cache from filling the box. The standby cache is reclaimable (it fell from
  14.89 to 4.36 GiB on its own after the guard stopped the engine), which is why commit
  headroom always stayed healthy.
- `--vram-reserve-mib 1500`: the engine's default 700 MiB left gpu_free at 0.32 GiB against
  the 0.5 GiB floor (the desktop already holds about 1.2 GiB and the engine locks the expert
  cache on top). 1500 MiB holds the floor at 1.46 GiB free and costs a few cached experts.
- `--pool-workers 15` is measured, not chosen: 8 performance cores plus half the efficiency
  cores; `--calibrate` re-measured it on this PC and tuned `--pcie-frac 0.75` and
  `--spec-min-p 0.50`, taking the measured rate from 19.5 to 22.5 tok/s on this box.

Not used: `--gpus`/`--layer-split` (one card), `--host 0.0.0.0`/`--api-key` (local only),
`idle_unload_s` (one workload at a time), `reasoning_budget_tokens` (left at the model
default so the screen is comparable with the MiMo runs, which declared thinking on with no
cap), `vram_reserve_mib` (engine default 700 MiB is what the vendor measured).
