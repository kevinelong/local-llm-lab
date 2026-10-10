# Harness tweaks: what we measured, what others found, what to adopt

2026-10-08. Written after the whole-history census, because "the model failed" turned out to be four
different things. Everything here is either measured on this box or cites the upstream report it came
from. Companion: `ai_bench/new-items-20261007/REPORT.md`.

## 1. Our own taxonomy, corrected

99 sub-perfect sessions, by the shape of the final assistant turn:

| Class | Sessions | What it is |
|---|---|---|
| **prose-quit** (text, no tool call, loop read it as done) | **50** | the model wrote a completion summary and stopped **while 1-8 hidden checks still failed** |
| **truncated-turn** (`stopReason=length`, no tool call) | 27 | reply cut inside its thinking by the reply cap or the context |
| **external kill** (`exit 143`) | 18 | resource guard or the wall |
| error/unknown stop | 4 | transport or engine |

**The correction:** I first read the prose-quits as the OpenHands class - a mid-task planning sentence
mistaken for completion. Our own closing texts say otherwise. Ten sampled across models and scores are
all *summaries*: "Solution complete", "solution.py repaired", "I have successfully implemented ...",
each followed by a bullet list of the fixes. The models believed they were finished. So this class is
**model self-verification failure** (they audited the cases they thought of, then declared victory), not
a harness misreading - and a nudge would mostly get "DONE" back. That matters for the ranking: the 1-8
check shortfall is a real capability difference, and it is exactly what `ledger2` now resolves.

The harness-mediated share is therefore 27 truncated + 18 killed = **45 of 99 (45 %)**, which is the
number to quote.

## 2. What others found

**OpenHands, "Asymmetric handling of content-without-tool-call responses terminates agents driven by
weaker/local models"** ([software-agent-sdk#3992](https://github.com/OpenHands/software-agent-sdk/issues/3992),
closed; fix attempted in [#3997](https://github.com/OpenHands/software-agent-sdk/pull/3997), closed
unmerged; independent reproduction in [#5510](https://github.com/OpenHands/software-agent-sdk/issues/5510)).
Their dispatcher classifies TOOL_CALLS / CONTENT / REASONING_ONLY / EMPTY, and *asymmetrically*:
EMPTY gets a corrective nudge ("Your last response did not include a function call or a message.
Please use a tool to proceed with the task.") and the loop continues, while CONTENT (prose, no tool
call) is treated as finished and terminates the run. Their controlled 2x2, four multi-file tasks per
cell: **OpenHands SDK x qwen3.6-coder 1/4 completions with 3/4 prose-quits; mini-SWE-agent 2.4.4 x the
same model 3/4 completions and 0 protocol failures**, because mini-SWE-agent's format-error loop
nudged and retried the same turns. Their own workaround: `tool_choice: "required"` makes the identical
model complete normally. The second reproduction (local `qwen3.8-27b`) is important for us: their
terminating turn was **577 completion tokens at 73k/255k context** - neither an output nor a context
limit. Their maintainer closed it: tool-calling reliability has improved, formats can be enforced, and
the Stop hook is the escape hatch.

*What applies here:* the mechanism is real and our relay controls the request body, so a bounded nudge
is implementable in our own code. But their failing turns were plans, ours are summaries, so the
expected gain is smaller; treat it as an experiment, not a fix. Design: nudge at most twice per
session when a turn has prose and no tool call, then accept the turn; measure on a model with a high
prose-quit rate (qwen3-coder-30b: six prose-quits, 59-67/70) against its own history.

**llama.cpp, "Qwen3.5 often prints tool calls in XML and stops when thinking is enabled"**
([#20837](https://github.com/ggml-org/llama.cpp/issues/20837)). The model emits the tool call *inside*
the thinking block, the server does not execute it, the client sees no tool call and the loop ends.
This is the class Strata's v0.1.40.1 rescue targets. **Not our failure mode:** a scan of 324 transcripts
for five markup shapes inside thinking blocks found **zero** occurrences, with or without a tool call in
the same turn. So we do not need markup rescue, and the earlier "0 of 26 sessions" finding holds at 12x
the coverage.

**llama.cpp `--reasoning-budget` is buggy in some builds**
([#22717](https://github.com/ggml-org/llama.cpp/issues/22717) "reasoning-budget stopped working";
[forge#54](https://github.com/antoinezambelli/forge/issues/54) "causes silent hangs after April 10
builds"). Our b11461 help documents `--reasoning-budget N` (-1 unrestricted, 0 immediate end, N>0
budget) and `--reasoning-budget-message MESSAGE` (a wrap-up line injected before the end-of-thinking
tag) - exactly the knob that fixed the Strata ledger - **but the flag must be verified by an actual
generation, never assumed.** Note also that a Debian manpage documents an older state where only -1
and 0 worked, so behaviour is build-specific.

**SWE-bench Verified** ([swebench.com/verified.html](https://www.swebench.com/verified.html)) evaluates
all LMs with **mini-SWE-agent in a minimal bash environment: no tools, no special scaffold structure,
just a simple ReAct loop**. The community's direction for comparability is *least* scaffold, which
supports our split of model behaviour from harness behaviour (the census) and argues against solving a
measurement problem with more scaffold.

**Also confirmed locally, from this build's own help:** context shift is **disabled by default**, so
KV-shift corruption is not one of our causes (it was a candidate). `--cache-reuse N` reuses cache via KV
shifting - deliberately left at 0 for long sessions.

## 3. Adopted here, with the evidence

| Tweak | Evidence it works |
|---|---|
| per-response cap 12,288 -> 32,768 | MiniCPM 217/221 with `paths` 75/75 (was 9/75 twice); gpt-oss 214/221; both 0 % collapse from 33 % |
| Strata `reasoning_budget_tokens: 6144` | 10/10 at 70/70; the truncation diagnostic still fires in 2 of 10 and **costs nothing** |
| ledger2 (226 checks) + repo (78) | reference 226/226 and 78/78 vs starters 62/226 and 43/78; reordered the top group |
| `quota_unknown` non-fatal | Kolibri's sweep aborted after three tasks on an engine usage gap; the declared change (precedent v8) completes it |
| context 32,768 -> 131,072 server **and** host, `--reasoning-budget 6144` | `provision-20261008-v1`: the served context, the launch command, the host descriptor and a returning generation are all verified from the run itself |

## 4. Deliberately not adopted

- **`--cache-reuse`**: KV shifting on long sessions, no evidence of need.
- **context shift**: already off by default.
- **`tool_choice: "required"`** (OpenHands' own workaround): it would make a text-only completion
  impossible, which is how every one of our tasks legitimately ends.
- **compaction**: the harness declares compaction off for a fixed no-compaction comparison; enabling it
  would test summarisation, not the window. It is a separate, declared arm if we ever want it.
- **raising the 720 s wall**: nothing has hit it since the ledger wall was raised to 3,600 s; the
  long-context task will decide whether it needs to move.

## 5. Next

1. **Nudge experiment** (design in section 2) on a high-prose-quit model - the only remaining candidate
   with a plausible mechanism behind it.
2. **The long-context task** is now unblocked: the served context is 131,072 with the host window to
   match, so a task whose prompt is 60-120k tokens can finally run and measure what the RAM bought.
3. Re-baseline **Strata** against the raised context: its runs used the same 32,768 window and are the
   ones the context cause actually injured.
