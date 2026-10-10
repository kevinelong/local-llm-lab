# Follow-up results, September 23

The frozen completion experiment finished all four smoke trials and twelve
paired trials. Source hashes and all trial cleanup were verified afterward;
no model process, resident Ollama model, or run lock remained. Historical
experiments were not overwritten. No commit, release publication or Go search
change was made.

## Prompt-only completion comparison

The intervention specifies a finite verification procedure: public tests,
one extra diagnostic file, explicit expected-exception checks, no unchanged
successful retests, and a final summary or an honest unresolved-issue report.
Both arms use the same observation-only extension; neither has forced guard
termination. Model, runtime, budgets, scorer and task fixtures are held fixed.

| Task | Baseline correct | Completion correct | Baseline clean | Completion clean |
|---|---:|---:|---:|---:|
| graph | 1/3 | 3/3 | 1/3 | 3/3 |
| intervals | 3/3 | 3/3 | 0/3 | 3/3 |
| Total | 4/6 | 6/6 | 1/6 | 6/6 |

All six completion trials were both correct and clean, with complete token
accounting. Five matched pairs improved clean completion; one tied. In the
tied pair the new instruction took 27.1 seconds longer. Median measured elapsed
time was 47.0 seconds with the instruction versus 180.0 seconds baseline; five
baseline trials reached the wall limit. This is censored task-completion time,
not a claim about inference throughput. The slowest completion trial took 54.4
seconds. No instruction-based forced stop was counted as success.

These are three technical repeats on two already-used development tasks.
They support retaining the procedure as an experimental one-shot option, not a
general agent ranking or a statistically established gain across unseen tasks.
Workspace paths, runtime nondeterminism and changing desktop memory pressure
remain limitations. Available physical RAM before smoke trials was 4.72-5.45 GiB.
No prompt tuning or unchanged retries occurred after observing these outcomes.

## Why the larger staging study stays held

All four smoke artifacts were correct, but only three trials completed cleanly.
The staged graph audit repeatedly rewrote diagnostic.py and exhausted its time
budget; its interrupted request left token usage incomplete. The new procedure
therefore helps the tested one-shot runs but has not solved staged audit loops.
The fixed gate requires all four smoke trials to succeed, so no 30-run staging
batch was started. The failed smoke remains part of the record.

Protocol: [completion plan](COMPLETION-PLAN-2026-09-23.md).
Raw outcomes and paired differences:
[experiment report](../ai_bench/completion-20260923-v1/REPORT.md).
Trace diagnosis: [review](COMPLETION-REVIEW-2026-09-23.md).

## CPU rerun readiness

The memory-qualified runner is prepared at
`C:/Users/kevin/ai_bench/cpu-headroom-20260923-v1`.
It prescribes two reversed-order rounds, PTQ1/PQ2/PQ2/PTQ1, with three measured
responses per fresh server and the original plain/tool/stream controls.
The required initial headroom is 14 GiB physical and 10 GiB commit; running
headroom must stay above 3 GiB for both. Windows page/commit counters and owned
process cleanup were exercised; threshold boundary checks passed.

After the LLM queue unloaded, the readiness check saw 7.16 GiB physical and
11.32 GiB commit headroom. It held before loading a CPU model; no new CPU
throughput result exists. The user is freeing memory. The exact current status
is in the CPU directory's status.json; do not lower the threshold after seeing
these results. The earlier memory-constrained CPU results remain separate.

Run the frozen CPU driver only after its headroom gate passes:
`python C:/Users/kevin/ai_bench/cpu-headroom-20260923-v1/source/cpu_headroom_20260923.py run`

## Go gate review

Nine Python neural-deadline/cancellation tests and fourteen focused Rust tests
in WSL passed. The Rust checks include preserving a completed learned round
after interruption, rejecting mixed-depth partial rounds, bounded slow socket
reads, and full ko history transport. This confirms the existing fallback
invariant; it does not improve throughput or provide new strength evidence.

The original 200 ms match retention remains 279/356 = 78.4%, below the 80% gate.
The saved 200 ms development miss occurs during learned-round completion,
without a root nomination timeout. The 400 ms development probes retained all
eight rounds but remain a different budget treatment. Larger matches stay held.
