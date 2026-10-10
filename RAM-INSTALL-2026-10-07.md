# RAM install and resume sheet, 2026-10-07

STATUS 2026-10-07: EXECUTED. The module is installed, trained at 5600, and dual
channel is active (63.46 GiB visible, 71.4 GB/s memcpy traffic). Part 3 is
satisfied - the evidence is in local-llm-lab/RAM-VERIFY-2026-10-07.md. Parts 1-2
and Part 3's pre-install state describe the pre-boot situation; Part 4's resume
queue and Part 5's open decisions are still current.

Read this with the PC off, or print it before shutting down. It is the whole
procedure: what to do before shutdown, how to install the module, how to verify
after boot, and how to resume the lab. The background, option analysis and the
purchase record are in RAM-UPGRADE-2026-09-30.md; this file is the action sheet.

Machine: Dell Tower Plus EBT2250, service tag C4LBDB4, Intel Core Ultra 9 285,
RTX 5070 12 GB, Windows 11 (10.0.26200). Owner: Kevin.

## Part 0 - state at handoff (2026-10-07, verified live)

- Memory: DIMM1 only, 32 GB SK hynix HMCG88AGBUA084N, DDR5-5600, 2Rx8, non-ECC.
  DIMM2 EMPTY. 31.46 GiB visible. Single channel (~44.8 GB/s).
- No RUNNING.lock in any ai_bench root; no benchmark is running.
- The detached Strata service (qwen3.8-flash-next-coder-iq1_m on 127.0.0.1:8080)
  is running now. It dies with the machine. It is NOT in startup - the only
  inference startup entry is Ollama - so nothing will relaunch it after boot.
  Nothing needs to be stopped by hand; a normal shutdown is enough.
- BitLocker: still UNDETERMINED. `manage-bde -status` is denied without
  elevation. Check this before opening the case (Part 1).
- Free physical RAM at the check was 11.12 GiB; GPU free 957 MiB (Strata held the
  card). Both are irrelevant once the machine is off.

## Part 1 - before opening the case

1. Check BitLocker from an elevated prompt:
   `manage-bde -status C:`
   If "Protection Status: Protection On", suspend it for the next reboot so the
   changed hardware does not trigger a recovery prompt:
   `manage-bde -protectors -disable C: -rebootcount 1`
   then re-enable after the boot (`manage-bde -protectors -enable C:`).
   If BitLocker is Off, do nothing.
2. Save any open work. Normal Windows shutdown from the Start menu.
3. Unplug the power cable, then hold the power button about 10 seconds to drain.
4. Work on a hard surface; touch a bare metal part of the case to discharge
   static before handling the module. Hold the module by its edges.

## Part 2 - install

- Module: Kingston KVR56U46BD8-32, 32 GB (1 x 32 GB), DDR5-5600, 2Rx8, CL46,
  1.1 V, non-ECC, 288-pin UDIMM. eBay item 800722063307, $379.99.
- Slot: DIMM2. Dell's manual for this chassis gives dual channel from DIMM1 +
  DIMM2. Do not move the existing DIMM1 module.
- Remove the left-side cover, open the DIMM slot's retention clips, seat the
  module until both clips click, refit the cover, reconnect power.
- First POST may take noticeably longer than usual while the board trains the
  memory. Let it finish; do not power-cycle mid-training.
- Returns are accepted through 2026-11-04. Validate before that date.

## Part 3 - verify after boot

Run these (PowerShell, normal window):

```
Get-CimInstance Win32_PhysicalMemory |
  Format-Table DeviceLocator,Capacity,Speed,ConfiguredClockSpeed,PartNumber -Auto

Get-CimInstance Win32_OperatingSystem |
  Select-Object @{n='TotalVisibleGB';e={[math]::Round($_.TotalVisibleMemorySize/1MB,2)}}

Get-CimInstance Win32_ComputerSystem |
  Select-Object @{n='TotalGB';e={[math]::Round($_.TotalPhysicalMemory/1GB,2)}}
```

Expected:

- Two entries in Win32_PhysicalMemory: DIMM1 and DIMM2, Capacity 34359738368
  each, ConfiguredClockSpeed 5600.
