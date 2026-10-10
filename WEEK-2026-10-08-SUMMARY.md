# The week of 2026-10-05 to 10-08: what changed, what it cost, and what is still open

Written overnight 2026-10-08 for the morning. Every number here is measured on this box; the primary
sources are `ai_bench/new-items-20261007/REPORT.md` (the week's main report),
`local-llm-lab/HARNESS-TWEAKS-2026-10-08.md`, `local-llm-lab/NEWS-2026-10-08.md`,
`local-llm-lab/BESPOKE-METRIC-2026-10-08.md` and `local-llm-lab/TASK-DISCRIMINATION-2026-10-08.md`.

## 1. The platform changed, and it was the wrong thing to blame

The RAM module landed: **64 GB, DIMM2, dual channel verified, 5600 MT/s, no down-bin**, all gates
unchanged. What the extra headroom bought is real but narrower than expected: Kolibri-1 78B runs at
~34 tok/s with 9.8 GiB still free, Qwen3.6-35B-A3B at 38-50 tok/s with ~24 GiB free, and both hold 262k
context. What it did **not** buy is a way to run gpt-oss-120b: every published 120B build is 62.6-65.4 GB
(the MoE experts are native MXFP4 and are not requantized - the whole "Q2_K to Q8_0" spread is 0.83 GB),
which is 58.26 GiB against 58.46 GiB usable, and a 32k KV puts it ~1.4 GiB over the line. Recorded and
closed in `ai_bench/queue-20261008-gpt-oss-120b/`.

## 2. The correction that mattered: half of our own failures were not the model's

A whole-history census classified all 178 then-324 sessions on disk: 94 perfect, 44 ended-normally-wrong,
**23 replies truncated inside their thinking** (`stopReason=length`, no tool call - which ends an agent
loop) and 17 external kills. A wider pass over 99 sub-perfect sessions split them as **50 prose-quit /
27 truncated / 18 killed / 4 error**, and the prose-quits are *completion summaries* ("Solution complete",
plus a bullet list) written while 1-8 hidden checks still failed - i.e. **model self-verification**, not a
harness misread. Harness and platform account for **45 of 99 (45 %)** of sub-perfect sessions, and the
lab's historical "reliability" numbers were roughly half measurement.

The single cleanest demonstration: **Swift Bonsai 2 PQ2 scored `ledger` 7/70 and `ledger2` 226/226 in the
same sweep** - and `ledger2` contains those same 70 checks byte-identical. The wire shows its third turn
using exactly 12,288 of a 12,288-token allowance, no tool call, loop ended.

## 3. Four fixes, each measured

| fix | evidence |
|---|---|
| per-response cap 12,288 -> 32,768 | MiniCPM5-2B **217/221** with `paths` 75/75 (it collapsed to 9/75 twice before); gpt-oss-20b 214/221; both 0 % collapse rate, from 33 % |
| Strata `reasoning_budget_tokens: 6144` | **10/10 at 70/70**; the engine's truncation diagnostic still fires in 2 of 10 and **costs nothing** - the budget moves the cut after the work |
| context 32,768 -> 131,072 (llama.cpp server **and** host descriptor) | `n_ctx_slot = 131072` in every session log, `config/models.yml` 131072/32768, no hang; the six context witnesses cannot recur |
| Strata `--max-context` 32,768 -> 65,536 | `context 65536 tokens`; 4 of 5 ledger runs at 70/70, zero diagnostics - at ~5 GiB of RAM cost, traced to the context-sized prefill buffers |

Plus `quota_unknown` declared non-fatal in **two** layers: the candidates runner's sweep guard, and -
the one that actually killed sessions - **the relay's `Budget`**, because the harness terminates on
`budget.failure` and this engine intermittently reports no usage. That single gap cost a 64k Strata run
mid-turn (169 s, empty `final_text`, exit 143).

## 4. Three instruments, each verified before use

- **`ledger2`, 226 checks** (the frozen ledger plus 106 labelled traps and 50 more random valid ledgers).
  Verified: reference **226/226**, the task's own buggy starter **62/226**.
- **`repo`, 78 checks**, a five-file cross-module repair (varint + store + README + public tests + shim).
  Verified: reference **78/78**, starter **43/78**.
- **`longctx`, 40 checks**, a 222 KB / ~65k-token module of 1,800 helpers with one wrong function and a
  minimal-edit rule. Verified: reference **40/40**, starter **15/40**; and the scorer was made linear
  (63 s -> 0.32 s) after noticing the relay kills a scorer at 30 s - it would have zeroed every live run.

## 5. Which checks still discriminate (the saturation question, answered with a count)

Method: check-level pass rates over every artifact on disk, point-biserial against the **leave-one-out**
total, restricted to artifacts at >= 90 % of the task's best score. Counts refreshed 2026-10-09 in a
final pass (six-task suite + variance repeats + n=3 samples + the Strata runs); the split counts moved
only in the tail. `repo2`, `perf` and `longctx2` now have two artifacts each and still no analysable
checks - the script reports a case only once it has >= 3 observations:

| task | artifacts | checks | splitting in top group | leading check |
|---|---|---|---|---|
| `events` | 71 | 76 | **6** | case 11 (59/64) |
| `paths` | 63 | 75 | **3** | case 23 (57/62) |
| `ledger` | 105 | 70 | **15** | **case 19 (64/93)** |
| `ledger2` | 190 | 226 | **43** | **case 140 (85/147)** |
| `repo` | 33 | 78 | **9** | case 63 (21/25) - two clusters now |
| `longctx` | 24 | 40 | **0** | - |
| `repo2` / `perf` / `longctx2` | 6 / 7 / 6 | 55 / 33 / 40 | 0 in the top group | the filter hides their cross-model separation by construction |

Two things to carry: `ledger2`'s single most-failing check is **case 140**, not case 19 (the display
used to sort by case number and cut the list at 14, which hid everything above 76 - fixed on 2026-10-09);
and the growth is confined to the tail (ledger cases 8 and 10 and paths case 13 each now show one
failure), while the five dominant ledger checks and `repo`'s UTF-8 byte-length class are unchanged.

