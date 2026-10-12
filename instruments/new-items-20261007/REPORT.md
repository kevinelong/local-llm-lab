# new-items-20261007 REPORT: the five queue items the plan created

Item-by-item work on the five-item queue that `PLAN-EXECUTION-20261007.md` produced - the ledger
termination probe (item 3), the tool-call-rescue check (item 4), Qwen3.6 long context (item 5), the
MTP rate comparison (item 1) and the rate sets with the checks behind them (item 2) - plus the deeper
pass the same day, which changed how the lab should read its own numbers.

Contents: the whole-history census and the two truncation causes; the reply-cap fix; the 226-check
ledger battery and the multi-file task; live validation of both; then items 1-5, the Strata mitigation,
the queued work that needs a decision, and the method notes.

## Whole-history census (2026-10-08): half of all sub-perfect sessions are harness artifacts

`census.py` classified **every session on disk** - 178 sessions, 2,414 scored checks, spanning
2026-09-16 to 2026-10-08 and the Pi 0.85.1/0.86.1/0.87.1 and OMP 18.3.1 hosts, the llama.cpp and
Strata engines and a dozen model families:

| Class | Sessions | Meaning |
|---|---|---|
| COMPLETE | 94 | full marks |
| OTHER | 44 | ended normally (`stop`), artifact still wrong - see the refinement below |
| **TRUNCATED_TURN** | **23** | last turn `stopReason=length` with **no tool call** - the loop ends before it acts |
| **EXTERNAL_KILL** | **17** | `exit 143`/SIGTERM - resource guard or wall, mid-work |

So of 84 sub-perfect sessions, **40 (48 %) are harness or platform artifacts, not model errors.** That figure is the single most important correction in this document: the
lab's historical per-model "reliability" numbers are roughly half measurement.

### Refinement: a wider scan reclassifies the largest bucket

A second pass over every root including the day's new ones (99 sub-perfect sessions) split the same
way, and it changes the reading of the "OTHER" rows:

| Class | Sessions | What the final turn actually was |
|---|---|---|
| **prose-quit** | **50** | prose text, no tool call, loop read it as done |
| truncated-turn | 27 | `stopReason=length`, no tool call |
| external kill | 18 | `exit 143` |
| error/unknown stop | 4 | transport or engine |

The prose-quits are **not** the well-known "planning sentence mistaken for completion" (OpenHands
#3992): ten of them sampled across models and scores are all *completion summaries* - "Solution
complete", "solution.py repaired", "I have successfully implemented ..." followed by a bullet list of
the fixes. The model believed it was finished while 1-8 hidden checks still failed. That is a
**self-verification gap on the model's side**, and it is the single largest failure class in the lab's
history. The harness-mediated share is therefore **45 of 99 (45 %)**: 27 truncations plus 18 kills.

The distinction matters for what to build. A nudge for tool-call-free turns - the fix the community
converged on for *their* version of this class - would mostly get "DONE" back from ours. What improves
these rows is a test battery sharp enough to catch what the model's own audit missed, which is what
`ledger2` and `repo` are for: on the frozen battery a 68/70 looked like a rounding error; on the finer
one the same artifacts separate into 208-226 and the shortfall has a name.

### The truncation class has two causes, and both are under-provisioned constants

`witnesses.py` reads each witness's wire capture (27 sessions end `stopReason=length` with no tool
call; 23 of them carry a scored result):

| Cause | Witnesses | Signature | Effect |
|---|---|---|---|
| **Reply-cap truncation** | **19** | `completion == allowance` exactly (8,192 / 12,288 / 49,152 depending on the root), thinking blocks 12k-209k chars | the reply is cut mid-thinking, so no tool call is ever emitted; scores collapse to 0-29 % |
| **Context exhaustion** | 6 | `prompt` 32,475-32,764 against a 32,768 served context; completion 4-292 tokens | the transcript has filled the window, so the closing turn is silently cut - **4 of these 6 still scored 68-76 of 76/70/75**, i.e. mostly benign |
| Engine-specific | 1 | Strata 0.1.39: completion 3,384 of a 12,288 allowance | one witness, superseded engine |

Both dominant causes are harness constants, not model properties: a 12,288-token reply cap and a
32,768-token context. On this machine both are unnecessarily small - the box has been measured at
**262,144 context with 26-27 GiB of RAM still free** (item 5). The context cause in particular is the
long-standing "sessions stop after two or three turns" mystery, and the 32k window is why the RAM
upgrade's headline capability has never been exercised by the screen.

Witnesses appear under every host and engine tested, with thinking blocks from 1,023 to 208,830
characters - the same mechanism, not one bad model:

```
candidates-20260929-v5  minicpm-paths    9/75    completion 12288 = cap   think  40,043
mimo-harness-20260925-v3 pi0871-paths    9/75    completion 12288 = cap   think  36,830
mimo-output-20260928-v2  pi0861-paths    9/75    completion 49152 = cap   think 208,830
mimo-timeout-20260928-v1 pi0871-ledger   7/70    completion 12288 = cap   think  46,062
strata-20261007-v3       oms-ledger      7/70    completion 12288 = cap   think  50,156
candidates-20261007-v27-2 (MTP) ledger  66/70    prompt 32,475 of 32768  completion 290
```

## The measurement fix: a 226-check ledger battery that un-saturates the task

The diagnosis above says the screen cannot rank the top group because two of its three tasks are
saturated and the ledger concentrates its discrimination in five checks. The fix is more of what
already discriminates. `new_tasks_20261008.py` defines **`ledger2`**: the frozen `reconcile`
specification, the frozen reference implementation, the frozen 70 cases and their indices, plus
**156 extra checks** (106 labelled traps + 50 further randomised valid ledgers with Unicode names).

Verification of the instrument itself (`ref_solution.py` delegates to the frozen reference):

| Candidate | frozen battery | ledger2 |
|---|---|---|
| frozen reference implementation | 70/70 | **226/226** |
| the task's buggy starter | 65/70 (92.9 %) | **62/226 (27.4 %)** |

Because cases 0-69 are byte-identical, **every ledger artifact already on disk can be re-scored**.
`rescore.py` did that for 62 sessions - no inference, and the result is the resolution the frozen
battery could not provide:

| Configuration | frozen | **ledger2** | What it misses |
|---|---|---|---|
| Swift Bonsai 2 (both runs), Strata v2/v5/v8/v9/v15-2/v16-1/v16-2/v19-2/v19-3/v20-1/v20-3, DeepSeek V4.1 Flash | 70/70 | **226/226** | nothing |
| Qwen3.6 `-v26-1`, Strata v1.39/v2/v16-3/v19-1/v20-2, DeepSeek v2 | 70/70 | **225** | one trap: `csv-shape/lone-cr-terminators` |
| Strata v16-1/v20-2, Qwen3.6 `-v26-2` | 68/70 | 220 | 4 CSV traps (unclosed quote, quote-then-char, quote-space-comma, lone CR) |
| Kolibri-1 `-v7`, Qwen3.6 `-v27-1` | 69/70 | 210-212 | the 12 Unicode-digit traps + `cents-shape/'١٢'` |
| Qwen3.6 `-v24` plain, `-v25` MTP, `-v27-2` | 68-69/70 | 208-209 | Unicode digits, header variants, more CSV shapes |
| Nemotron `-v11`, Qwen3-Coder `-v9`/`-v22-*`, gpt-oss `-v12`/`-v18-*` | 59-67/70 | 177-216 | mixed: Unicode digits and spaces, signs, header variants |
| truncated sessions (unchanged starter) | 7/70 | **62/226** | everything - the session never wrote an artifact |

Three things this buys:

1. **The top group now has a ladder**: a 18-check spread (208-226) where the frozen battery showed a
   2-check spread. Qwen3.6 plain/MTP, Kolibri and Strata are no longer "the same 99 %".
2. **The single sharpest trap is `lone-cr-terminators`** - a CSV whose line terminator is a bare CR,
   which `csv.reader` handles and a naive splitter does not. It is the sole miss in seven otherwise
   perfect sessions, making it the most discriminating single check in the suite.
3. **Trap-class profiles replace a composite score**: "accepts Unicode digits", "accepts zero-width
   whitespace in the account", "does not raise on a lone CR" are statements about a model that mean
   something, unlike "68 versus 70 out of 70".

| Trap class | Checks | Fails first at |
|---|---|---|
| `unicode-digit/*` (7 scripts × plain/leading-zero/embedded) | 21 | 208/226 class |
| `unicode-space/*` (NBSP, em space, ideographic, zero-width, BOM) | 24 | 199/226 class |
| `cents-shape/*` (signs, floats, exponents, fullwidth, embedded newline) | 18 | 179/226 class |
| `csv-shape/*` (20 quoting/terminator shapes) | 20 | 220/226 class |
| `header/*` (BOM, trailing space, case, empty and blank text) | 10 | 208/226 class |
| `name/*` (accents, emoji, zero-width, 300 chars) | 9 | 76/226 class |
| `accumulation/*` (huge values, 40-digit leading zeros) | 4 | 126/226 class |

## Item 3 - why the ledger session ends after two or three turns: ANSWERED

Forensics over every Strata ledger session on disk (13 sessions, engines 0.1.39 and 0.1.40.3),
using the engine's own server log, the per-turn `stopReason` and the wire captures:

| Class | Sessions | Score | Evidence |
|---|---|---|---|
| **Thinking-truncated reply** | v1, v3, v4 (3/13) | 7/70, 7/70, 64/70 | engine log: *"the reply reached max tokens while still thinking, so it has no answer"*; `stopReason=length` with no tool call |
| **External termination** | v15-1 (guard stop, 97.6 s), 2026-10-05-v1 (720 s wall) (2/13) | 7/70, 7/70 | `exit 143` (SIGTERM), STOP file, no truncation diagnostic |
| **Completes** | 8/13 | 70/70 | - |

