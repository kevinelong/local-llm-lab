# DARKTEXAS — Local AI & Agent Stack: Restart / Resume Notes

Last updated: **2026-10-12**. The 2026-07-08 section further down is kept for history and is now wrong on
several facts (it says 32 GB RAM and Ollama 0.31.1); everything in this section is measured today.

## The machine now

- **RAM 63.46 GiB usable, dual channel:** DIMM1 32 GB @ 5600 **+ DIMM2 32 GB @ 5600** (installed 2026-10-07,
  no down-bin).
- **Two 1 TB NVMe of the same model.** `C:` carries Windows; **`D:` is a second physical NVMe and is the
  models drive** - measured throughput parity with `C:`, 252.8 GiB free on 2026-10-12. New model downloads go
  to `D:\ai_bench-staged\`. `C:` free space moves with the **pagefile**, which grows under engine load and
  releases on its own: a `C:` drop is not a leak, and free disk here is not a static resource.
- **GPU RTX 5070 12 GB** (driver 32.0.16.1060 as Windows reports it; NVIDIA branch 610.x), **Intel iGPU**
  (32.0.101.8860) and the NPU. The NPU has no usable path in any engine here; the iGPU measures ~0.39x the
  5070 and is at best a second device for small decision work.
- **Python**: 3.11.9 on PATH, and the `py` launcher defaults to **3.14** (Colibri's launcher uses it).
  **Rust/cargo run on Windows**; gcc, cmake, ninja, uv, gh, jq and ffmpeg live in **WSL (Ubuntu)**.
- **WSL Ubuntu** costs ~5 GiB resident while running - shut it down (`wsl --shutdown`) when idle, because its
  memory is usually what trips a lab gate. Kevin's own `tools/dev-server.py` holds port 8080 and the WSL relay
  holds 8000; both are his, not lab leftovers.
- **Ollama 0.40.0**, autostarts on login (the only inference startup entry). `ollama list` still shows the
  2026-09-16 night models.
- Launchers on PATH via `C:/Users/kevin/ai_bench` (7 `.cmd` shims): `aider-local`, `oi-local`, `oi-research`,
  `ux-verify`, `ux-feature`, `pi-local`, `ask`.

## The lab's state, and what to read first

1. `ai_bench/CONTINUE-HERE.md` - the handoff index; its top section is a restart checklist.
2. `local-llm-lab/AGENTS.md` - the running changelog; its newest entry is the pause.
3. `local-llm-lab/README.md` - the measured recommendations.

- **A queue is paused, not abandoned.** `ai_bench/overnight-20261011/OVERNIGHT-STOP` is in place. Resume path:
  delete that file, then `cd overnight-20261011 && python runner.py --only i4-reason-repeat,i6-gliner-replay`,
  then the Colibri Qwen3.6-35B-A3B knowledge comparison (model already complete on `D:`) - and **never use
  `coli setup`** for it, because it ends by running the server in the foreground and never returns.
- **Nothing from the lab is resident.** Check the gates before any load: free physical >= 9 GiB and commit
  headroom >= 8 GiB, with runtime floors 3 / 2 / 0.5 GiB, one inference workload at a time.
- The instruments, frozen inputs and small evidence are snapshotted into the repo under
  `local-llm-lab/instruments/` (309 files, sha256 manifest); refresh with
  `python instruments/refresh-snapshot.py` and commit. `ai_bench` is **not** a git repo.
- **Licensing:** every public repo on this account is **FSL-1.1-MIT** - source-available, *not* OSI open
  source. Do not relicense the three third-party repos (`django-registration`, `mscgen`, `pdm`).
- **Preference in force:** commit and push after each change; open new documents with
  `ai_bench/Open-Document.ps1`.
- Published repos: `local-llm-lab` (notebook + instruments), `goproverbs`, `tek/tek-tube`, `score`,
  `score-dist`, `micro`, `fc` / `fc-app` / `fc-releases`.

---

# Historical: 2026-07-08

## Quick resume checklist (after a reboot)
1. **Ollama**: the desktop app auto-starts on login. Verify: `ollama --version` and
   `Invoke-RestMethod http://127.0.0.1:11434/api/version`. If down, launch the Ollama app or `ollama serve`.
2. Persistent env vars survive reboot (set at user level): `OLLAMA_CONTEXT_LENGTH=32768`.
   (`OLLAMA_FLASH_ATTENTION` was reset to default — do NOT re-disable it; MoE crash is fixed now.)
3. Everything below already installed; nothing to reinstall.

## Installed (versions as of 2026-07-08) — all current
- Ollama **0.31.1** (Blackwell MoE crash FIXED in this version)
- Claude Code **2.1.203** · Aider **0.86.2** · opencode **1.17.15** · Open Interpreter **0.4.3**
- GPU: RTX 5070 12GB (driver 595.95 / CUDA 13.2) · 32GB RAM · Python 3.11.9 · node 24.14.1

## Models (in Ollama)
qwen2.5-coder:7b (fast coder, 116 t/s) · qwen3-coder:30b (strong coder MoE, ~37 t/s CPU-offloaded) ·
qwen3:8b · qwen3:14b · qwen3:30b-a3b (general MoE) · deepseek-r1:8b · gemma3:12b · gemma4:12b ·
granite3-moe:3b (tiny/fast, 378 t/s). `ollama list` to confirm.

