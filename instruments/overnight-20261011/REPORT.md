# Overnight queue, 2026-10-11, overnight

A serial overnight queue for this lab. It extends the knowledge table to two more configurations, owns the placement-versus-output check we said we should have, repeats our own instruments under the lab's repeat rule, and takes a second decision model to a second engine. One inference workload at a time; the resource gates are checked between items and the queue stops rather than weakening them; no frozen artifact is edited; a file named OVERNIGHT-STOP in this root cancels the queue before the next item.

## i1-strata-placement - Does the resident budget change the answers?

The same 93 shared-correct reasoning items run on Strata at --resident-budget-gib 2 and at 8, everything else identical. Every engine now claims identical logits at every cache capacity; this measures ours, and it is the 'placement versus output' instrument this lab argued it should own.

Prediction recorded before the run: Replies differ on a substantial minority of items (20-60%), because this engine is not seed-stable on long free-form output; the chosen letters change on at most 3 of 93, and the two configurations stay within 2 letters of each other in total correctness.

- finished in 696 s: ok

  - 2026-10-11 21:17:29  run: C:\Program Files\Python311\python.exe C:\Users\kevin\ai_bench\new-items-20261007\knowledge_deep.py --url http://127.0.0.1:8080 --model strata-coder --label strata-res8 --forms reason --limit 93 --pool shared --seeds 3 --timeout 300
  - 2026-10-11 21:22:08    | strata-coder             -> knowledge-deep-result-strata-res8.json
  - 2026-10-11 21:22:08    |   reason : letters 92/93  mean distractors addressed 1.85
  - 2026-10-11 21:22:36  port 8080 cleared
  - 2026-10-11 21:22:36  wrote result-i1-strata-placement.json
  - 2026-10-11 21:22:36  placement: 65/93 replies differ, letters differ on 0, correct 92 vs 92

## i2-kolibri-knowledge - A third model on the knowledge instrument

Kolibri-1 78B (Q3_K_M, its own patched hob-b11434 runtime, experts resident, --load-mode none as declared) on the same 1,100 pinned items as the two leaders. Its results on the coding suite are the best this lab has; nothing is known about its knowledge.

Prediction recorded before the run: Within 3 points of the two leaders, i.e. 85-92% overall, with GSM8K no worse than MMLU, because the lab's other strong models behave that way.

- finished in 1658 s: ok

  - 2026-10-11 21:50:06    |         international_law                   84/100   0.840
  - 2026-10-11 21:50:06    |         philosophy                          80/100   0.800
  - 2026-10-11 21:50:06    |         prehistory                          71/100   0.710
  - 2026-10-11 21:50:06    |         virology                            51/100   0.510
  - 2026-10-11 21:50:06    |         world_religions                     81/100   0.810
  - 2026-10-11 21:50:24  wrote result-i2-kolibri-knowledge.json

## i3-colibri-qwen36 - The same model on a second engine

Colibri v2.0.0 serving its own Qwen3.6-35B-A3B build on the same 1,100 items. Same model family as our best configuration, different engine, different quantisation and packing, no GPU required.

Prediction recorded before the run: Accuracy inside 2 points of our llama.cpp number (88.5%), and the interesting number is wall time per item rather than accuracy.

- finished in 7200 s: TIMEOUT

  - timeout after 7200s

## i4-reason-repeat - Repeat rule on our own instrument

The format-fixed 93-item reasoning run, again, both stacks. The lab's rule is that single runs are samples; this is the first repeat of this instrument across runs.

Prediction recorded before the run: Qwen3.6 90/93 again and Strata 92/93 again, because within a run the replies were byte-identical.

- finished in 1109 s: ok

  - 2026-10-12 00:09:29    |    strata is up
  - 2026-10-12 00:09:29    |    knowledge_deep.py --label strata-deep-rep1 --url http://127.0.0.1:8080
  - 2026-10-12 00:09:29    | strata-coder             -> knowledge-deep-result-strata-deep-rep1.json
  - 2026-10-12 00:09:29    |   reason : letters 92/93  mean distractors addressed 1.90
  - 2026-10-12 00:09:29    | {"arm_exit_codes": {"qwen36": 0, "strata": 0}}
  - 2026-10-12 00:09:29  wrote result-i4-reason-repeat.json

## i5-papers-repeat - Repeatability of the free-form form

Three papers per stack again, same prompt, same pinned sampling. The first run had Qwen3.6 byte-identical three times and Strata producing two different topics.

