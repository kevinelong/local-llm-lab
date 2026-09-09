# Transparent decomposer prompt

A prompt preamble that makes an agent externalize its decomposition into a visible, reviewable plan and
work incrementally, instead of one-shotting the whole task. Especially useful for Claude Code in headless
`-p` mode, where the internal to-do list is not streamed.

Confirmed on DARKTEXAS (2026-09-09): with this preamble, `claude -p` produced a `PLAN.md` of 11 small
steps each mapped to a requirement, worked through them, and still produced correct code. Cost: about 133s
vs 58s without it, because transparency means more output.

## Preamble (append to your task prompt)

```
Be a transparent, incremental decomposer:
1. Before writing any code, break the task into a short numbered plan of small steps and write it to PLAN.md.
2. Implement one step at a time. Print "STEP n: <desc>" before each step and "STEP n DONE" after.
   Keep steps small and do not jump ahead.
3. At the end, check each requirement against your plan and report pass or fail per requirement.
```

## Example
```
claude -p "Read spec.md and implement it as notes.py. <paste the preamble above>"
```

## Alternative: stream the internal steps
```
claude -p "<task>" --output-format stream-json
```
(or add `--verbose`). This streams Claude Code's internal TodoWrite / tool events so you watch the to-do
list form and get checked off live. Use the PLAN.md prompt when you want a durable artifact; use
stream-json when you want to watch it work interactively. They combine.

## Why it helps
The model only predicts text, so "planning" is not automatic in a single-shot call. Forcing an explicit
PLAN.md plus per-step markers makes the decomposition visible and reviewable, and nudges the model to keep
steps small instead of trying to emit everything at once. It also gives a human a natural gate: read
PLAN.md before letting it code.
