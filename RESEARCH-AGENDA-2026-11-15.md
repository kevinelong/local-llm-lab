# Research agenda, 2026-11-15: everything the 36 scans asked for, deduplicated, ordered by what it would change

## What this file is

Thirty-six daily scans (`NEWS-2026-10-05.md` .. `NEWS-2026-11-15.md`, including the `-a`/`-b` same-day
variants) each end with a ranked shortlist and a "Gated on Kevin" list. Nothing had ever read those lists
against each other. This file does: every proposal in the corpus, clustered by the question it is
actually asking, with the earliest statement of each question and the latest refinement of it both
cited, and with the proposals the corpus has already answered moved to a `Closed` list rather than
re-ranked.

The point is not a reading list. It is to say which of the questions this lab has been asking for six
weeks would, if answered tomorrow, change a number we already publish - and which are asking the same
thing for the ninth time because nobody wrote down that it had been asked.

## Method, and what it deliberately does not do

- **Counted.** 36 notes. 32 of them carry a headed ranked shortlist (224 numbered proposals, 7 each,
  no exceptions - the format is fixed by convention, not by content). The other four (`10-05`, `10-08`,
  `10-14`, `10-16`) carry an earlier, unnumbered form of the same thing in "Proposed next steps",
  "What remains, in priority order", and "What this adds to the plan": 21 more proposals.
  `SHORTLIST-2026-10-26-untried.md` adds 21 (14 carried, 7 never carried anywhere else). **Total 266
  proposals.** From 2026-10-22 onward every note also closes with a "Dropped, with reasons, so they are
  not re-researched" (later "Not ranked, and why") list; those were read so that a dropped item is never
  listed here as open, and they are not counted as proposals.
- **Classified** by the subject of the item itself, one item to one theme, first match wins. The theme
  column of the count table below is that classification; the row counts are mine, after reading.
- **Read whole**: `DECLARATION-TEMPLATE.md` (all 12 sections), `SHORTLIST-2026-10-26-untried.md`,
  `CHUNK-LADDER-AND-RESERVE-2026-10-26.md`, `RESIDENT-ABOVE-8-2026-11-01.md`,
  `WDDM-SHARED-SEGMENT-2026-10-22.md`, `KNOWLEDGE-DEEP-2026-10-10.md`, and every shortlist and
  "Gated on Kevin" section in the 36 notes. `AGENTS.md`'s dated entries were read for the closing
  statements only (7,000 lines; read as a state register, not as prose).
- **Not invented.** Where a question was answered inside the corpus it is in `Closed` with the note that
  answered it. Where an item was neither answered nor carried again, it is in section 10 and named as
  absorbed or orphaned. No row in this file was added from outside the corpus.

## The ranking rule, in one line