Prediction recorded before the run: Qwen3.6 one distinct topic again, Strata two or three.

- finished in 323 s: ok

  - 2026-10-12 00:15:03    |    strata is up
  - 2026-10-12 00:15:03    |    knowledge_deep.py --label strata-deep-rep1 --url http://127.0.0.1:8080
  - 2026-10-12 00:15:03    | strata-coder             -> knowledge-deep-result-strata-deep-rep1.json
  - 2026-10-12 00:15:03    |   paper  : 3 papers, mean 429 words, on-subject 3, distinct topics 1, grounded 0.950
  - 2026-10-12 00:15:03    | {"arm_exit_codes": {"qwen36": 0, "strata": 0}}
  - 2026-10-12 00:15:03  wrote result-i5-papers-repeat.json

## i6-gliner-replay - A second decision model on a second engine

GLiNER2.5-Decide on Colibri over the same 18 frozen windows and the same question shape as the Laya replay. Our GLiNER-class verdict was 18/18 correct with 0/4 stalls caught at a 27.56 s p95; Colibri's own speed table predicts 25.7 s at 1923 tokens.

Prediction recorded before the run: Warm p95 between 20 and 35 s, 0/4 stalls caught, i.e. the latency is the model's sequence-length cost and the detection failure is the model, not the engine.

- finished in 1852 s: exit 1

  -              ^^^^^^^^^^^^^^^^^^^^
  -   File "C:\Users\kevin\ai_bench\overnight-20261011\items.py", line 184, in i6_gliner
  -     with shared.colibri_engine('colibri-gliner', GLINER_DIR):
  -   File "C:\Users\kevin\ai_bench\overnight-20261011\shared.py", line 121, in __enter__
  -     raise RuntimeError('%s failed to come up' % self.name)
  - RuntimeError: colibri-gliner failed to come up


**Queue complete** at 2026-10-12 00:46:13.

## i3-colibri-qwen36 - The same model on a second engine

Colibri v2.0.0 serving its own Qwen3.6-35B-A3B build on the same 1,100 items. Same model family as our best configuration, different engine, different quantisation and packing, no GPU required.

Prediction recorded before the run: Accuracy inside 2 points of our llama.cpp number (88.5%), and the interesting number is wall time per item rather than accuracy.

## i4-reason-repeat - Repeat rule on our own instrument

The format-fixed 93-item reasoning run, again, both stacks. The lab's rule is that single runs are samples; this is the first repeat of this instrument across runs.

Prediction recorded before the run: Qwen3.6 90/93 again and Strata 92/93 again, because within a run the replies were byte-identical.

## i4-reason-repeat - Repeat rule on our own instrument

The format-fixed 93-item reasoning run, again, both stacks. The lab's rule is that single runs are samples; this is the first repeat of this instrument across runs.

Prediction recorded before the run: Qwen3.6 90/93 again and Strata 92/93 again, because within a run the replies were byte-identical.

- finished in 368 s: ok

  - 2026-10-15 12:33:42    |    knowledge_deep.py --label qwen36-deep-rep-reason --url http://127.0.0.1:11436
  - 2026-10-15 12:33:42    | qwen36-35b-a3b           -> knowledge-deep-result-qwen36-deep-rep-reason.json
  - 2026-10-15 12:33:42    |   reason : letters 90/93  mean distractors addressed 2.08
  - 2026-10-15 12:33:42    | arm strata: port 8080 already occupied - refusing to start a second engine
  - 2026-10-15 12:33:42    | {"arm_exit_codes": {"qwen36": 0, "strata": 2}}
  - 2026-10-15 12:33:42  wrote result-i4-reason-repeat.json

## i6-gliner-replay - A second decision model on a second engine

GLiNER2.5-Decide on Colibri over the same 18 frozen windows and the same question shape as the Laya replay. Our GLiNER-class verdict was 18/18 correct with 0/4 stalls caught at a 27.56 s p95; Colibri's own speed table predicts 25.7 s at 1923 tokens.

Prediction recorded before the run: Warm p95 between 20 and 35 s, 0/4 stalls caught, i.e. the latency is the model's sequence-length cost and the detection failure is the model, not the engine.

