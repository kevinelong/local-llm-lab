# Staging integration smoke, September 22

The user authorized closing Comet. Normal close requests eventually closed all
Comet processes; available RAM rose to 5.56 GiB. Other applications were left
open. The initial memory block is resolved.

Smoke-v3 passed preflight, but Ollama 0.34.2 failed during CUDA warmup with
`shared object initialization failed`. No agent phase ran. Cleanup unloaded
the alias. After Comet fully exited, unchanged smoke-v4 loaded successfully;
that retry alone does not identify the cause of the earlier failure.

| Smoke-v4 treatment | Artifact checks | Wall seconds | Completion tokens | Clean finish |
|---|---:|---:|---:|---|
| Staged | 53/55 | 180.08 | 5460, complete | No |
| One-shot | 55/55 | 180.19 | 5648, incomplete | No |

Both exhausted the shared 180-second wall budget. Each repeated its own same
cycle-check command 60 times. Staged finished planning but never reached audit;
its artifact missed two cycle cases. One-shot's final artifact passed every
graph check, but its last interrupted response left usage unknown. Correctness
and successful agent termination are separate outcomes. This single diagnostic
pair does not establish a treatment winner.

The staged timeout exposed an infrastructure issue: Windows sandbox denied
taskkill /T. The owned parent exited and a separate elevated process query
found no remaining direct children. The historical result is retained, including
the denial. The runner now stops future batches when a phase or evaluator's
process-tree cleanup fails or times out. All 12 runner regressions pass. No
historical source snapshot or trial was rewritten.

The clean-completion integration gate did not pass, so the 30-run main-v1
comparison remains unstarted. A future harness intervention should address
repeated ineffective tool use, use a fresh protocol/label, and preserve this
baseline. Do not simply rerun unchanged smoke until a favorable outcome appears.

Evidence: `C:/Users/kevin/ai_bench/staging-20260922/smoke-v3` and `smoke-v4`.
Both smoke-v4 model unload checks passed and its pinned inputs stayed unchanged.
The Bonsai packing comparison is independent and uses its own runtime and model.