- TotalVisibleGB about 63.8-64; TotalGB 64.
- In BIOS setup: Memory Installed 65536 MB, Memory Channel Mode = Dual,
  DIMM 1 Size / DIMM 2 Size = 32768 MB.

If the speed reads 4800 or 5200, the pair has fallen to a common lower JEDEC
bin (about 14% bandwidth loss). Note it in the report; do not change BIOS memory
settings, there is nothing to tune on this board.

A read-only helper was staged earlier at
C:/Users/kevin/AppData/Local/Temp/ram-precheck.ps1 (Temp may be cleaned; the
commands above are equivalent if it is gone).

Optional but recommended inside the return window: run the first queued lab run
as the real load test. A full memory diagnostic (mdsched.exe) needs its own
reboot - Kevin's call, since the lab forbids unplanned reboots.

## Part 4 - resume the lab after the boot

Rules that do not change:

- Every resource gate stays UNCHANGED: initial physical >= 9 GiB, commit >= 8 GiB,
  coding VRAM >= 7.5 GiB, runtime floors 3/2/0.5 GiB, 6 GiB worker-private cap.
  The upgrade removes the RAM constraint; it is not a licence to lower or raise
  gates.
- Keep .wslconfig memory=8GB as it is.
- Record the 32 -> 64 GB platform change in the next RESUME/REPORT header.
- Use a NEW root for any re-run. A STOP file blocks a root, and a failed attempt
  leaves source/relay_<model>.py that the next attempt asserts absent.
- Do not start inference merely because a session opened; Kevin's ready message
  plus a passing preflight still gate every run.
- Existing RAM-guard-stopped evidence (candidates-20260929 v6/v7/v8,
  mimo-output-20260928-v1, and the Strata guard-stop probe folders) stays
  constrained-platform evidence, not a model verdict.

Then, in order:

1. `python C:/Users/kevin/ai_bench/decisions-20261005-v1/run.py preflight`
   (its own guard also refuses to start while another engine is resident).
2. Finish the decision track in a new root: screen the models that were blocked or
   inconclusive. Current results to beat, from decisions-20261005-v2 and -v3:
   julia-1 11/18 (1/4 stalls, 4/14 false alarms, p95 638 ms), kev4 14/18 (0/4
   caught, 0/14 false alarms, p95 430 ms, never crosses 0.85), nimble 15/18 (2/4
   caught, 1/14 false alarms, p95 596 ms, 6.94 GiB private under the amended
   8.0 GiB cap). CORRECTION: nimble is NOT blocked and the cap is NOT open - Kevin
   authorized the 8.0 GiB declaration on 2026-10-05 and decisions-20261005-v3
   executed it. What was left after that: laya, kev0 and lev had never been
   screened on this endpoint; decisions-20261007-v1 now scores all three (laya
   14/18 0/4 0/14 p95 183 ms; kev0 14/18 0/4 0/14 p95 169 ms; lev 14/18 1/4 1/14
   p95 345 ms, the only one of the three whose p crosses 0.85, and the endpoint is
   deterministic over two full passes). Ranking these needs the published suite,
   not 18 windows.
3. Re-run the Strata ledger screen in a new root with a larger resident budget
   and a longer declared wall. EXECUTED 2026-10-07 (`strata-20261007-v1`, budget
   4 -> 24 GiB, ledger wall 720 -> 3600 s; repeat in `strata-20261007-v2`).
   CORRECTION: it was NOT wall-bound. With the wall raised, run 1 still scored
   7/70 in 79 s, stopping by itself after 3 turns with an empty final message,
   while the byte-identical repeat scored 70/70 clean in 289.5 s. Decode went
   6.5-9.6 -> ~46-49 tok/s (5-7x). Budget 24 is not free RAM: min free physical
   4.33-5.10 GiB (floor 3), min GPU free 0.79-0.87 GiB (floor 0.5). Report Strata
   screens as a rate over runs.
