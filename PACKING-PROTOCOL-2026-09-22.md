# Bonsai packing continuation

The publisher provides PTQ1_0 and PQ2_0 ternary packings with different storage
and unpacking costs. Its measurements favor PQ2_0 on tested Blackwell GPUs;
that is a hypothesis for this RTX 5070, not a local result. Both require Prism's
runtime. See the [publisher model card](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf).

Local comparison pins the September 20 model revision
`6ed5e12bf84b7a63069882c91dd9e9218647d17b` and runtime release
`prism-b10709-9a9394a`. Existing PQ2 evidence and files remain untouched.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| PTQ1_0, installed and verified | 5946648928 | `53107f530aa52eb00912263ab1ee29bd199261c87cd7b4ad4ca1318c1fe33ee3` |
| PQ2_0, already installed | 7206168928 | `3907dc1658db1f78a9826bf8d5bcb8dc65db0d466388937af57f2294fae62ec1` |

The controlled question is memory/throughput and output validity with packing
changed. GPU contexts are 8192 and 32768; three fixed-prompt repetitions use
matched context, sampling, no-thinking settings, and runtime. Text, structured
tool-call and streaming controls must pass before performance interpretation.
Warmup, load time, prompt processing, generation time, token count, GPU/RAM
placement, cleanup and file hashes are recorded separately. Generated content
alone is not a coding-quality benchmark. An optional CPU-only 8192-context
treatment is reported separately from GPU comparisons.

The request sets cache_prompt=false; repeated prompt prefixes are reprocessed.
This avoids mixing prompt-cache reuse with packing speed. The pinned server's
[API documentation](https://github.com/PrismML-Eng/llama.cpp/blob/9a9394a895b96003ca842a6041cb28ac49a108f7/tools/server/README.md)
documents that behavior. Hash verification reads model files before loading,
so observed load times are not cold-filesystem-cache measurements. CPU cases
use 16 threads and explicitly disable GPU devices, KV and operation offload.

New runner defaults to preparation only; downloads and inference require
explicit flags. Execution waits until the current Go/LLM queue is finished.
Candidate work never mutates the old September 20 harness or result directory.

This does not isolate Prism versus stock llama.cpp runtime effects. That needs
one conventional GGUF supported by both pinned runtimes. Specialized CPU model
quality also remains a distinct experiment; packing results cannot answer it.

Execution correction: main-v1 sent an object-form tool_choice. The pinned
server warned and downgraded this to auto, so its apparent tool successes did
not establish the required-tool control. Preserve that run and exclude its
measurements from the corrected headline comparison. The pinned
[request parser](https://github.com/PrismML-Eng/llama.cpp/blob/9a9394a895b96003ca842a6041cb28ac49a108f7/tools/server/server-common.cpp)
expects a string; its
[tool-choice parser](https://github.com/PrismML-Eng/llama.cpp/blob/9a9394a895b96003ca842a6041cb28ac49a108f7/common/chat.cpp)
supports required. Main-v2 uses required with one declared function and parallel
calls disabled. It requires tool_calls termination and integer value 7.

The original CPU-only PTQ1 attempt timed out during its tool control at the
unchanged 120-second request bound. Both CPU packings receive their own corrected
cpu-ptq1-v2/cpu-pq2-v2 labels through --only, with the same CPU settings and
request limit, so one failure does not suppress the other packing's control.
Do not pool a short plain-control token rate with fixed-prompt repetitions.
