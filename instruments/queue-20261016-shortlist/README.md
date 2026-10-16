# Queue, 2026-10-16: the news scan's shortlist, in order

Declared 2026-10-16 for Kevin's instruction ("proceed with that plan now all in order"), where the plan is
`local-llm-lab/NEWS-2026-10-16.md` §8's ranked shortlist. Predictions are written **before** each run and
scored afterwards, including the ones that turn out wrong - this lab's own rule.

## Rules this queue runs under (unchanged from the 2026-10-11 queue)

- **Serial, one inference workload at a time.** A measured run is in flight until ~21:45 on 2026-10-16 (the
  Colibri knowledge item), and nothing here starts an engine until it stops: two engines on this box at once
  would contaminate both the run's wall time and these measurements. Kevin's standing rule is one workload.
- **The gates are checked, never lowered**: free physical >= 9 GiB and commit headroom >= 8 GiB before each
  item, and a trip **stops** the queue rather than weakening a bar. Nothing is deleted, nothing rebooted, no
  unrelated app killed.
- **No frozen artifact is edited.** New evidence lands in this root.
- **Nothing downloaded without saying so here.** Two items need a download and are marked as such.

## Items, in the scan's order

### 1. Strata: does KV residency change the numbers at fixed capacity? - READY

- **Question:** our Strata launch pins `--kv int8 --max-context 65536 --resident-budget-gib 2`, and the
  engine also exposes `--kv-resident` and `--kv-streaming`. At a fixed capacity, does keeping the KV cache
  resident instead of streaming it change correctness (the letters/answers) or only the rate?
- **Prediction:** correctness does not move (the same letters), the rate does - residency should raise
  decode and lower the time-to-first-token cost that streaming adds. If the letters move, that is a
  determinism finding about this engine and it outranks the speed number.
- **Instrument:** the engine's own cold/warm rates (the pair that settled 0.1.41) plus `ledger` on the frozen
  70-check battery; `knowledge_deep.py --forms reason` for the letter comparison on 93 items.
- **Cost:** one engine start per arm, no download. `--resident-budget-gib 2` stays fixed so capacity is not
  the variable.

### 2. llama.cpp: ladder `--moe-cache-mib` on a build that has it - STAGED AND VERIFIED

- **What is staged:** `ai_bench/staged-llamacpp-b11480/` (win-cuda-13.4-x64 release archives, sha256 in
  `SHA256SUMS.txt`): `llama-server.exe --version` reports `0.6.0-dev (build 11480, commit d6cf9acb2)` - the
  merge commit of PR #29887 - and `--help` lists `--moe-cache-mib N` ("GPU cache size in MiB for the MoE
  experts kept in the CPU"). Control: the pinned b11461 has **no** such flag. This is the A/B pair.
- **Question:** on our own `--cpu-moe` workload (Qwen3.6-35B-A3B Q4_K_M, 12 GB card), what does each rung of
  `--moe-cache-mib` buy, measured rather than assumed?
- **Prediction:** the curve is **non-monotonic** and peaks in the low thousands of MiB - a small cache
  recovers the experts that repeat between tokens, while a large one competes with the dense weights for the
  2 GiB `--vram-reserve-mib` region and regresses. Concretely: 0 -> ~35-40 tok/s decode, a rung in
  256-2048 MiB -> the best, and the top rung at or below the 0 rung.
- **Instrument:** `ledger` + `ledger2` for scoring (the caches change numerics by construction, so a speed
  number alone is not a result) and the engine's own decode rate for the shape of the curve.
- **Ladder:** 0 (control), 256, 512, 1024, 2048, 4096 MiB - ascending, stopping early if two rungs regress.

### 3. A per-workload noise floor before trusting any tune - DESIGNED, runs with item 2

- **Question:** how much do two *identical* runs of this workload differ? The scan found a tool whose own
  `--calibrate` made agent turns 5.2 % slower (6/6, p = 0.031), which means a tuning pass can measure itself.
- **Prediction:** the noise floor on our six-task and ranked batteries is small for the deterministic tasks
  and **large enough to swallow a 5 % speed claim** for wall time - so any timing claim below ~2x the
  measured spread is not a result.
- **Instrument:** the same config run twice, back to back, scored identically; report the spread in wall
  time and in checks. This is a methodology item and it gates how items 1, 2 and 4 may be read.

### 4. Warm the expert cache from a calibrated hot set, at fixed capacity - READY, later in the queue

