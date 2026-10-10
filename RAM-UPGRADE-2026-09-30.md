# RAM upgrade decision record: Dell Tower Plus EBT2250

Date: 2026-09-30. Owner: Kevin, machine DARKTEXAS.

Status: module ORDERED, not yet installed. No inference has been run this session.

## Why this note exists

The local-LLM work was blocked on host system RAM, not VRAM and not the
platform. This file records the measured constraint, the option analysis, the
purchase, and the verification/rollout plan so the next session can resume
without redoing the research. Pricing in this market moves weekly; re-check
before any further purchase.

## Baseline (queried live 2026-09-30)

- System: Dell Tower Plus EBT2250, board 02D3NT, BIOS 1.19.0, service tag
  C4LBDB4.
- CPU: Intel Core Ultra 9 285 (24C/24T). GPU: RTX 5070 12 GB.
- Memory: 2 DIMM slots, firmware max 64 GB (SMBIOS MaxCapacityEx = 67108864 KB).
  DIMM1 = 1 x 32 GB SK hynix HMCG88AGBUA084N, DDR5-5600, 2Rx8, non-ECC,
  running 5600. DIMM2 EMPTY. Therefore single channel (64-bit, ~44.8 GB/s).
- OS view at capture: 31.46 GiB total visible, 9.18 GiB free.
- .wslconfig: [wsl2] memory=8GB, vmIdleTimeout=-1.
- BitLocker: NOT DETERMINED (Get-BitLockerVolume needs elevation). Check
  before opening the case.

## Measured blockers (evidence, not estimates)

- Gemma 4 26B-A4B UD-IQ2_M at 32k: candidates-20260929-v8. Host free RAM
  bottomed 2.65-2.94 GiB against the unchanged 3 GiB floor; the model consumes
  about 14.5 GiB regardless of offload (about 10 GB of it mmapped weights).
  Started v8 with 17.18 GiB available and still bottomed. Three resource stops
  (v6, v7, v8). Host RAM, not VRAM, not context.
- MiMo larger-output ledger: mimo-output-20260928-v1. Stopped at the RAM guard
  at 2.94 GiB.
- Strata / Qwen3.8-Flash-Next: staged, never run. Original builds need
  37.6-54.8 GB RAM+VRAM, i.e. roughly 26.6/28.2/36/43.8 GiB of host RAM once a
  12 GB card is accounted for. Out of reach at 32 GB; in reach at 64 GB except
  the 54.8 GB IQ3_S build, which stays borderline. The Coder pack is gated by
  the missing runner revision, not by RAM.
- Budget arithmetic from the same data: with 32 GB total, about 14.8 GiB is
  consumed by Windows + desktop + 8 GB WSL + harness before any model loads,
  leaving about 14 GiB usable for weights against the 3 GiB floor.

## Decision: upgrade, do not replace

- A used replacement at parity (DDR5 tower + 32 GB + an RTX 5070-class card at
  $646 used) lands at roughly $1,220-1,420, i.e. over the $1,000 budget and
  with no more RAM.
- 128 GB is unreachable at any price near budget: $1,464 used, $1,400-1,900
  new, up to $3,399 for fast kits. 96 GB used is already $1,070.
- Used DDR5 64 GB (2 x 32) is $590 on its own; a $1,000 machine cannot contain
  it and the rest of a usable platform.
- Platform change would also invalidate the pinned lab baseline (harness
  runners, llama.cpp b10883, Prism b10743, the 8 GB WSL cap, the 9/8/7.5 GiB
  gates, 120 protected files).

## Compatibility rules applied (hard constraints)

- Required: DDR5, UDIMM (unbuffered), NON-ECC, 288-pin, JEDEC 5600 preferred,
  32 GB per module.
- Rejected by inspection: DDR4 of any kind (notch/keyed differently);
  DDR5 RDIMM (keyed differently from UDIMM, HP Z4/Z6 G5 class); DDR5 SODIMM
  (laptops, Dell Micro/MFF, Lenovo Tiny, HP Mini); ECC UDIMM ("EC4" listings).
- Donors only work if they carry 32 GB (or 64 GB) modules; 4 x 16 GB donors
  yield 32 GB usable because this board has 2 slots.
- Checked and rejected as donors this session: ASUS ProArt X570-Creator /
  B550-Creator (2021, DDR4); HP Z2 Tower G5 / Z4 G4 / Z6 G4 (DDR4, Z4 G4 with
  Xeon W is DDR4-2933 ECC Registered); a specific HP Z4 G4 listing
  (Xeon W-2235, 32 GB, T400 2 GB) for the same reason plus a T400 that cannot
  meet the 7.5 GiB VRAM coding gate.
- Only HP workstation family that could donate: Z2 Tower G9 (2022, DDR5-4800
  UDIMM, ECC or non-ECC) - still a compromise (4800 bin, ECC risk).

## Pricing snapshot (2026-09-30, USD, shipped to 97018; Oregon has no sales tax)

New, correct spec (32 GB DDR5-5600 non-ECC UDIMM):
- $528.00 total: Newegg marketplace Crucial CT32G56C46U5, seller Infinite
  Energypmax ($498.01 + $29.99) - cheapest new verified in stock.
- $529.99 free shipping (Blazing Memory) / $529.98 (3C Expert), same listing.
- $565.61 free ground shipping: CompSource, Kingston KVR56U46BD8-32,
  domestic, lifetime warranty.
