# Withdrawn: the chunk ladder and the reserve are inside this pack's own noise: 2026-10-26

**Correction, same day.** Everything below the first table was measured first and then contradicted by its own repeats.
The repeat of an identical arm (`--vram-reserve-mib 900`, same config, same prompt) returned prefill **987.0** and
**122.6** tok/s - an **8.1x** spread with nothing changed - and across every arm run today the ranges are prefill
**122.6-987.0** (8.1x) and decode **4.1-23.1** (5.6x). Both claimed effects are smaller than that spread, so **neither
is established**:

- "chunk is flat" - the triple 704/717/720 was tight, but the *same* 4096 arm read **460.5** in the other pass. Not a
  result; a contiguous block that happened to be warm.
- "900 beats 2000" - the two identical 900 arms span the entire claim.

**Why the numbers move:** this configuration keeps only **2 GiB** of experts resident and reads the other **29.6 GiB**
unbuffered from the model files, so throughput follows the file cache and the disk, not the flag under test. The engine
log says it plainly: *"the file cache cannot keep them"*. A flag sweep on this pack measures the I/O state.

**What a stable measurement needs, before any of these flags is swept again:** a resident budget large enough that the
experts are not re-read (or a deliberate page-cache warm-up before the first arm), `n >= 3` **interleaved** arms rather
than sequential blocks, and the granted cache size recorded per arm - a `--expert-cache 3000` request was **granted
2,168** slots in the last arm, which is the declared-versus-granted problem for the third time in two days.

The tables below are kept as what was run, not as findings.


Two experiments from the untried list, run on the **staged 0.1.47** engine with the **q2_0** pack, one server per arm,
same prompts, seed 1234. No download, no bump.

## 1. Prompt chunk: flat on this card, and the 24 GB row does not transfer

19,769-token prompt, `--prefill CHUNK`, all three rungs measured with **10.3 GiB of VRAM free at start**:

| `--prefill` | prefill tok/s | decode tok/s | wall |
|---|---:|---:|---:|
| 4096 | 704.3 | 12.5 | 30.4 s |
| 8192 | 717.1 | 13.9 | 30.5 s |
| 16384 | 719.7 | 12.8 | 30.4 s |

On a 24 GB 5090 D the same flag gave **4.2x** prefill and 12.04 -> 18.89 decode. Here this triple looked flat, and
**that reading is withdrawn above** - the same 4096 arm read 460.5 in the other pass. What survives is only that a
19.8k prompt at 12 GB is nowhere near the 24 GB card's response to chunk size, which was already the vendor's claim for
this VRAM class.

**The first pass said the opposite, and it was contamination.** Same three rungs, but started with only **5.54 GiB VRAM
free**: 4096 read prefill 460.5 / decode **4.1**, 16384 read 702.9 / 12.9, and the 8192 arm **failed to serve at all**
(`expert cache auto: 0.00 GiB free -> 0 slots`, then `verify: needs the profile-filled VRAM expert tier`). The expert
cache is sized from free VRAM at start, so a rung measured in a different memory state is not the same experiment. The
harness now records `vram_free_mib_before` per row and waits for the previous engine to release both port and VRAM.

## 2. `--vram-reserve-mib`: 900 beats the config's 2000, at the same chunk

Matched pair at `--prefill auto`, everything else identical:

| reserve | expert-cache slots | prefill tok/s | decode tok/s | wall (19.8k prompt) |
|---|---:|---:|---:|---:|
| 2000 (the q2_0 config) | ~2,000 | 825.4 | 13.5 | 26.7 s |
| **900** | **3,049** | **984.4** | **16.6** | **22.4 s** |

**+19 % prefill, +23 % decode, -16 % wall** from handing the reserve to the expert cache. This is the same lever our
2026-10-20 ladder found from the cache side (capacity -> 83 tok/s at 5,376 MiB), now visible from the reserve side on an
engine that had not been measured this way. The shipped default in 0.2.3+ is **1536**, which sits between the two arms
here and is **unmeasured on this pack**; #3952 is the reason it exists at all (0.1.46 spends the reserve at long
context, 0.1.43.1 does not).

