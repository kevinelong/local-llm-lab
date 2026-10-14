# Test ideas for the agent suite, from an outside reviewer's Strata Coder run

Provenance, and its limits. YouTube `09GB4LtXUok`, "Strata Coder tested - Local LLM setup", Luke's
Dev Lab, uploaded 2026-10-14, 18:32. Read from the auto-caption track, which yt-dlp would not serve
(HTTP 429 on the timedtext endpoint after several retries and three player clients) but
`youtube-transcript-api` did; raw transcript and the fetch script are kept out of this public repo at
`ai_bench/transcript-strata-coder-20261014/`. The model under test is
`ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder` (IQ1_M) on Strata, which is a pack **we already have
staged and have already run** - `strata Coder IQ1_M: ledger 7,70,7,64,70 - bimodal, 2/5 full`
(`local-llm-lab/AGENTS.md`). So this is a second opinion on a model with local evidence, which is
rare and worth mining.

**Status, 2026-10-14:** Kevin has read this note and **the generate-then-run class (idea 1) looks good
so far**, so it is the first of these to build when the queue has room. The wider scan that follows
it - other new repos, Hugging Face packs and three more transcripts - is in `NEWS-2026-10-14.md`,
which adds five ideas on top of these and annotates what each battery measures.

**What this file is not.** It is a proposal, not a queue change. Nothing was run, no engine was
started, no gate was checked, and no frozen artifact was touched. The overnight queue is still paused
where 2026-10-12 left it (`i4-reason-repeat`, `i6-gliner-replay`, then the Colibri Qwen3.6-35B-A3B
knowledge comparison), and these ideas do not jump it. **His numbers are not evidence**: one run per
test, prompts written and revised by hand, an RTX 2000 Ada 16 GB and a 5090 whose engine flags,
context and quantisation are not all stated, and results he corrects mid-video after prompting. What
transfers is the **test design** and the **failure classes**, which is what this note extracts.

## What the video measures, and what broke

| test | what it prices | his result | the failure he hit |
|---|---|---|---|
| Performance | prefill and decode under Strata | uncached prefill ~70 tok/s (RTX 2000) / ~200 (5090); cached 8K -> 479K tok/s; decode 42-43 / 182 | none; his claim is Strata beats llama.cpp **on prefill** (Q3_K_XL was "quite painful", "prefill was a nightmare") |
| Memory | recall a needle placed at a depth in a full window | 128K context, depths 0/25/50/75/100 %, 3 runs each = 15 runs, found every time | output cleanliness varies by depth (a "scroll bar", i.e. messier prose at 25 % and 75 %) |
| Reasoning | tiered hard reasoning | easy 100 %, medium 100 %, hard 92 %, expert 58 % | none; "just above average" |
| HumanEval Remix | 100 Python challenges | 99/100, attempted all 100 | none - and "this test needs to be more difficult", i.e. it is **saturated** |
| Kanban | frontend generation | working board, drag/drop/reorder/archive/search/toasts; 2 compactions, 69.2 % context | buttons overflowing their cards; every column named "untitled" until prompted |
| Sand physics | algorithm + substance semantics | water/wall/acid/erase/clear, all present | water and acid behaved **like sand**; then it **got stuck in a coding loop** and needed "you're stuck in a loop" to break out |
| Dungeon crawler | ray casting, fog of war, map generation | fully working, **no prompting at all, no compaction**, 64.8 % context | none |
| Blender (MCP) | complex tool API | lantern asset with glass and decorative pieces, good surface lighting; 3 compactions, 3 extra prompts | flailed on screenshotting instead of rendering through the scene camera; the **specified inner glow was missing** |
| Godot (MCP) | a whole 3D game | playable: pit death, moving killers, moving platforms, 3 keys, end state; 5 compactions, 67.8 % context | fog too dense; **left/right reversed**; **pit death crashed the game**; **one key unreachable** (platform too high) |

## What already exists here, so this does not rebuild it

- Throughput and load time, and the RAM/GPU/commit gates: measured per run.
- Factual recall: the 1,100-item knowledge instrument (800 MMLU over 8 subjects + 300 GSM8K as the
  procedural control). Planted-site reading of a 235 KB corpus
  in slices: `longctx` / `longctx2`. **Neither probes recall as a function of position in a full
  window.**
- Multi-file code work: `repo` (78) and `repo2` (55) are **repairs** scored by importing the artifact
  and asserting behaviour, so "run the generated code" is not new - "**generate** the code and verify
  its runtime behaviour" is.
- Engineering judgement priced numerically: `perf` (2,000,000 intervals inside a wall).
- Stall detection from identical outcomes: the three-line rule (4/4 caught, 1/14 false alarms).
- Reasoning: the 93-item run. Tiers are new.

## Ideas, in the order I would spend effort

