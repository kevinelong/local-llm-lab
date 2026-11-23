# Applying the local-LLM benchmarking work inside tile-lab

Written 2026-11-23. Read-only survey: tile-lab was cloned to a temp directory
(`tile-lab-plan-read`) and nothing was pushed, committed, or opened as a PR. No model was
downloaded, no engine was started, no inference was run, and neither repository was modified
except for adding this file. The working tree of `local-llm-lab` already had an uncommitted
change to `benchmarks/hard-probe-2026-11-22.py` (a new `vt` suite) while this was written; see
the note in section 6.

---

## 1. What tile-lab is

`https://github.com/kevinelong/tile-lab` is a one-commit repository (6cb74d8, 2026-11-22) for
"reproducible experiments in tile-based GPU programming on an RTX 4060 laptop". Python plus
PyTorch/TileLang kernels, CUDA-event timing, CSV results, static plots. Its own README states
its status: "documentation and environment probe only. No kernels or performance results have
been validated."

What is actually in it (13 files, 23 KB total):

| Path | Role |
|---|---|
| README.md | purpose, research questions, explicit non-goals, check commands |
| STATUS.md | current task (T01), what is done, what is blocked, latest verification |
| AGENTS.md | agent rules: one task per branch, stdlib-only probe, never fabricate timings, update STATUS.md, handoff format |
| docs/SETUP.md | inspect-first environment procedure, venv, verify in order |
| docs/ARCHITECTURE.md | research map, tool roles, "GEMM results do not establish faster end-to-end LLM inference" |
| docs/BENCHMARKING.md | the full measurement protocol: correctness gate, CUDA events, warmup/samples, manifest.json + measurements.csv + summary.csv contract, status vocabulary |
| docs/EXPERIMENTS.md | E01-E05 hypotheses and deliverables |
| docs/DECISIONS.md | ADR-001 Python, ADR-002 verified platform, ADR-003 evidence before claims, ADR-004 private initially |
| docs/ROADMAP.md | T01-T09 ordered tasks with acceptance evidence |
| docs/REFERENCES.md | primary sources, checked date |
| scripts/probe.py | 1.3 KB stdlib environment report (schema_version 1), no GPU imports |
| tests/test_probe.py | 2 unittest tests, run with `python -m unittest discover -s tests -v` |
| .gitignore | ignores `results/`, `vendor/`, `.venv/`, caches |

Conventions it sets, which a port must respect:

- **Python, standard library first.** The only script imports stdlib and must not install
  anything. No frameworks, no plugin layers.
- **Tests are unittest, discovered from `tests/`.** No pytest, no CI configuration exists at
  all (there is no `.github/`), so tests run by hand.
- **One numbered task per branch, STATUS.md updated on every handoff.** AGENTS.md also fixes a
  handoff format (task, changes, exact commands and outcomes, blockers, next).
- **Evidence discipline is already written down** in docs/BENCHMARKING.md: correctness before
  timing, failures preserved, tolerances not silently loosened, every claim tied to raw data
  and an environment, run-scoped `results/<run_id>/` with a manifest.
- **ASCII in scripts** (the source lab's METHODOLOGY.md records a PowerShell 5.1 encoding
  failure from an em dash), no credentials, no weights, no caches committed.

What it does **not** have, and this work would need:

1. **No LICENSE or NOTICE file.** Nothing states the terms of the repository. That is a
   blocker for any publishing decision, not just for the port.
2. **No model-run result schema.** docs/BENCHMARKING.md defines a schema for kernel timings
   (manifest + measurements.csv + summary.csv) and nothing for model replies, vectors, or
   budgets.
3. **No model or runtime pin record.** There is a hardware section in STATUS.md but no place
   for "model digest X served by runtime Y at window Z".
4. **No test fixtures.** tests/ has two mocked tests; there is no corpus of known input/output
   pairs, which is exactly what a scorer needs.
5. **No CI.** Fine for a private doc repo, a drift risk once harnesses live here.
6. **No data attribution convention.** The source lab has NOTICE.md explaining which dataset
   terms survive its licence; tile-lab has nowhere to put that.
7. **No summariser/plot for model runs**, and `results/` is git-ignored wholesale, so a naive
   port would store the evidence in a directory the repo refuses to track.