- $795: IT Creations, Kingston KVR56U46BD8-32-RETAIL.
- $499.99 Best Buy Crucial 32 GB - OUT OF STOCK.
- Wholesale spot reference: DDR5 UDIMM 32 GB 5600 = $310-320 (MemoryMarket,
  2026-09-29).

Used (eBay sold data):
- US median for used 32 GB DDR5: $325 (getpcparts, 2026-09-26).
- 1 x 32 GB DDR5: median EUR 290 over 303 sold listings / 90 days, typical
  EUR 261-322, cheapest delivered to the US about EUR 252; trending down about
  20% month over month and 42% below the September peak (pcprice.watch,
  2026-09-30).
- Used 64 GB = $590, 96 GB = $1,070, 128 GB = $1,464.

Whole-PC / NOS cannibalisation: no reliable edge in mainstream channels.
Dell Refurbished lists an OptiPlex 7010 Plus MT with only 16 GB at
$989-1,179 and shows whole categories out of stock; eBay bulk "up to 64 GB"
towers at $185-630 are DDR4 platforms. Arbitrage exists only in local,
mis-priced listings (Marketplace / Craigslist / surplus auctions), not as a
purchasable plan.

## Purchase (what was ordered)

- Kingston KVR56U46BD8-32, 32 GB (1 x 32 GB), DDR5-5600, 2Rx8, CL46, 1.1 V,
  non-ECC, 288-pin UDIMM.
- eBay item 800722063307, seller paymore_taylor (99.6%, 6.1K), used.
- $379.99, free shipping (USPS Ground Advantage), estimated Oct 2-6 to 97018.
- Returns accepted through 2026-11-04 -> validate before that date.
- Performance note: rank-matched 2Rx8 with the installed module, so no
  asymmetric-rank penalty. All candidate modules were JEDEC 5600 and this BIOS
  has no memory tuning, so there was no performance reason to prefer one over
  another; the tie-breaker was returns and delivery.

## Performance expectation

- Single DIMM -> two DIMMs: 64-bit to 128-bit, about 44.8 to about 89.6 GB/s
  at 5600. This is the whole upgrade and it is what matters for CPU-side MoE
  offload and CPU-resident models (see a3b-offload-20260924-v1, 33.90/32.72
  tok/s, bandwidth-bound).
- Rank interleaving (2Rx8 both channels) is a low single-digit effect.
- Watch for: BIOS reporting Memory Speed 4800/5200 after install, which would
  mean the pair fell to a common lower JEDEC bin (about 14% bandwidth loss).

## Install and verification plan

1. Check BitLocker first (elevated `manage-bde -status C:`); suspend protection
   if enabled, re-enable after.
2. Full shutdown, unplug, hold power ~10 s; remove the left-side cover; install
   the module into DIMM2 (Dell manual: DIMM1 + DIMM2 = dual channel); restore
   the upright position and cover.
3. First POST may take longer while the board retrains memory.
4. Verify after boot:
   - Win32_PhysicalMemory: two entries, 34359738368 bytes each, ConfiguredClockSpeed
     5600, FormFactor 8.
   - Win32_OperatingSystem: TotalVisibleMemorySize about 64 GB.
   - BIOS setup: Memory Installed 65536 MB, Memory Channel Mode = Dual,
     DIMM 1 Size / DIMM 2 Size = 32768 MB.
   Helper script already staged: C:/Users/kevin/AppData/Local/Temp/ram-precheck.ps1
   (read-only; safe to rerun).
5. Validate within the return window (through 2026-11-04): POST, Windows boot,
   and the first queued run acting as the load test. A full memory diagnostic
   (mdsched.exe) needs a reboot - Kevin's call, since the lab forbids
   unauthorised reboots.

## Lab-methodology obligations for the next session

- Record the platform change (32 GB -> 64 GB) in RESUME/REPORT headers. All
  gates stay UNCHANGED: initial physical >= 9 GiB, commit >= 8 GiB, coding VRAM
  >= 7.5 GiB, runtime floors 3/2/0.5 GiB, 6 GiB worker cap.
- Leave .wslconfig memory=8GB alone unless a deliberate re-baseline is wanted.
- Preserved RAM-guard-stopped evidence (candidates-20260929 v6/v7/v8,
  mimo-output-20260928-v1) remains constrained-platform evidence, not model
  verdicts.
- Re-runs need a NEW root: a STOP file blocks a root, and a failed attempt
  leaves source/relay_<model>.py that the next attempt asserts absent.
- Do not start inference on session open. The queued work still needs Kevin's
  explicit ready message plus a passing preflight.

## Source list

- Dell Tower Plus EBT2250 Owner's Manual (memory table; installing memory
  modules; system setup options).
- Live system queries: Win32_PhysicalMemory, Win32_PhysicalMemoryArray,
  Win32_BaseBoard, Win32_BIOS, Win32_OperatingSystem.
- getpcparts.com used RAM and GPU market pages (2026-09-26).
- pcprice.watch used RAM pages (2026-09-30).
- memorymarket.com UDIMM spot index (2026-09-29).
- Newegg product page N82E16820156311 and CompSource KVR56U46BD8-32 page
  (read 2026-09-30).
- pangoly.com product page for Crucial CT32G56C46U5 (store prices, 2026-09-30).
- eBay item pages for the four candidates (item specifics read 2026-09-30).
- thinkcomputers.org memory price surge article (2026-08-17); uk.pcmag.com RAM
  crisis guide (2026-05-24).
