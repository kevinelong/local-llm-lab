# Skill and tool collections, 2026-10-06

Tooling research and installs. No inference, no model loaded, no gate changed.

## Skill collections now registered

| Source | Pin | Skills | Why |
|---|---|---|---|
| addyosmani/agent-skills | `1401c8b8` (2026-10-03) | 25 | Process skills: spec, plan, build, test, review, ship |
| anthropics/skills | `683bc88e` (2026-10-05) | 19 | Complementary, no overlap: docx/pdf/pptx/xlsx, canvas-design, brand-guidelines, algorithmic-art, frontend-design, theme-factory, mcp-builder, skill-creator, webapp-testing, web-artifacts-builder, claude-api, doc-coauthoring, internal-comms, academy-guide, discernment-nudge, slack-gif-creator |
| lab-authored | local | 1 | `lab-evidence-discipline` |

Both vendored under `C:/Users/kevin/.omp/vendor/`; registered as the first two
entries of `skills.customDirectories` in `~/.omp/agent/config.yml`.

Licence note: most of anthropics/skills is Apache-2.0, but the document skills
(docx, pdf, pptx, xlsx) are source-available, not open source. Fine for local
use; do not redistribute them.

Verified: 50 skills discovered (`omp read skill://no-such-xyz`), 45 of them
rendered into the system prompt. The rendering question left open earlier is now
answered directly: the live `<skills>` block in this session's own system prompt
rebuilt mid-session and lists the Anthropic skills, so the list is injected and
rebuilt at runtime.

## Vendored but deliberately NOT registered

- **obra/superpowers** `8ca22dba` (v6.4.2, MIT), 15 skills. Duplicates the
  process methodology already adopted (test-driven-development, writing-plans,
  executing-plans, requesting/receiving-code-review, systematic-debugging,
  verification-before-completion, brainstorming, using-git-worktrees) and its
  core mechanism is subagent dispatch (`subagent-driven-development`,
  `dispatching-parallel-agents`), which contradicts this machine's standing rule
  of one agent at a time and no delegation. Take it whole or not at all;
  cherry-picking breaks its internal cross-references. To enable it, append
  `C:/Users/kevin/.omp/vendor/superpowers/skills` to `skills.customDirectories`
  and accept that its duplicate names get namespaced (`superpowers/<name>`).
- **MengTo/Skills** (6.6k stars, MIT), 176 skills in 9 categories: web-design 91,
  game-development 20, codex 20, 3d 16, illustration 14, game-combat 6,
  workflow 4, ui 3, media 2. Designer/game/3D prompt recipes aimed at Aura Build,
  Fable 5 and Lovable workflows. Not registered: 176 system-prompt entries is
  not acceptable, and OMP scans custom directories non-recursively, so a subset
  means adding a root per category. `ui/` (3) or `workflow/` (4) are the only
  plausible narrow picks.

## Assessed, not installed

- **vercel-labs/agent-skills** (31.7k stars): 9 skills, stack-specific
  (deploy-to-vercel, vercel-cli-with-tokens, react-best-practices,
  react-native-skills, react-view-transitions, vercel-optimize,
  composition-patterns, web-design-guidelines, writing-guidelines). Adopt only
  if we actually ship on Vercel/Next.
- **meridianlabs-ai/inspect-skills** (MIT): 4 skills for the Inspect AI
  ecosystem (map-inspect-packages, reading-logs, analyzing-logs,
  babysitting-evals) plus an optional Python-REPL MCP. Adopt only together with
  Inspect AI.
- **EleutherAI/lm-evaluation-harness**: standard academic benchmarks. Heavy
  torch stack, and every model here is GGUF behind llama.cpp, so it would run
  through its `local-completions` provider. Useful for a model-quality
  cross-check, not for harness comparison.
- **promptfoo**: LLM feature testing and red teaming, node-based, good CI story.
  Relevant to product LLM features; not installed.