8. **Stale STATUS.md.** It says remote creation and push are blocked by `gh` auth, but the
   remote exists and clones cleanly. The state file is already telling a false story.

And one scope statement that has to be faced rather than edited away: README.md lists "No
model downloads, paid compute, distributed runtime, full LLM training, dashboard, or custom
compiler" as boundaries, and every research question is about tile sizes, fusion, and tuning.
An LLM-serving measurement track does not need downloads or training - it needs an endpoint
that already has a model - but it is still a second research domain inside a repository whose
name, README, and roadmap describe one domain. Section 9 asks Kevin to settle that; the plan
below assumes it is settled in favour of a clearly fenced second track.

---

## 2. What the source work contains

Everything below is committed in `local-llm-lab` (branch main) except where noted.

| Artefact | Size / shape | What makes it reusable |
|---|---|---|
| `benchmarks/quality-pass-2026-11-22.py` | 313 lines | ten fixed tasks + one scorer each; every input is a CLI flag already (`--base-url`, `--model`, `--label`, `--out`, `--runs`, `--max-tokens`, `--seed`); stores raw reply text per row |
| `benchmarks/hard-probe-2026-11-22.py` | 365 lines + uncommitted `vt` suite | RULER-style long-context probes generated deterministically; BBH/GSM8K scored against the dataset's own answer; `--suite longctx|reasoning` |
| `benchmarks/speed-probe-2026-11-22.py` | 85 lines | one prompt, warmup, n runs, server token counts; already endpoint-generic |
| `benchmarks/ctx-probe-2026-11-22.py` | 130 lines | context ladder with placement from `/api/ps`; Ollama-specific |
| `benchmarks/rescore-2026-11-22.py`, `rescore-hard-2026-11-22.py` | 60 + 60 lines | re-score stored replies after a scorer fix, no inference |
| `benchmarks/sweep-inkling-ctx-2026-11-22.sh` | 45 lines | restarts llama-server per window; absolute `D:/` paths |
| `data/bbh-date_understanding.json`, `bbh-logical_deduction_seven_objects.json`, `gsm8k-test.jsonl` | 62 KB, 198 KB, 750 KB | frozen inputs; BBH carries its canary GUID |
| `results/*2026-11-22.json` | 28 files, 212 KB, 450 rows | the evidence: raw reply text, per-task outcome vectors, budgets |
| `RESULTS-2026-11-22.md`, `RESULTS-2026-11-22-HARD.md` | 16 KB + 11 KB | findings, three scorer defects, the aggregation ladder, what the batteries do not measure |
| `MODELS.md` | 4.8 KB | store table for one 12 GB / 32 GB workstation |

Two properties of the harnesses matter for a port:

- **They are already mostly host-neutral.** Ports, model ids, budgets, and result paths are CLI
  arguments. The host leaks in only in three places: the default `http://127.0.0.1:8080` in
  quality-pass, the literal `http://127.0.0.1:11434` in ctx-probe, and the `":11434" in base`
  sniff in hard-probe that decides which API shape to use. The shell sweep is the only file
  that is unambiguously machine-specific.
- **Results are evidence-shaped.** Each row keeps the full reply (quality) or its first 2,000
  characters (hard), the finish reason, the expected answer, and the verdict, and the rescorers
  exist precisely so a scorer fix never requires re-running a model. That is the same
  principle as tile-lab's "preserve raw samples with published findings".

---

## 3. Port / adapt / leave

