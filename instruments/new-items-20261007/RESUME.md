# RESUME 2026-10-09 - the six-task suite, per-model provisioning, and Swift's exemption

Written 2026-10-09, after the last run finished. Read with `new-items-20261007/REPORT.md` (the full
record) and `local-llm-lab/AGENTS.md` (the changelog). Every number here is measured; the two places
that are inference are marked.

## State at this writing (verified, not assumed)

- Platform: **64 GB DDR5-5600 dual channel**, 63.46 GiB visible (DIMM1 SK hynix HMCG88AGBUA084N plus
  DIMM2 Kingston 9905782-147.A00G), both configured 5600, no down-bin.
- **One serial chain is in flight (`bg_81`)**: nine-task sweeps for Kolibri / Nemotron / MiniCPM /
  gpt-oss / Swift, then position-controlled `ledger2` repeats for Kolibri and Nemotron, then the Strata
  `perf` + `longctx2` at 2 GiB in `strata-newtasks-20261009-v6` (the v5 sweep stopped after its `repo2`
  session hit the harness's 30 s scorer timeout, and re-scoring that artifact outside the harness ran
  the full 600 s with no output - the artifact **hangs** the battery, so the cell is a recorded failure
  of the model's output, not a gap). The chain's current root holds the only `RUNNING.lock`; no engine is left
  resident by a finished run; ports 11435 / 11436 / 8080 free. Port 11434 is Ollama, idle.
- **The declared cap removal cost two incidents, both fixed and recorded.** (i) The monitor module is
  pinned by digest in every root's 120-file manifest, so roots built afterwards refused to run
  (`verify()` is the freeze doing its job). The builder now **re-pins deliberately** and records
  old -> new digests in `evidence/pin-change.json`; verified 120 pinned / 0 mismatches in each rebuilt
  root. (ii) A `model`/`name` NameError of my own killed seven invocations before they started; fixed,
  and the failed roots are preserved as `newtasks-*-fail-pin-20261009`.
- Free physical **41.4 GiB**, GPU dedicated **1.42 GiB**. Every gate passes with room.
- **Gates**: initial 9 / 8 / 7.5 GiB and the runtime floors 3 / 2 / 0.5 GiB are unchanged; the
  **6 GiB worker-private cap is removed** (2026-10-09, declared - see "Ranking metric" above), and the
  warm p95 3 s gate is untouched. `.wslconfig memory=8GB` unchanged. No app closed, no reboot, no
  startup change.
- One inference workload at a time, throughout.

## What ran

**Ranking metric since 2026-10-09 (declared, on Kevin's instruction):** `events` and `paths` are retired
from ranking (they split on 5/76 and 3/75 checks in the top group), so the metric is the discriminating
subset `ledger + ledger2 + repo + longctx` = **414 checks**, and every row carries its context
(131,072 local, 32,768 Swift, 65,536 Strata). Regenerate with `ranked_table.py`. Two rows are perfect:
Qwen3.6 `ext-v12` **414/414** and **Strata 414/414**; then Qwen3.6 411, Qwen3.6/Kolibri 400, Nemotron
394/393, Swift 379, gpt-oss 377, MiniCPM 374, and the two weakest models' earlier runs at 305/294/283.
The **6 GiB worker-private cap is also removed** (`WORKER_PRIVATE_CAP_GIB = None`) with the eligibility
gate, the floors (3/2/0.5 GiB) and every historical record unchanged. Both changes are declared in the
report, the changelog and the week summary.

The table below is the six-task view: 565 checks = events 76 + ledger 70 + paths 75 + ledger2 226 +
repo 78 + longctx 40.
Baselines (32,768, no provisioning) are the `newtasks-20261008-v*` roots; the rest are `-ctx-`.

| Root | Model | Wall | Score | ev | led | pa | led2 | repo | lctx |
|---|---|---|---|---|---|---|---|---|---|
| **ext-v12** | **Qwen3.6-35B-A3B - nine-task loop** | **2,707 s** | **565/565** (+repo2 54/55, perf 33/33, longctx2 40/40) | 76 | 70 | 75 | 226 | 78 | 40 |
| ctx-v8 | Qwen3.6-35B-A3B | 1,330 s | **562/565** | 76 | 69 | 75 | 224 | 78 | 40 |
| ctx-v1 | Qwen3.6-35B-A3B | 1,642 s | 551/565 | 76 | 70 | 75 | 212 | 78 | 40 |
| 20261008-v1 | Qwen3.6 (32,768) | 1,195 s | 502/525 | 74 | 66 | 75 | 212 | 75 | - |
| ctx-v4 | Kolibri-1 | 2,971 s | 551/565 | 76 | 70 | 75 | 212 | 78 | 40 |
| ctx-v9 | Kolibri-1 (repeat) | 2,877 s | 551/565 | 76 | 70 | 75 | 212 | 78 | 40 |
| 20261008-v6 | Kolibri-1 (32,768) | 2,150 s | 524/525 | 76 | 69 | 75 | 226 | 78 | - |
| nemotron-r1 | Nemotron-3.5-Lightning-30B | 3,303 s | **545/565** | 76 | 68 | 75 | 208 | 78 | 40 |
| ctx-v7 | Nemotron-3.5-Lightning-30B | 3,377 s | 544/565 | 76 | 66 | 75 | 209 | 78 | 40 |
| 20261008-v4 | Nemotron-3.5 (32,768) | 2,758 s | 516/525 | 76 | 67 | 75 | 223 | 75 | - |
| **ctx-v11** | **Swift Bonsai 2 PQ2 (32,768, EXEMPT)** | **1,926 s** | **530/565** | 76 | **70** | 75 | **226** | 43 | **40** |
| 20261008-v3 | Swift Bonsai 2 PQ2 (32,768) | 1,678 s | 427/525 | 76 | **7** | 75 | **226** | 43 | - |
| minicpm-r1 | MiniCPM5-2B (quota 96k) | 1,110 s | **522/565** | 74 | 63 | 74 | 203 | **68** | 40 |
| ctx-v5 | MiniCPM5-2B (quota 96k) | 1,535 s | 456/565 | 76 | 66 | 75 | 199 | 0 | 40 |
| ctx-v3 | MiniCPM5-2B | 1,059 s | 445/565 | 76 | 67 | 75 | 144 | 43 | 40 |
| gpt-oss-r1 | gpt-oss-20b | 931 s | **528/565** | 76 | 66 | 75 | 204 | **78** | 29 |
| gpt-oss-r2 | gpt-oss-20b (partial) | 1,252 s | events/ledger/ledger2/repo only | 76 | 65 | **unscored** | 219 | 77 | **unscored** |
| ctx-v2 | gpt-oss-20b | 953 s | 432/565 | 74 | 66 | 75 | 202 | 0 | 15 |
| ctx-v10 | Swift (131k attempt) | 26 s | monitor stop | - | - | - | - | - | - |
| ctx-v6 | Swift (131k attempt) | - | host smoke failed | - | - | - | - | - | - |

## What the suite says, axis by axis

- **events 76 and paths 75 are saturated** at every good configuration; they absorb budget and
  manufacture ties. Only two partials tonight: Qwen3.6's 32,768 baseline and gpt-oss, both 74/76.
- **ledger 70** still discriminates, and Swift's old 7/70 was not the model: see finding 4.
- **ledger2 226** is the fine-grained discriminator: 226 (Kolibri, Swift) > 224/212 (Qwen3.6) >
  223/209 (Nemotron) > 202 (gpt-oss) > 199/144 (MiniCPM).
- **repo 78** splits the field hard: 78/78 for Qwen3.6, Kolibri, Nemotron; 43 for Swift and MiniCPM;
  **0/78 twice for MiniCPM at the raised context and once for gpt-oss** - a floor, not a score.
- **longctx 40** ran for every model; 40/40 for all but gpt-oss (15/40).

## Findings that should change how this lab reads its numbers

1. **Kolibri's six-task configuration is reproducible - but only that configuration.** `ctx-v4` and
   `ctx-v9` are both 551/565 with identical per-task values (76/70/75/212/78/40) at 2,971 s and
   2,877 s. Widen the sample and its `ledger2` moves to 226 at the same context (two targeted repeats),
   so the configuration repeats while the battery underneath it does not (finding 9).
2. **Provisioning is per model, and `longctx` is cumulative, not a big prompt.** The task reads a
   235 KB module in chunks, so its *peak* prompt is what matters, and the wire captures record it:
   Swift **16,111**, Qwen3.6 15,531 / 26,778, Kolibri 20,431 - all inside 32,768 - versus MiniCPM
   **40,336** and Nemotron **43,221**, which exceed it. So the raised window is load-bearing for two
   models, unnecessary for Swift (measured: it scored 40/40 at `n_ctx_slot = 32768`), and marginal for
   the other two. MiniCPM and Nemotron were only ever run at 131,072, so their "would not fit" is read
   from the peak they were allowed to use [INFERENCE - a 32,768 window would force compaction, and
   whether they would still score 40/40 is unmeasured].
3. **The raise does NOT cost `ledger2` - and that is a correction to this very file.** An earlier draft
   claimed Kolibri's 226/226 at 32,768 dropping to 212/226 at 131,072 twice was a systematic
   context cost. The targeted repeats refuted it: at the *same* 131,072 context, Kolibri scores
   **226/226 twice** when `ledger2` runs first in the loop (`-k1`, `-k2`), and 212 only when it sits
   fourth of six. See finding 9 - `ledger2` is the noisiest battery here, and context is not the
   variable.
4. **Swift's frozen-`ledger` collapse was a reply-cap artifact.** `20261008-v3` scored `ledger` 7/70
   with `ledger2` 226/226 on byte-identical checks; with the raised reply cap and quota (`ctx-v11`)
   it scores **70/70**. That is the report's Cause 1 (reply-cap truncation) reproduced on a second
   model - and it means the earlier "Swift is bad at ledger" reading was a harness artifact.
5. **The usage-gap tolerance is load-bearing.** Kolibri's first six-task attempt (`20261008-v2`)
   aborted after three tasks on `quota_unknown`; every provisioned run after it finished all six.
6. **Swift is EXEMPT from the context raise, on measurement.** At 131,072 its KV drove `gpu_free` to
   **0.49 GiB against the 0.5 GiB floor** (`gpu_used` 11.18 of 12 GiB) while physical RAM never went
   below 32.58 GiB - a VRAM wall, not a RAM one. `newtask_run.py` carries
   `PROVISION_EXEMPT = {'swift': ...}` and skips **both** the engine flags and the host-window rewrite;
   the exemption costs it nothing measurable (226/226 `ledger2`, 40/40 `longctx` at 32,768).
7. **Best and fastest full sweep: Qwen3.6 `ctx-v8`, 562/565 (99.5 %) in 1,330 s** - against Kolibri
   551/565 in 2,877 s and Nemotron 544/565 in 3,377 s. Speed did not cost accuracy here.
8. **The three batteries that had never run live behave exactly as designed.** In `ext-v12`, `repo2`
   is the only task that discriminates (54/55; the miss is `class2/unknown-kind-raises`, i.e. the
   per-instance registry was built but `register('nope')` was not made to raise), `perf` passes 33/33
   with the 2,000,000-interval wall (the one battery that prices engineering judgement - a
   correct-but-quadratic solution fails it and nothing else here does), and `longctx2` passes 40/40
   with all nine planted sites found. At n=1 those are "no failure observed", not "saturated"; the
   archive that makes them useful is partial fixers, which no run has produced yet.
9. **`repo` is the reproducible battery; `ledger2` is not.** The four targeted repeats
   (`newtasks-rep-20261009-q1/q2`, `-k1/k2`, `LAB_TASKS=ledger2,repo`) plus every earlier run give the
   first real spread:

   | Model | `ledger2` (n) | spread | `repo` (n) | spread |
   |---|---|---|---|---|
   | Qwen3.6 | 207, 212, 212, 224, 226, 226 (6) | **19** | 75, 78, 78, 78, 78, 78 (6) | 3 |
   | Kolibri | 211, 212, 212, 226, 226, 226 (6) | 15 | 78, 78, 78, 78, 78 (5) | **0** |
   | Swift (32,768) | 226, 226, 226 (3) | 0 | 43, 43, **75** (3) | **32** |
   | Nemotron | 208, 209, 222, 223 (4) | 15 | 75, 78, 78, 78 (4) | 3 |
   | MiniCPM | 144, 199, 201, 203 (4) | 59 | 0, 43, 43, 68 (4) | **68** |
   | gpt-oss | 202, 204, 206, 219 (4) | 17 | **0, 72, 77, 78** (4) | **78** |

   **Grouping the samples by the loop shape each ran in kills the "position" hypothesis** (the report
   carries the vectors): Kolibri's `ledger2` is **226 at pos 1 of 2 *and* at pos 4 of 5**, and 211/212/212
   only at pos 4 of 6; Qwen3.6 spans 207-226 with no pattern, including a perfect **226 at pos 4 of 9**;
   Nemotron spreads 209-222 and MiniCPM 144-203 *within a single shape*. So `ledger2` is simply noisy per
   model - **any single-run difference below ~19 checks is noise** - and the earlier position reading was
   a two-sample coincidence, now refuted. `repo` is tight *within* a model only above its boundary
   (Kolibri 0 spread over five samples, Qwen3.6 3, Nemotron 3) and volatile below it (MiniCPM 0-68,
   gpt-oss 0-78, and **Swift 43/43/75** once a third sample arrived - it is no longer "always 43").
   Separately, **`7/70` on the frozen ledger is a wall signature**: Nemotron produced one in exactly
   720.1 s, matching Swift's historical 7/70, so that pattern should never be read as a model verdict.
   Qwen3.6
   `-q1`'s low value (207, 19 failing traps) is the known cluster: frozen cases 0, 6, 19 plus the
   whole Unicode-digit group.

## Corrections made tonight (keep them visible)

Two claims were written here and then refuted by the very next runs. Both were corrected in place
rather than quietly dropped, because the refutations are the more useful evidence.

1. **"`longctx` cannot run at 32,768."** An earlier draft of the report and resume claimed it, and
   `newtask_run.py` briefly carried `TASK_EXCLUDE = {'swift': ('longctx',)}` on that assumption.
   `ctx-v11` refuted it (40/40 at 32,768, peak prompt 16,111 tokens), so the exclusion was **removed**
   from the driver rather than left as a dead switch. The same draft also inherited a duplicated
   provisioning block in `_build_into`; the function was rewritten as one implementation and both
   branches (exempt / normal) were verified by build.
2. **"The context raise costs `ledger2` (Kolibri 226 -> 212, systematic)."** Refuted by the targeted
   repeats: Kolibri scores **226 at the same 131,072 context** when `ledger2` runs first, so the
   variable is loop position or plain variance, not context (finding 9). The cost claim appeared in
   this resume, the report, both handoff documents and the week summary; all five were corrected.

## Pending, in the order it should be picked up

0. **Both GPU items finished** (one workload at a time, serially):
   - `newtasks-ext-20261009-v12` (Qwen3.6, nine-task loop, 2,707.5 s, no error): the six
     frozen-plus-new tasks scored **565/565, all clean and correct - the first perfect six-task
     sweep**, and the three never-run batteries scored **`repo2` 54/55** (its one miss is case 27,
     `class2/unknown-kind-raises`), **`perf` 33/33** (2,000,000 intervals inside the relative wall) and
     **`longctx2` 40/40** (all nine planted sites). Nine-task total **692/693**. Built with
     `LAB_EXTENDED_TASKS=1 python newtask_run.py qwen36-35b-a3b --root newtasks-ext-20261009-v12`.
   - The targeted repeats `newtasks-rep-20261009-q1/q2` (Qwen3.6) and `-k1/k2` (Kolibri) ran
     `ledger2`+`repo` each and produced the spread table in finding 9 - including the refutation above.
   - **Swift's context ladder - settled (`bg_72`); the exemption is confirmed.** The roots were:
     - `newtasks-swift-20261009-c65k` - Swift provisioned at **65,536** (`LAB_CONTEXT=65536`, the new
       per-build override; it deliberately overrides `PROVISION_EXEMPT`, since the exemption records a
       VRAM margin, not a runtime that rejects the flags),
   - `newtasks-swift-20261009-c98k` - **only if** 65,536 completes clean (the chain gates on the
     record's own `error` field), so the ladder ends wherever Swift's card actually ends,
   - `newtasks-minicpm-20261009-r1` and `newtasks-gptoss-20261009-r1/r2` - the n=3 samples the report's
     status table flags as open for the cap-arm rates.
   **Prediction, recorded before the result** (from `ctx_ladder.py` on the existing roots): Swift at
   32,768 bottoms at 1.28 GiB GPU free (`-v11`) and 0.69 GiB (`20261008-v3`, five tasks), while
   131,072 bottoms at 0.49 (trip) and 0.50, with `max_gpu` only 10.38 -> 11.18 GiB across a 4x window.
   So Swift's VRAM is weight-dominated and its KV is small: **65,536 should fit with room, and the
   exemption is a margin call near 131,072 rather than a wall.** If that holds, 98,304 becomes the
   interesting row and the exemption may deserve to be restated as "not at 131,072" rather than
   "32,768 only".
   **RESULT - the prediction is REFUTED, and the crossing is systematic.** `newtasks-swift-20261009-c65k`
   tripped the monitor after **24.8 s** with `gpu_free` bottoming at **0.31 GiB against the 0.5 GiB
   floor**, during model load, with physical 34.4 GiB and commit 33.5 GiB *comfortable* and a hard-fault
   storm (808,514 pages/s) as the weights came off disk; the retry (`-c65k2`) **reproduced it exactly**
   (0.31 GiB, 26.0 s). So the raised-context cost is a **load-time** GPU peak, not a generation-time
   one - comparing `max_gpu` during generation (10.38 vs 11.18 GiB) is what misled the prediction. The
   chain's gate then skipped 98,304, and the exemption is settled: **32,768 or nothing** (restated in
   the driver, the report and the week summary).
   - **The n=3 samples landed.** MiniCPM 445 / 456 / **522**/565 (`repo` 43/0/**68**); **Nemotron
     `-r1` 545/565** in 3,303.8 s, reproducible to one check against `ctx-v7`'s 544; **gpt-oss r1
     528/565** in 931 s with `repo` 0 -> **78**. gpt-oss r3 re-ran `paths` **75/75** (so r2's 0/75 was
     the scorer's abnormal exit, not the model), and its **`longctx` is unscored in both r2 and r3** -
     the harness resolves its scorer with a name-based `from staged_tasks_20260922 import TASKS`
     (harness `run.py:324`) and the **frozen** module sometimes wins; that module has neither `longctx`
     nor `ledger2`, and it is what raises `ValueError('unknown task: longctx')`. r3's longctx session
     finished clean in 233 s, but its artifact carries a syntax error (`def reconcile_batch(records):`
     with no body). **Unscored, not failed** - flagged as such in the record; the root's own scorer was
     probed offline and works (1/40), so the failure was a run-time name-resolution condition, and the
     cells are closed as failures below.   - **A starter-baseline rule now corrects four readings from this round.** Scoring the unmodified
     starters gives the no-op table (`events` 2/76, `ledger` **7/70**, `paths` 9/75, `ledger2` **62/226**,
     `repo` **0/78**, `longctx` 1/40, `repo2` 0/55, `perf` 1/33, `longctx2` 0/40; pinned in
     `starter-baselines-20261009.json`). Nine cells in the corpus land there and **four had been read as
     model behaviour**: Swift's historical 7/70 and its nine-task `ledger2` 62/226 (both "never wrote the
     file", artifact byte-identical to the starter), both of gpt-oss's `repo` zeros, and MiniCPM's `repo`
     0/78. So Swift's *edited* `ledger2` is 226/226/226 - still the most stable model on that battery, the
     opposite of what this resume said an hour ago - and gpt-oss's edited `repo` is 72/77/78. Separately,
     **Nemotron's `longctx2` 0/40 was unscored** (`abnormal_evaluator_exit`), not "all nine sites missed".
     A *clean* session can be a no-op, so `clean_finish` cannot tell you; hash the artifact against the starter.

   - **Strata: 692/693 on the nine-task suite - identical to Qwen3.6's best.** `strata-newtasks-20261009-v2`
     ran all nine batteries in **1,959 s** with no resource stop at the new **4 GiB** resident
     declaration (the template's 12 GiB had tripped the 3 GiB physical floor at 3.18 GiB; the engine
     loads in 31.7 s and decodes at 66-79 tok/s). Six batteries were initially **unscored** because
     `score_artifact` runs the task module from the *base module's own directory* - the harness's base
     pointed at the frozen module, which has only `events`/`ledger`/`paths`. The port now copies the
     base into the root (`source/relay_strata.py`, siblings beside it) and sets `lab.base` to it, the
     same move the OMP templates make; **verified 6/6 through the production path**, and a fresh
     independent sample (`strata-newtasks-20261009-v3`, six batteries) is in flight. The v2 artifacts
     re-scored offline give events 76, ledger 70, paths 75 (in-flight), ledger2 226, repo 78, longctx
     40, repo2 54/55, perf 33, longctx2 40 - the same cells as Qwen3.6, with the same single `repo2`
     miss (`class2/unknown-kind-raises`). Method and per-cell detail: `offline-rescores-20261009.json`.
     **Confirmed at n=2:** the fresh post-fix run `strata-newtasks-20261009-v3` reproduced five of six
     **exactly** (ledger2 226, repo 78, longctx 40, repo2 54/55, perf 33/33), which also validates the
     offline re-scores; `longctx2` runs in `strata-newtasks-20261009-v4` because the 4 GiB declaration
     leaves the 3 GiB floor marginal (session minima 2.94-5.11 GiB) and `perf` - the evaluator
     materialises 2,000,000 intervals - crossed it at 2.94, stopping that session after its artifact was
     already complete. 2 GiB is the safer declaration if this track continues.
   - **gpt-oss's `longctx` cells are closed as failures, not gaps**: re-scoring both roots' artifacts
     offline gives **0/26** each - the model's file has a syntax error (`def reconcile_batch(records):`
     with no body) - while r3's targeted re-run recovered `paths` 75/75.
   - **This round (2026-10-09, later): two build-flag mistakes of mine, two infrastructure failures, and
     a corrected variance finding.** The five "nine-task" roots and the two "position" roots had been
     pre-built *without* `LAB_EXTENDED_TASKS=1` / `LAB_TASKS=ledger2`, so those runs executed the
     six-task loop; the roots are preserved as `*-sixloop` (their results are valid six-task samples)
     and the true roots (`newtasks-nine9-*`, `newtasks-pos2-*`) are running now. Two runs failed
     outright: Kolibri `-k1` on `ConnectionResetError 10054` in 51.9 s, and Nemotron `-n1` on a bare
     `AssertionError` after an events run of 2/76 - both covered by the fresh roots. The new samples
     **refuted the loop-position hypothesis** (finding 9) and produced the `7/70`-is-a-wall-signature
     result.
   - **Strata's 2 GiB profile is complete**: events 76, ledger 70, paths 73, ledger2 226, repo 78,
     longctx 40, repo2 **hang (a recorded failure: the artifact's varint encoder is missing its loop
     terminator, so the first `class1` case loops forever - attributed by dumping the scorer's
     stack mid-hang)**, perf 33, longctx2 40 - 636 of the 638 checks it
     scored, against 692/693 at the 4 GiB declaration. The two differing cells (paths 73 vs 75, repo2
     hang vs 54/55) are n=1 each and the Strata config still pins no seed, so "thinner expert pool" and
     "sampling variance" are not yet separable.
   - **Two instruments were built and self-tested overnight; both run after the current chain.**
     `knowledge_items.py` + `knowledge_run.py` give the lab its first factual-knowledge instrument:
     1,100 pinned items (800 MMLU over 8 subjects for recognition, 300 GSM8K as the procedural control,
     because low-bit quantisation hits recall far harder than reasoning). Self-test: **gold 1100/1100**,
     seeded random **0.253 on MMLU** (chance for four options) and **0/300 on GSM8K**. Sampling is pinned
     per request (temperature 0, seed 20261009) - the Strata config declares no seed at all - and the
     prediction is on record before the run. `igpu_probe.py` is a declared **hardware probe** of Ollama's
     Vulkan iGPU against CUDA (the NPU has no engine path here). Both are described in the report's
     "Two new instruments".
   - **The knowledge A/B ran (1,100 items per stack) and the two stacks are indistinguishable.**
     Qwen3.6-35B-A3B Q4_K_M (llama.cpp, 131,072, `--cpu-moe`): **974/1100 = 88.5 %** (MMLU 688/800 =
     86.0 %, GSM8K 286/300 = 95.3 %, 3,078 s). Qwen3.8-Flash-Next Q2_0 (Strata, 65,536, 4 GiB resident,
     streamed): **987/1100 = 89.7 %** (MMLU 699/800 = 87.4 %, GSM8K 288/300 = 96.0 %, **2,128 s**).
     The gap is **13 items = 1.2 points against a 1.33-point standard error** - inside one se, so the
     second stack is *not* better, it is the same. My recorded prediction (the 2-bit giant should win
     MMLU by capacity while staying close on GSM8K, with a recall penalty as the alternative) was
     directionally right and materially wrong: **the low-bit penalty did not appear** - 87.4 % vs 86.0 %
     on recall. `virology` is 58 % for *both* (a dataset ceiling, not a model property) and `prehistory`
     is the only visible gap (.86 vs .94, ~1.9 se). The streamed engine was also 31 % faster in wall
     time on this workload.
   - **The Intel iGPU probe is answered with a ratio.** The Arc path works through Ollama's Vulkan
     backend (`OLLAMA_IGPU_ENABLE=1`), and on a 3B MoE it runs at **100.8 tok/s against the 5070's
     260.5 tok/s - 0.39x** - with the work split 59 % CPU / 41 % iGPU, its share spilling to system RAM.
     The first attempt was worthless because `CUDA_VISIBLE_DEVICES=''` is treated as *unset*, so both arms
     ran on the 5070 and reported the same rate; `-1` is the working way to hide it, and `ollama ps` is
     what proved which device ran. The NPU has no path in any engine here. So: the 5070 stays the device,
     and the iGPU is at best a second device for the small decision/embedding track.
1. **Decide (Kevin) whether the model comparison series reports each model at the context it can
   afford** - Qwen3.6/Kolibri at 131,072, Swift at 32,768. Note that the original argument for the
   question (a measured `ledger2` cost of raising the context) **no longer stands**: nothing measured
   so far shows the raise hurting any battery, and it is load-bearing only for MiniCPM's and
   Nemotron's `longctx` peaks. The remaining reason to keep contexts explicit per model is honesty
   about configuration, not a measured penalty.
2. **If the answer is "all at 32,768"**: MiniCPM and Nemotron need re-running there to see whether
   compaction keeps `longctx` passable; if it is "per model", nothing needs re-running and the suite
   above is the comparison. Swift's `ctx-v11` is already the correct 32,768 datapoint.
3. **Swift's mid-size context: ANSWERED, nothing remains.** The 65,536 attempt tripped during load at
   0.31 GiB GPU free and **reproduced on a retry**, so the ladder is closed: 32,768 or nothing. (The
   `LAB_CONTEXT` override stays in the driver for future probes.)
4. **The nine-task root has run once for Qwen3.6 and once for Strata; the other five models have only
   six-task profiles.** So `repo2`, `perf` and `longctx2` have **two artifacts each** - below the
   census's >= 3-observation threshold - and no per-model reading. This is the largest genuinely open
   measurement: `LAB_EXTENDED_TASKS=1` sweeps for Kolibri, Nemotron, MiniCPM, gpt-oss and Swift (Swift
   would drop `longctx` only if the window matters; `longctx` fits at 32,768 - measured).
5. **The position-controlled repeat**: hold `ledger2`'s loop position fixed while varying context. Both
   Kolibri and Nemotron show their low value in the same fourth-of-six shape, which is the confound the
   retired "context costs `ledger2`" reading mistook for an effect; this is the one design that settles it.
6. **A general fix for the OMP-side scorer resolution** (the harness's name-based
   `from staged_tasks_20260922 import TASKS`): two cells out of ~50 were left unscored by it. The Strata
   instance is fixed by keeping the base module root-local; the OMP roots still rely on sys.path order.
7. **Strata continuation, if the track resumes**: declare **2 GiB** resident rather than 4 (the 3 GiB
   physical floor was marginal at 2.94-5.11 GiB and `perf` crossed it), and note the frozen three have
   n=1 at that declaration.
8. **A decision: retire `events` and `paths` from ranking.** They still split on only 5/76 and 3/75
   checks in the top group, so they absorb budget and manufacture ties.
9. **The 6 GiB worker cap / nimble** is still Kevin's earlier open decision (keep the cap and end that
   track, or amend it); unchanged by tonight.
10. **Aggregate thresholds**: `repo2`/`perf`/`longctx2` enter the rate table at >= 3 observations, so
   item 4 also unlocks the last three rows of that table.

## How to re-run exactly

```
cd C:/Users/kevin/ai_bench/new-items-20261007
python newtask_run.py --check                 # offline: superset CLI vs the battery module
python newtask_run.py swift                   # one model: builds its root if absent, then runs it
python newtask_run.py qwen36-35b-a3b --root NAME            # explicit root: one model, many roots
LAB_EXTENDED_TASKS=1 python newtask_run.py qwen36-35b-a3b   # the nine-task loop
LAB_TASKS=ledger2,repo python newtask_run.py kolibri-1 --root NAME   # a declared loop subset
```

- The record is keyed by **root** (a repeat does not overwrite the earlier run). Each root's README
  declares its own loop and its provisioning/exemption, so a subset root is self-describing.

- The record accumulates in `newtask-run.json`: root, model, wall, error and per-task
  `passed/total/clean/correct/seconds/tokens`.
- Per-root evidence: `<root>/evidence/<model>-coding.json`, `<root>/evidence/<model>-run.log`, and
  per-session `<root>/<model>-<task>/{status.json,resources.json,server.log}` plus
  `<root>/<model>-<task>/trial/wire/*.summary.json` (that last one is where `prompt_tokens` per
  request lives - it is how the `longctx` peaks above were measured).
- A monitor stop is attributed from `resources.json` (compare `gpu_free` / `physical_available_gib`
  against the floors), not from the log's last line - and `python ctx_ladder.py [root ...]` prints
  served context, min GPU free, min physical free and max GPU used per Swift root in one table, with
  the lab's 0.5 GiB floor applied to flag a trip.
