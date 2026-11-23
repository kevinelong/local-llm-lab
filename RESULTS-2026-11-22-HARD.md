# Harder suites, 2026-11-22: what the ten-task battery could not separate

The first quality pass put four of five models at 27/30 or better, which means it is **saturated** - it can tell a
broken model from a working one, not a 9B from a 14B. These suites exist because the literature is specific about
which probes still separate model sizes, and none of them was in that battery.

## Why these, with sources

| suite | source | why it separates |
|---|---|---|
| **RULER** - single needle, **multi-needle**, **aggregation** (count a token in the haystack), **variable tracking** | Hsieh et al., *RULER: What's the Real Context Size of Your Long-Context Language Models?* (2024), arXiv:2404.06654 | Single-needle retrieval saturates long before a model's advertised window; multi-needle, aggregation and tracking are the probes where effective context shows through. RULER's headline finding is that most models' *effective* length is a fraction of the advertised one. |
| **BBH** - date understanding, seven-object logical deduction | Suzgun et al., *Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them* (2022), arXiv:2210.09261 | Compositional multi-step tasks where small models fail outright and the failure is not wording: the answer is a date or a list, checked exactly. |
| **GSM8K** | Cobbe et al., *Training Verifiers to Solve Math Word Problems* (2021), arXiv:2110.14168 | The classic multi-step arithmetic discriminator; every item has one numeric answer. |

Not used, and why: MMLU/ARC/HellaSwag are saturated for models of this size and mostly grade knowledge rather than
ability to hold a constraint; MuSR (murder-mystery soft reasoning) is a better discriminator than BBH but its items
are long narratives whose answers need a second model to grade, which turns the score into a judgement about the
judge. Everything here is scored against the dataset's own answer.

## How the long-context items are built

`benchmarks/hard-probe-2026-11-22.py --suite longctx --ctx N` generates four probes deterministically (seeds in the
code), each about `3.2 * N` characters of filler - about 25,000 tokens at the 32,768 window:

1. `niah_single` - one sentence buried at 50 % depth; ask for the number in it.
2. `niah_multi` - four record notes at 15/35/55/75 %; ask for all four.
3. `aggregation` - the word "falcon" inserted 7 times among the filler; ask how many.
4. `variable_tracking` - twelve chained assignments, then ask for one variable's final value (computed by replaying
   the chain in Python, so the expected answer is not a guess).

The filler is ten harbour paragraphs shuffled with a fixed seed, so two models see byte-identical prompts.

## Results

### Long context at ~25,000 tokens in a 32,768 window

| probe | Inkling 2 Mini | qwen3.5:9b |
|---|---|---|
| `niah_single` (one needle, 50 % depth) | pass | pass |
| `niah_multi` (four notes, all four) | pass | pass |
| `aggregation` (count "falcon", 7 planted) | **no answer** - `finish=length` at 1,024, 4,096 *and* 8,192 tokens (159 s, then cut) | pass |
| `variable_tracking` (twelve chained assignments) | pass | pass |

Both models retrieve at 25k and both track variables through a dozen reassignments; **both fail aggregation**, and
both fail it the same way: `finish=length`, empty content, after 100-160 s of deliberation. Inkling did the same at
1,024, 4,096 and 8,192 tokens. This probe has since been rebuilt - the marker word appeared in its own question,
which is an ambiguity a careful model can legitimately argue with rather than count - and the fixed version is what
the two `3/4` rows above were produced with; the counting failure persists under it.

### Reasoning (BBH 15+15, GSM8K 15)

| model | budget | total | date understanding | logical deduction (7 objects) | GSM8K |
|---|---|---|---|---|---|
| **Inkling 2 Mini** | 4096 | **42/45** | 13/15 | **15/15** | 14/15 |
| Inkling 2 Mini (same items as below) | 4096 | **28/30** | 8/10 | 10/10 | 10/10 |
| qwen3.5:9b | 4096 | **17/45 - invalid**, all 28 misses `finish=length` | - | - | - |
| qwen3.5:9b | 16384 | **27/30** | 8/10 | 10/10 | **8/10** |