1. **A "generate, then run it" battery class.** Every existing battery either repairs given code,
   reads given text, or prices a given algorithm. Nothing asks the model to *produce* a program whose
   behaviour is then observed. Three instances, cheapest first, each with a starter that must fail:
   - **Maze/dungeon invariants** (his dungeon test, objectively scorable): generate a maze; score
     connectivity (every cell reachable), no room overlap, a unique path under a stated rule, and
     determinism from a seed. Reference: a hand-written generator. Starter: one that emits a random
     grid and fails connectivity.
   - **Substance semantics** (his sand-physics defect, exactly): three cells with different rules
     (falls, spreads sideways, removes its neighbour) driven headlessly for N ticks; score the
     *transitions*, which is precisely what "water behaved like sand" is. This is the general form of
     his bug and it is trivially automatable.
   - **Frontend with DOM assertions** (his Kanban defects): generate a page, load it headless, assert
     the required controls exist and are *reachable* - a required element outside its container, or
     named "untitled", is a measurable defect, not a taste call. This one needs a browser, so it is
     the most expensive of the three; do it last.
2. **Solvability and crash-freedom under a scripted trace.** His two worst game defects are both
   machine-checkable: death-by-pit **crashed** the program (run a scripted input trace, require a
   clean exit and a defined state transition), and a key was **unreachable** (a reachability check on
   the generated level beats "it felt too high"). This is the only idea here that prices a defect
   class none of our batteries can see at all.
3. **A needle-at-depth probe at 131,072.** Cheap, and it closes a real gap: we raised the served
   window to 131,072 and never asked whether recall depends on where in the window the fact sits.
   Design from the video, hardened: depths 0/10/25/50/75/90/100 %, n >= 3 per depth, one planted
   unique token per probe, scored as found/not-found **plus** the position of the answer in the reply
   and the reply's length (his "scroll bar" observation is a prose-length effect, and this lab has
   already measured that placement moves prose and not answers - this would test that on long
   contexts rather than on the 93-item set).
4. **A canonical-tool-path battery.** His Blender failure is a *tool-choice* failure, not a coding
   failure: the model thrashed looking for a way to screenshot instead of doing the obvious thing in
   the tool it already had. Ours has no battery for that, and it needs no Blender - a small fake
   toolset where one correct call produces the required artifact and several plausible wrong calls
   exist (and cost budget) would separate "knows the tool" from "flails until told". The harness's own
   `write`-with-mangled-argument recovery note is the same family.
5. **A function-synthesis battery with hidden tests (HumanEval-shaped), adopted only if it
   discriminates.** He scored 99/100 and drew the right conclusion - the test is saturated. Ours has
   no equivalent at all, so it is worth having, but the lesson in the same breath is ours: `events`
   and `paths` were retired for exactly this reason, so this battery arrives with a rule - pin it,
   measure the top two models, and if both are at ceiling, either raise the difficulty or retire it
   rather than adding a third saturated row to the table.
6. **Report the cost of getting to green, which he does and we do not.** Every one of his results
   carries **compaction count** and **% context used at delivery** ("5 compactions, 67.8 %"), and his
   verdict everywhere is about **interventions** ("three extra prompts", "I had to jump in"). We
   record tokens, tool calls and turns; we do not report compactions/handoffs or a
   context-spent-at-delivery figure as first-class columns, and we have no assisted-versus-unaided
   axis at all. The first two are pure reporting and cost nothing. The third is a **protocol**
   decision, not a task: a second arm where a fixed, scripted hint set is allowed would price exactly
   what he spent the video judging, but it changes what a score means and needs Kevin's call.
7. **Pin the inverted-controls trap.** "The left and right was reversed - again, a common issue with
   models is reversing the controls" is a named, recurring failure class, and it is cheap to encode:
   a tiny generated program with a stated axis convention, driven by a scripted input, requiring the
   specified direction. Small, but it is a trap of the kind our suite does not yet carry.
8. **Try the stall rule on a coding loop, not only on decision windows.** The video is a fresh,
   independent, labelled stall incident - in a *coding* loop, inside a single task, with the user
   breaking it by naming it. Our rule was fitted on the 18 frozen decision windows and every neural
   model we tested caught 0/4 there. Whether identical-outcome repetition also fires in a coding loop
   is a different question, and the transcript gives the shape of the case even though it cannot be
   used as a label without the actual session log.
9. **A cached-versus-uncached prefill ladder - only if it changes a decision.** His performance
   screen is a ladder (uncached ~70; cached from 8K ramping to 479K), and prefill is this lab's
   measured wall (43.6:1 read:write), so the shape is right. But we already measure cold-prompt time
   and the expert-cache experiments; adopt this only when a specific question needs it, not as a
   standing instrument.

## What a decision would have to declare

- **A new battery changes the ranked subset.** The metric is `ledger + ledger2 + repo + longctx` =
  414 checks, chosen on evidence. Adding batteries means either a declared new subset or an explicit
  "unranked, exploratory" status, per `skill://lab-evidence-discipline` - not a quiet extension of the
  table.
- **Only idea 3 is runnable with today's instruments** (pure Python, no browser, no new tool). Ideas 1
  and 2 need a headless runner; idea 1's frontend instance needs a browser, which this lab has so far
  avoided on purpose.
- **Nothing here is scheduled.** The queue is paused and its owed items come first.
