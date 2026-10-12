# Local LLM and harness lab: continue here

Updated October 12, 2026. Owner: Kevin, machine DARKTEXAS.

## Restart checklist (2026-10-12, end of session)

1. **Read, in order:** this file, then `local-llm-lab/AGENTS.md` (its top entry is the pause), then
   `overnight-20261011/README.md`. The instruments, frozen inputs and small evidence are also in the repo
   under `local-llm-lab/instruments/`; refresh them with `python instruments/refresh-snapshot.py` and commit.
2. **Nothing from this lab is running or resident.** Check the gates before any load (free physical >= 9 GiB,
   commit headroom >= 8 GiB). Kevin's own `tools/dev-server.py` holds port 8080 and the WSL relay holds 8000 -
   those are his, not leftovers, and a gate trip may be WSL's ~5 GiB rather than a stale process.
3. **The paused queue, in this order:** delete `overnight-20261011/OVERNIGHT-STOP`, then
   `cd overnight-20261011 && python runner.py --only i4-reason-repeat,i6-gliner-replay`, then the
   **Colibri Qwen3.6-35B-A3B knowledge comparison** - the "same model, second engine" item that never ran.
   Its ~23 GB model is already complete on `D:\ai_bench-staged\colibri-models` (21.45 GiB, 50 files), so
   serve that directory and point the knowledge instrument at port 8000. **Never use `coli setup` for it:**
   that command downloads and then runs the server in the foreground, so it never returns - it deadlocked an
   eight-hour attempt.
4. **Preferences in force:** commit and push after each change (only `local-llm-lab` is a git repo;
   `ai_bench` is not, and its publishable parts are snapshotted into `instruments/`); open new documents with
   `ai_bench/Open-Document.ps1`; everything public here is **FSL-1.1-MIT** - source-available, *not* OSI open
   source, so do not describe it otherwise.
5. **Do not repeat:** relicensing the three third-party repos on the account (`django-registration`, `mscgen`,
   `pdm`) or the ~390 dormant Dropbox repos; committing model packs, build output or wire captures; guessing
   which of `LICENSE` / `LICENSE.md` a repo uses instead of checking both.

