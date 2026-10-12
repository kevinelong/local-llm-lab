# overnight-20261011: a serial queue for the night

Authorised 2026-10-11 evening ("research and test what you can overnight"). This root holds the queue, the
driver, the item scripts, per-item logs and results. Nothing outside it is edited except the knowledge
instrument's own result files, which land next to the instrument by design.

## Rules this queue runs under

- **Serial, one inference workload at a time.** Each item starts its own engine and stops it in a
  `finally`; the driver also clears the engine ports between items, so a crashed item cannot leave a model
  resident for the next one.
- **The gates are checked, never lowered.** Before each item the driver reads free physical memory and
  commit headroom and requires **9 GiB free and 8 GiB commit headroom**. A trip **stops the queue** and says
  so in `status.json` and `REPORT.md`; no item retries into a tighter machine.
- **No frozen artifact is edited.** The one exception is additive: the knowledge instrument writes
  `knowledge-result-<label>.json` next to itself, with new labels.
- **Nothing is deleted, nothing is rebooted, no app is killed**, and no process outside the ports this queue
  owns is touched.
- **Cancel at any time**: create a file named `OVERNIGHT-STOP` in this root. The driver checks it before each
  item and exits cleanly; if an item is mid-run it finishes first, then the queue stops.
- **No blind retries.** A failed item is logged with its exit code and its output tail and the queue moves on.

## How to read the morning

- `status.json` - where the night is: the queue, each item's exit code and duration, and why it stopped.
- `REPORT.md` - the same, growing, with each item's question and the prediction recorded *before* its run.
- `logs/` - `runner.log`, one `<item>.log`, and one `engine-<name>.log` per engine start.
- `result-<item>.json` - whatever the item computed (for instance the reply-diff counts for the placement
  item, or the path of the knowledge result it produced).

## The items and their predictions

| item | question | prediction, recorded before the run |
|---|---|---|
| `i1-strata-placement` | does the resident budget change the answers? Same 93 reasoning items at 2 GiB and 8 GiB | replies differ on 20-60% of items, chosen letters on at most 3 of 93, correctness within 2 |
| `i2-kolibri-knowledge` | a third model on the knowledge instrument: Kolibri-1 78B, its own patched runtime, experts resident | within 3 points of the two leaders (85-92%), GSM8K not worse than MMLU |
| `i3-colibri-qwen36` | the same model on a second engine: Colibri's Qwen3.6-35B-A3B over the same 1,100 items | accuracy inside 2 points of 88.5%; wall time is the interesting number |
| `i4-reason-repeat` | the lab's repeat rule on our own instrument: the 93-item reasoning run again | 90/93 and 92/93 again |
| `i5-papers-repeat` | repeatability of the free-form form, three papers per stack again | Qwen3.6 one distinct topic, Strata two or three |
| `i6-gliner-replay` | GLiNER2.5-Decide on Colibri over the frozen windows, the same shape as the Laya replay | warm p95 20-35 s, 0/4 stalls caught |

Predictions are scored in the morning, including the ones that turn out wrong - that is the point of
writing them down first.

## What is deliberately not in this queue

- **The iGPU / NPU second-device track.** It changes the lab's declared configuration and needs Kevin's
  declaration before anything runs, so it stays an open question.
- **Anything requiring a fork build** (the unmerged `-ehs`/`--expert-hot-s` expert cache). No Windows
  toolchain is staged for it, and the merge has not happened.
- **Repeats of the decision suite.** The platform check answered that question exactly: two runs, 7,760
  records, zero differences. Repeating it would measure nothing.
- **Clef** (55 GB, no calibration shipped) and **Colibri's 186 GB Qwen3.8 route** - both low value against
  their disk cost now that the archive lives on `D:`.

## Standing state when this was written

No engine resident, ports 8000/8080/11436 free, 36.7 GiB free physical and 27.1 GiB commit headroom,
`C:` 135.4 GiB and `D:` 276.0 GiB free. Downloads for items 3 and 6 go to
`D:\ai_bench-staged\colibri-models` and `D:\ai_bench-staged\models\GLiNER2.5-Decide`.