The correlation is exact in both directions: **every one of the three sub-70 scores in the
truncation class has the engine's diagnostic line, and none of the 70/70 sessions has it.** The
mechanism is not the model giving up and not the task being impossible: the model writes a long
chain of thought, the response hits its output budget *inside the thinking*, and a reply with no
answer and no tool call is exactly what ends an agent loop. Wire captures show the two limiting
paths - v3's call stopped at `completion_tokens: 12288` (the harness's per-response cap), v1's at
3,384 with `max_tokens: 12288` requested (the engine's own limit).

Two consequences worth keeping:

1. The engine documents the fix and it is untested here: `"reasoning_budget_tokens": N` in
   `strata-<model>.json` ends the thinking at N tokens with a wrap-up and `</think>` so the model
   answers from there, and `"reasoning_close_retry": true` closes a thinking-only ending once and
   continues. Both are opt-in and off by default. `ledger_budget.py` runs both (arms A and B,
   three sessions each) against the 12 GiB template.
2. `clean_finish` is not the score gate here: four of the eight 70/70 sessions ended with
   `exit 143` and `clean=False` because the runner terminates the agent after the artifact is
   already correct. Reading `clean` as failure would have mis-scored half the successes.

One further failure mode, unrelated to the engine: in the v2 (70/70) session the model's first
`write` call arrived with its payload mangled into the `path` argument
(`...solution.py\n</parameter=\n<parameter=content>\nimport csv...`), the harness answered
"content is required", and the model retried and recovered. Worth noting for item 4: the model
does emit XML-ish tool-call markup - just as broken *arguments*, not as `<tool_call>` inside
reasoning, which is the case the 0.1.40.1 rescue targets.

## Item 1 - MTP versus plain, n = 3 per arm: faster per token, not faster per task

`mtp_arms.py` added two samples to each arm (fresh roots, identical declaration; the first pair is
the `-v24`/`-v25` templates). Agent-side totals, the three tasks summed:

| Arm | Samples (checks, agent s, tokens, tok/s) | Mean checks | Mean agent s | Mean tokens | Mean tok/s |
|---|---|---|---|---|---|
| plain | 219 / 568.6 / 21,646 / 38.1<br>**221** / 972.4 / 38,133 / 39.2<br>219 / 741.8 / 28,013 / 37.8 | 219.7 | 760.9 | 29,264 | **38.3** |
| MTP (`--spec-type draft-mtp -n-max 3`) | 220 / 785.3 / 41,584 / 53.0<br>219 / 670.8 / 33,040 / 49.3<br>216 / 661.0 / 32,208 / 48.7 | 218.3 | 705.7 | 35,610 | **50.3** |

- **Decode: +31.2 % per token** (50.3 vs 38.3 tok/s), the largest and most consistent effect.
- **Task time: only -7.3 %**, because the MTP arm emitted **+21.7 % more tokens** - the speculative
  trajectories are longer, which eats most of the decode gain.
- **Accuracy: no gain.** Plain scored 219, 221, 219; MTP 220, 219, 216. Per task, `paths` is 75/75 in
  every sample both ways; `events` is 76/76 three times plain versus 76, 75, 75 MTP; `ledger` is
  68/70/68 plain versus 69/69/66 MTP. The single-pair reading that started this item (MTP "220 versus
  219, more capable") does not survive repetition: it was run variance.

So MTP is worth enabling for what it is - a decode-rate win - and not for capability. A workload that
pays per token or per second of decoding gains ~30 %; the coding screen as a whole gains ~7 %.

## Item 2 - the rate sets

| Configuration | `events` (76) | `ledger` (70) | `paths` (75) | Samples |
|---|---|---|---|---|
| Qwen3.6-35B-A3B plain | 76, 76, 76 | 68, **70**, 68 | 75, 75, 75 | 3 |
| Qwen3.6-35B-A3B + MTP | 76, 75, 75 | 69, 69, 66 | 75, 75, 75 | 3 |
| Kolibri-1 Q3_K_M | 76, 76, 76 | 68, 69, **70** | 75, 75, 75 | 3 |
| Nemotron-3.5-Lightning-30B | 76, 76, 76 | 67, 68, 68 | 75, 75, 75 | 3 |
| Strata Q2_0 (v0.1.40.3) | 76, 76, 76 | **70, 70**, 7, **70** | 75, 75, 75 | 4 |

`events` and `paths` are saturated at every configuration: the honest statement is that these tasks no
longer discriminate and their 76/76 and 75/75 should not be read as capability. `ledger` is the only
discriminating task, and the checks behind it (section above) show it discriminates on five edge cases
plus the truncation/harness effects of item 3. Qwen3.6 remains the best choice overall - it is the only
configuration with a perfect 221/221 sample, it holds 24 GiB of RAM headroom doing it, and its MTP head
is free decode speed - but a 1-2 check ledger difference between these four is not a capability ranking.

## Item 2 - the checks behind the ledger rates

The rate sets are only as useful as the checks behind them, so I tallied every ledger evaluation on
disk: 30 samples across 12 model configurations, of which 23 reached >= 60/70. Among those 23,
misses are almost entirely these five:

| Check | What it tests | Samples failing |
|---|---|---|
| 19 | `cents` must be **ASCII** digits - the case injects Arabic-Indic U+0661, which `'١'.isdigit()` and even `int('١')` accept | **14/23** |
| 7 | malformed quoting `"a"x` (must raise under `csv.reader(strict=True)`) | 12/23 |
| 5 | unclosed quote `"unclosed,credit,2` (must raise) | 11/23 |
| 0 | empty text (must raise) | 10/23 |
| 6 | blank record `\n\n` (must raise) | 5/23 |

Everything else - the other 65 checks, including 50 randomised valid ledgers - fails at most three
times each. Only four samples in the whole series ever scored 70/70: the two Swift Bonsai runs, the
Kolibri `-v16-3` run, and Qwen3.6 `-v26-1`. So a ledger score quoted without these five checks says
little: a 68/70 is usually the Unicode-digit trap, not a broken parser.

That also explains the model ranking the single-sample table suggested: Kolibri (68, 69, 70) and
Nemotron (67, 68, 68) and Qwen3.6 (68, 69, 70, 68) differ mostly in how often they remember that
`isdigit()` is Unicode-aware - a real, reproducible difference, but a narrow one.

**Refresh, 2026-10-09** (final pass, after the nine-task sweeps; `census_checks.py`, read-only, every
artifact on disk): **105 ledger artifacts**, 93 of them at >= 90 % of the task's best score, with the
leaders unchanged - **case 19 fails 64/93 (69 %)**, case 7 65/93, case 5 69/93, case 0 73/93, case 6
81/93, then a tail at 91-92/93. The other batteries, as artifacts (top group, checks still splitting):
`events` 71 (64, **6**), `paths` 63 (62, **3**), `ledger2` 190 (147, **43**), `repo` 33 (25, **9**),
`longctx` 24 (20, **0**), and the three newest at 6-7 artifacts each (`repo2` 6, `perf` 7, `longctx2` 6).
Two things this pass adds:

- **`repo` now splits on nine checks, not three.** The new samples brought a second cluster into view
  (cases 34-37 and 69-70 at 24/25) beside the varint class (63-65 at 21-22/25), so the battery is
  discriminating more than the "one UTF-8 class" reading of the earlier, smaller sample suggested.
- **The three newest batteries show 0 splitting *in the top group* while discriminating across models.**
  That is the filter doing its job, not saturation: `repo2`'s top group is only the two 54/55 rows, and
  gpt-oss's 0/78 `repo`, its 28/33 `perf` and Nemotron's 0/40 `longctx2` all sit *below* the 90 % line.
  Coarse separation between models is not visible to a top-group-only test, by construction.

## Cause 1 confirmed and fixed: the reply cap was killing MiniCPM

`cap_test.py` ran the two models with the most collapses at a raised per-response cap
(12,288 -> 32,768, session quota 24,000 -> 48,000; one declared change per root, wall unchanged):

| Configuration | events | ledger | paths | sweep | collapse |
|---|---|---|---|---|---|
| MiniCPM5-2B, historical (6 full sweeps) | 0-75-76 | 0-65-69 | **0**-75-75 | 0-99.5 % | **33 %** |
| MiniCPM5-2B, cap 32,768 (`truncation-20261008-v1`) | **76/76** | 66/70 | **75/75** | 217/221 = 98.2 % | **0** |
| gpt-oss-20b, historical (3 full sweeps) | 0-75-76 | 65-66-68 | 75-75-75 | 63.8-98.6 % | **33 %** |
| gpt-oss-20b, cap 32,768 (`truncation-20261008-v2`) | 75/76 | 66/70 | 73/75 | 214/221 = 96.8 % | **0** |

The decisive detail: **`paths` was the task that collapsed for MiniCPM at 9/75 twice, and at the
raised cap it completes at 75/75.** Its events session ran 39 turns and 19,606 tokens (its historical
sessions used 3-16 k) - the model was allowed to think instead of being cut. Both tasks that
previously died mid-thinking now finish at the top of the model's range, and the ledger lands at 66/70,
which is that model's median, not a collapse.

One detail that supports the earlier reading of cause 2: MiniCPM's events session still ends with
`stopReason=length` on its closing turn (the transcript has filled the window) and still scores 76/76 -
a truncated final turn is harmless once the artifact is already correct.

So: **the dominant truncation class is a harness constant, and raising it converts collapses into
ordinary results.** This is a budget declaration change in a new root, not a gate change; every floor
is untouched and the historical roots keep their frozen declarations.

## The multi-file task: `repo`

`new_tasks_repo.py` adds a second new task, on a different axis from `ledger2`: the *file* axis, not
the *trap* axis. The workspace has five files - `README.md` (wire-format spec), `varint.py` and
`store.py` (the buggy modules), `test_public.py` (assertions that pass with the bug present) and
`solution.py` (a re-export shim, because the relay always scores `workspace/solution.py`).

- The bug spans modules: `varint.encode` only writes the low 7 bits, `varint.decode` shifts by 8, the
  store uses `len(account)` (characters) instead of the UTF-8 byte length, and it does not zigzag. A
  fix in one file only counts when the other agrees.
- Public tests use single-byte values only, so they stay green; the hidden checks do the work.
- Verified the same way as `ledger2`: **reference 78/78, buggy starter 43/78.**
- Scoring runs through the root's superset scorer, verified offline against both workspaces before any
  inference (`repo through superset CLI: reference 78/78, starter 43/78`).

## Item 3 mitigation: adopted for Strata, measured at n = 10

Six fresh roots on the same 12 GiB template (`ledger_budget.py`), one declared change each:

| Arm | Sessions | Score | Engine truncation diagnostic | Ending |
|---|---|---|---|---|
| A `reasoning_budget_tokens: 6144` | v19-1, v19-2, v19-3 | **70/70, 70/70, 70/70** | 0, 0, 0 | toolUse, stop, stop |
| B `reasoning_close_retry: true` | v20-1, v20-2, v20-3 | **70/70, 70/70, 70/70** | 0, 0, 0 | stop, stop, stop |

Pre-change, the same template family produced the diagnostic in **3 of 13** sessions and every session
carrying it scored below 70/70. After the change: **0 of 6**, all perfect, in 165-253 s per session.
Arm A's thinking blocks still reach 20-25 k characters (~5-6 k tokens), so the model is not being
starved; the budget ends the thinking and the model answers from there, which is the documented
behaviour. Session cost and token use are unchanged (9.4-15.4 k tokens versus the baseline's 2-16 k).

Honest limits: **three sessions per arm cannot establish a rate change** - a 0/6 versus 3/13 comparison
is not significant on its own. What *is* established is the mechanism (item 3), the fact that both fixes
are one-line, reversible, config-level, and compatible with a perfect score, and that the diagnostic
line is an engine-emitted hard signal rather than a score proxy. Recommendation: put
`reasoning_budget_tokens` in the Strata ledger declaration (it bounds the failure deterministically -
the engine then guarantees room to answer) and keep `reasoning_close_retry` as the safety net for the
ending it covers; re-measure on the next ledger batch rather than trusting n=3.

One incidental confirmation from arm A: v19-1 scored 70/70 while reporting `clean_finish=false`,
`exit 143` and `quota_unknown` - the same clean/exit/quota reading caveat as item 3.

### The rate: ten fresh roots, and the cut stops mattering

`ledger_rate.py` repeated arm A's declaration (`reasoning_budget_tokens: 6144`) in ten fresh roots on
the same 12 GiB template:

| | Pre-change (13 sessions) | With the thinking budget (10 sessions) |
|---|---|---|
| Sessions at 70/70 | 10 (77 %) | **10 (100 %)** |
| Sessions carrying the engine's truncation diagnostic | 3 | **2** |
| Score of the truncated sessions | **7/70, 7/70, 64/70** | **70/70, 70/70** |
| Session time | 79-337 s | 115-242 s |

**The important line is the last two.** The mitigation does not stop the reply from being cut while
thinking - it still happened twice in ten runs - it **decouples the cut from the failure**. With the
thinking bounded, the model has already acted before the cap arrives, so the truncated turn is the
closing one and the artifact is complete; both truncated sessions scored 70/70. Before the change, a
truncation always landed mid-work and cost the run.

Honest statistics: 3/13 failures versus 0/10 is **not significant on its own** (Fisher exact one-sided
p = 0.161, two-sided 0.229). The argument rests on the mechanism - the same diagnostic fires and no
longer costs anything - plus the engine's own recommended remedy. Recommendation stands: put the
budget in the ledger declaration. Lifecycle note again: 4 of the 10 perfect sessions reported
`clean_finish=false` or `exit 143`.

## Live validation: both new tasks run end to end (`newtasks-20261008-v1`)

One Qwen3.6-35B-A3B sweep, five tasks, wall 1,374 s with the per-task wall unchanged at 720 s:

| Task | Live score | Reading |
|---|---|---|
| events | 74/76 | below its own historical 76/76 x3 - a weaker sweep than usual, not a harness effect |
| ledger (frozen) | 66/70 | at the bottom of its 68-70 range |
| paths | 75/75 | saturated as always |
| **ledger2** | **212/226** | failing profile: the 12 Unicode-digit traps + `cents-shape/'١٢'` + frozen case 19 |
| **repo** | **75/78** | residual defect named below |
| | **502/525 = 95.6 %** | |

Two things this establishes:

1. **The offline re-score is a valid ranking device.** The live `ledger2` class profile - Unicode
   digits plus the two Arabic-Indic cents shapes, nothing else - is *the same profile* the offline
   re-score produced for this configuration's four saved artifacts (`v24` 208 with `unicode-digit` 12,
   `v25` 209, `v26-1` 225, `v26-2` 220). A live run lands inside that range at 212 and fails the same
   trap classes, check for check.
2. **`repo` reports a named defect instead of a number.** Its three misses are
   `store/reopen/multi-byte`, `store/reopen/unicode` and `store/length-prefix-is-bytes` - i.e. the
   model fixed the varint boundaries and the zigzag path (its public tests and all the varint checks
   pass) and left `len(account)` in the append path, so a multi-byte account name corrupts every
   subsequent record. A score says 96 %; the labels say *which line is still wrong*.

So the state of the measurement is: the ledger ranks (226 checks, verified live and offline), the
multi-file axis discriminates (78 checks, with labels), and the remaining re-baseline work is
mechanical - run both across the top group rather than one configuration.

### The re-baseline, and the cleanest evidence in this report

`newtask_run.py` ran the same five tasks for three more configurations (one root each):

| Configuration | events 76 | ledger 70 | paths 75 | **ledger2 226** | **repo 78** | five-task total |
|---|---|---|---|---|---|---|
| **Kolibri-1 78B** | 76 | 69 | 75 | **226** | **78** | **524/525 = 99.8 %** |
| Nemotron-3.5-Lightning-30B | 76 | 67 | 75 | 223 | 75 | 516/525 = 98.3 % |
| Qwen3.6-35B-A3B (plain) | 74 | 66 | 75 | 212 | 75 | 502/525 = 95.6 % |
| Swift Bonsai 2 PQ2 | 76 | **7** | 75 | 226 | **43** | 427/525 = 81.3 % |

**Kolibri-1 is the only configuration that solves the multi-file task perfectly, and the only one
perfect on the 226-check battery.** On the frozen suite Kolibri (99.5 %) sat behind Swift (100 %); on
the two new axes it leads by 97 checks over Swift, whose 43/78 `repo` means it made no effective
cross-module fix at all. That is the point of adding tasks: the ranking was an artefact of two
saturated tasks plus a five-check ledger, and it does not survive finer measurement.

**Swift is the demonstration.** In one sweep, on one root, the frozen ledger scored it **7/70** while
`ledger2` - which *contains those same 70 checks, byte-identical* - scored **226/226**. The mechanism
is in its wire capture: three effective turns, and the third used **exactly 12,288 of a 12,288-token
allowance**, so the reply was cut inside its thinking, emitted no tool call, and the loop ended after
6 tool executions with the artifact barely touched. Its `ledger2` run made 24 turns and 25 tool calls
and completed every check.

That is the whole thesis of this document in one comparison: **the lab's best-scoring model produced a
7/70 because of a harness constant, not because it failed the task.** It also means the historical
"Swift 70/70, 70/70" plus this 7/70 should be read as 3/3 capability with one lost sample, and that
any rate table without this attribution understates every long-thinking model.

**`repo` measures a different axis.** Swift scored **43/78 - exactly the starter's score**, i.e. it made
no effective cross-module fix at all, while Qwen3.6 and Nemotron each landed at 75/78 (both missing
only the UTF-8 byte-length class). A model that is perfect on 226 single-function traps and 76/76 on
`events` cannot repair a three-module wire-format bug. That is the first genuinely orthogonal
discriminator the suite has produced.

Kolibri's first attempt aborted after three tasks: the runner treats the engine's `quota_unknown`
usage gap as fatal, and Kolibri hits it. That is a runner declaration, not a task result - the same
change `candidates-20261007-v8` already carries - so the sweep was repeated in a fresh root with
`quota_unknown` declared non-fatal.

## Provisioning: context, host window and thinking budget - verified from the run

`provision-20261008-v1` (Qwen3.6 plain, three frozen tasks, one declared change-set) raises the served
context 32,768 -> **131,072**, the host's `contextWindow`/`maxTokens` 32,768/12,288 -> **131,072/32,768**
in the descriptor the harness writes, and adds the llama.cpp thinking budget
`--reasoning-budget 6144 --reasoning-budget-message "Stop thinking and act now: ..."`, which is the
llama.cpp equivalent of the Strata knob that took the ledger to 10/10.

Every part of that is read back from the run's own artifacts, not assumed:

| What | Evidence | Value |
|---|---|---|
| served context | `n_ctx_slot` in each of the five session server logs | **131,072** |
| launch command | `status.json` command per session | `-c 131072`, `--reasoning-budget 6144`, wrap-up message present |
| host window | `config/models.yml` the harness wrote, all three task sessions | `contextWindow=131072`, `maxTokens=32768` |
| flag acceptance / hang risk | server logs + all three tasks completing | no unknown-argument errors, **no hang** (the upstream `--reasoning-budget` hang reports did not reproduce on b11461) |
| task outcome | the three evaluations | events **76/76**, ledger **67/70**, paths 75/75 = **218/221**, all clean |

That is 3 checks better than the same configuration ran unprovisioned in `newtasks-20261008-v1`
(74/76, 66/70, 75/75 = 215/221), at roughly double the wall per task (449/414/159 s versus 184/136/245 s)
- consistent with a bounded thinking budget producing more, shorter deliberation turns rather than one
long one. n = 1, so treat the 3 checks as indicative and the *verified provisioning* as the result.

The context raise also retires the reason the lab could never measure what the RAM upgrade bought: a
task whose prompt exceeds 32k can now run, which is what the queued long-context task needed. And it is
the same change the **Strata** runs needed - their 32,768 window is what the six context witnesses in
the census died against.

**Correction, 2026-10-09:** the raised window turned out to be necessary for the long-context task
only at *some* models. `newtasks-ctx-20261009-v11` ran it at 32,768 and scored 40/40 - the task reads a
235 KB module in chunks, so its peak prompt was 16,111 tokens over 11 requests. Measured peaks:
**Swift 16.1k** (passed at 32,768), Qwen3.6 15.5k-26.8k, Kolibri 20.4k, versus **MiniCPM 40.3k** and
**Nemotron 43.2k**, which are the two models whose `longctx` genuinely needs the larger window. See
"Provisioning is per model, and `longctx` is cumulative" below.

## Strata at a raised context: works, and the cost is the headroom

`strata-ctx-20261008-v*` raises the engine's `--max-context` 32,768 -> **65,536** (verified: the
engine's own startup line reads `context 65536 tokens`) and inherits the validated
`reasoning_budget_tokens: 6144`. Both floors stayed armed throughout:

| Run | Score | Clean | Session s | Min free physical | Min GPU free | Truncation diagnostics |
|---|---|---|---|---|---|---|
| v42 | **70/70** | yes | 235.6 | 4.11 GiB | 0.80 GiB | 0 |
| v43 | **70/70** | yes | 149.2 | 5.36 GiB | 0.82 GiB | 0 |
| v2 | 70/70 | no | 180.8 | 3.48 GiB | 0.77 GiB | 0 |
| v3 | 70/70 | no | 278.7 | 3.66 GiB | 0.79 GiB | 0 |
| v1 | 7/70 | no | 169.2 | 3.85 GiB | 0.79 GiB | 0 |

**Four of five valid runs at 70/70 with zero truncation diagnostics** - the context cause is gone, and
the ledger no longer dies at the 32.8k prompt ceiling. (v41 is an aborted build from a driver assertion,
kept with a README so the gap is not read as a missing run.)

The one 7/70 is a harness bug, not a model result, and its diagnosis is worth keeping: the session
ended at 169 s with `final_text` empty, `exit 143` and `quota_failure=quota_unknown`. The harness's
execute loop terminates on `budget.failure`, and the relay's `Budget.account` sets exactly that value
when the engine reports no usage - an engine reporting gap, not a task outcome. The same condition
landing *after* the work cost nothing (v2 scored 70/70 with it). Fixed at the right layer by wrapping
the relay's `Budget` in the root so a usage gap is counted instead of fatal; v42 and v43 then ran clean.
This is the second place the same gap had to be declared non-fatal, and the first place where the fix
belonged to the *relay* rather than the runner's sweep guard.

**The cost is the headroom.** Free physical falls to 3.5-5.4 GiB at 64k context, against ~10 GiB at
32k - a ~5 GiB price against a 3 GiB floor. The engine's own arithmetic puts 8-bit KV at ~13.7 KB per
token (~0.85 GB at 64k), so the rest is the prefill path: the engine reads prompts in chunks of up to
8,192 tokens and sizes those buffers from the context. 64k is therefore affordable but leaves the
ledger's reliability margin thin; a larger context on this pack would need the prefill chunk bounded
first.

## The provisioned six-task sweep: 551/565, and what it says about each axis

`newtasks-ctx-20261008-v1` (Qwen3.6 plain, raised context + thinking budget, six tasks, wall 1,839 s):

| Task | Score | Clean | Seconds | Tokens |
|---|---|---|---|---|
| events | 76/76 | yes | 318.8 | 12,617 |
| ledger (frozen) | **70/70** | yes | 355.5 | 13,701 |
| paths | 75/75 | yes | 215.5 | 8,341 |
| ledger2 | 212/226 | yes | 250.6 | 9,566 |
| repo | **78/78** | yes | 392.9 | 15,182 |
| longctx | **40/40** | yes | 108.6 | 3,817 |
| | **551/565 = 97.5 %** | | | |

Three things follow:

1. **The frozen three are perfect for the first time in this configuration** (221/221, all clean).
   Unprovisioned, the same model produced 215-219/221. That is the clearest single piece of evidence
   that the reply cap, the 32k window and the empty thinking-budget were costing real checks.
2. **`repo` went from 75/78 to 78/78** - the cross-module task that Qwen3.6 previously missed only on
   the UTF-8 byte-length class. Either the provisioned run gave it the room to finish that audit, or
   the earlier 75/78 was variance; n = 2, so both remain open, but the direction matches the ledger.
3. **`longctx` is solved first try and cheap**: 40/40 in 108.6 s with 3,817 tokens for a 65k-token
   corpus, i.e. the model greps and reads selectively rather than ingesting the module. **Honest
   caveat: at n = 1 this task is saturated for this model** - the same criticism I levelled at
   `events` and `paths`. What it does establish is that the raised window is *usable live* (a 222 KB
   workspace is now workable at all, which it was not at 32k) and that a minimal-edit rule is
   checkable. To make it discriminate it needs a harder variant: more planted defects across a larger
   corpus, or a defect that requires reasoning over several distant functions rather than finding one
   wrong body.

The residual shortfall is now one thing: **the 14 Unicode-digit checks in `ledger2`** (the twelve
`unicode-digit` traps plus `cents-shape/'١٢'`, and frozen case 19). Everything else in the suite is
clean for this configuration, so `ledger2` is carrying the discrimination for these models on its own -
which is exactly why it was worth building.

## The fast models on the full suite: speed bought on the axes that do not discriminate

The two fastest configurations on the frozen three were run through the same six-task provisioned root
(raised reply cap 32,768, context 131,072, `--reasoning-budget 6144`):

| Config | events | ledger | paths | ledger2 | repo | longctx | Total | Agent s | s/task | tok/s |
|---|---|---|---|---|---|---|---|---|---|---|
| **Qwen3.6-35B-A3B** (provisioned) | 76 | **70** | 75 | 212 | **78** | **40** | **551/565 = 97.5 %** | 1,642 | 274 | 39 |
| **Kolibri-1 78B** (5 tasks) | 76 | 69 | 75 | **226** | **78** | - | 524/525 = 99.8 % | 2,150 | 430 | 34 |
| Nemotron-30B (5 tasks) | 76 | 67 | 75 | 223 | 75 | - | 516/525 = 98.3 % | 2,758 | 552 | 31 |
| MiniCPM5-2B | 76 | 67 | 75 | 144 | 43 † | **40** | 445/565 = 78.8 % | 1,059 | 176 | **122** |
| gpt-oss-20b | 74 | 66 | 75 | 202 | **0** ‡ | 15 | 432/565 = 76.5 % | 953 | **159** | 24 |
| Swift Bonsai 2 (5 tasks) | 76 | 7 * | 75 | **226** | 43 | - | 427/525 = 81.3 % | 1,678 | 336 | 49 |

\* the reply-cap truncation victim from the cause-1 section. † ended on `length` at exactly its
48,000-token session quota after 31 turns and 34 tool calls, with no effective edit: it looped until
the harness cut it. ‡ every file parses but the module no longer imports, so all 78 checks fail - it
finished cleanly in 20 turns and broke the workspace.

**The ranking inverts with the bar.** gpt-oss-20b is the fastest thing here (159 s/task) and MiniCPM
the fastest at scale (176 s/task, 122 tok/s) - and both fail every hard axis. The speed was bought on
the tasks that do not discriminate: two saturated single-file tasks plus a 70-check ledger. The fastest
configuration that is *successful on the whole suite* is **Qwen3.6 with the provisioning** - the only
one that passes both `repo` (78/78) and `longctx` (40/40) - and it is 1.6x faster per task than the
only other qualifier, Kolibri (430 s/task, 99.8 %, 226/226 on ledger2, 78/78 on repo, longctx unrun).

One incidental pattern worth noting: MiniCPM's frozen three came out at 218/221 (98.6 %) with 122 tok/s,
the best quality-per-second in the lab - its failures are a budget loop on `repo` and a weaker ledger2
session (144/226) than its own frozen ledger run (67/70) in the same sweep. Per-task artifacts are
separate sessions, so within-model spread across tasks is real and n = 1 per task is not a verdict.

## MiniCPM's `repo` failure is thrashing, not budget: the quota test refutes its own hypothesis

MiniCPM's `repo` had ended on `length` at exactly its 48,000-token session quota, which looked like a
budget stop. So its root was rebuilt with the quota doubled to 96,000 and the same provisioning:

| Run | repo | clean | session s | tokens | tool calls | turns | last stop |
|---|---|---|---|---|---|---|---|
| quota 48,000 | 43/78 | no | 409.0 | 48,000 | 34 | 31 | `length` (at quota) |
| **quota 96,000** | **0/78** | no | **720.2** | **69,774** | **73** | **68** | `error` |

Doubling the budget did not recover the task: it spent more, ran **18x longer than the other tasks in
the same sweep**, made 73 tool calls, and produced a **worse** artifact (0/78 - the module does not
import at all). That is thrashing, not a budget limit, and it retires the "quota blocked it"
explanation. It also produced the first `720 s` task-wall hit in the new-task family, and the same
`quota_unknown`-as-budget-failure path that killed a Strata run - the harness terminates on
`budget.failure`, and this engine reports no usage intermittently.

The rest of that sweep, for completeness: events 76/76, ledger 66/70, paths 75/75, ledger2 **199/226**
(up from 144/226 - a different session, so per-task n = 1 is noisy for this model), longctx 40/40,
total **456/565 (80.7 %)**, at 99.7 tok/s.

## Kolibri on the full suite: a dead heat on score, and 1.8x slower

`newtasks-ctx-20261008-v4` (Kolibri-1 78B, provisioned, six tasks, wall 3,312 s):

| Task | Score | Clean | s | tokens |
|---|---|---|---|---|
| events | 76/76 | yes | 446.5 | 14,279 |
| ledger | **70/70** | yes | 531.4 | 17,836 |
| paths | 75/75 | yes | 608.4 | 21,337 |
| ledger2 | 212/226 | yes | 417.0 | 14,128 |
| repo | **78/78** | no (wall) | 720.0 | 24,381 |
| longctx | **40/40** | yes | 248.0 | 8,728 |
| | **551/565 = 97.5 %** | | 2,971 agent | |

**Identical to Qwen3.6's 551/565 - and Qwen3.6 does it 1.8x faster** (1,642 vs 2,971 agent seconds;
274 vs 495 s/task), with the same `ledger2` score of 212/226 and the same failing profile (the 14
Unicode-digit checks). Kolibri's earlier 226/226 on that battery was a different session's artifact:
session-to-session spread on the finer battery is real, and n = 1 per task is not a verdict.

Two mechanical points from this run:
- **`repo` hit the 720 s wall** (44 turns, 60 tool calls, 24,381 tokens, cut on a `toolUse` turn) - yet
  the artifact was already complete, so the score stands at 78/78. Kolibri and MiniCPM both hit that
  wall on `repo`; like `longctx`, that task wants a declared longer wall for the slower models.
- Its frozen three were **perfect (221/221)**, so on the tasks the old protocol could actually resolve,
  Kolibri and Qwen3.6 are now indistinguishable - which is exactly why the new axes were needed.

Six-task ranking, all measured live: **Kolibri-1 551/565 at 495 s/task** = **Qwen3.6 551/565 at
274 s/task** > Nemotron 516/525 (unprovisioned, 552 s/task) > MiniCPM 456/565 (256 s/task) >
gpt-oss-20b 432/565 (159 s/task) > Swift 427/525 (336 s/task).

## Strata 0.1.41 A/B: the upgrade is neutral, one card-specific hint is a regression

Strata **v0.1.41** shipped 2026-10-08 12:14 UTC with a headline aimed at our regime - *"Windows, model
bigger than RAM: prompts about twice as fast"*. It was staged the lab's way (copytree of the pinned
0.1.40.3 install, git checkout of the tag, sha256-verified release asset; `staged-strata-20261008/`)
and measured on the ledger at the 64k / 12 GiB / budget-6144 declaration. **All fifteen runs scored
70/70**, so the metrics that decide are the engine's own rates, read from its logs:

| Arm | n | cold prompt (9,854-token system prompt) | per-request rate (median) | GPU cache hit, first -> last |
|---|---|---|---|---|
| baseline **0.1.40.3**, same declaration | 5 | 632.3 (615.9-657.0) | 70.3 (68.8-73.8) | 48.5 % -> 53.8-69.2 % |
| **A: 0.1.41, defaults** | 2 | 636.4 (615.9-656.9) | 68.8 (68.1-69.4) | 49.3 % -> 59.1-65.1 % |
| **B: 0.1.41 + `--expert-cache 1500`** | 3 | **579.6 (identical in all three)** | 66.3 (62.9-71.4) | **41.2 %** -> 51.0-52.6 % |
| **C: 0.1.41 + `STRATA_ROUTE_RESIDENT=1`** | 3 | 643.2 (615.9-656.9) | 69.8 (68.2-71.8) | 49.3 % -> 62.0-62.5 % |
| *(C, first batch - contaminated, see below)* | 3 | 579.6 | 64.9 | 41.3 % -> 46.8-52.7 % |

- **A: the upgrade alone is neutral** on every rate (636 vs 632 cold prompt, 68.8 vs 70.3 per request,
  49.3 vs 48.5 cache) and its GPU expert cache holds **2,425 experts against 2,407** - the buffer
  savings from #1454 showing up. Take 0.1.41 for the *behavioural* fixes it carries: the hung-engine
  watchdog (`STRATA_ENGINE_STALL_S`) that addresses the stalled sessions we recorded, `<function= NAME>`
  tool-call parsing, the q8_1 clamp. Not for speed on this box.
