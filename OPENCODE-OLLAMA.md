# opencode + local Ollama: why it "hangs", and how to fix it

Earlier notes here said opencode was unusable on local Ollama (it hung indefinitely). After researching
the issue tracker and testing on the box, that conclusion was **too strong**. The hang is real but mostly
fixable: it is a cluster of distinct causes, and with the right config + a native-tool-calling model,
opencode runs end to end against local Ollama. Verified 2026-09-09 on Windows (RTX 5070, Ollama 0.33.3,
opencode 1.17.15).

## What actually caused our hang (Windows)
Two config mistakes, both flagged by the community guide that works:

1. **`baseURL` used `localhost`.** On Windows, `localhost` can resolve to IPv6 `::1`, but Ollama listens on
   IPv4 `127.0.0.1`. The connection then stalls with no error - the request never reaches Ollama, which is
   exactly the "request never sent" symptom in the issue tracker.
2. **Missing `apiKey`.** The AI SDK's OpenAI-compatible provider requires an api key even for local use; if
   it is absent the provider can stall instead of erroring.

Fix: use `127.0.0.1` (not `localhost`) and set a placeholder `apiKey`. That alone took our run from a
12+ minute hang to a 13.8s completion.

## The other documented failure modes (so you can tell them apart)
- **#5674 - options not forwarded** (closed "not planned"): older opencode dropped the `options` block
  (baseURL/apiKey) before the request, so it went nowhere. Works in current versions with a proper options
  block; if you hit it, pin `@ai-sdk/openai-compatible` to a recent version in `~/.config/opencode/`.
- **#21903 - reasoning-field spin**: for THINKING models, Ollama returns a generic `reasoning` field that
  opencode's schema does not accept (it wants `reasoning_text`/`reasoning_opaque`), causing an infinite
  spin at high CPU. Avoid by using a non-thinking model, or a patched opencode.
- **#22132 - stream + many tools**: Ollama can stall when `stream=true` is combined with many tool
  definitions. Mitigate with a larger `num_ctx` (>=16k) and fewer tools.
- **Tool-calls-as-text (not a hang)**: small models (e.g. qwen2.5-coder:7b) emit the tool call as inline
  JSON in the message body instead of a native function call, so opencode prints it but never executes it.
  The file never gets written. Use a model with strong native tool-calling.

## Confirmed working recipe (this box)
`~/.config/opencode/opencode.json` (or project `./opencode.json`):
```json
{
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://127.0.0.1:11434/v1", "apiKey": "ollama" },
      "models": {
        "qwen3-coder:30b": { "name": "Qwen3-Coder 30b", "tools": true }
      }
    }
  }
}
```
Plus a decent context (`OLLAMA_CONTEXT_LENGTH=32768`, or bake `num_ctx` into a saved model variant).

## Measured results (2026-09-09)
| Config / model | Outcome | Time |
|---|---|---|
| `localhost`, no apiKey, qwen2.5-coder:7b | HANG (request never reaches Ollama) | killed >12 min |
| `127.0.0.1` + apiKey, qwen2.5-coder:7b | reaches Ollama, responds, but tool-call comes back as text and is NOT executed | 13.8 s |
| `127.0.0.1` + apiKey, **qwen3-coder:30b** | **full success - fizzbuzz.py created and runs correctly** | 40 s |

## Bottom line
opencode on local Ollama is usable if you: (1) use `127.0.0.1` + an `apiKey` placeholder, (2) give it a
model with real native tool-calling (qwen3-coder:30b worked; small coders emit tool calls as text), and
(3) keep context >=16k. Thinking models risk the reasoning-field spin - prefer non-thinking tool models.
