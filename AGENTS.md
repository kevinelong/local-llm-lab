# Local AI lab working instructions

- October 16 (news scan, first of a daily series): **`NEWS-2026-10-16.md` is written against the
  `NEWS-2026-10-14.md` baseline, and its first finding corrects the note before it.** Reading only:
  nothing downloaded, installed, built or run, no engine started, no inference, no benchmark, and
  nothing read or touched under `C:/Users/kevin/ai_bench` while the Colibri run owns the slot.
  - **The standing rule, and the mechanism that carries it.** A news scan is **daily** from here on,
    written to `NEWS-YYYY-MM-DD.md` in this repo and **never over an earlier day's scan**. It is
    **reading-only** - no downloads, no installs, no builds, no engine, no inference, no benchmark,
    and **nothing under `C:/Users/kevin/ai_bench` at all while a measured run is in flight**. Its job
    is to **feed the queue, not to re-cover what yesterday already checked**: a release, a pack or a
    paper already covered earns a line only when its *state* changes (a release landed, a PR merged,
    a blocked item unblocked).
    - **Launcher:** `tools/daily-news-scan.cmd` - one `omp -p` run with `--cwd` this repo and
      `--max-time 60m`, logging to `%TEMP%\daily-news-scan.log`. Its prompt points at this AGENTS.md
      entry rather than carrying the procedure, so the procedure cannot drift from the notes. It
      works out of `%USERPROFILE%\.local\bin\omp.exe` and was verified non-interactive (exit 0).
    - **Trigger:** the Windows scheduled task **`omp daily lab news scan`**, daily at **07:30**,
      `StartWhenAvailable` (a scan missed because the box was off runs when it next wakes), with a
      90-minute execution limit. Verified 2026-10-16 with `schtasks /query /tn "omp daily lab news
      scan" /v /fo list`: `Status: Ready`, `Next Run Time: 10/17/2026 7:30:00 AM`, `Task To Run:
      C:\Users\kevin\local-llm-lab\tools\daily-news-scan.cmd`, `Stop Task If Runs X Hours and X Mins:
      01:30:00`.
    - **Test it without running a scan:** `daily-news-scan.cmd "Reply with exactly: SCAN-OK"`
      (verified 2026-10-16 - the log runs start, the reply, exit 0, repo untouched).
    - **Commit rule for a scan:** add only the three paths it owns - `NEWS-<date>.md`, `README.md`,
      `AGENTS.md` - and **never `git add -A`**, so a scan can never sweep someone else's uncommitted
      change into its commit.
  - **What the first entry found, because it changes a decision.** llama.cpp's MoE expert cache is
    **already upstream**: PR **#29887** merged **2026-10-07T18:07:46Z** adding **`--moe-cache-mib N`**
    - a GPU cache for the routed experts kept in host memory, which is exactly our `--cpu-moe` case -
    shipping from **b11480**, with PR #30112 extending it across GPUs on 2026-10-08. That is one day
    after our pinned `b11461` and one day before `STRATA-ALTERNATIVES-2026-10-11.md` concluded "we
    cannot get this by bumping our pinned build - there is no upstream flag to set". The correct
    statement is that **our build predates it**. Its own numbers: RTX 4090 25.0 -> 39.4-40.7 tok/s
    (72-77% hit), RTX 5090 30.8 -> 54.5-67.8 (up to 2.20x, 89%). The cache size is **non-monotonic**
    (community reports on 12 GB cards include 32 -> 12 tok/s at an 8 GB cache and 35 -> 45 at
    2.4 GB), so the test is a **ladder**, not one setting. Same note, same class of correction:
    **#27149 is a Discussion, not a PR** (`pulls/27149` and `issues/27149` both 404), and two of our
    notes call it an unmerged PR.
  - **The ranked shortlist it hands the queue, cheapest first:** the Strata KV-residency A/B at fixed
    capacity (no download); the llama.cpp `--moe-cache-mib` ladder; a per-workload noise floor for
    every tune - Profile Studio measured `setup.py --calibrate` making agent turns **5.2% slower, 6
    of 6, p = 0.031**, because it tunes on 128- and 512-token chats, and a 2026-10-15 video watched a
    203 tok/s agent-written benchmark fall to ~140 on re-test; a warm expert cache at fixed capacity
    (Colibri #2109 asks for the same thing); Ollama's new native decision-model path (0.40.4);
    the Coder IQ1_M pack at n >= 3 against a 12 GB community report; and the reference model on the
    second engine, gated on Strata #2747's Qwen3.6 OOM.
  - The task's first automatic run is tomorrow, 07:30.

- October 16 (morning): **the owed Colibri comparison is running, and it is a daytime run rather than a
  night one.** Kevin said "run it now, overnight" on 10-15 at ~15:15; the machine's clock only reached the
  launch at **08:02 on 10-16** (the gap is the session, not the lab), so the 15-hour item now occupies today
  and should finish ~22:00. Gates at launch: free physical **31.38 GiB**, commit headroom **30.37 GiB** -
  both far above the 9/8 GiB floors - and nothing else loads a model meanwhile. It is the only inference
  workload on the box; if the machine is needed for product work today it should be stopped and restarted
  tonight, because an abort costs at most the items since the last checkpoint.
  - **Two declared changes made before it started, both declared in the queue rather than improvised.**
    (1) `i3-colibri-qwen36`'s timeout is **57,600 s (16 h)**, raised from 7200 with a `timeout_note` in
    `queue.json` recording why (measured 45.1 s/item at `--cap 32`; the correctness run answered 86 items in
    7,200 s before the old timeout killed it), and the item's own instrument wall is 15 h so the two cannot
    race. (2) The knowledge instrument now **checkpoints**: `score()` takes the result path and rewrites it
    with `partial: true`, `scored_items` and `declared_items` every 25 items, so a wall-clock kill leaves the
    finished items instead of nothing - the failure that cost 7,200 s of work on 10-15. Verified offline
    before the run (a 60-item gold-responder pass wrote at items 25 and 50, and `--check` still reports gold
    perfect and random at chance, 0.253) and **live at item 25** on 10-16: the file landed with
    `partial: true`, `scored_items: 25`, `declared_items: 1100`, **23/25 passed at 45.8 s/item** and no
    transport failures, which projects the full run at 50,380 s = **14.0 h**, i.e. finishing ~22:02.
  - The item runs with `--cap 32` (45.1 s/item vs 65.7 at the engine default), reads the model id from
    `/v1/models` (`qwen3.6-colibri`), and writes `knowledge-result-colibri-qwen36-ctx8192-cap32.json` - the
    label names the context the engine actually serves (8192), not the 131,072 the old label claimed.
  - **Found while sweeping up: the driver's timeout does not stop the instrument.** The 12:55 attempt ran
    **10,137 s (2.82 h)** - the driver killed the wrapper and cleared port 8000 at 14:55:23, and the
    instrument kept posting to a dead port until 15:44:22. Its file claims **102/1100 = 9.3 %**, with 989
    connection errors (`10054`/`10061`): the 111 items that answered are the ones that ran before the port
    was cleared, so they are positional, not a sample. Preserved as
    `overnight-20261011/contaminated-i3-orphan-20261015.json` and moved out of the instrument's directory.
    This is the second instance - `supervise.py`'s docstring records the 2026-10-12 orphan - so the item now
    sets its own 15 h wall against the driver's 16 h, and the instrument marks any run with a transport gap
    `scored: false` and exits 2 rather than publishing a 9.3 % that reads like a weak model. The three
    `knowledge-result-colibri-smoke-*.json` files are 4-item smoke samples used to price the run.
  - **The scan's shortlist is declared as a queue**, on Kevin's instruction ("proceed with that plan now all
    in order"): `ai_bench/queue-20261016-shortlist/` (README + queue.json + status.json), seven items in the
    scan's order, each with its question, **prediction recorded before the run**, instrument, cost and
    readiness. The serial rule, the gates and the STOP file carry over unchanged, and nothing in it starts an
    engine while the Colibri item holds the one inference slot (~21:45).
  - **Two items were prepared read-only and are ready to run.** Item 2's build is staged at
    `ai_bench/staged-llamacpp-b11480` from the win-cuda-13.4 release archives (sha256 recorded):
    `--version` reports **build 11480, commit `d6cf9acb2`** - PR #29887's own merge commit - and `--help`
    lists **`--moe-cache-mib N`**, while the pinned b11461 lists no such flag. b11480 is the *first* build
    carrying it, so the A/B drifts by one build rather than by two days of unrelated commits. Item 1's arms
    are pinned too: `--kv-resident` versus `--kv-streaming` with `--kv int8 --max-context 65536
    --resident-budget-gib 2` fixed, so capacity is not the variable. Item 5 needs no download at all - the
    installed Ollama is already **0.40.4** - item 6's pack measures **54.40 GiB** (fits D:'s 252.8 GiB, leaves
    ~4 GiB of 58.46 GiB usable RAM, so it is parked rather than started), and item 7 stays gated on the OOM
    issue **#2747**, re-checked open at 09:31:46Z today.
  - **The queue is executable and is waiting for the slot on its own.** `runner.py` mirrors the 10-11 driver
    (STOP file, `status.json`, `REPORT.md`, gates between items, engine ports cleared, no blind retries) and
    adds a **slot check**: while anything listens on the lab's Colibri port it refuses to start an engine, so
    the one-workload rule is enforced rather than remembered. `wait_for_slot.py` waited on that port and was
    launched at 09:36 to run the queue the moment the Colibri item stops. Verified without engines: dry run
    (gates 28.75 GiB free / 19.18 GiB headroom, plan in order, q6/q7 skipped with reasons), the refusal path
    against the live run, both supervisor branches, and q1's arm construction (identical except the
    `--kv-resident` flag). Item 4 also got sharper while implementing: the engine *does* have
    `--expert-profile-save` / `--expert-profile-save-every`, and the server says the next start begins from a
    saved profile - which our 10-11 warm test never asked for, so its "nothing persisted" reading was a
    missing flag, not a missing mechanism.
  - **An incident worth more than the code it cost: I ran the wrong `supervise.py`.** Testing the new
    queue's supervisor, a snippet put two sibling roots on `sys.path` and then said `import supervise`, which
    bound the *overnight* root's historical `supervise.py`. Its job is to wait for an orphan and then drive
    i4/i6, so it cleared the engine ports and logged a start of `[i4-reason-repeat, i6-gliner-replay]` at
    09:30:48 - **no item ever ran** (it was killed within minutes), and the only casualties are bookkeeping:
    a duplicate i4 block in that root's `REPORT.md` (annotated) and a `status.json` that briefly claimed a
    run that never happened (rewritten with the note). The engine in flight was unharmed - port 8000 is the
    same process from 08:02:57 and the item kept checkpointing through the incident. The new module is now
    `wait_for_slot.py` so no two sibling roots share a module name, and the rule this lab already applies to
    shells now applies to imports: name the module you mean, do not let `sys.path` order pick it for you.
- October 15: **the paused queue's remainder ran, and both repeats came back exactly as predicted.** The
  STOP file was deleted on Kevin's go-ahead ("after the fleet's builds stop") and the owed items ran serially
  through the driver's own gates (free physical 33.5-42.9 GiB, commit headroom 40.0-45.2 GiB); no gate was
  lowered, nothing was deleted, nothing was rebooted, no frozen artifact was edited.
  - **i4-reason-repeat: both predictions hit to the check.** Qwen3.6 + provisioning **90/93** and Strata
    **92/93** - the same counts night 1 recorded - with the letters reproducing across runs and only the
    free-form prose moving (mean distractors addressed 1.90 -> 1.89 on Strata, 2.08 on Qwen3.6). This is the
    first *repeat* of this instrument across runs, and it says the letter is stable where the prose is not.
    The first attempt ran only the Qwen arm: the console's nginx-mirror proxy held port **8080**, which is the
    lab's own `STRATA_PORT` (`shared.py:29`), and the driver clears its engine ports *between* items rather
    than before the first - so the Strata arm refused to start (`arm_exit_codes {qwen36: 0, strata: 2}`) and
    the arm under test was exactly what the conflict cost. Re-run after the port was clear: 647 s,
    `{qwen36: 0, strata: 0}`.
  - **i6-gliner-replay: the detection prediction held, the latency prediction was refuted by ~10x.** 0/4
    stalls caught, 14/18 correct at the frozen 0.85 threshold with **zero** flags either way - the same shape
    Laya gives, so this instrument still carries no stall signal from either decision model. Warm p95 was
    **2 937 ms**, then **3 703 ms** on the repeat, against a predicted 20-35 s, and the `gate_3s_passed`
    verdict *flips* between those two samples: the model sits at the gate, not inside it. That kills the
    2026-10-11 reading that the 27.56 s p95 was sequence-length cost and "no engine will fix it" - the same
    class of model on Colibri answers in ~1.7-2.1 s median. The engine log settles what was served:
    `[gliner_decide] microsoft/deberta-v3-large: DeBERTa-v2 24 layers x 1024 ... loaded in 1.7 s`, 36 x
    `POST /v1/systemone 200`.
  - **i3-colibri-qwen36: not run to completion, and it cannot be at the item's declared 7200 s.** Three
    defects were fixed first, all three of the kind that make a result lie. (a) Colibri advertises the model
    as **`qwen3.6-colibri`** and answers any other name with `404 model_not_found`, so the item's
    `qwen36-35b` failed all **1,100** requests in 12.9 s while `knowledge_run.py` exited **0** with a
    `0/1100` that read like a model verdict; the dead run is preserved as
    `dead-i3-model-not-found-20261015.json`, the item now reads the id from `/v1/models`, and the instrument
    records `transport_failures` + `scored: false` and exits **2** when every reply is a transport error
    (the "unscored, not failed" rule the new-task driver already had). (b) The item would have called
    `coli setup` three times at a 5400 s timeout each **against a complete directory** - the documented trap
    that downloads and then serves in the foreground, which deadlocked eight hours on 2026-10-12; it now
    detects the staged 21.44 GiB model and skips setup. (c) `laya_replay.py` hardcoded `engine` and
    `checkpoint`, so the GLiNER replay wrote `colibri v2.0.0 laya.exe` and the Laya checkpoint into its own
    result file while the engine log said `gliner_decide`; both are now `--engine`/`--checkpoint` arguments
    with the Laya values as defaults, and both frozen Laya results still reproduce those fields byte-for-byte.
  - **What that comparison actually costs, four-item samples of this same instrument:** engine default
    (cache 8/layer) **65.7 s/item** (~20 h for 1,100 items), `--no-think --effort minimal` 66.2 s/item (no
    effect - the cost is per-token, not output length), **`--cap 32` 45.1 s/item (~13.8 h)** with `T(1)` down
    from ~240 ms to 175-200 ms per token. The corrected run answered **86 items in 7 200 s** before the
    driver's timeout killed it (exit -9). The comparison is sound - the model answers in the instrument's own
    format, 4/4 on both samples - but it is a ~14-hour run, so it **waits on Kevin's call** rather than
    retrying; the item now declares `--cap 32` and the honest label `colibri-qwen36-ctx8192-cap32`, because
    the served context is the engine's default **8192**, not the 131,072 the old label claimed (no knowledge
    prompt is anywhere near 8k).
  - **Carried forward:** the knowledge instrument writes its result only at the end, so a timeout loses the
    whole run - 7 200 s produced no artifact. Smoke with `OVERNIGHT_LIMIT` first, and give it a
    checkpointing result file before it runs again (done the next morning, see the October 16 entry). One
    stale process was killed on Kevin's word: a second `fifteenball-server.exe` on 8199 (a private-copy DB)
    that the score work reported as stopped. The demo stack on 8093/8094/8123 is the one that matters, and
    the 8080 nginx mirror was restarted once the queue had released the port.
- October 12 (paused): **testing is paused until tonight, at Kevin's request.** The overnight queue's second
  pass is stopped, not abandoned: `ai_bench/overnight-20261011/OVERNIGHT-STOP` is in place so the driver
  starts nothing, the supervisor and its runner/item were killed by hand, and the engine ports were cleared.
  Night-1 results are intact in `status-night1.json`, `REPORT-night1.md` and `REPORT-SUMMARY.md`.
  **Three things are owed, in this order:** `i4-reason-repeat` and `i6-gliner-replay` (via
  `python runner.py --only i4-reason-repeat,i6-gliner-replay` after deleting the STOP file), then the
  **Colibri Qwen3.6-35B-A3B knowledge comparison** - its ~23 GB model is already complete on
  `D:\ai_bench-staged\colibri-models` (21.45 GiB, 50 files, which is the "23 GB" in the docs after the
  decimal/binary difference), so serve that directory and point the knowledge instrument at port 8000.
  **Do not use `coli setup` for it:** that command downloads and then runs the server in the foreground, so it
  never returns - which is what deadlocked the first attempt for eight hours.
  Confirmed while stopping: with the Colibri server resident, commit headroom sat at **7.5 GiB against the
  8 GiB gate**; once its port was cleared the same check read **35.76 GiB free / 20.94 GiB headroom**, so the
  guard was measuring a real resident model rather than drift. Also still true from this morning: free space
  on `C:` is partly pagefile allocation, and the lab's instruments plus their frozen inputs are now
  snapshotted into the repo under `instruments/` with a sha256 manifest.

- October 12 (morning): **the overnight queue's first pass is done and its results are in** - read
  `ai_bench/overnight-20261011/REPORT-SUMMARY.md`, `REPORT-night1.md` and `status-night1.json`; queue 2 is
  running as a harness job for the three items that needed a fix. Four of six items produced results, the
  resource gates held throughout (free physical 39.9-43.4 GiB, commit headroom dipping to 26.7 and
  recovering), and no frozen artifact was touched.
  - **Placement changes the prose, not the answers.** Strata at `--resident-budget-gib` 2 vs 8 on the same 93
    shared-correct items: **65 of 93 justifications differ** (my recorded prediction was 20-60%, so wider than
    expected), **the chosen letter differs on 0 of 93**, correctness 92 vs 92. This localises what the lab had
    only as "temperature 0 is not seed-stable on that engine": free-form text moves with placement, the scored
    answer does not. Our suite scores are placement-robust; text-based instruments (papers, fact lists) are
    not, which is exactly where that earlier variance appeared.
  - **Kolibri-1 78B leads on coding and trails on knowledge: 901/1100 = 81.9%**, against Qwen3.6-35B-A3B
    88.5% and Strata Q2_0 89.7% - a 6.6-point gap, and **wrong against my recorded prediction of 85-92%**.
    It is also the fastest at 1.46 s/item (Qwen3.6 2.80, Strata 1.93). Per subject: grade-school math 285/300
    (95%), world history 86, international law 84, astronomy 82, geography 81, religions 81, philosophy 80,
    prehistory 71, **virology 51** - the same virology floor the other two hit, so that is the item set, not
    the model. Model ranking here is task-dependent, measured.
  - **The paper form's topic variability is not stable**: re-run, Qwen3.6 produced 1 distinct topic again
    (2/2 runs deterministic) while **Strata produced 1, not the 2 of the first run** - so "Strata picks
    different topics" is a sometimes-property, not a fixed one.
  - **Two failures, both mine, both fixed.** Items 4 and 5 shared the suffix `-rep1`, so the paper run
    **overwrote the reasoning repeat's artifact** - re-running with distinct labels. And queue 2 was launched
    with a bare shell `&`: **the driver was reaped when the tool call returned** (the first item survived as an
    orphan), which is precisely the trap this lab's notes record under "never launch a batch with a bare
    shell `&`". Fix: `supervise.py`, launched through the harness, waits for the orphan, clears the ports and
    drives the rest.
  - **Two environment findings worth keeping.** Colibri's Qwen3.6-35B-A3B download reached 21.45 GiB of ~23 GB
    in two hours (~3 MB/s, the slowest source this lab has used; the Laya checkpoint did 0.84 GiB in 15 s) and
    resumes. And GLiNER2.5-Decide has a **version skew**: upstream renamed the architecture, so from revision
    `2125c8ac` the root `config.json` is `model_type: gliner2` / `[Gliner2ForSchemaExtraction]` and the pinned
    Colibri v2.0.0 refuses it ("unsupported model_type: gliner2"); revisions up to `a6ef71ce` carry
    `model_type: extractor` / `[SpanExtractor]`, which is what its doc describes. Pinned there.

