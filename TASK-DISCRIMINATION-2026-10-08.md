# Which of our tasks still discriminate - a check-level census across every run on disk

2026-10-08, overnight. The suite's problem this week was that `events` (76/76) and `paths` (75/75)
returned constants for every good model while the ledger was carrying all the ranking. This note
replaces that impression with a count.

## Method

Saturation is "the loss of reliable discriminative power among top-performing models"
(arXiv 2602.16763); item-level analysis is the standard way to find what still carries information
(arXiv 2505.15055 applies IRT to benchmark items). The same analysis works at **check** level on data
we already have, because every scored artifact records pass/fail per check:

- Collect every scored artifact on disk (all root families: candidates, truncation, newtasks,
  newtasks-ctx, strata, strata-ctx, strata-ab) plus the 226-check battery applied offline to all saved
  ledger artifacts (`rescore.py`).
- For each check: pass rate, and a **point-biserial correlation against the artifact's total computed
  leave-one-out** (a check must not correlate with a total that contains it - the first version of this
  census had exactly that flaw and reported r = 0.98 for nearly every check).
- **Top-group scope**: the checks that still split among artifacts scoring >= 90 % of that task's best
  score. A check that separates only catastrophic failures is not discrimination among competent
  models, which is the question.

`census_checks.py`, read-only.

## Result: how many checks still split in the top group

| task | artifacts | checks | **splitting in the top group** | what splits |
|---|---|---|---|---|
| `events` | 44 | 76 | **5** | cases 9-12, 15 |
| `paths` | 38 | 75 | **2** | cases 23, 24 |
| `ledger` (frozen) | 64 | 70 | **13** | 0, 5, 6, 7, 9, 11, 12, 14-19 - the CSV/edge family |
| `ledger2` (226) | 119 | 226 | **40** | the frozen family plus **70-76 = the Unicode-digit group** |
| `repo` | 9 | 78 | **3** | **only cases 63-65** - the UTF-8 byte-length class |
| `longctx` | 5 | 40 | **0** | nothing |

Three things this settles:

1. **`events` and `paths` are effectively dead as ranking instruments**: 5 and 2 live checks, and the
   live ones ("cases 9-12, 15" / "23, 24") are ordinary validation rows, not hard ones. Every summary
   that quoted 76/76 and 75/75 as capability was quoting a constant.
2. **`ledger2` multiplies the live checks by ~3x over the frozen ledger** (40 vs 13) and the extra live
   checks are precisely the Unicode-digit traps I built it around - the design hypothesis confirmed by
   an independent method (this census vs the earlier per-artifact profile).
3. **`repo` discriminates, but on exactly one bug class**: across five top-group artifacts only the
   three UTF-8-length checks split (3/5 each). A model that fixes the byte-length accounting is done
   discriminating; the rest of the 78 checks are all-pass for competent artifacts. Same for `longctx`:
   **zero** checks split among the four top artifacts, so as built it measures nothing among models that
   can already grep - my n=1 caveat from the six-task run, now quantified at n=5.

## What to do with this

- **Retire `events` and `paths` from ranking** (or replace them with harder variants): they consume
  roughly a third of every sweep's wall time and return a constant. Their remaining value is a
  regression guard for catastrophic failures, which the collapsed artifacts already flag.
- **Keep and extend the ledger family.** It is the only task whose live checks are dense (40), and the
  live ones are known adversarial edge cases. A third battery built the same way - more trap families,
  not more random valid rows - is the cheapest way to add discrimination.
- **Widen `repo` by adding independent defect classes.** Its current live set is one class; two more
  unrelated bugs (e.g. a cross-module import cycle, a stale-cache bug) would multiply it without new
  infrastructure.
- **Rebuild `longctx` or drop it.** Zero live checks among the top group means it cannot rank anyone; a
  harder variant needs several planted defects whose interaction matters, not one wrong function in a
  large file.
- **Quote the live-check count next to every task score** in future summaries. A 76/76 with 5 live
  checks and a 212/226 with 40 are not comparable quantities, and this week's confusion came from
  treating them as if they were.