| # | Source | Decision | Target | Reason |
|---|---|---|---|---|
| 1 | `quality-pass-2026-11-22.py` | **Adapt** | `scripts/llm_quality.py` | Already flag-driven; keep tasks and scorers in one file so a reader can re-score by hand. Changes: `--base-url` required instead of defaulting to the workstation's llama-server; add a manifest block and `schema_version`; add a row `status` (pass / wrong / unanswered / transport / error) instead of boolean-only `ok`; store a prompt hash and task id per row; run generated code in a subprocess with a timeout (section 7). |
| 2 | `hard-probe-2026-11-22.py` | **Adapt, from the committed blob** | `scripts/llm_hard.py` | Data directory is computed as `../data` from the script; backend is inferred from a port number. Changes: `--data-dir` (default `data/llm`), explicit `--backend openai|ollama` replacing the `":11434"` sniff, a stable item id per row (the rescorer currently rebuilds the plan and assumes `len(rows)//3` items per task), and **full** reply text rather than `content[:2000]` (the current cap can change a GSM8K verdict, since scoring takes the last number in the stored slice). Port the `vt` suite only after it is committed in the source repo. |
| 3 | `speed-probe-2026-11-22.py` | **Port as-is** | `scripts/llm_speed.py` | One request, warmup, n runs, tokens from the server's own usage. Nothing host-specific; it already reports each run, not just the median. Keep the docstring's warning that wall time includes prefill. Only edit: ASCII-only docstring and the example command. |
| 4 | `ctx-probe-2026-11-22.py` | **Adapt, scope to Ollama** | `scripts/llm_ctx_sweep.py` | `/api/chat` and `/api/ps` are Ollama's; placement (`size_vram/size`) exists nowhere else. Make `--base-url` required, state "Ollama only" in the module docstring, and refuse (not silently degrade) on a non-Ollama endpoint. This probe answers a question about fit, which is a property of the box, not of the model. |
| 5 | `rescore-*.py` (two files) | **Adapt, merge** | `scripts/llm_rescore.py` | Both load the harness by filename with importlib, both rewrite rows in place, both stamp a free-text `scorer` label. Merge into one rescorer with `--suite quality|hard`, a real `scorer_version` constant, and no reliance on row order: re-score by stored task/item id. |
| 6 | `data/bbh-*.json`, `gsm8k-test.jsonl` | **Port as data** | `data/llm/` | Frozen inputs, small, and they carry their own terms (BBH canary; GSM8K is third-party text). Keep byte-identical, keep the canary, and add attribution in a NOTICE-style file. Do not fetch from upstream at run time. |
| 7 | `results/*2026-11-22.json` (28 files, 450 rows) | **Port as evidence** | `results/llm/2026-11-22/` | The stored replies are the claim, and the only way to check a rescore without inference. 212 KB is trivial. Requires a deliberate exception to the current `results/` ignore rule (section 5). |
| 8 | `RESULTS-2026-11-22.md`, `RESULTS-2026-11-22-HARD.md` | **Leave; port a one-page condensed baseline** | source repo stays canonical | Twelve of the most useful paragraphs are about the store's qwen/Inkling situation on a 12 GB card and the day's engine news; copying them creates two documents that will diverge. Instead write `docs/LLM-BASELINE-2026-11-22.md`: the pinned table, the score matrix, the three scorer defects, and an explicit "what this does not measure", with a link plus commit hash. |
| 9 | `MODELS.md` | **Leave** | source repo | It is tuning advice for one workstation ("12 GB / 32 GB", `D:/build/llamacpp-b12611`, "the store's" shortlist). The portable part is the pin row (name, digest, params, runtime, window), and that belongs in each run's manifest, not in a hand-maintained table that goes stale. |
| 10 | `sweep-inkling-ctx-2026-11-22.sh` | **Leave** | source repo | Absolute `D:/build/...`, `D:\models\...`, CUDA toolkit paths, `cygpath`, and it kills every `llama-server` process. That is the opposite of tile-lab's "do not silently start or change the environment". |
| 11 | `patches/`, `NEWS-*.md`, `INKLING-2-MINI-*.md`, `PLAN-CUDA-13-*.md`, results before 2026-11-22 | **Leave** | source repo | Engine patches, daily news, and older instruments from a September/October methodology. Nothing here continues the benchmarking track, and the older result files are not comparable with the new schema. |
| 12 | `benchmarks/__pycache__`, `logs/`, `.aider*`, the `goproverbs` symlink | **Do not copy, ever** | - | Caches, local logs, and a machine-local symlink (`D:\projects\goproverbs`). AGENTS.md already forbids committing caches and unrelated personal files. |

### What belongs as data, what stays code

- **Data:** frozen third-party datasets (BBH, GSM8K); any run-time generated prompt that must
  be byte-identical later; per-run model/runtime pins; event logs from a server. The
  long-context filler and variable-tracking chains are generated deterministically from seeds,
  so they can stay code **provided** each row stores a hash of the exact prompt - that is
  cheaper than a 100 KB prompt per row and still makes drift detectable.
