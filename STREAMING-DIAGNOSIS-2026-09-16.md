# Diagnosis: large tool writes lose the streaming completion signal

## Confirmed finding

On Ollama 0.34.0 with the installed OmniCoder Q4_K_M model, the captured failing request tries to write the entire task-manager implementation as one tool call. A 4,096-token response allowance is insufficient for that response. The resulting incomplete tool-call JSON fails server-side parsing. The compatible streaming endpoint returns HTTP 200 and then ends without a finish reason or DONE marker, hiding the useful error from Pi.

This was reproduced directly against Ollama, without Pi and without the overnight relay. It is not explained by a general failure of tool calling: all 27 short native/JSON/stream controls in the overnight round passed.

## Controlled replay

Source: `ai_bench/overnight-20260916/runs/pi-omni-hard-16384-1/wire/67b06584b98647ab9bf9548cc5b7b5b7-request.json`.

| Request | Result | Seconds |
|---|---|---:|
| Compatible streaming, 4,096 output tokens | HTTP 200; no tool call, finish reason, usage, or DONE marker | 49.38 |
| Compatible non-streaming, 4,096 output tokens | HTTP 500; invalid write arguments, unexpected end of JSON input | 48.19 |
| Corrected native non-streaming, 4,096 output tokens | HTTP 500; same incomplete write-arguments JSON error | 47.20 |
| Same compatible streaming request, 8,192 output tokens | Valid write call, `finish_reason=tool_calls`, DONE marker | 91.25 |

The successful response used **8,101 completion tokens** and 2,530 prompt tokens. Its tool arguments decoded successfully and contained a 27,732-character `tasks.py`; that Python source passed syntax parsing. Syntax validity does not establish program correctness. Between the two streaming replays, only `max_tokens` changed.

The initial native control was invalid because it forwarded compatible content arrays to an endpoint requiring strings. Its HTTP 400 is a diagnostic-script error, excluded from the model conclusions. The corrected native control flattened text content and supplied the tool name, then reproduced the same HTTP 500 parsing error.

Raw requests, full responses, measurements, and cleanup records are saved at `C:/Users/kevin/ai_bench/stream-diagnosis-20260916`. Reproducer: `benchmarks/diagnose_stream_20260916.py`; it refuses to overwrite existing result labels.

## Practical implications

- Increasing input context from 16k to 32k did not fix the overnight failures because the response limit remained 4,096 tokens.
- Keep an adequate response allowance, but also make file edits in small increments. A larger allowance alone cannot guarantee that a future whole-file rewrite fits.
- Do not synthesize a successful completion signal for an unfinished tool call. The missing data is real, and no file was written in the failed overnight hard runs.
- For diagnosis, replay a failed streaming request without streaming to expose the server error. This is a diagnostic step, not an instruction to repeat every failed request automatically.
- The earlier 0/10 hard-task scores describe programs that were never created; they should not be interpreted as the models' demonstrated coding capability at those settings.

The overnight runner itself lowered the response allowance from the previous 8,192-token profile to 4,096. That experimental configuration exposed this failure. Increasing input context while leaving that output allowance unchanged tested the wrong lever for this particular problem.

The September 15 failures are consistent with this mechanism, but their exact requests were not captured. This diagnosis establishes the mechanism for the captured September 16 case; it does not prove that every previous streaming failure had the same cause.

## Mitigation trial

A separate Pi hard-task run used the same normalized OmniCoder 16k configuration and 4,096-token response limit, adding instructions to keep each tool call below about 1,500 tokens and build the file through small edits or appends. It still ended with the same streaming error after 50.02 seconds and produced no tasks.py (0/10). Prompt instructions alone did not enforce the desired response size.

A follow-up uses an 8,192-token response allowance and reserves 8,192 context tokens for output during compaction. This full-agent run changes both the response allowance and context reserve; the direct replay above isolates the response-allowance change. Raw traffic and external scoring are retained.

That 8,192-token full-agent follow-up also ended with a missing finish reason before writing the file. The direct captured request fit at 8,101 tokens, but a new agent run with a changed prompt need not produce the same program or response length. An 8k allowance is therefore sufficient for the demonstrated replay, not a universal fix. A final trial uses 32k context, 12,288 output tokens, and a matching 12,288-token compaction reserve.

### Final full-agent result

The 32k-context/12k-output trial completed **115 captured streams with 115 terminal signals**, with no missing-finish errors. It ran for **550.14 seconds**, executed 109 tool calls, encountered 24 tool errors, and ultimately stopped with a legitimate `length` reason. The resulting program scored **2/10** on the historical evaluator and **0/4** on supplemental checks. This establishes a working transport configuration for this trial, not a successful coding solution. The agent left a broken implementation after repeated repairs.

Ollama reported the model fully on GPU at 32k context (`size_vram == size`, about 6.41 GB model allocation). Total GPU memory sampled before unloading was 7,886 MiB. Cleanup unloaded the model and confirmed an empty resident list; desktop GPU usage returned to 1,592 MiB.

The practical conclusion is to treat the roomy profile as an integration/debugging option. Do not replace the existing coding setup on the strength of these results. The next meaningful quality comparison should hold this adequate response allowance fixed and test decomposition or a stronger coding model; another input-context sweep alone would not address the demonstrated failures.

Compact evidence is available in [stream-diagnosis.json](results/2026-09-16/stream-diagnosis.json). Full raw responses and generated programs remain local. The experiment did not patch Pi, synthesize terminal events, change global Ollama settings, or alter the historical scores.

## Experimental local profile

The local launcher now accepts:

```powershell
C:/Users/kevin/ai_bench/pi-local.ps1 -Model omni -Profile roomy
```

This profile uses the normalized `night-20260916-omni-32768` alias, 32k context, 12k output allowance/reserve, thinking disabled, and automatic retries disabled. It targets local Ollama directly; the diagnostic relay is not needed for normal use. `benchmarks/configure_pi_roomy_20260916.py` recreates it from the saved trial configuration. Both the standard and roomy launch paths returned Pi 0.85.1 during validation. Larger response headroom addresses truncation risk; it does not guarantee correct code or prevent repair loops.

Reference: [Ollama v0.34.0 compatibility conversion source](https://github.com/ollama/ollama/blob/v0.34.0/openai/openai.go) distinguishes content chunks from terminal chunks and maps the requested response allowance into the local request. The behavior above is based on saved local responses, not an assumption that the documented protocol was followed.
