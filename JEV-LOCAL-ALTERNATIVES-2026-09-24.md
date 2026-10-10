# Local replacements for Jev: source audit and recommended trial

Start with a pinned Laya checkpoint on CPU, then compare AlexWortega's 0.8B
OpenJev classifier. Both are candidates for removing the hosted-key dependency;
neither has demonstrated useful loop detection in our harness. The hosted Jev
trial can stay pending without preventing local research.

This review retrieved public metadata for seven model repositories, pinned four
GitHub repositories, and saved 23 implementation/configuration/report files.
All seven model repositories reported `gated: false` and `private: false`.
Only metadata, documentation, and source were downloaded. No weights, packages,
or inference workloads were installed or run.

## Comparison for DARKTEXAS

Weight sizes below come from Hugging Face file metadata, not memory measurements.
Runtime tensors, loading copies, activations, and libraries require more memory.

| Candidate | Stored weights inspected | Serving approach | Assessment for our observer |
| --- | ---: | --- | --- |
| Laya multilingual, 322M | 0.600 GiB | Encoder plus decision heads; local Python or HTTP | First CPU candidate; explicitly manage context |
| Laya English / typed-decisions, 421M each | 0.785 GiB each | Same runtime, distinct checkpoints | Sequential comparison; keep only one loaded |
| NanoJev, 0.6B | 2.221 GiB | CUDA decision heads; custom batched schema | Secondary experiment; game-trained release |
| OpenJudgement-4B-Preview | 8.455 GiB | Qwen3.5 wrapper; one pass per question | Standalone GPU trial later, not first choice |
| AlexWortega/OpenJev 0.8B v5 | 1.589 GiB | NLI classifier and typed-decision adapter | Useful small-model comparison |
| lookski/OpenJev | Depends on base model | First-token logits from ordinary causal LMs | Mechanism baseline; not a separately trained decision model |
| openjev/openjev, 27B | 50.956 GiB | vLLM plus calibrated readout helper | Published serving configuration unsuitable for 12 GB VRAM |
| razorback16/OpenJev | Backend dependent | DiffusionGemma readout, or smaller encoder backends | Separate project; unnecessary complexity for first trial |