- **Code:** the scorer is inseparable from the task text in the ten-task battery, because the
  task exists to test one checkable property; splitting prompt out of scorer invites them to
  drift apart. Keep prompt + scorer adjacent, version the task id, and hash the prompt into
  the result.
- **Neither:** a hand-maintained "current best model" table. That is a finding, and findings
  belong in a dated note that cites run ids.

---

## 4. How results should be stored

Follow tile-lab's own contract rather than inventing a second one:

```
results/llm/<run_id>/
  manifest.json     # schema_version, run_id, UTC, git commit + dirty, host, python,
                    # backend + base_url, model id + digest + file + sha256, runtime version,
                    # ctx window, max_tokens, temperature, seed, scorer_version, datasets + hashes
  rows.json         # one object per row: task_id, item_id, prompt_sha256, status, ok, why,
                    # want, content (verbatim), finish_reason, seconds, usage
  summary.csv       # configuration, passed, possible, rate, per-task vector, status counts
  notes.md          # optional short note; the full finding lives in docs/
```

Rules that should be explicit in the port:

1. `status` is **pass | wrong | unanswered | transport | error**, mirroring the kernel
   contract's pass/incorrect/unsupported/error/oom. `unanswered` (empty content with
   `finish=length`) is not `wrong`; the 2026-11-22 notes turn on that distinction, and the
   current JSON cannot express it except by inspecting `content`.
2. Raw reply text is stored verbatim and scored by a named `scorer_version`. Re-scoring writes
   a new file or appends a rescore record; it never silently overwrites the original rows
   (the source rescorers rewrite in place, which loses the pre-fix verdict).
3. A budget is a declared property of a run, not a constant of the suite. Every summary row
   carries `max_tokens`, and a run is flagged if any row ended `finish=length`, because that
   is the harness failure the source notes found twice.
4. `summary.csv` uses the same column style as tile-lab's kernel summaries so one plotting or
   reporting script can read both, with model runs distinguished by a `kind=model` column.

---

## 5. .gitignore and the evidence question