- October 11 (evening): **an overnight queue is running** - read `ai_bench/overnight-20261011/README.md`
  before anything else; `status.json` and `REPORT.md` in that root say where it is, and a file named
  `OVERNIGHT-STOP` there cancels it before the next item. Six serial items, one inference workload at a
  time, gates re-checked before each item (a trip **stops** the queue, never lowers it), no frozen artifact
  edited, nothing deleted or rebooted. Predictions for every item were written down *before* its run.
  Items: Strata at `--resident-budget-gib` 2 vs 8 over the same 93 items (the placement/output instrument);
  **Kolibri-1** on the 1,100-item knowledge set; **Colibri's** own Qwen3.6-35B-A3B over the same items (same
  model, second engine); the repeat of our 93-item reasoning run; the paper form repeated; GLiNER2.5-Decide
  on Colibri over the frozen decision windows. Both smoke tests passed before the night started - the
  placement item end to end, Kolibri after fixing its launch.
  **Two launch facts worth keeping, both probed rather than guessed:** the community `hob-b11434` runtime
  (the only build that loads kolibri1) dies at load with `CUDA error: shared object initialization failed`
  in `launch_fattn` unless `-b 512 -ub 512` are set explicitly - with a 128k context the default micro-batch
  asks the flash-attention kernel for more shared memory than the card allows; and `-ctk/-ctv q8_0`
  *requires* `-fa on` (with `-fa off` the context fails to build, the opposite pairing to what the error
  suggests). Kolibri then loads in 26 s, matching the frozen note's 27.7 s, and answers at ~22 tok/s on a
  cold burst. Same day's disk work: the `D:` second NVMe (331.6 GiB free, throughput parity with `C:`) and
  the archived `staged-strata-20260930` are recorded in the research note.

