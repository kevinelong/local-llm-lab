# agent-skills adoption, 2026-10-06

Tooling change, no inference. Source: https://github.com/addyosmani/agent-skills (MIT).

## What was decided

Yes, there is something to take, but not the part that looks most transferable. The repo's
25 skills are product-engineering workflows (TDD, trunk-based git, Lighthouse/axe gates,
OWASP, rollback). Those are useful for the software-dev and UX work this workstation also
does. They are not useful for the model-evaluation track, which the repo does not address at
all. So this adopts the pack for development work and adds one lab-authored skill for the
evaluation work.

## What was installed

- Vendored clone, pinned: `C:/Users/kevin/.omp/vendor/agent-skills`, commit
  `1401c8b8030e023baeebb31781a6653fe8e93026` (2026-10-03), 25 skills. Update with
  `git -C C:/Users/kevin/.omp/vendor/agent-skills pull`; the pin is what makes a re-read
  reproducible.
- Lab-authored skill: `C:/Users/kevin/.omp/skills/lab-evidence-discipline/SKILL.md`
  (8871 bytes). Covers the repeated-run rule, version pinning, live-change proof, harness
  failure vs model failure, gate-loosening moves, circularity ranking, and procedure-not-
  workaround. Every entry is grounded in a recorded lab incident.
- Config: `skills.customDirectories = [".../vendor/agent-skills/skills", "C:/Users/kevin/.omp/skills"]`.
  Set with `omp config set`; `omp config get skills.customDirectories` confirms it.

## Verification

- `omp read skill://using-agent-skills` resolves to the vendored `SKILL.md`.
- `omp read skill://constraint-driven-development/references/floor-guard.md` resolves a
  nested asset (the shared `references/` tree stays reachable because the whole repo is
  vendored, not per-skill copies).
- `omp read skill://lab-evidence-discipline` resolves the lab skill.
- `omp read skill://no-such-xyz` lists 31 discovered skills: the 25 pack skills, 5
  pre-existing `codex-*` skills, and `lab-evidence-discipline`.
- NOT verified: that the skill list is rendered into the system prompt. `skillful` is true
  and `omp://system-prompt-customization.md` says discovered skills are rendered, but two
  model self-report probes disagreed with each other (NONE, then 26) and with the contents
  (`ci-cd-and-automation`'s description does contain 'quality gates'; the model paraphrased
  it). Treat the docs as the authority and `skillful` / `/skillful` / `--no-skills` as the
  control.

## Comparability: the measured screens are unaffected

This was the main risk and it is closed. `mimo-harness-20260925-v1/run.py` already invokes
the measured harness as:

```
<pinned omp.exe> --no-extensions --no-skills --no-session --provider lab --model <model> ...
```

so every frozen screen (events / ledger / paths, and the Strata runner that imports it) runs
with skills and extensions disabled regardless of what is installed. Nothing in the
2026-09-29..10-06 evidence is invalidated.

Also worth recording: the lab does NOT use the PATH `omp`. `HARNESS['omp1831']` points at
`mimo-harness-20260925-v1/omp/omp.exe`, downloaded from the v18.3.1 release and invoked by
absolute path. The PATH binary has since moved to 18.6.1. So "OMP 18.3.1" in the reports is
correct, and the two binaries must not be confused when quoting a version.

## Methodology worth taking next (not done here)

From `evals/README.md`, the one item with a measured cost model behind it: report a **rate
over n runs against an explicit floor**, never a single run as a point estimate. They
measured skill-trigger rates of 5/7 and 2/7, enforce a routing floor (`--min-rank1 95`) with
headroom, and run the token-costly behavioral tier on demand and never in CI. This is the
standard remedy for the lab's own recorded finding (MiniCPM5-2B paths 75/75, 75/75, 9/75
under identical declared config). It would change the screen protocol, not just the
documentation, so it needs a deliberate decision and a new root.

## Controls

- `omp config set skillful false`, or `/skillful` per session: stop listing skills in the
  system prompt.
- `omp config set skills.enabled false`: turn discovery off entirely.
- `--no-skills` on any launch: per-run suppression, which the lab runners already pass.
- Delete `C:/Users/kevin/.omp/skills/lab-evidence-discipline/` to remove the lab skill;
  emptying `skills.customDirectories` removes both roots.

## Standing reminder

Registered 2026-10-06 in the always-loaded user context
(`C:/Users/kevin/.omp/agent/AGENTS.md`, section "Product, development and UX work"):
before starting product, development or UX work, read this document and use the
vendored pack via `skill://<name>` rather than improvising a process. Start with
`skill://using-agent-skills`.

## Boundaries

Nothing ran: no inference, no model loaded, no gate or metric changed, no app closed, no
reboot. The Strata engine started earlier today (pid 33896, detached service `strata`) is
still up and serving, unrelated to this change.