## 3. Two of my own bugs, recorded because they cost runs

- The first reserve arm was launched with `--prefill r900` - the harness used the *rung label* as the chunk value, so
  the engine refused to serve (`needs --spec T and --prefill CHUNK`). The label is now only a chunk when it is a number.
- A retry failed because the previous engine still held port 8091 and its VRAM; the harness now waits for the port to
  close (up to 120 s) and for >= 4 GiB free before starting, and skips a rung rather than measuring it in the wrong
  state.

## What this changes

- **Drop the chunk ladder from the queue** for this card; it is measured flat. The rung to keep watching is whatever the
  engine picks automatically, read back from the log.
- **`--vram-reserve-mib 900` is a candidate default** for this pack (one arm, matched, +19-23 %), pending a repeat and a
  1536 row.
- **Free VRAM at start is a declared variable** for every engine measurement from now on, beside page file, commit and
  the cache size itself.

Evidence: `ai_bench/chunk-ladder-20261026.json` (contaminated first pass), `-rep2.json` (the table above),
`reserve-900-20261026.json`, `reserve-2000-20261026.json`; engine logs under
`ai_bench/staged-strata-0.1.47/logs/chunk-*.log`.

## Addendum: the variable was the resident budget, and the engine said so

One more pair, `--resident-budget-gib 16`:

| resident asked | resident granted (log) | decode | prefill | file-cache line |
|---|---:|---:|---:|---|
| 2 GiB (the config) | **2.00 GiB** | 4.1-23.1 | 122.6-987.0 | *"the file cache **cannot** keep them"* |
| 16 GiB | **10.09 GiB, page-locked** | **87.0** | 493.8 | *"the file cache **can** keep them"* |

That is a **4-8x decode difference from the resident budget**, and it explains the whole spread above: the arms were not
measuring chunk size or reserve, they were measuring how much of the 29.6 GiB expert set happened to be resident or in
the file cache. The engine prints the verdict in one line - `the file cache can keep them` versus `cannot` - which is the
covariate to record per arm from now on, beside `resident RAM mode: N GiB` and the granted cache slots.

The second 16 GiB arm **failed to start** for the same reason as the earlier 8192 failure: the previous engine's RAM was
still committed (`Windows commit: 13.6 GiB left`, then `expert cache auto: ... -> 0 slots`, then `verify` refused). So
sequential arms on this pack contaminate each other through **RAM and commit**, not only through VRAM and the port.

**To establish any of this:** n >= 3 arms **interleaved** (2, 16, 2, 16, 2, 16) with a cooldown long enough that
`Windows commit` returns to its starting value, recording per arm the granted resident GiB, the granted cache slots and
the `file cache can keep them` line. The 87 tok/s row is a single arm and is **not** a result yet - it is the reason to
run that experiment.

## Correction 2, 2026-10-27: it was not noise - the ladder measured one arm three times

