# Decisions, 2026-11-23: what happens to the benchmarking work

Kevin's answers to the seven questions the tile-lab survey raised, with the consequences and the two pieces of
advice he asked for. This supersedes `TILE-LAB-PLAN-2026-11-23.md` (kept as the survey, not as a plan).

## The seven, answered

| # | question | answer |
|---|---|---|
| 1 | Does the LLM track belong in tile-lab? | **No.** tile-lab stays about tiled GPU kernels. The benchmarking work stays in **`local-llm-lab`**, which is already the model-lab repository - no new sibling repo is needed, and nothing is ported to tile-lab. |
| 2 | Which licence? | **MIT** for this work. `local-llm-lab` is private today; if it is ever published it carries MIT, not the FSL-1.1-MIT that the source material assumed. Recorded here so the choice is not re-litigated per file. |
| 3 | Commit the raw replies, or summaries only? | **Commit everything, uncut - prompts as well as replies** (revised same day: "keep everything in, ignore the cap for now"). The 10 MB line is no longer a limit; it is a marker reported alongside results. Nothing in these suites is personal: the passages are generated filler and the reasoning items are public BBH/GSM8K. The rule that remains is the obvious one - **if a suite ever puts a personal file (a photo, a document) into a prompt, that prompt is redacted before it is committed**. |
| 4 | Retire the ten-task battery? | Advice below. |
| 5 | Which backends? | **Both**, and open to more. `--backend` is explicit; OpenAI-compatible and Ollama-native, plus whatever else can be measured. See the Strata note below - we do **not** currently measure with Strata. |
| 6 | Is the `vt` suite in scope? | Advice below. |
| 7 | Include older evidence? | Not as a rule: evidence kept with a discussion is included **without asking when it is under 10 MB**, older or newer. Above that, ask. This replaces case-by-case asking. |

## Advice: is there a reason not to retire the ten-task battery?

**Retire it as a ranking suite, keep it as a smoke gate.** Two different jobs were being done by one file:

- *Ranking* - it cannot do this. Four of five models land at 27/30 or better and its single separator is a word
  count. A suite that cannot order its subjects is not measuring quality, and keeping it as the headline invites the
  same mistake I made twice today: reading a saturated score as a verdict.
- *Smoke* - it is genuinely good at this: ten deterministic items, a JSON parse, an **executed** `is_prime`, a
  refusal, all in about two minutes per model. That is the check that catches a broken build, a mangled chat
  template or a scorer regression, and BBH/GSM8K cannot replace it because each item there costs far more to run.

So: `quality-pass` becomes the gate a change must pass (all ten, or the change is broken), and **BBH, GSM8K, the
RULER-style long-context probes and the context ladder are what the notes rank with.** If "retire" was meant as
"delete", the cost is losing that two-minute regression check - which is the cheapest thing in the whole harness.

## Advice: is the in-progress `vt` suite in scope?

**Yes, with the design it now has.** It is committed (not the uncommitted draft the survey saw), and it is the probe
that caught my own worst error of the day: the single-chain run scored the 8B 0/1 and I published "variable tracking
separates the 8B", where three distinct chains gave 3/3 and every miss turned out to be `finish=length`. Two rules
came out of it and belong in the port:

1. **distinct instances per repeat** (one haystack, different chains) - a repeat of one string at temperature 0
   measures determinism, and a fresh haystack at 32K measures the engine's prefill curve (110 tok/s at 4k of prompt,
   29 at 8k, 16 at 10k on this model);
2. **`finish_reason` decides whether a miss is a wrong answer or a non-answer**, and only the first is a capability
   result.

That makes `vt` the smallest worked example of the discipline the rest of the harness needs, which is why it travels
with it.

## Strata: what is true today

We **track** Strata and have studied its published numbers; we do **not** measure with it:

- `C:/Users/kevin/strata` is the notes/journal project (`AI-STRENGTH-NOTES.md`, `az-state.json`), not the engine.
- No Strata engine binary is installed on this box, and no version we track has evidence of loading `inkling2_loop`.
- What exists are the release targets the daily scan records (**app 0.2.20 / engine 0.1.65 / Control 0.1.65**) and
  the `RustingStrata` public benchmark page, which is a **separate** Rust engine.

For Strata to become a backend the harness measures, three things are needed and none is done: the engine installed
at a pinned version, an interface the harness can drive (HTTP or CLI), and a load check that it accepts the model
under test. Until then, a Strata row in any table would be a number copied from someone else's page - which is
exactly what this lab's evidence rules forbid.

## Evidence: full fidelity, and what it costs

Both harnesses now store **the prompt and the complete reply**, not a 2,000-character slice (13 rows in the runs of
2026-11-22 are cut at 2,000 characters and cannot be recovered - the prompts were not stored then; every run from now
on is whole).

Cost, measured: a long-context prompt is ~64 KB (a ~16k-token passage), so one model battery goes from **~30 KB to
roughly 500 KB** - long-context and `vt` dominate, the reasoning and quality items are a few KB each. At that rate
10 MB arrives after about **20 batteries**, which is why the cap was worth asking about; the answer was "keep
everything, disk is cheap, we may want a comprehensive reanalysis".

`tools/evidence-size.py` still reports the number and will say when 10 MB is passed - as a marker in the report, not
as a gate.