4. Gemma 4 26B-A4B (UD-IQ2_M or a smaller build) - previously stopped three
   times on host RAM at ~14.5 GiB resident. EXECUTED 2026-10-07: it runs now.
   `candidates-20261007-v1` produced unscored zeros from a runner defect (a new
   candidates root must carry source/staged_tasks_20260922.py and siblings next
   to the generated relay, or every task returns abnormal_evaluator_exit 2);
   re-scoring its preserved artifacts gives events 76/76, ledger 66/70, paths
   75/75. `candidates-20261007-v2` carries the fix and is runner-scored: events
   75/76, ledger 69/70 (wall-cut at 673 s), paths not run after the
   quota_unknown guard. Min free physical 28.5-31.0 GiB vs 2.65-2.94 at 32 GB.
5. Optional: move the coding screen onto llama.cpp b11461 (DFlash2/MTP
   speculative decoding, CUDA W4A4 NVFP4). Our frozen roots keep b10883.

## Part 5 - open decisions that are not mine to take

- The 6 GiB worker-private cap that stopped nimble: DECIDED AND EXECUTED, not open.
  Kevin authorized an 8.0 GiB declaration for the GPU systemone track on 2026-10-05 and
  decisions-20261005-v3 ran nimble under it (15/18, 2/4 stalls caught, 1/14 false alarms,
  p95 596 ms, peak private 6.94 GiB). The 6 GiB value stays attached to the roots that
  declare it (decisions-20261005-v1/-v2); decisions-20261005-v3 and the bespoke suite
  roots declare 8.0 GiB. No further cap change is proposed.
- Reporting scored screens as a rate over n runs against an explicit floor,
  instead of a single run. The MiniCPM paths outlier (75/75, 75/75, 9/75 under
  identical declared settings) is the motivating evidence.

## Part 6 - corrections and deltas since 2026-10-05

- CORRECTION, Strata sampling: the live endpoint DOES honour per-request
  sampling. An earlier probe claimed otherwise; it was invalid because it
  compared `choices[0].message.content` alone, and this reasoning model puts
  every token in `reasoning_content` at low max_tokens, so all cases compared
  the empty string. The valid probe (hashing reasoning_content + content) shows
  6/6 distinct traces; temperature, seed, top_k and top_p each change the output.
  Full write-up: ai_bench/staged-strata-20261005/SAMPLING-PROBE-NOTES.md.
- Two behaviours to carry forward: `temperature: 0` is NOT seed-stable on this
  engine (do not assume greedy determinism), and a trivial prompt at
  `max_tokens: 200` still ends `finish_reason: length` with zero visible content,
  so any screen through this engine needs a large output budget.
- The queue staged on 2026-10-05 was executed by later sessions: decisions-20261005-v2
  and -v3, bespoke-suite-20261005-v1, strata-20261005-v1. Nothing from that plan
  is still outstanding except the deferred items in Part 4.
- Newer upstream than our pins: llama.cpp b11461 (we staged b11429); Strata
  v0.1.40 and v0.1.40.1 (we ran v0.1.39). v0.1.40's Windows fixes concern the
  RAM budget and the large-page arena; NVIDIA decode is within about 3% of
  0.1.39, so it does not by itself fix the disk-bound ledger.
- New in the field, worth a look later, not now: OpenAI's hosted Decisions API
  with the `llm-openai-decisions` plugin (a hosted reference point for our local
  decision models), Ollaya (a local decision app allowing up to 255 options
  against Ollama's 15), vLLM's 2026-10-05 serving release, and Aleph Alpha's
  Kolibri-1 (78.1B MoE, Apache-2.0).

## Part 7 - where the notes live

- C:/Users/kevin/local-llm-lab/AGENTS.md - the running lab changelog (newest first).
- C:/Users/kevin/ai_bench/CONTINUE-HERE.md - the handoff index.
- C:/Users/kevin/local-llm-lab/NEWS-2026-10-05.md - the news scan.
- C:/Users/kevin/local-llm-lab/STAGING-2026-10-05.md - the decision/Strata staging.
- C:/Users/kevin/ai_bench/decisions-20261005-v1/RESUME.md - the decision runner.
- C:/Users/kevin/ai_bench/strata-20261005-v1/RESUME.md - the Strata run.
- C:/Users/kevin/ai_bench/bespoke-suite-20261005-v1/REPORT.md - the 3,880-decision suite.
