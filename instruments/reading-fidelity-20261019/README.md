# reading-fidelity-20261019: can a local model read a long document as faithfully as the cloud agent?

Run 2026-10-19. Question: the work we do together is mostly *reading something long and reporting it
exactly*. Which parts of that can a local model do equally well? The 414-check suite could not answer it -
our top local group already scores 414/414 and 692/693, i.e. it is at the instrument's ceiling, so there is
no headroom to detect a difference. This instrument asks instead about the failure mode that actually
produced bad numbers in this lab: a figure that gets **revised late in a long document**, and a two-sided
numeric comparison that can be **inverted**.

## Design

- **Document:** `local-llm-lab/NEWS-2026-10-19.md`, 50,804 chars (~17.3k tokens as sent) - one day's news
  scan, dense with numbers, containing a retraction, a correction, a trap, and one detail that appears in
  exactly one sentence.
- **Nine questions** (`prompt.txt`): eight answerable from the text, one a trap (Q8, "is Q4_K named among
  the fast-path kernels?" - the answer is no, and the document says so explicitly).
- **Ground truth:** `ground-truth.md`, written before either arm ran.
- **Arms**, identical prompt text, temperature 0, no web, one sample each:
  - **local:** Qwen3-30B-A3B-Thinking Q4_K_M, llama.cpp b11461, `-ngl 99 --cpu-moe -c 32768`, text inlined.
  - **cloud:** the session's own model (DeepSeek V4.1 Flash) through `omp -p --no-skills`, reading the same
    prompt file. Tool use permitted; neither arm needed anything beyond the text.

## Result

| arm | wall | completion tokens | score |
|---|---|---|---|
| cloud (DeepSeek V4.1 Flash, OMP) | **9.9 s** | ~700 | **9/9**, with the capability-check nuance in Q6 |
| local (Qwen3-30B-A3B Q4_K_M, llama.cpp) | 86.3 s | 2,529 | **7/9 + 1 partial** |

Local was right on Q1, Q2, Q3, Q5, Q6, Q8 (the trap), Q9 - including the retraction and the +22.6 %
correction, i.e. **it did not lose the revised figure**. Its two failures are exactly the class this
instrument was built to catch:

- **Q4 - substituted a date for a build id.** Asked "from which build does it land", it answered with the
  merge timestamp `2026-10-19T11:28:51Z` instead of `b11732`. Half credit: the PR number and the policy
  change (LRU -> 50/50 SLRU) were right.
- **Q7 - inverted a two-sided comparison.** It gave "Vulkan, 28.4-28.5 prompt / 8.9-9.5 decode". The
  document says the opposite: `CUDA=1 VK=1` (Vulkan) gave 115.6-117.6 / 48.5, and CUDA-alone gave
  28.4-28.5 / 8.9-9.5. Swapping which side was slow is the same error shape as the lab's own historical
  misses (a wrong workaround published for a day, a headline taken from unpinned numbers).

Cloud was exact on all nine, quoted the supporting text for the trap, and added correct detail the
questions did not ask for (RSS 300 -> 270-280 GB, the second reporter's exact wording).

## What it establishes, and what it does not

- **Establishes:** on this document and these questions, a top-group local model extracts nearly everything
  and survives a buried correction, but **misattributes a specific identifier and inverts a two-sided
  numeric comparison**. Those are precisely the errors that survive into a report and cost a day, because
  they are plausible and locally correct in form.
- **Does not establish a rate.** Nine questions, one document, one sample each (temperature 0) - the
  confidence interval on "local gets ~1-2 of 9 wrong" is wide (+-10 points). Treat it as a smoke that found
  the *shape* of the failure, not a score.
- **Cost asymmetry:** 8.7x wall time per document for the local arm (86.3 s against 9.9 s), on a 17k-token
  prompt with experts in host RAM.

## Cloud tier comparison (same instrument, run 2026-10-19)

Same nine questions, same prompt file, `omp -p --no-skills`, one sample each:

| model | wall | score |
|---|---|---|
| `deepseek-flash` | 9 s | 9/9 |
| `deepseek-v4-flash-vision-exp` (the session default) | 9.9 s | 9/9 |
| `deepseek-v4-flash` | 11 s | 9/9 |
| `deepseek-v4-pro` | 33 s | 9/9 |

Every tier answered correctly, **including the build id `b11732` and the two-sided backend comparison** that
the local arm got wrong. The pro tier cost 3.3x the wall time for no measurable gain on extraction, so the
flash tier is saturated for this class of work. Not a rate - nine questions, one document, one sample - and
pro would presumably earn its price on genuinely hard analysis rather than on reading.

This also exposed a configuration fact worth keeping: `smol`, `slow` and `plan` were all pointed at
`deepseek-flash` while only `default` used a different model, so the "thorough analysis" role was the same
tier as the cheap one. The routing that would let mechanical turns stay cheap and hard ones go to a stronger
model exists in OMP (`modelRoles`, `--prewalk`) and was unused.

## Consequence for how we work

Route **extraction and transformation** local, and **anything that pairs two numbers, or names a specific
build/commit/version, through the cloud** - or through a local arm with a verification step that re-reads
the source for exactly those two facts. The 22 % per-item discordance measured across engines is the same
warning: a plausible answer is not the same as a correct one, and per-task scores do not show it.
