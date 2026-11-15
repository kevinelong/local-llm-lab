# Reading log for RESEARCH-AGENDA-2026-11-15.md

Written with the agenda, 2026-11-15. Read-only over everything else in this repo: this file and the
agenda are the only two changes.

## What was read, and how

- All 36 `NEWS-*.md`, 2026-10-05 .. 2026-11-15. The 36 shortlist sections and the 21 headed
  "Gated on Kevin" sections were extracted mechanically and read in full, in date order, rather than
  sampled: the point was to see a question carried, refined and re-priced, not to find the best one.
- The four early notes do not use the shortlist heading. Their proposal sections were read by hand:
  `NEWS-2026-10-05.md:150`, `NEWS-2026-10-08.md:49`, `NEWS-2026-10-14.md:106`, `NEWS-2026-10-16.md:364`.
- `AGENTS.md` (7,000 lines) was read as a **state register only** - the dated entries were searched for
  closing statements ("closed unmerged", "retracted by its own reporter", "settles", "closes the"), not
  read as prose. Anything in the agenda attributed to `AGENTS.md` already appears in a `NEWS-` note with
  a date, so the citations point there.
- Read whole, because they hold results the shortlists only refer to: `DECLARATION-TEMPLATE.md` (all
  twelve sections, including the 2026-11-15 additions at sec. 8, 9, 10 and 12),
  `SHORTLIST-2026-10-26-untried.md`, `CHUNK-LADDER-AND-RESERVE-2026-10-26.md` (including both revisions
  and the 2026-11-15 addendum), `RESIDENT-ABOVE-8-2026-11-01.md` (including "Open questions this run
  creates"), `WDDM-SHARED-SEGMENT-2026-10-22.md`, `KNOWLEDGE-DEEP-2026-10-10.md` (including the
  2026-11-15 calibration addendum).
- Read for the `Closed` list only: `Q7-STRATA-BUMP-AB-2026-10-22.md`, `TENSOR-TYPES-2026-10-22.md`,
  `TTFT-MLOCK-AB-2026-10-22.md`.

## How the counts were made, so they can be checked

266 proposals: 224 numbered items in the 32 headed shortlists (7 each, without exception), 21 in the
four early notes' proposal sections, 21 in `SHORTLIST-2026-10-26-untried.md`. The theme split in the
agenda's count table is a keyword classification of each item by its own subject line, one theme per
item - reproducible from the notes, but a judgement at the margins: an item like "add the host-buffer
type to the declaration" is counted under Windows memory contracts rather than under harness, and a
pack-download item is counted under quantisation rather than under the engine queue. The **row** counts
in the same table are mine after reading, not mechanical.

The `Closed` list is the part I would most want checked against the notes, because a wrong entry there
retires a question that is still live. Every entry names the note and the date that closed it.

## Deliberately left out

- **The image track.** `IIMAGE-REVIEW-2026-11-03.md`, `IIMAGE-LESSONS-FOR-TK-2026-11-03.md`,
  `MAGNITUDE-2026-10-17.md`, the ComfyUI arms in the shortlists (roughly 25 of the 266 items). It is a
  second lab, with its own queue, its own card-time gate and its own instruments. Two of its live items
  appear in the agenda because they bear on a Windows memory contract the language side shares - the
  `--disable-pinned-memory` pair and the ComfyUI cast-buffer pin - and those are cited to their notes.
- **September.** `RESULTS-2026-09-*`, `OVERNIGHT-*`, `PACKING-*`, `JEV-*`, `RESEARCH-2026-09-29.md`,
  and `goproverbs/` entirely (a separate project with its own results tree). The scans in scope start
  2026-10-05 and the agenda holds to that.
- **The harness-lab docs** (`C:/Users/kevin/harness-lab/docs`: `DASHBOARD.md`, `GITHUB-PROJECTS.md`,
  `PARALLEL-WORKERS.md`, `UX-EXPECTATIONS.md`, 224 lines total). Read, no overlap: they concern a coding
  worker harness - worktrees, task claims, a one-way ledger-to-board mirror, UI conventions - and the
  only transferable rule, "the ledger is the source of truth, a board is a view", this lab already keeps.
- **Model landscape.** No attempt to rank or re-evaluate candidate models. The staging queue appears once
  (row 5.4) only because it is the largest block of proposals that produced no measurement.

## What I could not establish, and did not assert

- **The WDDM cap itself.** `WDDM-SHARED-SEGMENT-2026-10-22.md` says plainly that it measured usage
  against an assumed cap, not the cap. Row 4.1 states that as the finding rather than picking one of the
  three later numbers.
- **Whether the engine is still 0.1.47 and llama.cpp still b11480.** Taken from `NEWS-2026-11-15.md`'s
  gated list and from the build names the rows quote. I did not touch `C:/Users/kevin/ai_bench` to check
  a binary, which is the rule.
- **Any upstream number not already in our notes.** Every figure in the agenda is quoted from the note
  that holds it, with that note's date. Nothing was re-fetched or re-verified this week.

## Repository state worth knowing

`git status` shows an untracked `logs/` directory that predates this work (2026-11-13: `fix_policy.py`,
`wait-pull.sh`, and pull logs that `.gitignore` already covers via `*.log`). It is **not** mine, it is
someone's scratch, and it is deliberately not committed or removed - the two paths committed alongside
this note are the agenda and this file. `git status` therefore reads `?? logs/` until whoever owns it
decides; nothing else is dirty.