- **B is a regression here**: a deterministic 579.6 tok/s cold prompt in all three runs against
  615.9-657.0 for every other arm, and 41.2 % first-request cache hit against 49.3 %. The release note
  says the hint helps where the *automatic* cache is bigger than useful; our `--resident-budget-gib 12`
  keeps the RAM side small, so shrinking the GPU side just streams more experts. Rejected for our config.
- **C shows no gain** (69.8 vs 68.8 per request, within the spread): the +4.1 % decode the note claims for
  RTX 5070 + Q2_0 does not reach a prefill-dominated workload - our suite reads 43.6 tokens per token
  written, so a decode-only improvement barely moves task time.
- **Why the headline cannot apply here**: it targets prompt reads that *bypass the cache*, i.e. experts
  streamed from disk. Our prompt path is RAM-bandwidth bound - ~630 tok/s, far above a disk-bound read -
  and the disk-streaming configuration (plain `--mmap-experts`) drove free physical to 1.92 GiB in
  October and was never runnable under the 3 GiB floor.

**Two operational lessons, both paid for.** (1) The engine config file lives in the *engine install* and
is shared by every root that uses it, so an arm that does not state a value inherits the previous arm's -
arm C's first batch inherited B's `--expert-cache 1500` (all six runs showed an identical 579.6 cold
prompt). The driver now declares the expert cache for *every* arm and the built config is read back
before the run; the contaminated batch is preserved with a README. (2) A batch launched with a bare
shell `&` is reaped when the tool call returns, so C5/C6 never started and C4's record was lost between
completion and write-up - batches now go through the harness's background-job mechanism, and metrics can
be recomputed from the run artifacts at any time (`strata-ab-all.json`).

## What others found (and what applies)

Compiled in `local-llm-lab/HARNESS-TWEAKS-2026-10-08.md`, with sources. The short version:

- **OpenHands #3992** (closed; nudge policy #3997 unmerged) documents the mirror-image class - a
  content-only turn treated as finished - and their 2x2 is the useful part: OpenHands 1/4 completions
  versus **mini-SWE-agent 3/4 with the same model**, because mini-SWE-agent's format-error loop
  nudged-and-retried the same turns. Their independent re-reproduction ran with **577 completion tokens
  at 73k/255k context**, so their case is neither length nor context. **Applies partially**: our
  prose-quits are completion summaries rather than mid-task plans, so a nudge would mostly get "DONE" -
  worth one measured experiment, not adoption.
- **llama.cpp #20837** (Qwen3.5 printing tool calls inside thinking, so the client sees none):
  **not our failure mode** - a scan of **324 transcripts** for five markup shapes inside thinking found
  zero, with or without a tool call in the same turn. Strata's rescue fix is for a real problem, just
  not ours.
- **llama.cpp #22717 / forge #54** (`--reasoning-budget` hanging in some 2026 builds): the reason the
  provisioning run above measures a generation instead of trusting the flag.
- **SWE-bench Verified** evaluates every model with mini-SWE-agent in a minimal bash environment - the
  community's comparability direction is *less* scaffold, which is why the census splits model from
  harness instead of adding scaffold to fix a measurement.
- This build's own help confirms **context shift is off by default** (so KV-shift corruption is not one
  of our causes) and `--cache-reuse` uses KV shifting - deliberately left at 0.

## Ranking convention and the three declarations of 2026-10-09

Three things changed on Kevin's instruction. Two of them move bars, and this lab's rule is that
loosening a bar must be loud, so each is declared here and in the changelog.

1. **The 6 GiB worker-private cap is removed** (`local-decisions-20260925-v1/run.py`,
   `WORKER_PRIVATE_CAP_GIB = None`, was 6). It stopped nimble at a measured 6.94 GiB private floor while
   every system floor passed. Not changed: the eligibility gate (>=9 GiB physical / >=8 GiB commit /
   >=0.5 GiB GPU free), the runtime floors (3 / 2 / 0.5 GiB), the paging-pressure counter, and every
   historical root's record - those results are frozen evidence and keep the value they ran under.
2. **`events` and `paths` are retired from ranking.** The census puts them at 5/76 and 3/75 splitting
   checks in the top group, so they absorb budget and manufacture ties. The ranking metric is the
   discriminating subset **ledger 70 + ledger2 226 + repo 78 + longctx 40 = 414 checks**
   (`RANKED_TASKS` in `newtask_run.py`; `ranked_table.py` regenerates the table below from each root's
   own evidence, into `ranked-20261009.json`). They still run, as sanity checks.
3. **Each model is reported at the context it can afford**, and the context travels with the row:
   131,072 for the six local models, 32,768 for the exempt Swift, 65,536 for Strata.

| configuration | engine | ctx | ranked / 414 | six-task |
|---|---|---|---|---|
| **Qwen3.6-35B-A3B** (`ext-v12`, nine-task run) | llama.cpp | 131,072 | **414/414** | 565/565 |
| **Qwen3.8-Flash-Next Q2_0** (Strata, declared combination of v2+v3+v4) | Strata | 65,536 | **414/414** | 565/565 |
| Qwen3.6-35B-A3B (`ctx-v8`, repeat) | llama.cpp | 131,072 | 411/414 | 562/565 |
| Kolibri-1 78B (`ctx-v4` and `ctx-v9`, identical) | llama.cpp | 131,072 | 400/414 | 551/565 |
| Qwen3.6-35B-A3B (`ctx-v1`) | llama.cpp | 131,072 | 400/414 | 551/565 |
| Nemotron-3.5-Lightning-30B (`-r1` / `ctx-v7`) | llama.cpp | 131,072 | 394 / 393 | 545 / 544 |
| Swift Bonsai 2 PQ2 (`ctx-v11`, exempt) | Prism fork | 32,768 | 379/414 | 530/565 |
| gpt-oss-20b (`-r1`) | llama.cpp | 131,072 | 377/414 | 528/565 |
| MiniCPM5-2B (`-r1`) | llama.cpp | 131,072 | 374/414 | 522/565 |
| MiniCPM5-2B (`ctx-v5` / `ctx-v3`) | llama.cpp | 131,072 | 305 / 294 | 456 / 445 |
| gpt-oss-20b (`ctx-v2`) | llama.cpp | 131,072 | 283/414 | 432/565 |

The ranked metric sharpens the picture the six-task total blurred: the two perfect rows are perfect on
the *discriminating* checks, the exempt model is 35 checks behind them rather than 35 of 565, and the
two weakest models are 100+ ranked checks adrift. The nine-task view (only Qwen3.6 and Strata have one)
is unchanged at **692/693 each**; the sweeps now running extend it to the other five models.

