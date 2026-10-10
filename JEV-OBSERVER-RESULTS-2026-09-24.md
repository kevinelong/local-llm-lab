# Jev observer: isolated Pi integration verified

The observation-only adapter loads in the installed Pi 0.86.1 and preserves
tool calls and results. Eleven offline checks and a native Pi event smoke test
pass. Live Jev scoring has not run: TYPESAFE_API_KEY was absent from both the
current process and Kevin's Windows user environment. No efficacy result exists.

## What is ready

The implementation is in
`C:\Users\kevin\ai_bench\jev-pi-observer-20260924-v1`.
It is a reduced adapter based on the loop-detection approach in
[MoonTory/pi-jev-harness](https://github.com/MoonTory/pi-jev-harness),
pinned upstream commit `8b05776a4302d6bfb891eaa1ef38f3d715f3ae45`.
See its `ATTRIBUTION.md` for scope and provenance.

```text
Pi tool calls + previous results
             |
      third identical call
             |
      bounded Jev assessment   [network disabled by default]
             |
      log probabilities only
             |
      original tool executes
```

This needs a custom isolated extension and explicit configuration, but no Pi
fork or global installation. It targets the separately installed 0.86.1; the
existing pi-local launcher remains on 0.85.1.

| Setting | Prepared value |
| --- | --- |
| Jev model | `jev-1.13.0`, explicitly pinned |
| API | `https://api.typesafe.ai/v1/systemone` |
| Observation mode | `log`, network disabled in the default profile |
| Candidate trigger | Third identical tool name and canonical input within the last 12 calls |
| Evidence | Bounded task, tool inputs, and prior text results, including changes |
| Decision | `stuck` and `wrong_approach` probabilities; log a flag at stuck >= 0.7 |
| Request bounds | One attempt per user turn; six per observer instance; serial |
| Timeout | Three seconds; no retries |
| Active interventions | None: no blocking, pruning, routing, prompt injection, or compaction |

If enabled, the assessment is awaited and can delay a triggering tool call by
up to the request timeout, plus local processing. Observation-only refers to
preserving the tool action and content, not zero latency. A logging or provider
failure lets the original tool proceed. Logs retain hashes and decision metadata,
not raw task/tool text. Live requests contain bounded text evidence; the prepared
replay sends only the six authored synthetic fixtures.

## Verification

The 11 offline checks cover invalid configuration, canonical repeat identity,
disabled networking, unchanged events, progress evidence, serial requests and
budgets, error redaction, response validation, endpoint/model pinning, aborts,
timeouts, and request size limits. Evidence: `evidence/tests.txt`.

The native smoke test uses Pi's installed extension loader and ExtensionRunner.
It registered the three intended events, registered no tools, preserved three
tool calls and three results, and recorded one decision through a mocked HTTP
response. It made zero real API calls and zero model-inference calls. Evidence:
`evidence/host-smoke.json`, with a separate copied source/config directory.
This verifies native loading and event dispatch, not a model-driven coding task.

No global harness settings were changed. No local model was loaded, and no
reboot or startup changes occurred in this phase. The A3B memory gates and
single-inference rule remain in force for any subsequent local-model trial.

## Resume

The bounded dispatcher is approved as one reusable command prefix:

```powershell
powershell.exe -NoProfile -File C:\Users\kevin\ai_bench\jev-pi-observer-20260924-v1\run.ps1 -Action Inspect
powershell.exe -NoProfile -File C:\Users\kevin\ai_bench\jev-pi-observer-20260924-v1\run.ps1 -Action Test
powershell.exe -NoProfile -File C:\Users\kevin\ai_bench\jev-pi-observer-20260924-v1\run.ps1 -Action HostSmoke
powershell.exe -NoProfile -File C:\Users\kevin\ai_bench\jev-pi-observer-20260924-v1\run.ps1 -Action ReplayLive
```

`ReplayLive` reads TYPESAFE_API_KEY from the process or Windows user environment,
then makes at most six serial requests. It enables networking only in that
replay process; the extension's saved network-disabled profile stays unchanged.
It exits without requests if the key is missing. A key in another secret store
requires its location, not disclosure of the secret in chat.

The six development cases comprise three apparent stalls and three legitimate
repetitions. Expected labels are excluded from the API payload. The report
compares the Jev flags with a simple always-flag candidate baseline (3/6 on this
balanced set). This small authored replay cannot establish coding improvement,
general accuracy, probability calibration, or a production threshold.

After successful transport and diagnostic scoring, the next experiment is a
serial, resource-gated coding comparison with the local model and harness held
fixed. Observation-only logging first measures usefulness and latency. Automatic
interventions need a separately defined treatment and held-out evaluation.

Further harness constraints remain documented in
[JEV-HARNESS-COMPATIBILITY-2026-09-24.md](JEV-HARNESS-COMPATIBILITY-2026-09-24.md).
