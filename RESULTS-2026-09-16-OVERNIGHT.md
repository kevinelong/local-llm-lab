# Overnight local AI experiments: September 16, 2026

Follow-up diagnosis: [large tool writes were truncated by the response allowance](STREAMING-DIAGNOSIS-2026-09-16.md). The 4,096-token output limit caused a captured write to fail parsing, and the streaming endpoint hid the useful error. Treat the hard-task zeros as configuration/integration failures, not a general coding-capability ranking.

Status: **complete**. Updated 2026-09-16T13:31:01.525688+00:00.

## Design

One workload at a time; five-hour ceiling. Existing weights only. Raw native/JSON/SSE tool-call controls, repeated Python 3.11 bug repairs with external deterministic checks, CPU thread sweep, then 16k/32k hard-task trials on the two strongest repair candidates. Temperature 0 and sampling parameters are normalized using separate aliases; no global server settings are changed. Trials repeat deterministic configurations to measure operational stability, not stochastic model quality. Order is shuffled with a recorded fixed seed.

Pi sends an explicit 4096-token response cap and reasoning_effort=none. Compaction reserves 4096 tokens. Retries are disabled so failures remain visible. A loopback relay captures the actual request and raw SSE; it forwards without repairing or synthesizing finish events. Relay transport overhead and altered configuration mean these are not exact repetitions of September 15.

Raw records, wire captures, configurations, generated programs and evaluators: `C:/Users/kevin/ai_bench/overnight-20260916`. A STOP file there requests cancellation. External scorers are outside candidate workspaces. A score alone is not a successful agent run.

## Coding trials

| Run | Checks | Clean finish | Seconds | Error / stop |
|---|---:|---|---:|---|
| pi-omni-graph-16384-1 | ?/? | False | 16.0 | Command '['C:\\Program Files\\Python311\\python.exe', 'C:\\Users\\kevin\\local-llm-lab\\benchmarks\\night_tasks_20260916.py', 'graph', 'C:\\Users\\kevin\\ai_bench\\overnight-20260916\\runs\\pi-omni-graph-16384-1\\solution.py']' timed out after 20 seconds |
| pi-omni-graph-16384-2 | 55/55 | True | 14.0 | stop |
| pi-omni-graph-16384-3 | 55/55 | True | 14.0 | stop |
| pi-omni-hard-16384-1 | 0/10 | False | 52.0 | error |
| pi-omni-hard-16384-2 | 0/10 | False | 50.0 | error |
| pi-omni-hard-16384-3 | 0/10 | False | 50.0 | error |
| pi-omni-hard-32768-1 | 0/10 | False | 50.0 | error |
| pi-omni-hard-32768-2 | 0/10 | False | 50.0 | error |
| pi-omni-hard-32768-3 | 0/10 | False | 50.0 | error |
| pi-omni-intervals-16384-1 | 61/61 | True | 22.0 | stop |
| pi-omni-intervals-16384-2 | 61/61 | True | 18.0 | stop |
| pi-omni-intervals-16384-3 | 61/61 | True | 16.0 | stop |
| pi-qwen-graph-16384-1 | 55/55 | True | 16.0 | stop |
| pi-qwen-graph-16384-2 | 55/55 | True | 18.0 | stop |
| pi-qwen-graph-16384-3 | 55/55 | True | 14.0 | stop |
| pi-qwen-intervals-16384-1 | 21/61 | True | 22.0 | stop |
| pi-qwen-intervals-16384-2 | 21/61 | True | 20.0 | stop |
| pi-qwen-intervals-16384-3 | 17/61 | True | 20.0 | stop |
| pi-smoffyy-graph-16384-1 | ?/? | False | 240.9 | Command '['C:\\Program Files\\Python311\\python.exe', 'C:\\Users\\kevin\\local-llm-lab\\benchmarks\\night_tasks_20260916.py', 'graph', 'C:\\Users\\kevin\\ai_bench\\overnight-20260916\\runs\\pi-smoffyy-graph-16384-1\\solution.py']' timed out after 20 seconds |
| pi-smoffyy-graph-16384-2 | 10/55 | False | 120.0 | length |
| pi-smoffyy-graph-16384-3 | 55/55 | True | 34.0 | stop |
| pi-smoffyy-hard-16384-1 | 0/10 | False | 34.0 | error |
| pi-smoffyy-hard-16384-2 | 0/10 | False | 34.0 | error |
| pi-smoffyy-hard-16384-3 | 0/10 | False | 36.0 | error |
| pi-smoffyy-hard-32768-1 | 0/10 | False | 34.0 | error |
| pi-smoffyy-hard-32768-2 | 0/10 | False | 36.0 | error |
| pi-smoffyy-hard-32768-3 | 0/10 | False | 34.0 | error |
| pi-smoffyy-intervals-16384-1 | 61/61 | True | 36.0 | stop |
| pi-smoffyy-intervals-16384-2 | 61/61 | True | 26.0 | stop |
| pi-smoffyy-intervals-16384-3 | 61/61 | True | 18.0 | stop |

## Direct tool-call transport controls

Recorded 27 probes; 27 correct tool calls; 27 explicit terminal signals.

- qwen, native: 3/3 correct; 3/3 terminal signals.
- qwen, json: 3/3 correct; 3/3 terminal signals.
- qwen, stream: 3/3 correct; 3/3 terminal signals.
- smoffyy, native: 3/3 correct; 3/3 terminal signals.
- smoffyy, json: 3/3 correct; 3/3 terminal signals.
- smoffyy, stream: 3/3 correct; 3/3 terminal signals.
- omni, native: 3/3 correct; 3/3 terminal signals.
- omni, json: 3/3 correct; 3/3 terminal signals.
- omni, stream: 3/3 correct; 3/3 terminal signals.

## CPU-only thread sweep

| Threads | Completed repeats | Median output tok/s | All placements CPU-only |
|---:|---:|---:|---|
| 4 | 3 | 9.97 | True |
| 8 | 3 | 11.71 | True |
| 16 | 3 | 11.99 | True |
| 24 | 3 | 11.63 | True |

## Interpretation limits

12/30 completed coding records both finished cleanly and passed all external checks. 12 captured agent streams lacked a finish reason; some may be intentional client disconnects or timeouts, so inspect the associated error and raw capture before attributing blame.

Small repair checks are separate from the historical hard-spec score. The historical scorer can award a rejection point to broken code; hard-task success also requires all four supplemental checks. CPU tests include a warm-up and use the same prose prompt; speed alone does not measure answer quality.

Sources consulted: [Ollama compatibility](https://docs.ollama.com/api/openai-compatibility), [Pi model configuration](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/models.md). No new external model benchmark claims are inferred from these sources.