## What is queued, and what needs a decision

1. **Cause 2 (context exhaustion): DONE** in `provision-20261008-v1` - server `-c` 131,072 *and* the
   host descriptor 131,072/32,768, both verified from the run. The frozen harness stays untouched: the
   host window is patched through the harness's own `configuration()` from inside the new root, so every
   historical root keeps its manifest. Next: re-run **Strata** on the raised context, since its 32,768
   window is what those six witnesses died against.
2. **Strata ledger rate at n >= 10 with the thinking budget.** The 6/6 at 70/70 with zero diagnostics
   is not a rate. Adopt `reasoning_budget_tokens` in the ledger declaration in a new root and repeat.
3. **Re-baseline the top group on the new tasks.** `ledger2` and `repo` both need live runs across
   Qwen3.6 plain/MTP, Kolibri, Swift, Nemotron and Strata - the offline re-score ranks historical
   *artifacts*, which is a different (and weaker) claim than a fresh run.
4. **Convert the cap-arm single sweeps into rates**: MiniCPM and gpt-oss each ran once at the raised
   cap. Both now need n >= 3 to say the collapse class is gone rather than quiet.
5. **A long-context task.** The probe proves the capability (3/3 at 262k); no task measures it. This is
   the natural fourth task and it is blocked on decision 1, because it cannot exist under a 32k protocol.
6. **Retire `events` and `paths` from ranking**, or replace them with harder variants. They return a
   constant for every configuration above ~95 %, which is why a 2-check ledger difference was
   mistaken for a capability ranking for a week.
7. **Judge the trap classes, not just the score.** `unicode-digit`, `unicode-space`, `csv-shape`,
   `header` and `cents-shape` are separable behaviours; the profiles are already in
   `rates-20261007.json` under `new_battery`.

**Status of that list, 2026-10-09** (kept as written above; this is what the week actually did):

