# The WDDM shared segment on this box, measured: 17.8 GiB of our own resident arm
## 2026-10-22 — item 2 of the priority list, from `NEWS-2026-10-22` §3.1 / Strata #3725

## The claim being tested

Strata **#3725** (`altiber`, 2026-10-22T13:30Z) reports that under WDDM every page-locked, GPU-mapped host buffer
counts against the GPU's **shared (non-local) segment**, which Windows caps at roughly **half of system RAM** - and
that **commit capacity does not show this limit**. Their box: 31 GB RAM, cap ~15.5 GB, `GPU Adapter Memory\Shared
Usage` at 11.98 GB with a 10.5 GiB pinned complement, then `EngineDied` on a ~26 KB allocation that *names a token
buffer*. Yesterday's §2.1 stated the same rule from `FreeToken` #55 (13.77-13.82 GB of `cudaHostRegister` on 32 GB).

On this box (63.46 GiB RAM) the rule predicts a cap near **31.7 GiB**, which was previously `[INFERENCE]`.

## Instrument

`queue-20261016-shortlist/wddm_shared_segment.py` - Windows counters `GPU Adapter Memory(*)\Shared Usage` and
`\Dedicated Usage`, plus `Win32_OperatingSystem` commit figures, sampled at rest and during one resident arm:
llama.cpp **b11810**, `--cpu-moe --load-mode none --moe-cache-mib 5120 -c 131072 -n 1`. Result file
`result-wddm-shared-segment.json`.

## Measured

| | at rest | under the resident arm |
|---|---|---|
| `Shared Usage`, NVIDIA adapter | **163 MiB** | **17,941 MiB (17.52 GiB)** |
| `Shared Usage`, other adapter (iGPU) | 292 MiB | 292 MiB |
| `Dedicated Usage`, NVIDIA | 1.71 GiB | 11.2 GiB |
| commit free | 25.7 GiB | **0.84 GiB** |
| free physical | 33.46 GiB | 15.17 GiB |
| VRAM used / total | - | 11,383 / 12,227 MiB |
| decode | - | 72.7 tok/s |
| load | - | 14.6 s |

Reproduced twice: shared under load **17.63 GiB** then **17.81 GiB**.

## What this establishes

1. **The [INFERENCE] is now a measured number, and the headroom is smaller than it looked.** Predicted cap ~31.7 GiB
   against **17.5-17.8 GiB actually consumed** by one resident arm leaves **~13.9 GiB**, not "nothing we have
   measured comes near it". The earlier phrasing was too comfortable.
2. **Plain llama.cpp `--cpu-moe` charges this segment.** The mechanism #3725 describes is not specific to Strata's
   pinned complement: our experts mapped for `--cpu-moe` show up in the same counter, going from 163 MiB to
   17.5 GiB. So the ceiling binds *any* host-to-GPU expert mapping on Windows, including the route we use daily.
3. **The 24 GiB attempt that floor-tripped now has a mechanism.** "Pin all the experts" would have asked for ~24 GiB
   in this segment plus ~1.5 GiB of other mapped buffers (their measurement), i.e. within a few GiB of the ~31.7 GiB
   wall - and a failed mapping in their case surfaced as an unrelated allocation error, not as a budget refusal.
4. **Commit headroom, not RAM, is the binding gate in practice.** 25.7 -> **0.84 GiB** free commit under a single
   resident arm. That is why the lab's 8 GiB commit gate trips where free physical memory still reads 15 GiB.

## What this does not establish

- **The failure mode itself.** We cannot reproduce the pinned-complement refusal without Strata's qwen36 path,
  which our installed engines (**<= 0.1.41**) do not have - the `strata-q36:` loader in #3699 arrives later. This
  measures the *ceiling side* of the rule, not the death.
- Whether Windows' cap is exactly half of RAM on this build: we measured usage against an assumed cap, not the cap.
  Getting the cap directly needs the DXGI call the #3725 patch uses
  (`IDXGIAdapter3::QueryVideoMemoryInfo(0, DXGI_MEMORY_SEGMENT_GROUP_NON_LOCAL)`), which this instrument does not make.
- Anything about the iGPU adapter beyond its 292 MiB, which did not move under load.

## Consequence for the queue

- **Budget host-resident expert memory against ~31.7 GiB minus ~1.5 GiB of other mappings**, not against 63 GiB.
- **Read `Shared Usage` in every resident arm from now on** - it is two seconds of counters and it is the number that
  can abort a run, while commit headroom reads healthy.
- Re-test after the Strata 0.1.47 bump, which is what makes the pinned-complement path runnable here.