- finished in 116 s: ok

  - 2026-10-15 12:35:48    |   choice  correct 14/18 | stalls caught 0/4  | false alarms 0/14 | flagged 0
  - 2026-10-15 12:35:48    |   latency noul: median 1696 ms, warm p95 2937 ms (gate 3 s: PASS)
  - 2026-10-15 12:35:48    |   latency choice: median 2008 ms, warm p95 3656 ms
  - 2026-10-15 12:35:48    | 
  - 2026-10-15 12:35:48    | wrote C:\Users\kevin\ai_bench\overnight-20261011\gliner-colibri.json
  - 2026-10-15 12:35:50  wrote result-i6-gliner-replay.json


**Queue complete** at 2026-10-15 12:35:56.

## i4-reason-repeat - Repeat rule on our own instrument

The format-fixed 93-item reasoning run, again, both stacks. The lab's rule is that single runs are samples; this is the first repeat of this instrument across runs.

Prediction recorded before the run: Qwen3.6 90/93 again and Strata 92/93 again, because within a run the replies were byte-identical.

- finished in 647 s: ok

  - 2026-10-15 12:47:31    |    strata is up
  - 2026-10-15 12:47:31    |    knowledge_deep.py --label strata-deep-rep-reason --url http://127.0.0.1:8080
  - 2026-10-15 12:47:31    | strata-coder             -> knowledge-deep-result-strata-deep-rep-reason.json
  - 2026-10-15 12:47:31    |   reason : letters 92/93  mean distractors addressed 1.89
  - 2026-10-15 12:47:31    | {"arm_exit_codes": {"qwen36": 0, "strata": 0}}
  - 2026-10-15 12:47:31  wrote result-i4-reason-repeat.json


**Queue complete** at 2026-10-15 12:47:37.

## i6-gliner-replay - A second decision model on a second engine

GLiNER2.5-Decide on Colibri over the same 18 frozen windows and the same question shape as the Laya replay. Our GLiNER-class verdict was 18/18 correct with 0/4 stalls caught at a 27.56 s p95; Colibri's own speed table predicts 25.7 s at 1923 tokens.

Prediction recorded before the run: Warm p95 between 20 and 35 s, 0/4 stalls caught, i.e. the latency is the model's sequence-length cost and the detection failure is the model, not the engine.

- finished in 86 s: ok

  - 2026-10-15 12:49:09    |   choice  correct 14/18 | stalls caught 0/4  | false alarms 0/14 | flagged 0
  - 2026-10-15 12:49:09    |   latency noul: median 1906 ms, warm p95 3703 ms (gate 3 s: FAIL)
  - 2026-10-15 12:49:09    |   latency choice: median 2055 ms, warm p95 3594 ms
  - 2026-10-15 12:49:09    | 
  - 2026-10-15 12:49:09    | wrote C:\Users\kevin\ai_bench\overnight-20261011\gliner-colibri.json
  - 2026-10-15 12:49:11  wrote result-i6-gliner-replay.json


**Queue complete** at 2026-10-15 12:49:17.

## i3-colibri-qwen36 - The same model on a second engine

Colibri v2.0.0 serving its own Qwen3.6-35B-A3B build on the same 1,100 items. Same model family as our best configuration, different engine, different quantisation and packing, no GPU required.

Prediction recorded before the run: Accuracy inside 2 points of our llama.cpp number (88.5%), and the interesting number is wall time per item rather than accuracy.

- finished in 26 s: ok

  - 2026-10-15 12:49:49    |         international_law                    0/100   0.000
  - 2026-10-15 12:49:49    |         philosophy                           0/100   0.000
  - 2026-10-15 12:49:49    |         prehistory                           0/100   0.000
  - 2026-10-15 12:49:49    |         virology                             0/100   0.000
  - 2026-10-15 12:49:49    |         world_religions                      0/100   0.000
  - 2026-10-15 12:49:52  wrote result-i3-colibri-qwen36.json


**Queue complete** at 2026-10-15 12:49:58.

## i3-colibri-qwen36 - The same model on a second engine

Colibri v2.0.0 serving its own Qwen3.6-35B-A3B build on the same 1,100 items. Same model family as our best configuration, different engine, different quantisation and packing, no GPU required.

Prediction recorded before the run: Accuracy inside 2 points of our llama.cpp number (88.5%), and the interesting number is wall time per item rather than accuracy.

- finished in 7200 s: TIMEOUT

  - timeout after 7200s


**Queue complete** at 2026-10-15 14:55:23.

## Scoring, 2026-10-15 (predictions recorded on 2026-10-11, before any of these ran)