| # | Item | Status |
|---|---|---|
| 1 | Cause 2 provisioning | **DONE** - `provision-20261008-v1`, read back from the run; the Strata raised-context run followed ("Strata at a raised context"). |
| 2 | Strata ledger rate at n >= 10 | **DONE** - "Item 3 mitigation: adopted for Strata, measured at n = 10". |
| 3 | Re-baseline the top group on the new tasks | **DONE for the six local models and for Strata.** `newtask_strata.py` ports the suite to the Strata engine (root-local scorer copy, 4 GiB resident) and Strata scores **692/693 - identical to Qwen3.6's best, confirmed at n=2** over `strata-newtasks-20261009-v2`/`-v3`/`-v4`. See "Strata: the new-task port". |
| 4 | Cap-arm sweeps -> rates (MiniCPM, gpt-oss) | **DONE at n=3 each.** MiniCPM 445 / 456 / **522** of 565 (`repo` 43/0/**68**); gpt-oss 432 / **528** / partial-`-r2` (its `paths` scorer exited abnormally and `longctx` hit the frozen module - **unscored, not failed**, with a targeted `-r3` completing them). Both models are now the widest spreads in the family: see "Repeatability", readings 1, 5 and 6. |
| 5 | A long-context task | **DONE** - `longctx` ran for every model (40/40 for four of them) and `longctx2` was authored, verified and run. |
| 6 | Retire `events` and `paths` from ranking | **STILL OPEN - a decision**: the refreshed rate table still shows them splitting on 5/76 and 2/75 checks in the top group. |
| 7 | Judge the trap classes | **DONE for `ledger2`** - every run now records `failing_traps` per case; `repo2` extends the same idea with four labelled classes. |

New open question raised by tonight (not on the old list): **whether the comparison series reports each
model at the context it can afford** - see the RESUME and "Provisioning is per model".

## Strata: the new-task port

**Result: Strata scores 692/693 on the nine-task suite - identical to the best local configuration.**
`strata-newtasks-20261009-v2` ran all nine batteries in **1,959 s** with no resource stop, and the six
that the in-flight scorer aborted were re-scored offline from their recorded artifacts (deterministic
inputs; see `offline-rescores-20261009.json`):

| task | events | ledger | paths | ledger2 | repo | longctx | repo2 | perf | longctx2 |
|---|---|---|---|---|---|---|---|---|---|
| Strata (v2 / offline re-score) | 76 | 70 | 75 | **226** | **78** | **40** | **54/55** | **33** | **40** |
| Qwen3.6 `ctx-v8` / `ext-v12` | 76 | 70 | 75 | 226 | 78 | 40 | 54/55 | 33 | 40 |

The two configurations agree on **every task**, and both miss the same single check. So a streamed
Q2_0 pack on a 12 GB card (4 GiB resident, experts read from disk) equals a fully resident 35B-A3B
Q4_K_M on this suite - the disk-bound engine pays in wall time, not in score, at least at these
context sizes.

**Confirmed at n=2 by a fresh post-fix run.** `strata-newtasks-20261009-v3` re-ran six batteries with
the root-local scorer and reproduced five of them **exactly** - ledger2 226/226, repo 78/78, longctx
40/40, repo2 54/55 (the same single miss), perf 33/33 - which is also what validates the offline
re-scores of v2's artifacts. `longctx2` (v2: 40/40) is running in `strata-newtasks-20261009-v4`
because the v3 sweep stopped first: **the 4 GiB declaration leaves the 3 GiB physical floor marginal.**
Session minima across v3 were **2.94-5.11 GiB**, and `perf`, whose evaluator materialises 2,000,000
intervals, crossed it at **2.94 GiB**. The monitor stopped that session *after* its artifact was
already complete (33/33 - the lab's documented "external kill is not a wrong artifact"), and the
session's own STOP then halted the sweep before the last battery, which is the sweep behaving as
designed. Engine loads in v3 were 16-18 s. If the Strata track continues, **2 GiB is the safer
declaration**.

**Attributed, not merely observed.** Dumping the scorer's own stack 45 s into the hang gives the
cause: the artifact's `codec.encode` is

```python
while True:
    byte = value & 0x7F
    value >>= 7
    out.append(byte | 0x80 if value else byte)      # no terminator
```

- it never breaks, so the first `class1` byte-length case loops forever. A missing loop terminator is
exactly the defect class the harness's 30 s ceiling exists to bound, and it is why both of my
re-score attempts (30 s and 600 s) hung as well. The battery itself is fine: the same cases score
54/55 and 78/78 on other artifacts.

**One 2 GiB cell is a model result, not a gap.** In `strata-newtasks-20261009-v5` (the 2 GiB
declaration) `repo2` came back `evaluation_timeout: true` with `exit 143` after its artifact was
complete, and re-scoring that artifact **outside** the harness ran the full **600 s** wall with no
output at all - the battery hangs on it, which is why the in-flight 30 s ceiling tripped. So the cell is
recorded as a **failure of the artifact**, not recovered, and two things stay open at n=1: whether the
thinner 2 GiB expert pool caused it, or whether it is sampling variance - the Strata config still pins
**no seed**, unlike the llama-server roots. Operationally it also shows why a pathological artifact can
halt a sweep: the session writes STOP after an unclean cleanup, by design, and the recovery is a fresh
root for the remaining tasks (that is what `v6` is).

**First attempt tripped a floor, and the reason was a declaration, not the port.**
`strata-newtasks-20261009-v1` ran `events` for about 90 s - the engine loaded in **31.7 s** and
decoded at **66-79 tok/s** - and then the monitor stopped the session with free physical at **3.18 GiB
against the 3 GiB floor** (GPU fine: 1.52 GiB minimum free, a 0.5 GiB floor). The template's
`--resident-budget-gib 12` was declared for the 64 GB platform as "an order of magnitude more headroom
than the 3 GiB floor needs"; the mmap'd expert pages plus the file cache spent that headroom on the
actual workload. The port now declares **4 GiB** (the lab's documented-safe value from the 32 GB days,
which held 9.6-10.5 GiB free) in a **new root**, `strata-newtasks-20261009-v2`, because a resource stop
leaves STOP in its root and the lab's rule is a clean cutover rather than reuse. The trade is real and
declared: fewer resident experts means more streaming, i.e. slower decode - a rate, not a score. Every
session then ran clean at 4 GiB.

**The scorer had to be a root-local copy, and that is why six batteries were initially unscored.**
`score_artifact` (in the harness's `compare_staging_20260922.py`) runs
`python HERE/'staged_tasks_20260922.py' <task> <artifact>`, where `HERE` is the **base module's own
directory**. The Strata template used the harness's base, whose `HERE` is the frozen
`completion-20260923-v1/source` - a module that contains only `events`, `ledger` and `paths` - so
every new battery aborted with `abnormal_evaluator_exit: 1` while the frozen three scored normally. The
port now copies the base module into the root's `source/` as `relay_strata.py`, copies the sibling task
modules beside it, and sets `lab.base` to that copy - exactly the `lab.base=fresh` move the OMP
templates make (their own comment records the same 2026-10-07 lesson: "candidates-20261007-v1 omitted
them and all three tasks returned abnormal_evaluator_exit 2 - unscored zeros, not model failures").
**Verified through the production path before re-running:** `score_artifact` from the root-local base
reproduces six known artifacts exactly - ledger2 226/226, repo 78/78, longctx 40/40, repo2 54/55, perf
33/33, longctx2 40/40 - where the same call previously aborted.

The new-task suite had only ever run on llama-server. `newtask_strata.py` builds a Strata root from the
`strata-20261007-v19-1` template, which already drives `lab.execute(session, 'omp1831', ...)` with its
own engine in the session's place - so the port is the same patch set the OMP builder applies, anchored
on the Strata template's lines. Six declared changes:

1. the superset task module is loaded **by path** (the bare name resolves to the frozen module), so the
   new workspaces exist and the relay scores them;
2. `screen()` writes each new task's extra files (`repo2` gets three modules, `longctx`/`longctx2`
   their `legacy.py`) and a `sweep` action runs the list in order, honouring STOP between tasks;
3. `longctx` uses its own prompt and wall;
4. `lab.base.Budget` is **overridden** - the harness hard-codes `base.Budget(quota=16000, cap=12288)`,
   so the subclass ignores those arguments - and `quota_unknown` becomes a counted usage gap;
5. the host descriptor's `contextWindow`/`maxTokens` are set from the **engine's own declared context**
   (`--max-context 65536` in its config), not from an assumption.
6. the base module is **copied into the root** (`source/relay_strata.py`, with the sibling task modules
   beside it) and `lab.base` points at that copy, so `score_artifact`'s `HERE` resolves to the root's
   superset rather than the frozen module - without it, every new battery is unscored.

Unchanged by design: the engine config, resident budget 12 GiB, VRAM reserve 2000 MiB,
`STRATA_LOOKAHEAD=0`, `reasoning_budget_tokens 6144`, and every floor.

Verified offline before spending a GPU-hour: the ported root's scorers were run against tonight's live
artifacts and reproduce them exactly - ledger 70/70, ledger2 226/226, events 76/76, paths 75/75, repo
78/78, **repo2 54/55, perf 33/33, longctx2 40/40** - and the engine's own `setup --check` exits 0
(63 GB platform, Q2_0 fits). The port's data seams were then read back from the built root: all eleven
task keys present, the nine-task `SWEEP_DEFAULT`, the merged per-task walls, `BudgetRaised` installed,
and the configuration wrapper in place.

Two engine facts found while wiring it, both from the engine's own sources and logs rather than
assumption:

- **`fit_max_tokens` is a declared engine key** (`serve/runconfig.py`: "Shorten a max_tokens that does
  not fit the context instead of answering 400"), and the failure it prevents is real: a session in
  `strata-20261007-v19-1` died on **400** at prompt 31,445 + max_tokens 1,460 against a 32,768 window
  ("requests are never truncated"). The new batteries build far larger sessions, so the port declares
  `fit_max_tokens: true` in the engine config, keeps a pre-change copy in its `evidence/`, and records
  that a clamp remains visible as `clean_finish=false` / `stopReason=length`.
- **The sweep is far cheaper than the older notes suggested.** The 6.5-9.6 tok/s figure describes the
  old 32 GB / 4 GiB-resident, disk-bound configuration. On this box with a 12 GiB resident budget the
  engine decoded at **~70 tok/s with a 52.6 % expert-cache hit** in the session log inspected, and
  engine loads are **36-39 s** across the 58 sessions that recorded `load_seconds`. Nine sessions
  therefore cost roughly six minutes of loading and - at the frozen ledger's 238-337 s per task
  extrapolated to the bigger batteries - about **1.5-3 h**, not "hours by construction". The declared
  walls stay at 3,600 s (5,400 for `repo2`) as ceilings, not estimates.

## Item 4 - Strata v0.1.40.1's tool-call rescue: no observable effect here

The rescue (0.1.40.1) stops a `<tool_call>` written inside thinking or inside a code fence from being
executed. Test: search every Strata session transcript on disk for tool-call markup inside reasoning,
and compare tool-execution counts between engines.

- **26 sessions searched (both engines): zero** events contain tool-call markup inside reasoning.
- Tool executions per session are 5-30 on both engines (v0.1.39: 0, 5, 5, 8, 10, 16; v0.1.40.3:
  5-30 across 20 sessions). The counts track the task, not the engine.
- The harness's relay never surfaces `tool_calls` in message objects (0 across all sessions), so the
  harness reads tool activity from `tool_execution_start` events; that is unaffected.

Conclusion: the fix is correct but **unexercised by this workload** - this model does not write tool
calls inside its reasoning on these tasks, so v0.1.39 and v0.1.40.3 behave identically here. Worth
keeping in mind for models that do (it removes a class of silently-executed stray calls).

## Item 5 - Qwen3.6-35B-A3B long context: PASSES AT EVERY SIZE, EASIER THAN KOLIBRI

Architecture from its own GGUF metadata: `qwen35moe`, 40 blocks, 256 experts with 8 active, context
length 262,144. Same three-planted-codes probe as Kolibri's (`qwen36-ctx-20261007/probe.py`):

| Context | Prompt tokens | Recall | Load | Min free physical | Min GPU free | Max GPU used |
|---|---|---|---|---|---|---|
| 32,768 | 25,547 | **3/3** | 15.6 s | 26.30 GiB | 6.86 GiB | 4.80 GiB |
| 65,536 | 51,027 | **3/3** | 9.6 s | 26.26 GiB | 6.50 GiB | 5.16 GiB |
| 131,072 | 103,107 | **3/3** | 9.6 s | 26.24 GiB | 5.66 GiB | 6.01 GiB |
| 262,144 | 206,147 | **3/3** | 9.5 s | 27.49 GiB | 3.95 GiB | 7.71 GiB |

Same 3/3 result as Kolibri at every size, but with an order of magnitude more RAM headroom (26-27 GiB
free versus ~9), a third of the load time (9.5-15.6 s versus 25-28 s) and a smaller VRAM cost (7.7
versus 7.3 GiB at 256k - comparable there, but the model is also 40 % faster per token). For a
long-context workload on this box, Qwen3.6 is the cheaper of the two.

## The chain's last runs: the best score, the stable repeat, and the runtime that cannot take the raise

`newtasks-ctx-20261008-v7` (Nemotron), `-v8` (Qwen3.6) and `-v9` (Kolibri, a deliberate repeat of
`-v4`) closed the provisioned sweep, and `newtasks-ctx-20261009-v11` closed the exempt one. Six
tasks = 565 checks (events 76, ledger 70, paths 75, ledger2 226, repo 78, longctx 40):

| Root | Model | Wall | Score | Per task |
|---|---|---|---|---|
| **ctx-v8** | **Qwen3.6-35B-A3B** | **1,330 s** | **562/565 (99.5 %)** | 76 / 69 / 75 / 224 / 78 / 40 |
| ctx-v9 | Kolibri-1 | 2,877 s | 551/565 | 76 / **70** / 75 / 212 / 78 / 40 |
| ctx-v4 | Kolibri-1 | 2,971 s | 551/565 | 76 / **70** / 75 / 212 / 78 / 40 |
| ctx-v7 | Nemotron-3.5-Lightning-30B | 3,377 s | 544/565 | 76 / 66 / 75 / 209 / 78 / 40 |
| ctx-v1 | Qwen3.6-35B-A3B | 1,642 s | 551/565 | 76 / **70** / 75 / 212 / 78 / 40 |
| **ctx-v11** | **Swift Bonsai 2 PQ2 (32,768, exempt)** | **1,926 s** | **530/565** | 76 / **70** / 75 / **226** / 43 / **40** |
| ctx-v5 | MiniCPM5-2B | 1,535 s | 456/565 | 76 / 66 / 75 / 199 / **0** / 40 |
| ctx-v3 | MiniCPM5-2B | 1,059 s | 445/565 | 76 / 67 / 75 / 144 / 43 / 40 |
| ctx-v2 | gpt-oss-20b | 953 s | 432/565 | 74 / 66 / 75 / 202 / **0** / 15 |

Five readings:

1. **Kolibri repeats to the check.** `-v4` and `-v9` are both 551/565 with identical per-task values
   (76/70/75/212/78/40) at 2,971 s and 2,877 s. That is the first *reproducible* six-task result in
   the series, and it is the one number tonight that is a point estimate rather than a sample.
2. **Provisioning is per model, and `longctx` is cumulative.** The task reads a 235 KB module in
   chunks across a long session, so what matters is its *peak* prompt, which the wire captures record
   per model - and the peaks straddle 32,768:

   | Model | longctx requests | Peak prompt tokens | Runs at 32,768? |
   |---|---|---|---|
   | Swift | 11 | **16,111** | **yes - measured, 40/40** |
   | Qwen3.6 | 16 / 7 | 15,531 / 26,778 | yes (peak inside the window) |
   | Kolibri | 12 | 20,431 | yes |
   | MiniCPM | 23 | **40,336** | no - exceeds the window |
   | Nemotron | 19 | **43,221** | no - exceeds the window |

   So the raise is load-bearing for MiniCPM and Nemotron and unnecessary for Swift; for Qwen3.6 and
   Kolibri it is marginal. (MiniCPM and Nemotron were only ever run at 131,072, so "no" is read from
   the peak they were *allowed* to use; a 32,768 window would force the harness to compact, and
   whether they would still score 40/40 that way is unmeasured.)
3. **The raise does NOT cost `ledger2` - a claim this section made earlier, now refuted by the
   repeats.** Kolibri's `ledger2` is 226/226 at 32,768 (six-task loop, fourth position), **212/226
   twice at 131,072 in the same six-task position**, and **226/226 twice at 131,072 when `ledger2`
   runs first** (`newtasks-rep-20261009-k1/k2`). The same context produces both values, so context is
   not the driver; loop position, or plain run-to-run variance, is. `ledger2` is simply the noisiest
   battery here - see "Repeatability, measured" below - and single-run differences under ~19 checks
   are not interpretable for these models.
4. **The usage-gap tolerance is load-bearing.** Kolibri's first six-task attempt (`-v2`) aborted after
   three tasks on `quota_unknown`; with the tolerant `Budget` subclass every provisioned run finished
   all six tasks.
5. **Swift's frozen-`ledger` collapse was a reply-cap artifact, not a model verdict.** Its 32,768
   baseline (`newtasks-20261008-v3`) scored `ledger` **7/70** with `ledger2` **226/226** on
   byte-identical checks. With the raised reply cap and quota (`-v11`) it scored **70/70** - the same
   Cause 1 that the report fixes for MiniCPM, now reproduced on a second model. It also confirms the
   exemption costs Swift nothing: with a 32,768 window it still reaches 226/226 on `ledger2` and
   40/40 on `longctx`, and its best-ever six-task total is 530/565 at 1,926 s.

### Swift Bonsai 2 is EXEMPT from the provisioning: a raised context crosses the GPU floor at load

Swift runs on the Prism fork (`staged-swift-20260930/prism/llama-server.exe`), not stock llama.cpp.
Three failures pin the reason, two of them at 131,072 and one at 65,536:

- `newtasks-ctx-20261008-v6` never started the sweep: the pre-sweep host smoke raised
  `AssertionError('OMP native read smoke failed')`.
- `newtasks-ctx-20261009-v10` started, loaded the model with `n_ctx_slot = 131072` and began
  listening, then the monitor stopped the session: `monitor_errors = ["RuntimeError('Resource,
  paging, STOP, or queue deadline')"]`. The samples say which resource - **`gpu_free` bottomed at
  0.49 GiB against the 0.5 GiB floor** with `gpu_used` 11.18 of 12 GiB, while physical RAM was never
  below 32.58 GiB free.
- `newtasks-swift-20261009-c65k` (65,536, via `LAB_CONTEXT`) tripped even earlier - **24.8 s in,
  `gpu_free` 0.31 GiB, before the model finished loading** - which is what identifies the crossing as
  a load-time peak rather than a generation-time cache size; the ladder below has the numbers.

So `newtask_run.py` carries `PROVISION_EXEMPT = {'swift': ...}` and skips **both** the engine flags
and the host-window rewrite for that model (a half-skip would leave the host believing in a window
the server does not serve). `newtasks-ctx-20261009-v11` is the retry with only the runtime-agnostic
changes - the usage-gap tolerance, the raised reply cap and the repo wall - and it is the run that
paid off: **530/565 in 1,926 s** (76 / 70 / 75 / 226 / 43 / 40), against 427/525 for its own 32,768
baseline, with `ledger` 7/70 -> **70/70** and `longctx` 40/40 at `n_ctx_slot = 32768`.

### The ladder: 32,768 holds, 65,536 and 131,072 trip at load

`ctx_ladder.py` reads the served context and the GPU/memory minima back out of every Swift root, and
the provisioned retry (`LAB_CONTEXT=<tokens>`, operator-declared per build, which deliberately
outranks the exemption) settles where the ceiling actually is:

| Root | Served context | min `gpu_free` | max `gpu_used` | Verdict |
|---|---|---|---|---|
| 20261008-v3 | 32,768 | 0.69 GiB | 10.97 GiB | ok (five tasks) |
| ctx-v11 | 32,768 | 1.28 GiB | 10.38 GiB | ok (six tasks, 530/565) |
| **newtasks-swift-20261009-c65k** | **65,536** | **0.31 GiB** | ~11.7 GiB | **monitor stop after 24.8 s** |
| **newtasks-swift-20261009-c65k2** (retry) | **65,536** | **0.31 GiB** | ~11.7 GiB | **monitor stop after 26.0 s - reproduces** |
| ctx-20261008-v6 | 131,072 | 0.50 GiB | 11.16 GiB | host read-smoke failure |
| ctx-20261009-v10 | 131,072 | **0.49 GiB** | 11.18 GiB | **monitor stop** |

The raise costs a **load-time** GPU peak, not a generation-time one. Comparing `max_gpu_used` between
the 32k and 131k runs (10.38 -> 11.18 GiB) implies a small KV and is what misled this report into
predicting that 65,536 would fit with room; it does not. The weights coming off disk (a hard-fault
storm at **808,514 pages/s** on the 65,536 attempt) push allocation past the 0.5 GiB floor while
physical RAM (34.4 GiB free) and commit headroom (33.5 GiB) are untroubled, and the session never
finished loading. So the exemption holds at **65,536 and 131,072**; 32,768 is the only measured
configuration that clears the floor, and 98,304 was skipped by the chain's own gate (which proceeds
only when the previous rung exits clean). **The 65,536 retry reproduced it exactly** - 0.31 GiB again,
26.0 s instead of 24.8 - so the crossing is systematic at that context, not a one-off desktop
footprint, and the exemption is settled: 32,768 or nothing.

An earlier draft of this section proposed excluding `longctx` from an exempt model's task loop, on
the assumption that a ~65k-token corpus cannot fit a 32,768 window. `-v11` refutes it - the task's
peak prompt is 16,111 tokens (11 requests, 142,476 cumulative) - and the exclusion was removed from
the driver rather than kept as a dead switch.

## The nine-task loop: a perfect six-task sweep, and the first live reading of `repo2`, `perf`, `longctx2`

`newtasks-ext-20261009-v12` (Qwen3.6, the reference configuration, 2,707.5 s, no error) is the first
root whose loop carries every battery built this week:

| task | score | clean | correct | s | tokens |
|---|---|---|---|---|---|
| events | 76/76 | yes | yes | 631.0 | 25,670 |
| ledger | 70/70 | yes | yes | 419.1 | 16,867 |
| paths | 75/75 | yes | yes | 146.2 | 5,561 |
| ledger2 | 226/226 | yes | yes | 212.6 | 8,170 |
| repo | 78/78 | yes | yes | 134.4 | 5,148 |
| longctx | 40/40 | yes | yes | 153.2 | 5,031 |
| **repo2** | **54/55** | yes | **no** | 269.7 | 10,633 |
| perf | 33/33 | yes | yes | 263.3 | 5,208 |
| longctx2 | 40/40 | yes | yes | 225.0 | 8,018 |

1. **First perfect six-task sweep: 565/565, every task clean and correct.** The previous best,
   `ctx-v8`, was 562/565 with one `ledger` and two `ledger2` misses; those did not recur, which is
   the expected behaviour of batteries with a run-to-run spread of about a dozen checks.
2. **`repo2` is the only battery that discriminated here, and it says why.** Its 55 checks are the
   four independent defect classes the census asked for - class1 UTF-8 byte-length accounting (22
   checks), class2 the per-instance extension registry (6), class3 buffer aliasing on reopen (5),
   class4 swallowed errors (7) - plus 15 extras. Qwen3.6 passed 54 and missed exactly one: case 27,
   `class2/unknown-kind-raises` - `Registry().register('nope')` must raise `ValueError` and does not.
   It built the per-instance registry (5 of 6 class2 checks pass) and did not validate the kind. That
   is the granularity the old `repo` lacked: across five top-group artifacts it split on three checks,
   all of one class.
3. **`perf` passes, and it measures an axis nothing else did.** 33/33: the required `merge` handled
   **2,000,000 intervals** inside the evaluator's budget, with the bound expressed *relative to the
   reference* so a loaded machine cannot manufacture a failure. Every other battery here accepts a
   correct-but-quadratic implementation; this one is the only place engineering judgement is priced.
4. **`longctx2` passes 40/40 - all nine planted frame-length sites found.** The nine sites are written
   differently and agree on ASCII, so the public tests stay green and only a real audit finds them;
   its designed split is for *partial* fixers (say five of nine), which no run has produced yet.
   At n=1 this is "no failure observed", not "saturated" - the same reading the census applies
   everywhere else.

Nine-task total: **692/693**. The three new batteries now have their first live sample; they join the
rate aggregate as samples accumulate, not before.

## Repeatability, measured: `ledger2` is noisy everywhere, `repo` is stable only for the strong models

The targeted repeats (`LAB_TASKS=ledger2,repo`, two per model, roots `-q1/q2`, `-k1/k2`) plus every
earlier run give the first real spread for the two batteries meant to be the fine-grained
discriminators. Loop position is shown because it turned out to matter.

| Model | `ledger2` values (n) | spread | `repo` values (n) | spread |
|---|---|---|---|---|
| Qwen3.6-35B-A3B | 207, 212, 212, 224, 226, 226 (6) | **19** | 75, 78, 78, 78, 78, 78 (6) | 3 |
| Kolibri-1 78B | 211, 212, 212, 226, 226, 226 (6) | 15 | 78, 78, 78, 78, 78 (5) | **0** |
| Swift Bonsai 2 (32,768) | 226, 226, 226 (3), plus one 62* no-op | **0** (edited) | 43, 43, **75** (3) | **32** |
| Nemotron-3.5 | 208, 209, 222, 223 (4) | 15 | 75, 78, 78, 78 (4) | 3 |
| MiniCPM5-2B | 144, 199, 201, 203 (4) | 59 | 0*, 43, 43, 68 (4) | **68** |
| gpt-oss-20b | 202, 204, 206, 219 (4) | 17 | **0***, 72, 77, 78 (4) | 6 (edited) |

1. **`repo` is the reproducible battery - but only for the models that can do it, and only Kolibri
   is perfect.** Kolibri 78/78 **five times (spread 0)**, Qwen3.6 78/78 five of six (spread 3),
   Nemotron 78 in three of four (spread 3) - against MiniCPM 0*/43/43/68, gpt-oss **0*/72/77/78** and
   **Swift 43/43/75**, where `0*` marks the no-op cells that the starter-baseline rule now catches: the
   zeros were never edits, so gpt-oss's edited `repo` samples are 72, 77, 78 and MiniCPM's are 43, 43, 68. So `repo` splits between models (a boundary at 78,
   43 or 0) and is tight *within* one only above that boundary; for the weaker models it is closer to
   bimodal, and the sixth sample moved Swift off the "always 43" line the first two had drawn. For the two weakest it is the
   **most volatile** battery in the set: MiniCPM 0/43/68 and gpt-oss **0/78/77**, so `repo` is closer
   to bimodal there (either the multi-file repair lands or it does not), and its swing dwarfs
   `ledger2`'s.
2. **`ledger2` is not.** Qwen3.6 spans 19 checks and Kolibri 15 in the same configuration, and
   Kolibri's swing is not explained by context: it is **226 at both 32,768 and 131,072**, and 212 only
   when `ledger2` sits fourth in a six-task loop. The battery still separates the field - 226 (Swift,
   Kolibri) vs 207-226 (Qwen3.6) vs 144-202 (gpt-oss, MiniCPM) - but **a single-run difference below
   about 19 checks carries no information about these models**, and every earlier "X beats Y on
   `ledger2` by 12 checks" reading in this family sits inside that noise.
3. **When `ledger2` does fail, the failure is legible.** Qwen3.6 `-q1`'s 207 came with 19 failing
   traps, all in the known cluster: frozen cases 0, 6 and 19 plus the whole Unicode-digit group
   (arabic-indic / extended-arabic-indic / devanagari / fullwidth, each plain / leading-zero /
   embedded). That is the ASCII-digit rule the census identified, not a scattered collapse.
4. **The loop-position hypothesis does NOT survive a third same-shape sample, and the shaped vectors
   are the evidence.** Grouping every sample by the shape it ran in kills the story:
   **Kolibri `ledger2`** is 226 at *pos 1 of 2* and 226 at *pos 4 of 5*, but 211/212/212 at *pos 4 of 6*
   - so it is not position, and the same position gives both values depending on the loop's length;
   **Qwen3.6** spans 207-226 with no pattern at all, including a perfect **226 at pos 4 of 9** (its
   longest loop), which is the opposite of "later is worse"; **Nemotron** spreads 209-222 *within one
   shape* (4 of 6); **MiniCPM** spreads 144-203 within one shape. What looked like a position effect at
   n=2 was a coincidence; `ledger2` is simply noisy per model, and the corrected form of the earlier
   claim is in the spread table, not in a mechanism.
   The vectors, grouped by the loop shape each sample ran in (`notclean` = the session's cleanup flag;
   walls in seconds):

   | model | `ledger2` by shape | `repo` by shape |
   |---|---|---|
   | Kolibri-1 | pos 1 of 2: **226, 226** · pos 4 of 5: 226 · pos 4 of 6: **211, 212, 212** | 78, 78 (1 of 2) · 78 (4 of 5) · 78, 78, 78 (4 of 6) |
   | Qwen3.6 | pos 1 of 2: 207, 226 · pos 4 of 5: 212 · pos 4 of 6: 212, 224 · **pos 4 of 9: 226** | 78, 78 · 75 · 78, 78 · 78 |
   | Nemotron | pos 4 of 5: 223 · pos 4 of 6: **208, 209, 222** | 75 (4 of 5) · 78, 78, 78 |
   | MiniCPM | pos 4 of 6: **144, 199, 201, 203** | 0, 43, 43, 68 (4 of 6) |
   | gpt-oss | pos 4 of 5: 219 · pos 4 of 6: 202, 204, 206 | **0, 72, 78** (4 of 6) |
   | Swift | pos 4 of 5: 226 · pos 4 of 6: 226, 226 | 43, 43 (4 of 6) · **75** (5 of 5, the six-loop run) |

5. **`7/70` is the ledger starter's score, so a 7/70 means the session never wrote the artifact** -
   not a wall signature and certainly not a capability reading. Nemotron's `pos-n1` 7/70 came with a
   session stopped at exactly 720.1 s, and Swift's historical 7/70 (the one the lab spent effort on as a
   truncation) is the same no-op. The wall is a plausible *cause* of the non-write in that sample; the
   *fact* to read is "no edit".
