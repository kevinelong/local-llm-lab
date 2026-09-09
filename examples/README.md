# examples

The actual programs the agents produced in the head-to-head tests, plus the specs and the scorer, so you
can inspect exactly what each harness+model wrote (and where the local one fell short).

- `spec-notes.md` - the easy 7-part spec (`notes.py`). All five passed it (DECOMPOSITION-TEST.md,
  BASELINE-REMOTE.md).
- `spec2-tasks.md` - the hard 16-part spec (`tasks.py`) with a dependency graph, topological `plan`, and
  cycle detection (HARD-SPEC-TEST.md).
- `eval2.py` - the black-box scorer for the hard spec: `python eval2.py <dir-with-tasks.py>`.
- `easy-spec-notes/notes.<harness>.py` - the five easy-spec outputs (all scored functionally correct).
- `hard-spec-tasks/tasks.<harness>.py` - the five hard-spec outputs. Frontier ones scored 10/10;
  `tasks.aider.py` (local qwen3-coder:30b) scored 8/10 - compare its `plan` / cycle handling and its
  `test()` against the others to see the miss.

Harness -> model in these tests: claude = Claude Code (Claude), astra = raw gpt-6-astra one-shot,
codex = Codex CLI on gpt-6-astra, dsh = DeepSeek Harness on DeepSeek V4-Pro, aider = Aider on the LOCAL
qwen3-coder:30b.
