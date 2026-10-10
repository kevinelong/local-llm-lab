# RAM install verification, 2026-10-07 (post-boot, read-only checks)

Plan this verifies: local-llm-lab/RAM-INSTALL-2026-10-07.md Part 3.
Nothing was loaded, no inference was run, no gate was changed. One read-only
frozen preflight was executed (it creates no lock, see Notes).

## Verdict

The module is installed, recognised, trained at rated speed and BOTH channels are
active. Capacity 32 -> 64 GiB; the RAM constraint that blocked the decision
track and Strata's resident budgets is gone.

| Check | Expected (action sheet) | Measured | Result |
|---|---|---|---|
| Win32_PhysicalMemory entries | DIMM1 + DIMM2 | DIMM1 + DIMM2, 34359738368 B each | PASS |
| ConfiguredClockSpeed | 5600 (watch for 4800/5200) | 5600 / 5600, no down-bin | PASS |
| Total visible | 63.8-64 GiB | 63.46 GiB | PASS (see reservation note) |
| Channels | dual | 71.4 GB/s copy traffic > 44.8 GB/s single-channel ceiling (inference, see below) | PASS |
| BIOS "Memory Channel Mode = Dual" | Dual | NOT READ (no BIOS access from Windows) | unverified |
| Memory-corrected errors | none | none; all WHEA events are the RTX 5070 PCIe link, pre-existing | PASS |

## Module identity

- DIMM1 (unchanged): SK hynix HMCG88AGBUA084N, 32 GiB, 5600, manufacturer ID
  0x80AD, SPD serial 98D87E7E.
- DIMM2 (new): Kingston module part number 9905782-147.A00G, 32 GiB, 5600,
  manufacturer ID 0x0198 (Kingston), SPD serial 3B0A3E59.
- SMBIOS memory type 34 (DDR5), FormFactor 8 (DIMM), DataWidth == TotalWidth ==
  64 (no ECC), Speed == ConfiguredClockSpeed == 5600 for both.
- The ordered part was KVR56U46BD8-32. Kingston's datasheet for that SKU is
  "32GB 2Rx8 4G x 64-Bit PC5-5600 CL46 288-Pin DIMM", SPD timing 46-45-45 at
  1.1 V, On-Die ECC. Every field Windows exposes matches that SKU; the SPD
  module part number (9905782-147.A00G) is Kingston's internal DIMM number and
  was not resolvable to the SKU string online (kingston.com partid page returns
  HTTP 403 to the fetcher), so the SKU match rests on capacity, DDR5, x64
  non-ECC, 5600 and manufacturer ID, not on a documented number mapping.
- Rank (2Rx8) is not exposed by Win32_PhysicalMemory; not verified from the box.

## Capacity arithmetic

Windows reserves the same 0.54 GiB of physical address space as before:
31.46 GiB visible on 32 GiB installed, 63.46 GiB visible on 64 GiB installed.
TotalPhysicalMemory == TotalVisibleMemorySize == 63.46 GiB. The action sheet's
"63.8-64" expectation was optimistic; the measured value is exactly
2x the old figure, so nothing is being withheld.

## Channel evidence (bandwidth, not a BIOS read)

2 GiB float64 arrays, numpy 2.4.4, array.copyto into a second 2 GiB array;
reported GB/s = read+write traffic, best of 3.

| Threads | Copy traffic (GB/s) |
|---|---|
| 1 | 39.7 |
| 2 | 50.4 |
| 4 | 62.7 |
| 8 | 67.8 |
| 16 | 71.4 |

DDR5-5600 single channel peak is 44.8 GB/s and dual channel 89.6 GB/s. 71.4 GB/s
is 79.7% of the dual-channel peak and exceeds the single-channel ceiling by 59%,
which no single-channel configuration can reach. Independent check: an 8-thread
read (numpy sum, 2 GiB) measured 49.7 GB/s, also above the 44.8 GB/s
single-channel ceiling. Single-thread read was 10.3 GB/s (latency/compute bound,
not a bandwidth number).

## Boot health

- Boot 2026-10-07 02:23:49 local; LoggedOnUser session up normally.
- EventLog 6008 + Kernel-Power 41: previous shutdown at 01:51:32 was unexpected -
  that is the install-time power removal (unplug + power-button drain), not a
  fault observed now. Kernel-Boot 29 "fast startup failed 0xC0000411" follows
  from the same non-hygienic shutdown / hardware change.
- WHEA-Logger ID 17 x2 at 02:24:06: PCI Express corrected errors on the RTX 5070
  (PCI\VEN_10DE&DEV_2F04). Identical pairs occurred 2026-10-02, 10-04 and 10-06,
  i.e. before the install; nothing in the log points at memory.
- No WHEA memory-corrected error, no bugcheck, no thermal event.

## Frozen preflight (read-only, no lock created)

`python C:/Users/kevin/ai_bench/decisions-20261005-v1/run.py preflight`, run
2026-10-07 09:27 UTC (it calls resident_blockers() + mon.preflight() only; the
RUNNING.lock is created inside `screen()`, run.py lines 176-179):

| Gate | Required | Measured |
|---|---|---|
| physical_available_gib | >= 9 | 44.14 |
| commit_headroom_gib | >= 8 | 56.89 |
| gpu_free_gib | >= 7.5 | 10.60 |
| resident engine / port 8080 / decision port | none | none (ollama offline, no listener) |
| wsl_servers | none | none |

All unchanged gates pass with 4.9x headroom on physical RAM. No RUNNING.lock
exists in any ai_bench root after the check.

## Notes for the next run

- Every gate stays as it was: 9/8/7.5 GiB initial, 3/2/0.5 GiB runtime floors,
  6 GiB worker-private cap. 6 GiB worker cap is still an open decision for the
  nimble track (RAM-INSTALL Part 5).
- Use a NEW root for any re-run; existing RAM-stopped evidence stays
  constrained-platform evidence.
- .wslconfig is unchanged (memory=8GB). vmmemWSL was resident at 790 MiB with no
  distro workload; no WSL shutdown was performed, none is required by this check.
- `/v1/systemone` engines were not resident: nothing on 8080 or 11434. Ollama's
  process was absent (preflight: status offline_process_absence_verified).
- Still recommended inside the return window (through 2026-11-04): the first
  queued lab run as the real load test, and optionally mdsched.exe - the latter
  needs its own reboot and is Kevin's call.
- Not done, needs elevation: `manage-bde -status C:`. The box booted without a
  recovery prompt after a hardware change, which is evidence protection was off
  or already suspended, but that was never confirmed.