- **Question:** our 2026-10-11 warm-cache test was negative, but it warmed with same-domain *prompts*
  (and found `expert-profile.bin` byte-identical afterwards, i.e. nothing persisted). The scan's version is
  different: calibrate the hot set from real text and measure the hit rate (6 % random -> 42 % calibrated).
- **Prediction:** a calibrated hot set raises the hit rate materially and moves decode on our ledger runs,
  but **not** the letters; if the letters move, the cache is not transparent and that is the finding.
- **Instrument:** `ledger2` plus the engine's own hit-rate line; fixed capacity so residency is not the
  variable (this is the same discipline item 1 uses).

### 5. Ollama 0.40.4's native decision-model path - READY, no download

- **What is ready:** the installed Ollama is already **0.40.4**, so the new decision-model path needs no
  upgrade.
- **Question:** does serving Laya/GLiNER through Ollama's native path change either number we care about -
  the 0/4 stall catch rate or the latency (our own serving path measured 27.56 s p95; Colibri measured
  1.7-2.1 s median on the same class)?
- **Prediction:** the catch rate stays **0/4** (the model is the failure, not the server - measured now on
  two engines), and the latency lands nearer Colibri's than ours, i.e. the 27.56 s was our serving path.
- **Instrument:** the frozen 18-window screen, `colibri-laya-20261011/laya_replay.py`, same threshold 0.85.

### 6. Coder IQ1_M - PARKED, needs a 54.40 GiB download and a tight-RAM decision

- **What is known:** `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF` holds IQ1_M as two parts,
  **27.58 + 26.82 = 54.40 GiB**, plus a 0.85 GiB mmproj. D: has 252.8 GiB free, so it fits on disk; against
  this box's **58.46 GiB of usable RAM** it leaves ~4 GiB for everything else, which is tighter than any
  model we have run resident - it needs mmap plus `--cpu-moe` and the same gate discipline the 120B analysis
  used. Not started: the download is ~54 GiB and it is item 6 of 7.
- **Prediction if it runs:** accuracy on the ranked batteries in the same band as the Q2_0/Q4_K_M stacks
  (quantisation cost is mostly recall), with chat throughput near the 20.5 tok/s the scan quotes for 12 GB.

### 7. The reference model on Strata 0.1.44's route - **GATED, do not run**

- **Gate:** issue **#2747** (Niko1221/Strata) opened **2026-10-16T09:31:46Z** and still open - *"Qwen3.6A3B
  fails with out of memory with recommended configs while Qwen3.8-Flash-Next unsloth Q4 runs fine"*. That is
  exactly the route this item would take, so it waits for the OOM to be resolved or explained. Also needs a
  20.98 GiB pack download.

## How to run it

```sh
cd C:/Users/kevin/ai_bench/queue-20261016-shortlist
python runner.py --dry-run                 # gates, slot check, plan, status.json and REPORT.md; no engines
python runner.py                           # the whole queue, in order, serially
python runner.py --only q2-moe-cache-mib-ladder
python runner.py --from q3-noise-floor
python items.py q1-strata-kv-residency     # one item by hand (rarely; the driver owns the gates)
touch QUEUE-STOP                           # cancels before the next item
```

- **The driver refuses to start while another measured run holds the slot.** Mechanically: if anything is
  listening on the lab's Colibri port, it records `inference slot busy` and exits without starting an engine.
  That is the rule about one inference workload at a time, enforced rather than remembered - verified
  on 2026-10-16 while the Colibri knowledge item was still running.
- **It checks the same gates** as the 2026-10-11 queue (free physical >= 9 GiB, commit headroom >= 8 GiB)
  before every item, and a trip stops the queue rather than lowering a bar. It also clears the three engine
  ports between items, so a crashed item cannot leave a model resident.
- **Items q6 and q7 are skipped by their declared status** (`parked`, `gated`) with the reason written into
  `REPORT.md`, rather than being attempted and failing.
- `REPORT.md` is the record: each item's question and prediction are written into it before the run, and the
  outcome after. `status.json` is where the queue is. Logs land in `logs/` (`runner.log`, one per item, and
  one per engine start).

## What this queue deliberately does not do

- It does not re-run anything the 10-14 or 10-16 scans settled.
- It does not touch the Colibri knowledge run: that item keeps its slot, its checkpoint and its own result.
- It does not upgrade the pinned engine or build in place: item 2 stages a *second* build beside b11461, and
  the pinned dir stays byte-identical so every frozen manifest that references it stays valid.
