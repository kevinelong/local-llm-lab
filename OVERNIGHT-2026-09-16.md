# Overnight follow-up plan

Authorized by the user on September 16: extend the research autonomously overnight using the most informative experiments.

## Questions

1. Does Ollama provide valid terminal events for a small tool call through its native, compatible JSON, and compatible streaming APIs?
2. Do Pi's failures persist on small Python 3.11 repair tasks, with normalized sampling, a 4096-token response limit, and retries disabled?
3. Which CPU thread count improves Smoffyy's warmed output rate on this machine?
4. Do 32k context and the strongest small-task models improve the original hard task across repeated runs?

## Run design

- Existing Qwen3.5 9B, OmniCoder 9B, and Smoffyy 4B weights; separate aliases preserve existing models/settings.
- 27 direct tool-call controls: three models, three API modes, three repeats.
- 18 repair runs: two tasks, three models, three repeats; 240 seconds each. External deterministic checks cover 55 dependency-graph cases and 61 interval cases. Scorers were checked against seeded bugs and known-correct implementations.
- 12 warmed CPU measurements: 4/8/16/24 threads, three repeats, explicit zero GPU layers and placement verification.
- Up to 12 hard-task runs: the top two models by mean repair pass fraction (clean finishes break ties), 16k/32k context, three repeats, 600 seconds each.
- Shuffled order with fixed seeds; temperature 0. Repeats test operational stability, not a broad stochastic capability distribution.
- Loopback relay records actual Pi requests and unmodified SSE output. Missing finish reasons are distinguished from client disconnects and timeout termination; raw captures support later diagnosis.

The coordinator has a five-hour experiment budget. An in-flight request and cleanup may extend shutdown slightly. It saves each result, updates the report, and unloads its own models after every experiment. Another resident model, low available RAM, or low free VRAM stops the suite instead of killing unrelated applications. It prevents automatic system sleep while running and releases that request on exit; it does not change the power plan or force the display to stay on. The worker is a separately launched hidden process; shutting down Windows stops it.

## Progress and output

- Worker: `benchmarks/overnight_20260916.py run`.
- Live state: `C:/Users/kevin/ai_bench/overnight-20260916/status.json`.
- Logs: `stdout.txt` and `stderr.txt` in that directory.
- Results: [incremental report](RESULTS-2026-09-16-OVERNIGHT.md), plus local `summary.json`, per-run artifacts, and raw wire records.
- Stop: create an empty `STOP` file in the local overnight directory. The runner stops its own agent process, unloads its models, and updates status.
- On a normal restart, completed records are skipped. An unfinished existing run directory is preserved and requires review before reusing its label. A stale lock after a crash also requires review; never start a second runner blindly.

No model weights or software upgrades are downloaded in this round. No automatic GitHub push is performed by the worker; its evolving report must be reviewed before publication. The previous published round remains unchanged.

Sources checked: [Ollama compatibility API](https://docs.ollama.com/api/openai-compatibility), [Pi model configuration](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/models.md), and the installed Pi 0.85.1 settings documentation.
