# RESUME: strata-20261005-v1

State: Strata v0.1.39 (Qwen3.8-Flash-Next Coder IQ1_M) is installed, configured, probed and
has completed the OMP `events` screen correctly. Read `REPORT.md` for results and `FLAGS.md`
for the flag research and the measured low-RAM investigation.

## Done (2026-10-06 UTC)

- Engine pinned and installed from the v0.1.39 tree (commit 6f32ec07, main == tag): flags
  `--family coder --model IQ1_M --context 32768 --vision no --low-ram on --kv int8
  --draft-vocab en --yes --no-start`, then `--calibrate` (12 -> 22.5 tok/s measured on this
  box; `--pcie-frac 0.75`, `--spec-min-p 0.50`, `--pool-workers 15`).
- Config `strata-coder-iq1_m.json` carries the declared sampling (temperature 1.0, top_p
  0.95, min_p 0.0, top_k 64), `open_browser` false, `--vram-reserve-mib 1500`,
  `--resident-budget-gib 4` and `STRATA_LOOKAHEAD=0`.
- The low-RAM variant was the real work: `--resident-experts` (setup's default), plain
  `--mmap-experts`, `--resident-budget-gib 20`, budget 20 again after the reboot, and finally
  budget 4 with the lookahead prefetch off. The first four each drove free physical to
  1.92-2.77 GiB against the 3 GiB floor; the last holds 9.6-10.4 GiB. No floor, metric or
  threshold was changed. Full table in `FLAGS.md`.
- Probe passed end to end: endpoint `/v1/models` lists the model, greedy answers repeat
  identically, the config sampling is read and per-request `seed` is forwarded, an OpenAI
  `tool_calls` echo is emitted with exact arguments, and the full tool roundtrip returns
  `STRATA_TOOL_OK`. Evidence: `probe/`.
- `screen events`: artifact correct, **76/76 checks passed**, 720 s wall, 4,895 tokens
  accounted, ~7 tok/s decode, expert cache 55-57% hit, `quota_unknown` from the engine's
  usage reporting. Min free physical 9.60 GiB, commit 10.09 GiB, GPU free 1.33 GiB. No guard
  trip. Evidence: `runs/oms-events/`, `oms-events/`.

## Open

- The three-task screen is complete: events 76/76, paths 75/75, ledger 7/70 (wall-bound at
  720 s; ledger needs more tokens than the wall allows at 6.5-9.6 tok/s). A longer-wall rerun
  of ledger is the only outstanding option, and it needs a deliberate wall change in a new
  root, not a silent edit.
- The minimal-startup suppression applied on 2026-10-06 was RESTORED the same day at
  13:13 UTC (`boot-status.json` -> `"state": "restored"`, verified, zero failures; the three
  startup shortcuts, the 13 user Run values and the packaged app startups are back and the
  `disabled-startup` folder is empty). No further reboot was needed or made. Both backups
  remain: `startup-backup.clixml` (2026-10-06) and `startup-backup-20260924.clixml`.
- `mimo-harness-20260925-v1/STOP` was a stale September stop that aborted every
  `lab.execute` session in 0.0 s; it is preserved as `STOP.stale-20260925-preserved` and the
  move is recorded in `evidence/stale-stop-moved.json`.
- Strata is slow on this box by design (disk-bound on a 12 GB card). Re-running with a
  64 GB module would allow a larger resident budget and the faster quants; that is a
  new-root job after the RAM upgrade.

## Operational state (2026-10-06, later)

- `omp` reported `Unable to connect` for `strata/qwen3.8-flash-next-coder-iq1_m` because nothing was
  listening on 127.0.0.1:8080: the engine process had exited (the prior session's service was stopped,
  and the .bat console the user launched afterwards had closed). Not a gate trip and not a config fault.
- Re-started with the same validated command and config (`strata-coder-iq1_m.json`: 32K, int8 KV,
  `--resident-budget-gib 4`, `--vram-reserve-mib 1500`, `STRATA_LOOKAHEAD=0`) and switched the OMP
  service to `detached` so it survives session end: `omp ps` shows `strata ready pid=33896 detached`.
- Verified end to end: `/v1/models` lists the model `loaded`; `curl /v1/chat/completions` returned
  `STRATA_LIVE_OK`; `omp --model strata/qwen3.8-flash-next-coder-iq1_m --no-session --no-tools -p`
  returned `STRATA_OMP_OK` (18 s). Resident footprint: free physical 10.29 GiB (initial gate 9),
  GPU free 1.29 GiB. Stop with `write proc://strata/kill` or `omp ps` when the session is done.

## Boundaries

One inference workload at a time, no second agent, no app kills, no gate change, no gate
metric change without an explicit instruction, no further reboot without an instruction.
Preserve every attempt in its own folder; `probe-*-guardstop` folders are the measured
guard trips and are evidence.