**i4-reason-repeat - both predictions hit exactly.** Qwen3.6 + provisioning **90/93** and Strata **92/93**,
the identical counts night 1 recorded, with the letters reproducing across runs and only the free-form prose
moving (mean distractors addressed 1.90 -> 1.89 on Strata, 2.08 on Qwen3.6). This is the first *repeat* of
this instrument across runs, and the answer is that the letter is stable where the prose is not - the same
split the placement item measured on 2026-10-11.

The first attempt was half a run and is kept: the Qwen arm scored 90/93 while the Strata arm never started
("port 8080 already occupied - refusing to start a second engine", `arm_exit_codes {qwen36: 0, strata: 2}`)
because the console's nginx-mirror proxy held 8080, which is this lab's own `STRATA_PORT` (`shared.py:29`).
The driver clears its engine ports *between* items, not before the first one, so the conflict cost exactly
the arm under test. Re-run after the port was clear: **647 s, both arms, `{qwen36: 0, strata: 0}`**.

**i6-gliner-replay - the detection prediction held, the latency prediction was refuted by ~10x.**
Predicted "warm p95 between 20 and 35 s, 0/4 stalls caught, because the latency is the model's
sequence-length cost". Observed 0/4 stalls caught, 14/18 correct at the frozen 0.85 threshold with **zero**
flags either way - the same shape Laya produces, so this instrument still carries no stall signal from
either decision model. But the latency is **2 937 ms warm p95** on the first run and **3 703 ms** on the
repeat: two orders of magnitude below the prediction, and the `gate_3s_passed` verdict flips between the
two samples. So the 2026-10-11 conclusion - "that latency is sequence length (quadratic attention on a
DeBERTa-large), not a serving path; no engine will fix it" - does not survive: the same class of model on
Colibri answers in ~1.7-2.1 s median, where our own serving path measured a 27.56 s p95. The second
finding is that this model sits *at* the 3 s gate rather than inside it, which needs saying whenever the
gate is quoted. The engine log settles what was served: `[gliner_decide] microsoft/deberta-v3-large:
DeBERTa-v2 24 layers x 1024 ... max_len 4096; loaded in 1.7 s`, 36 x `POST /v1/systemone 200`.

**i3-colibri-qwen36 - NOT RUN TO COMPLETION, and it cannot be at the declared timeout.** Three defects
were found and fixed before the run could mean anything, and then the run itself timed out:

1. **The engine's model name is `qwen3.6-colibri`.** The item named the model `qwen36-35b` (the setup name),
   Colibri answers a request naming anything else with `404 model_not_found`, and so all **1,100** requests
   failed in 12.9 s - while `knowledge_run.py` exited **0** with a `0/1100` that read like a model verdict.
   The dead run is preserved as `dead-i3-model-not-found-20261015.json`; the item now reads the id from the
   engine's own `/v1/models`, and the instrument now records `transport_failures` + `scored: false` and exits
   **2** when every reply is a transport error ("unscored, not failed", the same rule the new-task driver got).
2. **The item would have called `coli setup` against a complete directory.** Three attempts at a 5400 s
   timeout each, on the documented trap that downloads and then serves in the foreground so it never
   returns - the eight-hour deadlock of 2026-10-12. It now detects the staged model
   (`qwen36-35b`, 21.44 GiB of 50 files) and skips setup.
3. **`laya_replay.py` hardcoded the engine and checkpoint strings** (its `summary` at lines 123-124), so the
   GLiNER replay wrote `colibri v2.0.0 laya.exe` + the Laya checkpoint into its own result file while the
   engine log said `gliner_decide`. Now `--engine` / `--checkpoint`, with the Laya values as defaults -
   verified: both frozen Laya results still reproduce from those defaults byte-for-byte in those two fields.

Then the measured cost, four-item samples of this same instrument (engine banner `ctx=8192` in all three):

| configuration | s/item | T(1) per token | projection for 1,100 items |
|---|---|---|---|
| engine default (cache 8/layer) | 65.7 | ~240 ms | ~20 h |
| `--no-think --effort minimal` | 66.2 | ~240 ms | ~20 h (no effect) |
| `--cap 32` (32 slots/layer) | 45.1 | 175-200 ms | **~13.8 h** |