tile-lab ignores `results/` entirely, matching its stated policy ("generated results are
ignored by default; deliberately commit compact verified summaries when reviewed"). Two
workable options, in preference order:

1. **Commit the 450-row evidence deliberately**: add an exception (`!results/llm/`) and a line
   in docs/LLM-SERVING.md saying model-run evidence is committed, kernel timings are not.
   Justification: the raw replies are the only artifact that lets a scorer change be audited
   without inference, which is the method's whole point.
2. Commit only `summary.csv` and the manifest, and keep replies out of the repo. Cheaper, but
   it breaks auditability and contradicts "the log as the claim".

Recommend option 1 and treat this as a question for Kevin only insofar as repository size or
model-output licensing is a concern (section 9).

---

## 6. Ordered steps, by value, with risks

**S1. Make the repository's state true, and add a licence.**
Rewrite STATUS.md (the remote exists; the "blocked" note is obsolete; T01 is still the real
task), and add LICENSE and a short NOTICE for third-party data. Value: every later commit is
read against these files, and the port adds third-party text.
Risk: choosing terms without Kevin; a licence cannot be un-chosen for already-published
versions (the source repo's own NOTICE.md documents exactly that trap).

**S2. Write the track spec before the code: `docs/LLM-SERVING.md`.**
Purpose, what is measured, the run directory contract, the status vocabulary, the budget rule,
the "bring your own endpoint" rule (the harness never starts, installs, or stops an engine),
and the non-goals. Add T10-T13 to docs/ROADMAP.md and one line to README.md's boundaries
("no model downloads; serving an already-installed model for measurement is in scope") - or,
if Kevin decides against the track, stop here and do none of S3-S8.
Risk: scope inflation inside a repo whose research questions are all about tiles. Mitigation:
the track exists to supply the end-to-end number that ARCHITECTURE.md already says GEMM results
cannot establish, and every task is fenced behind its own doc.

**S3. Port the scorer core and give it tests.**
`scripts/llm_quality.py` plus `tests/test_llm_scorers.py`, using the stored 2026-11-22 rows as
fixtures: the qwen3 $0.05 answer that also explains $0.10, the "no crewed landing ... has
occurred" decline, the `ANSWER: 12/25/1937` BBH answer, the bare `D` logical-deduction answer.
Assert only content -> verdict, never the stored `ok` (some rows were scored by earlier
scorers). This is the highest-value step: all three historical defects were scorer defects,
and none of them has a regression test today.
Risk: fixtures encode a bug as expected behaviour. Mitigation: every fixture cites the dated
note that explains why the verdict is right.

**S4. Port the hard suites and the frozen data.**
`scripts/llm_hard.py` + `data/llm/` + attribution. Explicit backend flag, stable item ids,
full reply text, data hashes in the manifest.
Risk: the current rows truncated replies to 2,000 characters, so a re-score of the ported 2026
data can differ from the published one. Record that difference rather than hiding it, and keep
the source JSON untouched. Dataset drift is avoided by freezing the files and hashing them.

**S5. Unify transport in one small module.**
`scripts/llm_client.py` (stdlib urllib only, well under 100 lines): OpenAI-compatible chat,
optional Ollama `/api/chat` for `num_ctx`, and one `usage` normalisation. All harnesses import
it.
Risk: abstraction creep. Keep it to functions, no classes or backends registry; tile-lab's
ARCHITECTURE.md explicitly warns against introducing a backend framework.

**S6. Manifest, summary, and the rescorer.**
`manifest.json` + `summary.csv` writing shared by all suites; `scripts/llm_rescore.py`.
Value: comparisons become mechanical, and a scorer change never needs inference.
Risk: two result schemas in one repo (kernel CSV vs model JSON). Document the mapping in
docs/LLM-SERVING.md instead of stretching BENCHMARKING.md to cover both.

**S7. Commit the 2026-11-22 evidence and the condensed baseline note.**
`results/llm/2026-11-22/` (28 files), `docs/LLM-BASELINE-2026-11-22.md`, gitignore exception.
Value: the next run has something to be comparable to.
Risk: model output licences and a growing history; 212 KB now, but this grows every run, so
state a rotation policy (keep evidence; summaries forever).

**S8. Prove the port without inference: re-score the stored rows.**
Run the ported rescorer over the copied 2026-11-22 JSON and require the published vectors
(30/30, 30/30, 27/30, 27/30, 24/30; 42/45 and the 28/30, 27/30 rows) to come back unchanged.
This is the port's acceptance gate and costs no model time.
Risk: mismatch reveals an adaptation bug, which is the point. Do not adjust the expected
vector to match the code.

Only after S8 should a new inference run happen, and that is outside this plan's authority.

---

## 7. What should NOT be moved, and why

- **`sweep-inkling-ctx-2026-11-22.sh`** - `D:/build/llamacpp-b12611`, `D:\models\...`,
  `/d/tools/cuda-13.5`, `cygpath`, and a `Stop-Process llama-server` that would kill whatever
  else is running. It only makes sense on this workstation, and it violates tile-lab's rule
  against silently starting or changing the environment.
- **`MODELS.md`** - a recommendation table for one 12 GB card and one 32 GB of RAM, tied to a
  named store and a locally built binary. The reusable content (the pin row) becomes per-run
  manifest data; the advice stays where the workstation is.
- **`RESULTS-*.md` as documents** - the findings are about this box and the day's engine
  state; the portable claims are the score matrix and the three scorer defects, which become a
  short baseline note with a commit-hash link.
- **The aggregation ladder result files** - single-model, single-item, n=1 observations whose
  meaning depends on that llama-server build. They are evidence for the aggregation probe's
  calibration, not a general result; if the probe is continued, recalibrate rather than inherit.
- **Engine patches, NEWS files, CUDA plans, Inkling notes** - unrelated to benchmarking and
  actively moving in the source repo.
- **Anything under `logs/`, `__pycache__`, `.aider*`, or the `goproverbs` symlink** - local
  state, caches, and a symlink to `D:\projects\goproverbs`.
- **Pre-2026-11-22 results** - different instruments and a different schema; mixing them would
  manufacture comparability that does not exist.

Also do not move **the source harnesses' default endpoints** (`127.0.0.1:8080`,
`127.0.0.1:11434`) as defaults. A benchmark that silently talks to whatever is on the port is
how a stale server produced the 5.4 tok/s contaminated reading the source notes describe.

---

## 8. Risks that are not step-specific

| Risk | Why it bites | Mitigation |
|---|---|---|
| **Scope collision** | tile-lab's README, roadmap, and all nine tasks are about GPU tiles; a model benchmark track can read as mission drift and dilute both. | One fenced doc and four T-tasks; name the bridge (end-to-end numbers) in ARCHITECTURE.md; Kevin's explicit decision in section 9. |
| **Licence mismatch** | Source is FSL-1.1-MIT, source-available, not OSI open source; tile-lab has no licence at all. Third-party datasets keep their own terms. | Add LICENSE/NOTICE in S1; never describe the repo as open source; keep BBH canary and attribution. |
| **Evidence drift** | The rescorers currently rewrite rows in place and rely on code order to map a stored row to its task. A prompt edit silently re-labels old evidence. | Store task/item id and prompt hash; append rescore records instead of overwriting; fixture tests. |
| **Arbitrary code execution** | `score_code` runs model-written Python with `exec` in the harness process, with filesystem and network access. | Run it in a subprocess with a timeout and no network; treat the reply as untrusted input. Keep the execute-don't-eyeball principle. |
| **Budget fairness** | One `max_tokens` per run, but models think for wildly different lengths; the 2026-11-22 pass had to use 2048 for three models and 8192 for two. | Declare the budget per run, flag any `finish=length`, and refuse to publish a score from a run with truncation. |
| **n=1 rows read as results** | The long-context and per-item reasoning rows are single observations; the source notes say so, the JSON cannot. | Carry `n` and the outcome vector in the summary; a single row is a `sample`, not a `rate`. |
| **Windows path and encoding assumptions** | Absolute drive paths, `cygpath`, and em dashes have already broken one PowerShell script in the source lab. | Relative paths resolved from the repo root; ASCII only; tests that run from any cwd. |
| **No CI** | Scorer changes can land untested; the repo has no gate at all. | `python -m unittest discover -s tests -v` before every handoff, written into AGENTS.md's definition of done; add CI only if the repo goes public. |
| **Two schemas** | tile-lab already defines manifest + measurements.csv + summary.csv for kernels. | Do not retrofit model rows into measurements.csv; document the LLM schema separately and share only the summary shape. |

---

## 9. Open questions only Kevin can answer

1. **Does this track belong in tile-lab?** Its README is explicitly about tile-based GPU
   kernels and lists "no model downloads" among the boundaries. Serving an installed model for
   measurement does not need a download, but it is a second research domain. Alternatives: a
   fenced `docs/LLM-SERVING.md` track (this plan), or a sibling repository that tile-lab links
   to. The plan's value ordering changes completely if the answer is "sibling".
2. **What licence does tile-lab carry?** The source is FSL-1.1-MIT. Options: match it, MIT, or
   leave private and unlicensed. Nothing can be published until this is decided, and the
   source lab's NOTICE.md shows the choice is effectively irrevocable per published version.
3. **Is the raw reply evidence committed, or summaries only?** 212 KB today, growing per run;
   committing it is what makes a scorer fix auditable without inference.
4. **Is the ten-task battery canonical or retired?** It saturated (four of five models at 27/30
   or better) and its only separator is a formatting ceiling. Keeping it as a smoke gate and
   making BBH/GSM8K/longctx the ranking suites is one answer; keeping it as the headline is
   another. The port should not decide this by accident.
5. **Which backends are in scope?** OpenAI-compatible only (drops the ctx sweep), or Ollama
   extras too (keeps `num_ctx` and placement, which is what made the 14B spill measurable)?
6. **Is the in-progress `vt` suite in scope?** The working tree of the source repo has an
   uncommitted `variable_tracking`-with-reps suite. Port only committed artefacts, so either it
   lands there first or the port starts without it.
7. **Does the older evidence come along?** The 2026-09/10 results use different instruments.
   Recommendation is no; confirm, because "continue the work" could also mean "keep the
   history in one place".

---

## 10. What this plan did not do

No commits, pushes, issues, PRs, or releases in tile-lab. No model download, engine start,
inference, or benchmark. No edit to `local-llm-lab` other than creating this file, and nothing
read there was modified; the pre-existing uncommitted change to `benchmarks/hard-probe-2026-11-22.py`
was left exactly as found.
