# Completion follow-up, September 23

User authorized all proposed follow-up work. One coordinating writer; serial
inference. Preserve all previous source snapshots and results. No publication.

## Evidence and intervention

Overnight v3 finished at 00:18 PDT September 23 with verified cleanup. All 12
ablation artifacts were correct. Clean completion: baseline graph 3/3,
intervals 0/3; guard graph 2/3, intervals 2/3. The two improved interval trials
never triggered a guard block. This is not evidence that blocking caused their
improvement. Graph repeat 3 was terminated by the guard despite correct code.

Trace inspection found 118 repetitions of a silent successful Python call in
intervals baseline repeat 1, and alternating commands 64/63 times in repeat 2.
Other runs kept inventing diagnostics, including invalid inline try/except
syntax and uncaught expected exceptions. These are observed behavior patterns,
not access to the model's internal reasoning. Artifact correctness is known
only to the external scorer and is never fed to the candidate.

Test one prompt-only completion procedure: run the public test file after the
final edit, group extra assertions in diagnostic.py, catch expected exceptions,
do not repeat unchanged successful checks, and finish with results or unresolved
issues. The exact instruction is frozen in the driver and per-suite protocol.
No new runtime guard is enabled. Both arms load the same observation extension.
Baseline prompts remain byte-identical to the previous baseline. Same pinned
Omni alias, Pi 0.86.1, 32K context, temperature zero, 180-second wall and 16K
cumulative completion budget. Each trial uses a new workspace and unloads.

## Fixed schedules and gate

1. Four diagnostic trials: graph and intervals, one-shot and staged, all with
   the completion instruction. This checks both previously problematic tasks.
2. Twelve one-shot trials: two tasks x three technical repeats x baseline or
   completion instruction. Adjacent pairs randomized with seed 260923.
3. Thirty staging trials on all five existing tasks only if all four smoke
   trials succeed cleanly with complete positive token counts and unchanged
   inputs, all six completion-arm artifacts are correct, at least five of six
   complete cleanly, and completion does not regress versus baseline within
   either task. Both staging treatments receive the completion instruction.

Smoke and main evidence remain separate. No unchanged retries or gate changes
after outcomes. Technical repeats are not independent tasks or a holdout.
Report correctness, clean completion, paired differences and time separately.
Stop on infrastructure failure, STOP file, or three-hour queue cap (plus bounded
trial cleanup). Windows Job containment and existing integration controls apply.

## CPU and Go gates

CPU reruns use the same pinned runtime, models, 8K context, 16 threads and
600-second request timeout. Require at least 14 GiB free physical RAM before
loading and 3 GiB free while loaded; otherwise hold or stop with no valid speed
comparison. Record memory continuously, including commit and page activity.
Do not close unrelated apps without authorization. Run both packings in opposite
orders across two rounds if headroom permits; report these separately from the
memory-constrained September 22 results.

Go strength expansion remains held at the original 200 ms gate: NN retention
279/356 = 78.4%, below 80%. The existing 400 ms development probe (8/8 retained)
is a separate budget treatment, not a pass at 200 ms. Review deadline tests and
saved failure telemetry before changing search or ordering more matches.