6. **MiniCPM is the widest spread in the family, on both batteries** (n=3: `ledger2` 144/199/203,
   `repo` **0/43/68**). Its third run (`newtasks-minicpm-20261009-r1`, quota 96,000) is its best by
   66 checks - **522/565 in 1,110 s**, with `repo` 68/78 where the first two runs scored 43 and 0.
   So "MiniCPM thrashes on cross-module work" is too strong: it *can* do the multi-file repair, it
   just does not do it reliably, and reliability is the finding. The cap-arm reading is now n=1 per
   arm (456 at 96k vs 522 at 96k vs 445 at the default), so the mitigation is not yet established
   either - which is exactly the gap item 4 of the status table was written to close.
7. **gpt-oss has the largest single-model swing measured: 432 -> 528/565 (+96), and `repo` 0 -> 78.**
   `newtasks-gptoss-20261009-r1` scored 76 / 66 / 75 / **204** / **78** / **29** in 931.5 s against
   its own `ctx-v2` of 432 (74 / 66 / 75 / 202 / **0** / 15): same configuration, same model, and the
   difference is almost entirely `repo` (0 -> 78) and `longctx` (15 -> 29). "gpt-oss fails every hard
   axis" was an n=1 conclusion; at n=3 it is weak on the ledger traps (66/70, 204-219/226) and
   *capable* of the multi-file repair. The third sample (`-r2`) is **partial**: it scored events 76,
   ledger 65, ledger2 219 and repo 77/78, then its `paths` scorer exited abnormally
   (`abnormal_evaluator_exit: 1`) and `longctx` raised `ValueError('unknown task: longctx')` **from the
   frozen benchmarks module** rather than the root's superset. Those two cells are **unscored, not
   failed** - the lab's established category - and the record now carries an explicit `unscored` flag
   for exactly this case. r3's targeted re-run recovered `paths` **75/75**, and re-scoring both roots'
   `longctx` artifacts offline gives **0/26** for each: the model's file carries a syntax error
   (`def reconcile_batch(records):` with no body), so those cells are a genuine failure rather than a
   gap. (The denominator is 26 rather than `longctx`'s usual 40 because the scorer enumerates fewer
   cases for an artifact it cannot import - recorded as the reading, not as a verified mechanism.)

## Two new instruments, built and self-tested - not yet run

The suite measures procedural coding/repair and nothing else, so two questions the week raised have no
instrument behind them. Both are now built, pinned and self-tested; both are queued behind the running
chain so their first numbers are not collected on a busy box.

**1. A knowledge/recall instrument (`knowledge_items.py`, `knowledge_run.py`).** It answers "does
Qwen3.8-Flash-Next Q2_0 know more than Qwen3.6-35B-A3B?" - a question no existing evidence can touch.
1,100 items, pinned by sha256 (`knowledge-items-20261009.jsonl`, `knowledge-sources.json`): **800 MMLU
over 8 subjects** for factual recognition, and **300 GSM8K** as the *procedural control*, because
low-bit quantisation damages factual recall far harder than step-by-step reasoning - so a model that
holds GSM8K while losing MMLU has the aggressive-quant signature rather than less knowledge. Sampling is
pinned per request (temperature 0, seed 20261009), which matters here because the Strata config declares
**no seed at all**.

The instrument's own test caught two defects in my code before any engine saw it: a `%`-format collision
that ate the percent-encoded dataset name in the fetch URL, and a scorer that normalised thousands
separators on the model's side but not the reference's (so `2,125` in the gold answer read as a miss).
Both fixed. The self-test reports **gold 1100/1100 (1.000)** and a seeded random responder at
**0.253 on MMLU** (chance for four options) with **0/300 on GSM8K** - so the prompt carries the answer,
the parser reads it back, and the scorer discriminates.

