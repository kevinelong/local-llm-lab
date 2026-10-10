# Completion trace review, September 23

Evidence: ai_bench/overnight-followup-20260922-v3/staging/ablation, untouched.
The overnight queue finished at 00:18 PDT with empty resident-model/process lists.

## Paired development-task results

All 12 artifacts passed their external checks. Clean completion was baseline
3/6 and guard 4/6. Within task, graph changed 3/3 to 2/3; intervals changed 0/3
to 2/3. Technical repeats at temperature zero are not independent task samples.
Different paths and runtime nondeterminism remain possible sources of variation.

| Task / repeat | Baseline clean | Guard clean | Guard blocks | Interpretation |
|---|---|---|---:|---|
| graph / 1 | yes | yes | 1 | Recovered after warning; baseline also finished |
| graph / 2 | yes | yes | 0 | No intervention occurred |
| graph / 3 | yes | no | 2 | Guard terminated an already-correct artifact |
| intervals / 1 | no | no | 0 | Both reached wall limit |
| intervals / 2 | no | yes | 0 | Improvement without a guard intervention |
| intervals / 3 | no | yes | 0 | Improvement without a guard intervention |

The extension hashes solution.py; identical command strings across code edits
do not count as unchanged repeats. Interval guard repeat 1 made 79 PowerShell
calls but no command/artifact pair occurred more than twice. Baseline interval
repeat 3 made 88 calls, with each command/artifact pair occurring only once.
An exact-repeat guard cannot address this changing diagnostic work.

Baseline interval repeat 1 made 132 PowerShell calls: 119 silent successes,
including one identical command/artifact repeated 118 times. Repeat 2 made 135
calls, alternating two command strings 64/63 times. The output logs also show
invalid inline Python try/except and uncaught expected ValueError diagnostics.
These observations motivate a finite verification/completion instruction;
they do not establish why the model selected any particular action.

The new prompt-only comparison is specified in COMPLETION-PLAN-2026-09-23.md.
The original exact-repeat extension remains observation-only in both new arms.
Candidate prompts receive neither hidden checks nor external correctness scores.

## CPU controls

Both old 600-second CPU cases completed plain/tool/stream controls and three
fixed-prompt repetitions. Median generation PTQ1 0.6434 and PQ2 1.3884 tok/s;
median full-request latency 157.95 and 72.51 seconds. The required-tool control
took 430.43 and 193.14 seconds respectively, explaining the earlier 120-second
timeouts. Observed repetition RAM availability was only 0.30-0.55 GiB. Do not
attribute the speed difference solely to packing. Short 38-token input and
69-token output do not establish agent quality or long-context performance.

CPU-HEADROOM-PLAN-2026-09-23.md defines a separate reversed-order rerun. Its first
readiness check held before loading; no new CPU speed measurements exist yet.

## Go review

The complete-round invariant remains in src/search.rs: commit only a complete
root round; keep a completed learned one-ply round when deeper verification is
interrupted. The remaining development-probe miss at 200 ms was position
48d2d375f4b1-240: no root nomination timeout, 202.1 ms total, heuristic fallback
after the learned round failed to finish. At 400 ms all eight development
positions retained a learned round. This does not pass the original 200 ms
match gate (279/356 = 78.4%, requirement 80%).

All nine Python neural-deadline/cancellation regressions passed on September 23.
Fourteen focused Rust tests in WSL also passed, including complete-round
retention, partial-round rejection, ko transport and bounded slow reads.
No Go executable, search behavior, strength result, or release ZIP was changed.
Keep strength expansion held; next engineering evidence should isolate learned
evaluation cost on failed saved positions before changing search semantics.