- October 11: **Strata-alternative research** (no inference, no install, no gate touched, nothing
  deleted). Read `local-llm-lab/STRATA-ALTERNATIVES-2026-10-11.md`. The mechanism that makes an engine
  "like Strata" is streaming routed experts from disk inside a bounded memory budget, so a GPU becomes an
  optional tier rather than a requirement. **Colibrì** (`JustVugg/colibri`, tag v2.0.0 published
  2026-10-06T20:24:40Z, Apache-2.0, pure C, Windows, GPU optional, asset sha256s published) is the one real
  alternative: it has an engine for the Qwen3.8-Flash-Next we serve, and a **Jev-compatible
  `/v1/systemone`** with three native decision models on the CPU (Laya 0.85 GB, GLiNER2.5-Decide 1.95 GB,
  Clef 55 GB) - the cheapest test of a Strata alternative we have, and it needs no GPU. On Windows its CUDA
  DLL covers only `colibri`, `qwen36` and `kimi_k3`, so Qwen3.8 there is Vulkan/CPU, and its 186 GB download
  does not fit our free space (81 GiB, see the disk note below). **Name collision: Kolibri-1 78B is a model we measure; Colibrì is an
  unrelated engine.** StrataFlow (Coaade, 2026-10-05) is the same thesis - `.strata` format built from GGUF -
  but source-available (not OSI), CPU-only, no HTTP server, no release: watch only, plus an open lineage
  question about whether our MIT Strata shares its code. The unmerged llama.cpp proposal #27149 is still
  worth reading for its measurements [corrected 2026-10-16: it is **Discussion** #27149, not a PR -
  `pulls/27149` 404s - so "proposal" is the right word and "PR" was not; the interleaving findings stand]:
  GGUF expert interleaving costs **111x page amplification** (36x after
  a contiguous re-layout), and calibrating the hot set from real text lifts the hit rate from **6 % to 42 %**
  (56 % with LRU) - the next lever for our own expert cache. **Disk note, resolved the same day: free space
  fell 103 -> 81 -> 61 GiB across three measurements, and the cause is the pagefile.** `pagefile.sys` read
  32.57 GiB early and 50.79 GiB two hours later (written 2026-10-11 10:11, only 3.54 GiB in use) - an ~18 GiB
  allocation against a 20 GiB drop, with nothing in the lab's roots growing (the only new file over 300 MB is
  the 0.78 GiB Laya checkpoint), Windows Update at 0.03 GiB and no shadow copies. So engine loads raise commit
  charge, Windows grows the pagefile, and the space stays allocated until a reboot. **Free disk on this box is
  not a static resource, and a guard watching disk during an engine run is partly watching the pagefile.** At
  61 GiB no large Colibrì pack fits without deleting something; the decision models (0.85-1.95 GB, Laya staged
  already), OLMoE (14 GB), Qwen3-Coder-30B (19 GB) and Qwen3.6-35B-A3B (23 GB) do. **Then the same day found
  a second identical NVMe: `D:` (disk 0, same `NVMe P0527 Phison 1024GB` as `C:` on disk 1), 953.7 GiB with
  331.6 GiB free, already holding a 622 GiB models store (Kimi-K2.7-Code 554.3 GiB; Qwen3.8-Flash-Next as
  Ollama `UD-IQ1_S` 72.5 GiB - a different quantisation, checked and *not* a duplicate of our GSQ-RCO Q2_0,
  so nothing was deleted). Measured 1 GB sequential: `C:` 1187 write / 3212 read MB/s, `D:` 1261 / 3123 -
  parity, and enough read for expert streaming. So large routes do fit, on `D:`; frozen roots keep their
  absolute `C:` paths, so staging stays put and new downloads go to `D:`. Same note, addendum: a
  captions-less video (AgenticEngineering,
  2026-10-08, `egYyctiT2Kk`) named two engines the first search missed because they use different words for
  the same idea - **ds4/DwarfStar 4** (`antirez/ds4`, MIT, Metal/CUDA/ROCm, `--ssd-streaming`, own GGUFs,
  60-197 GiB models, persistent SHA1-keyed disk KV cache) and **FreeToken** (arXiv 2608.16157v1,
  bandwidth-adaptive, `ft bench bw` measures CPU-vs-PCIe bandwidth before scheduling). Both are
  hardware-blocked on this box; ds4's cache rule ("more cache helps only while the rest of the working set
  still fits") and its identical-logits result are the takeaways. Searching one phrasing of an idea is how
  you miss its implementations. **Ran the first recommended experiment** (`ai_bench/colibri-laya-20261011/`):
  Colibrì v2.0.0 (tag-pinned, zip sha256 verified) serving Laya (checkpoint pinned `7b928d82`), over the 18
  frozen windows with the verbatim `stuck` question from `decisions-20261005-v3/worker.py`, frozen inputs
  verified against `protocol.json`. Result: **14/18, 0/4 stalls caught, 0/14 false alarms at 0.85 - identical
  to our own Laya run**, so that failure is the model, not our serving path. New mechanism: at the
  checkpoint's default `max_len` 512 the head returned a near-constant **0.7179** for unrelated windows
  (truncation, not blindness); at 4096 its values are state-dependent but carry **no** stall signal (mean
  stall 0.5868 vs non-stall 0.5768; no threshold in 0.40-0.90 catches a stall) and the doc's two-option
  `choice` workaround points the wrong way (-0.021). Latency is the second finding: warm p95 **2765 ms** at
  4096, about 15x our Laya's 183 ms and close to our own 3 s gate. The sweep is label-tuned and is not
  validation. Server stopped, no gate touched. **The stall signal is in the transcript and a rule reads it**
  (`ai_bench/decision-signal-20261011/`, frozen features only, no inference): the discriminator is not the
  error flag but whether a repeated action produced a **byte-identical outcome** - three of the four labelled
  stalls repeat a *successful* action with the same output hash, which is why the 2026-09-25 rule (identical
  **error** repeat) caught only **1/4**. Error-agnostic identical-outcome catches **4/4 at 2/14 false
  alarms**; adding "no DISTINCT successful outcome" gives **4/4 at 1/14**; the variant that also demands no
  successful mutation gives 3/4 at 0/14. Against that, every neural decision model we have screened catches
  **0/4** (Laya on two engines, kev4, kev0, julia), Laya adds **zero** catches on top of the rule at every
  threshold down to 0.60, and the rule costs microseconds against Laya's 1562 ms. Descriptive, fitted on
  these 18 labels - a real detector needs a fresh labelled set. **Colibrì's GLiNER2.5-Decide run was skipped
  as redundant**: its own speed table predicts 25.7 s at 1923 tokens and our GLiNER verdict was p95 27.56 s,
  so that latency is sequence length (quadratic attention on a DeBERTa-large), not a serving path - no engine
  will fix it, only shorter states or a rule. Its checkpoint needs a root `config.json` (the opposite of
  Laya's gotcha) and ships **no calibration**, so its probabilities are raw softmax.
  **Calibrated-hot-set test on our own Strata: negative** (`ai_bench/strata-warmcache-20261011/`). One engine
  process, declaration unchanged (`--resident-budget-gib 2`), three cold probes, four to eight same-domain
  warm-ups, three warm probes: cold steady 22.4-26.4 s against warm 22.5-28.3 s, with the within-phase spread
  (4.65-7.14 tok/s) larger than any between-phase difference. `expert-profile.bin` is byte-identical after
  both runs (the pack's own file, dated 2026-10-07), so the engine persists no learned profile and a warm-up
  has nothing to carry over. Two by-products worth keeping: this engine **is** deterministic for this prompt
  and length (three byte-identical probes, 657-703 chars), so the earlier output variance belongs to long
  free-form generations rather than to the engine as such; and a trap - the endpoint returns its tokens in
  `reasoning_content`, so a collector reading only `content` silently measures 0 chars and "identical" empty
  outputs, which my first run did.
  Pending Kevin: whether to spend the ~2 GB on the GLiNER replication anyway.

- October 9 (small hours): the new-task suite ran live end to end - read
  `ai_bench/new-items-20261007/RESUME.md` and its REPORT.md section "The chain's last runs". The
  frozen three tasks (events 76, ledger 70, paths 75) now sit beside three new batteries: **ledger2**
  (226 checks, the fine-grained version of ledger), **repo** (78, a multi-file task) and **longctx**
  (40, a 222 KB / ~65k-token corpus that the models read in slices, not whole). Six-task total 565.
  - Declared provisioning, verified from the run (`provision.py` / `provision-20261008-v1`): served
    context 32,768 -> **131,072**, the host's contextWindow/maxTokens -> 131,072/32,768, and
    llama.cpp's thinking budget 6144 with a wrap-up message. The relay's Budget also demotes
    `quota_unknown` to a counted usage gap, and the reply cap goes 12,288 -> 32,768 (MiniCPM's `repo`
    had died on `length` at exactly 48,000 tokens).
  - Scores (565 checks, one run each): Qwen3.6 `ctx-v8` **562/565 in 1,330 s** - best and fastest full
    sweep - then Kolibri `ctx-v4` and its repeat `ctx-v9`, both **551/565, identical per task**
    (2,971 / 2,877 s), Nemotron `ctx-v7` 544, **Swift `ctx-v11` 530** (exempt, 32,768), MiniCPM
    `ctx-v5` 456, gpt-oss `ctx-v2` 432.
  - **The n=3 repeats then moved the two weakest a long way in both directions** (one workload at a
    time, serial): gpt-oss **432 -> 528/565** in 931 s with `repo` **0 -> 78** and `longctx` 15 -> 29;
    MiniCPM 445 -> 456 -> **522/565** with `repo` 43 -> 0 -> **68**. So `repo` - which looks stable
    within a model for the strong ones (Kolibri 78/78 x4, Qwen3.6 x5/6, Swift 43/78 x2) - is the most
    volatile battery for these two (0-78 and 0-68, effectively bimodal), and their single-run verdicts
    in the week summary were wrong in both directions.
  - **The context ladder is settled and the exemption confirmed.** Swift at 65,536 trips the monitor
    during model load - `gpu_free` 0.31 GiB against the 0.5 GiB floor at **24.8 s, reproduced at
    26.0 s** on a deliberate retry - while 32,768 holds 0.69-1.28 GiB free across two runs and
    131,072 sits at 0.49-0.50. So it is 32,768 or nothing, and the cost is a *load-time* peak:
    comparing `max_gpu` during generation (10.38 -> 11.18 GiB across the 32k/131k runs) is what made an
    earlier note predict 65,536 would fit. The chain's own gate skipped 98,304. Nemotron's third
    sample is **545/565** (3,303.8 s) against `ctx-v7`'s 544 - reproducible to one check - with
    `ledger2` 208/209 against 223 at 32,768, the same fourth-of-six shape in which Kolibri's 212s
    appear, so the position hypothesis now has two models behind it.
  - **A harness scoring bug leaves `longctx` unscored in some roots.** The harness resolves its
    scorer with a name-based `from staged_tasks_20260922 import TASKS` (`mimo-harness-20260925-v1`
    `run.py:324`), and the **frozen** module sometimes wins over the root's superset - the frozen
    module has neither `longctx` nor `ledger2`, and it is what raised
    `ValueError('unknown task: longctx')` in `newtasks-gptoss-20261009-r2` and `-r3` (r1 and every
    other root scored it fine). Those cells are **unscored, not failed**; the driver now records the
    harness's own `abnormal_evaluator_exit` as `unscored: true` so they cannot read as zeros. r3 also
    re-ran `paths` 75/75, which shows r2's 0/75 was the scorer's abnormal exit rather than the model.
    The mechanism is a name-resolution race (`from staged_tasks_20260922 import TASKS` inside the
    harness's `run.py:324`), and the instance that mattered for the Strata track is **fixed** by
    keeping the base module root-local - see the next bullet; the OMP cells are closed as failures by
    offline re-scoring. What remains open is a general fix for the OMP roots.
  - **Strata now scores the full new-task suite: 692/693, identical to Qwen3.6's best.** The port had
    to fix two things the hard way. (1) The template's `--resident-budget-gib 12` tripped the 3 GiB
    physical floor on its first session (free physical 3.18 GiB) although the engine loaded in 31.7 s
    and decoded at 66-79 tok/s, so the port declares **4 GiB** (the documented-safe value) in
    `strata-newtasks-20261009-v2`, where all nine sessions ran clean in 1,959 s. (2) `score_artifact`
    runs the task module from the **base module's own directory**, and the template used the harness's
    base - whose `HERE` is the frozen `completion-20260923-v1/source`, holding only events/ledger/paths
    - so six batteries came back `abnormal_evaluator_exit: 1`. The port now copies the base into the
    root (`source/relay_strata.py` plus siblings) and sets `lab.base` to it, which is the OMP
    templates' `lab.base=fresh` move; verified 6/6 through the production path before re-running. The
    v2 artifacts re-scored offline give the same cells as Qwen3.6 (ledger2 226, repo 78, longctx 40,
    repo2 **54/55**, perf 33, longctx2 40) with the same single miss, so a streamed Q2_0 pack at 4 GiB
    resident matches a fully resident 35B-A3B Q4_K_M on this suite. **Confirmed at n=2**: the fresh
    post-fix run `strata-newtasks-20261009-v3` reproduced five of six batteries exactly (which also
    validates the offline re-scores), and `longctx2` runs in `strata-newtasks-20261009-v4` because the
    4 GiB declaration leaves the 3 GiB floor marginal (v3 session minima 2.94-5.11 GiB; `perf` crossed
    it at 2.94 after its artifact was already complete) - 2 GiB is the safer value if the track
    continues. v3 engine loads were 16-18 s.
  - **gpt-oss's unscored `longctx` cells are closed as failures**: re-scoring both roots' artifacts
    offline gives **0/26** each (the model wrote a file with a syntax error), while r3's targeted
    re-run recovered `paths` 75/75.
  - **Provisioning is per model: the raise is load-bearing for two models and harmless elsewhere.**
    It is load-bearing for exactly two models: `longctx` reads a 235 KB module in chunks, so its
    *peak prompt* is what matters, and the wire captures give Swift 16,111 tokens, Qwen3.6 15,531 /
    26,778, Kolibri 20,431 - all inside
    32,768 - versus **MiniCPM 40,336 and Nemotron 43,221**, which exceed it. Swift proved the small
    window is enough: 40/40 at `n_ctx_slot = 32768`. **The raise does not cost `ledger2`** - an earlier
    draft of this entry claimed Kolibri's 226 -> 212 twice was a systematic context loss, and four
    targeted repeats (`newtasks-rep-20261009-q1/q2`, `-k1/k2`, `LAB_TASKS=ledger2,repo`) refuted it:
    at the *same* 131,072 context Kolibri scores **226/226 twice** when `ledger2` runs first, so the
    variable is loop position or plain variance.
  - **`repo` is the reproducible battery for models that can do it, and the most volatile one for the
    two weakest; `ledger2` is noisy everywhere** (the repeats plus every earlier run): Qwen3.6
    `ledger2` 207/212/212/224/226/226 (n=6, spread **19**), Kolibri 212/212/226/226/226 (n=5, spread
    **14**), Swift 226 twice, Nemotron 209/223, MiniCPM 144/199/**203**, gpt-oss 202/204/**219** -
    against `repo` 78/78 four times for Kolibri, 78/78 five times out of six for Qwen3.6, 43/78 twice
    for Swift, but **MiniCPM 0/43/68 and gpt-oss 0/78/77**. So any single-run `ledger2` difference
    below ~19 checks is noise, which retires earlier "X beats Y by 12 checks" readings in this family,
    and for MiniCPM/gpt-oss a single `repo` run says almost nothing. When `ledger2` does fail the traps
    are the known cluster (frozen 0/6/19 plus the Unicode-digit group; `-q1` had 19).
  - `events` and `paths` are saturated for the strong models; `repo` is 0/78 for MiniCPM at the raised
    context and was 0/78 for gpt-oss before its repeat scored 78.
  - **Swift's old 7/70 ledger was a reply-cap artifact, not a model verdict.** With the raised reply
    cap and quota it scores `ledger` **70/70** while keeping `ledger2` 226/226 - the report's Cause 1
    reproduced on a second model, beside a 226/226 ledger2 on byte-identical checks.
  - **Swift Bonsai 2 is EXEMPT from the context raise, and the reason is a load-time GPU peak.** Its
    runtime is the Prism fork; at 131,072 its KV drove `gpu_free` to **0.49 GiB against the 0.5 GiB
    floor** (`gpu_used` 11.18 of 12), and a 65,536 attempt (`LAB_CONTEXT`, an operator-declared
    per-build override) tripped even earlier - **24.8 s, `gpu_free` 0.31 GiB, before the model
    finished loading** - while physical RAM (34.4 GiB free) and commit (33.5 GiB) stayed comfortable.
    So the ceiling is the weight load, not the generation-time cache (comparing `max_gpu_used` across
    the 32k/131k runs, 10.38 -> 11.18 GiB, is what made this entry predict 65,536 would fit: wrong).
    32,768 is the only measured configuration that clears the floor (0.69-1.28 GiB free); the
    exemption therefore holds at both raised contexts, and `PROVISION_EXEMPT` says so. It skips both
    the engine flags and the host-window rewrite, since a half-skip would leave the host believing in
    a window the server does not serve. A draft briefly also excluded `longctx` from its loop on the
    assumption that a 32,768 window cannot hold the corpus; `ctx-v11` refuted that (40/40) and the
    exclusion was removed rather than kept as a dead switch.
  - The usage-gap tolerance is load-bearing: Kolibri's first six-task attempt aborted after three
    tasks on `quota_unknown`; every provisioned run after it finished all six.
  - **The nine-task loop then ran for the first time** (`newtasks-ext-20261009-v12`, Qwen3.6,
    2,707.5 s, no error): **565/565 on the six-task suite, every task clean and correct - the first
    perfect six-task sweep** - plus the three never-run batteries: `repo2` **54/55** (its one miss is
    case 27, `class2/unknown-kind-raises` - the per-instance registry was built but `register('nope')`
    was not made to raise; the four labelled classes are 22/6/5/7 checks, where the old `repo` split
    on three checks of one class), `perf` **33/33** (2,000,000 intervals inside a wall stated relative
    to the reference - the only battery here that prices engineering judgement, since a
    correct-but-quadratic solution passes everything else) and `longctx2` **40/40** (all nine planted
    frame-length sites found). Nine-task total **692/693**. At n=1 the new batteries are "no failure
    observed", not saturated.
  - Driver changes made to support that: the record is keyed by **root** (a repeat no longer
    overwrites the earlier run - the old model-keyed entry was migrated), `--root NAME` lets one model
    own several roots, and `LAB_TASKS=ledger2,repo` builds a declared loop subset (unknown names are
    refused, not dropped) for targeted repeats. `_build_into` was rewritten as one implementation and
    both branches verified by build; a fresh Swift build is byte-identical to the root that ran.
  - **Three declarations made on Kevin's instruction (2026-10-09).** (i) The **6 GiB worker-private cap
    is REMOVED** (`local-decisions-20260925-v1/run.py`: `WORKER_PRIVATE_CAP_GIB = None`, was 6). It
    stopped nimble at a measured 6.94 GiB private floor while every system floor passed. Unchanged: the
    eligibility gate (>=9 GiB physical / >=8 GiB commit / >=0.5 GiB GPU free), the runtime floors
    (3 / 2 / 0.5 GiB), the paging-pressure counter, and every historical root's record - loosening a
    bar is loud, per `skill://lab-evidence-discipline`. (ii) **`events` and `paths` are RETIRED from
    ranking**; the metric is the discriminating subset `ledger + ledger2 + repo + longctx` = **414
    checks** (`RANKED_TASKS` in `newtask_run.py`; `ranked_table.py` regenerates the table from each
    root's own evidence into `ranked-20261009.json`). They still run, as sanity checks. (iii)
    **Per-model context reporting**: every row carries the context it was served - 131,072 for the six
    local models, 32,768 for the exempt Swift, 65,536 for Strata - because nothing measured shows the
    raise hurting a battery and a row without its context is unreadable.
  - **The ranked table has two perfect rows**: Qwen3.6 `ext-v12` **414/414** and **Strata 414/414**
    (a declared combination of v2+v3+v4), then Qwen3.6 `ctx-v8` 411, Qwen3.6/Kolibri 400 (Kolibri twice
    and identical), Nemotron 394/393, Swift 379 (at 32,768), gpt-oss 377, MiniCPM 374, with the two
    weakest models' earlier runs at 305 / 294 / 283.
  - **The gpt-oss `longctx` cells have a root-local fix.** The harness resolves its scorer with a
    name-based import (`mimo-harness-20260925-v1/run.py:324`) and `sys.modules` caches whichever copy
    arrives first; the new-task roots now bind that name eagerly to their own superset right after
    putting their `source/` on `sys.path`, with an assert that the superset won.
  - **Now running** (one serial chain): nine-task sweeps for Kolibri / Nemotron / MiniCPM / gpt-oss /
    Swift, position-controlled `ledger2` repeats for Kolibri and Nemotron, and the Strata nine-task
    sweep at the safer **2 GiB** resident declaration (`strata-newtasks-20261009-v5`) - 4 GiB left the
    3 GiB physical floor marginal (v3 session minima 2.94-5.11 GiB).
  - **Incident worth keeping: a declared change to a *pinned* file stops every new root, by design.**
    Removing the worker cap edited `local-decisions-20260925-v1/run.py`, which every root's
    `manifest.json` pins by digest (120 files, including the monitor). The roots built after the edit
    died in `verify()` with `AssertionError: ['...local-decisions-20260925-v1\\run.py']` - the freeze
    working as designed, not a bug. The fix is a **declared re-pin, not a bypass**: the builder now
    recomputes the manifest and writes `evidence/pin-change.json` (old -> new digests) beside it, and
    the roots' inherited `protocol.json` field `decision_worker_private_cap_gib` is set to `null` with a
    note. Verified after rebuild: **120 pinned files, 0 mismatches, one re-pin recorded**. A separate
    driver bug of my own (a `model`/`name` NameError in the new context-recording block) killed seven
    invocations before they could start; it is fixed, and the failed roots are preserved as
    `newtasks-*-fail-pin-20261009` rather than deleted.
  - **Two new instruments, built and self-tested (2026-10-09, not yet run).** (i) The lab's first
    factual-knowledge instrument: `new-items-20261007/knowledge_items.py` + `knowledge_run.py`, 1,100
    pinned items (800 MMLU over 8 subjects for recall, 300 GSM8K as the procedural control so a
    quantisation effect can be told from a knowledge effect), sampling pinned per request because the
    Strata config declares no seed. Self-test before any engine touched it: **gold 1100/1100**, seeded
    random **0.253 on MMLU** and **0/300 on GSM8K** - and it caught two defects in my own scorer/fetcher
    first. (ii) `igpu_probe.py`, a declared **hardware probe** of Ollama's Vulkan iGPU against CUDA; the
    NPU has no engine path here (Ollama 0.40.0's log names no NPU backend).
  - **The knowledge A/B ran, and the two stacks are indistinguishable.** 1,100 pinned items per stack,
    sampling pinned per request. Qwen3.6-35B-A3B Q4_K_M: **974/1100 = 88.5 %** (MMLU 86.0 %, GSM8K
    95.3 %, 3,078 s). Qwen3.8-Flash-Next Q2_0 streamed: **987/1100 = 89.7 %** (MMLU 87.4 %, GSM8K
    96.0 %, **2,128 s**). The gap is 13 items = 1.2 points against a **1.33-point standard error**, so
    it is *not* better - it is the same. The prediction on record (a recall penalty for ~2-bit weights)
    **did not appear**; `virology` is 58 % for both (a dataset ceiling) and `prehistory` is the only
    visible gap (.86 vs .94, ~1.9 se). The streamed engine was also 31 % faster in wall time here.
  - **Cleanup found six orphaned `llama-server` processes and that is why Kolibri's block is testable.**
    The knowledge driver's `terminate()` does not kill llama-server on Windows, so six servers from the
    smoke/full runs survived, holding **~8.9 GiB** (free physical 35.9 -> **44.3 GiB** after
    `Stop-Process`). The driver now tree-kills by pid (`taskkill /F /T /PID`). Verified after cleanup:
    0 llama-server, GPU 1.51 GiB, only Ollama on 11434. Because free commit is now ~8 GiB better than when
    Kolibri crossed the 2 GiB floor, its nine-task and position runs were retried in fresh roots
    (`newtasks-nine9b-20261009-k1`, `newtasks-pos2b-20261009-k1`) rather than left blocked.
  - **The Intel iGPU probe is answered: 0.39x, and its first run was void.** With the card hidden via
    `CUDA_VISIBLE_DEVICES=-1` and `OLLAMA_IGPU_ENABLE=1`, `ollama ps` reports **59 % CPU / 41 % GPU** at
    **100.8 tok/s** against **10/90 % at 260.5 tok/s** on the 5070 - so Ollama's Vulkan iGPU path works
    and costs 2.6x, spilling to system RAM. The first attempt used `CUDA_VISIBLE_DEVICES=''`, which CUDA
    treats as *unset*: both arms ran on the 5070 and reported identical rates. **An instrument must
    verify its own attribution** (`ollama ps` is that check). The NPU has no path in any engine here.
  - **INTERPRETATION RULE worth carrying forward: a score equal to the starter's baseline is a no-op
    reading, not a model verdict.** The baselines (score the unmodified starter through the same scorer):
    events **2/76**, ledger **7/70**, paths 9/75, ledger2 **62/226**, repo **0/78**, longctx 1/40, repo2
    0/55, perf 1/33, longctx2 0/40 - pinned with the starters' sha256 in
    `new-items-20261007/starter-baselines-20261009.json`, with the nine affected cells listed in
    `starter-flags-20261009.json`. Four cells had been read as model behaviour and are not: **Swift's
    historical 7/70 and its `ledger2` 62/226** (artifact byte-identical to the starter), **both of
    gpt-oss's `repo` zeros**, and **MiniCPM's `repo` 0/78**. Consequence: Swift's edited `ledger2` is
    226/226/226 (it stays the most stable model there) and gpt-oss's edited `repo` is 72/77/78. A
    *clean* session can still be a no-op, so `clean_finish` cannot distinguish it - **hash the artifact
    against the starter**. Also: Nemotron's `longctx2` 0/40 was **unscored** (`abnormal_evaluator_exit`),
    not "all nine sites missed".
  - **Kolibri remains blocked, now twice-confirmed on fresh roots.** Its retries (`newtasks-nine9b-*`,
    `newtasks-pos2b-*`) scored exactly the starter (`events` 2/76, `ledger2` 62/226) with sessions at
    **commit 1.99-2.47 GiB against the 2 GiB floor**, where its known-good run held 3.35-4.7 GiB - same
    physical (~9.3 GiB free) and the same ~500k hard faults/s. Freeing 8.9 GiB of *physical* RAM by
    killing six orphaned servers did not restore commit headroom, because the committed bytes belong to
    other processes. The floor stays; the run needs a machine whose *commit* is ~3.5 GiB lighter.
  - Unchanged: no gate, one inference workload at a time, no app closed, no reboot, no lock or engine
    left resident, `.wslconfig memory=8GB`. Platform is the 64 GB dual-channel box throughout.
- October 8: the five queue items the October 7 plan created are EXECUTED. Read
  `ai_bench/new-items-20261007/REPORT.md`. One inference workload at a time, no gate changed,
  no reboot, no app closed, no lock or engine left resident.
  - (1) MTP versus plain at n=3 per arm, fresh roots: MTP is **+31.2 % per token** (50.3 vs
    38.3 effective tok/s) but only **-7.3 % wall**, because it emits **+21.7 % more tokens**, and
    it does NOT raise accuracy (plain 219, 221, 219; MTP 220, 219, 216). The single-pair
    "MTP scored higher" reading was run variance. First perfect sample in the coding series:
    Qwen3.6 `-v26-1` **221/221**, all three tasks clean, 972 s, 38.1k tokens.
  - (2) Rate sets: `events` (76/76) and `paths` (75/75) are saturated at every good
    configuration, so only `ledger` discriminates - and five of its 70 checks carry nearly all of
    it. Case 19 (ASCII-only digits; the U+0661 Arabic-Indic trap that both `isdigit()` and `int()`
    accept) fails 14/23 samples, case 7 (`"a"x` quoting) 12/23, case 5 (unclosed quote) 11/23,
    case 0 (empty text) 10/23, case 6 (blank record) 5/23. Only four samples ever scored 70/70.
  - (3) The ledger's early termination is ANSWERED: the engine truncates a reply that is still
    inside its thinking - its own log says *"the reply reached max tokens while still thinking, so
    it has no answer"* and the message ends `stopReason=length` with no tool call. 3 of 13 sessions,
    every one below 70/70; the other two 7/70s were external terminations (guard stop, 720 s wall).
    `clean_finish=false` / `exit 143` / `quota_unknown` also occur on 70/70 runs, so `clean` must
    not be read as failure. Mitigation tested in roots v19/v20: `reasoning_budget_tokens: 6144` and
    `reasoning_close_retry: true` each gave 3/3 at 70/70 with zero diagnostics (baseline 3/13), but
    n=3 per arm cannot establish the rate change - re-measure before relying on it.
  - (4) The v0.1.40.1 tool-call rescue is unexercised by this workload: 0 occurrences of tool-call
    markup inside reasoning across 26 sessions (a mangled `write` argument did appear, and the
    model recovered).
  - (5) Qwen3.6-35B-A3B (`qwen35moe`, 262 144 context) passes long context 3/3 at 32k/64k/131k/262k
    (206,147-token prompt) with 26-27 GiB free physical, GPU 7.71 GiB and load ~10 s at 262k -
    strictly cheaper than Kolibri for the same 3/3.
  - (6) WHOLE-HISTORY CENSUS, the biggest correction of the day: `census.py` classified all 178
    sessions on disk (2026-09-16 to 10-08, Pi 0.85.1/0.86.1/0.87.1 + OMP 18.3.1, llama.cpp and
    Strata) - 94 perfect, 44 genuine model errors, **23 replies truncated inside their thinking**
    (`stopReason=length`, no tool call, which ends the agent loop) and **17 external kills**. So 40 of
    84 sub-perfect sessions (48%) are harness or platform artifacts, not model errors.
  - (7) The truncation class has TWO causes, both under-provisioned constants: **reply cap** (19
    witnesses, `completion == allowance` exactly, thinking 12k-209k chars) and **context exhaustion**
    (6 witnesses, prompt 32,475-32,764 against a 32,768 served context; 4 of those 6 still scored
    well, so it is mostly benign when it lands on the closing turn). One engine-specific witness
    (Strata 0.1.39, 3,384 of a 12,288 allowance). `witnesses.py` reproduces the split.
  - (8) CAP RAISE FIXES CAUSE 1. `truncation-20261008-v1/v2` (cap 12,288 -> 32,768, quota -> 48,000,
    one declared change): **MiniCPM5-2B 76/76, 66/70, 75/75 = 217/221 (98.2%)** where its historical
    `paths` collapsed to 9/75 twice (its sweep collapse rate was 33%), and **gpt-oss-20b 75/76, 66/70,
    73/75 = 214/221 (96.8%)**, also 33% before. Both now 0%. No gate changed; the wall is unchanged.
  - (8c) THE SAME CLASS BIT THE LAB'S BEST MODEL, in a fresh run: in `newtasks-20261008-v3` (Swift
    Bonsai 2 PQ2, five tasks) the frozen ledger scored **7/70** while `ledger2` - which contains those
    same 70 checks byte-identical - scored **226/226** in the SAME sweep. Its wire shows the third turn
    using exactly 12,288 of a 12,288-token allowance, no tool call, loop ended after 6 tool calls. So
    a 7/70 for the best-scoring model was a harness constant, not a capability failure. Re-baseline on
    the five tasks: Qwen3.6 74/66/75/212/75, Swift 76/**7**/75/**226**/**43**, Nemotron 76/67/75/223/75
    (events/ledger/paths/ledger2/repo). Kolibri's completed sweep (fresh root, quota_unknown declared
    non-fatal) is **76/69/75/226/78 = 524/525: the only configuration perfect on the 226-check battery
    AND the only one that solves the multi-file task**. **NEW RANKING**: on the frozen suite Kolibri
    (99.5 %) sat behind Swift (100 %); on the two new axes Kolibri leads by 97 checks, i.e. the old
    ranking was an artefact of two saturated tasks plus a five-check ledger.
    (events/ledger/paths/ledger2/repo). **`repo` is orthogonal**: Swift scored 43/78 = the starter's
    score (no effective cross-module fix) while Qwen3.6 and Nemotron each reached 75/78. Kolibri's first
    attempt aborted on the runner's fatal `quota_unknown` path (declared non-fatal in a fresh root).
  - (8b) The Strata half of the same fix, now a RATE: `reasoning_budget_tokens: 6144` in the ledger
    declaration, ten fresh roots (`strata-20261008-v1..v10`) -> **10/10 at 70/70**. The engine's
    truncation diagnostic still fired in 2 of the 10, and **both of those scored 70/70**: the budget
    does not stop the cut, it moves it after the work is done. Pre-change, 13 sessions had 3
    truncations, all sub-70 (7, 7, 64). Fisher one-sided p = 0.161, so the rate alone is not
    significant - the mechanism is the argument. 4 of the 10 perfect runs reported clean=false/exit 143.
  - (9) THE MEASUREMENT WAS THE REAL BOTTLENECK. `events` (76/76) and `paths` (75/75) are saturated at
    every good configuration, and the frozen ledger concentrates its discrimination in five checks
    (case 19 = ASCII-only digits, the U+0661 trap, fails 14/23 top-group samples; then 7, 5, 0, 6).
    New instrument `new_tasks_20261008.py` = **`ledger2`, 226 checks** (frozen 70, indices 0-69
    byte-identical, + 106 labelled traps + 50 random valid ledgers). Verified: frozen reference
    226/226, the task's own buggy starter 62/226. Offline re-score of 62 saved artifacts splits the
    top group **208-226** where the frozen battery showed a 2-check spread: Swift and 11 Strata
    sessions at 226/226, seven sessions at 225 (only `csv-shape/lone-cr-terminators`), Qwen3.6
    plain/MTP and Kolibri at 208-212, i.e. Unicode digits + header variants. New task #2:
    `new_tasks_repo.py` = a **five-file cross-module repair** (`varint.py` + `store.py` + README +
    public tests + a shim), verified reference 78/78 vs starter 43/78. Both new tasks score through a
    superset module in the new-task root; live root `newtasks-20261008-v1` runs all five tasks.
    LIVE run of that root (Qwen3.6 plain, wall 1374 s): events 74/76, ledger 66/70, paths 75/75,
    **ledger2 212/226** with exactly the Unicode-digit profile the offline re-score predicted for
    this configuration, and **repo 75/78** whose three misses are one named defect - `len(account)`
    (characters) instead of the UTF-8 byte length in the append path.
  - (14) STRATA AT A RAISED CONTEXT (`strata-ctx-20261008-v*`): `--max-context` 32,768 -> **65,536**,
    verified by the engine's own startup line (`context 65536 tokens`), with the validated
    `reasoning_budget_tokens 6144`. **4 of 5 valid runs at 70/70, zero truncation diagnostics** - the
    context cause is gone. The one 7/70 is a harness bug worth remembering: the harness's execute loop
    terminates on `budget.failure`, and the relay's `Budget.account` sets `quota_unknown` when the
    engine reports no usage (a reporting gap, not an outcome), so the session was killed mid-turn at
    169 s with `final_text` empty and exit 143 - while the same condition landing AFTER the work cost
    nothing (v2 scored 70/70 with it). Fixed by wrapping the relay's `Budget` inside the root; v42/v43
    then ran clean. That is the SECOND place the same gap had to be declared non-fatal (the first was
    the candidates runner's sweep guard), and the first where the fix belonged to the RELAY.
    COST: free physical falls to 3.5-5.4 GiB at 64k versus ~10 GiB at 32k (~5 GiB against a 3 GiB
    floor). The engine's arithmetic puts 8-bit KV at ~13.7 KB/token (~0.85 GB at 64k), so most of the
    price is the prefill path, which is sized from the context (chunks up to 8,192 tokens). 64k is
    affordable; a larger context on this pack needs the prefill chunk bounded first.
  - (15) LONG-CONTEXT TASK BUILT (`new_tasks_longctx.py`): `legacy.py` is a deterministic **222 KB /
    ~65k-token, 1800-helper module with exactly one wrong function** and a minimal-edit rule (every
    other function's source must be unchanged). Verified: reference 40/40, its own buggy starter 15/40,
    and 40 checks in **0.32 s** after removing an O(n^2) `ast.get_source_segment` loop that took 63 s -
    over the relay's 30 s scorer limit, which would have scored every live run as zero. Provisioned
    six-task root `newtasks-ctx-20261008-v1` = frozen three + ledger2 + repo + longctx, with the
    provisioning folded into every new-task root from now on.
  - (24) OVERNIGHT 2026-10-08/09 (chain of four batches, 8,510 s). Qwen3.6's repeat produced the best
    six-task sweep recorded: **562/565 = 99.5 %**, all six tasks clean (76 / 69 / 75 / **224** / **78** /
    40). Nemotron-3.5-Lightning-30B provisioned: **544/565 = 96.3 %** in 3,377 s, with `repo` improving
    75/78 -> **78/78** and `ledger2` 223 -> 209 - session variance on that battery runs +/- 14 checks, so
    those two runs are the same configuration. Kolibri's repeat and the Swift retry (v10) are the other
    two batches; Swift's *first* attempt died at 122 s on the usage-gap smoke (see (22)) and was retried.
    Two driver bugs were found and fixed during the chain, both mine: the accumulate patch's record path
    was shadowed by a per-task dict named `record`, so every invocation after the first died at the
    record write *after* its batch had completed (no run data lost; the record was rebuilt from
    evidence), and the extended-loop option was added so a future root can run all nine tasks.
  - (22) `quota_unknown` HAS NOW COST THREE DIFFERENT THINGS - the general rule is that it must be
    demoted at the RELAY in every root, because the harness's `execute()` terminates a session whenever
    `budget.failure` is set and the relay sets that value when a response carries no usage. (a) the
    candidates runner's sweep guard (fixed with the declared tolerant tuple); (b) a Strata 64k ledger
    run killed mid-turn at 169 s with `final_text` empty (fixed by wrapping the relay's `Budget` in the
    Strata root); (c) **tonight, the Swift host smoke killed at 31 s (exit 143, no assistant turn),
    which aborted the whole Swift batch with `AssertionError('OMP native read smoke failed')`** - Swift
    Bonsai 2 reports no usage intermittently (its earlier root needed the same tolerance). Fixed by
    injecting a `_BudgetUsageTolerant` subclass into every new-task root's relay (and into the
    already-built Qwen3.6 root in place), so a usage gap is counted (`usage_gap`) instead of fatal.
    A runner-level guard alone is NOT sufficient: it protects the sweep, not the session.
  - (23) TWO NEW INSTRUMENTS AUTHORED AND VERIFIED, both staged but deliberately NOT in the six-task
    loop so tonight's batches stay comparable. `repo2` (55 checks: byte-length accounting, default-arg
    aliasing, buffer aliasing, swallowed ValueError - reference 55/55, starter 34/55 in 0.07 s) widens
    the multi-file axis after the census showed `repo` splits on exactly one class. `perf` (33 checks:
    30 correctness + 12 invalid-input + 2 graded scale tiers at 100k/1M intervals + API structure -
    reference 33/33 in 5.5 s, the quadratic starter 31/33 failing only the scale tiers) adds an axis
    no other task touches: engineering judgement about complexity. The scale tiers run in a
    subprocess with a 12 s timeout, because a quadratic candidate would otherwise hang the evaluator
    past the relay's 30 s scorer limit and zero the correctness checks with it.
  - (21) STRATA 0.1.41 STAGED AND A/B'D (`staged-strata-20261008/engine-src-v0.1.41`, BUILD.json
    0.1.41, plain-x64 asset sha256 verified, venv+configs preserved from the copied 0.1.40.3 install).
    15 ledger runs at the 64k / 12 GiB / budget-6144 declaration, **all 70/70**, so the engine's own
    rates decide: baseline 0.1.40.3 cold prompt 632.3 (615.9-657) / per-request 70.3 / cache hit 48.5%;
    A (0.1.41 defaults) 636.4 / 68.8 / 49.3% -> NEUTRAL, with the GPU cache holding 2,425 experts vs
    2,407 (the #1454 buffer savings) - take it for the behavioural fixes (hung-engine watchdog,
    `<function= NAME>` parsing, q8_1 clamp), not for speed; B (`--expert-cache 1500`) **REGRESSION**:
    579.6 cold prompt in all three runs against 615.9-657 elsewhere and 41.2% first cache hit vs 49.3% -
    the note's hint assumes an automatic cache bigger than useful, ours is already RAM-budgeted; C
    (`STRATA_ROUTE_RESIDENT=1`) 643.2 / 69.8 -> NO GAIN on a prefill-bound workload (43.6:1 read:write).
    The headline "prompts ~2x faster on Windows when the model is bigger than RAM" targets reads that
    BYPASS the cache (disk streaming); ours is RAM-bandwidth bound at ~630 tok/s and the disk-streaming
    config was never runnable under the 3 GiB floor. TWO OPERATIONAL LESSONS: the engine config is
    SHARED across roots, so an arm that does not declare a value inherits the previous arm's (arm C's
    first batch inherited B's cache setting; the driver now declares it per arm and reads the built
    config back), and a batch launched with a bare shell `&` is reaped when the tool call returns.
  - (20) KOLIBRI ON THE FULL SIX-TASK SUITE: 551/565 (97.5 %) - **exactly Qwen3.6's score, at 1.8x the
    time** (2,971 vs 1,642 agent seconds; 495 vs 274 s/task). Frozen three perfect (76/70/75 = 221/221),
    repo 78/78, longctx 40/40, ledger2 212/226 with the SAME failing profile as Qwen3.6 (the 14
    Unicode-digit checks; its earlier 226/226 was a different session - spread on the finer battery is
    real). So on equal score **Qwen3.6 + provisioning is the fastest successful combo**, and the two are
    indistinguishable on anything the old protocol could resolve. Two mechanics: `repo` hit the 720 s
    wall (44 turns, 60 tool calls; artifact already complete so the score stood - it and MiniCPM both hit
    that wall, so `repo` wants a declared longer wall like longctx), and ledger2 session variance means
    n=1 per task is not a verdict.
  - (19) MiniCPM's `repo` failure is THRASHING, not budget - the quota test refutes its own hypothesis.
    At a 48,000-token quota it ended on `length` at exactly the quota with 43/78 (= the starter); with
    the quota doubled to 96,000 it spent MORE (69,774 tokens, 73 tool calls, 68 turns), ran 18x longer
    than its other tasks (720.2 s - the first 720 s wall hit in the new-task family) and produced a
    WORSE artifact (0/78: the module does not import). Same sweep otherwise: events 76/76, ledger 66/70,
    paths 75/75, ledger2 199/226, longctx 40/40 = 456/565 (80.7 %) at 99.7 tok/s. `quota_unknown`
    appeared again as a budget failure - the harness terminates on `budget.failure` and this engine
    reports no usage intermittently.
  - (18) FAST MODELS ON THE FULL SUITE - the ranking inverts with the bar. gpt-oss-20b (159 s/task) and
    MiniCPM5-2B (176 s/task, 122 tok/s) are the fastest, and both FAIL every hard axis: gpt-oss repo
    **0/78** (all files parse but the module no longer imports - it broke the workspace in 20 clean
    turns) and longctx 15/40 (= the starter); MiniCPM repo 43/78 (= the starter) after ending on
    `length` at exactly its 48,000-token session quota, i.e. it looped until the harness cut it, though
    it did pass longctx 40/40. So the fastest configuration that is SUCCESSFUL ON THE WHOLE SUITE is
    **Qwen3.6 + provisioning**: 551/565 at 274 s/task, the only one passing both repo (78/78) and
    longctx (40/40), and 1.6x faster per task than the only other qualifier Kolibri (430 s/task,
    99.8 %, 226/226 ledger2, 78/78 repo, longctx unrun). On the frozen three alone gpt-oss is fastest
    (177 s, 98.6 %) - but that bar is the saturated one, and its repo 0/78 shows what it hides.
    MiniCPM has the best quality-per-second on the easy axes (121.7 tok/s, frozen three 218/221).
  - (17) PROVISIONED SIX-TASK SWEEP (`newtasks-ctx-20261008-v1`, Qwen3.6 plain, wall 1839 s):
    events 76/76, ledger **70/70**, paths 75/75, ledger2 212/226, repo **78/78**, longctx **40/40** =
    **551/565 (97.5 %)**. The frozen three are perfect for the first time in this configuration (the
    unprovisioned runs gave 215-219/221), and `repo` went 75/78 -> 78/78, both consistent with the cap,
    context and thinking-budget fixes recovering real checks. `longctx` was solved first try and cheap
    (108.6 s, 3,817 tokens for a 65k-token corpus - it greps rather than ingests), so at n=1 it is
    SATURATED for this model like events/paths; a harder variant (more planted defects, or a defect
    needing several distant functions) is what would make it discriminate. The residual shortfall for
    this configuration is now exactly ONE thing: the 14 Unicode-digit checks in ledger2.
  - (16) The community's nudge fix (OpenHands #3992/#3997) is NOT adopted: our prose-quits are completion
    summaries rather than mid-task plans, so a nudge would mostly get "DONE" back, and the narrow
    trigger that would help - a turn cut at the cap - is already covered by the cap raise and the
    thinking budget. Documented in HARNESS-TWEAKS-2026-10-08.md rather than implemented.
  - (11) CORRECTION to (6): the largest sub-perfect bucket is NOT a harness misread. A wider scan (99
    sub-perfect sessions) gives 50 prose-quits, 27 truncated turns, 18 external kills, 4 error stops -
    and ten sampled prose-quit closings are all COMPLETION SUMMARIES ("Solution complete", "solution.py
    repaired" + a bullet list), not mid-task plans. So that class is model self-verification failure
    (the model stops believing it is done, with 1-8 hidden checks still failing) and the harness share
    is **45 of 99 (45 %)**, not 50 %. Consequence: OpenHands' nudge fix (#3992) targets plans, so it
    would mostly get "DONE" from our models - an experiment, not an adoption.
  - (12) PROVISIONING BUILT AND VERIFIED (`provision-20261008-v1`, Qwen3.6 plain): served context
    32,768 -> **131,072**; the host descriptor the harness writes 32,768/12,288 -> **131,072/32,768**;
    and llama.cpp's `--reasoning-budget 6144` + `--reasoning-budget-message` (the llama.cpp equivalent
    of the Strata knob). Verified from the run's own artifacts: `n_ctx_slot = 131072` in all five
    session logs, the launch command carries both flags, `config/models.yml` reads 131072/32768, no
    unknown-argument error, **no hang** (the upstream `--reasoning-budget` hang reports did NOT
    reproduce on b11461). Tasks: events 76/76, ledger 67/70, paths 75/75 = **218/221**, all clean, at
    ~2x the wall of the unprovisioned root (449/414/159 s vs 184/136/245 s) and 3 checks better
    (215/221). The frozen harness is untouched: the host window is patched through the harness's own
    `configuration()` from inside the root, so historical manifests stay valid. Context shift is off by
    default in this build (rules out KV-shift corruption as a cause); `--cache-reuse` left at 0.
  - (13) RESEARCHED others' tweaks -> `local-llm-lab/HARNESS-TWEAKS-2026-10-08.md`. OpenHands #3992
    (nudge policy #3997 unmerged; mini-SWE-agent 3/4 vs OpenHands 1/4 on the same model because
    mini-SWE's format-error loop nudges-and-retries; their repro ran at 577 tokens and 73k/255k, i.e.
    neither length nor context). llama.cpp #20837 (tool calls printed inside thinking): **not our mode -
    0 hits in 324 transcripts** across five markup shapes, so Strata's rescue fix is not needed here.
    llama.cpp #22717 / forge #54: the reasoning-budget sampler hung in some 2026 builds, which is why
    (12) measures a generation instead of trusting the flag. SWE-bench Verified runs every model with
    mini-SWE-agent in a minimal bash environment - the community's comparability direction is LESS
    scaffold, which is why the census splits model from harness rather than adding scaffold.
  - (10) Rates aggregate now separates arms (`+MTP`, `+ledger2`), reports a **collapse rate** (top
    group 0%, MiniCPM/gpt-oss 33% historically, weak models 100%) and a `new_battery` section;
    `rates-20261007.json` regenerated. Queued and needing a decision: raise the served context
    (fixes cause 2 and finally exercises the 262k capability; the host's declared `contextWindow`
    lives in the frozen harness), the Strata thinking budget at n>=10, and re-baselining the top group
    on the two new tasks. Method notes: `clean_finish`/`exit 143`/`quota_unknown` are NOT failure
    signals here (they appear on 70/70 runs); attribute failures from the engine log and per-turn
    `stopReason` before counting them.
