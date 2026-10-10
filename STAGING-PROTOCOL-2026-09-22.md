# One-shot versus staged repair protocol

This continues the deferred September 20 task-diversity comparison. It fixes
the deployment to the existing OmniCoder-9B Q4_K_M alias on Ollama and isolated
Pi 0.86.1. Exact model/runtime/configuration and source hashes are saved per run.

Five repair tasks cover graph scheduling, interval merging, CSV ledgers, account
event replay, and relative path normalization. Graph and interval tasks retain
their historical specifications/cases. The new domains have separate reference
implementations and scoring oracles, deterministic edge/random cases, public
controls, seeded faults and selected mutants. Controls pass after fixing an
initial path-output type error. Difficulty has not been empirically calibrated.

Each task has three fresh workspaces per treatment, 30 runs total. Each paired
task/repeat block randomizes treatment order using seed 20260922. Both treatments
use 180 seconds and a cumulative allowance of 16,000 completion tokens, with a
12,288-token per-request maximum reduced to the remaining allowance. Streaming
usage is required. Unknown usage stops requests in that trial. If caused by
the measured wall timeout or explicit STOP, the trial fails and its token count
is labeled incomplete; a fresh trial may proceed only after verified cleanup.
Missing usage without expected cancellation, or a backend overrun, stops the
experiment. Evaluator timeouts are candidate failures, not transport failures.

One-shot uses one Pi context to repair, test and audit. Staged uses three
separate contexts: read-only plan, implementation with that plan forwarded,
then audit. Process/context reset and plan transfer are therefore part of the
treatment. Both share the same cumulative budget; this is not a comparison of
wording alone. A one-token warmup precedes each measured run. Models unload
between runs. Only one inference workload may run at a time.

Transcripts, wire captures, prompts, hidden scoring and configuration live
outside candidate workspaces. This is an experimental convention, not a
security sandbox. First-artifact snapshots are polling observations and may
capture an intermediate write. Final correctness is scored separately from
clean agent termination, timeouts and quota failures. Success requires both
full correctness and clean completion of every required phase.

First run the two-run graph integration smoke with --smoke; exclude it from
the experiment. All 30 main runs use new workspaces and a distinct label.
Report task-level full-pass rates, paired success differences, time and tokens;
do not pool unequal hidden-check counts into a headline accuracy figure.

Commands from the repository root:

```powershell
python benchmarks/validate_staged_tasks_20260922.py
python -m unittest discover -s benchmarks -p test_compare_staging_20260922.py
python benchmarks/compare_staging_20260922.py --label prepared-v1
python benchmarks/compare_staging_20260922.py --label smoke-v1 --smoke --run
python benchmarks/compare_staging_20260922.py --label main-v1 --run
```

Labels refuse reuse. A STOP file inside the experiment directory requests
bounded cleanup. Files and results stay under ai_bench/staging-20260922.
This experiment does not evaluate Bonsai packing or specialized CPU models.
