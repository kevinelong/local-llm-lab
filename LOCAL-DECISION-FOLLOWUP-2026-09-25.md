# Local decision follow-up - September 25, 2026

Completed and cleaned up. Full report and evidence:
[REPORT.md](../ai_bench/local-decisions-followup-20260925-v1/REPORT.md).

- Stuck-only OpenJev preserved all 46 synthetic probabilities exactly.
  Paired median fell from 4.04s to 3.03s; warm p95 3.34s still fails the 3s gate.
- 18 windows from real archived coding traces were newly used for judging,
  with four stalls and 14 legitimate retries/progress windows labeled before
  inference. OpenJev at the frozen 0.85 threshold caught 0/4 stalls, with
  0/14 false alarms. Median 11.26s, p95 18.05s. Same decisions as never flag.
- Deterministic identical-failure/no-successful-mutation rule caught 1/4
  stalls, with 0/14 false alarms. Successful-output loops are outside its
  scope. Six behavior checks passed. It is an offline candidate, not installed.
- One reviewer, small correlated archival sample, compact history format;
  this does not establish general effectiveness or live coding improvement.
  Thresholds were not retuned. All 12 recent calls retained; excerpts shortened
  explicitly, full identities retained through equality IDs; max 1,888 tokens.
- Serial CPU float32, four threads; unchanged memory gates. Peak owned-tree
  private memory 4.50/4.78 GiB. No aborts. Ten owned process identities absent,
  port 8098 closed, lock removed. All 19 prior source hashes and 34 archival
  source hashes verified. No reboot, startup changes, or global hooks.

Do not promote OpenJev to automatic interruption. Next useful experiment:
cheap observation-only logging that separates unchanged failures from
successful-output loops, followed by independent labels from new sessions.
Do not tune a broader rule on these cases and call them validation.