- 2026-10-12: **PAUSED MID-QUEUE, resumes tonight.** Read `local-llm-lab/AGENTS.md` (its top entry) and
  `overnight-20261011/README.md`. The queue's stop marker is in place, no engine is resident, and night 1's
  results are preserved in `status-night1.json`, `REPORT-night1.md` and `REPORT-SUMMARY.md`.
  **Owed, in order:** (1) `python runner.py --only i4-reason-repeat,i6-gliner-replay` after deleting
  `overnight-20261011/OVERNIGHT-STOP`; (2) the **Colibri Qwen3.6-35B-A3B knowledge comparison** - the ~23 GB
  model is already complete on `D:\ai_bench-staged\colibri-models` (21.45 GiB, 50 files), so serve that
  directory and point the knowledge instrument at port 8000; **do not use `coli setup`** for it, because that
  command downloads and then runs the server in the foreground, so it never returns - it deadlocked an
  attempt for eight hours.
  **Measured 2026-10-10 to 11** (all written up in `local-llm-lab/`):
  (a) **Knowledge**: Kolibri-1 78B **81.9%** against Qwen3.6-35B-A3B 88.5% and Strata Q2_0 89.7% on the same
  1,100 pinned items - the coding leader is *not* the knowledge leader, and Kolibri is the fastest at 1.46 s
  per item; (b) **placement changes the prose, not the answers**: Strata at `--resident-budget-gib` 2 vs 8,
  **65 of 93 justifications differ, 0 of 93 letters, correctness 92 vs 92**; (c) **the stall signal is in the
  transcript**: a three-line rule on identical-outcome repetition catches **4/4 stalls at 1/14 false alarms**
  where every neural decision model this lab has screened caught **0/4**, and Laya adds nothing on top;
  (d) **engine research** in `STRATA-ALTERNATIVES-2026-10-11.md`: Colibri v2.0.0 is the only alternative whose
  route fits this box (Apache-2.0, Windows, Jev-compatible `/v1/systemone`, decision models on CPU), the
  "2x expert cache" video describes an **unmerged** PR (#26563, flags `-ehs`/`--expert-hot-s`), and ds4 /
  FreeToken / StrataFlow are hardware-blocked or not usable here. `KNOWLEDGE-DEEP-2026-10-10.md` holds the
  instrument details and the parse lesson that manufactured a 4.3-point gap.
  **Machine facts:** there is a **second identical NVMe on `D:`** (331 GiB free at the time, measured
  throughput parity with `C:`, and `D:` already held a 622 GiB models store) - the `C:` space drops were
  **pagefile allocation**, which grows under engine load and releases on its own; the lab's instruments,
  frozen inputs and small evidence are now snapshotted into `local-llm-lab/instruments/` with a sha256
  manifest and a refresh script; and a **standing preference is recorded to commit and push after each
  change** (that repo is public, so the snapshot is secret-scanned first).
  **Licensing (same day):** every public repo on this account is licensed **FSL-1.1-MIT** (Functional Source
  License 1.1, MIT future licence - source-available, **not** OSI open source; each version becomes MIT on
  its second anniversary). An audit of 262 public non-fork repos found **213 already carried it**, **46 had
  no licence file and all 46 were written through the GitHub Contents API** (no `gh`, no WSL, no cloning -
  the stored git credential is enough), and **3 were deliberately skipped** because they hold other people's
  licences: `django-registration` (James Bennett), `mscgen` (GPL), `pdm` (BSD-3-Clause) - archive or delete
  those rather than licensing them. Two traps: GitHub's licence detection does not know FSL, so a repo
  sidebar shows no licence even when the file is there (audit the file, never the API's `license` field), and
  a repo may legitimately carry the licence as `LICENSE.md` rather than `LICENSE` - `tek/tek-tube` does, with
  a `NOTICE.md` for its third-party assets. `local-llm-lab` itself is FSL-1.1-MIT and its `NOTICE.md` covers
  the third-party datasets and model outputs inside `instruments/`.
  **Repos published in this pass:** `local-llm-lab` (this notebook), `tek/tek-tube`, and **`goproverbs`** -
  the last found locally at `local-llm-lab/goproverbs` with one branch and no remote, imported as 1,836 files
  / 29.9 MB and pushed to <https://github.com/kevinelong/goproverbs>, with its build output (`target/`, 461 MB)
  and 2.7 GB of raw `.jsonl` traces ignored and left local.

- 2026-10-09 (small hours): THE NEW-TASK SUITE RAN LIVE, and Swift is exempt from its provisioning.
  Read `new-items-20261007/RESUME.md` first. The frozen three (events 76 / ledger 70 / paths 75) now
  sit beside three new batteries - **ledger2** (226 checks), **repo** (78, multi-file) and **longctx**
  (40, a 235 KB corpus read in chunks) - 565 checks in all, run under a declared provisioning (served
  context 131,072, host window 131,072/32,768, thinking budget 6144, reply cap 32,768, `quota_unknown`
  demoted to a counted usage gap). Results, one run each: **Qwen3.6 562/565 in 1,330 s** (best and
  fastest), Kolibri 551/565 twice with identical per-task values, Nemotron 544, **Swift 530** with the
  exemption, MiniCPM 456, gpt-oss 432. Five things to carry forward: (a) provisioning is **per model**
  - `longctx`'s measured peak prompt is 16.1k (Swift), 15.5-26.8k (Qwen3.6) and 20.4k (Kolibri), all
  inside 32,768, versus 40.3k (MiniCPM) and 43.2k (Nemotron), which need the bigger window - and it
  does **not** cost anything measurable: four targeted repeats (`newtasks-rep-20261009-q1/q2`,
  `-k1/k2`) refuted the earlier "Kolibri 226 -> 212 is a context cost" reading, since Kolibri scores
  226/226 at the *same* 131,072 context when `ledger2` runs first, so the variable is loop position or
  variance; the open question for Kevin is now only about reporting configuration honestly, not about
  a measured penalty; (b) **Swift Bonsai 2
  (Prism fork) cannot take the raise** - at 131k its KV drove `gpu_free` to 0.49 GiB against the 0.5
  floor, and a 65,536 attempt tripped even earlier (24.8 s, 0.31 GiB, before the model finished
  loading, with RAM and commit comfortable), so the ceiling is the weight load rather than the
  generation-time cache; 32,768 is the only measured configuration that clears the floor - and is
  declared `PROVISION_EXEMPT` in `newtask_run.py`, which is why its 530 comes from a
  32,768 window; (c) its old 7/70 ledger was a **reply-cap artifact** and is now 70/70, the report's
  Cause 1 reproduced on a second model; (d) the nine-task loop (`LAB_EXTENDED_TASKS=1`) ran once
  (`newtasks-ext-20261009-v12`, Qwen3.6, 2,707.5 s): **565/565 on the six-task suite - the first
  perfect six-task sweep, every task clean and correct** - plus the three never-run batteries `repo2`
  54/55 (miss: `class2/unknown-kind-raises`), `perf` 33/33 (the only battery that prices engineering
  judgement) and `longctx2` 40/40, i.e. **692/693**; at n=1 the new batteries are "no failure
  observed", not saturated; (e) those repeats moved the two weakest a long way in both directions:
  **gpt-oss 432 -> 528/565** (its `repo` 0 -> **78**, `longctx` 15 -> 29) and **MiniCPM 445 -> 456 ->
  522** (`repo` 43 -> 0 -> **68**). So `repo` is reproducible only for models above its boundary
  (Kolibri 78/78 x4, Qwen3.6 x5/6, Swift 43/78 x2) and is the *most volatile* battery for the two
  weakest (0-78, 0-68), while `ledger2` is noisy everywhere (Qwen3.6 spread 19 over six runs, Kolibri
  14 over five) - single-run `ledger2` differences below ~19 checks are noise. gpt-oss's third sample
  is **partial**: its `paths` scorer exited abnormally (`abnormal_evaluator_exit: 1`, so 0/75 is
  unscored, not zero) and `longctx` raised the frozen module's "unknown task" - **unscored, not
  failed**, now flagged in the record, with a targeted re-run completing them.
  (f) **The context ladder is settled**: Swift at 65,536 trips the monitor during load (0.31 GiB free
  against the 0.5 floor) at 24.8 s and **again at 26.0 s on a retry**, while 32,768 holds 0.69-1.28 GiB
  free - so the exemption is 32,768 or nothing, and the cost is a *load-time* peak (comparing
  generation-time `max_gpu` is what made an earlier note predict otherwise). (g) A **harness scoring
  bug** leaves `longctx` unscored in some roots: the harness resolves its scorer with a name-based
  `from staged_tasks_20260922 import TASKS` and the frozen module - which has neither `longctx` nor
  `ledger2` - sometimes wins; the cells are *unscored, not failed*, now flagged in the record, and a
  general fix for the OMP roots remains open (the Strata instance is fixed - see (h)).
  (h) **Strata now scores the whole new-task suite: 692/693, identical to Qwen3.6's best** (same
  cells, same single `repo2` miss) - a streamed Q2_0 pack at **4 GiB resident** equals a fully resident
  35B-A3B Q4_K_M here. Two fixes got it there: the template's 12 GiB resident budget tripped the 3 GiB
  physical floor (3.18 GiB) even though the engine loaded in 31.7 s and decoded at 66-79 tok/s, now
  declared at 4 GiB; and `score_artifact` runs the task module from the **base module's own directory**,
  so the base must be a root-local copy with the superset beside it (`source/relay_strata.py` +
  siblings + `lab.base = _fresh`, the OMP templates' own move) - without it six batteries returned
  `abnormal_evaluator_exit: 1` and had to be re-scored offline. Verified 6/6 through the production
  path before re-running, and **confirmed at n=2** by the fresh post-fix run `strata-newtasks-20261009-v3`
  (five of six batteries reproduced exactly); its `longctx2` runs in `strata-newtasks-20261009-v4`
  because the 4 GiB declaration leaves the 3 GiB floor marginal (v3 minima 2.94-5.11 GiB; `perf`, the
  evaluator that materialises 2,000,000 intervals, crossed it at 2.94 after its artifact was already
  complete) - **2 GiB is the safer value** if the Strata track continues. v3 engine loads: 16-18 s.
  **Three declarations were made on Kevin's instruction (2026-10-09)**, all recorded in the report and
  the changelog: (i) the **6 GiB worker-private cap is removed**
  (`local-decisions-20260925-v1/run.py`, `WORKER_PRIVATE_CAP_GIB = None`) while the eligibility gate
  (9/8/0.5 GiB) and the runtime floors (3/2/0.5 GiB) stay armed and every historical record is untouched;
  (ii) **`events` and `paths` are retired from ranking** - the metric is now the discriminating subset
  `ledger + ledger2 + repo + longctx` = **414 checks** (`ranked_table.py` regenerates it from the roots'
  evidence), with **two perfect rows**: Qwen3.6 `ext-v12` 414/414 and **Strata 414/414**; (iii) **each
  model is reported at the context it can afford** (131,072 local, 32,768 Swift, 65,536 Strata). A
  self-contained visual report is at `new-items-20261007/RECENT-WORK-2026-10-09.html`.
  **Running now** (one serial chain): nine-task sweeps for Kolibri / Nemotron / MiniCPM / gpt-oss / Swift,
  position-controlled `ledger2` repeats for Kolibri and Nemotron, and the Strata nine-task sweep at the
  safer **2 GiB** resident declaration.
  **One incident is worth carrying forward:** the declared cap removal edited a file that every root's
  `manifest.json` pins by digest (120 files, including the monitor module), so roots built afterwards
  died in `verify()` with `AssertionError: [...local-decisions-20260925-v1\run.py]` - the freeze doing
  its job. The fix is a **declared re-pin, not a bypass**: the builder recomputes the manifest and
  records old -> new digests in `evidence/pin-change.json`, and the inherited protocol field
  `decision_worker_private_cap_gib` is set to null with a note. Verified after rebuild: 120 pinned,
  0 mismatches. A separate driver NameError of my own killed seven invocations before they started;
  fixed, with the failed roots preserved as `newtasks-*-fail-pin-20261009`.
  **Overnight (2026-10-09, later): two instruments built, self-tested and RUN.** (i) The lab's first
  knowledge/recall instrument answered the Qwen3.8-vs-3.6 question: **974/1100 = 88.5 % (Qwen3.6 Q4_K_M)
  against 987/1100 = 89.7 % (Qwen3.8-Flash-Next Q2_0, streamed)** - a 1.2-point gap against a 1.33-point
  standard error, i.e. **indistinguishable**, and the predicted low-bit recall penalty did not appear.
  (ii) The Intel iGPU probe: the Arc path works via Ollama's Vulkan backend at **0.39x** the 5070
  (100.8 vs 260.5 tok/s, 59 % CPU / 41 % iGPU); its first run was void because
  `CUDA_VISIBLE_DEVICES=''` is treated as unset - `ollama ps` is the attribution check. Also delivered:
  four nine-task profiles (MiniCPM **656/693**, Nemotron 620, gpt-oss 549, Swift 508) with `repo2` as the
  new discriminator, the loop-position hypothesis refuted, and a fresh visual report at
  `new-items-20261007/RECENT-WORK-2026-10-09.html`.
  No gate changed beyond the declared cap removal, no app closed, no reboot, platform 64 GB dual
  channel throughout.
- 2026-10-08: the FIVE NEW QUEUE ITEMS ARE EXECUTED - read `new-items-20261007/REPORT.md`.
  (1) **MTP versus plain, n=3 per arm**: MTP is **+31.2 % per token** (50.3 vs 38.3 tok/s) but only
  **-7.3 % wall**, because it emits **+21.7 % more tokens**, and it does NOT raise accuracy (plain
  219, 221, 219; MTP 220, 219, 216). The single-pair "MTP scored higher" reading was run variance.
  First perfect coding sample in the series: Qwen3.6 `-v26-1` **221/221**, all three tasks clean,
  972 s, 38.1k tokens.
  (2) **Rate sets**: `events` (76/76) and `paths` (75/75) are saturated at every good configuration,
  so only `ledger` discriminates - and five of its 70 checks carry nearly all of it: case 19
  (ASCII-only digits, the U+0661 trap that `isdigit()` and `int()` both accept) fails 14/23 samples,
  7 (`"a"x` quoting) 12/23, 5 (unclosed quote) 11/23, 0 (empty text) 10/23, 6 (blank record) 5/23.
  Only four samples ever scored 70/70 (Swift x2, Kolibri v16-3, Qwen3.6 v26-1).
  (3) **Ledger early termination ANSWERED**: the engine's own log says *"the reply reached max tokens
  while still thinking, so it has no answer"* and the message ends `stopReason=length` with no tool
  call - 3 of 13 sessions, every one below 70/70; the other two 7/70s were external terminations
  (guard stop, 720 s wall). Also `clean_finish=false` / `exit 143` / `quota_unknown` occur on 70/70
  runs, so `clean` is NOT a failure signal. Mitigation tested: `reasoning_budget_tokens: 6144` and
  `reasoning_close_retry: true` each gave 3/3 at 70/70 with zero diagnostics (baseline 3/13) - but
  n=3 per arm cannot establish the rate change, so re-measure before relying on it. Roots v19/v20.
  (4) The v0.1.40.1 **tool-call rescue is unexercised here**: 0 occurrences of tool-call markup inside
  reasoning in 26 sessions (a mangled `write` argument did appear, and the model recovered).
  (5) **Qwen3.6 long context**: 3/3 planted codes at 32k/64k/131k/262k (206,147-token prompt), 26-27
  GiB free physical, GPU 7.71 GiB and load ~10 s at 262k - strictly cheaper than Kolibri at the same
  3/3. No gate changed, no reboot, no app closed, no lock and no engine left resident.
- 2026-10-08 Kolibri on the full six-task suite: **551/565 (97.5 %) - the same score as Qwen3.6 with the
  provisioning, at 1.8x the time** (2,971 vs 1,642 agent seconds; 495 vs 274 s/task). Frozen three
  perfect, repo 78/78, longctx 40/40, ledger2 212/226 (same Unicode-digit shortfall as Qwen3.6). So
  **Qwen3.6 + provisioning remains the fastest successful combo**, and the top two are tied on
  everything the old protocol could resolve.
- 2026-10-08 MiniCPM `repo` quota test: DOUBLING the session quota (48k -> 96k) did NOT recover it -
  it spent more (69,774 tokens, 73 tool calls, 68 turns), hit the 720 s task wall for the first time in
  the new-task family, and produced a WORSE artifact (0/78, module does not import). So that failure is
  thrashing, not a budget limit. Same sweep: 456/565 (80.7 %) at 99.7 tok/s, ledger2 199/226, longctx 40/40.
- 2026-10-08 Strata 0.1.41: staged (sha256-verified, copytree of the pinned 0.1.40.3 install) and A/B'd -
  15 ledger runs, all 70/70. Upgrade alone NEUTRAL (cold prompt 636 vs 632; GPU cache 2,425 experts vs
  2,407) - adopt for the watchdog/tool-parse fixes, not speed; `--expert-cache 1500` is a REGRESSION
  here (579.6 vs 615.9-657 cold prompt, 41% vs 49% hit rate); `STRATA_ROUTE_RESIDENT=1` no gain on a
  prefill-bound workload. The headline prompt fix targets disk-bypassing reads; ours is RAM-bound.
  Read `local-llm-lab/NEWS-2026-10-08.md` and `ai_bench/new-items-20261007/REPORT.md`.
- 2026-10-08 NEWS SCAN: `local-llm-lab/NEWS-2026-10-08.md`. Three of our engines moved today, and the
  first one is aimed at our measured bottleneck. **Strata v0.1.41** (12:14 UTC; 0.1.40.4 at 08:04; we
  are pinned at 0.1.40.3): "Windows, model bigger than RAM: prompts about twice as fast" (RTX 5070 PC
  prompt time -45-52%; IQ3_XXS/IQ3_S with a RAM budget -16-25% on 4K-20K prompts) - and our suite is
  **43.6:1 read:write**, so prefill is the wall. Their own RTX 5070 + Q2_0 row says **`--expert-cache
  1500` beats `auto` by 15-27% on short prompts** (we run auto), and `STRATA_ROUTE_RESIDENT=1` measured
  **+4.1% decode on the 5070 with Q2_0** (6/6). Also: a hung-engine watchdog, `<function= NAME>` tool
  calls now parsed, and a fix for RAM-resident prompts being 4-7x slower on the SSD path. **llama.cpp
  b11512** (today) fixes DFlash output-head sharing - relevant to our staged DFlash heads. **Ollama
  v0.40.1** fixes "clef head reads past 2GiB on windows" (a decision-track model family).
  QUEUE: (1) Strata 0.1.41 A/B set - stage the pinned zip (sha256 646ded01...), copy the engine (never
  the pinned tree), then expert-cache / ROUTE_RESIDENT / 64k ledger n>=3; (2) move the Strata coding
  pack to IQ3_XXS (3-bit, ~76 GB, 111 GB free); (3) re-baseline Swift and Nemotron on the provisioned
  six-task suite; (4) ledger2/repo repeats for Qwen3.6 and Kolibri (session spread +-14 checks);
  (5) Kevin's open decisions - retire events/paths from ranking, declare Qwen3.6+provisioning as the
  reference config, the 6 GiB worker cap for nimble, and the civil_comments anomaly.
- 2026-10-08 QUEUE CLOSED, gpt-oss-120b on 64 GB: asked whether a re-quantized 120B could now fit; the
  answer is no, and the registry says why - **every published build is 62.6-65.4 GB** because the MoE
  experts are native MXFP4 and the quantizers do not requantize them (the whole Q2_K..Q8_0 spread is
  0.83 GB; smallest = unsloth Q3_K_S at 62.56 GB = 58.26 GiB against 58.46 GiB usable, and a 32k KV
  pushes it ~1.4 GiB over). Nothing downloaded. Revisit only if an expert-pruned build appears or RAM
  exceeds ~70 GB. Evidence and pins: `ai_bench/queue-20261008-gpt-oss-120b/{RESUME.md,staged.json}`.
  Also recorded: the 20B we DO run needs the official ggml-org GGUF (every llama.cpp build rejects the
  Ollama-store blob, `unknown model architecture: 'gptoss'`).
- 2026-10-08 (deeper pass, same day): the biggest correction to the lab's own numbers so far, plus two
  new instruments. `census.py` classified **all 178 sessions on disk**: 94 perfect, 44 genuine model
  errors, **23 replies truncated inside their thinking** (`stopReason=length` with no tool call, which
  is what ends the agent loop) and **17 external kills** - so **40 of 84 sub-perfect sessions (48 %)
  are harness or platform artifacts, not model errors**. `witnesses.py` splits the truncation class by
  cause: **reply cap** (19 witnesses, `completion == allowance` exactly, thinking 12k-209k chars) and
  **context exhaustion** (6 witnesses, prompt 32,475-32,764 at a 32,768 served context; 4 of those 6
  still scored well). Two of the three causes are just small harness constants.
  - **Fix for the reply cap, measured**: `truncation-20261008-v1/v2` raise it 12,288 -> 32,768 (one
    declared change, wall unchanged). MiniCPM5-2B then scores **76/76, 66/70, 75/75 = 217/221** - and
    `paths` was the exact task that collapsed to 9/75 twice for it - and gpt-oss-20b scores
    **75/76, 66/70, 73/75 = 214/221**. Both had a 33 % sweep collapse rate before; both are 0 % now.
    The Strata half is a rate too: `reasoning_budget_tokens: 6144` in ten fresh roots -> **10/10 at
    70/70**, with the engine's truncation diagnostic still firing in 2 of them and **both scoring
    70/70** - the budget moves the cut after the work instead of removing it.
  - **Provisioning raised and verified** (`provision-20261008-v1`): served context **131,072** and the
    host descriptor **131,072/32,768** (host window patched through the harness's own `configuration()`,
    so the frozen harness and every historical manifest stay valid), plus llama.cpp's
    `--reasoning-budget 6144` with a wrap-up message. Read back from the run itself: `n_ctx_slot =
    131072` in all five session logs, both flags in the launch command, 131072/32768 in `models.yml`,
    no hang. Tasks 76/76, 67/70, 75/75 = **218/221** (215/221 unprovisioned) at ~2x wall.
  - **Strata at a raised context**: `--max-context` 32,768 -> **65,536**, verified from the engine's
    startup line, with the thinking budget. 4 of 5 runs at 70/70 with zero truncation diagnostics. The
    one 7/70 was the relay's `quota_unknown` marking a harness-level budget failure (the harness kills
    the session on `budget.failure`) - fixed by wrapping the relay's Budget in the root. Cost: free
    physical 3.5-5.4 GiB at 64k vs ~10 GiB at 32k, mostly the context-sized prefill buffers.
  - **Fastest successful combo, measured**: the fastest models fail the hard axes - gpt-oss-20b
    (159 s/task) repo **0/78** (broke the import) and longctx 15/40; MiniCPM5-2B (176 s/task, 122 tok/s)
    repo 43/78 after looping to its 48,000-token quota, though longctx 40/40. The fastest *successful on
    the whole suite* is **Qwen3.6 + provisioning** (551/565, 274 s/task, the only one passing repo 78/78
    AND longctx 40/40), 1.6x faster per task than Kolibri (430 s/task, 99.8 %).
  - **Provisioned six-task sweep** (`newtasks-ctx-20261008-v1`, Qwen3.6): events 76/76, ledger 70/70,
    paths 75/75, ledger2 212/226, repo **78/78**, longctx **40/40** = **551/565**. The frozen three are
    perfect for the first time, `repo` improved 75 -> 78, and the residual shortfall is now only the 14
    Unicode-digit checks in ledger2. longctx was solved first try in 108.6 s / 3,817 tokens, so at n=1
    it saturates for this model and needs a harder variant.
  - **Long-context task**: `legacy.py` is 222 KB / ~65k tokens / 1800 helpers with one wrong function
    and a minimal-edit rule; reference 40/40 vs starter 15/40, scored in 0.32 s (an O(n^2) ast loop had
    taken 63 s, past the relay's 30 s scorer limit). Six-task provisioned root
    `newtasks-ctx-20261008-v1` = frozen three + ledger2 + repo + longctx.
  - **Correction to the census**: the biggest sub-perfect bucket (50 of 99) is prose-quits that are
    actually *completion summaries* - model self-verification failure, not a harness misread - so the
    harness/platform share is **45 of 99**. Others' tweaks, with sources and what does/doesn't apply:
    `local-llm-lab/HARNESS-TWEAKS-2026-10-08.md`.
  - **The same class bit the best model in a fresh run**: in the Swift five-task root, the frozen
    ledger scored **7/70** while `ledger2` (containing those same 70 checks byte-identical) scored
    **226/226** in the same sweep - the wire shows the third turn using exactly 12,288 of a 12,288-token
    allowance with no tool call. Re-baseline (events/ledger/paths/ledger2/repo): Qwen3.6 74/66/75/212/75,
    Swift 76/7/75/226/**43** (43 = the starter's score: no cross-module fix at all), Nemotron
    76/67/75/223/75. `repo` is the first orthogonal discriminator the suite has produced.
    Kolibri's completed sweep is the best row in the series: **76/69/75/226/78 = 524/525**, the only
    configuration perfect on the 226-check battery and the only one that solves the multi-file task -
    so the new tasks REORDER the top group (Kolibri ahead of Swift by 97 checks).
  - **Fix for the measurement, built and verified**: `events` and `paths` are saturated (76/76, 75/75
    at every good configuration) and the frozen ledger's 70 checks put nearly all of their
    discrimination in five of them. New `new_tasks_20261008.py` = **`ledger2`, 226 checks** (the frozen
    70 with identical indices, + 106 labelled traps + 50 random valid ledgers), verified frozen
    reference 226/226 vs the task's own buggy starter 62/226. Re-scoring the 62 artifacts already on
    disk splits the top group **208-226**, where the frozen battery showed a 2-check spread; the
    sharpest single trap is `csv-shape/lone-cr-terminators`. New task #2, `new_tasks_repo.py`, is a
    five-file cross-module repair verified 78/78 reference vs 43/78 starter. Live root
    `newtasks-20261008-v1` runs all five tasks through a superset scorer.
  - The aggregate now separates arms (`+MTP`, `+ledger2`) and reports a **collapse rate** (top group
    0 %, MiniCPM/gpt-oss 33 % historically, the weak models 100 %). Queued with a decision needed:
    raise the served context (fixes the context cause and finally exercises 262k; the host's declared
    `contextWindow` sits in the frozen harness), the Strata thinking budget at n >= 10, and
    re-baselining the top group on the two new tasks. Read `ai_bench/new-items-20261007/REPORT.md`.
    Live validation, one Qwen3.6 sweep in `newtasks-20261008-v1`: events 74/76, ledger 66/70,
    paths 75/75, **ledger2 212/226** (the same Unicode-digit profile the offline re-score predicted
    for this configuration) and **repo 75/78**, whose three misses are the single named defect
    `len(account)` instead of the UTF-8 byte length in the append path.
    Two reading rules: `clean_finish` / `exit 143` / `quota_unknown` are **not** failure signals on
    this harness (they appear on 70/70 runs), and attribute a failure from the engine log plus the
    per-turn `stopReason` before counting it as the model's.
- Kolibri-1 (78B MoE, 3.46B active) PROBED - the RAM payoff, and the configuration matters as
  much as the model. With all routed experts in system RAM it decodes 38.2/34.1 tok/s when the
  experts are mmap-faulted, but that config FAILS the harness (prefill 349 -> 170 tok/s once the
  file cache is cold, against a ~9.5k-token one-shot prompt). With `--load-mode none` the same
  model gives **prefill 881/972 tok/s and decode 44.4/43.0 tok/s**, load 27.7 s, min free
  physical 9.8 GiB, peak GPU 3.88 GiB, tool-call path passing. Q3_K_M 37.5 GB from Hob-forge
  revision 5d285d87 on the community hob-b11434 build (kolibri1 patch; stock llama.cpp cannot
  load it). That is 3x the parameters of the dense 27B at 10x its speed. Read
  `staged-kolibri-20261007/REPORT.md`; the coding screen is running in `candidates-20261007-v7`
  (v4/v5 aborted on the frozen teardown grace and v6 on the 90 s host smoke - both diagnosed,
  and the grace fix is documented in v6/v7).
- Kolibri-1 SCREENED and it is the best local coding result yet: **events 76/76, ledger 69/70,
  paths 75/75**, every task clean and inside the 720 s wall (240.9 / 240.5 / 358.0 s, 7.8k / 7.6k
  / 11.6k tokens) with full usage reporting and no quota anomaly. First local candidate with two
  fully correct-and-clean tasks in one clean run. Read `candidates-20261007-v7/REPORT.md`; repeat
  before treating it as a verdict.
- Swift Bonsai 2 PQ2 DONE and its missing row filled: `candidates-20261007-v8` ran with one
  declared change (quota_unknown non-fatal - the 2026-09-30 sweep aborted there, which is why its
  `paths` never started) and scored **events 76/76, ledger 70/70, paths 75/75**, reproducing both
  earlier scores exactly. By one ledger case Swift is the highest-scoring local candidate, ahead of
  Kolibri-1 (76/76, 69/70, 75/75). Effective 44.8-47.3 tokens/wall-second. Repro note: events and
  ledger are now 2/2 identical two days apart and across the 32 -> 64 GB change, unlike Strata's
  ledger (7/70 vs 70/70) and Gemma's events (76/76 vs 75/76) - non-reproducibility is task- and
  model-specific, not a blanket property of the harness. Read `candidates-20261007-v8/REPORT.md`.
- FIRST APPLES-TO-APPLES THROUGHPUT TABLE: `throughput-20261007` (one script, one protocol, one
  server at a time). Decode tok/s at 1k / 4.9k prompts: ling 226/225, minicpm5-2b 188/174,
  spark-4b 106/103, granite3-moe-3b ~84, swift-bonsai 65/63, gemma-26b-a4b 59/55, **kolibri-1-78b
  42/41**, qwen3-30b-a3b 35/34, qwen3-coder-30b 34/35, nemotron-3.5-lightning-30b 35/34,
  qwen38-27b dense 5/5. So yes - several already-tested models are faster in raw decode, but only
  minicpm among the fast ones also scores well. Engine control: identical A3B on b10883 vs b11461
  is within noise. Read `throughput-20261007/REPORT.md`.
- ARCHITECTURE of the four >=90%-success models, read from their GGUF headers
  (`local-llm-lab/arch-check-20261007.json`): **two are MoE** - Kolibri-1 78B (`kolibri1`, 384
  experts/6 active) and Gemma 4 26B-A4B (`gemma4`, 128/8) - and **two are dense** - MiniCPM5-2B
  (`llama`) and Swift Bonsai 2 PQ2 (`qwen35`, ternary). CORRECTION: Swift was labelled MoE in the
  first throughput report; it is dense, and that report now carries the fix plus a verified-kind
  section. Implication: the two fastest in that group are the two DENSE models, both fully
  GPU-resident (MiniCPM 124 eff / 181 raw, Swift 45 eff / 64 raw); the two MoE models are slower
  (Gemma 19-33 eff, Kolibri 32 eff) but carry far more capacity. MoE + RAM residency buys scale,
  not speed.
- MoE SET FINISHED AND EVERYTHING RANKED (`moe-screens-20261007/REPORT.md`, JSON in
  `local-llm-lab/ranking-20261007.json`). Four new MoE screens: nemotron-3.5-lightning-30b 218/221
  (98.6%, 3/3 clean), gpt-oss-20b 218/221 (98.6%, 3/3 clean, **fastest wall time in the whole
  series: 52-66 s per task**), qwen3-coder-30b 204/221 (92.3%), qwen3-30b-a3b-thinking-2507
  80/221 (36.2%, paths artifact had a Python syntax error). Ineligible: granite3-moe-3b (4096
  native context), gpt-oss-120b (63.4 GB, does not fit).
  Ranking: Swift dense 100.0% > MiniCPM dense 99.55% > **Kolibri-1 MoE 99.55%** >
  Nemotron MoE 98.64% = gpt-oss MoE 98.64% > Gemma MoE 98.63% (2 tasks only) >
  Qwen3-Coder MoE 92.31% > Qwen3-Thinking MoE 36.2% > ling 18.1% > spark 8.1%.
  MoE-only best: Kolibri (accuracy + token rate), gpt-oss (wall-clock speed), Nemotron (middle).
  Conclusion: MoE + RAM buys scale and token efficiency, not speed - the fastest two are dense.
  Same architecture, different training: coder 92.3% vs thinking 36.2%.
- Next MoE candidates researched but NOT run: `ggml-org/Qwen3.6-35B-A3B` (35B total / 3B active,
  Q4_K_M 19 GiB plus MTP and DFlash heads - the preferred publisher, newest small-active MoE);
  Kolibri-1 Q4_K_M only if the desktop footprint is cut (46.6 GB resident) and Q5+/Q8 never fit;
  Nemotron ONYX quants (compact 21.6 GB); Kolibri at 64k-256k context (the publisher validated
  253k tokens on this exact card).
- STRATA ENGINE BUMPED v0.1.39 -> **v0.1.40.3** (upstream published it today 18:01Z) in a COPY, so
  the v0.1.39 tree stays frozen; record in `staged-strata-20261007/upgrade-record.json`. On 64 GB
  with budget 24: LEDGER 7/70, 64/70 and **70/70 correct** in three runs; EVENTS 76/76 and PATHS
  75/75, both correct and clean. Ledger rate across both engines is now five samples - 70/70 twice,
  64/70 once, 7/70 twice - so it completes about 2 in 5 and fails by early termination, not by the
  wall. The bump is correctness- and speed-neutral here (43-57 tok/s effective either way); its
  value is the mmap prompt-path fix, the tool-call rescue, and crash/NaN fixes.
- NEW STRATA LEVER from the RAM: `setup --check` now reports Q2_0 (~48 GB), IQ2_XS (~48),
  IQ3_XXS (~60) and IQ3_S (~62) all fit on this machine, where only IQ1_M fit at 32 GB. Strata's
  own measured table for an RTX 5070 12 GB puts Q2_0 at ~88 tok/s decode / ~571 prompt at 32k
  context, versus our measured IQ1_M 46-49 - about 1.8x at a higher quant. Q2_0 is staging
  (`staged-strata-q2-0-20261007`, 37.6 GB incremental) and will be packed and screened against the
  IQ1_M numbers.
- Q2_0 PACKED AND MEASURED. It does NOT fit at a 24 GiB resident budget: the load drove free
  physical to 0.62 GiB against the 3 GiB floor while filling the GPU expert cache, so the monitor
  wrote STOP (`strata-20261007-v7`, preserved - its native shard is 37.6 GB against IQ1_M's
  29.6 GB). At a DECLARED 12 GiB budget (`strata-20261007-v8`) it is better than budget 24 ever
  was: **ledger 70/70 clean and correct**, 157.4 s, 9,642 tokens = 61.3 tokens/wall-second, engine
  log 70.8-72.4 tok/s decode at a 70.1% expert-cache hit, load 23.8 s, min free physical 4.95 GiB
  with every floor holding. Against IQ1_M's 43-57 effective / 46-49 decode that is ~1.5x, at a
  smaller budget, and it is the full model rather than the Coder's half-experts build. Their
  advertised ~88 tok/s is not reached; we measured ~72.
- Q2_0 SECOND LEDGER SAMPLE (`strata-20261007-v9`): 70/70 clean and correct, 137.2 s, 8,644 tokens
  = 63.0 effective tok/s. Q2_0's ledger is 2/2 complete-and-clean against IQ1_M's 2/5, and the full
  Q2_0 sweep is 221/221 with all three tasks clean. Read `strata-runs-20261007/REPORT.md`.
- PLANNING PROBE: Q2_0 was given only facts (machine, constraints, measured tables, on-disk
  inventory, anomalies) and asked what to do next, with no plan or queue. It matched my top priority
  unprompted - reproducibility and n>=3 re-runs, MiniCPM's paths anomaly first - and added a
  gpt-oss token-frugality audit and load-vs-agent-time reporting. It missed the Kolibri long-context
  test, the engine question and new-model acquisition (my brief listed only on-disk models), and it
  disagreed on the dense 27B, which existing data settles: at ctx 8192 it still decoded 5.0/4.8 tok/s.
  Three attempts were needed (high reasoning armed the paging guard; low reasoning swallowed the
  budget; only `reasoning_budget_tokens: 2000` produced visible content). Comparison:
  `local-llm-lab/plan-comparison-20261007.md`; baseline pre-registered in
  `local-llm-lab/my-plan-20261007-pre-registered.txt`.
- ITEM 1 (RATES) DONE, 12 repeats in fresh roots plus the historical samples. Task scores across all
  roots: kolibri events 76,76,76 | ledger 68,69,70 | paths 75,75,75 (221/221 on its third sample);
  nemotron 76,76,76 | 67,68,68 | 75,75,75 (218-219/221, the most stable large config); gpt-oss
  75,76,**0** | 68,65,66 | 75,75,75 (218, 216, and one 141/221 from an all-or-nothing events
  collapse); minicpm median 96.8 % over six sweeps with paths 4/6 full marks; qwen3-coder 204/197/202;
  swift 221/221 and 146/146; strata Q2_0 ledger 70,70,**7**,70 (3/4 - one sample shows the same
  early-termination mode the Coder pack has, so the quant did not fix the ledger instability) and
  events/paths full; strata IQ1_M ledger
  7,70,7,64,70 (bimodal). CONCLUSION: events and paths are stable, LEDGER is where everything loses
  points, and each model has ONE characteristic failure mode - which is exactly what the rate
  convention is for. Two harness causes found and fixed: a strict-vs-relaxed quota-guard template
  mismatch, and the Strata roots needing `configure` before `screen` (the engine reads its run
  config, not run.py's constants). Distribution data: `local-llm-lab/rates-20261007.json`.
- ITEM 3: Kolibri-1 passes the publisher's long-context test at EVERY size - 3/3 planted codes at 32k,
  65k, 131k and **262k (206,188-token prompt)**, VRAM 4.5 -> 7.3 GiB, free physical ~9 GiB, load
  25-28 s. `kolibri-ctx-20261007/REPORT.md`. So our 32k protocol is a choice, not a limit.
- ITEM 4: **Qwen3.6-35B-A3B Q4_K_M** (ggml-org baec3ebe + MTP/DFlash heads) is the best large model
  here: **219/221 = 99.1%**, 3/3 clean, 569 s, 38.1 effective tok/s, 24 GiB of RAM headroom (Kolibri
  needs 8-9 GiB for the same class at 32 tok/s). Bench: 46.14/46.17 tok/s decode plain, and
  **67.06/62.06 with its MTP head (+45%/+34%)** - the first speculative-decoding gain that matters
  here. Roots v24 (plain) and v25 (MTP). `staged-qwen36-20261007/REPORT.md`.
- ITEM 6 SUBSTITUTED (stated, not dropped): the IQ2_XS/IQ3_XXS download comparison needs ~113 GB against
  129.5 GB free and ~2 h, with bounded expected value since a better quant does not remove the
  behavioural ledger failure. Instead: the resident-budget curve on the Q2_0 pack already on disk.
- ITEM 6 SUBSTITUTE DONE: at 12 GiB the Q2_0 ledger reads 70,70,7,70 (3/4) with 4.95 GiB free physical;
  at 8 GiB it reads 70,70,70 (3/3) but one session sampled **2.990 GiB, below the 3 GiB floor**, so the
  monitor stopped it (agent already finished, score stands; v16-1 preserved). Events/paths full at both.
  Counterintuitive and worth keeping: a LARGER resident budget leaves MORE free RAM here (fewer expert
  reads = less page-cache pressure). Keep 12 GiB; do not lower. Config restored to 12 GiB / reserve 2000.
- PLAN COMPLETE: all eight pre-registered items done or explicitly substituted. Item-by-item summary in
  `local-llm-lab/PLAN-EXECUTION-20261007.md`, including five new queue items the work created (n=3
  MTP-vs-plain arms; rate sets for Kolibri/Nemotron/Qwen3.6; a probe into the ledger's early-termination
  behaviour; the Strata tool-call-rescue effect; Qwen3.6 at long context). All five of those were then
  executed on 2026-10-08 - see the top entry and `new-items-20261007/REPORT.md`.

## 2026-10-07 (later): what the extra RAM unlocks, being retested now

- Qwen3.8-27B Q4_K_M is NOT viable for the harness here, and now for a measured reason: on
  llama.cpp b11461 with `--fit on`, decode is 4.28/4.05 tok/s (4.45/3.99 with the MTP head,
  4.62/4.26 with DFlash, ~33% draft acceptance) at context 32768, because ~half of its 18.97 GB
  sits in RAM. Tool calls and reasoning separation pass; only speed fails - 720 s buys ~3,000
  tokens against the 14k-24k the reference runs needed. `candidates-20261007-v3` is prepared and
  audited but deliberately unrun. Read `staged-27b-20261007/REPORT.md`.
- Lesson recorded: host RAM removes the residency barrier, not the throughput barrier. The shape
  that does benefit is a large MoE with a small active parameter count - which is the next test
  in flight: Kolibri-1 (78B total, 3.46B active, Apache-2.0) Q3_K_M 37.5 GB with all routed
  experts in system RAM (`--cpu-moe`) on the patched community build that supports the kolibri1
  architecture, staged and sha256-verified in `ai_bench/staged-kolibri-20261007`.

- A3B all-experts-in-RAM DONE: `a3b-offload-20261007-v1` re-ran the exact configuration the
  paging guard killed at 32 GB (48 CPU expert layers, every routed expert in system RAM). It
  completes now - short 34.82 / long 33.11 tok/s median, min free physical 27.61 GiB where the
  old attempt aborted at 3.69 GiB - and is the fastest placement in that family, but only
  +2.7%/+1.2% over the 32-layer baseline, so "no longer impossible" is the claim, not
  "measurably better".
- NEW: Qwen3.8-27B Q4_K_M (18.97 GB) plus its MTP (1.68 GB) and DFlash (1.09 GB) draft heads
  staged from ggml-org at revision 71bc7b62, with llama.cpp b11461 (published today 06:50Z,
  Windows CUDA 13.4, asset digest 62c91b76...). This is the first model here whose weights
  cannot sit in 12 GB of VRAM at all and which therefore depends on the new host RAM; it is
  the strongest candidate yet for the coding screen. Staging path
  `ai_bench/staged-27b-20261007`, probe and screen to follow.

## 2026-10-07: RAM MODULE INSTALLED AND VERIFIED - 64 GB, dual channel, gates pass

The install is DONE and verified; the pre-install handoff note it replaced is
preserved in local-llm-lab/RAM-INSTALL-2026-10-07.md and the evidence is in
local-llm-lab/RAM-VERIFY-2026-10-07.md. Read that verification file first.

- Installed and trained at rated speed: DIMM1 SK hynix HMCG88AGBUA084N plus DIMM2
  Kingston 9905782-147.A00G (the ordered KVR56U46BD8-32, 2Rx8 CL46 non-ECC), both
  34359738368 bytes, Speed AND ConfiguredClockSpeed 5600 on both - no down-bin to
  4800/5200.
- 63.46 GiB visible (32 GiB showed 31.46 before, so the same 0.54 GiB reserved,
  nothing withheld). Win32_PhysicalMemoryArray MemoryDevices 2, MaxCapacityEx
  67108864 matches the 2 x 32 GB ceiling.
- Dual channel is active, proved by bandwidth rather than a BIOS read: 16-thread
  memcpy moved 71.4 GB/s of combined traffic (single-thread 39.7), i.e. 79.7% of
  the 89.6 GB/s DDR5-5600 dual-channel peak and well past the 44.8 GB/s
  single-channel ceiling; an 8-thread read measured 49.7 GB/s. BIOS-level
  "Memory Channel Mode = Dual" was not read - Windows cannot enter BIOS.
- No memory-corrected errors. The two WHEA-Logger ID 17 warnings at boot are the
  RTX 5070 PCIe link (VEN_10DE&DEV_2F04), the same pair that already occurred on
  2026-10-02, 10-04 and 10-06, i.e. pre-existing. One Kernel-Power 41 / EventLog
  6008 records the install-time power removal at 01:51:32, not a current fault.
- Frozen preflight passed with no lock created (it is read-only):
  physical_available 44.14 GiB vs the 9 GiB gate, commit headroom 56.89 vs 8,
  GPU free 10.60 vs 7.5, no resident engine on 8080/11434, ollama absent.
- Platform change to record everywhere from now on: 32 -> 64 GB. Machine now
  DARKTEXAS at 64 GB DDR5-5600 dual channel, ~89.6 GB/s theoretical.

Not done yet, and all still Kevin's call: BitLocker status was never confirmed
(the box booted without a recovery prompt after the hardware change, which is
evidence it was off or suspended); the real load test (first queued lab run) and
the optional mdsched.exe reboot are pending; the 6 GiB worker-private cap and the
rate-over-n-runs reporting question are still open decisions.

Resume queue after the install is unchanged - see RAM-INSTALL-2026-10-07.md
Part 4 (frozen preflight, finish the decision track in a NEW root, then the Strata
ledger with a larger declared budget, then Gemma 4 26B-A4B). No run starts
without Kevin's ready message.

## 2026-10-07 resume session: decision track finished, three roots prepared

Kevin said resume, so the queue is running. No gate changed, no app killed, no reboot, one
inference workload at a time.

- Nothing to free: GPU was 1411/12227 MiB used, all desktop compositing (no model server),
  and 42.35 GiB physical was free. The only cleanup was `wsl --shutdown`, which reclaimed the
  idle utility VM (Ubuntu already Stopped, 828 MiB) and left free physical at 44.25 GiB.
- Decision track DONE on the 18-window set. New root `decisions-20261007-v1` (runner
  byte-identical to the corrected -v2) screened the three staged models that had never run
  on `/v1/systemone`: laya 14/18 (0/4 caught, 0/14 false alarms, p95 183 ms), kev0 14/18
  (0/4, 0/14, p95 169 ms), lev 14/18 (1/4, 1/14, p95 345 ms, the only one whose p crosses
  0.85). Peak server private 4.32 GiB vs the 6 GiB cap; audit clean.
- Determinism answered: lev and laya are bit-identical across two full passes of all 18
  windows (`evidence/diagnostics/determinism.py`), so a single screen on this endpoint IS a
  point estimate. The "rate over n runs" concern belongs to the mimo agent harness, not to
  `/v1/systemone` scoring.
- CORRECTION: nimble is NOT blocked and the 6 GiB worker cap is NOT open. Kevin authorized
  8.0 GiB on 2026-10-05 and `decisions-20261005-v3` ran nimble under it (15/18, 2/4 stalls
  caught, 1/14 false alarms, p95 596 ms, 6.94 GiB private) - the best 18-window result of all
  six staged models. RAM-INSTALL-2026-10-07.md Parts 4-5 were corrected in place.
- Still true: 18 archived windows cannot rank these models - four of six never cross 0.85 at
  all. The published suite is the substrate.
- Published suite DONE in `bespoke-suite-20261007-v1` (inputs re-proved locally, 13/13 MATCH,
  3,880 records). Macro/micro: nimble 75.65/77.11 and kev4 74.42/75.28 (carried from
  2026-10-05), then lev 68.41/71.11, kev0 61.21/63.27, laya 58.01/62.04. The suite OVERTURNS
  the 18-window reading: lev, the only new model whose p crossed 0.85 there, is 6 macro points
  behind kev4. lev's loss is one subset (summeval-consistency 0.194, under-predicting the top
  of a 121-of-144 level-4 scale); laya fails the same subset (0.215) despite winning
  civil_comments 0.937 and vitaminc-dev 0.790. `score` is the weak primitive for all five.
- Strata ledger DONE, and it overturns the old conclusion: `strata-20261007-v1` scored 7/70 in
  79 s (session ends by itself after 3 turns with an empty final message) while the
  byte-identical repeat `strata-20261007-v2` scored **70/70 clean and correct** in 289.5 s.
  Same declaration, same model, 1 of 2 runs clean. The 2026-10-06 "wall-bound" note is
  corrected: run 1's 7/70 did not need more time, and run 2 finished inside 290 s. Strata
  screens must be reported as a rate over runs.
- Upgrade effect: engine load 16.4 -> ~36 s, decode 6.5-9.6 -> ~46-49 tok/s (5-7x), ledger now
  completable. Cost: budget 24 holds only 4.3-5.1 GiB free physical (floor 3) and 0.79-0.87
  GiB free VRAM (floor 0.5) at its lowest; use 16-20 GiB for longer tasks.
- Gemma 4 26B-A4B DONE - first time it has ever run here. `candidates-20261007-v1` ran clean
  but produced unscored zeros (`abnormal_evaluator_exit 2`) because a new candidates root must
  carry `source/staged_tasks_20260922.py` and its siblings next to the generated relay; the
  relay's scorer executes that file from the relay's own directory and the frozen manifest
  cannot catch the omission. Re-scoring the preserved artifacts: events 76/76, ledger 66/70,
  paths 75/75. `candidates-20261007-v2` carries the fix and is runner-scored: events 75/76,
  ledger 69/70 (wall-cut at 673 s), then the sweep aborted on the `quota_unknown` guard (the
  same accepted outcome as the Swift run), so paths did not re-run. Envelope: min free physical
  28.5-31.0 GiB vs 2.65-2.94 GiB at 32 GB. No clean three-task sweep in two runs.

Delta since 2026-10-05, in short:

- The staged decision track was executed by later sessions (decisions-20261005-v2
  and -v3): julia-1 11/18, kev4 14/18 with 0/4 stalls caught, nimble blocked by
  the 6 GiB worker-private cap. The Bespoke 3,880-decision suite ran: kev4 macro
  74.4 / micro 75.3, nimble 75.7 / 77.1 (about Jev parity).
- Strata v0.1.39 screens: events 76/76, paths 75/75, ledger 7/70 wall-bound at
  about 7 tok/s decode.
- CORRECTION: the Strata endpoint DOES honour per-request sampling. The probe
  that suggested otherwise compared empty `content`; see
  staged-strata-20261005/SAMPLING-PROBE-NOTES.md. Also: temperature 0 is not
  seed-stable on this engine, and a trivial prompt at 200 tokens still ends at
  finish_reason=length with no visible content.
- Newer upstream than our pins: llama.cpp b11461 (we staged b11429), Strata
  v0.1.40 / v0.1.40.1 (Windows RAM-budget and large-page fixes; NVIDIA decode
  within about 3% of 0.1.39, so it does not fix the disk-bound ledger).
- Pending Kevin's decision: the 6 GiB worker-private cap that blocked nimble, and
  reporting screens as a rate over n runs instead of a single run.

## 2026-10-03 resume check: still 32 GB, HOLDING on the RAM module

- Live check 2026-10-03 06:56 UTC: Win32_PhysicalMemory shows DIMM1 only
  (32 GB HMCG88AGBUA084N, configured 5600). DIMM2 still EMPTY, so the ordered
  Kingston KVR56U46BD8-32 has NOT been installed. 31.46 GiB visible.
- Fixed-runner preflight (candidates-20260929-v1/run.py preflight) FAILED on the
  unchanged 9 GiB gate: physical_available 8.55 GiB, commit headroom 35.19 GiB,
  GPU free 10.37 GiB, ollama.models [], wsl_servers empty. No lock created; a
  failed preflight does not write RUNNING.lock.
- Nothing was run: no inference, no download, no install, no reboot, no gate
  change, no file moved. Deliberate STOP files remain in v6/v7 and the documented
  relay_*.py leftovers remain in v2-v8; all left as they were.
- Noted, not touched: ollama.exe plus "ollama app.exe" running on 11434 with no
  model loaded, and two omp.exe sessions besides this one. BitLocker still
  undetermined (manage-bde -status denied without elevation).
- Decision (Kevin, 2026-10-03): HOLD until the RAM module is installed. Do not
  start inference, downloads, installs or a reboot before that. After install:
  re-run the precheck, record the 32 -> 64 GB platform change, keep ALL gates
  unchanged (9/8/7.5 GiB initial, 3/2/0.5 GiB floors, 6 GiB worker cap), keep
  .wslconfig memory=8GB, and use a NEW root for any re-run.

## 2026-10-05 news scan: no action taken, still HOLDING

Read local-llm-lab/NEWS-2026-10-05.md. Nothing downloaded, installed, loaded or
run; all gates unchanged. Headlines that matter to us:

- Decision models reached mainline. llama.cpp v0.6.0 (2026-10-05) and Ollama
  0.35.0 (2026-09-29) both ship /v1/systemone (Jev/TypeSafe API) with models
  laya, julia-1, lev, openjev(+vision), kev, nimble, clef. Bespoke Labs publishes
  a 3,880-decision, 13-dataset human-labelled suite -- a far better substrate
  than our 18-window set for the decision screen, and nimble 9B / tev1 4B
  should clear our 3 s latency gate (jeff/gliner failed it). Discrimination is
  the open question, not speed.
- Our llama.cpp pin (b10883) is two releases behind v0.5.0 / v0.6.0: DFlash2 and
  MTP speculative decoding, CUDA W4A4 NVFP4 for Blackwell, Qwen4Exp support,
  Gemma 4 fixes. v0.6.0 breaks session format (version 11) -- new root only.
- Prism: 1-bit Q1_0 and ternary Q2_0 are merged upstream; Ternary Bonsai 2
  (PTQ1_0/PQ2_0) still needs the Prism fork. Our v8 result stands.
- Strata pin is stale: staged v0.1.27, current v0.1.39 (2026-10-04). 32 GB
  low-RAM is now vendor/community-confirmed, and the API surface is three shapes
  (OpenAI, Anthropic, Responses/Codex). Re-pin before any run; resolve the model
  licence (staged apache-2.0 vs Qwen Community License 1.0).
- Gemma is NOT unblocked: the "TQ3_1S ternary" Gemma GGUF is 12.9 GB, larger
  than the IQ2_M we already failed on. It stays RAM-blocked until the module.

## 2026-10-05 staging: decision track and Strata re-pin (no inference)

Read local-llm-lab/STAGING-2026-10-05.md. Staged and offline-verified only; no
model loaded, no scored run, no app closed, gates unchanged, still HOLDING.

- Decision runtime: llama.cpp b11429 = v0.6.0 (CUDA 13.4, Windows). llama-server
  and llama-cli run and report 0.6.0-dev. This is the build that serves
  /v1/systemone. Under ai_bench/staged-decisions-20261005/llamacpp-b11429.
- Decision models staged (sha256-verified, revision-pinned): julia-1, laya,
  kev0 (Q8_0) and kev4, lev, nimble (Q4_K_M), all ggml-org GGUFs. Under
  ai_bench/staged-decisions-20261005/gguf. See staged.json.
- New runner root ai_bench/decisions-20261005-v1 (worker.py, score.py, run.py).
  Offline self-test against a mock server passed: 18/18, 4/4 stalls, 0 false
  alarms, warm p95 16 ms. Frozen inputs/labels and the 0.85 threshold / 3 s gate
  are reused, so results will be comparable to jeff/julia/gliner.
- Strata engine re-pinned v0.1.27 -> v0.1.39 (2026-10-04). Windows NVIDIA zip
  sha256 a862bcfa...3813a under ai_bench/staged-strata-20261005. The 2026-09-30
  model GGUF and hashes are untouched. API surface is now three shapes (OpenAI,
  Anthropic, Responses/Codex).
- Licence: the Coder GGUF repo tags apache-2.0 but the Qwen weights are Qwen
  Community License 1.0; local evaluation is fine.
- Deferred (needs app closure): any live screen. Preflight now fails at 6.73 GiB
  free vs the 9 GiB gate. First live steps: `run.py preflight`, then
  `run.py screen julia-1|kev4|nimble`, one at a time, then `audit`.

## 2026-10-05 live decision screen: julia-1 and kev4 run, nimble gate-blocked

Root `ai_bench/decisions-20261005-v2` (v1 preserved: its first live run died on two
runner bugs, documented in v2/README.md). Read `decisions-20261005-v2/REPORT.md`.

- The resource gate was already satisfied at session start: 12.72 GiB free physical vs
  the 9 GiB gate, commit headroom 23.41 GiB, GPU free 9.91 GiB, no resident model, no
  lock. No app was closed and no reboot was used; freeing RAM was never the blocker.
- `screen julia-1`: 11/18, 1/4 stalls caught, 4/14 false alarms, warm p95 638 ms
  (latency gate PASS). Same non-discrimination the CPU screen saw for julia.
- `screen kev4` at `-np 1 -b 512 -ub 512`: 14/18, 0/4 caught, 0/14 false alarms, warm
  p95 430 ms (PASS). It never crosses 0.85; p range 0.344-0.546.
- `nimble` is RESOURCE-STOPPED by the frozen 6 GiB worker-private cap. Its floor is
  6.94 GiB at the minimum batch (`-np 1 -b 512 -ub 512`; `--no-warmup` does not move
  it, so it is the 6.32 GB model, not a transient). All system floors pass in that
  configuration (7.20 GiB free RAM vs 3, commit 17.38 GiB vs 2, GPU free 4.11 GiB vs
  0.5). kev4 fits only at `-np 1 -b 512 -ub 512` (5.26 GiB); batch/slot count is a
  declared run variable (<= 0.017 drift) recorded per run in `command.json`.
- Runner facts worth keeping: the decision/embedding path needs an explicit batch
  (default 512 rejects every frozen window), and `state` encoding is a declared
  variable (identical on julia-1, 0.4949 vs 0.5153 on kev4).
- Audit clean: 8 staged files verified, no lock, no residual server. No gate changed,
  no reboot, no promotion. nimble and the Bespoke 3,880-decision suite await Kevin's
  decision on whether the GPU decision-server track may use a documented
  worker-private cap above 6 GiB, in a NEW root.

## 2026-10-06 published decision suite (3,880 records): decision track answered

Root `ai_bench/bespoke-suite-20261005-v1`. Read its REPORT.md and FLAGS-style RECORD.

- The suite's 13 subsets were rebuilt locally from the upstream raw sources with the vendored
  converters (clone dcfdbd9a at `staged-bespoke-20261005/nimble`, fetcher `fetch_public.py`).
  Every rebuilt payload reproduces the committed `dataset_sha256` and id list byte-for-byte,
  13/13, 3,880 records (1,848 choice / 1,399 noul / 633 score). That is the proof the inputs
  are the published ones.
- `screen kev4` (4B Q4_K_M): macro 74.4%, micro 75.3%, wall 368 s.
- `screen nimble` (Bespoke-Nimble-9B-v3 Q4_K_M): macro 75.7%, micro 77.1%, wall 622 s.
- Published reference: Bespoke-Nimble-9B BF16 74.8 / 75.9; Jev 1.13.0 76.0 / 77.3. Our GGUF
  nimble matches the published BF16 run and sits at Jev parity; the 4B kev4 is 1.2 macro
  points behind nimble and ahead of it on multinli (92.0 vs 88.3) and summeval-consistency
  (81.3 vs 76.4). Score is the weak primitive for both; noul and choice are solid.
- Caveat recorded, not hidden: our serving path is llama.cpp `/v1/systemone`, not the repo's
  PyTorch scorer, so the per-subset comparison against the published table is indicative
  (civil_comments is 20 points high in our run and that is unexplained). Within our own runs
  the comparison is clean.
- No gate changed, no reboot, no promotion. One inference workload at a time throughout.

## Strata ran: v0.1.39, Coder IQ1_M, two of three coding tasks fully correct (2026-10-06)

Root `ai_bench/strata-20261005-v1`; read `REPORT.md` (results) and `FLAGS.md` (the flag
research and the measured low-RAM investigation).

- Engine pinned and installed from v0.1.39 (commit 6f32ec07, main == tag) using the staged
  pack. Chosen flags: `--family coder --model IQ1_M --context 32768 --vision no --low-ram on
  --kv int8 --draft-vocab en --yes --no-start`, then `--calibrate` (measured 19.5 -> 22.5
  tok/s with `--pcie-frac 0.75 --spec-min-p 0.50`), plus declared sampling (temperature 1.0,
  top_p 0.95, min_p 0.0, top_k 64; the lab's top_k 0 cannot be expressed), `open_browser`
  false, `--vram-reserve-mib 1500`.
- The real work was the low-RAM variant. `--resident-experts` (setup's default), plain
  `--mmap-experts`, and `--resident-budget-gib 20` each drove free physical to 1.92-2.77 GiB
  against the 3 GiB floor; the user-requested minimal-startup reboot was executed and verified
  (free 15.14 -> 18.19 GiB, GPU used 1313 -> 721 MiB) and the engine absorbed it, tripping
  again at 2.77 GiB. **`--resident-budget-gib 4` plus `STRATA_LOOKAHEAD=0` holds 9.6-10.5 GiB
  free and every floor held through all runs.** No floor, threshold or metric was changed.
- OMP 18.3.1 screens, 720 s wall each: events 76/76 correct, paths 75/75 correct, ledger 7/70
  (wall-bound: decode is 6.5-9.6 tok/s on this disk-bound card, prompts of 9.4-10.4K tokens
  read at ~550-670 tok/s, so 720 s allows only ~5,000 output tokens). The engine is much
  slower than its 64 GB figures by design; the RAM module is the lever, not a flag.
- Probe passed: deterministic greedy answers, the config sampling is read, per-request `seed`
  forwarded, OpenAI tool call and full tool roundtrip work. `quota_unknown` on every run
  (engine usage-reporting gap, as with Prism) makes token totals lower bounds.
- The minimal-startup suppression applied for the experiment was RESTORED the same day
  (2026-10-06 13:13 UTC, `boot-status.json` -> `"state": "restored"`, verified, zero
  failures, startup shortcuts and Run values back). A stale September `STOP` in
  `mimo-harness-20260925-v1` (the relay's stop path) aborted sessions in 0.0 s until it was
  moved to `STOP.stale-20260925-preserved`.


## 2026-09-30 memory upgrade: module ordered, NOT installed

Full record: C:/Users/kevin/local-llm-lab/RAM-UPGRADE-2026-09-30.md. Summary:

- Blocking constraint confirmed as HOST RAM, not VRAM: Gemma 4 26B-A4B
  UD-IQ2_M at 32k bottomed 2.65-2.94 GiB against the 3 GiB floor across v6,
  v7, v8 (about 14.5 GiB resident, 10 GB of it mmapped); MiMo larger-output
  ledger stopped at the RAM guard 2.94 GiB; Strata / Qwen3.8-Flash-Next
  original builds need about 26.6-43.8 GiB host RAM and stay out of reach at
  32 GB.
- Decision: UPGRADE, do not replace. A used parity replacement is about
  $1,220-1,420 (an RTX 5070 alone is $646 used); 128 GB costs $1,464 used or
  $1,400-1,900 new, so it is unreachable near the $1,000 budget. A platform
  swap would also invalidate the pinned baseline.
- Ordered: used Kingston KVR56U46BD8-32, 32 GB (1 x 32 GB) DDR5-5600 2Rx8 CL46
  non-ECC UDIMM, eBay item 800722063307, seller paymore_taylor, $379.99 free
  shipping, ETA Oct 2-6, returns through 2026-11-04. This is the correct spec
  (DDR5 UDIMM non-ECC; DIMM2 is empty; 2 slots, firmware cap 64 GB).
- Cheapest new for the same capacity was $528 (Newegg marketplace Crucial
  CT32G56C46U5); CompSource had the same Kingston SKU new at $565.61.
- Expected effect: single channel to dual channel, about 44.8 to about
  89.6 GB/s, plus about 14 GiB of extra headroom for model residency. Gemma
  and MiMo no longer need the minimal boot; Strata Q2_0/IQ2_XS/IQ3_XXS become
  feasible, IQ3_S stays borderline.
- Next actions: check/suspend BitLocker; install into DIMM2; verify two 32 GB
  modules at 5600 and 64 GB visible plus BIOS dual-channel; watch for a
  4800/5200 down-bin. Then re-baseline notes only, keep ALL gates unchanged
  (9/8/7.5 GiB initial, 3/2/0.5 GiB floors, 6 GiB worker cap), keep
  .wslconfig memory=8GB, and use a NEW root for any re-run.
- Pre-install state captured: 31.46 GiB visible, 9.18 GiB free, DIMM1 only
  (SK hynix HMCG88AGBUA084N 5600). No inference was run this session and no
  benchmark was started.

## State at 2026-09-30 session close

Roots v1 through v8 exist under ai_bench/candidates-20260929-*. Reports: v3 (coding
truth after the scorer fix), v4 (cap changes), v5 (effective quota plus ling), v8
(Gemma attempts plus Swift Bonsai). All roots audit clean: 120 protected files, no
lock, no resident model. v6 and v7 still carry STOP files left by resource stops;
clear them before any further run in those roots. A failed attempt also leaves
source/relay_<model>.py, which the next attempt asserts absent, so remove that too.

Gates unchanged and currently passing: 9 GiB initial physical, 8 GiB commit, 7.5 GiB
coding VRAM, runtime floors 3/2/0.5 GiB. WSL is capped at 8 GB (backup at
wsl-cap-20260929/). No reboot path has been used; the minimal-boot apparatus is
intact and last verified 2026-09-24 with zero restore failures.

A 32 GB module is ordered for this machine, recorded by a separate session in the
section above and in local-llm-lab/RAM-UPGRADE-2026-09-30.md. Until it is installed
this box stays at 32 GB, so Gemma stays blocked on host RAM and Strata's original
builds stay out of reach. Any re-run after the upgrade must use a NEW root, keep
every gate unchanged, and preserve the RAM-stopped runs as constrained-platform
evidence.

Local results, best first, cases passed: Swift Bonsai 2 PQ2 on the Prism runtime
146/146 (its ledger run stopped by a Prism usage-accounting gap, paths not run);
MiniCPM5-2B Q8 218-220 of 221 across three runs, with one paths outlier at 9/75
showing the harness is not reproducible run to run; Ling-3.0-tiny 40/221;
Spark-X2.5-4B 18/221. Decision models: jeff and gliner do not discriminate on the
archival set and both miss the 3 s latency gate (6.27 s and 27.56 s); julia passes
at 0.82 s but calls three labelled negatives stuck.

Staged and verified, nothing installed or run: queue-20260929-v2 (the 12 GB
addendum; ling complete, swift two thirds, gemma blocked by host RAM) and
queue-20260930-strata (engine commit a79080535d1b2a71a3419a0d97d8e7dca194b0f1,
engine binary v0.1.27 digest-verified, Coder IQ1_M 55.25 GiB with every file hash
matching the pinned revision). Strata's next steps: install with --gguf-dir and
--low-ram on, run the sampling probe, then write the runner revision that drives an
external server rather than launching llama-server.

To resume this conversation: `omp --continue` from C:/Users/kevin/ai_bench, or
`omp --resume` and pick it from the list.

## Current task and stop point

User authorized reviewing Bonsai 2 revisions/variants and recent YouTube
mentions, then trying the new candidates. Research, downloads and isolated
setup are done. The queue has since run to completion. Results are in
candidates-20260929-v3/REPORT.md, with root history in the v1, v2 and v3 RESUME
files. Read:

- candidates-20260929-v1/RESUME.md
- candidates-20260929-v1/BONSAI-REVIEW.md
- candidates-20260929-v1/protocol.json and manifest.json

Screen finished 2026-09-30 UTC. Root history: v1 froze and stopped on the
resource guard (vmmemWSL held 8.31 GiB; the jeff worker peaked at 4.81 GiB,
under its 6 GiB cap); v2 ran the decision items but produced unscored coding
zeros because the root lacked source/staged_tasks_20260922.py, so the scorer
never started; v3 is the corrected root that graded the coding items. .wslconfig
now caps WSL at 8 GB (backup at wsl-cap-20260929/). The 9 GiB gate is UNCHANGED
and was not lowered.

Results: jeff 18/18 windows, warm p95 6.27 s (fails the 3 s gate), 0/4 stalls
caught, 0/14 false alarms. julia 18/18, p95 0.82 s passes, 0/4 caught, 3/14
false alarms. gliner no verdict: the frozen 2048-token cap rejected natural-4 at
2443 tokens. MiniCPM5-2B Q8 events 76/76 but quota_exhausted, ledger 67/70
clean, paths 75/75 clean, so 1/3 correct-and-clean. Spark-X2.5-4B 2/76, 7/70,
9/75, 0/3. Nothing promoted. Audit passed: 120 protected files, no run lock, no
resident model.

Next work: the three-item 12 GB addendum at queue-20260929-v2 is still staged and
undownloaded; gliner needs a decided input-cap policy before it can be screened;
MiniCPM's events quota is a separate declared variable.

Caps decided and applied (v4, v5). Decision cap 2048 -> 4096: measured tokenizer
need is gliner 2555 (2637 with schema), julia 1835, jeff 1951, so only gliner
could hit 2048 and jeff/julia results stand unchanged. gliner then scored 18/18
with 0/4 stalls caught, 0/14 false alarms and p95 27.56 s, failing the latency
gate. Session quota 16000 -> 24000: the v4 relay substitution was INERT
(mimo-harness passes quota=16000 explicitly); v5 overrides the Budget constructor
and proves it (ledger used 17953 tokens, no quota stop). v5 also added ling
(Ling-3.0-tiny Q6_K, hash-verified against the pinned revision; bailingmoe3 loads
in stock b10883): controls pass, events 2/76, ledger 29/70, paths 9/75. MiniCPM
paths scored 75/75, 75/75, 9/75 across v3, v4 and v5 under identical declared
settings, so single-run scores on this harness are NOT point estimates and repeat
runs are required before drawing model conclusions. Read
candidates-20260929-v5/REPORT.md. Not started: the Gemma 4 26B-A4B item (needs the
turboquant fork build) and Swift Bonsai 2 PQ2 (needs Prism b10743).

12 GB addendum ran 2026-09-30 with no reboot (roots v6, v7, v8; read
candidates-20260929-v8/REPORT.md). Swift Bonsai 2 PQ2 on the Prism runtime
prism-b10743-adfffbe: events 76/76 clean and correct, ledger 70/70 correct but
stopped by a Prism usage-accounting gap (quota_unknown), paths not run. That is
the strongest local result in the series. Gemma 4 26B-A4B UD-IQ2_M was
resource-stopped three times (v6 -ngl 27, v7 -ngl 24, v8 -ngl 24 with WSL down and
stale harness sessions ended). Deeper offload fixed the VRAM side (free VRAM 0.96
-> 1.92 GiB against a 1 GiB floor) but host RAM still bottoms at about 2.7 GiB
against the 3 GiB floor, because the model consumes about 14.5 GiB regardless of
offload. Gemma therefore needs the deferred minimal boot or a smaller declared
configuration. Two operational traps: a resource stop leaves STOP in the root and
blocks any later run there, and a failed attempt leaves source/relay_<model>.py
which the next attempt asserts absent; clear both deliberately.

Strata engine reviewed and staged, not installed or run:
local-llm-lab/STRATA-REVIEW-2026-09-30.md and queue-20260930-strata/. It serves
Qwen3.8-Flash-Next by splitting it across GPU, RAM and SSD, and its central claim
("on a 12 GB card your RAM is the problem") matches what we measured with Gemma
on 2026-09-30. The original builds need 37-55 GB resident and stay out of reach on
32 GB, but the Coder pack is documented to run on 32 GB in a low-RAM mode that maps
experts from disk, so the exclusion recorded in BONSAI-REVIEW.md was revised with
a dated update. Pins: engine commit a79080535d1b2a71a3419a0d97d8e7dca194b0f1;
model ISTA-DASLab Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF revision
5348543e0147355ac9cbcb031184a3546350988e with per-file sha256 in staged.json.
Two cautions: on a 12 GB card low-RAM mode is disk-bound and much slower than the
55 t/s headline, so this is a correctness test rather than a speed test; and
Strata is an external server, so the harness needs a new runner revision that
skips the runtime launch and points the relay at its endpoint.

## Resume procedure after ready

1. Read C:/Users/kevin/local-llm-lab/AGENTS.md and ai_bench/AGENTS.md.
2. Inspect current locks/status and run the fixed runner's preflight.
3. Serial actions: cpu jeff, cpu julia, cpu gliner, coding minicpm,
   coding spark. Inspect each result before the next. Finish with audit.
   This queue completed 2026-09-30 UTC across roots v1, v2 and v3. Reuse the same
   shape for the staged addendum in queue-20260929-v2. Note that a new root must
   contain source/staged_tasks_20260922.py or the coding scorer cannot start.
4. Preserve failed evidence. If implementation changes are needed after a
   run starts, use a new version/directory and explicitly document changes.
5. Write results/report, audit protected hashes and owned process cleanup,
   update this file and both AGENTS files, open the report via Open-Document.

Runner prefix (Git Bash compatible):
`python C:/Users/kevin/ai_bench/candidates-20260929-v1/run.py`

Example: append `preflight` or `cpu jeff`. Never run candidates concurrently.
Frozen inputs: 120 hashes verified September 29. No RUNNING.lock was created
because resource preflight did not pass. Recheck live state; notes age.

## What is installed/prepared

- Regular OMP 18.3.1: C:/Users/kevin/.local/bin/omp.exe, on persistent user PATH.
- Global OMP configuration/instructions: C:/Users/kevin/.omp/agent/.
- Default native provider/model: deepseek/deepseek-flash, high thinking.
  Existing DEEPSEEK_API_KEY; no key in these notes. Full normal harness,
  unlike deliberately restricted benchmark sessions.
- OMP setup/verification/approval migration: omp-setup-20260929/.
  Live smoke passed: native deepseek-flash, automatic handoff read, approved
  nvidia-smi command without a prompt, clean exit and empty Windows Job.
  57 source prefixes mapped into 114 patterns; 127 matcher checks passed.
  80 historical PowerShell cmdlets/complex payloads are preserved in the
  migration audit but not automatically allowed as Bash equivalents.
- Jeff v1.1 Qwen3.5 0.8B, Julia-1 and GLiNER2.5-Decide: CPU environments
  and pinned weights under candidates-20260929-v1/.
- MiniCPM5-2B and Spark-X2.5-4B: Q8_0 GGUFs; stock llama.cpp b10883 CUDA.
- Bonsai official PQ2 hash unchanged from September 20. Prism runtime has
  a newer September 25 release; Swift PQ2 is a distinct changed fine-tune.
  Neither newer runtime nor Swift has been measured locally in this queue.

## Results that matter before comparing another run

| Experiment | Outcome | Evidence |
|---|---|---|
| Hosted DeepSeek V4.1 Flash + OMP 18.3.1 | Events 76/76, ledger 70/70, paths 75/75; all clean after documented byte-budget correction | deepseek-flash-20260928-v1/REPORT.md and v2 |
| Local MiMo timeout-only retest | Ledger 7/70, paths 75/75 but not clean, events 76/76 clean; 720 s cap | mimo-timeout-20260928-v1/REPORT.md |
| Local MiMo larger-output/context retest | Ledger 68/70 stopped at RAM guard; paths 9/75 with repeated reasoning; neither clean | mimo-output-20260928-v1/SUMMARY.md and v2 |
| New harness screen on MiMo | Goose 1/3 correct-and-clean; mini-SWE-agent 0/3 | new-harnesses-20260928-v1/REPORT.md |
| OpenJev archival stall screen | 0/4 stalls, 0/14 false alarms at .85; median 11.26 s | local-decisions-followup-20260925-v1/REPORT.md |
| Pi observation-only loop logger | Missed one semantic loop; one false alarm among 48 negative calls | pi-loop-logger-20260925-v1/REPORT.md |
| A3B expert offloading | Qwen3-Coder, 32 CPU-expert layers, 8 threads, 8192 context: 33.90/32.72 tok/s; speed only | a3b-offload-20260924-v1/REPORT.md |

MiMo paths repeated: "Also reject if path contains a newline? Not specified.
I'll allow." 3,043 times. More timeout/output alone did not solve it.
Thinking labels must reflect the actual server request/output; read
mimo-overnight-20260926-v1/THINKING-AUDIT.md before causal comparisons.
Historical complete scores are not equivalent to correctness-and-clean finish.

## Fixed methodology and constraints

Decision screen: same 18 archived labeled windows, .85 frozen threshold,
CPU float32/four threads, reject >2048-token input, no truncation, <=6 GiB
worker private memory. Warm p95 <=3 s is a screening gate. No threshold
tuning, live intervention or promotion from this small archival set.

Coding screen: native parser and OMP read-tool controls before three tasks;
32k context, 12288 response/16000 session output tokens, wall 720 s.
Authors' recommended sampling differs from MiMo historical temperature 0;
Q8 versus Q4 differs too. Label this a deployment screen, not model-only proof.

Initial physical/commit RAM >=9/8 GiB; coding VRAM >=7.5 GiB. Runtime
floors 3/2/.5 GiB; original sustained paging guard. Windows Job ownership,
STOP support, one inference workload, no second agent, no reboot. Monitor
the full owned process tree. Unload and verify cleanup after every run.
Keep transcripts/config/scorers outside candidate workspaces. Do not alter
old evidence or include interrupted unknown usage as exact token totals.

Startup restoration after the minimal boot already succeeded September 24;
do not redo it or reboot. Existing benchmark sources are the source of truth.

## Other queued work

September 29 12 GB research note plus a three-item staged addendum:
local-llm-lab/RESEARCH-2026-09-29.md and ai_bench/queue-20260929-v2
(staged.json, RESUME.md). Nothing downloaded or run; the v1 candidate
queue at candidates-20260929-v1 keeps priority.

GoProverbs feature-weight sweep remains queued behind LLM work. Read
C:/Users/kevin/local-llm-lab/goproverbs/docs/NEURAL-VERIFY-RESULTS-2026-09-23.md
and lab AGENTS before any Go inference. Prior development gates failed;
do not promote tuned subgroups as independently validated.

## Permission handoff

OMP config.yml contains translated Codex Always Run prefixes as native Bash
approval patterns, with an audit at omp-setup-20260929/permission-migration.json.
Use literal commands/forward-slash Windows paths. Old complex PowerShell
one-offs were not widened into arbitrary shell execution. Do not use yolo
merely to suppress a prompt. Existing authorizations do not bypass the guards.
The native user AGENTS.md pointer was verified by a fresh hosted OMP session
without supplying the handoff path in its prompt. This installation check
did not run any queued local inference or change benchmark evidence.