- Directories rather than packs, useful for discovery: agenticskills.io (194
  skills indexed), awesomeclaudeskills.com,
  obviousworks/Claude-AI-skills-collection-2026.

## The eval-framework gap

Two things would give the coding-agent screen external, reproducible evidence,
which is the weakest part of the current record (one bespoke task set, one run
per task, no outside reference):

- **Inspect AI** (UK AI Security Institute and Meridian Labs). `inspect eval`,
  200+ pre-built evals, composable datasets/solvers/scorers, and explicit
  support for running "arbitrary external agents like Claude Code, Codex CLI,
  Gemini CLI" - i.e. it can drive the same harnesses this lab compares.
  Installed on WSL as a uv tool (0.3.277). No Docker needed for non-sandboxed
  evals; sandboxed agent tasks need Docker.
- **Terminal-Bench 4.0** (tbench.ai) and **SWE-bench / SWE-bench Verified**:
  the standard agentic-coding benchmarks. The Laude Institute Harbor harness is
  what OpenAI used for Codex CLI on Terminal-Bench. Both require Docker.

Blocker for both: Docker in WSL needs `/etc/wsl.conf` `[boot] systemd=true` and a
`wsl --shutdown`, and adds daemon overhead inside the 8 GB `.wslconfig` cap. That
is a platform change for the lab, so it is a decision, not an install.

## WSL tooling installed

Ubuntu 24.04.5. sudo is passwordless; apt and the network work.

| Tool | Version | Note |
|---|---|---|
| uv / uvx | 0.12.23 | Official release tarball, sha256 verified against the published `.sha256` (no pipe-to-shell) |
| inspect | 0.3.277 | `uv tool install inspect-ai`, isolated |
| fd-find | 9.0.0 | aliased to `fd` in `~/.local/bin` |
| bat | 0.24.0 | aliased to `bat` in `~/.local/bin` |
| fzf, zoxide, direnv, tree, tmux | 0.44.1 / 0.9.3 / 2.32.1 / 2.1.1 / 3.4 | shell ergonomics |
| hyperfine | 1.18.0 | command and latency benchmarking |
| shellcheck | 0.9.0 | script lint |
| just | 1.21.0 | task runner |
| ffmpeg, cmake, ninja-build, pkg-config | 6.1.1 / 3.28.3 / 1.11.1 | media and native builds |
| python3-pip, python3-venv, pipx | 1.4.3 | packaging |

`~/.bashrc:118` exports `$HOME/.local/bin`, so `fd`, `bat`, `uv` and `inspect`
resolve in a normal shell. Already present: node 24.21, npm 12.1, ripgrep 14.1,
jq 1.7, gh 2.45, git 2.43, gcc 13.3, make 4.3.

Nothing was installed system-wide that alters the lab: no Docker, no systemd
change, `.wslconfig` untouched.

## Resource note

Starting WSL cost about **4.7 GiB of free physical memory** (10.29 -> 5.63 GiB
with the Strata engine resident). WSL has been shut down again; free physical is
back to 8.81 GiB and `wsl -l -v` shows `Stopped`. Treat `wsl --shutdown` as the
same class of lever as before and re-measure before any gated run.

Separately: with the Strata engine resident, GPU free is **552 MiB** against the
0.5 GiB (512 MiB) floor. The engine's `--vram-reserve-mib 1500` was holding
1.29 GiB free when it started, so roughly 740 MiB of VRAM has been taken by
something else since (a browser or Perplexity GPU process). No app was closed.
Worth re-measuring before any screen that has a VRAM gate.

## Verification

- `omp config get skills.customDirectories` returns the three registered roots.
- `omp read skill://canvas-design`, `skill://docx`, `skill://lab-evidence-discipline` all resolve.
- `omp read skill://no-such-xyz` lists 50 skills.
- `~/.local/bin/uv --version` -> 0.12.23 after a sha256 match against the
  published checksum file; `inspect --version` -> 0.3.277.
- `wsl -l -v` -> Stopped; Windows free physical 8.81 GiB.
