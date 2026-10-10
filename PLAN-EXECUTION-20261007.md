# Plan execution, 2026-10-07 (the pre-registered list, item by item)

Baseline: `my-plan-20261007-pre-registered.txt`, written before the work. Status of each item, its
evidence, and what it settled.

## Item 1 - turn single runs into rates. DONE

12 repeats in fresh roots plus every historical sample, aggregated in `local-llm-lab/rates-20261007.json`
and written up in `rates-20261007/REPORT.md`.

- **`ledger` is the discriminating task.** Full marks are rare: Swift 2/2, Strata Q2_0 3/4, Kolibri 1/3,
  and no other configuration ever reached 70/70. `events` and `paths` are full marks in 3/3 or better for
  every model that scores well at all.
- **Each model has ONE characteristic failure mode**, not general flakiness: MiniCPM `paths` 9/75 once in
  six; gpt-oss `events` 0/76 once in three; Strata `ledger` early termination (241 tokens in the 7/70
  sample). Nemotron never failed events or paths, only gave away two or three ledger checks.
- **A better quant does not fix a behavioural failure.** IQ1_M -> Q2_0 raised decode 46-49 -> 71-72 tok/s
  and the ledger rate 2/6 -> 3/4, and the early-termination mode still appeared once.
- Speed-versus-consistency is now quantified: Kolibri never below 99.1 % in three sweeps at 32 tok/s;
  Strata Q2_0 best per-task rates at 561 s per sweep (2.2x faster); Swift 2/2 on every task at 45.6 tok/s;
  gpt-oss fastest (201 s median) and least reliable of the good ones.

## Item 2 - adopt rate reporting. DONE

Written into `DECISIONS-AND-CONVENTIONS-20261007.md`: state n, report distributions, rank only at n >= 3,
caption best-sample selection, report tasks separately, quote rates against an explicit floor.

## Item 3 - Kolibri long-context capability. DONE

`kolibri-ctx-20261007/REPORT.md`. Three planted codes recovered **3/3 at 32k, 64k, 128k and 256k**
(206,188-token prompt), VRAM 4.5 -> 7.3 GiB, free physical flat at ~9 GiB, load 25-28 s. Our 32k
protocol is a choice, not a limit. The first 128k attempt failed on my probe's O(n^2) prompt builder, not
the model; fixed and re-run.

## Item 4 - stage and screen Qwen3.6-35B-A3B. DONE

`staged-qwen36-20261007/REPORT.md`. Staged Q4_K_M (20.42 GB) plus MTP (1.06 GB) and DFlash (0.42 GB)
heads, all sha256-verified at revision `baec3ebe`. Screen: **219/221 = 99.1 %, all three tasks clean,
569 s, 38.1 effective tok/s, 24 GiB of RAM headroom** - the same accuracy class as Kolibri at 20 % more
speed and far less memory pressure. Bench: 46.14/46.17 tok/s decode plain; **67.06/62.06 with the MTP
head (+45 % / +34 %)**, the first speculative-decoding gain that matters here. The declared MTP harness
screen scored 220/221 but took 785 s against 569 s because the sampled trajectory emitted 1.9x the
tokens - with n=1 per arm at temperature 1.0 that is not attributable to MTP, so the honest claim is
"faster per token, unproven per task" and an n=3-per-arm comparison is queued.

## Item 5 - the engine question. DONE (decision, no run needed)

`DECISIONS-AND-CONVENTIONS-20261007.md`. The identical model and placement on b10883 versus b11461
measured within noise (34.1/35.1 versus 35.4/34.0 tok/s, prefill ~5 % higher on b11461), so the frozen
coding roots stay on b10883 and b11461 is used only where a model needs its features (27B `--fit`/spec
heads, Nemotron's architecture, Kolibri's community build).

## Item 6 - Strata quant curve. SUBSTITUTED, with reasons

The original form (IQ2_XS 68 GB + IQ3_XXS 75.8 GB) needs ~113 GB of disk against 129.5 GB free and about
two hours, for a question the IQ1_M -> Q2_0 comparison already bounds. Substituted with the resident-budget
curve on the pack already on disk: **12 GiB holds 4.95 GiB free physical and scored ledger 3/4; 8 GiB
dipped to 2.990 GiB (below the 3 GiB floor, one STOP) for ledger 3/3** - accuracy indistinguishable,
margins not. Recommendation: keep 12 GiB, do not lower. The IQ2_XS/IQ3_XXS comparison stays available if
disk and time are granted.

## Item 7 - owner decisions to surface. DONE (listed, awaiting the owner)

BitLocker never confirmed; no reason to raise the Q2_0 budget above 12 GiB; whether to adopt the rate
convention as lab policy; the 6 GiB worker cap is closed (8 GiB authorized and executed in v3).

## Item 8 - hygiene. DONE

The dense-27B root stays deliberately unrun with its reason recorded; the 67 GB Q2_0 GGUF staging is kept
(it is the only verified local copy of the source shards) and disk was checked before every large
download; the two roots killed at the start of the rates batch (my filename bug, 77 s, no evidence) are
documented; every guard trip of the day is preserved with its STOP file (`strata-20261007-v7` load-time
floor, `-v13-1/-2` and `-v14-1/-2` VRAM floor, `-v15-1/-2` paging guard, `-v16-1` free-physical floor).

## New items this work created (queued, not assumed)

1. **n = 3 per arm for MTP versus plain** on the coding protocol - the only way to separate a
   speculative-decoding effect from run variance at temperature 1.0.
2. **Rate sets for the three best configurations** (Kolibri, Nemotron, Qwen3.6-35B-A3B) to the n >= 3
   standard the convention now sets.
3. **The ledger's early-termination mode deserves its own probe**: why does the model end the session
   after two or three turns? That is a behaviour question, and every local model shows a version of it.
4. **Strata v0.1.40.1's tool-call rescue** (a `<tool_call>` quoted in thinking or a code fence no longer
   executes) is now in the pinned engine; the harness screens ran fine, but its effect on tool-heavy
   tasks has not been isolated.
5. **Qwen3.6-35B-A3B at long context** - its own context behaviour is untested (Kolibri now has a
   reference at 256k).