- October 7 (later): RETESTS of RAM-stopped work and one new capability, after Kevin asked what
  the extra RAM unlocks. One inference workload at a time, no gate changed, no reboot, no app
  killed.
  - Qwen3.8-27B Q4_K_M PROBED and found NOT viable for the harness on this card, for a
    measured reason. With llama.cpp b11461 (published today, 0.6.0-dev build 11461 commit
    4d756bc72) and `--fit on --fit-target 1536` at the protocol context 32768: load 12.6-13.6 s,
    prompt 254-370 tok/s, decode 4.28/4.05 tok/s (no head), 4.45/3.99 (MTP head), 4.62/4.26
    (DFlash head) - MTP/DFlash buy only +4-13% because draft acceptance on free-form code is
    ~33% (the same heads hit 0.90-0.97 on the repetitive tool-call turn). GPU used 8.5-10.1 GiB
    of the 18.97 GB of weights, so ~half sits in RAM and decode is RAM-bandwidth-bound. Tool
    calls, reasoning_content and the full roundtrip all pass, so it is functionally
    harness-compatible: only speed fails, and at ~4.3 tok/s the 720 s wall covers ~3,000 tokens
    against the 14k-24k the reference runs needed. CONCLUSIONS: host RAM removes the residency
    barrier, not the throughput barrier; "fits in RAM" is not "usable"; a dense 27B needs VRAM
    residency (a smaller quant) or it is not a time-bounded agent candidate here. The prepared
    root `candidates-20261007-v3` is declared and audited but deliberately NOT run, with that
    reason recorded. Read staged-27b-20261007/REPORT.md.
  - Also learned: b11461 works on this box and adds `--fit`/`--fit-target` auto-placement,
    `--spec-type draft-mtp|draft-dflash` with `-md` heads, `--n-cpu-moe`, `--cache-ram`,
    `--reasoning-effort`/`--reasoning-budget`. Its Windows build ships thin launchers: invoke
    llama-server.exe via subprocess with the full path, not `./llama-server.exe` from a POSIX
    shell, or argv[0] parsing fails with "command not found".
  - A3B all-experts-in-RAM RETESTED and now completes. `a3b-offload-20261007-v1` re-runs the
    exact 2026-09-24 configuration that died on the sustained paging guard (48 CPU expert
    layers = every routed expert in RAM, `--n-cpu-moe 48`, same driver/runtime/prompts/guards,
    ROOT repointed, runtime copied). Result: short 34.82 tok/s, long 33.11 tok/s median (3
    reps), long TTFT 7.16 s, load 7.90 s, cleanup verified. Min free physical 27.61 GiB where
    the 32 GB attempt aborted at 3.69 GiB. It is now the fastest placement in that family but
    only +2.7%/+1.2% over the 32-layer baseline, so the honest claim is "no longer impossible,
    not measurably better" - 3 reps do not separate them. 2026-09-24 root untouched.
  - NEW capability staged: Qwen3.8-27B (ggml-org, revision 71bc7b62) Q4_K_M 18.97 GB plus its
    MTP (1.68 GB) and DFlash (1.09 GB) draft heads, on llama.cpp b11461 (published
    2026-10-07T06:50Z, tag commit 4d756bc7, Windows CUDA 13.4 x64 asset digest
    62c91b76abe5a704304eb1d2a5041944953d438c1b1d9f6b56261ea36b0461cf). The b11461 cudart asset
    is byte-identical to the bundle already staged for b11429 (738f8c25...), so it was reused,
    not re-downloaded. This is the first model here whose weights (18.97 GB) cannot be fully
    GPU-resident on a 12 GB card and whose usefulness depends on 64 GB of host RAM.
  - Kolibri-1 (78B MoE, 3.46B active, Apache-2.0) is the payoff, and the configuration matters
    as much as the model. Q3_K_M 37.5 GB staged from Hob-forge revision 5d285d87 (HF LFS oid
    b797de9c...) on the community llama.cpp hob-b11434 (0.5.0-dev build 11434, commit 8798b654e
    = upstream 836d571 + kolibri1-llama.cpp.patch; required because stock llama.cpp has no
    kolibri1 support; release asset digest 5ab681ee...). With all 384 routed experts in system
    RAM (`--cpu-moe`, attention + shared expert on the card, q8_0 KV, context 32768):
      - mmap (default): load 7.1 s, prefill 349/352 tok/s, decode 38.20/34.14 tok/s, min free
        physical 17.08 GiB. This LOOKS fine but fails the harness: the one-shot prompt is about
        9.5k tokens, and with experts faulting in from disk prefill collapsed to 170 tok/s, so
        the 90 s host smoke and 720 s task walls could not hold.
      - --load-mode none (resident): load 27.7 s, prefill 881/972 tok/s on the same 9.8k-token
        prompt, decode 44.35/42.98 tok/s, min free physical 9.82 GiB (floor 3).
    So: 78B total / 3.46B active runs at ~43 tok/s decode and ~970 tok/s prefill on a 12 GB card
    because the expert pool lives in the 64 GB of RAM. Compare the dense 27B at 4.28 tok/s on the
    same box: three times the parameters, ten times the speed. Q4_K_M (44.2 GiB disk, 46.6 GB
    resident per the publisher) was rejected on arithmetic - it does not fit beside the desktop.
    Read ai_bench/staged-kolibri-20261007/REPORT.md.
    SCREEN RESULT (`candidates-20261007-v7`, first clean run): parser and host smoke passed;
    events 76/76 (240.9 s, 7,772 tokens), ledger 69/70 (240.5 s, 7,576 tokens, case 19 failed),
    paths 75/75 (358.0 s, 11,623 tokens) - every task clean, inside the 720 s wall, full usage
    reporting, no quota anomaly. First local candidate with two fully correct-and-clean tasks in
    one clean run; comparison table in candidates-20261007-v7/REPORT.md. Envelope: min free
    physical 9.12 GiB, min commit 16.58 GiB, min GPU free 7.70 GiB, max GPU used 3.96 GiB
    against floors 3/2/0.5; audit verified 120 protected files, no lock, no resident model.
    Repeat before treating the numbers as a model verdict (the MiniCPM paths outlier is the
    standing reason).
  - RUNNER TRAPS found by this work, both fixed only inside the new roots: (1) the frozen harness
    teardown asserts port-closed plus all-owned-pids-gone with a 5 s port grace, and a 37.5 GB
    server leaves the process table more slowly - `candidates-20261007-v6/-v7` override
    Session.__exit__ to extend the grace to 180 s, save cleanup-grace.json, and still re-raise if
    anything survives; (2) a candidates root must carry the scorer's sibling task modules
    (otherwise abnormal_evaluator_exit 2 = unscored zeros) and its generated
    source/relay_<model>.py must be deleted before a re-run in the same root.
  - FIRST APPLES-TO-APPLES THROUGHPUT TABLE, `throughput-20261007` (one script, one protocol, one
    server at a time: ctx 8192, 1k/4.9k-token /tokenize-calibrated prompts, temp 0, ignore_eos,
    64-token warmup + 3 reps of 256 tokens, floors checked every 2 s). Decode tok/s at 1k / 4.9k
    prompts, with min free physical: ling-3.0-tiny 226.3/224.6 (33.1 GiB); minicpm5-2b 187.6/173.9
    (37.4); spark-x2.5-4b 105.5/103.1 (35.5); granite3-moe-3b 84.3/n-a (41.2); swift-bonsai-2-pq2
    65.0/62.9 (32.7); gemma-4-26b-a4b 58.9/54.6 (30.3); kolibri-1-78b 42.2/40.9 (8.1);
    qwen3-30b-a3b-thinking 35.5/34.1 (25.3); qwen3-coder-30b-a3b 34.1/35.1 (23.4);
    nemotron-3.5-lightning-30b 35.2/33.8 (20.6); qwen38-27b dense 5.0/4.8 (21.7).
    - ANSWERS it settles: (a) yes, several already-tested models are faster in raw decode - the
      small dense ones by 2.5-5x (ling 226, minicpm 188, spark 106) and the mid-size MoEs by
      1.3-1.5x (swift 65, gemma 59); Kolibri is 7th of 12 completed rows and only the dense 27B is
      slower. (b) until this run the only strictly comparable throughput family was the A3B
      placement sweep; the quality axis (frozen coding protocol) has been comparable across
      models for a while. (c) the 30B-class MoE band is 34-36 tok/s with experts in RAM, and the
      78B Kolibri is only ~20% behind them at 2.5x the size, while the dense 27B is one seventh
      of the band - the RAM-based MoE recipe is what makes big models usable here.
    - ENGINE CONTROL: the identical qwen3-coder-30b-a3b model and placement on b10883 vs b11461 is
      within noise (34.1/35.1 vs 35.4/34.0 decode, prefill ~5% higher on b11461). b11461 buys
      features (--fit, MTP/DFlash, --n-cpu-moe, --reasoning-*), not speed for this model.
    - Two rows excluded with reasons: gpt-oss:20b from the Ollama store is rejected by every
      llama.cpp build here ("unknown model architecture: 'gptoss'"), and granite3-moe-3b has a
      4096-token native context so the 4.9k long prompt is refused (short-prompt decode 84 tok/s).
    - Harness-effective rate is NOT decode rate: from the coding screens, tokens/wall gives ling
      174-184, minicpm 119-127, spark 90-93, swift 45-47, kolibri 31.5-32.5, gemma 9.7-32.9.
  - Candidates for the next MoE test, researched: `ggml-org/Qwen3.6-35B-A3B-GGUF` (35B total /
    3B active, Q4_K_M 19.0 GiB, plus MTP and DFlash heads - the preferred publisher, newest
    small-active MoE); the three local 30B-class MoEs are benchmarked but not yet screened on the
    coding harness (nemotron-3.5-lightning:30b, qwen3:30b-a3b thinking, qwen3-coder:30b);
    Kolibri-1 has no alternative quantizer yet (only Hob-forge) and Q4_K_M needs 46.6 GB resident,
    so it needs the desktop footprint cut to fit; nemotron ONYX quants exist (compact 21.6 GB);
    gpt-oss would need an official GGUF re-download. Capability variant worth a run: Kolibri at
    64k-256k context (the publisher validated 253k tokens on this exact card).
  - SWIFT BONSAI 2 PQ2's missing row is FILLED and its earlier scores REPRODUCED. Root
    `candidates-20261007-v8` re-ran it with one declared change (quota_unknown non-fatal, which is
    what aborted the 2026-09-30 sweep before paths) and the extended teardown grace: events 76/76
    clean+correct (322.3 s, 15,251 tokens), ledger 70/70 correct (469.4 s, 21,014), paths 75/75
    correct (453.8 s, 20,490). Swift's complete set is 76/76, 70/70, 75/75 - by one ledger case the
    highest-scoring local candidate in the series, ahead of Kolibri-1 (76/76, 69/70, 75/75).
    Envelope: min free physical 35.62-35.87 GiB, min GPU free 0.87-0.92 GiB, max GPU used
    10.79 GiB, no floor tripped; audit verified 120 protected files. Effective rates 44.8-47.3
    tokens/wall-second (the harness-free benchmark for the same model: 65.0/62.9 tok/s decode).
    - REPRODUCIBILITY: events 76/76 and ledger 70/70 reproduced exactly two days apart and across
      the 32 -> 64 GB platform change. That is 2/2 identical, against Strata's ledger 7/70 vs
      70/70 and Gemma's events 76/76 vs 75/76 - so non-reproducibility here is task- and
      model-specific, not a blanket property of the harness. Curve: 23 task records now in
      C:/Users/kevin/local-llm-lab/harness-speed-20261007.json.
    - The `clean_finish: false` on ledger and paths is NOT a scoring loss: both artifacts scored
      full marks. The flag records no final summary text (ledger) and a post-artifact termination
      (paths, exit 143). The scorer reads the artifact, not the transcript.
  - OTHER MoEs SCREENED on the frozen protocol, four new roots (`moe-screens-20261007/screen_moe.py`
    builds one root per model from `candidates-20261007-v8/run.py`, declares the MoE rule
    `-ngl 99 --cpu-moe --load-mode none`, and screens them serially). Results, checks passed
    (events 76 + ledger 70 + paths 75 = 221) and wall per task:
      - NEMOTRON-3.5-LIGHTNING-30B (MoE 128 exp / 6 active, 23.7 GiB, b11461): 76/76, 67/70, 75/75
        = 218/221 = 98.6%, 3/3 clean, 403/561/452 s.
      - GPT-OSS-20B (MoE 32/4, MXFP4 official ggml-org GGUF, 11.3 GiB, b11461): 75/76, 68/70,
        75/75 = 218/221 = 98.6%, 3/3 clean, 66/58/52 s - AND by far the fastest task completion in
        the series, because it used only ~1.2-1.6k tokens per task instead of 7.6-21k. It had never
        run here: the Ollama-store copy is rejected by llama.cpp ("unknown model architecture:
        'gptoss'"), so the official MXFP4 GGUF was staged (revision ef9b12f2, sha256 27cd6c43...).
      - QWEN3-CODER-30B (MoE 128/8, 17.3 GiB, b10883): 67/76, 62/70, 75/75 = 204/221 = 92.3%, 3/3
        clean, 207/89/199 s.
      - QWEN3-30B-A3B-THINKING-2507 (MoE 128/8, 17.3 GiB, b10883): 66/76, 14/70, 0/75 = 80/221 =
        36.2%, 437/371/405 s. The paths artifact shipped a Python syntax error ("expected an
        indented block after 'for' statement on line 23") and ledger collapsed to 14/70, so the
        thinking variant of the same architecture is markedly worse at these tasks than the coder
        variant despite identical size/placement. 3/3 "clean" flags are meaningless here - the
        artifact was broken.
      - INELIGIBLE, with reasons: granite3-moe-3b (native context 4096 tokens; the protocol's
        one-shot prompt is ~9.5k, measured failing with HTTP 400) and gpt-oss-120b (63.4 GB MXFP4,
        cannot fit beside the desktop on a 63.46 GiB system).
    - Two driver bugs found and fixed while doing this, worth remembering: an Ollama blob has NO
      .gguf extension, so a root must link it under a .gguf name or the runner's
      `next((ROOT/'models'/name).glob('*.gguf'))` raises StopIteration; and a shell redirect to a
      path containing `..` from inside the root silently aborts the whole run (use absolute log
      paths).
  - RANKING after finishing the MoE set (`moe-screens-20261007/REPORT.md`, machine-readable in
    `local-llm-lab/ranking-20261007.json`). Success = checks passed / attempted; best observed
    multi-task sample per model; eff = tokens/wall (includes prefill and every turn).
    Overall: Swift dense 221/221 = 100.0% (eff 45.1, raw 63.9) > MiniCPM dense 220/221 = 99.55%
    (eff 121.1, raw 180.7) > KOLIBRI-1 MoE 220/221 = 99.55% (eff 32.3, raw 41.5) >
    NEMOTRON-3.5-LIGHTNING MoE 218/221 = 98.64% (eff 31.1, raw 34.5) > GPT-OSS-20B MoE 218/221 =
    98.64% (eff 23.7, raw 28.4) > Gemma MoE 144/146 = 98.63% (2 tasks only) > QWEN3-CODER-30B MoE
    204/221 = 92.31% > QWEN3-30B-A3B-THINKING MoE 80/221 = 36.2% (broken paths artifact) > ling
    18.1% > spark 8.1%.
    - MoE-only order: Kolibri-1 (most accurate, best MoE token rate), Nemotron (2nd), gpt-oss-20b
      (3rd by accuracy, FASTEST BY WALL TIME of everything: 176 s for the whole task set vs 264 s
      MiniCPM, 839 s Kolibri, 1246 s Swift - it wins on token frugality, 1.2-1.6k tokens per task
      against 7.6-21k), Gemma (2 tasks only), Qwen3-Coder, Qwen3-Thinking.
    - CONCLUSION: MoE + RAM residency buys SCALE (a 78B model that otherwise would not run) and
      token efficiency at equal accuracy, NOT speed - the two fastest models remain the two dense
      ones. And architecture is not destiny: Qwen3-Coder 92.3% vs its Thinking sibling 36.2% at
      identical size, quant, engine and placement (the thinking variant shipped a Python syntax
      error in the paths artifact and scored 14/70 on ledger).
    - Selection caveat recorded: these are best observed samples, not central estimates. MiniCPM's
      four scored runs read 99.55%, 98.64%, 66.97% (+1 unscored), and its paths alone was 75/75,
      75/75, 9/75 under identical declarations. Gemma has never completed a three-task sweep.
  - STRATA ENGINE BUMP and ledger RATE. Upstream moved four releases while we were pinned:
    v0.1.39 (installed 2026-10-06) -> v0.1.40.3 (published 2026-10-07T18:01Z). Upgraded in a COPY
    (`staged-strata-20261007/engine-src-v0.1.40.3`, source HEAD d5ea7133, engine binary 159.1 MB
    sha256 34cde150b21148e6cf192dbf2242e5544d3456c09ab0010837aaacfda11eca5b, release asset sha256
    766373e74d1e25c9e87d7464b1e0c04857ec9fb4326a4d50c3a9d53ea84b26e4 verified, venv/pack/config
    preserved, v0.1.39 tree untouched, old engine binaries backed up; `setup --check` passes).
    Record: staged-strata-20261007/upgrade-record.json.
    - Runs on v0.1.40.3 (64 GB, resident budget 24 GiB, mmap experts, lookahead off, declared walls
      events/paths 720 s and ledger 3600 s): LEDGER 7/70 (220.6 s, 12,546 tokens), 64/70 (337.1 s,
      16,000 tokens = session quota), **70/70 correct** (190.2 s, 8,190 tokens); EVENTS 76/76
      correct+clean (195.6 s, 8,848); PATHS 75/75 correct+clean (210.2 s, 10,010).
    - LEDGER RATE across both engines, five samples: 70/70 (v0.1.39), 70/70 (v0.1.40.3), 64/70, and
      7/70 twice. So the ledger completes about 2 of 5 times and its failure mode is early
      termination after 2-3 turns, not the wall - the same diagnosis as before, now with n=5.
    - The engine bump is correctness- and speed-neutral here: effective decode stayed in the same
      band (43.1-56.9 tok/s on v0.1.40.3 versus 45.8-48.9 on v0.1.39), events/paths unchanged. Its
      value is the mmap prompt-path fix, the tool-call rescue (a `<tool_call>` quoted in thinking
      or inside a code fence no longer executes), the short-prompt CPU-share opt-in, and the
      crash/NaN fixes - not raw speed.
  - NEW STRATA LEVER, only available because of the RAM: the upgraded `setup --check` on this
    64 GB machine lists Q2_0 (~48 GB RAM) FITS, IQ2_XS (~48) FITS, IQ3_XXS (~60) FITS, IQ3_S (~62)
    FITS, IQ1_M (~32) FITS - at 32 GB only IQ1_M fit, which is what every previous Strata run used.
    Strata's own measured table for an RTX 5070 12 GB gives decode at 32k context: Q2_0 ~88 tok/s,
    IQ2_XS ~65, IQ3_XXS ~57 (prompt ~571 / ~495 / ~435), against our measured IQ1_M 46-49 tok/s
    (prompt 550-670). Q2_0 is ~1.8x the decode at a HIGHER quant, and it is the full model rather
    than the Coder's half-experts build. Cost: the Coder repo publishes only IQ1_M, so this means
    the original family at Q2_0 - 66.4 GB of GGUFs of which only 37.6 GB is new, because Q2_0's
    second shard (316b46f3...) is byte-identical to the Coder IQ1_M shard 2 already staged and the
    mmproj is the same file (both hardlinked). Staged to `staged-strata-q2-0-20261007`; plan and
    hashes in local-llm-lab/q2_0-staging-plan.json.
    - Q2_0 INSTALLED, PACKED AND MEASURED. The pack built cleanly into
      `Staged-strata-data/packs/q2_0` and the engine wrote `strata-q2_0.json`
      (model_name qwen3.8-flash-next-q2_0). FIRST ATTEMPT FAILED ON A FLOOR, and that is itself the
      finding: with `--resident-budget-gib 24` the load drove free physical to **0.62 GiB** against
      the 3 GiB floor while the engine was filling the GPU expert cache, so it never answered and
      the monitor wrote STOP (`strata-20261007-v7`, preserved). Cause: Q2_0's native shard is
      37.6 GB against the Coder IQ1_M's 29.6 GB, and the mmap'd pages add to the 24 GiB resident
      copy. Q2_0's own advertised ~48 GB residency does not fit beside our desktop (~44 GiB free).
    - REPEATED AT A DECLARED 12 GiB BUDGET and it works better than budget 24 ever did:
      `strata-20261007-v8` scored **ledger 70/70 clean and correct** in 157.4 s with 9,642 tokens =
      **61.3 tokens/wall-second**, and the engine's own log shows **70.8-72.4 tok/s decode** with a
      70.1% expert-cache hit, load 23.8 s. Envelope: min free physical 4.95 GiB, min commit 23.23,
      min GPU free 0.71, max GPU used 10.95 GiB - every floor held. Compare IQ1_M on the same
      engine: 43.1-56.9 tok/s effective and 46-49 tok/s decode. So Q2_0 is ~1.5x the decode of
      IQ1_M here AT A SMALLER BUDGET, because the quant reads fewer bytes per expert and the cache
      hit rate is high - the earlier suspicion that a small budget would make Q2_0 slower was
      wrong, and the measurement settled it.
    - The earlier 1.8x expectation (Strata's ~88 tok/s at 32k) is not reached: we measure ~72, which
      is consistent with their table being a best case. Still a clear win over IQ1_M.
    - SECOND LEDGER SAMPLE (`strata-20261007-v9`, identical declarations): 70/70 clean and correct,
      137.2 s, 8,644 tokens = 63.0 effective tok/s. So the Q2_0 ledger is 2/2 complete-and-clean
      against IQ1_M's 2/5, and the full Q2_0 sweep is 221/221 with all three tasks clean. Report:
      `strata-runs-20261007/REPORT.md`.
    - FASTEST PERFECT-SCORING COMBO, computed over every task record
      (`local-llm-lab/all-task-records-20261007.json`, per-task table): exactly TWO configurations
      have ever passed 100% of checks on a full three-task sweep. Strata Q2_0 at budget 12
      (`strata-20261007-v8`: 221/221, events 208 + ledger 157 + paths 196 = 561.4 s wall, effective
      63.0 tok/s) and Swift Bonsai 2 PQ2 (`candidates-20261007-v8`: 221/221, 322 + 469 + 454 =
      1245.5 s wall, effective 45.6 tok/s). So Q2_0 is 2.2x faster on agent time and 2.0x faster
      including the model load per session (630.6 s versus 1257.7 s total), and 1.4x faster per
      token; it also beats the IQ1_M@24 tasks assembled across
      roots (596.0 s, 45.4 tok/s). Caveat: Q2_0's perfect rests on one full sweep plus a second clean
      ledger (v9), and events/paths are single samples; if 99% is acceptable instead of 100%,
      gpt-oss-20b is faster still (218/221 in 176.5 s) and MiniCPM5-2B does 220/221 in 264.3 s.
  - PLANNING PROBE: asked the Q2_0 model what the lab should do next, giving it only facts
    (machine, constraints, measured tables, on-disk inventory, anomalies) and no plan, queue or
    recommendation. Comparison written up in `local-llm-lab/plan-comparison-20261007.md` against a
    baseline I pre-registered BEFORE reading its answer (`my-plan-20261007-pre-registered.txt`).
    - It MATCHED my top priority unprompted: reproducibility first - re-run MiniCPM (its `paths`
      75/75, 75/75, 9/75), re-run Q2_0 at 12 GiB, replicate the other thin-evidence models, all with
      n>=3 in fresh directories. It also asked for owner authorization unprompted, refused
      gpt-oss-120b on fit grounds, and asked for load time to be reported separately from agent time.
    - It MISSED: the Kolibri long-context capability test, the b10883-vs-b11461 engine question, the
      Strata quant curve (IQ2_XS/IQ3_XXS), and any new-model acquisition. Two of those gaps are
      artefacts of my brief (it listed only on-disk models and no acquisition research).
    - It DISAGREED on one item: it proposed exploring the dense 27B at reduced context, whereas I treat
      it as settled. Existing data settles it its way or mine: the uniform benchmark ran that model at
      ctx 8192 and it still decoded at 5.00/4.76 tok/s, so context is not the blocker.
    - It ADDED: an audit of gpt-oss's token frugality (is 1.4k tokens/task real efficiency or an
      accounting artefact?), a why-do-fast-models-fail pass on ling/spark, and a gate-safety sweep
      before ranking.
    - Practical limit on "taking over": three attempts were needed to get an answer at all. Default
      `reasoning_effort: high` produced a 6,761-token think whose page-in rate armed the frozen
      sustained-paging guard (run stopped, root preserved, floors untouched); `reasoning_effort: low`
      with a 4,000-token cap spent the whole budget reasoning and emitted NO visible content; only the
      documented per-request `reasoning_budget_tokens: 2000` produced a plan. It is a model behind an
      API, not an agent - the agency lives in the harness.
  - ITEM 1 OF THE PLAN DONE (rates): 12 repeats in fresh roots plus the historical samples, aggregated
    into task-level distributions (`rates-20261007/aggregate.py`, JSON in
    `local-llm-lab/rates-20261007.json`). Task scores across every root that scored that task:
      - kolibri-1: events 76,76,76 (3/3 full) | ledger 68,69,70 (1/3 full) | paths 75,75,75 (3/3)
        -> 220/221, 219/221 and now 221/221: its third sample is the first perfect sweep.
      - nemotron-3.5-lightning-30b: events 76,76,76 (3/3) | ledger 67,68,68 (0/3) | paths 75,75,75
        (3/3) -> 218/221, 219/221, 219/221. The most stable large configuration measured.
      - gpt-oss-20b: events 75,76,0 (1/3) | ledger 68,65,66 (0/3) | paths 75,75,75 (3/3) -> 218/221,
        216/221 and one 141/221 caused by a single all-or-nothing events collapse.
      - minicpm5-2b: 6 full sweeps 0, 98.6, 99.5, 67.0, 96.8, 96.8 % (median 96.8); paths 4/6 full
        marks with the historic 9/75 outlier, ledger never full (63-69).
      - qwen3-coder-30b: 204/221, 197/221, 202/221 - consistent 89-92 %.
      - swift: 221/221 and 146/146 (two samples, events and ledger full marks both times).
      - strata Q2_0: ledger 70,70,7,70 (3/4 full - CORRECTION: root v15-1 at the same
        12 GiB budget, scored 7/70 in 97.6 s with 241 tokens, the identical early-termination mode the
        Coder pack shows, so the quant improves the completed runs but does NOT remove that failure
        mode); events 76,76,76 (3/3); paths 75,75,75 (3/3, one task per fresh root).
      - strata Coder IQ1_M: ledger 7,70,7,64,70 - bimodal, 2/5 full; events 76 and paths 75.
    CONCLUSION: events and paths are stable for good models; LEDGER is where every model loses points
    (no model but Swift and Strata Q2_0 ever scored 70/70); and each model has ONE characteristic
    failure mode (minicpm paths, gpt-oss events, Strata IQ1_M ledger) rather than general flakiness.
    That is what the "rate over n runs" convention (DECISIONS-AND-CONVENTIONS-20261007.md) is for.
  - TWO HARNESS CAUSES found by the repeats, both fixed and worth remembering:
    (1) the minicpm and kolibri repeat roots were built from a template carrying the STRICT quota
        guard, so their sweeps aborted after `events` on the engine's `quota_unknown` report, while
        the gpt-oss/nemotron templates carry the declared relaxation. Scores are unaffected; only
        sweep continuation is - check which declaration a template carries before mixing it into a
        rate set.
    (2) the Strata repeats tripped the 0.5 GiB free-VRAM floor twice (0.41/0.31, then 0.34/0.30 GiB,
        where the reference run held 0.71) even after the runner declared VRAM_RESERVE_MIB 2000 -
        because the ENGINE reads its run config, and `configure` had not been run in the new roots,
        so the config still said 1500. Roots v13 and v14 are preserved; v15 runs configure first.
  - ITEM 3 DONE - Kolibri-1 LONG CONTEXT, and the publisher's claim reproduces exactly: three planted
    access codes recovered 3/3 at every context tested - 32k (24,758-token prompt), 65k (50,260),
    131k (102,587) and **262k (206,188 tokens)** - on the same 12 GB card, with `--cpu-moe
    --load-mode none`, q8_0 KV and flash attention. Load 24.7-27.7 s at every size; VRAM cost rises
    from 4.5 to 7.3 GiB while free physical stays ~9 GiB, so context costs VRAM, not host RAM. The
    first 128k attempt failed on my probe, not the model: the prompt builder re-tokenized the growing
    text every round (O(n^2)) and timed out; it now tokenizes twice. Report:
    `kolibri-ctx-20261007/REPORT.md`. Implication: our 32k protocol is a choice, not a limit.
  - ITEM 4 DONE - Qwen3.6-35B-A3B (ggml-org revision baec3ebe, Q4_K_M 20.42 GB, plus MTP 1.06 GB and
    DFlash 0.42 GB heads, all sha256-verified) is the best large model here yet: coding screen
    **events 76/76, ledger 68/70, paths 75/75 = 219/221 = 99.1%**, all three tasks clean, 569 s of
    agent time, 38.1 effective tok/s, min free physical 24.26 GiB (Kolibri needs 8-9 GiB of headroom
    for the same accuracy class and runs at 32 tok/s). Uniform bench: load 9.6 s, prefill 1,087/1,147
    tok/s, decode **46.14/46.17 tok/s** plain; and **67.06/62.06 tok/s with its MTP head attached
    (+45% / +34%)** - the first speculative-decoding feature here that changes the picture, against
    +4-13% for the 27B's MTP. Root `candidates-20261007-v24` (plain) and `-v25` (MTP, declared);
    report `staged-qwen36-20261007/REPORT.md`.
  - ITEM 6 SUBSTITUTED, stated rather than silently dropped: the original form (download IQ2_XS 68 GB
    and IQ3_XXS 75.8 GB and compare quants) needs ~113 GB of disk against 129.5 GB free and about two
    hours, and its expected value is bounded because IQ1_M -> Q2_0 already showed a better quant
    reduces but does not remove the ledger failure (it is behavioural). Substituted with the
    resident-budget curve on the pack we already have (Q2_0 at 8 GiB, one task per fresh root), which
    tests the variable that is actually actionable on this box. The IQ2_XS/IQ3_XXS comparison stays
    available if disk and time are granted.
  - ITEM 6 SUBSTITUTE DONE - the resident-budget curve on the Q2_0 pack, one task per fresh root:
    at 12 GiB the ledger reads 70,70,7,70 (3/4) with min free physical 4.95 GiB; at 8 GiB it reads
    70,70,70 (3/3) but **one session sampled 2.990 GiB - below the 3 GiB floor - so the monitor
    tripped and wrote STOP** (the agent had finished, so the 70/70 stands; root v16-1 preserved).
    Events and paths are full at both, and effective rates are comparable (56.6-68.4 versus 61-66).
    COUNTERINTUITIVE RESULT WORTH KEEPING: a LARGER resident budget leaves MORE free RAM here, because
    fewer expert reads means less page-cache pressure from the pack and native files. Recommendation:
    keep 12 GiB; 16 GiB is an owner-decided experiment only (raising it is what tripped the load-time
    floor in v7); do not lower it to 8. The shared engine config was restored to budget 12, reserve
    2000 afterwards.
  - PLAN COMPLETE. All eight pre-registered items are done or explicitly substituted, with evidence:
    see `local-llm-lab/PLAN-EXECUTION-20261007.md` for the item-by-item summary and the five new queue
    items the work created (n=3 MTP-vs-plain arms; rate sets for the three best configurations; a probe
    into the ledger's early-termination behaviour; the tool-call-rescue effect; Qwen3.6 at long context).
  - ARCHITECTURE CHECK of the four models that clear 90% success on the coding protocol, read from
    their own GGUF metadata (`local-llm-lab/arch-check-20261007.json`): MiniCPM5-2B Q8 arch `llama`
    with 0 expert and 126 dense FFN tensors = DENSE; Swift Bonsai 2 PQ2 arch `qwen35` with 0 expert
    and 192 dense FFN tensors = DENSE (ternary-quantized); Gemma 4 26B-A4B arch `gemma4` with 90
    expert tensors and 128 experts / 8 active = MoE; Kolibri-1 78B arch `kolibri1` with 150 expert
    tensors and 384 experts / 6 active + 1 shared = MoE. So two of the four are MoE. CORRECTION:
    Swift Bonsai 2 PQ2 was labelled MoE in the first throughput report - it is not; that report now
    carries the corrected row plus a "kind column verified from GGUF headers" section. Implication:
    among the >=90% group the two fastest (MiniCPM 124 eff / 181 raw, Swift 45 eff / 64 raw) are
    both DENSE and fully GPU-resident, while the two MoE models are slower (Gemma 19-33 eff / 57
    raw, Kolibri 32 eff / 42 raw) but carry far more capacity - MoE plus RAM residency buys scale
    (a 78B model that otherwise would not run), not speed.

- October 7 resume after the RAM install: decision track finished on the 18-window set,
  suite and the two big runs prepared. No gate changed, no app killed, no reboot. Only
  resource action was `wsl --shutdown` (idle Ubuntu, already Stopped, 828 MiB reclaimed;
  free physical 42.35 -> 44.25 GiB). There was nothing else to free: GPU was 1411/12227 MiB
  used, all of it desktop compositing, and no model server was resident.
  - VRAM/RAM audit: 1411 MiB GPU used (mscopilot, LinkedIn, NVIDIA Overlay, webview2,
    explorer, Discord, Chrome, PowerToys, WhatsApp, Killer, Dell tray - all C+G display
    clients), 42.35 GiB free physical, 56 GiB commit free, no listener on 8080/11434/18091,
    no RUNNING.lock anywhere, ollama absent. No hog existed.
  - New root `decisions-20261007-v1` (runner byte-identical to the corrected -v2). Screened
    the three staged models that had never been run on `/v1/systemone`: laya 14/18 (0/4
    caught, 0/14 false alarms, p95 183 ms, p 0.386-0.693), kev0 14/18 (0/4, 0/14, p95
    169 ms, p 0.353-0.573), lev 14/18 (1/4, 1/14, p95 345 ms, p 0.139-0.895 - the only one
    of the three whose probability crosses 0.85). Peak server private 4.32 GiB vs the 6 GiB
    cap; min free physical 39.77 GiB; audit clean, no lock left.
  - Determinism probe (throwaway, `evidence/diagnostics/determinism.py`): lev and laya are
    BIT-IDENTICAL over two full passes of all 18 windows (max |delta p_stuck| 0.0, identical
    threshold crossings). The decision endpoint is deterministic, so a single screen here IS
    a point estimate - unlike the mimo agent harness. That refines the "report a rate over n
    runs" question: it applies to the agent harness, not to `/v1/systemone` scoring.
  - CORRECTION, nimble and the cap: nimble is NOT blocked and the 6 GiB cap is NOT an open
    decision. Kevin authorized an 8.0 GiB worker-private declaration for the GPU systemone
    track on 2026-10-05 and `decisions-20261005-v3` executed it: nimble 15/18, 2/4 stalls
    caught, 1/14 false alarms, p95 596 ms, peak private 6.94 GiB - the best 18-window result
    of all six staged models. The stale wording in RAM-INSTALL-2026-10-07.md Parts 4-5 is
    corrected in place. Conclusion carried forward: 18 archived windows cannot rank these
    models (4 of 6 never cross 0.85 at all); the published suite is the substrate.
  - Published suite DONE on the new platform, root `bespoke-suite-20261007-v1` (runner
    byte-identical to the 2026-10-05 root, inherits the 8.0 GiB v3 declaration). Inputs
    re-proved locally with no network: 13/13 subsets reproduce the committed
    `dataset_sha256` and count, 3,880 records. Results, macro/micro: nimble 75.65/77.11
    (carried), kev4 74.42/75.28 (carried), lev 68.41/71.11 (465 s), kev0 61.21/63.27
    (194 s), laya 58.01/62.04 (136 s). Peaks 4.34/3.02/2.03 GiB private, min free physical
    40.0 GiB, floors untouched, audit clean. By type, `score` is the weak primitive for all
    five (nimble 52.6, kev4 50.4, lev 31.9, kev0 33.0, laya 28.7 macro).
    - Decisive: the suite OVERTURNS the 18-window reading. lev was the only new model whose
      p crossed 0.85 there; on 3,880 labelled records it is 6 macro points behind the 4B kev4
      and 7.2 behind nimble. Nothing local beats kev4/nimble; published Jev 1.13.0 is 76.0.
    - lev's loss is one subset: summeval-consistency 0.194 (28/144 argmax) with mean expected
      score 2.54 against mean target 3.61 and 121 of 144 targets at level 4 - it
      under-predicts the top of the scale. laya has the same failure (31/144, 2.25). On
      helpsteer2 and summeval-relevance lev is the best of the three new models. laya is
      best of all five on civil_comments 0.937 and vitaminc-dev 0.790 yet last overall
      (aegis2 0.436, massive-de-DE 0.400).
  - Strata ledger DONE on the 64 GB platform, two roots, and it changes the conclusion.
    `strata-20261007-v1` (budget 4 -> 24 GiB, ledger wall 720 -> 3600 s, session margin 1800 s;
    the two declared changes, engine config snapshotted before the rewrite) scored 7/70 in
    79 s: exit 0, clean_finish false, 3,617 tokens, empty final message after 3 turns, passing
    cases {2,16,17,21,33,48,62} - the identical set the 32 GB run produced. The byte-identical
    repeat `strata-20261007-v2` scored **70/70, clean and correct**, 289.5 s, 14,171 tokens.
    CORRECTION: the 2026-10-06 "ledger 7/70 is wall-bound" note was wrong twice - run 1 stops
    by itself in 79 s (the 720 s wall was cutting a still-generating session, exit 143), and
    run 2 finishes the whole task in 289.5 s. The real property is non-reproducibility: same
    declaration, 7/70 or 70/70, 1 of 2 runs clean, exactly the MiniCPM-style lesson. Strata
    screens must be reported as a rate over runs.
  - Upgrade effect measured: engine load 16.4 s -> 35.4-36.4 s (bigger resident copy to read),
    decode 6.5-9.6 -> ~46-49 tok/s, so 5-7x faster and the ledger now completes inside its
    wall. Cost: budget 24 is NOT free RAM - min free physical 4.33-5.10 GiB (floor 3), min
    commit 22.05-22.37 GiB (floor 2), min GPU free 0.79-0.87 GiB (floor 0.5), peak hard
    page-ins ~460k/s during load. No guard trip, no STOP, monitor_errors [] in all runs, but
    the margin is thin: a longer task, larger context or heavier KV should start at budget
    16-20 and measure. The earlier "leaves roughly 35 GiB free" expectation is corrected in
    the root README.
  - Gemma 4 26B-A4B DONE, first time it has ever run here. `candidates-20261007-v1` (10.0 GB
    UD-IQ2_M hardlinked, inherited manifest, declared -ngl 24) ran clean through parser, host
    smoke and all three tasks, but produced UNSCORED ZEROS: every task returned
    `abnormal_evaluator_exit 2`. RUNNER TRAP, worth remembering: the candidates runner copies
    the audited relay to `<root>/source/relay_<model>.py` and the relay's `score_artifact`
    executes `source/staged_tasks_20260922.py` from that same directory, so a new root MUST
    carry that module and its siblings; the frozen `manifest.json` cannot catch the omission
    because the relay is generated at run time. Earlier roots had them by luck of copying.
    Re-scoring the preserved artifacts with the same frozen scorer gave events 76/76,
    ledger 66/70, paths 75/75.
  - Re-run with the fix in `candidates-20261007-v2` (the fix: `coding()` now copies the five
    sibling modules next to the relay) is runner-scored: parser and host smoke passed, events
    75/76 (553.8 s, case 15), ledger 69/70 (673.3 s, wall-cut, exit 143, case 19), then the
    sweep aborted on `Quota accounting stop: quota_unknown` because the wall-cut session
    reported no usage - the same accepted outcome the Swift Bonsai run recorded, so `paths`
    did not run under the fixed runner. Envelope: min free physical 28.50-30.95 GiB vs
    2.65-2.94 GiB in v6/v7/v8, min GPU free 1.84 GiB, min commit 39.75 GiB; audit verified 120
    protected files. Across the two runs: events 75-76/76, ledger 66-69/70, paths 75/75, never
    a clean three-task sweep, and the two runs differ in duration and clean-finish just like
    the Strata ledger pair.

- October 7 RAM INSTALLED AND VERIFIED (read-only checks plus one lock-free frozen
  preflight; no inference, no gate change). The box is now 64 GB DDR5-5600 dual
  channel: DIMM1 SK hynix HMCG88AGBUA084N plus DIMM2 Kingston 9905782-147.A00G
  (the ordered KVR56U46BD8-32, 2Rx8 CL46 non-ECC), both 34359738368 bytes, Speed
  and ConfiguredClockSpeed 5600 on both, no 4800/5200 down-bin. 63.46 GiB visible
  (31.46 before on 32 GB, so the same 0.54 GiB reserved). Dual channel proved by
  bandwidth, not a BIOS read: 16-thread memcpy 71.4 GB/s combined traffic (79.7%
  of the 89.6 GB/s peak, past the 44.8 GB/s single-channel ceiling), 8-thread read
  49.7 GB/s; BIOS "Memory Channel Mode = Dual" was NOT read (no BIOS access from
  Windows). No memory-corrected errors; the two boot WHEA-Logger ID 17 warnings are
  the RTX 5070 PCIe link, identical to the pairs on Oct 2/4/6, and Kernel-Power 41
  / EventLog 6008 records the install-time power removal at 01:51:32. Frozen
  preflight `decisions-20261005-v1/run.py preflight` passed read-only (creates no
  lock; the lock is written inside screen()): physical_available 44.14 GiB vs the
  9 GiB gate, commit headroom 56.89 vs 8, GPU free 10.60 vs 7.5, no listener on
  8080/11434, ollama absent. Platform change 32 -> 64 GB recorded; ALL gates
  unchanged (9/8/7.5 GiB, 3/2/0.5 floors, 6 GiB worker cap), .wslconfig still
  memory=8GB. Full evidence: RAM-VERIFY-2026-10-07.md. Still open: BitLocker status
  never confirmed (no recovery prompt on the post-install boot is evidence it was
  off or suspended), the real-load-test run and mdsched.exe reboot are Kevin's
  call, and the 6 GiB cap plus rate-over-n-runs reporting decisions are untouched.
  Nothing queued was started; the resume order is RAM-INSTALL-2026-10-07.md Part 4.

- October 7 RAM-install handoff and a Strata probe correction (no lab inference;
  a few read-only probe requests to the already-loaded Strata service). Read
  local-llm-lab/RAM-INSTALL-2026-10-07.md before shutting the PC down: it is the
  pre-shutdown checklist, the install steps, the post-boot verification and the
  resume queue. Live state: 32 GB still (DIMM1 only), no RUNNING.lock anywhere,
  no benchmark running, and no startup entry for Strata or llama.cpp (only
  Ollama), so the detached Strata service dies with the machine and nothing
  relaunches it. BitLocker still undetermined without elevation: check it before
  opening the case. CORRECTION: the Strata endpoint DOES honour per-request
  sampling - an earlier probe compared `choices[0].message.content` alone, but
  this reasoning model puts every token in `reasoning_content` at low
  max_tokens, so all cases compared the empty string; re-probing the trace gives
  6/6 distinct outputs. See staged-strata-20261005/SAMPLING-PROBE-NOTES.md. Two
  behaviours recorded: temperature 0 is not seed-stable on this engine, and a
  trivial prompt at 200 tokens still ends `finish_reason=length` with no visible
  content. Runner fix: decisions-20261005-v1 preflight now refuses to start while
  another engine is resident (it correctly caught strata.exe and listen:8080).
  Delta since Oct 5: llama.cpp b11461 (our staged build is b11429), Strata
  v0.1.40 / v0.1.40.1 (Windows RAM-budget and large-page-arena fixes; NVIDIA
  decode within about 3% of 0.1.39, so it does not fix the disk-bound ledger),
  OpenAI's hosted Decisions API with `llm-openai-decisions`, Ollaya, vLLM's
  2026-10-05 serving release, Kolibri-1 (78.1B MoE, Apache-2.0). Pending Kevin's
  decisions: the 6 GiB worker-private cap that blocked nimble, and reporting
  screens as a rate over n runs. No gate changed, no promotion.

- October 6 tooling: agent-skills adopted for dev/UX work, no inference. Read
  local-llm-lab/AGENT-SKILLS-2026-10-06.md. Vendored addyosmani/agent-skills
  (MIT, 25 skills) at commit 1401c8b8 under C:/Users/kevin/.omp/vendor, plus a
  lab-authored skill C:/Users/kevin/.omp/skills/lab-evidence-discipline; both
  registered via skills.customDirectories, 31 skills discovered. Measured
  screens are UNAFFECTED: mimo-harness already launches the harness with
  --no-extensions --no-skills from its own pinned omp.exe (v18.3.1), so no
  frozen evidence is invalidated. The PATH omp is a different binary (18.6.1);
  never quote one version for the other. Outstanding proposal, needs a decision
  and a new root: report scored screens as a rate over n runs against an
  explicit floor instead of a single run.

- October 5 news scan plus decision-track staging (no inference). Read
  local-llm-lab/NEWS-2026-10-05.md and STAGING-2026-10-05.md. Decision models
  reached mainline: llama.cpp v0.6.0 (build b11429) and Ollama 0.35.0 both serve
  the TypeSafe/Jev /v1/systemone API, and ggml-org publishes GGUFs (julia-1, laya,
  kev 0.8B/4B/9B, lev, nimble, clef, openjev). Staged and sha256-verified:
  llama.cpp b11429 Windows CUDA 13.4 runtime plus julia-1, laya, kev0 (Q8_0) and
  kev4, lev, nimble (Q4_K_M) under ai_bench/staged-decisions-20261005. New runner
  root ai_bench/decisions-20261005-v1 reuses the frozen 18-window inputs/labels
  and the 0.85 threshold / 3 s warm-p95 gate; offline mock self-test passed 18/18,
  4/4 stalls caught, 0 false alarms. Strata engine re-pinned v0.1.27 -> v0.1.39
  (api now OpenAI + Anthropic + Responses). No model loaded, no scored run, no
  app closed, gates unchanged: still HOLDING for the RAM module. Deferred (needs
  app closure): live screens, because the decision preflight fails at 6.73 GiB
  free vs the 9 GiB gate. Plan once RAM frees: run.py preflight, then screen
  julia-1, kev4, nimble one at a time, then audit, then evaluate the best on
  Bespoke's published 3,880-decision suite. Do not run inference before that.

- October 5 live decision screen ran (root ai_bench/decisions-20261005-v2; read its
  REPORT.md and RESUME.md). Gates were already satisfied at session start (12.72 GiB
  free physical vs the 9 GiB gate, commit 23.41 GiB, GPU free 9.91 GiB), so no app was
  closed and no reboot was used. julia-1: 11/18, 1/4 stalls caught, 4/14 false alarms,
  warm p95 638 ms, latency gate PASS. kev4 at `-np 1 -b 512 -ub 512`: 14/18, 0/4 caught,
  0/14 false alarms, warm p95 430 ms, PASS; it never crosses 0.85 (p 0.344-0.546).
  nimble is resource-stopped by the frozen 6 GiB worker-private cap: its floor is
  6.94 GiB at the minimum batch and `--no-warmup` does not move it, while every system
  floor passes (7.20 GiB free RAM vs 3, commit 17.38 GiB vs 2, GPU free 4.11 GiB vs
  0.5). The decision/embedding path needs an explicit batch (the default 512 rejects
  every frozen window) and the `state` encoding is a declared variable. v1 is preserved
  because its first live run died on two runner bugs. No gate changed, no promotion.
  Pending Kevin's decision: keep 6 GiB and end the track, or amend the cap for the GPU
  decision-server track in a NEW root and then screen nimble plus the Bespoke suite.

- October 6 published decision suite (Bespoke, 3,880 human-labelled records, 13 subsets) run
  through llama.cpp /v1/systemone. Read ai_bench/bespoke-suite-20261005-v1/REPORT.md. The
  subsets were rebuilt locally and every rebuilt payload reproduces the committed
  dataset_sha256 and id list byte-for-byte (13/13). kev4 (4B Q4_K_M) macro 74.4 / micro 75.3,
  wall 368 s; nimble (Bespoke-Nimble-9B-v3 Q4_K_M) macro 75.7 / micro 77.1, wall 622 s.
  Published references: nimble-9B BF16 74.8 / 75.9, Jev 1.13.0 76.0 / 77.3, so the local GGUF
  nimble matches the published BF16 run and is at Jev parity, and the 4B model is 1.2 macro
  points behind. Our serving path is not the repo's PyTorch scorer, so per-subset comparisons
  against the published table are indicative (civil_comments +20 points, unexplained). Score
  is the weak primitive for both models. Strata: engine re-pinned to v0.1.39 (main == tag
  6f32ec07), installed from the staged Coder pack and RUN. Read ai_bench/strata-20261005-v1/
  REPORT.md and FLAGS.md. Flags were chosen from the pinned tree plus the two recent videos
  that have captions (`--family coder --model IQ1_M --context 32768 --vision no --low-ram on
  --kv int8 --draft-vocab en`, then `--calibrate`: 19.5 -> 22.5 tok/s measured). The blocker
  was the low-RAM variant, not the engine: `--resident-experts`, plain `--mmap-experts` and
  `--resident-budget-gib 20` each drove free physical to 1.92-2.77 GiB against the 3 GiB floor,
  and a verified minimal-startup reboot (free 15.14 -> 18.19 GiB, GPU used 1313 -> 721 MiB) was
  absorbed by the engine's file cache. `--resident-budget-gib 4` + `STRATA_LOOKAHEAD=0` holds
  9.6-10.5 GiB free; no floor or metric changed. OMP screens at the usual 720 s wall: events
  76/76 correct, paths 75/75 correct, ledger 7/70 wall-bound (decode 6.5-9.6 tok/s on a 12 GB
  card, prompts ~9.4-10.4K tokens read at ~550-670 tok/s). `quota_unknown` on every run. The
  minimal-startup suppression was restored the same day (2026-10-06 13:13 UTC, state
  `restored`, verified, zero failures, startup shortcuts and Run values back).

- September 30 RAM upgrade decision and purchase (module ordered, not
  installed). Read C:/Users/kevin/local-llm-lab/RAM-UPGRADE-2026-09-30.md.
  The blocking constraint was confirmed as host RAM, not VRAM: Gemma 4 26B-A4B
  UD-IQ2_M at 32k bottomed 2.65-2.94 GiB against the 3 GiB floor in v6/v7/v8
  (about 14.5 GiB resident); MiMo larger-output ledger stopped at the RAM guard
  2.94 GiB; Strata original builds need about 26.6-43.8 GiB host RAM. Decision:
  upgrade rather than replace (used parity replacement is about $1,220-1,420,
  and 128 GB is $1,464 used / $1,400-1,900 new against a $1,000 budget).
  Ordered a used Kingston KVR56U46BD8-32, 32 GB (1 x 32 GB) DDR5-5600 2Rx8
  CL46 non-ECC UDIMM, eBay item 800722063307, $379.99 free shipping, returns
  through 2026-11-04. Correct spec for this board: DDR5 UDIMM non-ECC only,
  2 slots, DIMM2 empty, firmware max 64 GB. Install into DIMM2 for
  dual channel (about 44.8 to about 89.6 GB/s); verify two 32 GB modules at
  5600, 64 GB visible, BIOS Memory Channel Mode = Dual, and watch for a
  4800/5200 down-bin. Check/suspend BitLocker before opening the case. After
  install: record the 32 -> 64 GB platform change, keep ALL gates unchanged
  (9/8/7.5 GiB initial, 3/2/0.5 GiB floors, 6 GiB worker cap), keep
  .wslconfig memory=8GB, preserve the RAM-guard-stopped evidence as
  constrained-platform evidence, and use a NEW root for any re-run. No
  inference was run during the RAM research session.

- September 30 Strata engine reviewed and staged, nothing installed or run. Read
  C:/Users/kevin/local-llm-lab/STRATA-REVIEW-2026-09-30.md and
  C:/Users/kevin/ai_bench/queue-20260930-strata/. The engine (github.com/Niko1221/Strata,
  MIT, cloned at commit a79080535d1b2a71a3419a0d97d8e7dca194b0f1) serves
  Qwen3.8-Flash-Next by splitting it across GPU, RAM and SSD. Its thesis that the
  12 GB card is not the limit but system RAM is matches our own Gemma 4 26B-A4B
  measurement in candidates-20260929-v8. Original builds need 37-55 GB resident
  and stay out of reach here; the Coder pack (ISTA-DASLab GSQ-RCO IQ1_M, revision
  5348543e0147355ac9cbcb031184a3546350988e, per-file sha256 in staged.json) is
  documented to run on 32 GB with low-RAM mode mapping experts from disk, which
  revises the Strata exclusion previously recorded in BONSAI-REVIEW.md (dated
  UPDATE added there). Two things to remember: on a 12 GB card low-RAM mode is
  disk-bound so the open question is correctness and start-up, not speed; and
  Strata is an external server, so a new runner revision is needed that skips the
  llama-server launch and points the relay at its endpoint. The video behind this
  ("6x Faster Than llama.cpp") is marketing arithmetic: its 6x compares
  llama.cpp's 15 t/s on one build against 93 t/s on the fastest build, while the
  engine's own table puts the comparable 3-bit build at 53-62 t/s.

- September 30 12 GB addendum ran with no reboot. Read
  C:/Users/kevin/ai_bench/candidates-20260929-v8/REPORT.md. Swift Bonsai 2 PQ2
  (sha256 5912bb73...d5633d5) on the Prism runtime prism-b10743-adfffbe
  (win x64 cuda 13.3, zip sha256 c4f937e2...24c7bb plus the cudart bundle):
  events 76/76 clean and correct, ledger 70/70 correct but the run stopped on
  quota_unknown, which Budget.account sets when a response carries no
  completion_tokens, an engine usage-reporting gap rather than a model problem;
  paths therefore did not run. Best local result in the series so far.
  Gemma 4 26B-A4B UD-IQ2_M (sha256 3fe245f4...6b3c3a) was resource-stopped three
  times: v6 at -ngl 27 (22 s, events 2/76), v7 at -ngl 24 (104 s, 75/76), v8 at
  -ngl 24 with WSL down and stale sessions ended (235 s, 75/76). Deeper offload
  fixed VRAM (free 0.96 -> 1.92 GiB against a 1 GiB floor) but host RAM bottoms at
  about 2.7 GiB against a 3 GiB floor because the model consumes about 14.5 GiB
  regardless of offload. Non-reboot levers are exhausted for it: tray GPU apps
  closed, WSL shut down, two completed harness sessions ended, deeper offload. It
  needs the deferred minimal boot or a smaller declared configuration.
  Traps worth remembering: a resource stop leaves STOP in the root and blocks any
  further run there, and a failed attempt leaves source/relay_<model>.py that the
  next attempt asserts absent.

- September 30 follow-up roots v4 and v5. Read
  C:/Users/kevin/ai_bench/candidates-20260929-v5/REPORT.md. Caps were decided
  from measurement: decision input cap 2048 -> 4096 (gliner tokenizer needs 2555,
  2637 with schema; julia 1835; jeff 1951, so jeff/julia results are unaffected)
  and session output quota 16000 -> 24000. gliner then got a real verdict: 18/18
  windows, 0/4 stalls caught, 0/14 false alarms, p95 27.56 s, which fails the 3 s
  latency gate. The v4 quota change was INERT because mimo-harness constructs
  base.Budget(quota=16000, cap=12288) explicitly; v5 overrides the constructor and
  proves it (ledger used 17953 tokens, no quota stop). v5 added ling: Ling-3.0-tiny
  Q6_K, 6839076160 bytes, sha256 cb58a01e...73fc9b8 matching the pinned revision's
  LFS oid; bailingmoe3 loads in stock llama.cpp b10883; parser and host controls
  pass; events 2/76, ledger 29/70, paths 9/75; no promotion.
  Critical methodology note: MiniCPM5-2B paths scored 75/75, 75/75, 9/75 across
  v3, v4 and v5 under identical declared model, quant, context, wall and seed, and
  model selection is confirmed by the pinned enabledModels entry. The agent path is
  not reproducible run to run, so single-run scores on this harness are NOT point
  estimates and repeat runs are required before drawing model conclusions.
  Not started: the Gemma 4 26B-A4B item (needs the turboquant fork build) and
  Swift Bonsai 2 PQ2 (needs Prism b10743).

- September 29-30 candidate screen COMPLETE. Read
  C:/Users/kevin/ai_bench/candidates-20260929-v3/REPORT.md. Decision models, 18
  archived windows, frozen 0.85 threshold, 3 s warm p95 gate: jeff 18/18 but
  p95 6.27 s (FAIL), 0/4 stalls caught, 0/14 false alarms; julia 18/18, p95
  0.82 s (PASS) but 0/4 caught with 3/14 false alarms; gliner no verdict, its
  tokenizer exceeded the frozen 2048-token cap on natural-4 (2443 tokens).
  Coding, external scorer, 32k context, 720 s wall: MiniCPM5-2B Q8 events 76/76
  (quota_exhausted, not clean), ledger 67/70 clean, paths 75/75 clean, so 1/3
  correct-and-clean; Spark-X2.5-4B 2/76, 7/70, 9/75, 0/3. Both passed
  parser_passed and host_passed, and inputs_unchanged held for all runs. No
  promotion and no threshold tuning.
  Roots: v1 stopped on the resource guard (vmmemWSL held 8.31 GiB; worker peak
  4.81 GiB, under its 6 GiB cap); v2 ran the decision items and produced INVALID
  coding zeros because the root lacked source/staged_tasks_20260922.py, so the
  scorer never ran (unscored, not failed); v3 is the corrected root that graded
  the coding items. Fix applied outside the roots: .wslconfig memory=8GB, backup
  at ai_bench/wsl-cap-20260929/. No gate was lowered. Audit passed: 120 protected
  files, no run lock, no resident model. Rule consolidation: 25 to 25, 137
  prefixes, 142 checks, exact equivalence, nothing installed.

- September 29 12 GB model research note: read RESEARCH-2026-09-29.md.
  Covers Ling-3.0-tiny (fits, mainline bailingmoe3 support), Gemma 4 26B-A4B
  at UD-IQ2_M with turbo3 KV from a fork (engine experiment), Swift Bonsai 2
  PQ2 on the changed Prism runtime, and the arithmetic showing
  Qwen3.8-Flash-Next and Qwen3.8-27B Q4 do not fit 12 GB. A three-item staged
  addendum with pinned revisions is at ai_bench/queue-20260929-v2
  (staged.json, RESUME.md): staged, not run, nothing downloaded. The v1
  candidate queue at candidates-20260929-v1 keeps priority and remains
  frozen and awaiting ready plus a passing preflight.

- September 29 regular OMP installed on user PATH at ~/.local/bin/omp.exe,
  official 18.3.1. Default native deepseek/deepseek-flash, high thinking,
  existing persistent key; normal full harness. Global OMP AGENTS points to
  C:/Users/kevin/ai_bench/CONTINUE-HERE.md, the current lab handoff index.
  Fresh hosted smoke verified automatic notes, native model, read and approved
  nvidia-smi, clean Windows Job cleanup. 57 compatible prior approvals mapped
  to 114 Bash patterns, 127 matching checks passed. Historical complex
  PowerShell entries retained in migration audit, not broadened. Setup records
  under ai_bench/omp-setup-20260929. Candidate testing remains pending ready.

- September 29 candidate screen prepared, inference pending available RAM.
  Read C:/Users/kevin/ai_bench/candidates-20260929-v1/RESUME.md and
  BONSAI-REVIEW.md. Official Bonsai PQ2 unchanged; runtime and Swift changed.
  Jeff v1.1, Julia, GLiNER, MiniCPM5 Q8 and Spark Q8 pinned/downloaded;
  isolated dependencies and monitored runner ready, 120 files frozen.
  Preflight stopped at 7.26/7.35 GiB available RAM below original 9 GiB gate.
  User will close unused apps and reply ready; wait for that message, then
  recheck resources and proceed serially. No inference, apps closed, reboot
  or startup changes. No second agent or relaxed resource guards.

- September 28-29 MiMo larger-output/context retest finished. Read
  C:/Users/kevin/ai_bench/mimo-output-20260928-v1/SUMMARY.md. User authorized
  49,152 response/64,000 session tokens, with declared context increase to
  65,536; wall 720s unchanged. Ledger/Pi 0.87.1: 68/70, 699.1s, RAM guard
  at 2.94 GiB, >=52,890 tokens. Paths/Pi 0.86.1: 9/75, 628.1s, response cap,
  repeated reasoning sentence 3,043 times, starter unchanged. Neither clean.
  v1 stopped and preserved; v2 ran only unstarted paths after RAM recovered
  and unchanged preflight passed. Events not repeated. 40 protected hashes
  and 18 absent owned identities verified; models/ports/locks cleaned up.
  No reboot/startup changes/apps closed. No promotion or causal output-only
  claim. Next option: controlled reasoning/repetition handling, not more
  output alone. Rules 28 to 25, 132 prefixes, 137 checks, exact-equivalent.
  The timeout-only follow-up below is historical and has now been executed.

- September 28 local MiMo timeout-only retest completed and cleaned up. Read
  C:/Users/kevin/ai_bench/mimo-timeout-20260928-v1/REPORT.md. Wall 180 to 720s;
  same model/runtime/template/harnesses, 12,288 per-response and 16,000 session
  output caps. Pi 0.87.1 ledger 7/70, reasoning hit response cap at 146.1s;
  Pi 0.86.1 paths 75/75, session quota at 195.6s; OMP events 76/76 clean at
  110.9s. 1/3 correct-and-clean, 2/3 correct artifacts, zero 720s timeouts.
  Events finished below old deadline, so no causal timeout benefit established.
  35 hashes/configuration equality and 24 owned process identities verified;
  models unloaded, ports/locks cleared. No apps closed/reboot/startup changes.
  Next option is separately controlled output-cap increase; not run/authorized
  by the timeout-only request. Preserve all original and new evidence.

- September 28 hosted DeepSeek V4.1 Flash screen completed with OMP 18.3.1.
  Read C:/Users/kevin/ai_bench/deepseek-flash-20260928-v1/REPORT.md.
  Events 76/76 in 50.9s; corrected ledger 70/70 in 50.1s; paths 75/75 in
  33.1s, all three clean. Four coding sessions actually ran: original ledger
  also passed 70/70 but the shared request-byte cap interrupted finalization.
  v2 gives ledger/paths independent byte caps; originals preserved, no pooling.
  Hosted deepseek-flash identified by authenticated catalog as V4.1 Flash;
  explicit high thinking and exact reasoning roundtrip verified. Not a local
  placement or model-only comparison. 33 protected hashes, five cleanups and
  22 sampled process identities verified. No apps closed or models loaded.
  Rules consolidated 29 to 25, 128 prefixes preserved, 133 checks passed.

- September 28 new-harness screen complete: read
  C:/Users/kevin/ai_bench/new-harnesses-20260928-v1/REPORT.md.
  Six serial MiMo Q4 sessions; Goose 1.52.0 correct-and-clean 1/3
  (events 76/76, 42.1s), mini-SWE-agent 2.4.6 0/3. Isolated installs,
  explicit server reasoning on, unchanged resource gates, no promotion.
  v1 stopped after a known deadline cutoff; v2 ran only five unstarted
  sessions. Missing final usage remains a lower-bound token count.
  All protected inputs/frozen source snapshots and cleanup verified;
  no models/locks remain, no reboot/startup changes. Next: fresh-task
  server-thinking control, and separately mini's native text-command mode.
  Prior September 26 Pi/OMP labels do NOT establish an on/off comparison;
  read mimo-overnight-20260926-v1/THINKING-AUDIT.md under ai_bench.
  Approval rules consolidated 39 to 25 with 129 checks, exact-equivalent.

- September 25 Pi loop logger completed: read
  PI-LOOP-LOGGER-RESULTS-2026-09-25.md and
  C:/Users/kevin/ai_bench/pi-loop-logger-20260925-v1/REPORT.md.
  Opt-in, no judge calls/interventions, never installed globally. Nine checks
  and native Pi preservation of 18 calls/results passed. Three fresh serial
  coding sessions, 95 calls; labels frozen before reading flags. Exact-match
  rule missed one semantic loop (40 calls; 7 uncertain excluded), with one
  false alarm among 48 negative calls. Mean instrumented handler 0.050ms.
  Live categories exactly match replay. Events passed correctness; ledger
  timed out; paths finished but failed external correctness. v1 preflight
  stopped on a transient server before second inference; preserved evidence.
  v2 continuation ran only unstarted events/paths with unchanged observer and
  bounded settle wait. All 100 sampled owned identities absent; port/locks
  cleared, memory gates held, no reboot/startup changes. No promotion.
  Next candidate: operation similarity and progress tracking, with fresh
  validation; do not tune on these labels and claim independent validation.

- September 25 local decision follow-up completed: read
  LOCAL-DECISION-FOLLOWUP-2026-09-25.md and
  C:/Users/kevin/ai_bench/local-decisions-followup-20260925-v1/REPORT.md.
  Stuck-only OpenJev preserves all 46 synthetic probabilities exactly;
  paired median 4.04s to 3.03s, warm p95 3.34s fails the fixed 3s gate.
  On 18 real archived windows (single-reviewer labels frozen before scoring),
  OpenJev at 0.85 catches 0/4 stalls, false alarms 0/14; median 11.26s.
  Deterministic identical-failure/no-successful-mutation rule catches 1/4,
  false alarms 0/14; six checks pass. Successful-output loops outside scope.
  Compact representation and correlated small sample limit interpretation.
  Neither installed or promoted. All models unloaded, ten owned identities
  absent, port and lock cleared; gates unchanged. No reboot/startup changes.
  Next: cheap observation-only logging and independently labeled new sessions;
  do not tune on these evaluation labels and call the result validation.

- September 25 local decision trial completed: read
  LOCAL-DECISION-RESULTS-2026-09-25.md and
  C:/Users/kevin/ai_bench/local-decisions-20260925-v1/REPORT.md.
  CPU float32, four threads; 46 synthetic cases per model (6 diagnostic,
  20 development, 20 evaluation). Laya multilingual: unusably high stuck
  probabilities, disabled threshold, evaluation 10/20. OpenJev 0.8B v5:
  threshold 0.85, evaluation 18/20 with no false alarms but two missed
  failing-test loops; original diagnostic only 4/6. Median latency 4.15s
  exceeds the 3s gate. Neither promoted; no coding-model session was run.
  Audit fixed Windows venv launcher-only memory measurement to the full
  owned process tree; originals preserved, all cases replayed as monitored-v2.
  Peak private memory 2.38/4.52 GiB. All 92 replay probabilities exactly
  match originals; 184 requests total are not 184 independent cases.
  Laya tokenizer config migration verified against pinned upstream file.
  Hashes, 30 owned process identities absent, lock removal, and port closure
  verified. Native Pi test preserves nine calls/results; local hook opt-in,
  never globally installed. No reboot, startup changes, or relaxed gates.
  Next: separate OpenJev stuck-only latency control and fresh natural traces;
  do not retune on these evaluation labels and call it independent validation.

- September 24 key-free Jev alternatives researched: read
  JEV-LOCAL-ALTERNATIVES-2026-09-24.md. Seven ungated model repositories and
  four GitHub identities pinned; 23 code/config/report files archived in
  ai_bench/jev-research-20260924/alternatives. No installs, weights, or inference.
  Recommend isolated CPU Laya first, then AlexWortega OpenJev 0.8B comparison.
  Laya HTTP does not forward max_len; avoid silent history truncation and
  all-checkpoint preloading. NanoJev serving requires CUDA and stores FP32
  parameters even under bf16 autocast. OpenJudgement requires its wrapper
  and /v1/judgments; 8.455 GiB stored weights. OpenJev names are ambiguous.
  Existing hosted observer remains unchanged; local provider adapter is not
  implemented. Keep resource gates and serial inference; no reboot.

- September 24 Jev observer prepared and verified: read
  JEV-OBSERVER-RESULTS-2026-09-24.md. Isolated adapter at
  C:/Users/kevin/ai_bench/jev-pi-observer-20260924-v1 targets Pi 0.86.1,
  pins jev-1.13.0, logs only, defaults to network disabled. Eleven offline
  checks and native Pi loader/event smoke passed with mocked transport.
  Live six-case synthetic replay is pending TYPESAFE_API_KEY availability;
  actual Windows process/user environments were checked and had no key.
  No global installation, live API call, local inference, or reboot occurred.
  Use run.ps1's bounded actions; keep serial inference and A3B memory gates.

- September 24 deeper Jev compatibility review: read
  JEV-HARNESS-COMPATIBILITY-2026-09-24.md. Verified Windows Claude 2.1.266,
  OpenCode 1.17.15, Codex CLI 0.156.1 (hooks stable true; plugin_hooks removed).
  pi-local still selects 0.85.1; 0.86.1 is separate. Some Jev extensions ignore
  PI_CODING_AGENT_DIR. MoonTory/pi-jev-harness has loop-only logging mode, but
  needs isolated config/log paths and model pinning before our proposed trial.
  Claude replacement compaction targets gated function hooks at 2.1.274/278;
  OpenCode compactor validated against 2.0.7. No installations or inference.

- September 24 Jev research completed: JEV-RESEARCH-2026-09-24.md covers
  13 repositories and transcript material from nine videos. Eight repos pinned;
  15 implementation/package/report files inspected, no extensions installed or
  API/inference calls. Prefer evaluating a small existing Pi decision adapter
  on labeled replays before automatic routing or pruning. Static findings:
  iefnaf router colon parsing conflicts with Ollama model tags; jev-code score
  description exceeds current API limits. Latest Codex compaction audit proves
  integration, not efficacy. Preserve serial inference and memory guards.

- September 24 post-reboot stock A3B screen finished. Read
  C:/Users/kevin/ai_bench/a3b-offload-20260924-v1/REPORT.md and status.json.
  Six configurations completed; two loads stopped at unchanged memory guards;
  210 stored-evidence checks passed. No model server or benchmark lock remains.
  Baseline candidate: Qwen3-Coder, 32 CPU expert layers, 8 threads, context 8192,
  --load-mode none: 33.90/32.72 tok/s short/long raw continuation. This is not
  coding-quality validation or dynamic expert caching. All-CPU-experts loading
  stopped on the sustained paging guard. More threads gave mixed differences.
  Startup restoration succeeded on the authorized retry at 22:23 UTC. The
  administrator audit passed with no failures; see minimal-boot/boot-status.json
  and restore-verification.json. Original startup backup is preserved.
  No additional reboot occurred; do not reboot again or launch concurrent inference.
  Latest rule consolidation: 28 to 24, exact-equivalent, 114 checks passed.
  The following September 24 pre-reboot notes are historical, not live state.

- September 24 reboot continuation: user authorized a reversible minimal-startup
  reboot and automatic continuation of A3B work, plus exact-equivalent approval
  consolidation. FIRST read C:/Users/kevin/ai_bench/a3b-offload-20260924-v1/
  minimal-boot/RESUME.md and boot-status.json. One-time logon helper resumes
  session 01a0d0bf-e99f-70d3-aa5f-bc57f9bf7271 interactively. Do not reboot again.
  Restore temporary startup settings after the experiment session. Ollama
  autostart is suppressed, so verify process absence before adapting preflight
  to an unavailable Ollama endpoint. No inference has run yet. Use fixed helper
  script approval prefixes; do not accumulate arbitrary PowerShell payloads.
  Full setup applied: 17 services, 23 tasks, 13 Run values, 2 shortcuts and
  2 packaged app startups suppressed. Protected CoworkVMService is preserved.
  Inspect boot-status.json and verification.json for completion. No reboot is
  allowed until state is applied and verification has no failures. A one-time
  post-logon terminal continuation is registered; original settings are backed up.
  Core and accessible startup verification passed; 5 administrator-only optional
  task states are explicitly unverified after a canceled elevated read check.
  Administrator Apply had disabled them successfully. Restart guard validated;
  check reboot-requested.txt and actual LastBootUpTime before any further action.
  Approval consolidation IS installed: 37 rules to 24, 111 checks passed.

- September 24 current task: A3B-family expert-offloading research and resource
  preflight. New scope: A3B-OFFLOAD-RESEARCH-2026-09-24.md,
  A3B-OFFLOAD-PLAN-2026-09-24.md, benchmarks/a3b_preflight_20260924.py,
  and ai_bench/a3b-offload-20260924-v1. User authorized normal closure of unused
  applications for RAM headroom; preserve the active assistant and unsaved work.
  GoProverbs 10-feature weight sweep is authorized but queued after this work.
  Do not start a competing inference workload; inspect the new status first.
  Research/plan saved; isolated b10883 CUDA 13.3 installed with official archive
  SHA256 checks and RTX 5070 detection. Preflight-03: 4.80 GiB free physical,
  11.38 GiB commit, 9.75 GiB VRAM; no eligible placement and no inference run.
  Preferred 36-layer CPU expert placement needs about 16.17 GiB free RAM/commit
  and 8.37 GiB VRAM. Normal app closure found no eligible windows. Three
  resource/parser regression tests pass. Current qwen3:30b-a3b is Thinking-2507.

- September23 small-search verification completed. Read
  goproverbs/docs/NEURAL-VERIFY-RESULTS-2026-09-23.md.4/8/16 visits fit timing;
  16 selected.40 development cases had positive pooled reference gains, but the
  combined role failed its fixed nonnegative512-visit criterion. Validation40
  cases remain unqueried; no fresh games or default change.98 tests pass; hashes,
  gates and cleanup verified. No inference active. Do not tune this failed
  treatment or reclassify its neural-only subgroup as validated.

- September23 disagreement review completed79 cases at128/512 visits. Read
  goproverbs/docs/NEURAL-LED-DISAGREEMENT-RESULTS-2026-09-23.md. The fixed
  policy-protection candidate failed its development/validation gates; playing
  controller unchanged, no fresh matches launched.89 tests pass. All inference
  cleaned up. Do not tune thresholds on these labels and claim validation.

- User preference: after generating user-facing files, open them in their
  default Windows application using the file association. Do this as part of
  delivery rather than only providing a link. Applies to Markdown reports too.
  2026-09-29: .md/.markdown open in the native Markdown Viewer
  (winget id 0x4D44.mdmdview 1.16.0, Rust plus egui, one process, about 160 MiB)
  rather than an editor or a browser; Electron-based mdview was rejected as a
  second Chromium. Fallback is ai_bench/md-to-html.py plus the default browser;
  -Viewer association restores the Windows file association.
  Use the approved document-only helper for new files:
  `powershell.exe -NoProfile -File C:\Users\kevin\ai_bench\Open-Document.ps1 -FilePath C:\absolute\path\report.md`.
  Invoke this command directly, without an additional PowerShell command wrapper.
  Do not use raw Start-Process for new document paths: its approvals only cover
  specific historical targets. The helper validates document types and rejects
  executables/scripts. If it rejects a target, inspect the reason; do not bypass
  its checks. See ai_bench/codex-rules-cleanup-20260923/REPORT.md under the user home.

- September23 pass-agreement follow-up is complete and cleaned up. Read
  goproverbs/docs/NEURAL-LED-PASS-RESULTS-2026-09-23.md and pass-v1/status.json.
  Rule implemented;85 Python tests,45 live controls and5 endgame replays pass.
  All80 fresh games finished:neural-policy20/40, combined-neural21/40, neither
  establishes superiority. Zero overruns/fallbacks,31 agreements counted
  separately. No inference active; larger confirmation/default promotion held.
  The stopped-screen/pass-rule-proposed notes below are historical.

- September23 neural-led screens are stopped and cleaned up. Read
  goproverbs/docs/NEURAL-LED-SCREEN-RESULTS-2026-09-23.md before more Go inference.
  Neural-policy completed20pairs24/40, inconclusive. Combined timing was fixed
  with full-history-preserving container copies, but revised screen-v3 stopped
  on722-move nontermination after2 complete pairs (2/4). No active run. An endgame
  pass-policy change is proposed but not implemented; don't resume frozen runs
  or count the unfinished game as a loss. All80 Python tests passed.

- September 23 completion comparison is finished and cleaned up: read FOLLOWUP-RESULTS-2026-09-23.md and C:/Users/kevin/ai_bench/completion-20260923-v1/status.json. New prompt: 6/6 correct and clean; baseline 4/6 correct, 1/6 clean. Staged smoke 3/4 clean, so 30-run staging remains held. CPU reruns are prepared at C:/Users/kevin/ai_bench/cpu-headroom-20260923-v1 but held for 14 GiB physical / 10 GiB commit headroom. Check status/locks and live resources before any inference. User is freeing memory. Read both September 23 protocols; preserve frozen source/results. Go gate remains held; 9 Python and 14 focused WSL regressions passed.

- Overnight September 22 follow-up: inspect C:/Users/kevin/ai_bench/overnight-followup-20260922-v3/status.json and RUNNING.lock before any inference. The user authorized a serial, eight-hour queue for a repeat-call guard ablation, conditional guarded staging, and separately labeled 600-second CPU packing controls. Frozen source is under that directory; do not edit it or launch competing models. REPORT.md updates while it runs. A STOP file in that directory requests cancellation. The first preparation failed cleanup validation and was never launched; v2 was stopped and preserved after revealing a scorer/lifecycle bookkeeping bug. The validated replacement v3 separates correctness from cleanup status. Read OVERNIGHT-PLAN-2026-09-22.md for the fixed protocol.

- September 20 experiments: inspect C:/Users/kevin/ai_bench/round-20260920/status.json and RUNNING.lock before starting inference. Read RESULTS-2026-09-20.md for current results and benchmarks/EVALUATOR-V2.md for the new scoring contract. Keep the historical scorer unchanged. The isolated Pi 0.86.1 installation is in ai_bench/pi-lab-0861; pi-lab remains 0.85.1.
- Keep benchmark transcripts, wire captures, process metadata, and harness configuration outside the candidate's working directory. The original September 20 runs shared those files with the candidate; Bonsai's full-task run read them and looped. The isolated follow-up uses agent(isolated=True); preserve the original runs and label the changed workspace treatment separately. This directory layout is not a security boundary.

- Read REVIEW-2026-09-20.md before interpreting historical rankings or selecting new experiments. The archived local cycle failure was an exit-status bug; the Claude 10/10 artifact overwrites existing data during its self-test. Historical scores are preserved, and new evidence is in diagnostics/review-20260920/.

- Read README.md, METHODOLOGY.md, RESULTS.md, and RESEARCH-2026-09-15.md before selecting new experiments.
- Read RESULTS-2026-09-15.md for the latest executed round and Pi configuration corrections. Preserve failed runs and distinguish a CLI exit code from agent or program success.
- Read STREAMING-DIAGNOSIS-2026-09-16.md before interpreting the overnight hard-task zeros. A captured 4k-output request truncated tool JSON; 8k fixed that replay but not every new run. An experimental Omni 32k-context/12k-output profile delivered 115/115 terminal signals but only 2/10 program correctness. Input context and output allowance are separate controls; match compaction reserve to output allowance.
- Overnight follow-up: check C:/Users/kevin/ai_bench/overnight-20260916/status.json and RUNNING.lock before starting inference. The independent overnight runner owns its night-20260916-* aliases. Do not launch competing tests. RESULTS-2026-09-16-OVERNIGHT.md is regenerated as experiments finish; distinguish running records from final results. A STOP file in the overnight directory requests graceful cancellation.
- User preference, 2026-09-15: free VRAM before tests. Inspect nvidia-smi and ollama ps; unload resident models and stop confirmed idle model servers or other identified VRAM hogs before loading a benchmark model. Recheck GPU memory and record the before/after values. Do not indiscriminately kill Python, Node, browsers, the active assistant, Windows shell processes, or applications with unsaved work.
- Run one inference workload at a time. Unload the model after each experiment, including failures. Record context, quantization, server version, placement, and available RAM.
- Include popular Hugging Face variants, CPU-only approaches, and agent-harness comparisons (especially Pi). Downloads and likes indicate interest, not correctness.
- A model server (Ollama/llama.cpp), coding agent (Pi/Aider/OpenCode), and evaluator are separate experimental variables. Hold the others fixed when comparing one.
- Keep scripts and new notes ASCII. Windows and PowerShell are the primary environment.
- User preference, 2026-10-12: **commit and push after each change, in this repo.** Kevin asked for it
  explicitly and asked that it be remembered. Only `C:/Users/kevin/local-llm-lab` is a git repo (remote
  `https://github.com/kevinelong/local-llm-lab.git`, branch `main`, public); `C:/Users/kevin/ai_bench` is
  NOT a repo, so instruments, roots and evidence stay local and are referenced from the notes by path.
  Because the remote is public, before every commit: scan for secrets (API keys, tokens), keep the commit
  to notes and small text, and never add model weights, packs, logs or anything under `ai_bench` - the 37 GB
  Kolibri GGUF and the ~66 GB Strata pack live there and must never be committed. Push with the existing
  credential helper; if a push fails, report it rather than rewriting history.
- Licensing, 2026-10-12: this repository is **FSL-1.1-MIT** (Functional Source License 1.1, MIT future
  licence) - source-available, not OSI open source, converting to MIT two years after each version is
  published. See `LICENSE` and `NOTICE.md`. Two consequences to respect in future edits: **never paste
  third-party code or data into this repo without checking its licence** (the vendor packs keep their own
  terms, and the four Anthropic document skills must not be redistributed), and **never describe this repo as
  open source**. The FSL's only restriction is against a competing commercial product or service; Kevin
  confirmed "FSL" after asking for "the latest FLS licence", and the licensor line reads "Kevin Ernest
  Long" (taken from his existing `score` and `score-dist` licences, not guessed).
  **Scope, decided 2026-10-12:** FSL-1.1-MIT was applied to the repositories that are Kevin's *and* live or
  published - this one, `tek/tek-tube`, `local-llm-lab/goproverbs`, plus the ones that already carried it
  (`micro` = pool-table-streaming, `score`, `score-dist`, `fc`, `fc-app`, `fc-releases`). A full scan then
  found roughly **390** further git repositories under `C:/Users/kevin`, almost all dormant
  `Dropbox/IdeaProjects/*` and `Dropbox/GitHub/*` coursework from 2014-2017, and they are deliberately
  **not** relicensed. Three reasons, not to be re-litigated without Kevin's word: about fifty are copies of
  *other people's* projects (freeCodeCamp, angular.js, rancher, swift-nio, SwiftyJSON, django-model-utils,
  data-science-from-scratch, browserify-handbook, Metro-UI-CSS, Reacteroids, DrapsTV_Materials) whose licences
  are upstream's, and an FSL file there would misattribute authorship; about twenty are Dropbox
  **cloud-only placeholders**, so their contents are not on disk at all (reads fail with os error 1920) and
  would have to be hydrated first; and nearly all have **no git remote**, so a licence there changes nothing
  publicly while adding ~390 commits to dormant work this lab did not create. If Kevin names a subset (for
  example `Dropbox/!PROJECTS/`), do it path-scoped, one commit per repository, and leave dirty working trees
  alone - several of those repos have uncommitted work.
  **Completed the same day, via the GitHub API and without cloning anything** (Kevin asked whether "we can
  use gh to add the license directly to all public repos that we created": gh is not needed, and neither is
  WSL - the credential that `git push` already stores is enough). Audit of every public non-fork repo on the
  account: **262 repos, of which 213 already carried FSL-1.1-MIT** from an earlier pass, **46 had no licence
  file at all, and all 46 were written through the Contents API** (`PUT /repos/{owner}/{repo}/contents/
  LICENSE.md` with the file base64-encoded), reusing the preamble style of the existing 213 and verified
  46/46 to contain the full FSL-1.1-MIT body. **Three were deliberately left alone** because they carry other
  people's licences: `django-registration` (Copyright James Bennett), `mscgen` (GPL), `pdm` (BSD-3-Clause) -
  all three are third-party projects sitting on this account and should probably be archived or deleted
  rather than relicensed. **Caveat for future sessions:** GitHub's licence detection does not know FSL, so a
  repository's sidebar shows no licence even when the file is present - check the file, never the API's
  `license` field, when auditing this.
  **`goproverbs` was published the same day:** found locally at `local-llm-lab/goproverbs` (branch `master`,
  no remote until now, only the licence commit in it) and imported as **1,836 files / 29.9 MB**, pushed to
  <https://github.com/kevinelong/goproverbs>. Excluded and left local: `target/` (461 MB of build output),
  `dist/`, and **`results/**/*.jsonl` - 277 raw wire and per-game traces totalling 2.7 GB**, consistent with
  the lab's rule that captures are not published; the reports, fixtures, SGF records and the frozen
  per-experiment source snapshots under `results/` *are* committed. Check `LICENSE` *and* `LICENSE.md` when
  auditing a repo - `tek-tube` uses the latter and `goproverbs` the former, and guessing wrong twice cost two
  false alarms. Its licence preamble also needed correcting by hand: the first draft described
  "Go/weiqi proverb retrieval with neural verification" when the repository is the **Rust Go player engine**
  (README and Cargo.toml are authoritative) - read the README before writing a preamble.
- Preserve existing work.