**qwen3.5:9b's first run is not a score.** Every one of its 28 misses ended `finish=length` - empty `content` after
the model spent all 4,096 tokens reasoning. Capability was never exercised. Inkling answered the same items inside
that 4,096 budget; qwen3.5 needed **16,384** to finish them.

**On the comparable 30 items, the two are level:** Inkling 28/30, qwen3.5:9b 27/30, the single item of difference
being two GSM8K questions. At n=30 that is a tie, not a ranking. Where they do differ is cost: **Inkling reached the
same answers in a quarter of the reasoning budget.** For an agent loop that pays by token, that is the more useful
number of the two.

The three Inkling misses are real but narrow: two date-arithmetic items and one GSM8K item where its final number was
wrong. Everything else - the full seven-object deduction set, thirteen of fifteen date items - it gets.

### The scorer bug this suite exposed, again on our side

The first run scored Inkling **17/45**, with **0/15 on date understanding** and 3/15 on logical deduction. The model
had not failed: **BBH's targets are letters** (`(B)`), while the models answer the *value* ("12/25/1937") or a bare
`D`. Comparing "12/25/1937" to "(B)" marks a correct answer wrong. The scorer now accepts either the letter or the
option text the letter names, and the stored replies were re-scored without re-running anything
(`benchmarks/rescore-hard-2026-11-22.py`): **17/45 -> 42/45**.

That is the third scorer defect of the day, all three in the same direction - a correct model answer marked wrong by a
narrow comparison. It is also the reason each of these files keeps the raw `content` of every reply.

## Where aggregation breaks: a budget-by-context ladder

The `0/1` in the 32K table is not a single fact - it hides two variables, the passage length and the deliberation
budget, and the request carries both inside the window (prompt + `max_tokens` cannot exceed it). Measuring them
apart is what turns "fails long context" into a number.

Inkling 2 Mini, one item (seven planted occurrences of a marker word), every run a fresh `llama-server` at that
window:

| passage | budget | result | wall |
|---|---|---|---|
| 1,024 | 512 | empty (`finish=length`) | 8 s |
| 2,048 | 512 | empty | 9 s |
| **1,024** | **4,096** | **"7"** (`stop`) | **10 s** |
| **4,096** | **8,192** | **"7"** | **83 s** |
| 8,192 | 2,048 | empty | 36 s |
| **8,192** | **8,192** | **"7"** | **103 s** |
| 16,384 | 4,096 | empty | - |
| 16,384 | 16,384 | empty | 309 s |
| 32,768 | 8,192 | empty | - |

**It can count** - a three-line prompt asking the same thing gets `3`, `stop`, after 272 characters of reasoning -
so the failures above are deliberation, not arithmetic. The pattern is consistent: with enough budget it answers up
to **8,192** tokens of passage, and at **16,384** a 16,384-token budget is still not enough (309 s, then cut). The
break is therefore between 8K and 16K, at about a quarter to a half of the 32,768 window, and the cost of getting
there grows with the passage (10 s at 1K, 83 s at 4K, 103 s at 8K).

qwen3.5:9b, same item, `num_ctx` set explicitly:

| passage | budget | result | wall |
|---|---|---|---|
| 8,192 | 8,192 | empty (`finish=length`) | 102 s |
| 16,384 | 16,384 | empty | 197 s |
| 32,768 | 8,192 | empty | - |

**qwen3.5:9b does not answer the aggregation probe at any window tried**, including 8,192 where Inkling answers in
103 s. This is the one probe where the two models separate on ability rather than on cost.

The general lesson is RULER's: a retrieval probe saturates long before a model's window, and the probe that
actually separates is the one that has to *sweep* the passage rather than find one line in it.

## The size ladder: all five models on both suites

Long context at ~15,800 tokens inside a 32,768 window, one run per probe; reasoning on the first 10 items of each
BBH/GSM8K task (30 items), budget 8,192, `num_ctx` 8,192 for the Ollama models so a 14B is not paying its 32K spill.

