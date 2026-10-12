# colibri-laya-20261011: the frozen decision screen, run on a second engine

Laya, the same model this lab screened on 2026-10-07, served by a different engine and a different
implementation of the model, on the same 18 frozen decision windows, scored the lab's way.

**Why:** our Laya result was 14/18 with **0 of 4 stalls caught**, recorded since 2026-09-25 as "unusably
high stuck probabilities" with a disabled threshold. That was our serving path's number for one engine. If
the failure is the model, a second engine reproduces it; if it is our path, it should move. Colibrì is the
only Strata-alternative whose route fits this machine, and its per-engine doc warns that this checkpoint's
`noul` "can follow its option labels rather than the state" - and gives a workaround (a two-option `choice`
with neutral keys). So both shapes were run.

## Setup (pinned, no inference in the staging steps)

- **Colibrì v2.0.0**, released 2026-10-06T20:24:40Z. `colibri-v2.0.0-windows-x86_64.zip` downloaded from the
  GitHub release; **sha256 verified against the published digest**
  `fdb8ea2fad7dcfe44d9d37bfb3e444f1299207f268ab499719f98bd772397d79`. Unpacked under
  `ai_bench/staged-colibri-20261011/`; the release ships prebuilt engines, no build needed.
- **Laya** from `convaiinnovations/laya`, revision pinned **`7b928d828b7b0e022f929d9bd2e44165aa270148`**
  (Apache-2.0). Files: `model.safetensors` (842,609,210 bytes), `rl_agent_config.json`, `encoder/config.json`,
  `tokenizer/tokenizer.json`, `tokenizer/tokenizer_config.json`. Loaded with no conversion.
- **Two layout gotchas, both cost a failed start:** the launcher wants `tokenizer.json` at the **model root**
  (the doc's own `hf download "tokenizer/*"` leaves it in `tokenizer/`, so it must be mirrored up), and a
  **stray root `config.json` must not be present** - the launcher reads it and rejects `model_type: laya`
  ("unsupported model: unsupported model_type: laya"). The doc says it recognises the checkpoint by
  `rl_agent_config.json` plus `encoder/config.json`.
- Serve: `coli.cmd serve --model Models/laya` (OpenAI-compatible API and `/v1/systemone` on 127.0.0.1:8000).
  Context knobs: `COLI_LAYA_MAX_LEN` (checkpoint default 512; the encoder reads up to 8192) and
  `COLI_LAYA_HEAD_MAX_LEN` (default 192).

## Protocol

- Inputs are the lab's frozen files, **verified by sha256 against `local-decisions-followup-20260925-v1/protocol.json`
  before use**: `natural-inputs.json` `9adc36c7b1b6e302…` MATCH, `natural-labels.json` `73d1cda76d94f1c2…` MATCH.
  18 windows, **4 labelled stalls**.
- The question is **verbatim from `decisions-20261005-v3/worker.py`** (`{'type': 'noul', 'instructions':
  'Looking at recentCalls and their observed outcomes, is the agent repeating the same actions without making
  progress on task? …'}`), the `state` sent as the JSON object, and the score is the lab's: **0.85 threshold,
  catch rate over the 4 stalls, false alarms over the other 14**, plus warm p95 against the 3 s gate.
- Second shape: the documented workaround, a two-option `choice` with neutral keys (`repeating` /
  `progressing`), read as P(repeating).
- Script: `laya_replay.py`. Raw results: `laya-colibri-maxlen512.json`, `laya-colibri-maxlen4096.json`.

## Results

| shape | max_len | correct | stalls caught | false alarms | flagged | latency median | warm p95 |
|---|---|---|---|---|---|---|---|
| `noul` (lab's question) | 512 (default) | 14/18 | **0/4** | 0/14 | 0 | 360 ms | 375 ms |
| `noul` | **4096** (lab's input cap) | 14/18 | **0/4** | 0/14 | 0 | 1562 ms | **2765 ms** |
| `choice` workaround | 512 | 14/18 | 0/4 | 0/14 | 0 | 406 ms | 422 ms |
| `choice` workaround | 4096 | 14/18 | 0/4 | 0/14 | 0 | 1672 ms | 2969 ms |
| *our own Laya, for reference* | full | 14/18 | 0/4 | 0/14 | 0 | - | 183 ms |

Reported score matches the lab's recorded Laya result **exactly** - and note that with zero flags at 0.85,
"correct" is just the 14 non-stalls.

### The interesting part is not the score, it is the signal

- **At 512 tokens the head was effectively state-blind**: the same value, `0.717901`, came back for many
  unrelated windows. That is a *truncation* artifact, not a model property - the windows are ~2K tokens, so
  at the default cap the model saw the same truncated prefix every time.
- **At 4096 the values become state-dependent** (18 distinct values, 0.392-0.720) - and **still carry no
  stall signal**: mean(stalls) **0.5868** against mean(non-stalls) **0.5768**, a difference of **+0.010**.
  Sweeping every threshold from 0.40 to 0.90, **no threshold catches a single stall.**
- **The documented workaround does not rescue it either**, and points the wrong way on these windows:
  mean(stalls) 0.5721 against 0.5931, i.e. **-0.021**, and again no threshold catches a stall.
- **Latency is the other finding.** At the context these windows need, Colibrì's Laya is **15x** our
  llama.cpp-served Laya (warm p95 2765 ms vs 183 ms) and it *nearly* trips our own 3 s gate; at the truncated
  default it is 2x slower than ours while seeing a quarter of the input.

**Conclusion:** Laya's failure on this task is **the model, not the serving path**. Reproduced on a second
engine, a second implementation, and a second question shape, on the frozen inputs, with a mechanism now
identified: the head produces near-prior probabilities that do not separate stalled windows from healthy
ones. The earlier note's "unusably high stuck probabilities" was the same phenomenon described from one side.

## Limits

- The threshold sweep above is **tuned on these 18 labels and is not validation**; the lab's rule applies -
  a threshold chosen here would need a fresh labelled set to mean anything. The claim that survives is the
  weak one: no threshold in range separates the 4 stalls from the 14 others.
- One decision model (Laya, English root checkpoint), one engine pair, 18 windows. Colibrì's other decision
  engines (GLiNER2.5-Decide 1.95 GB, Clef 55 GB) are untouched, and GLiNER2.5-Decide is the cheapest next
  probe because our own GLiNER2.5-class result was the opposite: 18/18 with 0 stalls caught but a 27.56 s
  p95 that failed the latency gate.
- The `noul`-follows-labels warning in Colibrì's doc is about the model card's behaviour on its own labels;
  what we measure here is the same failure with our labels, which is a different observation.
- No gate, floor or frozen artifact was touched; the Laya server was stopped after the run.