So `events` and `paths` cannot rank the top group and should be retired or replaced; `ledger2` tripled
the live checks over the frozen ledger; `repo` discriminates on exactly one bug class; `longctx` as built
measures nothing among competent models.

## 6. The ranking, and the reference configuration

**Ranking convention since 2026-10-09:** `events` and `paths` are retired from ranking (they split on
5/76 and 3/75 checks in the top group, so they absorb budget and manufacture ties). The metric below is
the discriminating subset - **ledger 70 + ledger2 226 + repo 78 + longctx 40 = 414 checks** - and every
row carries the context it was served. Regenerate from the roots' own evidence with
`ranked_table.py` (writes `ranked-20261009.json`).

| configuration | ctx | ranked / 414 | six-task | agent s |
|---|---|---|---|---|
| **Qwen3.6-35B-A3B (nine-task run, 2026-10-09)** | 131,072 | **414/414 = 100 %** | 565/565 | 2,708 |
| **Strata qwen3.8-flash-next-coder Q2_0 (streamed, 4 GiB resident)** | 65,536 | **414/414 = 100 %** | 565/565 | ~1,100 |
| Qwen3.6-35B-A3B + provisioning (repeat) | 131,072 | 411/414 = 99.3 % | 562/565 | ~1,700 |
| Qwen3.6-35B-A3B + provisioning (first) | 131,072 | 400/414 = 96.6 % | 551/565 | 1,642 |
| Kolibri-1 78B + provisioning (twice, identical per task) | 131,072 | 400/414 = 96.6 % | 551/565 | 2,971 / 2,877 |
| **Nemotron-3.5-Lightning-30B + provisioning (2026-10-09 / earlier)** | 131,072 | 394 / 393 = 95.2 / 94.9 % | 545 / 544 | 3,304 / 3,377 |
| **MiniCPM5-2B (nine-task, 2026-10-09)** | 131,072 | **392/414 = 94.7 %** | 540/565 - nine-task **656/693** | 1,534 |
| **Nemotron-3.5-Lightning-30B (nine-task, 2026-10-09)** | 131,072 | **388/414 = 93.7 %** | 539/565 - nine-task **620/693** | 4,709 |
| **Swift Bonsai 2 PQ2 - EXEMPT** | **32,768** | 379/414 = 91.5 % | 530/565 | 1,926 |
| **gpt-oss-20b (repeat)** | 131,072 | 377/414 = 91.1 % | 528/565 | 931 |
| **MiniCPM5-2B (third run)** | 131,072 | 374/414 = 90.3 % | 522/565 | 1,110 |
| **gpt-oss-20b (nine-task, 2026-10-09)** | 131,072 | 306/414 = 73.9 % | 457/565 - nine-task **549/693** | 1,626 |
| MiniCPM5-2B | 131,072 | 305/414 = 73.7 % | 456/565 | 1,534 |
| gpt-oss-20b | 131,072 | 283/414 = 68.4 % | 432/565 | 953 |
| **Swift Bonsai 2 PQ2 (nine-task, EXEMPT)** | **32,768** | 250/414 = 60.4 % | nine-task **508/693** | 2,937 |

Four rows carry the *nine-task* loop (they include `repo2`, `perf` and `longctx2`; the rest are six-task runs).

Two older rows are not ranked here because they lack `longctx`: Nemotron 5-task unprovisioned
(516/525) and Swift 5-task unprovisioned (427/525).

