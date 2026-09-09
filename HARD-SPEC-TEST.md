# Hard spec: where the local model finally falls behind

The 7-part `notes.py` spec (DECOMPOSITION-TEST.md, BASELINE-REMOTE.md) was too easy - everyone passed. So
we built a genuinely harder spec and reran all five. Run 2026-09-09.

## The spec
`tasks.py`: a dependency-aware task manager (single file, stdlib only) with 16 requirements that are
actually interdependent and algorithmic: a task dependency graph, `done` blocked by open deps, a `ready`
set (deps all done), `plan` = a topological sort with priority tie-breaking, **dependency cycle
detection**, `rm` refusing to orphan dependents (with `--force` cleanup), longest-dependency-chain depth
in `stats`, CSV export/import round-trip, and a self-test. Full text: `spec2.md` in examples/.

## Scoring
A rigorous black-box evaluator (`examples/eval2.py`) runs 10 checks per implementation using distinctive
titles and exit codes (format-tolerant): self-test, dep validation, done-blocking, ready set, topological
plan validity, cycle detection, rm-dependents guard, export/import, persistence, and corrupt-file safety.

## Results

| Harness (model) | Location | Time | Lines | Score |
|---|---|---|---|---|
| gpt-6-astra raw (one-shot API) | cloud | 76 s | 661 | **10/10** |
| Claude Code (Claude) | cloud | 116 s | 777 | **10/10** |
| Codex (gpt-6-astra) | cloud | 337 s | 671 | **10/10** |
| dsh (DeepSeek V4-Pro) | cloud | 526 s | 1029 | **10/10** |
| Aider architect (qwen3-coder:30b) | **LOCAL** | 517 s | 571 | **8/10** |

## What separated them
All four frontier options scored a perfect 10/10. The **local** qwen3-coder:30b scored **8/10**, failing:
- **cycle_detected** - its `plan` did not error on a dependency cycle (either it skipped cycle detection
  or did not implement the `dep <id> --on <id>` edge command used to form the cycle). A real algorithmic
  miss and the exact kind of edge case a spec like this is designed to catch.
- **self_test** - its own `test` command exited 1, so its implementation has a bug its asserts caught (or
  the test itself is broken).

Everything else - dep validation, done-blocking, ready set, topological ordering, rm guard, CSV
round-trip, persistence, corrupt-file safety - the local model got right.

## The honest takeaway
This is the result the earlier tests predicted. On a well-specified *medium* task the local 30B matched the
frontier; on a *harder* task with real algorithmic depth (cycle detection, topological reasoning) it slips
to 8/10 while the frontier holds 10/10. Two more points worth noting:
- A **raw single-shot** gpt-6-astra call scored 10/10 in 76 s - the frontier model did not even need an
  agent loop for this.
- Score is not the whole story: dsh (10/10) took 526 s and 1029 lines; gpt-6-astra raw hit the same score
  in 76 s and 661 lines. Frontier models were both more correct and (the OpenAI ones) more concise here.

So: locals are genuinely useful and competitive up to a real complexity ceiling; past it, the frontier's
edge on correctness and edge-case reasoning shows, and it is worth the remote call. The generated programs
are in `examples/hard-spec-tasks/` so you can inspect exactly where the local one went wrong.
