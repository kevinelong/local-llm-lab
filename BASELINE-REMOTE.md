# Remote baseline: how do the locals compare to cutting-edge remote?

To answer "how close do local models get to the frontier," we ran the same 7-part `notes.py` spec
(see DECOMPOSITION-TEST.md) through cutting-edge remote options and lined them up against the locals.
Run 2026-09-09.

Remote entries added:
- **Codex** (OpenAI's agent CLI) driving **GPT-6 Astra** (`gpt-6-astra`, released 2026-09-03).
- **gpt-6-astra raw**: the same frontier model called once through the API with no agent loop, its code
  saved and tested. This isolates "raw frontier model" from "agent harness."

## Results: everything passed

| Entry | Type | Model | Location | Time | Lines | Result |
|---|---|---|---|---|---|---|
| Claude Code | agent | Claude | cloud | 58.5 s | 246 | PASS |
| gpt-6-astra (raw) | one-shot model | gpt-6-astra | cloud | 54 s | 291 | PASS |
| Aider architect | agent | qwen3-coder:30b | **LOCAL** | 114 s | 188 | PASS |
| dsh | agent | DeepSeek V4-Pro | cloud | 122 s | 356 | PASS |
| Codex | agent | gpt-6-astra | cloud | 176 s | 238 | PASS |

Every one produced a complete, correct `notes.py`: all 7 requirements, its own `test()` passes, commands
work, `notes.json` persists.

## What this tells us
- **On a well-specified medium task, the local model matched the frontier.** qwen3-coder:30b running on a
  12 GB GPU (via Aider) produced a result as correct as GPT-6 Astra, Claude, and DeepSeek V4-Pro. The
  frontier's advantage did not show up here.
- **Even a raw single-shot frontier call nailed it** (gpt-6-astra, no agent, 54 s, about $0.13 in tokens).
  A 7-part spec fits inside one frontier model turn, so the agent loop was not the deciding factor.
- **Where the remote edge actually lives:** harder and larger tasks (dozens of interdependent
  requirements, long-horizon work, ambiguous specs, deep debugging), and raw speed / not needing local
  hardware. This spec was not big enough to expose that gap. That is the honest limit of this test.
- **Cost:** the raw gpt-6-astra run cost about $0.13 (336 prompt + 2,563 completion tokens at $10/$50 per
  million). The local runs cost nothing but electricity. Codex (agentic, reasoning-high) used more tokens.

## Windows gotcha: Codex sandbox blocks everything
Codex on Windows first came up `sandbox: read-only` even with `-s workspace-write`, and its sandbox then
rejected every command ("blocked by policy"), so it could not even read the spec. It only worked after
`codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check`. Also, Codex ignores
`OPENAI_API_KEY` from the environment for its websocket transport; authenticate with
`printf %s $OPENAI_API_KEY | codex login --with-api-key` first (on PowerShell: `$env:OPENAI_API_KEY | codex
login --with-api-key`).

## Bottom line
For tasks of this size, a good local 30B MoE on a 12 GB box is competitive with the current frontier on
outcome. Reach for remote frontier models when the task is large, long-horizon, or ambiguous, or when you
need speed without tying up local hardware. Match the tool to the task, not the hype.

Follow-up: we then built a harder spec to find that ceiling, and it showed up cleanly - the local model
dropped to 8/10 while every frontier option held 10/10. See [HARD-SPEC-TEST.md](HARD-SPEC-TEST.md).