**Strata is a different engine** and appears here because the same nine batteries ran on it for the
first time on 2026-10-09 (`strata-newtasks-20261009-v2`, read `new-items-20261007/REPORT.md`). Its ranked
and six-task subtotals are **perfect** and its nine-task total is **692/693**, cell-for-cell identical to
Qwen3.6's best, at ~1,100 s for the six tasks. So a Q2_0 pack streamed from disk with a 4 GiB resident
budget matches a fully resident 35B-A3B Q4_K_M on this suite; the wall times are not strictly comparable
across engines (Strata serves from its own expert cache) but the scores are, because the batteries,
workspaces and scoring path are the same.

Qwen3.6's repeat is the best llama-server six-task sweep recorded before the nine-task run (562/565,
all six tasks clean: events 76, ledger 69, paths 75, ledger2 224, repo 78, longctx 40) - and the
nine-task run reached 565/565 on the same six.
Nemotron's provisioned run replaced its own `repo` 75/78 with **78/78** and its `ledger2` 223 with 209.
**An earlier version of this paragraph called Kolibri's `ledger2` 226/226 -> 212/226 a context effect;
the targeted repeats refuted that** - at the same 131,072 context Kolibri scores 226/226 twice when
`ledger2` runs first in the loop (`newtasks-rep-20261009-k1/k2`), so the variable is loop position or
plain variance. The repeats also settle which battery can rank: over all runs, `repo` is reproducible
(Kolibri 78/78 four times, Qwen3.6 78/78 five of six, Swift 43/78 twice) while `ledger2` is not
(Qwen3.6 spans 207-226 over six runs, spread 19; Kolibri 212-226 over five, spread 14) - so any
single-run `ledger2` gap below ~19 checks is noise. Swift's row is the exemption at work: at a
32,768 window it reaches `ledger2` 226/226 and `longctx` 40/40, and its old 7/70 frozen ledger became
**70/70** once the reply cap was raised - that collapse was harness truncation, not the model. Its
`repo` is 43/78 in both runs: genuinely single-file.

Its **context ceiling is now measured, not assumed** (`ctx_ladder.py` over every Swift root, plus a
65,536 attempt on 2026-10-09): 32,768 holds 0.69-1.28 GiB GPU free, while 65,536 tripped the monitor
after 24.8 s at **0.31 GiB** *before the model finished loading* and 131,072 bottomed at 0.49-0.50.
The crossing is a **load-time** GPU peak, not a generation-time cache: comparing `max_gpu_used` across
the 32k/131k runs (10.38 -> 11.18 GiB) is what made an earlier note predict 65,536 would fit. Physical
RAM (34.4 GiB free) and commit (33.5 GiB) were never the constraint. So Swift runs at 32,768 or not at
all under the lab's 0.5 GiB floor.

**Recommended reference config: Qwen3.6-35B-A3B Q4_K_M with the provisioning** (reply cap 32,768,
context 131,072, `--reasoning-budget 6144`) - the joint accuracy-and-speed winner: it passes `repo`
(78/78) and `longctx` (40/40) at 1,330 s, where the only other configuration to pass both, Kolibri, needs
2,877 s. Kolibri is the accuracy leader on the finer ledger; Swift is single-file only (repo 43/78).
**gpt-oss and MiniCPM are the two widest spreads in the family**, and the repeats moved both a long way
up: gpt-oss 432 -> **528**/565 (its `repo` went 0 -> **78** and `longctx` 15 -> 29) and MiniCPM
456 -> **522** (its `repo` 0 -> **68**). So "gpt-oss is the fastest and fails every hard axis" was an
n=1 reading - at n=3 it is weak on the ledger traps and *capable* of the multi-file repair; MiniCPM's
quota doubling was called "worse" by an earlier note, which its third run also refutes (456 and 522
against 445). For this family a single run misleads in both directions, so the table above should be
read as samples of a distribution, not as a ranking of capabilities.

### The nine-task loop (2026-10-09)

`newtasks-ext-20261009-v12` (Qwen3.6, the reference config, 2,707.5 s, no error) ran every battery
built this week - the six above plus `repo2`, `perf` and `longctx2`:

- **565/565 on the six-task suite, every task clean and correct - the first perfect six-task sweep.**
- `repo2` **54/55**: the only discriminating task in the run. Its single miss is case 27,
  `class2/unknown-kind-raises` (the per-instance registry was built, but `register('nope')` was not
  made to raise). Four labelled defect classes (22/6/5/7 checks) replace the old `repo`, which split
  on three checks of one class.
- `perf` **33/33**: `merge` handled 2,000,000 intervals inside a wall stated *relative to the
  reference*. This is the only battery in the lab that prices engineering judgement - a
  correct-but-quadratic implementation passes everything else.
- `longctx2` **40/40**: all nine planted frame-length sites found, each agreeing on ASCII so the
  public tests stay green.