**Ranked by how many published rows a plausible answer would re-read or invalidate, divided by what it
costs in gated things (downloads, engine bumps, Kevin's signature) - so a two-start test that re-reads
four rows outranks a one-start test that adds a fifth row nobody needs.**

Two consequences, applied throughout rather than argued:

1. **A correction outranks an addition.** The lab holds ~30 measured rows and roughly a dozen of them
   are now known to rest on a declared field that did not exist when the row was taken (sampler block,
   `-b`/`-ub`, route prior, chunk, KV type delivered, engine build). An edit that dates a row is worth
   more than a run that adds one.
2. **A gate is not a cost, it is a veto.** 82 of the 224 shortlist items are edits, and 80 of those 82
   appear after 2026-10-28 - the queue did not get cheaper, it converted itself into paperwork because
   the two downloads stayed gated (below). The count table's last column is therefore the column that
   matters: how many of these rows a granted download would move *today*.

## The shape of the queue in one table

| theme | proposals in | notes spanning | distinct open questions (rows below) | rows that need a download or a bump |
|---|---:|---:|---:|---:|
| 1. KV cache and quantisation | 20 | 15 | 4 | 3 |
| 2. MoE expert cache and offload | 56 | 26 | 8 | 3 |
| 3. Speculative decoding (MTP, drafter) | 13 | 11 | 4 | 2 |
| 4. Windows memory contracts | 32 | 22 | 7 | 0 |
| 5. Quantisation and pack provenance | 48 | 26 | 4 | 3 |
| 6. Determinism and reproducibility | 18 | 12 | 5 | 0 |
| 7. Engine and toolchain gates | 26 | 19 | 6 | 3 |
| 8. The harness and the instrument | 23 | 14 | 6 | 0 |
| 9. Not a research question (recorded decisions, one-off image-track runs, dropped items) | 30 | 21 | 0 | - |
| **total** | **266** | **36** | **44** | **14** |

Two of the numbered rows above are not counted as open and appear only for continuity: **1.4** (lazy KV) is
closed on 2026-11-15 and **3.5** (DFlash) was dropped with a reason on 2026-10-24.

Three facts fall out of that table, and the rest of this file is downstream of them.

- **The two gates have been shut for the whole corpus.** The first gated item is
  `NEWS-2026-10-14.md:124` ("Any upgrade of the pinned engine ... is a declared change with a re-pin,
  not an edit"); `NEWS-2026-10-16.md:457` adds the llama.cpp download. On 2026-11-15 the same two are
  still gated - llama.cpp at `>= b12383`, Strata at `0.2.13 / 0.1.59` - and the engine we hold is still
  **0.1.47** and the llama.cpp build still **b11480**. That is **32 days** for one and **30 days** for
  the other, across 36 scans, with the target moving eight times (0.2.6 -> 0.2.7 -> 0.2.8 -> 0.2.9 ->
  0.2.10 -> 0.2.11 -> 0.2.12 -> 0.2.13).
- **The queue's centre of mass moved from measurement to declaration.** Before 2026-10-29, 2 of 84
  shortlist items are edits. From 2026-10-29 on, 80 of 140 are. The template grew to 0.2 with twelve
  sections and a nine-rule start gate in the same period.
- **Fourteen of 44 open questions cannot be started at all** without a download, a bump, or a system
  change. That is the honest answer to "are there areas for further research": yes, and a quarter of
  them are blocked on one signature.

---

# 1. KV cache and quantisation

The lab's KV question has changed subject. In October it was "how many bytes per token"; since
2026-11-12 it is "**which bytes** - the ones we selected or the ones the engine received". That is a
strictly harder question and it dates several rows we hold.

| question | what is already established (note + date) | what is still open | the test that would settle it | cost | gated on |
|---|---|---|---|---|---|
| **1.1 Does the KV type we select equal the type the engine receives?** | A GUI can silently deliver `--kv int8` from a `q4_0` selection on 0.2.13 / 0.1.59 / Windows, and an `args` entry that did not reach argv either (Strata `#5919`, `NEWS-2026-11-13` sec. 2.5, item 2). The runner already parses the argv echo, so the field is free (`NEWS-2026-11-13`). | Never checked on our line, and never checked on any line with a declared `-ctk`. Every KV row we hold names the flag we asked for, not the one that ran. | One context, one engine start: read the delivered type from the argv echo **and** from the engine's own KV line, compare against the declared value; one answer-level check (the 92/93-letter metric) because a geometry change is admissible only if it does not cost answers (`NEWS-2026-10-25` sec. 12.4). | 1 start, no download (needs >= 0.1.52 for the printed routing/KV state) | Kevin (Strata bump) |
| **1.2 What does each KV geometry cost per token on our pack - and what is 65,536 really worth?** | `--kv int8` on Q2_0 is **12.4 KiB/token**, so 65,536 holds **0.77 GiB** of pinned RAM, measured on **engine 0.1.47, the one we run** (`NEWS-2026-11-12` sec. 3.1). `--kv-resident` is the flag that decides how much of the session sits in VRAM: **1,147 -> 7,302 slots, 76.7 -> 93.8 tok/s** when the card had room (same note), and our own q1 row reads **7.2 vs 69.1 tok/s with letters 92/93 in four arms** (`SHORTLIST-2026-10-26-untried.md`). | `--kv q4_0` "halves it" is arithmetic, never measured. `--kv-resident 32768` stopped being a default at some point between 0.1.52 and 0.1.53 (`NEWS-2026-11-01` item 4) and the rollback between them is a manual asset swap, so the flag's history on our engine is unknown. | Ladder at one context: `q4_0`, `int8`, `f8_e4m3`, reading KB/token and the fallback line per arm, plus `--kv-resident` on/off at 65,536. The number that counts is bytes/token, not tok/s - `NEWS-2026-10-31` established that a rate comparison alone cannot decide this. | 4 starts | Kevin (build with FP8 KV: `>= b12274`) |
| **1.3 Does an FP8-KV row measure the cache or the f16 fallback?** | FP8 KV merged in `>= b12274`; the pair is "supported and not compiled" without `GGML_CUDA_FA_QUANTS`, so the row would silently measure a different cache (`#31213`, `NEWS-2026-10-28` sec. 11.6); the f16 fallback costs **0.4-0.5 GiB** of workspace; the fused dequant `#31802` is **open** at 15 comments, so a fused path is a build question and not a flag (`NEWS-2026-11-14` item 2). | Whether any build we can name has FP8 KV *and* the fused dequant. `NEWS-2026-11-13` item 1 records that an FP8-KV row on `b12318` is a **one-route** row because `#28898` is still open. | On `>= b12383`: `-ctk f8_e4m3` against `-ctk q8_0` at one context, KV bytes/token and the fallback warning read back; VOID if the fallback fires (`DECLARATION-TEMPLATE.md` sec. 12). | 2 starts + the same llama.cpp download items 2.2 and 3.1 need | Kevin (llama.cpp download) |
| **1.4 Is KV still reserved before experts are placed?** | **Closed 2026-11-15**: `#32170` (lazy KV) closed **unmerged** on doctrine - *"the memory usage will be the same once the key-value cache is full. This deviates from the project's core concept"* - so 0.77 GiB at 65,536 stays the price and a smaller `--ctx` remains the only lever (`NEWS-2026-11-15`). | Nothing. The question is answered for the engine we would have moved to. | - | - | - |
| **1.5 Does a smaller `--ctx` buy a measurable expert-cache rung?** | The 6x resident-expert cost at longer context is reported but has no row on our card (`NEWS-2026-11-13` item 4 proposes the test). Our own ladder ran at one context throughout (`CHUNK-LADDER-AND-RESERVE-2026-10-26.md`). | Whether 32,768 vs 65,536 changes the granted slot count on 12 GB. This is the only lever `#32170`'s closure leaves, and it is untested. | Two starts, `--max-context 32768` against `65536` on staged 0.1.47 + q2_0, at ~24K prompt, reading the placement line and the granted slots. | 2 starts, no download | none |

# 2. MoE expert cache and offload

The lab's largest theme by both count (56 proposals) and money: this is the only axis where a measured
change on our own hardware has ever been more than 10% (47.4 -> 78.3 tok/s on the ladder,
`--moe-cache-mib`). It is also the theme where the most proposals are *questions already half-answered
by our own runs* being re-asked with one more declared variable attached.

| question | what is already established (note + date) | what is still open | the test that would settle it | cost | gated on |
|---|---|---|---|---|---|
| **2.1 Where is the cache ladder's bad band, in tokens' worth, and is our 512 MiB rung inside it?** | Unit conversion is ours: **0.527 GiB of expert bytes per token**, so our rungs are **0.47 / 0.95 / 1.90 / 3.79 / 7.59 / 9.96** tokens' worth (`NEWS-2026-10-31` item 3). Upstream names the same knee in a different unit: `#31233` prints `1.4 tokens worth`; `#31421`'s collapse is at exactly **1.0x**, and at **240 slots SLRU reads 0.6% hits / 8.8 tok/s against LRU's 37.5% / 12.9** with the first bad commit `#30637` (`b11732`) and the fix `#30848` **closed unmerged on 2026-10-27** (`NEWS-2026-10-30` sec. 3.1). A 5060 Ti reads **18.7 tok/s** with a small cache against **44** with none, mechanism **6.5 GB/s** slot-copy bandwidth (`NEWS-2026-11-12` sec. 6). Our own 256/512 MiB rungs already sat at or below rung 0 (`NEWS-2026-10-20`). | **The one honest gap**: our ladder ran on **b11480 (LRU, pre-`#30637`)**, so the collapse mechanism cannot be its cause and the 512 MiB rung's dead zone has never been attributed. `NEWS-2026-10-30` item 1's correction - "past SLRU and *worse* at the low end" - has never been tested against a build that logs the hit rate. | The ladder re-run on a build that logs `N slots (P %, T tokens worth)` and the hit rate, at n>=5 per rung, with the granted slots and the section fill state read back per arm; declare the build and the policy by build, because a ladder that does not name its build measures a moving policy (`NEWS-2026-10-20` item 3). | 8 starts + 1 download (`>= b12246`, ClassLRU and the `tokens worth` lines) | Kevin (llama.cpp download) |
| **2.2 What is the sign of `--moe-cache-cpu-share` on our pack?** | Unblocked **2026-11-07T16:20:59Z** (merged), which retires five weeks of "needs a build from the PR" (`NEWS-2026-11-08` item 5). The sign flips with cache size: **24.2 -> 47.6 tok/s at 6,464 MiB, 65.5 -> 54.1 at 19,392**, and **+43% at a 3,136 MiB cache, negative on a high-bandwidth host** (`NEWS-2026-10-25` item 6, `NEWS-2026-10-26` item 6). The share is **inert until a section of the cache is full**, so our 512 MiB rung (0.44 tokens' worth) physically cannot fire it (`NEWS-2026-11-11` sec. 9, item 4). The tuner we would use **under-reports the cache by 3.4x whenever a drafter is in the process** - **1,691 vs 5,696 MiB** - and `#31934`'s fix is **closed unmerged** (`NEWS-2026-11-09` item 7, `NEWS-2026-11-10` item 2). | Everything on this box. Not one cell of the grid has been run here. The `-ncmoe` cliff (**80 -> 23.6 tok/s, -70%, no warning**, `NEWS-2026-11-08` sec. 8) is the confound any sweep must fix out. | `scripts/moe-cache-tune.py` verbatim, single-model (not with a drafter, since `#31934` is dead), cache and `-ncmoe` fixed per cell, fill line and granted slots read back, one answer-level check because the Vulkan path produced garbage until `GGML_VK_ALLOW_GRAPHICS_QUEUE=1` (`NEWS-2026-10-26` item 6). | 6 cells, ~40 min, 1 download (`>= b12246`) | Kevin (llama.cpp download) |
| **2.3 Does the engine grant the cache and budget we declare?** | Settled as a *rule*: granted must equal declared or the arm is VOID (`DECLARATION-TEMPLATE.md` sec. 9 rule 7). Settled as a *fact on our box*: 16 arms asking `--resident-budget-gib 16` were granted **5.29-10.18 GiB**, and the complement is sized from free RAM at load (`CHUNK-LADDER-AND-RESERVE-2026-10-26.md`, Revision 2). Mechanisms named: `#4474` (the cache now leaves the reserve you asked for), `#4808` (a `cudaHostAlloc` refused as one block past the driver's single-allocation limit falls back to pageable, `STRATA_PARTIAL_PIN` stepping down 2 GiB at a time and stopping at ~20 of 34.7), `#5570` (a 2.03 GB region outside the line the gate reads). | The **cliff test itself** - a budget deliberately 1-2 GiB short of the pack - has been proposed on `2026-10-22`, `10-23`, `10-24`, `10-26` and then **absorbed into the gate as a rule and never run**. Whether "too small" is a point on a curve or a different configuration is still unknown, and our q2c row found the flag-is-not-the-number case by accident. | Two starts: one at a budget 1-2 GiB short of the pack, reading the engine's own `experts live in VRAM/RAM/file` line; one at a named `--expert-cache N` reading the **granted** slot count back. | 2 starts, no download | none |
| **2.4 Does our learned `.strp` profile buy anything, and does its provenance matter?** | The mechanism is proven and the artifact held: a **196,632-byte `STRP`**, 48 layers x 512 experts, learned in 106 s on 2026-10-16, sha `3acf05d1...` against the shipped `8f59b4aa...` (`NEWS-2026-10-17` item 2, `NEWS-2026-10-24` item 7). The prior is **low and stated**: the shipped profile is only the **third** sort key behind resident and learned heat (`#3448`, `src/core/expert_cache.cpp:160-164`), and a stale-vs-rebuilt comparison measured **44.8 vs 43.6 tok/s inside +-5%** (`NEWS-2026-10-20` item 4). A from-profile start ran cold at **53.3 tok/s against a warm engine's 64.3** (`NEWS-2026-10-17`). Separately: English-calibrated expert pruning costs **1.7 points of English and 21.4 of Lithuanian** at 25% (`2611.07654`, `NEWS-2026-11-08` item 6), and we have never declared the calibration text of our profile. | The cold-vs-cold pair itself: proposed 2026-10-17, carried **six times**, never run. And the provenance test - 414-check with the profile and without - was proposed once (`NEWS-2026-11-08` item 6) and not carried. | Two or more fresh cold engines per arm, both arms after the **same idle period** (the spread has a time-since-last-heavy-pass component, `NEWS-2026-10-21` item 2), reporting which profile the engine actually read; then the 414-check with and without the profile. | 4 starts, no download | none. Expected value is *small or absent*, and that is the result worth having |
| **2.5 Can the hot set be predicted before a run?** | Two independent routes to the same question: per-layer **routing entropy** from the staged pack's router tensors (SPARE, `2610.29662`, `NEWS-2026-10-22` sec. 7), and our own `.strp` ranking against the per-layer cache behaviour the log already reports (`NEWS-2026-10-24` item 7). The prior it would replace is `#27149`'s **6% random vs 42% calibrated** (`NEWS-2026-10-16` item 4). | **Orphaned**: carried `10-22`, `10-23`, `10-24`, then never again - not dropped with a reason, not answered. It is the cheapest possible answer to the 6%/42% result and it is no longer on any list. | Compute the profile's (or the router's) per-layer ranking offline and compare it against where the cache actually hit in an arm we already have. No engine start for the offline half. | one script + one existing run | none |
| **2.6 Is the lend region reachable on 12 GB at all?** | Measured: **0 of 1,373-2,541 slots in all 21 arms**, including five re-runs - "it never was the lever" (`CHUNK-LADDER-AND-RESERVE-2026-10-26.md`). `--prefill-borrow` **does exist** on our line and is absent from `--help` (266 lines, 0 hits for `borrow`; the literal `--no-prefill-borrow` is in the binary) - settled by `strings`, not by a run (`DECLARATION-TEMPLATE.md` sec. 8, 2026-11-09). The engine prices an 18% uncovered region at **26%** of prompt time. The only levers are a resident budget with a remainder after **24,576 ranked pairs** (needs 42.35 GiB commit, out of reach) or a smaller `--prefill` (tested: **-23.4% prefill, 0% coverage gained**). | One cheap thing is left and it is free: whether a **different pack with fewer ranked pairs** leaves a remainder at 16 GiB. `RESIDENT-ABOVE-8-2026-11-01.md` names the check - read the ranked count from the profile line - and nobody has. | Read the ranked-pair count from the existing profile/log line; no arm needed. | minutes, read-only | none |
| **2.7 Is the prefill loan priced, and does 0.1.59 change it?** | `#5943` prices the mirror of our 2026-11-01 finding at **-26% decode**, and `STRATA_PREFILL_LEND_PCT=0` is the back-out (`NEWS-2026-11-14b` item 6). The declaration has no "loan planned / slots lent" field yet, so any 0.1.58 -> 0.1.59 comparison measures an undeclared state. | Whether the loan fires at all once the cache can keep the experts - i.e. whether the lend region is a *different* mechanism from the loan or the same one under two names. | The field first (an edit), then one interleaved pair per build. | 2 starts, rides the gated bump | Kevin (Strata bump) |
| **2.8 Can one conversation's cache be read by another request?** | Two independent observations point at it: our own `reused = 0` declaration item is "the same observation from the other side" of an engine evicting a cache the caller believed was imported (`NEWS-2026-10-28` item 7), and the harness already holds the conversation-cache fields (`reused`, `N checkpoints`, `#4206`/`#2518`) made mandatory on 2026-10-26. | Whether prefix reuse crosses requests. Proposed `2026-10-27` (item 6, "~10 min") and `2026-10-28` (item 7), then never carried. This is the only security-shaped question in the corpus and it costs two requests. | Two conversations with disjoint secrets sharing one conversation cache: does request B ever see A's tokens? Read `reused` per request. | 1 engine, 2 requests, ~10 min | none |

# 3. Speculative decoding (MTP, ngram, DFlash)

Thirteen proposals, one of them the single most consequential re-pricing in the corpus: our only
speculative row is now a **pre-kernel** result and nobody had noticed the kernel existed
(`NEWS-2026-11-15`).

| question | what is already established (note + date) | what is still open | the test that would settle it | cost | gated on |
|---|---|---|---|---|---|
| **3.1 Is MTP a wall-clock win on this card?** | Our row: **+31.2% per token, -7.3% wall, +21.7% tokens, accuracy unchanged**, on **b11461** (`NEWS-2026-10-08`). `#31533` ("CUDA: few-row MMQ for BS 2-24", merged **2026-11-12T13:12:46Z**, commit `0fb8f1577`) is in **`>= b12359`** and **not** in `b12208`: an interleaved benchmark reads **+52% / +55% with MTP on v1.0.0** at **unchanged acceptance of 32-33%**, so the gain is the verify step getting cheaper, not the drafter improving (`NEWS-2026-11-15`). Same page: the **14-22%** component needs **4 concurrent slots**, i.e. it is unreachable at our `--parallel 1`. | Everything on our card. The one fact that makes this urgent is that a **-7.3% wall** result is currently our most quotable statement about MTP and it may be a kernel artefact. | Two starts on one build `>= b12383`: `--spec-type draft-mtp` off and on, same prompt, reporting **accepted/offered** plus wall clock. Acceptance unchanged is the prediction; wall clock is the answer. | 2 starts + the same download as 2.1/2.2 | Kevin (llama.cpp download) |
| **3.2 Is acceptance the quantity that moves decode, and is ours saturated?** | `#4778`'s triangle shows acceptance moving decode at **fixed flags**: 70K accept **70-74% / 65-72% / 72-75%** against decode **161.7-162.3 / 153.3 / 163.8 tok/s** for 0.1.52 / 0.1.54 / 0.1.55 (`NEWS-2026-10-31` item 2). Above **~98%** acceptance the pair is repeating rather than drafting; healthy is **65-85%** (`#4402`'s closing comment, `NEWS-2026-11-04` item 3). Our own q7 pair accepted **43-48 of 46-49 drafts** - at the top of the healthy band, i.e. we have no headroom in acceptance, only in verify cost. | **Which drafter**: `ACCEPTED/OFFERED` is a declaration field since 2026-10-31, but the drafter's identity (Auto / MTP / DFlash2 / Off, one per run) and the `--draft-conf` in force are not, and 0.1.56's parallel-mode witness (`#5194`) is unread. Our newer arms print neither. | An edit plus one re-read of which rows already carry the counter; then one start per drafter. | 1 edit + 1 start | none for the edit; the arm rides the download |
| **3.3 Why did MTP draft nothing in the 0.1.47 row (`drafts accepted 0 of 0`)?** | Answered in mechanism, not on our box: `needs_logits()` is true whenever a penalty is present, so the model card's **`presence_penalty 1.5` disables MTP drafting**, confirmed by a third party on 4x3090 at v0.2.12 (`NEWS-2026-11-11` sec. 3.1). `#3354` is **still open** at 2026-11-15. That is the mechanism behind our 2026-10-21 `drafts accepted 0 of 0`. | Whether explicit zeros in the sampler block restore drafting, and whether our q1 KV row's letters 92/93 came from four arms that were *not greedy* - which `NEWS-2026-11-11` now asserts they were not. | One start reading `drafts accepted` with and without explicit zero penalties. | 1 start, no download | none |
| **3.4 Does our configuration reproduce `#5213`'s draft-conf mispricing?** | `#5213`'s trigger is literally our declaration - `--kv-resident` below `--max-context` and no explicit `--draft-conf` - and it misprices **815 slots**; two vendor cards measure the flag at **+0.5 to +11%** (32 GB R9700 66.7 -> 71.1; 24 GB RX 7900 XTX 85.3 -> 94.5) (`NEWS-2026-11-04` item 4, `NEWS-2026-11-05` item 4). | Never run, because the conf is only readable on an engine that prints it (ours does not). The remedy if it reproduces is a `user_args` entry, since `strata launch` regenerates the config. | Read the app's launch line for `--draft-conf` and the engine's `expert cache N slots`, compare against `CONF_STEPS`. No benchmark. | 1 start + 2 log lines | Kevin (Strata bump) |
| **3.5 Is DFlash worth staging?** | **Dropped with a reason on 2026-10-24** and never carried: `[HFR]` Nemotron 3.5 Bolt E4B ships a DFlash draft - "the right *shape* for a drafter test, the wrong *size* for a VRAM row; revisit only if the DFlash question outranks the MTP one." It has not. | Nothing open. The question it was deferred to (3.1) outranks it and is itself gated. | - | - | - |

# 4. Windows memory contracts

Thirty-two proposals, twenty-two notes, **and not one of them needs a download**. This is the theme
where the lab's cost of being wrong is highest and its cost of asking is lowest - and the one
correction it has ranked first on seven consecutive scans has still not been made.

| question | what is already established (note + date) | what is still open | the test that would settle it | cost | gated on |
|---|---|---|---|---|---|
| **4.1 What *is* the WDDM shared-segment cap on this build?** | What we measured: one resident arm consumes **17,941 MiB (17.52 GiB)** of `GPU Adapter Memory\Shared Usage` against 163 MiB at rest, **reproduced twice** (17.63, then 17.81 GiB), and commit free falls **25.7 -> 0.84 GiB** while free physical still reads 15.17 GiB (`WDDM-SHARED-SEGMENT-2026-10-22.md`). The note is explicit that the cap was **never measured**: "we measured usage against an assumed cap, not the cap." That assumed cap - `~31.7 GiB`, from ComfyUI `#17416`'s "50% of RAM" - is the number every later note quotes. Against it: `#4860` measures **one `cudaHostAlloc` succeeding at 23 GiB and failing at 24 GiB with 58 GiB free**, while **cumulative 1-GiB pins reach 45.0 GiB** against `IDXGIAdapter3` **NON_LOCAL 47,268 MiB** (`NEWS-2026-11-01` sec. 2.1); Ollama `#19636` says *"about half of RAM: 63.6 GB on a 128 GB machine"* (`NEWS-2026-11-10` sec. 4.3); ComfyUI `#17578` reads `ram * 0.40` (`Enabled pinned memory 26180.0` on 64 GB, `NEWS-2026-11-06` item 2). | Three witnesses give three different arithmetic shapes and our own note still carries the fourth. **The correcting edit has been the first- or second-ranked item on 2026-11-01, 11-01a, 11-02, 11-04, 11-05, 11-06 and 11-07** (called "the third / fourth / fifth / sixth consecutive scan" in turn) and the file `WDDM-SHARED-SEGMENT-2026-10-22.md` is unchanged (`git log -1` = `ed6d19f`, 2026-10-22). So: the *rule* is open and the *edit* is open, and they are not the same item. | Two things. (a) The cap directly: one DXGI call - `IDXGIAdapter3::QueryVideoMemoryInfo(0, DXGI_MEMORY_SEGMENT_GROUP_NON_LOCAL)` - which the note says "this instrument does not make". (b) The edit: replace the rule with per-allocation ~23 GiB inside a ~46 GiB non-local pool, and cite the three witnesses. | (a) one throwaway script, no engine; (b) one edit | none |
| **4.2 Is the pinned pool a ceiling or a per-request churn cost?** | Measured **on our card class**: llama.cpp `#31840` reports **33 `cudaMallocHost` / 33 `cudaFreeHost` per 32-request batch, ~80.02 MiB each, 1.409 s of API time and 1.434 s of `sched_reserve` over stretches with no GPU work**, on an RTX 5070 SM120; `#31841` measures **-16.15% wall** from keeping the scheduler (`NEWS-2026-11-07` sec. 2). The sentence the note had been missing: *the pinned pool is not only a ceiling, it is churned, and the churn is a per-request cost that commit headroom sees and tok/s does not.* | Whether our arms pay it. Nothing in our records reads `cudaMallocHost` counts, and `#31841`'s -16.15% is a whole-wall effect that our decode-only rows would not show. | Add a scheduler/`cudaMallocHost` signal to the retained-log grep, and read it against the arms we already hold. `NEWS-2026-11-07` item 3 asks exactly this and calls it "the gate for items 4 and 5". | one grep over retained logs | none |
| **4.3 Does a failed pin degrade silently, and is that our 2026-10-11 load failure?** | The tell is one line, `CUDA_Host` vs `CPU` in `load_tensors`, and the log line to grep is `page-locking refused (out of memory); trying pageable memory` (`NEWS-2026-11-01` item 1). A `cudaHostRegister` can return `cudaSuccess` in 7-21 ms and the **next** kernel launch fail OOM, 2 of 3 boots (Strata-xeno `#300`, `NEWS-2026-11-04` item 2). Pageable host weights cost **-43% pp512 at `-ngl 0`** (905 -> 514) with decode unchanged; a refused pin alone costs **60.9-107 s** of start time (Ollama `#19636`, `NEWS-2026-11-10`). So: *registration succeeding is not residency being acquired* and *acquiring it is not automatically worth anything* (ik_llama `#2849`: mlock 106 GB + direct DMA gave **32.1 vs 32.6 tok/s**). | Our recorded cause for `CUDA error: shared object initialization failed` on Windows/CUDA/sm_120 with `0xc0000409` is flash-attention shared memory. That is real for that build and is now **one of two causes for the same string** (`#17380`, `NEWS-2026-10-30` item 2). We have never re-read our own note against the second cause. | A re-read of `NEWS-2026-10-11` against `#17380`, plus adding the host-buffer type to the declaration. | an edit + a re-read | none |
| **4.4 Commit headroom or RAM - which gate actually binds?** | Commit free 25.7 -> **0.84 GiB** under one resident arm while free physical reads 15.17 GiB (`WDDM-SHARED-SEGMENT-2026-10-22.md`); idle weights go from ~30 GiB to ~0.1 GiB *within one sample* when commit headroom exists, TTFT **35-50 s against 22 s**, and the same model evicts again with a 48 GB page file (`NEWS-2026-11-12` sec. 1.3); the lab's own 8 GiB commit gate refuses arms while free physical reads 15 GiB. And a 24 GiB arm needs **42.35 GiB** free commit while the box peaks at ~35.3 GiB, so the arithmetic ceiling is **17.0 GiB** on this box today (`RESIDENT-ABOVE-8-2026-11-01.md`). | Nothing reads device-local memory beside free commit at ready and again after an idle interval - the field is proposed (`NEWS-2026-11-12` item 5) and would subsume the contention item, and it is never taken. | Two starts (~15 min): device-local memory and free commit at ready, then the same pair after an idle interval. | 2 starts, no download | none |
| **4.5 File-cache expert reads or unbuffered - which mode is our box in?** | Two Windows measurements point **opposite ways**: `#3059` gained **+26.3% decode** (28.5 -> 36.0 tok/s) by letting the Windows file cache serve later expert reads, on 64 GB RAM / 16 GB card; Maya `#995` is the opposite sign - misses read through the GGUF mapping stalled a **27,908-token prompt every time** until unbuffered reads plus `VirtualUnlock`, on 112 GB pack / 32 GB RAM, and it now answers in **185 s** (`NEWS-2026-11-15` item 4). The reconciliation is **whether free RAM sits above the working set**, and this box - **63.46 GiB RAM against a ~66 GB pack** - is the boundary case. | Our whole chunk ladder sat on the Maya side of that line (2 GiB resident, 29.6 GiB streamed) and **never declared which mode it was in**. Now a template field (`expert_read_mode`), `unreported` on every row we hold. Also: `#3059` was **closed by the reset, not merged**, and 0.2.1's notes contain no Windows file-read-cache default (`NEWS-2026-10-20` item 7). | Declare the mode per arm and read the tier line; then the `STRATA_R6_FILE_READ_CACHE` pair the corpus has carried since **2026-10-18**, same binary, `STRATA_UNBUFFERED_LOAD=1` in both arms, identical text pair by pair required. | an edit + 2 starts (the pair needs a build) | a build for the switch; the declaration does not |
| **4.6 Is idle VRAM a desktop artefact, and does the display cable change pay?** | Idle readings of **831 MiB clean vs ~1,982 MiB with clients up**, while the admissible cache rung leaves **683 MiB** free (`NEWS-2026-10-26` item 2); and the same box's "idle" figure has read 1.3, 1.7 and 9.6 GiB within one day (`SHORTLIST-2026-10-26-untried.md` item 6). | Which reading is the desktop. Proposed 2026-10-26, then carried only as a gated line; the *measurement* half (no engine, minutes) was never taken. | `nvidia-smi` idle at a fixed desktop, repeated at two states. | minutes, no engine | the cable change is Kevin's; the reading is not |
| **4.7 Does an NVMe drop off the Windows bus under host-buffer staging?** | One window, two engines: `error=433` / `stornvme 129/11`, drive fine, and `--disable-dynamic-vram --disable-pinned-memory` fixes it at **25-35% wall** (`NEWS-2026-11-11` sec. 2). Our packs and image models are on `D:`. | Never looked for in our own logs. | One grep of retained logs for `433` and `stornvme`, plus a VOID rule for a drive that disappears. | one grep | none |

# 5. Quantisation and pack provenance

Forty-eight proposals, and a genuine shift of subject: October's version of this theme was "which pack
should we download"; November's is "**what is a pack**, and can a score be quoted without knowing it".
That shift produced the single most uncomfortable finding in the corpus (5.1).

| question | what is already established (note + date) | what is still open | the test that would settle it | cost | gated on |
|---|---|---|---|---|---|
| **5.1 What identifies a pack, and is our staged copy the pack we think?** | Three separate ways identity fails. (a) **Size and revision are not enough**: a re-uploaded set whose file sizes *and* revision we already track cost **-56% at 2.5K and -41% at 100K** prompt throughput because **33 of 48 down layers moved to Q5_0**, leaving the fused prompt path (`NEWS-2026-11-09` sec. 4.1). (b) **The same quant name is not the same file**: `bartowski/Kolibri-1-GGUF` Q3_K_M and our Hob-forge file are **96.6 MB apart** (`NEWS-2026-10-18` item 6). (c) **Our staged copy is two conversions old**: `7878dc9a90 -> eb0b3cc97f`, `.src_sha` `995ad96e -> 345d467b`, Q4_K_M **+118 MiB**, i.e. a fresh download is different bytes under the same name (`NEWS-2026-11-08` item 4). And **"the pack loads" is not "the pack is right"**: 7 of 305 official GGUF tags solved at most 6 of 164 HumanEval+ tasks while **five rebuilt from source matched tensor for tensor** (`NEWS-2026-10-30` item 7). | Our `q2_0` pack is described by name and bytes only: no revision field was enforced when it was staged, no expert-type histogram, no digest, no `.src_sha`. The template now has the fields; the pack has not been re-read into them. | One GGUF header read: expert-type histogram beside the revision. Plus the digest fields. | an edit + one header read | none |
| **5.2 Does calibration text explain the score gap we report as a tie?** | `2611.11079`: **task-informed calibration is worth +1.83 pp** mean ten-task accuracy at two bits over generic-text calibration, recovery **concentrates on families included in calibration**, and **deliberately incorrect answer designations retain about 90%** of the gain, while **reconstruction error does not track accuracy**. Our knowledge null is **88.5% vs 89.7%** on 1,100 items with a **paired SE of 1.33 pt**; the 89.7% stack is a **2-bit** pack; **neither publisher declares its calibration text** (`KNOWLEDGE-DEEP-2026-10-10.md`, addendum 2026-11-15; `NEWS-2026-11-15` item 6). | The effect (~1.8 pp) is **larger than the 1.2-point gap** and larger than the instrument's own error bar, which means the tie cannot be read as "two bits equals four bits". Both stacks' entries read `UNVERIFIED`. No pack we hold declares its calibration text, so the field cannot resolve it without a download. | Re-read the null with the field present, i.e. one 2-bit and one 4-bit pack **whose publishers declare calibration**. The pessimistic version is already possible and free: restate the null as "not measured", which retires the 2-bit-equals-4-bit reading without any engine time. | an edit now; 2 downloads for the measurement | Kevin (downloads) for the measurement; nothing for the restatement |
| **5.3 Is a first run a task check, not a load check?** | The rule is decided and the evidence is double-sourced: **7 of 305** tags broken at the task level while bit-identical to a rebuild; perplexity must never be quoted alone because `2610.37126` ranks a **functionally inverted** model (17.7% accuracy) as *less* damaged than random pruning (**74.5 vs 140.1**) (`NEWS-2026-10-29` item 4, `NEWS-2026-10-30` item 7). | Never applied. It is the standing opening move for the Kolibri APEX 22.2 GB, Flint IQ3_M 17.5 GB, Clover 16.5 GB and Groot 8.4 GB candidates - all downloads, all parked behind a rule that has never executed. | The 414-check (or a task-shaped probe) as the *first* run of any new pack, with teacher-forced perplexity paired beside it. | a spec now; the runs are gated | Kevin (downloads) |
| **5.4 Which candidate pack earns the first task check?** | Six shortlists carried `ggml-org/Qwen3-Coder-30B-A3B-Instruct-GGUF` Q4_K_M **16.75 GiB** (revision `0ca51122012f` unchanged across `10-22`..`10-26`) as "the only first-party 30B-class coder in our shape"; Flint 21.78 GiB and Kolibri Q3_K_M 35.04 GiB were carried on three; Clover/Groot arrived `10-31` and are now **blocked by a quantisation-tool question as well as a loader one** - `This GGUF is missing the metadata key 'clover_moe.expert_shared_count'`, workaround "quantise with `llama-clover-b4838ffb` rather than upstream" (`NEWS-2026-11-07`). | This is a queue, not a question - and it is the clearest instance of a *download* being the whole gate. It is listed because it is the largest single block of proposals in the corpus (15) that has produced no measurement. | Nothing to settle: the first download is the test. | 16.75 GiB | Kevin (download) |

# 6. Determinism and reproducibility

Eighteen proposals. This theme is unusual in that **every one of its open items is an edit that dates a
row we already publish** - there is almost nothing to run.

| question | what is already established (note + date) | what is still open | the test that would settle it | cost | gated on |
|---|---|---|---|---|---|
| **6.1 Which of our published rows are determinism claims, and does the expert cache void them?** | The vendor names the mechanism in its own release notes - *"the expert cache, which moves experts between the CPU and the GPU between requests; the two round differently"* - and gives the controls (`--no-expert-cache=on` restored identity; `DS4_ASYNC_T=16` gave 20/20) and the price (**8-10% of decode, 58% on one card**). Two independent witnesses agree: Maya `#644` (0 experts on the CPU lane -> bit-identical **including `--parallel 2`**; 329 on the lane -> last-row logits differ by **2.3-3.0**), and llama.cpp `#25618`/`#31472` (a quantised target plus any engaged draft diverges at temp 0) (`NEWS-2026-10-31` item 1). | The relabel itself: our 2026-10-08 MTP row is a **speed-and-letters** result and **not** a determinism result. Ranked first on 2026-10-31, carried or implied on twelve notes since, and still not written. | An edit. Five lines in `DECLARATION-TEMPLATE.md` and one dated line beside the 2026-10-08 row. | an edit | none |
| **6.2 Is "same flags, same answer" valid without a build gate?** | `b12208` **is** the tied-Top-K merge commit (mean KLD **0.0011 -> 0.000000**, same-top-p **99.48 -> 100.000%**), and with **CCCL 3.4.3+** one or two rows still route through `DeviceTopK`, so ties there remain timing-dependent (`NEWS-2026-11-08` item 7, `NEWS-2026-11-09` item 3). `-b`/`-ub` was added the same way on 2026-11-01: **ub1 vs ub512 bitwise-identical logits over 140 positions at twelve ub values**, MTP 2-row verify delta **+0.25 -> 0.0**, but the remainder diverges **past position 196 in 4 of 8 prompts**. Every row we hold is pre-patch (`b11480`/`b11461`/`b10883`). | The fields exist (`top_k_impl`, `cccl_version`, `ubatch`, `chunk`). No row has been backfilled, and no one has asked whether the *pattern* - a new numerics field appears roughly every four days - is converging or merely accumulating. | An edit to backfill, plus a decision: is a row without these four fields VOID (like rule 7) or merely dated? Currently it is merely dated. | an edit | none |
| **6.3 Does the sampler block silently change or disable things?** | Three findings, all in one class: the model card's **`presence_penalty 1.5`** reaches `temperature: 0` requests at v0.2.12 and **disables MTP drafting** (`needs_logits()`), the mechanism behind our `drafts accepted 0 of 0` (`NEWS-2026-11-11` sec. 3.1); Ollama `/v1` was sending `temperature 1.0`/`top_p 1.0` when the client omitted them and resetting penalties to 0, so `qwen3.6`'s `presence_penalty 1.5` **became 0** and four families' `top_p 0.95` **became 1.0** (`#19432`, merged 2026-10-31, `NEWS-2026-11-01` item 6); and leaving them out is not "off". | Whether our rows were greedy at all. `NEWS-2026-11-11` item 1 states it changes the reading of the q1 KV row (**letters 92/93 in four arms that were not greedy**), the 0.1.47 MTP reading, and every "same flags, same answer" claim - i.e. it re-dates rows, and the re-dating has not been done. | A declaration field (exists) plus one start reading `drafts accepted` with and without explicit zeros. | an edit + 1 start | none |
| **6.4 Does a chunk change move agent prompts, and are our KL rows readable?** | The vendor's own Known-problems item: agent prompts flip attention blocks on **70-90% of queries** at a **sub-1e-3 near-tie margin**, any chunk change moves them by an **O(1) KL** while plain text moves ~1e-5, and the vendor's own agent-prompt KL figures (route-tail skip 0.203, K-quant 0.065/0.052) *"may be inflated by this effect and were not re-measured"* (`NEWS-2026-11-05` sec. 1.4, item 1). | Rule 13 of the start gate now says "a KL row without `chunk=` is VOID, and an agent-prompt determinism claim at all". **That rule post-dates every KL row we hold.** | An audit: how many KL rows do we have, and how many can now be quoted? This is a counting job, not a run. | an hour of reading our own results | none |
| **6.5 Is the single-card prefill CPU share a non-determinism source?** | On by default on one CUDA card since 0.1.41, its two parameters come from per-process CUDA-event timings, and two processes shared **23 and 36 of 42 layers on the same request** (`NEWS-2026-11-10` sec. 2). The binary adds the text-changing half: *"the CPU share is ON by default for prompt chunks below 1024 tokens ... answers can differ slightly from 0.1.40.3, mean KL ~0.004"*, `STRATA_PREFILL_CPU_SHARE=0` to turn it off - which **fires on exactly the arms whose chunk clamps to 512** (`DECLARATION-TEMPLATE.md` sec. 8, 2026-11-09). | Not declared on the q1 KV row, the resident ladder or the MTP row, all of which ran on 0.1.47 where it is on. The two-start check that the flag is honoured is still owed. | An edit plus two starts proving the flag changes something. | an edit + 2 starts | none |

# 7. Engine and toolchain gates, build identity

Twenty-six proposals. In October this theme was "should we bump"; it is now "**what is a build, and can
a row be quoted across one**" - a strictly better question, and one the corpus answered for itself on
2026-11-15 (`DECLARATION-TEMPLATE.md` sec. 12).

| question | what is already established (note + date) | what is still open | the test that would settle it | cost | gated on |
|---|---|---|---|---|---|
| **7.1 What is the build boundary for each feature a row uses?** | Answered by construction: sec. 12 of the template is now a five-row table - `b12383` for `-nkvo` + `--moe-cache-mib` (and below it the load aborts at `src/llama-moe-cache.cpp:560`, "a start failure that measures nothing"), `b12208` for deterministic tied Top-K, `#31533` in `>= b12359` as a **comparability** boundary rather than a void, ComfyUI's cast-buffer fix in **no release we hold**, and the GGUF advisory explicitly **not ours** (`DECLARATION-TEMPLATE.md` sec. 12, 2026-11-15). Two principles are stated with it: *a versioned release is a name, not a boundary* (`v1.0.0` is `b12359`'s tree) and *a closed issue is not a moved boundary*. | The table lists the features that **have already surprised us**. The unanswered general question is whether every arm should declare the feature-to-boundary map its flags imply, or whether the table is a growing exception list - and the difference decides whether the next surprise is caught by the gate or by a scan. | A review of the nine start-gate rules against the five boundaries: which flags in the copy-paste block have no boundary row? Cheap, and it is the only open item in this theme that is not a download. | an hour's reading | none |
| **7.2 Is a locally compiled engine a qualified build?** | `#4879`: a **source build, sm_120 only, nvcc 13.2** scored **0/10** on a tool-call probe where the **prebuilt 0.1.55** scored **10/10** on the same host, model, tokenizer and profile - while *"short factual prompts"* passed and a 30-minute soak plus 61-task-style checks did not catch it. A second reporter on the same GPU with **nvcc 13.4.92** is clean, so the field is not "local is bad" but **which binary and which nvcc minor** (`NEWS-2026-11-01` sec. 2). | What a new build's load check must therefore be. The note's own answer - a tool-call-shaped probe, not a factual smoke - has never become a rule in the start gate, and it is the only load check in the corpus that was falsified by a build we would otherwise have trusted. | Add the probe to the gate, then use it on the first build we compile. | an edit | none |
| **7.3 Is the Strata bump worth taking at all, five weeks on?** | The gate is as old as the corpus (`NEWS-2026-10-14.md:124`) and the target has moved **eight times**. Along the way the bump acquired: a routing default the vendor turned **on and back off again** (12 GB residency-biased routing, **+22.9% teacher-forced perplexity** at prior 1.5 by the only published measurement, then reverted citing *"repeated text in long sessions"*, `NEWS-2026-10-28` item 1, `NEWS-2026-10-30` item 4); a decode-regression scare that was **retracted by its own reporter** (`#4826`, `NEWS-2026-11-02` sec. 1.1); two failures that are **Windows-specific** (`0xC0000135` on Control; `cfg.pop("lib_dirs", None)` dropping the CUDA 13 `cublas64_13.dll` path, `#4994`, `NEWS-2026-11-02` item 3); and the vendor's own two admissions on 0.1.55 - **defaults on a 64 GB Windows PC were not tested** and **UD-Q4_K_XL on Windows Strix Halo stopped on the first request in 7 of 30 starts** (`NEWS-2026-10-31` item 6). | Whether a bump that has been the top gated item for five weeks is still a *bump* or has become a **re-baseline of the whole instrument**. `NEWS-2026-11-13` now asks for a **fifth control arm at 0.1.59** and carries **three more fields** into the bump's declaration, and the declaration list has grown from the **eight items** `SHORTLIST-2026-10-26-untried.md` counted (item 8) to a block that on 2026-11-15 also declares the lend region, the `--ple` served-from line, `STRATA_PREFILL_RING`, and `#6019`'s "none with Q2_0" as a reason not to move the pack in the same step. The honest open question is not "which version" but **"what does the bump's cost estimate have to include before it can be signed"**. | Not a test - a decision, written once. The material for it is already in the corpus; what is missing is a single page that says what would be true if the bump were taken, what would be true if it were skipped, and which of our published rows depends on which. | writing, not running | Kevin (signature) |
| **7.4 Does the route prior pay at task level or only at perplexity?** | Both sides are measured, on other cards. **For**: **+24% decode and 2.3x cache hits with 24/24 passing** on an 8 GB card (`#5000`, `NEWS-2026-11-02` sec. 1.3). **Against**: **+22.9% teacher-forced perplexity** and **AIME -10.0** (`NEWS-2026-10-28`, `NEWS-2026-11-01`), and a published task-level table - IFEvalCode **20.0 -> 16.7%**, AIME 2026 **76.7 -> 66.7%**, IFeval **81.3 -> 78.7%** against speed **72.3 -> 104.6 tok/s** (`#4841`, `NEWS-2026-11-01` item 5). The rule from `2610.37126` is that perplexity alone must never be quoted. | Never run here, and it needs engine **>= 0.1.52**; we hold **0.1.47**, which predates it. So this question is *entirely* downstream of 7.3 - it is the strongest single argument for taking the bump. | Teacher-forced log-probability over ~8,192 forced positions at `prior=0` vs `1.5`, n>=2 starts per arm, plus the 92/93-letter check. | 2 arms x 2 starts, ~1 h | Kevin (Strata bump) |
| **7.5 Is `--vram-reserve-mib` a tuning value or a paging threshold?** | It became **budget** rather than scratch space between 0.1.43.1 and 0.1.46, with a **+53% prefill difference either side of it** (`NEWS-2026-10-29` item 1); the engine **skips every memory adaptation when it is given** (`#3750`, `NEWS-2026-11-05` item 3); and the concrete pair is uneven - on a 20 GB Ada card, **1536 increased the granted cache from 3,429 to 4,112 MiB and restored prompt rate (1,139 -> 1,588 tok/s), while 2,048 collapsed it to 2,577** (`NEWS-2026-10-31` item 5). | Our own note's finding - **900 beats the config's 2000 at the same chunk** (`CHUNK-LADDER-AND-RESERVE-2026-10-26.md` sec. 2) - was taken at 2168 inherited slots and then re-taken at 3000, where the reserve's prefill effect is **+0.5-4.4%** and its decode half is **withdrawn as unresolved**. So our reserve row now says less than it used to, and no one has decided what the gate should require of a reserve declaration. | An edit: "did free VRAM fall below the declared reserve during the request" as a field, plus `--vram-elastic` in the declaration list. | an edit | none |
| **7.6 Is the Windows update path usable?** | Two Windows failures make `strata.py update` unusable on this box, and the documented alternative is to rewrite `engine.pinned` in `components/.updates/state.json` and cycle the model, verifying against the engine's own **`session is up (engine X)`** line (`#4994`/`#4996`, `NEWS-2026-11-02` item 3). `setup` re-downloads the current engine, so an old engine is restored by replacing `engine/` from the matching release tag's asset (`NEWS-2026-11-01` item 4). | Whether the pinned path reproduces `strata components rollback`'s result. Untested; it is the difference between a bump we can undo and one we cannot. | one bump plus one deliberate rollback, logged. | rides 7.3 | Kevin (Strata bump) |

# 8. The harness and the instrument itself

Twenty-three proposals, and the theme with the best value-per-cost in the file: four of its six rows need
no engine at all, and one of them decides whether the other five can be believed.

| question | what is already established (note + date) | what is still open | the test that would settle it | cost | gated on |
|---|---|---|---|---|---|
| **8.1 Can the 414-check metric resolve the effects we now chase?** | **No, and it has not been able to for five weeks.** The metric is **saturated at 414/414 for both the reference stack and Strata** (`NEWS-2026-10-28` sec. 2.2) and "cannot resolve a 23% perplexity move", while teacher-forced perplexity resolved a **1%** one with byte-identical repeats. The pairing requirement is also established, from the other direction: `2610.37126` ranks a functionally inverted model (17.7% accuracy) as *less* damaged than random pruning, so perplexity alone must never be quoted (`NEWS-2026-10-29` item 4). The spec was written on 2026-10-28 (item 2: `STRATA_LOGPOS`, 8,192 forced positions, code/agent/prose split) and the pairing decided on 2026-10-29. | The instrument does not exist. This is the only place in the corpus where a *saturation* is known, a replacement is specified, and neither happened - while 40+ rows in the meantime were scored with the saturated instrument or not at all. | Build it: 8,192 forced positions, three text classes, byte-identical repeat check, and a task-level check beside it for every use. | a spec (exists) + one implementation | none |
| **8.2 What is the minimum detectable effect per workload, and is our n enough?** | Measured on our own arms: **prefill is resolvable at n=5, decode is not** - the two cell means are **+8.1% apart** with ranges **78.3-99.1 against 72.1-86.3**, i.e. overlapping across almost their whole width; across 30 arms prefill rises **21.4 tok/s per granted GiB (r = 0.58)** and decode **1.5 tok/s per GiB (r = 0.31)** (`CHUNK-LADDER-AND-RESERVE-2026-10-26.md`, Revision 2). Strata's own start-to-start spread is **8-28%** (`#1332`, `NEWS-2026-10-20` item 4). Our own first-request prefill artefact - **~99 tok/s then 50-60** - was recorded on 2026-10-20 and is now a precondition of every bump arm. | The *number* nobody wrote: a stated minimum detectable effect per workload. `NEWS-2026-10-16` item 3 proposed it as "a reporting rule, zero downloads" and it has never been adopted, so every later "won" claim is still judged by eye against a spread that is stated only in passing. | Take the n=5 prefill and n=5 decode spreads we already hold (they are in the note) and publish them as the lab's MDE per workload; then re-examine the claims that were made before them. | an afternoon of arithmetic on existing data | none |
| **8.3 Has the declaration become a substitute for the run?** | The mechanical fact: **82 of 224 shortlist items are edits**, **80 of them after 2026-10-28**, against 2 of 84 before. The template is at 0.2, twelve sections, a nine-rule start gate (`DECLARATION-TEMPLATE.md` sec. 9), a five-row build-boundary table (sec. 12), and a copy-paste block of **~60 fields**. Some of that growth is earned - every field added after 2026-10-28 names a defect that changed a reading. | Whether the marginal field buys resolution. Two test cases are already in the file and point opposite ways: the **sampling block** field (sec. 7) re-dates four rows and costs one line; the **prefill ring** field (`#6020`, +23.1% at 4K / +24.2% at 16K) is a *rate* effect that no field can capture - it needs an arm. The open question is the line between "declare it" and "run it", and it has never been drawn. | Classify the 60 fields: does each one *date* a row, *void* a row, or *substitute* for a measurement? The third class is the one to be suspicious of. | a reading pass, no engine | none |
| **8.4 Is a readout's provenance declared?** | `ollama ps` reported **2.50 GB** against **10,966 + 11,748 MiB**, and **851 MiB** against **8,127,397,888 B**, and printed **"100% GPU"** for a split model (`NEWS-2026-11-09` sec. 6.1). **Two of our own notes used it as evidence** (2026-10-09, 2026-10-20), so both need a dated correction line. The vendor's own audit found footer/monitor/console readouts reading up to **632 tok/s where the per-request line read 50-75** (`NEWS-2026-10-21`, now start-gate rule 10). | The two dated correction lines. This is a five-minute job that has been ranked second-to-third for six scans. | an edit | an edit | none |
| **8.5 Can contention be controlled, or only declared?** | One HN measurement says our gate is the **wrong shape**: a **budgeted** engine lost **9%** under +8 GiB of external load where a **configured** one lost **27%** (`NEWS-2026-11-10` sec. 9.1). And the lab's own record: **4 of 12 arms** lost to a render the gate could not hold on 2026-10-31. Later, on admission: throttling recovered **1 of 7** collapsed runs while **suspending admitted sessions against a capacity limit recovered all**, and a CPU offload tier only delays it (`NEWS-2026-11-11` sec. 8.1). | Which of the two mechanisms our one-slot configuration should use, and whether the contention test - one arm with a page-touching 4 GiB process, one without, interleaved - was ever run. Proposed twice (`NEWS-2026-11-10` item 7, `NEWS-2026-11-11` item 5), never carried. | 2 starts, ~15 min, no download. | 2 starts | none |
| **8.6 Is the decision track's ceiling a model problem or a screen problem?** | The track's only closed row: the native replay lands **14/18 correct at the frozen 0.85 threshold and catches 0 of 4 labelled stalls** (`SHORTLIST-2026-10-26-untried.md`, "What actually ran"; `NEWS-2026-10-21` sec. 8). Every neural model screened since has caught **0/4**. The abstention hypothesis was written and never tested: a "none of these" option in the label set, because *"a model that never abstains cannot be distinguished from one that is confident"* (`2610.29961`, `NEWS-2026-10-22a` item 5). | Whether 0/4 is the models or the screen. With no abstention arm, the two are formally indistinguishable - which means one published sentence about the decision track ("every neural model catches 0/4") currently supports no conclusion. | Add the abstention label to the existing 18-window screen and re-score the three models we already have on it. No new model, no download. | one replay per model | none |

---

# 9. Closed: questions the corpus answered, and the note that closed each

Recorded so they are not re-litigated. A closed row is **not** re-listed above.

| closed question | answer | closed by |
|---|---|---|
| Does the decision track's new native path reproduce the frozen fields? | No change in detection: **14/18 correct, 0/4 stalls caught**, 94 ms median | `NEWS-2026-10-20` (replay run); recorded as done in `NEWS-2026-10-21` sec. 8 and in `SHORTLIST-2026-10-26-untried.md` |
| What is the `--moe-cache-mib` curve and where is its admissible ceiling? | **47.4 -> 78.3 tok/s**, ceiling **5,376 MiB** at the ~2 GiB VRAM reserve (q2, q2c) | `SHORTLIST-2026-10-26-untried.md`; the shape first recorded `NEWS-2026-10-17` item 3 |
| Does Strata KV residency move our rate? | **7.6 -> 69.1 tok/s**, repeat 83.0 (q1) | `SHORTLIST-2026-10-26-untried.md` (q1) |
| Does engine 0.1.40.3 vs 0.1.47 change text or speed on our pack? | Neutral on both (q7) | `Q7-STRATA-BUMP-AB-2026-10-22.md` |
| Are our pack's routed-expert **down** projections Q4_K or Q6_K? | **All 40 at Q4_K** | `TENSOR-TYPES-2026-10-22.md`; closes `NEWS-2026-10-22a` item 1 |
| Is Colibri's `Q4_K is not named among the fast-path kernels` question closed? | Closed at **release** level, not by a reply: v2.1.0 ships **native GGUF block formats on CUDA for Qwen3.6/3.8 chains** | `NEWS-2026-10-31` item 7 |
| Does `--load-mode mlock` buy TTFT on our model? | **No-op for our model**; no buffer over 4 GiB | `TTFT-MLOCK-AB-2026-10-22.md`; retires items on `10-22`..`10-25` |
| How much WDDM shared segment does one resident arm consume? | **17.5-17.8 GiB**, reproduced twice, with commit free falling 25.7 -> 0.84 GiB. **The cap itself was not measured** - that half is row 4.1 | `WDDM-SHARED-SEGMENT-2026-10-22.md` |
| Does `STRATA_STAGE_TRIM=1` do anything on one card? | **No**, and the engine says why: `--trim-stage-weights needs a layer split across GPUs (ignored)`; `STRATA_ARENA_PIN_GIB` is a no-op for the same reason. Re-checked at 3000 slots: same cache, same chunk, lower free VRAM | `NEWS-2026-10-29` sec. 2.2 / item 2; `CHUNK-LADDER-AND-RESERVE-2026-10-26.md` Revision 2 |
| Is `--moe-cache-cpu-share` still blocked on an unmerged PR? | **No** - merged **2026-11-07T16:20:59Z**; the item changes from "needs a build from the PR" to "needs a download" | `NEWS-2026-11-08` item 5 (and `#29510`'s correctness prerequisite closed by the same merge) |
| Will the SLRU collapse be fixed? | **No.** `#30848` closed **unmerged 2026-10-27**, and v0.8.0 shipped the 50/50 policy anyway | `NEWS-2026-10-30` sec. 3.1 / item 1 |
| Is the 0.1.54/0.1.55 decode regression real? | **No.** Retracted by the reporter who filed it (`#4826`), with a second negative (`#4996`); carried as a bump-gate fact until 2026-11-02 | `NEWS-2026-11-02` sec. 1.1 / item 2 |
| Is `--prefill-borrow` a real switch on our line? | **Yes, and undocumented.** `--help` prints 266 lines and 0 hits for `borrow`; the binary contains `--no-prefill-borrow` | `DECLARATION-TEMPLATE.md` sec. 8, from the 0.1.47 asset read on 2026-11-09 |
| Does `STRATA_KVA` exist in 0.1.47? | **No** - no string in the binary, so the Q2_0 + KVA crash cannot fire on our line; the VOID rule is armed for >= 0.1.55 | `DECLARATION-TEMPLATE.md` sec. 8 (2026-11-09); rule 2 of sec. 9 |
| Can KV be made lazy, so experts are placed first? | **No.** `#32170` closed **unmerged 2026-11-15T12:13:36Z** on doctrine - *"a fixed amount of memory once, without subsequent increases"* - so 0.77 GiB at 65,536 stays the price | `NEWS-2026-11-15` (and start-gate note in `DECLARATION-TEMPLATE.md` sec. 12) |
| Was the 2026-10-26 chunk-ladder "withdrawal" real? | **No.** The spread was the **RAM state, not the flags**; and on our pack the engine's own chunk is worth **+7.7 / +8.1 / +8.3% prefill** in three cache-matched groups, the reserve **+0.5-4.4%**, and decode is **not resolvable at n=5** | `CHUNK-LADDER-AND-RESERVE-2026-10-26.md` Phase 2 and Revision 2 (measured 2026-10-27) |
| Which tag first carries `#31775`, so that `-nkvo` + `--moe-cache-mib` is legal? | **`b12383`**, published 2026-11-14T14:43:25Z, `compare/c56be864f...b12383` -> behind 0, and no `b12382` exists. VOID below it | `NEWS-2026-11-15` item 1; `DECLARATION-TEMPLATE.md` sec. 12 |
| Is a new engine's "no speed difference" claim safe to take? | **No.** `#3189` measures 0.1.46 as identical to 0.1.45.3 on a single RTX 50, so pin 0.1.46 deliberately - there is no speed argument either way (`NEWS-2026-10-20` item 6). Superseded in practice by the 7.3 gate, kept because it is the reason no bump has ever been justified on speed | `NEWS-2026-10-20` item 6 |

# 10. Not closed and not open: items that were absorbed, or lost

An item that stops appearing is not the same as an item that was answered. Three fates are visible in
the corpus and only the first is legitimate.

**Absorbed into the gate (legitimate - a field replaced a run).** The cliff test (`10-22`..`10-26`) became
start-gate rule 7. The declared-vs-granted readback became rules 7 and 8. `--moe-cache-cpu-share`'s
precondition became "the fill state must be declared". The `-nkvo` boundary became sec. 12. Each of these
is fine *because the thing it replaced was a declaration check*.

**Absorbed into a note as a witness (questionable).** The **pinned-vs-fresh copy microbench** (`#3321`,
`10-24` item 2, `10-25` item 2) - six cells at 256 MiB, **pinned reused 26.3 GB/s, pageable reused 21.3,
pageable fresh 2.28, fresh pre-touched 22.3** - asked "is our decode at 60-70% of measured bandwidth
because of kernels or because of page faults", and it would have changed what a `--moe-cache-mib` rung
*means*. It was folded into the WDDM note as one more witness and never run. **A rate question cannot be
absorbed into a field**; this is the clearest instance of 8.3's problem.

**Lost without a reason.** Unlike the notes from `10-22` onward, which record drops explicitly ("Dropped,
with reasons, so they are not re-researched"), three items simply stop:

- **`H2O-Lightning-4B` then `pplx-decider:27b`** on `/v1/systemone` - carried `10-21` (items 3 and 4) and
  `10-22a` (item 5), last mentioned `10-28`/`11-05` in passing. This was "the cheapest genuinely new row
  in the track" with an independent **231-task agreement check** behind it, and it is not in any "dropped"
  list. The decision track's remaining arm is therefore missing from every later shortlist by omission.
- **Routing-entropy hot-set prediction** (SPARE, `2610.29662`) - carried `10-22`, `10-23`, `10-24`, then
  gone. Row 2.5 above keeps it alive because it is the cheapest unrun question in the corpus.
- **The Colibri arithmetic bracket** (`88.4-89.1%`, `10-17`..`10-22a`) - carried as "also owed, not
  ranked" on six notes and then dropped when Colibri stopped releasing. It narrowed a bracket rather than
  answering a question, which is why it was always last, and it is now nowhere.

---

# 11a. Status, 2026-11-15 evening: question 2 answered, question 1 answered

**Q2 - answered, and the row it asked about inverted.** MTP pays wall clock on `b12383`: **-10.08 % end-to-end wall,
+11.21 % throughput**, acceptance **57.71 %** (161/279), five starts with disjoint ranges. The 2026-10-08
`+31.2 %/token, -7.3 % wall` row was **a property of b11461**. Costs found with it: drafter raises prefill **+21.9 %**
and costs **~1,043 MiB VRAM / ~1.1 GiB commit** (`DECLARATION-TEMPLATE.md` sec. 5).

**Q1 - answered as outcome 2: the curve differs and no low rung is below the control.** On `b12383`, 512 MiB is
**+29.5 % over its own control** at **0.9 tokens worth** with **28.95 % hits**; the elbow is **4096** (+96 %) and 6144
is admitted and buys nothing. So **"512 MiB is a dead zone" and the 5,376 ceiling are `b11480` facts**, and the cache
work closes at this rung set (`CACHE-CEILING-2026-11-15.md`). Two caveats stay: no `b11480` arm ran today, and the
plateau past 4096 is not explained by the hit rate.

**Q3 - the free half is closed (2026-11-16); the positive half needs a download.** Neither publisher declares calibration:
`ggml-org`'s README is 483 bytes, ISTA's 16,649 bytes document GSQ/RCO but no calibration corpus. So the tie **may
not be quoted as a property of bit-width**, and answering whether calibration explains it needs a pack chosen **for
a declared calibration**, not for its bit width (`KNOWLEDGE-DEEP-2026-10-10.md`, 2026-11-16).

# 11. The three questions this lab should answer next

The table order above is not the answer. Value does not sit where the proposals are densest - theme 2 has
56 proposals and theme 8 has 23, and it is theme 8's saturated instrument that decides whether any of
theme 2's 56 can be read. What follows is the argument for three, and each one carries the thing that
makes it a question rather than a task: **what changes in our recorded numbers if the answer goes either
way.**

### First: what is a bigger expert cache worth in *tokens' worth*, on a build that proves it engaged?

Everything the lab calls its main lever rests on one ladder taken on **b11480**, a build with **LRU**,
before `#30637` moved the policy to 50/50 SLRU at `b11732` and before the `tokens worth` line existed.
The measured shape is 47.4 -> 78.3 tok/s with an admissible ceiling at 5,376 MiB, and it is quoted in
every resident row we hold. Upstream has since published the same knee twice in units we can convert:
`#31421`'s collapse at **exactly 1.0x**, and SLRU at **240 slots** reading **0.6% hits / 8.8 tok/s against
LRU's 37.5% / 12.9**. Our rungs convert to **0.47 / 0.95 / 1.90 / 3.79 / 7.59 / 9.96**, which puts our
dead zone at 512 MiB *inside* the band upstream calls catastrophic - and our ladder ran on a build where
that mechanism could not fire. So the question is not "how big should the cache be"; it is whether our
ceiling is the pack's or b11480's.

If the answer is **the pack's** - the curve reproduces on a logging build at n>=5, with granted slots and
fill state declared - then the last six weeks of cache work closes, `q2`'s ceiling stands as a property of
a 66 GB pack on 12 GB of VRAM, and the CPU share (2.2) becomes the only remaining lever worth a download.
If the answer is **b11480's**, then two published claims change meaning at once: the 5,376 MiB "admissible
ceiling" is an artefact of a policy nobody runs any more, and the 256/512 MiB rungs that sat *below the
no-cache control* were measuring the SLRU collapse rather than the pack's own arithmetic. That second
outcome is the more likely one on the evidence we already have - our dead zone lands on the same knee in a
different unit - and it is the reason this is the first question rather than a maintenance item: **it
decides whether a row we quote is a property of hardware we own or of a build we replaced.**

### Second: is MTP a wall-clock win on this card, now that the verify step has been made cheap?

This is the corpus's own most uncomfortable finding and it was made eight minutes after a note had closed.
Our only speculative row says **+31.2% per token, -7.3% wall, +21.7% tokens, accuracy unchanged**, on
**b11461**. `#31533` - "CUDA: few-row MMQ for BS 2-24", merged 2026-11-12, in `>= b12359` and not in
`b12208` - was invisible to every scan until 2026-11-15, and a proper interleaved benchmark on it reads
**+52% / +55% with MTP on v1.0.0** at **unchanged acceptance of 32-33%**. That is a kernel that makes the
*verify* step cheaper, which is precisely the term that made our wall clock negative while the per-token
cost stayed positive. We have been quoting "-7.3% wall" for five weeks against a build that could not
have shown anything else.

If the answer is **a gain**, then the row does not merely update: it inverts, and the lab's only
speculative statement becomes "we left a wall-clock gain on the floor because we never checked whether
our build had the kernel that prices the verify step". If the answer is **still a loss**, that is a
stronger result than the one we hold, because it would mean the tax is in the drafting or the
acceptance structure rather than in the verify kernel - and the one datum that supports this reading is
already in hand: the **14-22%** component needs **4 concurrent slots**, which our `--parallel 1` cannot
reach, while the **+52%** component does not. Either way this question is decided by two starts and it
rides the same download the first question needs, which is why the two are proposed together: **one
granted llama.cpp build at `>= b12383` settles the cache ceiling and the MTP sign, and those are the two
rows most likely to be wrong today.**

### Third: does calibration text explain the knowledge gap we have been reporting as a tie - or does it
mean the tie cannot be quoted?

The lab's knowledge result is **88.5% vs 89.7%** on 1,100 items, read since 2026-10-10 as "the same
knowledge, so ask the next question". On 2026-11-15 an input arrived that the file had never declared:
task-informed calibration is worth **+1.83 pp** mean ten-task accuracy at two bits, the recovery
**concentrates on families included in calibration**, deliberately wrong labels retain about **90%** of
the gain (so part of the effect is circular), and **reconstruction error does not track accuracy** - which
is why a perplexity, an MSE or a file size cannot stand in for the field. Our 89.7% stack is a **2-bit**
pack, **neither publisher declares its calibration text**, and the paired SE on these items is **1.33 pt**.
An effect of ~1.8 pp is larger than the 1.2-point gap *and* larger than the instrument's own error bar.

If the answer is **calibration explains it**, then the tie is a property of two specific packs and not of
two bit-widths, and the sentence "two bits equals four bits on this model" - which the lab has been
entitled to say since October - becomes unsayable. If the answer is **it does not**, the tie hardens into
a result about the model family rather than about the packs, and it becomes worth the download of a
4-bit pack whose calibration is declared. But note the third possibility, which is the reason this ranks
above the WDDM cap correction (4.1) despite costing more: **the pessimistic version of this question is
already answerable for free.** Both stacks' `pack_calibration_text` fields read `UNVERIFIED` today, so
restating the null as *"not measured"* costs one edit and retires the 2-bit-equals-4-bit reading without
any engine time at all. A question whose cheaper half is an edit and whose expensive half is a download is
exactly the shape this lab's queue should be in - and it is the only one of the three whose free half can
be taken today.

---

## Provenance

- **Read for the tables**: all 36 `NEWS-*.md` shortlist and "Gated on Kevin" sections (line numbers in
  the citations above are the section starts, e.g. `NEWS-2026-10-17.md:313`); the four early notes'
  proposal sections (`NEWS-2026-10-05.md:150`, `NEWS-2026-10-08.md:49`, `NEWS-2026-10-14.md:106`,
  `NEWS-2026-10-16.md:364`); `SHORTLIST-2026-10-26-untried.md`; `AGENTS.md`'s dated entries, read as a
  state register for closing statements; `DECLARATION-TEMPLATE.md` (all twelve sections);
  `CHUNK-LADDER-AND-RESERVE-2026-10-26.md`; `RESIDENT-ABOVE-8-2026-11-01.md`;
  `WDDM-SHARED-SEGMENT-2026-10-22.md`; `KNOWLEDGE-DEEP-2026-10-10.md`;
  and, for the closed rows, `Q7-STRATA-BUMP-AB-2026-10-22.md`, `TENSOR-TYPES-2026-10-22.md` and
  `TTFT-MLOCK-AB-2026-10-22.md`.
- **Counted**: 36 notes, 32 headed shortlists, 224 numbered proposals, plus 21 in the four early notes and
  21 in `SHORTLIST-2026-10-26-untried.md` - **266 in total**. The "Dropped, with reasons" and "Not ranked,
  and why" lists that close the notes from 2026-10-22 onward were read but are not counted, because a
  dropped item is not an open question and is not listed as one.
- **Deliberately left out**: the image track (`IIMAGE-*`, `ComfyUI` arms, `MAGNITUDE-2026-10-17.md`),
  which is a second lab with its own queue and its own gates - its two live items (the `--disable-pinned-memory`
  pair and the cast-buffer pin) appear above only where they bear on a Windows memory contract we share.
  The September notes and `goproverbs` (a separate project, different instruments). The decision track's
  model landscape, beyond the one closed row and the one orphaned arm. `C:/Users/kevin/harness-lab/docs`
  (4 files: a worker dashboard, GitHub Projects, parallel workers, UI conventions) was read and carries no
  overlap with this agenda beyond "the ledger is the source of truth, a board is a view" - a rule this
  lab already keeps.
- **Not asserted**: any upstream number not already recorded in our notes. Where a figure appears above it
  is quoted from the note that holds it, with that note's date, and has not been re-verified against the
  upstream source this week.
