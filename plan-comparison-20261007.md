# Planning probe: what Strata Q2_0 proposes vs my pre-registered plan (2026-10-07)

Model: Qwen3.8-Flash-Next (original) at Q2_0 through Strata v0.1.40.3, `--resident-budget-gib 12`.
Probe root: `strata-20261007-v12`. Brief and raw answers: `strata-20261007-v12/evidence/`
(`brief.txt`, `ask.json`). My baseline, written before reading its answer:
`my-plan-20261007-pre-registered.txt`.

The brief gave it: the machine, the lab's constraints (one workload at a time, fixed floors and
gates, no reboot, owner authorization, new directory per re-run, preserve failures), the measured
result tables, the models on disk with sizes, the Strata measurements, and a list of anomalies and
open questions. It gave no plan, queue, recommendation, or priority.

## Its answer, condensed

1. Re-run MiniCPM5-2B as a post-upgrade calibration probe (full success, per-task wall, RAM/VRAM, load, failing check ids).
2. Replicate the MiniCPM `paths` anomaly in fresh directories, 3-5 runs, identical settings; find where it breaks.
3. Run the Q2_0 Strata pack at 12 GiB several more times for reproducibility.
4. Characterise the 24 GiB budget failure quantitatively, then test 16 GiB **if the owner approves**.
5. Test whether context size changes performance (8k/16k/32k) for MiniCPM, Swift and Q2_0.
6. Profile gpt-oss-20b's unusually low token usage - is "success" comparable or a token-accounting/quirk artefact?
7. Repeat the fast-but-poor dense models (ling, spark) to find where they actually fail.
8. Replicate the well-scoring MoEs with thin evidence (gemma, nemotron, gpt-oss, qwen3-coder), 3+ runs each.
9. Exploratory: dense 27B at reduced context (8k/16k) to see whether it can meet the wall - explicitly without changing the frozen protocol.
10. Benchmark Strata load separately from inference, so wall times are comparable.
11. Resource-gate safety sweep over the top candidates before any final ranking.
12. A reproducibility manifest per run (hashes, quant, engine version, harness, context, seed, resource readings, check ids).

Its own uncertainty list: pre/post-upgrade comparability; the MiniCPM anomaly's cause; the safe
maximum budget; whether Q2_0's 221/221 repeats; gpt-oss's token accounting; single-run rankings being
provisional; and the 27B's real blocker.

## Item-by-item against my pre-registered list

| My item | Its coverage | Verdict |
|---|---|---|
| 1. Convert single runs into rates (n>=3) | Items 1, 2, 3, 8; priority answer puts MiniCPM repeatability first | **MATCH** - same top priority, same reasoning |
| 2. Adopt "rate over n runs" as the lab's reporting rule | Item 12 is a provenance manifest; no policy proposal | partial (measurement yes, policy no) |
| 3. Kolibri long-context capability test (64k-262k) | Item 5 tests *smaller* contexts on other models; Kolibri and 262k absent | **MISS** |
| 4. Stage and screen Qwen3.6-35B-A3B | not proposed | **MISS** (brief listed only on-disk models - see bias below) |
| 5. Decide the engine question (b10883 vs b11461) | touches "probe after hardware/version changes" | partial |
| 6. Strata quant curve (IQ2_XS / IQ3_XXS at 12 GiB) | item 4 covers budgets, not quants | partial (brief listed only two packs) |
| 7. Owner decisions to surface | repeatedly conditions on owner authorization; surfaces the 16 GiB decision | **MATCH in spirit** (it inferred the rule from the brief) |
| 8. Hygiene (27B stays unrun; consider deleting staging) | item 9 proposes *testing* the 27B at reduced context | **DISAGREES** |

It proposed four things I had not: the gpt-oss token-frugality audit (a sceptical read of a
favourable number - genuinely good), a why-do-fast-models-fail pass on ling/spark, separating load
time from agent time in reporting, and a gate-safety sweep before ranking.

## Resolving the one disagreement with existing data

Its item 9 assumes context size might be the dense 27B's blocker. It is not: the uniform benchmark
ran that model at **ctx 8192** (not 32k) and it still decoded at 5.00 / 4.76 tok/s, because half its
weights sit in system RAM. So a smaller context does not rescue it, and the exploratory run would
re-measure a known quantity.

## How much of the match is real

- The **top-priority match is real**: from the same numbers it independently concluded that
  reproducibility, not more models, is the binding problem - the same conclusion that put "rates"
  first on my list.
- But part of that is attributable to the brief's framing: I listed the ledger's 2-in-5 behaviour and
  the MiniCPM 75/75-75/75-9/75 spread as anomalies. A hint-free version of that test would hand over
  raw logs, not my curated anomaly list, so its agreement is partly my selection talking.
- Its plan is confined to "measure better with what exists". It could not propose acquiring the new
  model I have researched (Qwen3.6-35B-A3B) because the brief listed only the on-disk inventory; and
  it could not know the owner-specific open items (BitLocker status, app closure) because they were
  not in the brief. Both are gaps in my test, not failures of the model.
- It asked for owner authorization unprompted and refused to consider gpt-oss-120b on fit grounds -
  correct behaviour derived from the constraints, not from any instruction to be careful.

## Could it take over the task?

- **As a planner, yes within limits**: it produced a coherent, correctly-prioritised programme that
  overlaps mine on the highest-value item, and it added monitoring advice I had not written down.
- **As an agent, no**: it is a model behind an API. It has no tools, no filesystem access, no
  awareness of the session; the agency lives in the OMP harness and the lab's runners, which is what
  actually executes work here.
- **Cost of asking**: three attempts were needed. The default `reasoning_effort: high` produced a
  6,761-token think and armed the lab's frozen sustained-paging guard (run stopped, root preserved);
  `reasoning_effort: low` with a 4,000-token cap spent the entire budget reasoning and emitted no
  visible answer; only the documented `reasoning_budget_tokens: 2000` cap produced an answer. A model
  cannot take over this role unaided while that is true.
- **What our own harness data says about its reliability**: Q2_0 scored 221/221 in one sweep and its
  ledger 2/2, but events and paths are single samples, and the same engine's older pack split its
  ledger 2-in-5. Its plan is the right response to exactly that weakness.
