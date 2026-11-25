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
| 5 | Which backends? | **Both**, and open to more. `--backend` is explicit; OpenAI-compatible and Ollama-native, plus whatever else can be measured. See the Strata note below - **corrected 2026-11-25: we do measure with Strata** (0.1.66, since 2026-11-24). |
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

**Corrected 2026-11-25 - this section was wrong.** It read *"we do **not** measure with it"* and *"no version we track
has evidence of loading `inkling2_loop`"*. Both were written from Strata's release notes and neither survived an
install: on **2026-11-24**, **Strata 0.1.66** imported our exact GGUF as `inkling2_loop` (744 tensors, tokenizer
present, the unsloth `Mainline_Support` layout read in place) and served it, then was measured on the ten-task
battery. Evidence and the correction's own record: `README.md` §0.3-0.4, `INKLING-2-MINI-2026-11-21.md` §"Strata,
2026-11-24", `results/quality-strata-2026-11-24.json`, `results/quality-strata-sq10-2026-11-24.json`.

What the measurement settled:

- The engine installs **without elevation** (engine tarball + Control zip, both sha256-verified; the signed `.exe` was
  skipped on purpose), and on first launch it downloads a **model-specific engine** (417 MB) rather than using the
  generic one.
- On this card it is **2.4x slower than llama.cpp on the same file**: 28.3 against 67.4 tok/s, 27/30 against 30/30. Its
  own SQ-10 pack is the slowest row measured (**17.1 tok/s**) and, on the one question that has no answer, it
  **fabricated a year** where our two-bit file on the same engine refused. Strata's design pays on the 24 GB card its
  own table quotes, not on 12 GB.
- **It is not resident now.** The staged binaries stay on disk; no `strata` process is running (the only engine process
  on this box is `ollama`, pid 57832). Note that *"we do not measure with Strata"* was already false when this section
  was written, independently of the `inkling2_loop` question: the October ladders on engine **0.1.47** and the `q2_0`
  pack are Strata rows (`CHUNK-LADDER-AND-RESERVE-2026-10-26.md`, `CACHE-CEILING-2026-11-15.md`), and `README.md` §3
  quotes Strata at **1.93 s per item** on the 1,100-item knowledge set. What is new in November is this model on it.
- What the original text still gets right: `C:/Users/kevin/strata` is the notes/journal project (`AI-STRENGTH-NOTES.md`,
  `az-state.json`), not the engine; and `RustingStrata` is a **separate** Rust engine, not a Strata release. The targets
  the daily scan tracks have moved to **app 0.2.21 / Terminal 0.2.21.1 / engines 0.1.67 / Control 0.1.68**
  (`NEWS-2026-11-25.md` §1).

So the original objection no longer holds either: a Strata row is no longer "a number copied from someone else's
page" - it is one this lab measured, and it sits beside llama.cpp's and Colibri's in `MODELS.md`.

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