Primary identities: [Laya](https://github.com/NandhaKishorM/laya),
[NanoJev](https://github.com/TianyuCodings/NanoJev),
[OpenJudgement](https://huggingface.co/kitaniai/OpenJudgement-4B-Preview),
[AlexWortega](https://huggingface.co/AlexWortega/openjev),
[lookski](https://github.com/lookski/openjev),
[27B OpenJev](https://huggingface.co/openjev/openjev), and
[razorback16](https://github.com/razorback16/openjev).
The size records are preserved in each model's `metadata.json` under the source
archive named below. Public access was checked through anonymous requests.

## Laya: best starting point, with specific runtime changes

The repository declares Apache-2.0 and supplies local decision checkpoints.
Its reported 0.766 typed-decisions accuracy belongs to a task-fine-tuned
checkpoint; the English base scored 0.362 on that evaluation. These results do
not establish coding-harness accuracy. The English checkpoint defaults to 512
tokens; multilingual and typed-decisions default to 1024. Multilingual supports
an explicit larger limit. [Project documentation](https://github.com/NandhaKishorM/laya)

Our source inspection found these integration requirements:

- Set `LAYA_HOST=127.0.0.1`, `LAYA_DEVICE=cpu`, `LAYA_MODELS=multilingual`,
  `LAYA_PRELOAD=1`, and initially `LAYA_THREADS=4`. The thread count is a trial
  choice, not a measured optimum. Leave local API authentication unset.
- The stock server defaults to all-interface binding and preloading all three
  checkpoints. An unrecognized model name can fall back to automatic routing.
  Use an explicit checkpoint and verify the returned identity.
- The HTTP route calls `router.predict` without forwarding `max_len`. Merely
  sending a context override in the JSON body will not activate it. Use a small
  local wrapper with an explicit limit, or a direct Python call.

These findings are from the pinned
[HTTP server](https://github.com/NandhaKishorM/laya/blob/970dc8c5f63d7b886a68409493f37d569424f933/laya/serve.py).

The encoder input builder trims state to its remaining token budget. Our
observer's 16 KB transport cap therefore does not prevent semantic truncation.
Count tokens after formatting, preserve the latest results, and reject oversized
evidence rather than silently score an incomplete history. Start with short
fixtures, then test an explicit 2048-token multilingual profile. Loading uses
ordinary model parameters with device-dependent autocast; the small BF16 file
size is not a complete resident-memory estimate. Use the eager CPU path before
testing compilation or TileLang. [Input builder](https://github.com/NandhaKishorM/laya/blob/970dc8c5f63d7b886a68409493f37d569424f933/laya/common.py),
[runtime](https://github.com/NandhaKishorM/laya/blob/970dc8c5f63d7b886a68409493f37d569424f933/laya/agent.py)

The inspected package is 0.3.20. Its dependencies have broad lower bounds;
install into an isolated environment and record the resolved versions. A stock
GGUF/Ollama text-generation endpoint does not implement these decision heads.
[Package definition](https://github.com/NandhaKishorM/laya/blob/970dc8c5f63d7b886a68409493f37d569424f933/pyproject.toml)

## NanoJev: small architecture, specialized evidence

The published `unified-games-v1` checkpoint covers Maze, Snake, and two ViZDoom
tasks. Its gameplay results are evidence for those tasks, not our loop detector.
It batches candidate paths without generating answer tokens.
[Project and release instructions](https://github.com/TianyuCodings/NanoJev)

The audited entry point requires CUDA and explicitly rejects CPU fallback.
`--precision bf16` uses BF16 autocast while keeping parameter storage FP32.
Budget at least the approximately 2.22 GiB parameter storage plus runtime and
activation overhead. `--disable-native-triton` is the documented simpler path.
The protocol needs translation: `/api/evaluate`, a `states` array, `boolean`
questions, and response `probability` instead of Jev's `noul`.
[Inference implementation](https://github.com/TianyuCodings/NanoJev/blob/76fdfc9ecdca45a9bcef17991a07d3041a87685a/scripts/predict_toy_decisions.py),
[contract audit](https://github.com/TianyuCodings/NanoJev/blob/76fdfc9ecdca45a9bcef17991a07d3041a87685a/docs/TYPESAFE_CONTRACT.md)

## OpenJudgement: real weights, preview limitations

The Apache-2.0 release uses a merged Qwen3.5-4B derivative, preserving the
backbone and reading answer-index logits. It does not generate response JSON.
It handles multiple questions sequentially, not in one shared document pass.
The author describes calibration and quality as unfinished. Its reported 76.8%
test agreement is not a Jev comparison or coding benchmark. The model is text-only
through this API despite retaining multimodal weights.
[Model card](https://huggingface.co/kitaniai/OpenJudgement-4B-Preview)

Use the supplied wrapper, not `.generate()` or a generic classification pipeline.
The HTTP path is `/v1/judgments`, so a route adapter is required. Use one worker,
a bounded context, and a serial request queue. CUDA loads BF16; CPU loads FP32,
which would roughly double weight storage before overhead. The reference pins
Torch 2.8.0 and Transformers 5.17.0; keep them isolated from other harnesses.
[Runtime](https://huggingface.co/kitaniai/OpenJudgement-4B-Preview/blob/main/v4_model.py),
[server](https://huggingface.co/kitaniai/OpenJudgement-4B-Preview/blob/main/serve.py),
[requirements](https://huggingface.co/kitaniai/OpenJudgement-4B-Preview/blob/main/requirements.txt)

## OpenJev is several different projects

**AlexWortega:** trained NLI checkpoints in 0.8B, 2B, and 4B sizes. Each option is
evaluated as a hypothesis; a typed-decision wrapper normalizes the results. This
is promising as a comparison, not automatically a calibrated substitute. The
author reports prompt-injection weakness and explicitly discloses training on
test splits of several familiar benchmarks. Avoid those contaminated benchmarks
when evaluating it. [Model card](https://huggingface.co/AlexWortega/openjev)

Its wrapper returns a list of answers rather than our keyed Jev envelope, and
some answers omit `type`. Adapt the schema and probability meaning explicitly.
[Decision adapter](https://huggingface.co/AlexWortega/openjev/blob/main/code/openjev_decide.py)

**lookski:** a MIT interface using existing causal models, defaulting to
Qwen3-0.6B. The implementation scores first-token logits, processes questions
sequentially, and validates answer tokens. Its probabilities do not acquire
Jev's calibration merely by using the same response schema. Useful as a baseline.
[Source](https://github.com/lookski/openjev/blob/0eb596c5b7cc6b6483606b288a1c2418687a81a0/openjev/core.py)

**openjev/openjev:** a 27B trained model with non-commercial weights and a vLLM
helper. Its published H100 setup uses FP8, exact candidate logprobs, and specific
temperature/bias settings. Around 27 GB of FP8 weights alone exceeds our GPU;
quantization/offload would be a new configuration requiring new measurements.
The helper's defaults differ from its published calibration recipe.
[Serving requirements](https://huggingface.co/openjev/openjev/blob/main/serve/SERVE.md)

**razorback16:** a diffusion-model decision engine. Its primary path needs vLLM
read-only diffusion support, with an Apple MLX alternative and small encoder
backends. The Windows RTX machine gains little from adding this layer just to
reach Laya. [Project](https://github.com/razorback16/openjev)

## Changes needed in our harness

Our prepared observer intentionally pins a hosted URL, requires a TypeSafe key,
and only accepts `jev-1.13.0`. Changing an environment variable alone will not
switch it. Preserve that verified version and create a separate local-provider
adapter with a fixed loopback endpoint, checkpoint identity, and no key requirement.

```text
Recorded tool history -> existing repeat trigger -> local decision adapter
                                                     |
                                    Laya OR small OpenJev, serial
                                                     |
                                  validated probabilities -> log only
```

Retain payload limits, request budgets, failure handling, and unchanged tool
events. Add token-budget checks, served-checkpoint checks, and backend-specific
schema normalization. A client timeout does not necessarily stop a Python model
forward pass: do not enqueue a second inference until the first has completed
or its worker has been stopped and cleaned up.

The first evaluation should run the six existing diagnostic fixtures with the
coding model unloaded. Next use fresh labeled examples covering genuine stalls,
legitimate polling, changing test output, file edits, and adversarial tool text.
Measure false alarms, missed stalls, Brier score, latency, and peak memory against
the deterministic repeat trigger. Do not reuse Jev's 0.7 threshold as though it
were calibrated for another model. Reserve untouched cases before tuning.

CPU placement protects VRAM, but still consumes RAM and memory bandwidth needed
by A3B expert offloading. Keep inference serial and rerun the original memory
gates before each model load. A later integration can await the local observer
between coding-model steps; simultaneous generation remains disallowed.

## Evidence and current state

The read-only resource check found 10632 MiB free VRAM and 16240108 KiB free RAM
(about 10.38 GiB and 15.49 GiB). These are a point-in-time observation, not a
resource reservation or model-fit certification. No application was closed.

Source archive:
`C:\Users\kevin\ai_bench\jev-research-20260924\alternatives`

`manifest.json` records repository/model revisions; `code-manifest.json` records
the 23 retrieved files and hashes, with no remaining retrieval errors.
Model `metadata.json` files retain anonymous-access status and weight-file sizes.
The existing approved `fetch_public_sources.py` gained bounded alternatives
retrieval actions; it does not install packages or execute downloaded code.

This is a source audit and experiment recommendation. No local decision model's
speed, calibration, or coding usefulness has been measured on DARKTEXAS yet.
