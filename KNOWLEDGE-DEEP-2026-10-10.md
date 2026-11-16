# The tied-topic expansion: reasoning, facts and a one-page paper (2026-10-10)

Two stacks, one prompt set: **Qwen3.6-35B-A3B Q4_K_M on llama.cpp** (context 131,072, `--cpu-moe`) and
**Qwen3.8-Flash-Next Q2_0 on Strata** (context 65,536, 4 GiB resident, streamed). The MCQ knowledge
instrument left them tied (88.5 % vs 89.7 %, inside one standard error), so this asks the next question:
can they *reason about and explain* the topic they are tied on? Instrument and artifacts live in
`ai_bench/new-items-20261007/` (`knowledge_deep.py`, `rescore.py`, `deep_report.py`).

## Design

- **Reasoning form** - held-out astronomy items *both* stacks answered correctly in the MCQ run (93 of
  them), asking for the answer, the single decisive fact, and why the strongest distractor fails.
- **Facts form** - "list 25 checkable facts about Mars and its exploration, one per line."
- **Paper form** - "a one-page paper (~550 words) on a related topic of your choice within Mars science,
  topic on the first line", three repeats at pinned sampling (temperature 0, seed 20261009).
- **Verification corpus**, pinned by sha256 (`05e8091a…`): 12 Wikipedia Mars-science pages, 63,297 words.
  No judge model; everything local. The instrument self-tests against gold, invented junk and
  generic-but-true prose before use (see "Instrument discipline" below).

## Reasoning: no difference, but a systematic failure mode

The first pass used free-form answers and was scored by taking the first `[ABCD]` token of the reply.
That was **wrong as an instrument**: Qwen3.6 often opens by echoing the option it is about to reject
("A. 4:1 … D (9:4) is actually the correct answer"), so the first token is the distractor. The prompt now
requires `ANSWER: <letter>` on the first line, and both runs were scored with a declared rule
(explicit phrase, then bare letter, then first token) recorded per item.

| run | Qwen3.6 | Strata | paired McNemar |
|---|---|---|---|
| morning, 8 Mars items, free-form | 7/8 | 8/8 | - |
| 93 items, free-form, first-token parse | 88/93 (94.6 %) | 92/93 (98.9 %) | p = 0.219 |
| 93 items, free-form, declared rule | 89/93 (95.7 %) | 92/93 (98.9 %) | - |
| **93 items, `ANSWER:` required** | **90/93 (96.8 %)** | **92/93 (98.9 %)** | **p = 0.625** |

With the format required, **all 186 replies parsed by the explicit rule** - no ambiguity left. The
difference is 2 items with 1 discordant pair one way and 3 the other, so **no reasoning difference is
established** on the topic they are most tied on.

What the item level does show is a **reproducible failure mode in Qwen3.6**: all three of its misses are
"derives the correct value, then states a different letter".

| item | its own derivation | it answered | gold |
|---|---|---|---|
| 66 | inverse-square gives 25x | A (100x) | **B (25x)** |
| 74 | "the most precise value is ~2.537 million ly" | B (2.1) | **C (2.5)** |
| 90 | computes 2.175e16 kg | B (2.2e14) | **D (2.2e16)** |

Items 74 and 90 give the identical wrong letter under both prompt variants, so this is a property of the
model, not sampling noise. Strata's single miss (item 94, answering "A and B" where the key is A) is one
item, and its own reasoning is defensible. This is also a warning about the earlier 7/8 reading: one item
in eight is not a rate, and the parse made the rest of the difference look larger than it is.

**My own adjudication was too generous, and the format-fixed run caught it.** In the free-form pass I
credited items 66 and 74 because their *bodies* concluded correctly; the format-fixed run shows the
*stated* letter is wrong in both. For a question of the form "which letter did the model answer", the
stated letter is the measure, and the mismatch with its derivation is the finding - not something to
credit away.

## Facts and papers

| form | Qwen3.6 | Strata |
|---|---|---|
| 25-fact list, grounded | 25/25 | 25/25 |
| facts carrying figures | 16 | 8 |
| paper length (asked ~550 words) | 408 words | 424 words |
| paper grounding | 0.86 | 0.98 |
| distinct topics over 3 repeats | 1 | 2 |