`NEWS-2026-10-27.md` §2.1 (#4261) says the prompt chunk is capped by expert-cache slots **and that the engine prints the
clamp**. The stored logs from yesterday answer it without starting an engine:

```
chunk-8192.log   : strata serve: prompt chunk 8192 -> 4096 tokens so its buffers fit in every expert cache
chunk-16384.log  : strata serve: prompt chunk 16384 -> 4096 tokens so its buffers fit in every expert cache
chunk-4096.log   : (no clamp line)
```

**8192 and 16384 were both executed at 4096.** The "flat triple" was not noise and not a near-miss: it was the same arm
three times, which is why it was flat to within 2 %. The withdrawal above stands, but its stated reason was wrong.

The second log line names the variance instead:

```
strata generate: WARNING: a prompt chunk of N tokens lends S cache slots to the prompt path, but only 0 of their experts
fit in RAM: the others are read from the SSD on every chunk, and prompts can read ~3x slower than with --prefill auto
(#669). A larger --resident-budget-gib ... keeps them all in RAM
```

Every arm had **0 experts of the lend region in RAM**, and the lend region itself moved (2,468 slots in r900a against
717 in r900b) - which is exactly the 987.0-vs-122.6 repeat, and matches the engine's own "~3x slower" warning. So:

- **the chunk effect is unmeasured**, because asking for more chunk than the cache can lend is silently rounded down;
- **the reserve effect is unmeasured**, because the arm is dominated by whether the lend region fits in RAM;
- the engine names both fixes: a larger `--resident-budget-gib`, or `STRATA_STAGE_TRIM=1` (the reporter's box: VRAM free
  for the cache 3.00 -> 5.54 GiB, slots 1,128 -> 2,115, chunk 5,376 -> 8,192).

**What any re-run must read back per arm, from the log:** the clamp line (`prompt chunk N -> M`), the lend-region line
(`lends S slots ... only R fit in RAM`), granted resident GiB, granted cache slots, and the reserve as the engine reports
it - #4134 says the engine sometimes ignores `--vram-reserve-mib`, and that `session state allocation failed` is a start
failure rather than a VRAM shortage.

## Addendum 2, 2026-10-27: the ten void arms, tabulated from their own logs, and the gate that stops the next ones

No engine was started for this section. The table below is read from the ten stored logs under
`ai_bench/staged-strata-0.1.47/logs/chunk-*.log` by one command, which is now part of the harness rather than a
throwaway grep:

```
cd C:\Users\kevin\ai_bench\staged-strata-0.1.47\control
.\python\python.exe chunk_ladder.py --forensics --forensics-json <each ai_bench result json> --out table.md
```

It reads the same lines every future arm must read back: the clamp (`prompt chunk N -> M tokens so its buffers fit`,
#4261), the lend region (`lends S cache slots ... only R of their experts fit in RAM`, #669), the auto sizing line
(`expert cache auto: X GiB free -> N slots`), the granted cache (`expert cache N slots`), the granted resident budget
(`resident RAM mode: N GiB`), the file-tier verdict (`the file cache can/cannot keep them`) and `Windows commit:`.
Throughput columns are joined in from the stored result JSONs by log name, so a row shows what was measured beside what
was granted.

| log | chunk asked -> ran | lend slots (in RAM) | cache auto -> granted | reserve MiB | resident GiB | file tier | commit GiB left | prefill tok/s | decode tok/s | gate |
|---|---|---|---|---|---|---|---|---|---|---|
| chunk-4096.log | 4096 -> 4096 | 1373 (0) | 2731 -> 1971 | 2000 | 2.00 | unbuffered | 8.7 | 460.5 | 4.1 | VOID: lend 0/1373 in RAM, file tier unbuffered |
| chunk-8192.log | 8192 -> **4096** | 1373 (0) | 2731 -> 1937 | 2000 | 2.00 | unbuffered | 8.9 | 717.1 | 13.9 | VOID: clamped 8192 -> 4096; lend 0/1373 |
| chunk-16384.log | 16384 -> **4096** | 1373 (0) | 2731 -> 1919 | 2000 | 2.00 | unbuffered | 8.8 | 702.9 | 12.9 | VOID: clamped 16384 -> 4096; lend 0/1373 |
| chunk-default2000.log | auto -> 5120 | 1665 (0) | 2731 -> 1982 | 2000 | 2.00 | unbuffered | 8.4 | 825.4 | 13.5 | VOID: lend 0/1665 |
| chunk-fixed2000.log | auto -> 5632 | 1811 (0) | 2731 -> 2168 | 2000 | 2.00 | through the file cache | 8.7 | 438.7 | **23.1** | ok (lend 0, page-cached) |
| chunk-r900.log | auto -> 8192 | 2541 (0) | 3565 -> 3049 | 900 | 2.00 | unbuffered | 7.5 | 984.4 | 16.6 | VOID: lend 0/2541 |
| chunk-r900a.log | auto -> 7936 | 2468 (0) | 3565 -> 2907 | 900 | 2.00 | unbuffered | 7.6 | 987.0 | 16.4 | VOID: lend 0/2468 |
| chunk-r900b.log | auto -> 1792 | 717 (0) | 862 -> 862 | 900 | 2.00 | unbuffered | 10.0 | 122.6 | 7.6 | VOID: lend 0/717 |
| chunk-res16a.log | auto -> 5632 | 1811 (0) | 2731 -> 2168 | 2000 | **10.09** | through the file cache | 4.3 | 493.8 | **87.0** | ok (lend 0, page-cached) |
| chunk-res16b.log | auto -> none | none | 862 -> **0** | 2000 | none | through the file cache | 13.6 | - | - | VOID: start failure, 0 slots |

Shrink witness, where the granted slots are below the auto sizing (the engine's own line):
`only 97 MiB free once the slots are written (reserve 900 MiB); shrinking the expert cache` (r900a), `1322 MiB` at
reserve 2000 (fixed2000/res16a), `284 MiB` (r900). The auto line is a sizing *proposal*; `expert cache N slots` is the
grant.

### What the table settles, row by row

- **The "flat triple" was 4096, 4096, 4096 - and the third rung was not even the same arm.** 8192 and 16384 both ran at
  4096; the 4096 arm ran as asked. Correction 2 is confirmed mechanically, not by memory.
- **Every one of the ten arms had 0 experts of the lend region in RAM** - 717 to 2,541 slots lent, none resident. At the
  config's 2 GiB the lend region loses every time, because `--resident-budget-gib` fills the ranked experts first and the
  lend region comes after (the engine says so in the warning's own last clause).
- **The reserve was honoured in every arm.** 900 MiB reserved at r900/r900a/r900b, 2000 MiB at the rest: #4134's
  "sometimes ignored" did not bite yesterday on this engine, and the readback that proves it is one regex on the same
  line. It is now a gate rule anyway, because a reserve arm whose reserve was ignored is not a reserve arm.
- **`--expert-cache auto` was never a "declared 3,000": the sizing proposal moved 862-3,565 slots and the grant 862-3,049,
  and the difference is the reserve, not the cache.** The lend region tracks the grant almost exactly (3049 -> 2,541,
  2,907 -> 2,468, 2,168 -> 1,811, 862 -> 717), which is the #4261 mechanism in our own logs: the chunk a prompt may
  borrow is the cache, so the reserve decides the chunk, and the chunk decides the prompt read.
- **The file-tier verdict, not the flags, separates the fast rows from the slow ones.** The two arms the engine recorded as
  *"reads through the file cache"* are the only two with decode above 20 tok/s (23.1 and 87.0); all eight *"unbuffered"*
  arms are 4.1-16.6. This is the covariate the withdrawal named, and it now has a column.
- **Correction to the earlier addendum: the failed 16 GiB repeat was VRAM at the sizing step, not the commit.** res16a and
  res16b started with **11,126** and **10,995 MiB** free by `nvidia-smi` (131 MiB apart) and the engine then found
  **5.54 GiB** and **1.28 GiB** free after its own loads; the arm with **more** commit free (13.6 GiB left) is the one that
  sized `-> 0 slots`. So `nvidia-smi` free before a start does not predict what the engine sees, and a 0-slot start is a
  start failure to re-run (#4134's reading), not a measurement. The commit cooldown is still implemented, because the
  successful 16 GiB arm **ended at 4.3 GiB of a 68.1 GiB limit** and the engine warned its exit code `0xC0000409` mode
  (#1607) - host commit is a real covariate for a page-locked 10 GiB arm, just not the cause of that particular failure.

### The harness now refuses to record a void arm as a result

`ai_bench/staged-strata-0.1.47/control/chunk_ladder.py` (one file, stdlib only; the staged interpreter runs it). After
each arm it re-reads that arm's log and marks the arm **VOID** when any of these holds, with the reason text stored:

1. **the request did not run**: a clamp line whose target differs from a declared `--prefill`, or a granted chunk
   (`prompt chunk auto: N`) that differs from it;
2. **the lend region had 0 experts in RAM and the file tier was unbuffered** - the #669 condition, i.e. the arm measured
   the disk. 0 in RAM with *"the file cache can keep them"* is recorded as a warning, not a void, because the engine emits
   the #669 warning **before** it builds the RAM copy (logs/chunk-res16a.log fires it at 10.09 GiB resident while the page
   cache covers the set); both lines are in every arm's JSON so the distinction is auditable, not asserted;
3. **the granted cache slots differ from a declared `--expert-cache`** (the "granted 2,168 of 3,000" failure, now a hard
   gate);
4. **the engine ran a reserve other than the declared `--vram-reserve-mib`** (#4134), and a start failure
   (`session state allocation failed`, `needs the profile-filled VRAM expert tier`, `-> 0 slots`) is always a void.

A void arm keeps `"result": null`, its reasons, and its readback; it is re-queued behind the other arms up to
`--max-retries` (default 2) instead of being reported; the aggregate JSON separates `results` from `void`. Every attempt
writes its own file, so a re-run never overwrites the arm it replaced. Also added: a **commit cooldown** before every
start (`Get-CimInstance Win32_OperatingSystem` -> `TotalVirtualMemorySize` / `FreeVirtualMemory`, held until free commit
is back to its pre-run value, up to `--cooldown-s`, default 300 s), the port rotating 8091/8092/8093 so a dying engine
cannot shadow the next start, and the per-arm declaration read from the engine's **own argv echo** rather than from the
harness's intent.

Its own checks, run today, start no engine: `--forensics` reproduces the table above from the stored logs, and the gate
was exercised on synthetic readbacks (declared cache 3,000 granted 2,907 -> void; reserve 1,536 run at 900 -> void;
`--prefill 8192` clamped to 4096 -> void; 0 slots -> void; 0-lend page-cached -> ok with warning).

### The re-run design, written down and not started

`chunk_ladder.py --plan phase2`. Thirteen arms, **interleaved 2, 16, 2, 16 ...** so no resident budget is measured
twice in a row, every arm declaring a fixed `--expert-cache` and its own `--vram-reserve-mib` so ambient VRAM cannot
choose the arm, and each start behind the commit cooldown. **The cache column below (3000) is superseded**: no arm we
hold was ever granted 3000, so the declared value now comes from the two-arm pre-flight described in the revision at the
end of this note, per reserve, and `--plan phase2` refuses to run without it.

| # | arm | prefill | reserve MiB | resident GiB | cache | env |
|---|---|---|---:|---:|---:|---|
| 1 | `p4096-r900-res2` | 4096 | 900 | 2 | pre-flight | |
| 2 | `p4096-r900-res16` | 4096 | 900 | 16 | pre-flight | |
| 3 | `p4096-r1536-res2` | 4096 | 1536 | 2 | pre-flight | |
| 4 | `p4096-r1536-res16` | 4096 | 1536 | 16 | pre-flight | |
| 5 | `p4096-r2000-res2` | 4096 | 2000 | 2 | pre-flight | |
| 6 | `p4096-r2000-res16` | 4096 | 2000 | 16 | pre-flight | |
| 7 | `pauto-r900-res2` | auto | 900 | 2 | pre-flight | |
| 8 | `pauto-r900-res16` | auto | 900 | 16 | pre-flight | |
| 9 | `pauto-r1536-res2` | auto | 1536 | 2 | pre-flight | |
| 10 | `pauto-r1536-res16` | auto | 1536 | 16 | pre-flight | |
| 11 | `pauto-r2000-res2` | auto | 2000 | 2 | pre-flight | |
| 12 | `pauto-r2000-res16` | auto | 2000 | 16 | pre-flight | |
| 13 | `p4096-r1536-res16-trim1` | 4096 | 1536 | 16 | pre-flight | `STRATA_STAGE_TRIM=1` |

Artifacts, per arm and per attempt: `ai_bench/chunk-reserve-20261027/<arm>-a<attempt>.json` (declaration, the engine's
own lines, timings, void verdict), the engine log `ai_bench/staged-strata-0.1.47/logs/chunk-<arm>.log`, and the aggregate
`ai_bench/chunk-ladder-20261027.json`. Expected: the six 2 GiB rows are **expected to be VOID on rule 2** (at 2 GiB the
lend region has never had an expert in RAM - 0 of 717-2,541 slots in ten of ten stored arms - and the file tier has read
unbuffered in 8 of 10), and that is the **result of the 2 GiB half**, not a failed run: on this pack at the config's
resident budget a prompt-chunk measurement cannot exist, because every number there is a disk number. Those arms are
reported as void, with one of them carrying its #669 line verbatim, and the half is not re-run hoping for a different
verdict. The 16 GiB rows are the ones that can be results, and they are where 900 vs 1536 vs 2000 is measurable, because
the reserve moves the cache (3,565 vs ~2,731 slots when auto) with the page cache holding the set. Arm 13 is the
reporter's trim on a **single** card, quoted against arm 4: it must move VRAM-free, granted slots and the chunk, or it
says the split report does not transfer. A cell whose declared cache is still granted short after two attempts is
re-run with `cache=auto` under a `-cacheauto` label and the change is reported - the arm is relabelled rather than the
gate relaxed.

**Status: written, checked, not started.** Phase 2 needs the GPU, which the image track holds; it begins only on the
coordinator's handoff, and no engine, model or GPU workload was started today.

### Revision, 2026-10-27 (before any engine start): the declared cache comes from a pre-flight, and the 2 GiB half is a finding

Reviewing Addendum 2 turned up a defect in **my own plan**, not in the gate: `--expert-cache 3000` was never granted in
any arm we hold. The grants were 1,971 / 1,937 / 1,919 / 1,982 / 2,168 / 3,049 / 2,907 / 862 slots, and the engine's own
shrink line (`only N MiB free once the slots are written (reserve M MiB); shrinking the expert cache`) says why - it
sizes the cache, then shrinks it to honour the reserve. Rule (c) is right; the plan was wrong, and as written it would
have voided most of the sweep on a declaration the card cannot grant.

- **Two-arm pre-flight first** (`--plan preflight`, ~5 min): one start at `--vram-reserve-mib 2000` and one at `900`,
  both `--expert-cache 3000`, resident 2 GiB, `--prefill 4096`. Read the granted `expert cache N slots` off each log.
  Result: `ai_bench/chunk-reserve-20261027-preflight.json`.
- **The design's declared cache is then derived from those grants, not chosen by hand**:
  `--plan phase2 --cache-preflight <preflight.json>`, whose default mode is `per-reserve` - each reserve declares the
  smallest grant seen at that reserve, and a reserve the pre-flight did not probe (1536 sits between the two it does)
  inherits the smallest grant of all, because a cache that fits behind the heavier reserve fits behind a lighter one.
  `--cache-mode single` declares one value everywhere. The policy, the observed grants and the inherited value are
  written into the aggregate JSON under `cache_policy`, so the declaration is auditable after the fact.
- **The 2 GiB half is a finding, not a failed run.** If all six 2 GiB arms come back VOID on rule (b), that *is* the
  answer: at the pack's 2 GiB resident budget a prompt-chunk measurement cannot exist on this card, because the lend
  region is empty (0 of 717-2,541 slots in RAM in ten of ten stored arms) and the file tier is unbuffered, so any number
  measured there is a disk number. Those arms are reported as the result of the 2 GiB half, one of them with its #669
  line quoted verbatim, and the run is not repeated hoping for a different verdict.
- **The evidence travels in the JSON, not in prose.** Every row - result or void - now carries the engine's own lines:
  `chunk_asked` / `chunk_granted` / `clamp_line`, `lend_slots` / `lend_in_ram` / `lend_line` (verbatim),
  `cache_auto_slots` / `cache_granted_slots` / `cache_shrunk`, `reserve_used_mib`, `resident_granted_gib`,
  `file_tier` / `file_cache_line`, `commit_left_gib`, `vram_free_end_mib`. That is what a reviewer re-derives the verdict
  from, and it is why the 2026-10-26 withdrawal could be settled a day later without starting an engine.

Still **not started**: both `--plan preflight` and `--plan phase2` wait for the coordinator's GPU handoff, and the
phase-2 command is refused without a pre-flight JSON.
