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