## One-command launchers (on PATH — usable from any shell/folder)
`~/ai_bench` is on the user PATH, with `.cmd` shims (cmd.exe) + `.ps1` (PowerShell). Open a NEW terminal
after a reboot for PATH to apply. Short commands:
- **Local coding (Aider):** `aider-local`  (or `aider-local -Model qwen3-coder:30b`)
- **Local shell agent (OI):** `oi-local`  (interactive) or `oi-local -Task "..."` (one-shot, auto-runs)
- **Local research agent (OI + web search):** `oi-research -Task "...search the web..."` (uses DuckDuckGo
  via research_tools.web_search; researches before answering instead of guessing). Use a stronger model
  for better synthesis: `oi-research -Model qwen3:14b -Task "..."`
- **UX verify harness:** `ux-verify -Url <url> -Screen <name>`
- **UX feature loop:** `ux-feature -RepoPath <repo> -Feature "..." -Url <url> -Screen <name>`
(Full paths still work too: `~/ai_bench/aider-local.ps1`, etc.)

## UX agent-loop PoC kit (~/ai_bench/ux-agent-poc) — built + validated, NOT yet on a real repo
- Grounding templates: `CLAUDE.md.template`, `design-system.CLAUDE.md.template`, `acceptance.example.md`
- Verify harness (Playwright+axe): `verify\run-verify.ps1 -Url <url> -Screen <name>`  (tested pass/fail)
- Hybrid dispatcher: `orchestrate\route.ps1` (cloud=`claude -p`, local-code=Aider, local-shell=OI)
- The loop: `orchestrate\run-feature.ps1 -RepoPath <repo> -Feature "..." -Url <url> -Screen <name>`

## Known issues / decisions
- **dsh web shell commands fail with "Windows ACL temp root must be outside the workspace"**: the
  dsh sandbox derives its temp root from os.tmpdir() (no config override), and the default per-user
  temp C:\Users\kevin\AppData\Local\Temp sits INSIDE the workspace C:\Users\kevin, so the fail-closed
  boundary check rejects every workspace-write shell call. FIX: start dsh with TMP/TEMP outside the
  workspace - use `~/ai_bench/dsh-web.ps1` (uses D:\dsh-temp, fallback C:\Users\Public\dsh-temp).
  A plain reboot does NOT fix it (env resets to the same inside-workspace temp); you must launch via
  `dsh-web`. Do NOT weaken the boundary check - it is a security design, not a bug.
- **opencode**: hangs on LOCAL Ollama (bug #14956, unfixed in 1.17.15). Use only with cloud providers.
- **MoE + 12GB**: 30B MoE models run ~37 t/s at ~50/50 CPU/GPU split with 32k context. Lower context
  (e.g. 8k) to keep more on GPU and go faster.
- Best local combo: Aider (coding) + Open Interpreter (shell) + qwen coders.

## THE NEXT STEP
Point the PoC kit at a REAL repo: fill the CLAUDE.md templates, start its dev server, run
`ux-agent-poc\orchestrate\run-feature.ps1` on ONE small net-new screen; measure iterations-to-green
and % kept local.

## DeepSeek Harness (dsh) - installed 2026, wired to DeepSeek API (working)
`dsh` v0.1.0-rc.7 installed globally via npm (`@deepseek-ai/dsh`); config at `C:\Users\kevin\.dsh`.
DeepSeek's open-source agent runtime (MIT, Claude Code rival, plugin-based; providers bundled: Anthropic,
OpenAI, Bedrock, Google, Mistral, DeepSeek, MCP). Run: `dsh web` (UI :3080), `dsh --profile headless "task"`,
`dsh --profile tui` (TUI not yet published). Wired to DeepSeek API via DEEPSEEK_API_KEY. ALWAYS launch via
`~/ai_bench/dsh-web.ps1` (see Known issues). Optional later: point its OpenAI-compatible provider at local
Ollama (http://127.0.0.1:11434/v1). Dev preview: expect breaking changes.

## Kimi archive (downloaded, CANNOT run on this box)
Full latest Kimi weights archived at **D:\models\Kimi-K2.7-Code** (554.3 GB, 87 files, verified complete
2026-07-24). Kimi-K2.7-Code = latest release, 1T-param MoE coding specialist, Modified-MIT. This machine
cannot run it (needs ~344-554 GB RAM/VRAM; box maxes at 64 GB). Use via cloud/API or future hardware.
Re-download/verify tool: ~/ai_bench/kimi_download.ps1 (curl-based, resumable, survives HF connection resets).

## Where things live
- Full report (all rounds 1–6): `~/ai_bench/REPORT.md`
- Playbook: `~/ai_bench/AGENT_LOOPS_PLAYBOOK.md`
- Benchmark data/scripts: `~/ai_bench/results*.json`, `benchmark*.ps1`
- Persistent memory (auto-loads next session): `~/.claude/projects/C--Users-kevin/memory/`
- Claude Code settings: `~/.claude/settings.json` (permissions.allow updated this session)
