# Bonsai packing results, September 22

Evidence: `C:/Users/kevin/ai_bench/packing-20260922`. Run status: main-v2=complete, cpu-ptq1-v2=failed, cpu-pq2-v2=failed.

| Packing | Context | Device | Reps | Median generation tok/s | Median request ms | GPU delta MiB |
|---|---:|---|---:|---:|---:|---:|
| PQ2 | 32768 | GPU | 3 | 52.93 | 1801.2 | 8649 |
| PQ2 | 8192 | GPU | 3 | 54.86 | 1848.7 | 7455 |
| PTQ1 | 32768 | GPU | 3 | 49.70 | 1729.0 | 7920 |
| PTQ1 | 8192 | GPU | 3 | 54.30 | 1610.0 | 6373 |

Incomplete case PQ2-ctx8192-ngl0: TimeoutError('timed out').
Incomplete case PTQ1-ctx8192-ngl0: TimeoutError('timed out').

Both corrected CPU controls passed plain text but timed out on the required-tool request at the 120-second bound, before any fixed-prompt repetitions. This does not measure their unconstrained CPU throughput.

GPU delta is whole-device usage relative to the pre-load snapshot, not a process-isolated allocation.
Missing GPU telemetry samples: 1. Memory medians use only successful queries; raw failures remain recorded.
Three repetitions use one fixed short prompt with cache_prompt=false, seed 260922, temperature zero, and no thinking.
The context column is allocated capacity; this does not measure long-prompt processing or long-context quality.
CPU runs use 16 threads and disable GPU, KV, and operation offload. Report them separately from GPU.
Controls cover exact plain text, forced tool JSON, and streamed tool-call reconstruction.
All observed generated texts identical: True. This finite observation does not prove mathematical equivalence or general coding quality.
Source/model/runtime hashes, load times, placement logs and raw responses are retained. File hashing warmed the filesystem cache.
Run order was fixed; system memory pressure and application activity limit speed comparisons. No stock-versus-Prism runtime conclusion follows.

The preserved main-v1 run used an unsupported object-form tool_choice that the server downgraded to auto. Its observations are excluded from this table.
Main-v2 and both cpu-*-v2 runs use the supported required string with one available tool. Each measured case must pass these corrected controls first.
CPU-only PTQ1 in main-v1 passed plain text at about 0.61 generated tokens/s, then its tool-control request timed out at 120 seconds. No fixed-prompt repetitions were reached; this is not a matched throughput result.

Final cleanup: no active model processes or run locks; Ollama has no resident model.
Available RAM: 10.64 GiB. GPU and source verification are recorded in final-cleanup-v2.json.
