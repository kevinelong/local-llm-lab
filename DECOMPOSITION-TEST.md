# Head-to-head: breaking a multi-part spec into working code

A measured follow-up to the "who is best at decomposition" ranking. Run 2026-09-09.

## Method
Gave the identical spec (a `notes.py` CLI with 7 numbered requirements plus persistence, a usage message,
and a self-test) to three agent harnesses, each headless, each in its own empty directory, told to "work
through the requirements one at a time." Then evaluated objectively: does the source cover every
requirement, and does the produced program actually run every command correctly (including its own
`test()`)?

**Important confound:** each harness ran on a different model, so this measures harness+model combos, not
the harness alone:
- Claude Code -> cloud Claude
- Aider (architect mode) -> local qwen3-coder:30b (Ollama)
- DeepSeek Harness (dsh, headless) -> DeepSeek V4-Pro (API)

## Result: all three succeeded

| Harness (model) | Time | Lines | All 7 reqs in source | Functional test (all commands + its own test()) |
|---|---|---|---|---|
| Claude Code (cloud Claude) | 58.5 s | 246 | yes | PASS (all commands work, stats correct, notes.json persists) |
| Aider architect (qwen3-coder:30b, local) | 114 s | 188 | yes | PASS |
| dsh headless (DeepSeek V4-Pro) | 122 s | 356 | yes | PASS |

None "bit off more than it could chew" on this spec. That is itself the main finding: a 7-part spec is
within reach of all three current harness+model combos, so it did not separate them on success. To find
where each over-reaches you would need a much larger / gnarlier spec (dozens of interdependent
requirements). This test validates competence, not a decomposition winner.

## Decomposition behavior we could see
- **Aider (architect mode) showed its work most clearly.** Transcript: "I'll build this incrementally.
  First, I'll create the basic structure with command parsing and file handling," then it implemented,
  then "I'll review the implementation against the spec requirements... I notice a few issues that need to
  be addressed," and fixed them. A visible plan -> implement -> self-review -> fix loop. That is exactly
  the incremental discipline you want, and it was the most transparent about it.
- **dsh** did careful per-requirement implementation and verified edge cases on its own (e.g. `rm 999`
  prints an error and exits 1, sibling notes stay open when one is marked done).
- **Claude Code (headless `-p`)** produced the fastest, cleanest, requirement-organized result, but its
  plan/to-do decomposition happens internally and is not streamed in headless mode, so this run did not
  surface it. To watch it decompose out loud you use interactive plan mode.

## Honest conclusion
On a medium spec, all three decompose well enough to finish. The earlier ranking (Claude Code best, by
design: plan mode + to-do list + subagents) is about *features for staying scoped on hard, long tasks*,
which this test did not stress. What this test adds: Aider's architect mode is the most transparent about
its incremental process, and a local 30B MoE (qwen3-coder) driving Aider handled a full 7-part spec
correctly. Style differences show in verbosity: Aider was leanest (188 lines), dsh most defensive (356).

Artifacts: the three `notes.py` files and transcripts live under `~/ai_bench/decomp-test/` on the test box.
