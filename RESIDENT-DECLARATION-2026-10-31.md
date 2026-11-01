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