The corrected run answered **86 items in 7 200 s** before the driver killed it (exit -9). The model does
answer in the instrument's format - 4/4 on both 4-item samples - so the comparison is sound, just long: it
does **not** fit the 7200 s this item declares. Two further corrections from the same evidence: the served
context is the engine's default **8192**, not the 131,072 the old label claimed (the item passed no
`--ctx`; no knowledge prompt is anywhere near 8k, and the label now says what was served), and the faster
configuration is now declared in the item (`--cap 32`, label `colibri-qwen36-ctx8192-cap32`). Whether to
spend ~14 h on it is Kevin's call, so the item waits with its measurements recorded rather than retrying.

**Also carried forward:** the instrument writes its result only at the end, so a timeout loses the whole run
(7 200 s of work produced no artifact). That is the argument for a `--limit` smoke first, which the
`OVERNIGHT_LIMIT` env var already supports, and for a checkpointing result file if this item runs again.

## A run with a gap in it is not a score (2026-10-16)

The 2026-10-15 12:55 attempt did not stop when the driver reported it timed out. The driver's per-item
timeout killed the wrapper and cleared port 8000 at 14:55:23; the instrument itself survived as an **orphan**
and kept posting to a dead port until 15:44:22, having run **10,137 s (2.82 h)** - more than the 7,200 s the
driver believed it had run. Its file claims **102/1100 = 9.3 %**, and 989 of those failures are connection
errors (`10054` reset, `10061` refused): the 111 items that did answer are simply the ones that ran before
the port was cleared, i.e. *positional*, not a sample. Preserved as
`contaminated-i3-orphan-20261015.json`, moved out of the instrument's directory so it cannot be mistaken for
a result. This is the second instance of the same quirk - `supervise.py`'s docstring records the 2026-10-12
orphan - so the driver's timeout is not, by itself, a stop.

Two consequences, both applied: the instrument now marks a run `scored: false` and exits **2** when **any**
reply fails at the transport level (the ambiguity is worse than an obvious zero - a 9.3 % reads like a weak
model), and the 2026-10-16 run's own wall is 15 h against the driver's 16 h, so the instrument finishes
before the driver can orphan it. The three `knowledge-result-colibri-smoke-*.json` files in the instrument
directory are 4-item smoke samples (baseline / `--no-think` / `--cap 32`) used to price the run, not
comparison results.

**A phantom start, from my own test (2026-10-16 09:30).** While testing the new queue's supervisor, a test
snippet put two sibling roots on `sys.path` and then wrote `import supervise` - which bound *this* root's
historical `supervise.py`, not the new one. That module's job is to wait for an orphan and then drive
i4/i6, so it cleared the engine ports and logged a start of `[i4-reason-repeat, i6-gliner-replay]`; it was
killed within minutes and **no item ever began**, which is why a duplicate i4 block appears above this note
and why `status.json` briefly claimed a run that never happened (it has been rewritten and says so). Two
things came out of it: the new queue's module is now `wait_for_slot.py`, so no two sibling roots share a
module name, and the run in flight was **not harmed** - port 8000 is the same engine process from 08:02:57
and the item kept checkpointing through 09:33:40 (175/1100, zero transport failures). Recorded because "a
run that appears in a log and never happened" is exactly the class of artifact this lab keeps finding in
other people's reports.

## i3-colibri-qwen36 - The same model on a second engine

Colibri v2.0.0 serving its own Qwen3.6-35B-A3B build on the same 1,100 items. Same model family as our best configuration, different engine, different quantisation and packing, no GPU required.

Prediction recorded before the run: Accuracy inside 2 points of our llama.cpp number (88.5%), and the interesting number is wall time per item rather than accuracy.

## i4-reason-repeat - Repeat rule on our own instrument

The format-fixed 93-item reasoning run, again, both stacks. The lab's rule is that single runs are samples; this is the first repeat of this instrument across runs.

Prediction recorded before the run: Qwen3.6 90/93 again and Strata 92/93 again, because within a run the replies were byte-identical.

- finished in 12838 s: exit 4294967295

  - 2026-10-16 08:03:06  healthy
  - 2026-10-16 08:03:06  engine advertises model id 'qwen3.6-colibri'
  - 2026-10-16 08:03:06  run: C:\Program Files\Python311\python.exe C:\Users\kevin\ai_bench\new-items-20261007\knowledge_run.py --url http://127.0.0.1:8000 --model qwen3.6-colibri --label colibri-qwen36-ctx8192-cap32 --timeout 200
  - 2026-10-16 11:36:44    | instrument: 1100 items (gsm8k 300, mmlu 800)
  - 2026-10-16 11:36:44  exit code 4294967295
  - 2026-10-16 11:36:53  wrote result-i3-colibri-qwen36.json