The *live* smoke then found a third class, and it needed two iterations to name: the first pass scored
Qwen3.6 **0/6** and Strata 2/6 (implausible), because a 24-token MCQ allowance is consumed entirely by
the reasoning block; widening the caps and parsing the *last* letter gave 2/6 and 5/6, and the recorded
failures showed what was really happening - the replies were **empty strings**, not mis-parsed ones.
Both engines were sending every token to the reasoning field, which is the same behaviour this lab
measured on the Strata engine in September ("this reasoning model puts every token in
`reasoning_content` at low `max_tokens`"). The fix is per request, so no pinned engine config moves:
`chat_template_kwargs: {reasoning_effort: none}` for llama.cpp and `reasoning_budget_tokens: 0` for the
Strata engine, plus a capture that falls back to `reasoning_content`. A smoke that scores a new
instrument *before* the real run is what turned three silent zeroes into three named defects; the
full run launches only once the smoke reads plausibly.

Prediction, recorded before the run: **Qwen3.8-Flash-Next Q2_0 should win MMLU** (stored capacity is
what carries facts, and it holds roughly 5-6x the parameters) **while the two stay close on GSM8K**; if
instead the 2-bit model loses MMLU and holds GSM8K, the low-bit penalty is confirmed and the knowledge
question becomes "how much precision, not how much capacity".

**2. An Intel iGPU probe (`igpu_probe.py`), and it had to be fixed before it could be believed.**
The NPU is not reachable from any engine here - Ollama 0.40.0's log lists CUDA plus an opt-in Vulkan path
for the Arc iGPU and names no NPU backend - so the question is what the iGPU costs on identical prompts.
First run: both arms reported **`100% GPU`** and near-identical rates (335.8 vs 330.9 tok/s), because the
discrete card was hidden with `CUDA_VISIBLE_DEVICES=''`, which CUDA tooling treats as *unset*. An
instrument that does not verify its own attribution reports a confident zero, and this one nearly did.
With `CUDA_VISIBLE_DEVICES=-1` (the canonical "no device") the arms separate on the model's own report:

| arm | `ollama ps` split | median | vs the 5070 |
|---|---|---|---|
| cuda (default) | **10 % CPU / 90 % GPU** | **260.5 tok/s** | - |
| iGPU (`OLLAMA_IGPU_ENABLE=1`, discrete hidden) | **59 % CPU / 41 % GPU** | **100.8 tok/s** | **0.39x** |

So the Arc path does work - it engages through Ollama's Vulkan backend - and on a 3B MoE it delivers
about **39 %** of the discrete card while splitting the work with the CPU, its share spilling to system
RAM. For this lab's measured work that settles it: the 5070 stays the device, and the iGPU is at best a
*second* device for the small decision/embedding track so it does not contend for the card. Declared a
**hardware probe** either way: it changes an execution provider, so its numbers never mix with the
frozen screens.

## The nine-task suite on four more models

The nine-task loop has now run end to end for Nemotron, MiniCPM, gpt-oss and Swift (Kolibri below), with
the same declaration as the reference rows - provisioned at 131,072, Swift at its exempt 32,768:

| root | wall | nine-task | ranked / 414 | ev | led | pa | led2 | repo | lctx | repo2 | perf | lctx2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MiniCPM5-2B | 1,534 s | **656/693** | **392** | 73 | 67 | 75 | 207 | **78** | 40 | 43/55 | 33 | 40 |
| Nemotron-3.5-L | 4,709 s | **620/693** | 388 | 76 | 68 | 75 | 202 | 78 | 40 | 48/55 | 33 | **0/40** |
| gpt-oss-20b | 1,626 s | 549/693 | 306 | 76 | 64 | 75 | 202 | **0** | 40 | 48/55 | **28/33** | 16 |
| Swift Bonsai 2 (exempt) | 2,937 s | 508/693 | 250 | 76 | 70 | 75 | **62 no-op** | 78 | 40 | 34/55 | 33 | 40 |

1. **MiniCPM's 656/693 is the best non-reference profile**, and it is built on a first: `repo` **78/78**
   where that model previously scored 0, 43 and 43 - the bimodality again, now resolved in its favour
   once. Its `repo2` 43/55 and its `events` 73/76 are the cost.
2. **`repo2` is the new discriminator, and nobody has solved it.** Across all nine-task runs the battery
   reads 34-48/55 for these four against **54/55 for Qwen3.6 and Strata**, whose single miss is the same
   check (`class2/unknown-kind-raises`). One battery, three and a half grades of separation.
3. **Swift's `ledger2` 62/226 is NOT a collapse - it is the starter's score, i.e. the session never
   wrote the file** (its artifact is byte-identical to the template, sha256 `329f3332...`, 215 bytes, and
   the session logged 13.6k tokens without an edit). With that cell reclassified, Swift's *edited*
   `ledger2` samples are 226, 226, 226 - it stays the most stable model on the finer ledger, and an
   earlier draft of this very section had it backwards. See the starter-baseline rule below.
4. **Nemotron's `longctx2` is unscored, not 0/40** - the evaluation carries
   `abnormal_evaluator_exit: 1` and no checks, which an earlier draft of this section read as "all nine
   planted sites missed". gpt-oss's is a real 16/40. So on this battery the honest statement is: one
   model unscored, one at 16/40, the rest 40/40.
5. **The position hypothesis gets its cleanest test and dies.** `newtasks-pos2-20261009-n1` ran
   `ledger2` **alone** (position 1 of 1) for Nemotron: **218/226**, which sits in the middle of the same
   model's 4-of-6 samples (202, 208, 209, 222) and below its 4-of-5 sample (223). No shape predicts it;
   the spread is the model's, not the loop's.

**Kolibri's nine-task profile is blocked by a floor, and that is the result to record.** Both attempts
died in the *host smoke* stage (before any task) with `AssertionError('OMP native read smoke failed')`
whose cause is in the session's own monitor artifact: **commit headroom bottomed at 1.97 and 1.96 GiB
against the 2 GiB floor** (physical 10.2 GiB free, GPU 6.5 GiB free - both fine). The commit history
shows why this is a knife-edge rather than a regression: every earlier Kolibri session held 4.28-9.34
GiB of commit headroom, and every session from 15:19 onward held 1.5-3.5 GiB, because a 78B Q4 MoE plus
its KV plus the agent draws roughly 40 GiB of commit and the machine's ambient committed bytes moved a
few GiB. WSL is not the culprit (no distro running, 490 MiB residue) and there are no significant
orphans. The floor stays where it is: this is a measurement against it, and the honest next step is to
re-run Kolibri when ambient commit is lower, not to lower the bar.

## The knowledge A/B: the 2-bit giant and the 4.8-bit 35B are indistinguishable

The instrument's first real run, 1,100 items per stack, same prompts, same pinned sampling (temperature 0,
seed 20261009), each engine launched in the declaration its scored runs used:

| stack | overall | MMLU (recall, 800) | GSM8K (procedural, 300) | wall |
|---|---|---|---|---|
| **Qwen3.6-35B-A3B Q4_K_M** (llama.cpp, 131,072, `--cpu-moe`) | **974/1100 = 88.5 %** | 688/800 = 86.0 % | 286/300 = 95.3 % | 3,078 s |
| **Qwen3.8-Flash-Next Q2_0** (Strata, 65,536, 4 GiB resident, streamed) | **987/1100 = 89.7 %** | 699/800 = 87.4 % | 288/300 = 96.0 % | **2,128 s** |

Per subject the two are the same picture: astronomy .95/.96, geography .90/.90, world history
.90/.91, international law .93/.90, philosophy .90/.91, prehistory **.86/.94**, virology **.58/.58**,
world religions .86/.89.

1. **The gap is inside one standard error, so the second stack is not better - it is indistinguishable.**
   13 items out of 1,100 is +1.2 points, with a standard error on the difference of about 1.3 points.
   MMLU alone is +1.4 points (11 items) and GSM8K is +0.7 (2 items). Reporting either as a win would be
   the n=1 mistake this lab keeps punishing.
2. **My prediction was directionally right and materially wrong, and the wrong part matters.** I recorded
   before the run that the 2-bit giant should *win* MMLU while staying close on GSM8K, and that a
   recall-specific penalty was the alternative to watch for. It did not appear: at roughly 2 bits per
   weight this model's factual recognition is **87.4 % against 86.0 %** - no measurable loss - and its
   procedural math is 96.0 % against 95.3 %. So on this instrument, **aggressive quantisation did not
   cost measurable knowledge**, which is the opposite of the "low bits eat facts first" expectation I
   wrote down. The honest form of the claim is the one the nine-task suite reached from the other
   direction: a streamed Q2_0 pack is the equal of a resident Q4_K_M 35B.
3. **`virology` is 58 % for both models and 30 points below every other subject.** That is a property of
   the items, not of the models - it is the instrument's own ceiling for that subject and should be
   excluded from any claim about knowledge differences.
4. **`prehistory` is the only subject with a visible gap** (.86 vs .94, 8 items): at 100 items per
   subject that is about 1.9 standard errors, suggestive rather than established.
5. **Operational aside worth keeping: the streamed engine was faster on this workload** - 2,128 s
   against 3,078 s for the same 1,100 items, because the 35B runs `--cpu-moe` (experts on CPU) while
   Strata answers from its 4 GiB cache and disk with a ~53 % expert-cache hit.

Both engines were launched with the exact declaration their scored suite runs used, and the instrument's
own checks (gold 1100/1100, random 0.253) bracket the result.

## Method notes worth keeping

- **Attribute before you count.** An engine's own log line and a per-turn `stopReason` are cheap and
  decisive; 40 of 84 historical sub-perfect sessions were not the model's fault, and no score table
  could show that. `census.py` + `witnesses.py` are 180 lines of read-only analysis.
- **`clean_finish`, `exit 143` and `quota_unknown` are not failure signals** on this harness: they
  appear on 70/70 runs. Correctness is `evaluation.passed`; the others are lifecycle facts.
- **A saturated task is worse than no task**: it absorbs budget and manufactures false ties.
- **Instrument first, then infer.** Both new batteries were verified against their reference and
  their own starter (226 vs 62; 78 vs 43) *before* spending a single GPU-second, and both were proven
  through the live scoring path offline.
- **Editing a pinned file stops every new root - by design, and the cure is a declared re-pin.** Each
  root's `manifest.json` pins 120 files by digest, including the monitor module
  (`local-decisions-20260925-v1/run.py`). Removing the worker cap there made seven freshly built roots
  die in `verify()` with `AssertionError: [...run.py]` - the freeze working exactly as intended. The
  builder now **recomputes the manifest and records old -> new digests** in `evidence/pin-change.json`,
  and the inherited protocol field `decision_worker_private_cap_gib` is set to null with a note.
  Verified after rebuild: 120 pinned, 0 mismatches. A bypass would have silenced the check that caught
  the change; a re-pin states it.
- **A scorer timeout is unscored, not a model failure - and the harness's timeout is 30 s.** The
  Strata `repo2` session ended with `evaluation_timeout: true` and `exit 143` after its artifact was
  complete; re-scoring that artifact outside the harness is the recovery path (see
  `offline-rescores-20261009.json` for the same move on the v2 sweep). The 30 s ceiling lives in
  `compare_staging_20260922.score_artifact`, so a heavy battery can exceed it on a loaded box even when
  the artifact is fine. **It stays at 30 s deliberately, and that is an evidence call, not inertia:** the
  one artifact that exceeded it hung for the full 600 s, and several heavy batteries scored well inside
  30 s - nothing has ever landed between the two, so raising the ceiling would only buy more wall time
  for pathological artifacts. Raising it is a *pinned-file* change anyway (the roots carry their own copy
  of the base), so it would need its own declared re-pin.
- **A score equal to the starter's baseline is a NO-OP reading, not a model verdict.** Score the
  unmodified starter through the same scorer and keep the table: `events` **2/76**, `ledger` **7/70**,
  `paths` **9/75**, `ledger2` **62/226**, `repo` **0/78**, `longctx` **1/40**, `repo2` **0/55**,
  `perf` **1/33**, `longctx2` **0/40** (`starter-baselines-20261009.json` pins them, with the starters'
  sha256). Nine cells in the whole corpus land exactly there (`starter-flags-20261009.json`), and four
  of them had been read as model behaviour: Swift's 7/70 and its `ledger2` 62/226, both of gpt-oss's
  `repo` zeros, and MiniCPM's `repo` 0/78. The double check is cheap and exact: **hash the artifact
  against the starter** - byte-identical settles it, and a *clean* session can still be a no-op, so
  `clean_finish` cannot distinguish it.
- **An empty `content` is a capture bug, not a wrong answer - check `reasoning_content` first.** A
  reasoning engine that exhausts its allowance inside the thinking block returns `content: ''`, which
  any scorer will read as a miss. This lab already knew the shape of it (the September Strata sampling
  probe: "every token in `reasoning_content` at low `max_tokens`"); the knowledge instrument rediscovered
  it because its first live smoke scored 0/6 and the *replies* were empty. Instruct the model not to
  deliberate, and fall back to `reasoning_content` before scoring.
- **Verify the *value* you record, not just the field name.** A `model`/`name` NameError in the new
  context-recording block killed seven invocations *before* they started, and it looked like runs that
  had silently produced nothing. Cheap discipline: after adding a field to the record, print it from a
  real run and read it back.