Neither stack fabricated entities: every one of the 50 facts was grounded, and the three figures the
exact-check flagged were hand-verified as **two correct facts absent from the corpus** (Perseverance
1,025 kg; Phobos 22.4 km) and one slightly off (Mars "4,217 miles" vs 4,212). The exact-figure check is a
**flag for human review, not a verdict** - taken at face value it would have reported two hallucinations
that do not exist. Both stacks undershot the requested length by about a quarter, a shared
instruction-following gap rather than a difference. Qwen3.6 returned a byte-identical paper three times
while Strata returned two different papers from the same pinned request, which independently reproduces
the lab's earlier note that temperature 0 is not seed-stable on that engine.

## Instrument discipline (what to reuse, what to avoid)

- **Force the answer format in the prompt.** Free-form reasoning replies cannot be scored reliably; a
  required `ANSWER: <letter>` line made parsing exact for 186/186 replies.
- **Record the parse method per item** and keep both the naive and rule-based letters in the artifact.
- **Self-test the verifier against gold, invented junk and generic-but-true prose.** The first version of
  the grounding check scored invented junk at 0.64 because it was measuring "is this English"; grounding
  only became discriminative when restricted to proper nouns the corpus uses mid-sentence plus exact
  figures.
- **A corpus check cannot confirm truth.** It flags claims that are absent from the corpus, which is not
  the same as false.
- Both stacks' answer-letter distributions match the gold distribution (A20/B16/C30/D27 and
  A16/B15/C31/D31 against gold A18/B18/C32/D32), so **no position bias** on this instrument.
- Repeated identical prompts reproduced the same first letters (8/8 for both stacks), so the endpoint is
  deterministic here.

## Still open

- The papers have not been read by a human. `new-items-20261007/DEEP-SCORECARD.md` holds both stacks'
  facts lists and full papers **relabelled A/B** for blind scoring; the mapping is only in the result
  JSONs. Argument quality and whether the prose is worth reading are not measured by anything here.
- One topic (astronomy/Mars) and one sampling setting; the 4.3-point raw gap that the naive parse
  suggested is a good example of how much a scoring convention can move a headline.

## 2026-11-15: the tie acquires a declared variable, worth about as much as the gap

The 88.5 % vs 89.7 % above was read as "the same knowledge, so ask the next question". `2611.11079`, *"When
Calibration Data Matter in Sub-4-Bit Language Model Quantization"*, prices an input this file never declared:
**task-informed calibration (FragCal-DC) is worth +1.83 pp mean ten-task accuracy at two bits** over generic-text
calibration (SignRound V2, over a 2-4 bit sweep, six dense models 1.7B-8B, ten tasks, four-seed comparisons), with
iterative methods improving at 2 bits while single-pass GPTQ and AWQ show only small mean responses at 3 bits, and
both improving at 2 bits at 70B. Its two controls are what make it usable here instead of a headline: recovery
**concentrates on families included in calibration**, and **deliberately incorrect answer designations retain about
90 %** of the mean gain - so part of the effect is circular - while **changes in reconstruction error do not
consistently track accuracy gains**, which is why a perplexity, an MSE or a file size cannot stand in for the field
(template §2 `pack_calibration_text`).

What that does to the null above: the 89.7 % stack is a **2-bit** pack (Qwen3.8-Flash-Next Q2_0), **neither publisher
declares its calibration text**, and the paired SE on these 1,100 items is **1.33 pt**. An effect of ~1.8 pp is
therefore larger than the 1.2-point gap *and* larger than the instrument's own error bar. The tie stands **as measured
on these two packs** - nothing here is retracted - but it can no longer be read as "two bits equals four bits on this
model": a different calibration set is now measured to move that endpoint by more than the difference between them.
Both stacks' entries for the field read `UNVERIFIED`.


**2026-11-16: the free half is now closed, by absence.** Both publishers were read today for the field the null needs.
`ggml-org/Qwen3.6-35B-A3B-GGUF`'s README is **483 bytes** and declares nothing about calibration, imatrix or the corpus a
quantiser used; `ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF` documents its **GSQ / RCO** method at length
(16,649 bytes) but not a calibration set. So `pack_calibration_text` cannot be filled for either stack from its publisher,
and the consequence is not neutral: **the 88.5 % vs 89.7 % tie may not be quoted as a property of bit-width** - it is a
property of two packs whose calibration is unknown, at an effect size (**+1.83 pp**) larger than both the gap
(**1.2 pt**) and the instrument's paired SE (**1.33 pt**). The positive half of the question - does calibration explain
it - needs a pack whose calibration **is** declared, which means a download, and it should be chosen for that property
rather than for its bit-width.