**Queue complete** at 2026-10-16 11:37:09.

## i3-colibri-qwen36 - The same model on a second engine

Colibri v2.0.0 serving its own Qwen3.6-35B-A3B build on the same 1,100 items. Same model family as our best configuration, different engine, different quantisation and packing, no GPU required.

Prediction recorded before the run: Accuracy inside 2 points of our llama.cpp number (88.5%), and the interesting number is wall time per item rather than accuracy.

- finished in 28403 s: exit 2

  - 2026-10-16 21:16:37    |         virology                            51/100   0.510
  - 2026-10-16 21:16:37    |         world_religions                     85/100   0.850
  - 2026-10-16 21:16:37    |         17 of 1100 replies failed at the transport level, e.g. TRANSPORT: ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None)
  - 2026-10-16 21:16:37    |         UNSCORED: the run has a gap in it - the items that answered are positional, not a sample
  - 2026-10-16 21:16:37  exit code 2
  - 2026-10-16 21:16:46  wrote result-i3-colibri-qwen36.json


**Queue complete** at 2026-10-16 21:16:52.

## i3b-colibri-fill - Re-ask what the network dropped

The 13:23 Colibri run answered a 1,100 items but lost 17 requests to ConnectionResetError 10054 (9 virology, 8 grade-school math), which the strict rule treats as a gap. Are those 17 transport events rather than model answers?

Prediction recorded before the run: Yes: the fill resolves most of them, lifting the total from 967/1100 toward ~984/1100, and either end leaves accuracy inside 2 points of the llama.cpp 88.5% the i3 prediction named.

- finished in 6699 s: exit 2

  - 2026-10-16 23:09:45    |         grade_school_math                    0/8     0.000
  - 2026-10-16 23:09:45    |         virology                             5/9     0.556
  - 2026-10-16 23:09:45    |         8 of 17 replies failed at the transport level, e.g. TRANSPORT: TimeoutError('timed out')
  - 2026-10-16 23:09:45    |         UNSCORED: the run has a gap in it - the items that answered are positional, not a sample
  - 2026-10-16 23:09:45  exit code 2
  - 2026-10-16 23:09:54  wrote result-i3b-colibri-fill.json


**Queue complete** at 2026-10-16 23:10:00.

## i3b's outcome: the 17 losses were two different things, and the cause of the second is a timeout

The fill answered 9 of the 17 and lost 8 again - but the split is the finding, and it falls on the subject
boundary:

- **The 9 virology items were transient.** All nine answered on the re-ask (5 correct, 4 wrong), so the main
  run's `ConnectionResetError` there was the network, exactly as predicted.
- **The 8 grade-school-math items are not transport events.** All eight failed four attempts each, now with
  `TimeoutError('timed out')` at the instrument's **200 s per-request budget**, and the engine's log shows
  9 requests served - i.e. the eight GSM8K generations were still in flight when the client gave up. At
  ~4 tok/s a 1024-token arithmetic answer needs ~256 s, so these cannot complete inside 200 s on this
  engine; and because the server is single-slot, a retry queues *behind* the abandoned request, so four
  attempts compound instead of recovering. The fill spent 6,678 s on 17 items - 835 s per GSM8K item - which
  is that compounding, measured.
- **So the prediction is half-right and the half that is wrong is the useful half.** "These are transport
  events, not model answers" holds for virology and fails for grade-school math, whose cause is a declared
  timeout that is too small for this engine's arithmetic items. A retry cannot fix a budget.

**The combined number, with its gap stated rather than smoothed:** 967 from the main run plus 5 from the
fill = **972/1,100 = 88.4 %**, with **8 items (0.73 %) unmeasured**. Bracket: 972 to 980 (all eight right) =
**88.4 % to 89.1 %**. Against llama.cpp's 974/1,100 = 88.5 % on the same items and the same model family:
0.14 points apart at the measured end, 0.6 the other way, both far inside the 1.33-point paired standard
error. The i3 prediction - "accuracy inside 2 points of 88.5 %" - is confirmed at either end, and the
headline is not in doubt: **the same knowledge, and about 13x the wall time** (11.4 h against 51 min).

Closing the last 0.73 % needs `--timeout 400` on the eight arithmetic items: roughly an hour of Colibri
time, a declared follow-up rather than a third pass tonight.

