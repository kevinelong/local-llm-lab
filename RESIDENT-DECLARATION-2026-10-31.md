# The resident budget is a clamp, not a lever: what every future row must declare

2026-10-31. Read-only re-read of the 32 arm JSONs in `ai_bench/chunk-reserve-20261027` plus their engine logs, and the
statement the scan (`NEWS-2026-10-31.md`) asked for. No model was loaded to write this; the run it describes is
separate and is recorded below once it finishes.

## 1. The engine prints its own clamp, and it is arithmetic

Every Strata 0.1.47 log carries one line:

    FileExpertSource: --resident-budget-gib 16.00 exceeds available commit (12.90 GiB minus 4 GiB headroom and a
    0.25 GiB margin): 8.65 GiB

So, for a declared value above what the host can carry:

    granted_resident = engine_available_commit - 4.25 GiB

and `engine_available_commit = script_commit_free_before - process_commit_at_that_moment`. Verified on all **18** arms
declared at 16 GiB: `granted == engine_avail - 4.25` in 18 of 18, and **18 of 18 were clamped**. The process had already
committed **10.48 GiB mean** (9.39-13.60, n=18) when the resident allocation was attempted.

Consequences, and they are the reason the 2026-10-27 ladder cannot be read as a resident curve:

* `--resident-budget-gib 16` granted **5.29 / 7.75 mean / 10.18 GiB, spread 4.89** across 18 arms. What varied was
  ambient commit headroom at each start, never the flag.
* Declared `2` granted **2.00 GiB in every arm**. The flag binds exactly where it is smaller than the clamp.
* Granted resident correlates with free commit at start (**r = +0.82**), with prompt rate (**r = +0.52**) and, in that
  set, with decode rate **not at all (r = +0.02)**. That last number is a property of the set, not of the mechanism:
  it spans only **5.29-10.18 GiB** and every arm carried **cache 3000**. Section 5 shows what decode does when the span
  is wider and the cache is halved.
* The engine reports `resident_pinned: true` in every clamped arm. That is **not** #4808's failure mode: #4808 ends in
  *pageable* memory, ours ends in a smaller page-locked block. Same silent direction, different mechanism, and #4808
  alone does not explain our gap.

## 2. What a row must carry from now on

Per arm, non-optional:

1. `commit_free_gib_before` (the runner's own pre-start reading) and the engine's `engine_available_commit` line.
2. `resident_granted_gib` and `resident_pinned` - never the declared value alone.
3. `cache_granted_gib`, `cache_granted_slots`, `chunk_granted`, `reserve_used_mib`.
4. `draft_accepted` **and** drafts offered, plus `completion_tokens`; the answer text, not just a rate.
5. >= 5 replicates per cell before any decode comparison, or the cell is a single observation and is labelled so.
6. Prefill, reserve, cache and chunk held at one value while resident moves; declared resident above ~10 GiB is not a
   control and must not be printed as one.

The decode noise floor our own replicates measured at *fixed* flags: **78.3-99.1 tok/s (26 %)** and **72.1-86.3
(20 %)**, with greedy text identical in **10 of 10** runs. So on this build and pack:

* the expert-cache non-determinism the 0.2.9 notes name (five answers from five identical requests) is **not** visible
  at this scale here - do not claim it;
* Strata #4778's acceptance margins (70-75 % vs 79-81 %) and its "+1 % for 0.1.55" cannot be resolved at n=2 on one
  card, which is what the scan already concluded from the issue;
* the 2026-10-08 MTP row (+31.2 % per token, -7.3 % wall, +21.7 % tokens) is a **speed-and-letters** result, not a
  determinism result.

## 3. The declaration for the ladder that answers the open question

With the clamp known, the ladder's only readable form is **inside the binding range**, so 2026-10-31 uses
`resident = 2 / 4 / 6 / 8` with `prefill=4096`, `reserve=900`, `cache=1500`, `STRATA_LOOKAHEAD=0`, 3 replicates each,
interleaved so drift cannot pick a rung.

Why `cache=1500`: the card had 9,172 MiB free (2,772 MiB held by desktop apps) against the 10,799 MiB the 2026-10-27
arms started from. Slots cost 1.317 MiB each on this pack (3,000 slots = 3,952 MiB), so 1,500 slots is ~1,976 MiB and
leaves the engine ~8.2 GiB and ~1 GiB above the 900 MiB reserve. A cache declared over what the card grants is a cell
that the harness itself voids, and the pre-flight already measured that 3,000 slots was never granted at reserve 2000.

The cell is comparable **within today's set** and not to the 2026-10-27 rungs: the cache and the chunk both moved.

## 4. What this closes and what it does not

* Closes the scan's shortlist item 4: the shape of our declared-vs-granted gap is now named, measured and reproduced.
* Does not test #4811's `--vram-reserve-mib 1536` claim (a bigger cache from a *larger* reserve on a 20 GB card). That
  needs a reserve sweep at one resident value, and it must be run when the card is emptier than today's 9,172 MiB.
* Does not test 0.2.9 / engine 0.1.55, and must not be read as one.
* **The scan's shortlist item 5 is not answerable from the source we hold.** The staged tree
  `ai_bench/staged-strata-20261007/engine-src-v0.1.40.3` (git `d5ea713`, tag "Version 0.1.40.3") contains **no
  `nv_defaults` file, no speed table and no `sm_121` anywhere** - the auto-table branch #4778 quotes arrived after
  0.1.40.3, so a checkout at 0.1.55 is required before anyone can say whether an sm_120 card reads one of its tables.
  What that tree does show is the architecture policy behind #4662: `src/core/device_main.cpp` keeps the run-time half
  of the sm_120 rule - *"CMake refuses to COMPILE for another architecture, and this refuses to RUN on one"* - which is
  the mechanism that produced "unspecified launch failure" on a mismatched engine.

## 5. The 2026-10-31 run: void as a declared sweep, usable as a granted curve

24 starts (`ai_bench/resident-ladder-20261031.json`, arms in `ai_bench/resident-ladder-20261031/`, logs
`ai_bench/staged-strata-0.1.47/logs/chunk-l*.log`), design as in section 3: `prefill=4096`, `reserve=900`,
`cache=1500`, `resident = 2/4/6/8`, 3 replicates, interleaved. **All 24 arms are void**, for one mechanical reason:
**the engine granted chunk 2048 where 4096 was declared**, in every arm, so the harness's own declared-vs-granted rule
fired. Cache was granted exactly as declared (1500 slots, 1.93 GiB) in all 24, and every arm reported
`resident_pinned: true`.

That is not a resident finding, it is a design error with a known shape: the phase-2 plan already learned to declare
the *granted* cache from a probe (`--cache-preflight`). The same probe is needed for the **chunk**, which the engine
sizes from what the smaller cache leaves - with cache 1500 the granted chunk is 2048.

**The commit baseline never came back inside a run.** `commit_free_gib_before` fell monotonically **24.87 -> 13.91 GiB**
across the 24 starts, the runner's `wait_commit` hit its 130 s timeout from the third start onward, and only the **first
two** arms (24.87 and 24.71 GiB free) bound their declared value. The 2026-10-27 set shows the same drift in miniature
(23.9 -> 20.5). A declared sweep therefore needs **one process per arm**, or an explicit re-baseline, not a bigger
cooldown.

### The controlled pair

Same night, same cache, same chunk, same reserve, commit free within 0.16 GiB of each other:

| arm | declared | granted | prompt tok/s | decode tok/s | drafts accepted |
|---|---|---|---|---|---|
| `l2-r1` | 2 GiB | 2.00 | 374.9 | 12.4 | 24 |
| `l8-r1` | 8 GiB | 8.00 | 477.9 | 23.2 | 20 |

**+103 tok/s prompt (+27 %) and +10.8 tok/s decode (+87 %) for 6 GiB more resident RAM**, with the answer text identical
(`42` / `150`) in all 24 arms. This is the cleanest resident comparison the lab has: the declared flag was honoured on
both sides and the ambient conditions match.

### The curve, in granted terms (n = 24, granted 0.65-8.00 GiB)

* prompt rate: **r = +0.929, +18.0 tok/s per GiB**, 297-478 tok/s
* decode rate: **r = +0.923, +1.7 tok/s per GiB**, 3.6-23.2 tok/s
* granted vs free commit at start: r = +0.769

Within a single declared value the effect is just as plain: `res8` ran at **477.9 / 23.2** with 8.00 GiB granted and
**344.7 / 10.9** with 1.08 GiB, same flags. So decode follows resident closely *here* - and the reason it did not in the
2026-10-27 arms is that those carried **cache 3000** at a span of 5-10 GiB: with twice the cache, fewer experts come off
the resident copy, so decode stops riding it. **The resident->decode slope is a function of the cache size and must not
be quoted without it.** Conversely, halving the cache costs prefill and decode unless the resident budget is raised to
compensate - which is the trade-off 0.2.8 moved when it switched its own 12 GB default off.

### What the next run must do

1. Probe first and declare the **granted chunk** (2048 at cache 1500) as well as the granted cache, or the harness voids
   every arm it runs.
2. One arm per process with a fresh commit baseline; record `commit_free_gib_before` per arm and refuse any arm whose
   baseline is more than ~1 GiB below the set's first.
3. Keep the rung span wide enough to see a slope (0.65-8.0 GiB was enough) and keep cache and chunk fixed while the
   resident budget moves.
4. n >= 5 for anything that will be compared to a 20 % decode spread; 3 was enough for the slope, not for a cell.

## 6. The sequential run: rungs honoured, prefill follows resident, decode does not

`ai_bench/resident-ladder-seq-20261031/` - 12 arms, one process each, `prefill=2048` (the granted chunk at this cache),
`cache=1500`, `reserve=900`, `resident = 2/4/6/8`, 3 replicates interleaved, each arm gated on ComfyUI idle, >= 8,000
MiB VRAM free and commit >= rung + 18.35 GiB.

**Every rung was honoured**: granted == declared (2.00 / 4.00 / 6.00 / 8.00 GiB) in 12 of 12 arms, `resident_pinned:
true`, chunk 2048, cache 1.93 GiB. The fixes in section 5 hold.

**Four arms are excluded and the reason is not the engine.** Three (q2-r1, q4-r3, q8-r2) show a separate mode - prefill
**216-229 tok/s** against 585-653, two of them with decode **4.7 / 7.9 tok/s** - and every readback field is identical to
the clean arms (cache 1.93 GiB, lend 0 of 790, same file tier). They overlap the user's ComfyUI renders: the gate can
refuse to start while the card is busy, but it cannot hold the card, and ComfyUI took it mid-arm. The fourth (q8-r1) is
void: the cache was granted **10 slots (0.01 GiB)** instead of 1500, with **0 MiB of VRAM free at the request start** and
a measured decode cache hit rate of **1.1 % (135 hits / 11,883 lookups)**.

**The clean set (n = 8, rungs honoured, no contention):**

| rung | n | prefill tok/s | decode tok/s | drafts accepted |
|---|---|---|---|---|
| 2 GiB | 2 | 588 | 70.2 | 23, 25 |
| 4 GiB | 2 | 613 | 70.8 | 21, 20 |
| 6 GiB | 3 | 634 | 72.4 | 20, 21, 20 |
| 8 GiB | 1 | 652 | 67.9 | 21 |

* **prefill: r = +0.926, +11.0 tok/s per GiB** (588 -> 652 for 6 GiB)
* **decode: r = -0.012, flat** (70.2 / 70.8 / 72.4 / 67.9 - no trend outside a 4 % spread). **Superseded by section 7**:
  that flat reading came from n=1-3 with the res8 cell resting on a single low arm; at n=5 the slope is +1.70 tok/s per
  GiB and the same number reproduces the 2026-10-27 curve.

So section 5's "+87 % decode from 6 GiB of resident" is **not** a general result, and this is the correction: it was
measured with the rungs **clamped**, where the low-resident arms had too little RAM for the experts the 3,000-slot cache
did not hold. With the rungs honoured at a fixed cache, resident RAM buys **prefill breadth** and nothing for decode.

**The three tiers, as measured:**

* **VRAM cache** carries decode: it holds the experts a reply re-uses, and its size is what keeps decode at ~70 tok/s.
* **Resident RAM** carries prefill: a 19,769-token prompt touches far more experts than any cache holds, so the RAM copy
  is worth **+11 tok/s of prefill per GiB** and ~0 to decode.
* **Disk** is the collapse mode: the contended arms read the same tier and fell to ~220 tok/s prefill and, when the
  reader was cold too, 4.7-7.9 tok/s decode. A 2.5-15x loss, not a percentage.

**The accidental A/B on the void arm is worth keeping, at n=1:** 8 GiB resident with a **10-slot** cache scored
**648.8 prefill / 55.9 decode** against **651.8 / 67.9** for 8 GiB resident with 1,500 slots. At 8 GiB resident the expert
cache is worth **~3 tok/s of prefill (inside noise) and ~12 tok/s of decode (-18 %)**. That is the tier hierarchy in one
line: with enough resident RAM, the cache is a decode device, not a prefill device.

**Operational consequence.** A ladder run needs the card to itself for its whole duration, not merely at each start. The
next design either (a) runs while nothing else renders, declared up front, or (b) records a `comfy_active` boolean per arm
by sampling the queue during the arm - and of the two, (a) is the honest one, because contention cannot be subtracted
after the fact.


## 7. The clean re-run: 20 of 20 arms honoured, both slopes measured

`ai_bench/resident-ladder-idle-20261101/` - the same design as section 6 (`prefill=2048`, `cache=1500`, `reserve=900`,
`resident = 2/4/6/8`), but **five replicates per rung** and the card to itself: ComfyUI and the Z-Image window were
closed, nothing else held the GPU, and every arm ran in its own process. Commit free stayed **30.93-31.62 GiB** for the
whole 21.9 min run - the decay of section 5 does not exist when each arm gets a fresh process and nothing else competes.

**20 of 20 arms valid**: granted == declared, chunk 2048, cache 1.93 GiB, `resident_pinned: true`, no voids.

| resident | n | prefill tok/s | decode tok/s | accepted | answer text |
|---|---|---|---|---|---|
| 2 GiB | 5 | 578 +/- 5 | 62.2 +/- 2.0 | 23,23,23,23,25 | identical |
| 4 GiB | 5 | 600 +/- 13 | 66.6 +/- 3.4 | 20,20,20,21,20 | identical |
| 6 GiB | 5 | 623 +/- 13 | 69.5 +/- 4.9 | 24,20,20,24,21 | identical |
| 8 GiB | 5 | 645 +/- 10 | 72.5 +/- 3.4 | 20,21,21,21,21 | identical |

* **prefill: 578 -> 645 (+12 %), r = +0.933, +11.2 tok/s per GiB**
* **decode: 62.2 -> 72.5 (+17 %), r = +0.763, +1.70 tok/s per GiB**
* greedy answer text identical in **20 of 20** arms, acceptance 20-25 drafts with no trend

So the resident budget buys **both** paths, and the sizes are now quotable:

* **+11.2 tok/s of prefill per GiB** at cache 1500 / chunk 2048 (the 2026-10-27 set, read as a granted curve over
  0.65-8.00 GiB, gave +18.0 - the difference is that set's low tail, where 0.65-2 GiB arms were disk-bound).
* **+1.70 tok/s of decode per GiB** - the *same* figure the 2026-10-27 arms produced from a completely different design
  (declared sweep, cache 3000, clamped grants). Two designs, one number: that is the lab's first cross-design
  reproduction of a resident effect.
* Sections 5 and 6's "+87 % decode" and "-0.012, flat" are both withdrawn. The first was measured on clamped,
  cache-starved rungs; the second on n=1-3 where the res8 cell was one low arm (67.9 against 70.2-72.4). n = 5 with an
  idle card settles it at +17 %.
* **Day-to-day offset:** res2 decode was 70.2 yesterday and 62.2 today at identical flags - a **12 % offset** between
  sessions, which is exactly the lab's existing 12 % bar. Within-run slopes are quotable; absolute tok/s across days are
  not.

**Design rule now settled for the resident axis:** hold cache, chunk and reserve; run >= 5 replicates; one process per
arm; require the card idle for the whole run; declare the granted chunk.

## 8. The reserve sweep: a reserve is a 1:1 tax on the expert cache, and #4811 reproduces from the other side

`ai_bench/reserve-sweep-20261101/` - 9 arms, `--expert-cache auto`, `resident=4` GiB, `prefill=2048`,
`--vram-reserve-mib = 900 / 1536 / 2000`, 3 replicates interleaved, card idle, no contention, no voids.

| reserve | granted cache | prefill tok/s | decode tok/s | accepted |
|---|---|---|---|---|
| 900 MiB | **4.03 GiB** (sd 0.10) | 646 (sd 8) | **89.2** (sd 4.2) | 24, 24, 23 |
| 1536 MiB | 3.25 GiB (sd 0.03) | 638 (sd 8) | 74.3 (sd 7.0) | 23, 23, 21 |
| 2000 MiB | 2.79 GiB (sd 0.04) | 634 (sd 8) | 79.3 (sd 3.6) | 23, 21, 21 |

* **The reserve is subtracted from the cache almost exactly 1:1**: +1,100 MiB of reserve cost **1.24 GiB of cache**
  (4.03 -> 2.79). Whatever the reserve protects, it is paid for in expert cache slots.
* **Prefill barely moves** (646 -> 634, **+2 %** for the whole 1.1 GiB of reserve) - inside the 12 % bar and in the
  direction cache size predicts.
* **Decode tracks the cache**, not the reserve: 900 MiB beats both larger reserves by **+9.9 tok/s (+12 %)** against
  2,000 MiB, and the 1536 cell is the noisy one (sd 7.0). Across the 9 arms, cache vs decode is **r = +0.593,
  +8.6 tok/s per GiB of cache**.
* **#4811 reproduces from the other side, and its direction is the one this sweep measures.** Their 20 GB Ada card read
  cache **3,429 -> 4,112 MiB** moving to `--vram-reserve-mib 1536` and **2,577 MiB** at 2,048. Our card gives 3,328 MiB
  at 1536 and 2,857 MiB at 2,000 - the same numbers within ~10-20 %. So their "1536 restored prompt rate" is a *lowering*
  of a ~2 GiB default, not a special property of 1536; and their 2,048 "collapse" is the 1:1 tax, exactly as here.
* **The actionable ratio:** a GiB of **VRAM expert cache** is worth **+8.6 tok/s of decode** (this sweep), a GiB of
  **resident RAM** is worth **+1.70 tok/s** (section 7). Cache is **~5x more valuable per GiB for decode**, and the
  reverse holds for prefill (+9.9 per GiB of cache here vs +11.2 per GiB of resident there). On a 12 GB card the config
  that reads "spend the last GiB on cache, not on resident" is the measured one; resident is the lever for long prompts.

**What this closes:** the scan's #4811 item, and the reserve question generally - on this card `900` is simply better
than `1536` or `2000` at a fixed resident budget, by 12 % of decode, because it buys back a GiB of cache.