- Nine-task total **692/693**. At n=1 the three new batteries are "no failure observed", not
  saturated; they join the rate aggregate as samples accumulate.

## 7. Engines and outside work

- **Strata 0.1.41 staged and A/B'd** (15 runs, all 70/70): the upgrade alone is **neutral** (cold prompt
  636 vs 632 tok/s, per-request 68.8 vs 70.3, cache 49.3 % vs 48.5 %) and holds **2,425 GPU-cached experts
  against 2,407** - adopt it for the hung-engine watchdog and `<function= NAME>` parsing, not for speed.
  `--expert-cache 1500` is a **regression** here (579.6 vs 615.9-657 cold prompt, 41 % vs 49 % hit rate);
  `STRATA_ROUTE_RESIDENT=1` shows no gain on a prefill-bound workload. The headline "prompts ~2x faster
  on Windows when the model is bigger than RAM" targets disk-bypassing reads; ours is RAM-bandwidth bound
  at ~630 tok/s, and the disk-streaming configuration is below our 3 GiB floor.
- **The agent metric that matters is prefill.** Measured across 21 sessions: **43.6 tokens read per token
  written** (10.3 M read / 237 k written, 493 model calls) - twice the ratio in the reference video, and
  `longctx` is 53-321:1 by design. Any engine work that only speeds decode barely moves our task walls.
- **llama.cpp b11512** (2026-10-08) fixes DFlash output-head sharing; DFlash is one of the draft heads
  staged for Qwen3.6. **Ollama v0.40.1** fixes "clef head reads past 2GiB on windows" (a decision-model
  family we staged). **IQ3_XXS** - the 3-bit coding build both videos recommend - needs 75.84 GB of GGUF
  plus a derived pack, i.e. it only fits if the Q2_0 weights (62.7 GB, re-downloadable) are deleted.
- The community nudge fix (OpenHands #3992/#3997) was **not adopted**: our prose-quits are completion
  summaries, so a nudge would mostly get "DONE" back, and the narrow trigger it would help is already
  covered by the cap raise and the thinking budget.

## 8. The decision suite's open anomaly is closed - and the metric flips the ranking

The `civil_comments` +20-point anomaly was a **metric artifact**: the subset has 32 positive of 300
(majority baseline **89.3 %**), so our 91.0 % is the baseline plus 1.7 points, and our **balanced
accuracy is 72.9 %**, matching the published 70.3 % to 2.6 points - the same band as every other subset.
Consequence: under balanced accuracy **kev4 4B takes the top spot from nimble 9B** (0.805 vs 0.797) and
`lev` moves +10.6 points. Recommendation: report balanced accuracy plus prediction rate for binary
subsets, and stop averaging the `score`-type subsets (argmax accuracy on a 5-point scale) into the same
macro as binary accuracy.

## 9. Open decisions for Kevin

1. **IQ3_XXS for the Strata coding track** - delete the Q2_0 weights (62.7 GB, re-downloadable) to make
   room, or skip. It is also the *full* 125B, not the Coder prune, so it supersedes those baselines.
2. **Retire `events` and `paths` from ranking** (5 and 2 live checks) or replace them with harder
   variants - they are a third of every sweep's wall time for a constant.
3. **Declare Qwen3.6 + provisioning as the reference config** (and keep Kolibri as the accuracy track).
4. **The 6 GiB worker-private cap** that blocks `nimble` on the decision track (`moe-screens`/decisions):
   keep it and end the track, or amend it in a new root for the GPU decision-server track.
5. **Does the Ollama clef fix change the decision track's numbers?** (its serving path moved under us).

## 10. Method lessons, all paid for this week

- **Attribute a failure before counting it.** An engine's own log line plus the per-turn `stopReason`
  turned "50 flaky models" into "45 % harness, 50 self-verification, 4 transport" for ~180 lines of
  read-only analysis.
- **`clean_finish`, `exit 143` and `quota_unknown` are not failure signals here** - they appear on 70/70
  runs. Correctness is `evaluation.passed`.
- **A saturated task is worse than none**: it consumes wall time and manufactures false ties. Quote the
  live-check count beside every score.
- **Verify the instrument before spending GPU time**: reference-vs-starter for every new battery, and a
  timing check on the scorer (63 s vs the relay's 30 s limit would have zeroed a whole batch).
- **State is shared in ways that bite**: the engine config file is shared across roots, so an arm that
  does not declare a value inherits the previous arm's - arm C's first batch was silently arm B.
- **Never launch a batch with a bare shell `&`** - it is reaped when the tool call returns; use the
  harness's background jobs, and recompute metrics from artifacts when a record is lost.
- **Check a metric's baseline before comparing to published numbers**: on the decision suite, 89.3 % of
  one subset is the majority class, which is where a 20-point "anomaly" came from.
