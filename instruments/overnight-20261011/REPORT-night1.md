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

