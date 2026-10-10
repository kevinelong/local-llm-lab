# Overnight follow-up protocol, September 22

Authorized by the user: carry out the suggested next work overnight. Maximum
eight hours from worker launch, with one inference workload at a time. No
commits, publication, runtime upgrades, new model downloads, or unrelated app
closures are part of this queue. Current assets and historical results remain
unchanged. Frozen source and protocol live in the new overnight directory.

## 1. Validate the repeat guard and cleanup

The same Pi 0.86.1 extension loads for observation and intervention. It tracks
identical canonical PowerShell tool arguments together with the current SHA256
of solution.py. Three matching calls are allowed. The fourth is blocked with
a generic warning to examine prior output, change the diagnostic or code, or
finish. The fifth terminates the trial. Reads are not restricted. A changed
solution permits retesting. This is a narrow repeated-command control, not a
general loop detector or security sandbox. It never sees hidden test answers.

Unit controls verify thresholds, key ordering, changed artifacts, different
commands and observation-only behavior. A deterministic local mock drives
actual Pi and the extension through block/terminate and observe paths without
model inference. A separate owned-parent/child control verifies Windows tree
cleanup. A first preparation failed because taskkill stalled even outside the
sandbox. Its evidence is preserved, and it was never launched. The replacement
uses Windows Job Objects with a start handshake, kill-on-close, no breakaway,
and a kernel active-process count. Real Pi mock controls also run inside jobs.
See [Microsoft's Job Object documentation](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).
The v2 live smoke was deliberately stopped after it exposed cleanup bookkeeping
being mixed into artifact correctness. The replacement keeps those outcomes
separate and gives normal job accounting one second to settle before reaping.
It adds normal-process/scorer lifecycle controls. The v2 results are diagnostic,
not part of the replacement main comparisons; the frozen v2 inputs remain intact.

## 2. One fixed guarded integration smoke

One fresh graph pair: one-shot and staged, both guarded. Preserve the existing
OmniCoder alias, Ollama configuration, 32K context, temperature zero, 180-second
cumulative measured wall budget and 16K completion quota. Each run uses new
workspace/config and unloads the model afterward. The plan, implement and audit
contexts still share the same budgets. Guard-forced termination is failure.

The guarded 30-run study is eligible only if both smoke trials finish cleanly,
have positive, complete token counts, unchanged pinned inputs, working extension
logs and verified cleanup. Artifact correctness is reported but is not this
infrastructure gate. A failed smoke is not retried unchanged. The original
unguarded main comparison remains unstarted; no evidence is pooled across it.

## 3. Controlled guard ablation

Twelve fresh one-shot trials: graph and interval tasks, three technical repeats,
guard versus observation-only, paired with randomized order fixed by seed 260922.
The model, prompts, budgets and extension loading are identical across modes;
only blocking/warning/termination differs. Run regardless of smoke correctness
or guard-stopping outcomes, but stop on infrastructure failure. This tests
whether the intervention reduces repeated work and whether it changes correctness
or clean completion. Report within-task paired differences, not pooled check counts.
These are already-seen development tasks, not an unseen holdout. Deterministic
technical repeats are not independent samples of task diversity.

## 4. Guarded staging comparison, conditional

If the single smoke passes, run five existing repair tasks times two staging
treatments times three fresh workspaces: 30 trials. Both treatments use the
guard. Preserve the existing fixed task schedule, scorer and budgets. Hold this
entire batch if the smoke does not meet its prespecified gate. Preserve every
trial, including timeouts, partial token counts, incorrect artifacts and guard stops.

## 5. Slower CPU packing treatment

Run both pinned Bonsai packings independently at context 8192, 16 CPU threads,
GPU/KV/operation offload disabled, three fixed-prompt repetitions, required-tool
and streaming controls. The only intended change from the corrected CPU attempts
is a 600-second socket timeout, recorded in the new protocol and labels. Each
whole CPU job also has a 3600-second wall cap. A control timeout with verified
owned cleanup is a recorded bounded failure and does not suppress the other
packing. Other infrastructure failures stop the queue. Do not pool these results
with 120-second attempts or treat a plain-control token rate as the benchmark.

## Reporting and stopping

The worker updates status.json and REPORT.md, and each study writes its own
per-trial records. STOP in the overnight directory requests cancellation. The
worker forwards STOP to the active job; after 75 seconds it terminates only
that owned tree, unloads its own Omni alias when applicable, records the abort
and stops the queue. Aborted locks are preserved for inspection. Eight hours is
the work cap; allow bounded cleanup afterward. No automatic retry or tuning
based on outcomes. If the queue finishes sooner, it stays idle.