| model | parameters | longctx | single | multi | aggregation | tracking | reasoning (30) | date | deduction | GSM8K |
|---|---|---|---|---|---|---|---|---|---|---|
| **Inkling 2 Mini** | 26.4B/3.4B MoE | **3/4** | pass | pass | **fail** | pass | **28/30** | 8/10 | 10/10 | 10/10 |
| **qwen3:14b** | 14.8B dense | **3/4** | pass | pass | **fail** | **pass** | **28/30** | 8/10 | **10/10** | **10/10** |
| qwen3.5:9b | 9B dense | 3/4 | pass | pass | fail | pass | 27/30 | 8/10 | 10/10 | 8/10 |
| qwen3:8b | 8.2B dense | **2/4** | pass | pass | fail | **fail** | 24/30 | 8/10 | 6/10 | 10/10 |
| gemma4:12b | 12B dense | **1/4** | pass | **fail** | fail | **fail** | **4/30 (26 unanswered)** | 1/10 (9 unanswered) | 0/10 (10 unanswered) | 3/10 (7 unanswered) |

**What actually separates them, in order of sharpness:**

1. ~~Variable tracking at 32K separates the 8B from everything else.~~ **RETRACTED 2026-11-23 - see the repeats
   below. The 8B holds the chain 3/3; its single miss in this table ended `finish=length`, which was my budget, not
   its ability. There is no scale effect on this probe.**
2. **Reasoning separates by size, but not monotonically**: 14B 28/30, 26B/3.4B-active 28/30, 9B 27/30, 8B 24/30. The
   MoE matches the 14B dense at a fifth of its speed cost; the 8B is two items behind the 9B and four behind the 14B,
   and its failures are concentrated in the seven-object deduction task (6/10).
3. **Aggregation separates nobody at 25k** - every model fails it, which is RULER's point: this probe does not
   reward size, it rewards being able to sweep a long passage at all.
4. **gemma4:12b fails by not answering, and the numbers say so rather than flattering it.** Its reasoning row is
   **4/30, but 26 of those 30 rows ended `finish=length` with empty `content`** - only four answers were produced, and
   **all four were correct**. Same shape as its `1/4` long-context row and its six unanswered items in the quality
   pass: it deliberates and does not terminate, so it returns nothing on anything needing more than a few hundred
   output tokens. Every probe that could score it, it passed; it reached the probes too rarely to be scored. No budget
   tried - up to 16,384 tokens, on a five-word prompt - gets an answer out of it.

**A caveat that keeps this honest:** all five rows are n=1 per long-context probe and n=1 per reasoning item. BBH and
GSM8K items are fixed and machine-scored, so the reasoning numbers are not noisy in the way a generated task would be,
but the aggregate over 30 items still carries about ±2 items of sampling error. The 8B's missing variable-tracking
item is a single observation; it is reported as one, and would be worth repeating before anyone builds a rule on it.

## The variable-tracking repeat, and the retraction it forced

The matrix above reports **one** tracking probe per model, and I read the 8B's single miss as scale. That was wrong,
and repeating it with three **distinct chains** (same haystack across reps, so the repeat measures the chain and not
the engine's prefill: at 32K this model processes a 16k prompt at 15-29 tok/s, against 110 tok/s at 4k) says so:

| model | tracking at 32K, 3 chains | finishes |
|---|---|---|
| Inkling 2 Mini | **3/3** | stop, stop, stop |
| qwen3:14b | **3/3** | stop, stop, stop |
| qwen3:8b | **3/3** | stop, stop, stop |
| qwen3.5:9b | 1/3 | **stop, length, length** |
| gemma4:12b | 1/3 | **length, length, stop** |

**Every miss in that table is `finish=length` with empty content - not one model ever produced a wrong value.** So
this probe does not rank models by capability at all; it separates the models that *finish* from the ones that
deliberate past 2,048 tokens. The 8B - the model the retracted claim was about - is 3/3, and the two 1/3 rows are a
budget effect, exactly like the one that produced the original miss.

Lesson, in the lab's own terms: **n=1 on a probe whose failure mode is "did not answer" is not a measurement of
ability**, and `finish_reason` decides which of the two happened. The original miss had `finish=length` written next
to it in the stored row, and I read past it.
