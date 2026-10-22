@echo off
REM Daily local-LLM news scan - one non-interactive omp run.
REM Created 2026-10-16 with Kevin's standing instruction ("remember to do that daily").
REM Registered as the Windows scheduled task "omp daily lab news scan" (daily 07:30, runs when
REM available if the machine was off). The rule and the baseline live in AGENTS.md.
REM
REM The scan is READING ONLY: no downloads, installs, builds, engines, inference or benchmarks, and it
REM must never touch C:\Users\kevin\ai_bench, which holds the measurement evidence. It writes one file
REM (NEWS-<date>.md), updates the README's report list and AGENTS.md's dated entry, and commits only
REM those paths - never "git add -A", so an unrelated uncommitted change is never swept into its commit.
REM
REM Run it by hand the same way the task runs it; the log is %TEMP%\daily-news-scan.log.
REM Pass an argument to exercise the mechanism without running a scan:
REM   daily-news-scan.cmd SCAN-OK        (a single word: a quoted phrase with a colon trips cmd's parser
REM                                        before the script runs, which is a shell quirk, not a scan failure)
setlocal
set "REPO=C:\Users\kevin\local-llm-lab"
set "OMP=%USERPROFILE%\.local\bin\omp.exe"
set "LOG=%TEMP%\daily-news-scan.log"
set "PROMPT=Standing instruction: the daily local-LLM news scan. Read the standing-rule entry in C:\Users\kevin\local-llm-lab\AGENTS.md and the most recent NEWS-*.md, then write today's NEWS-<YYYY-MM-DD>.md: what moved since the previous scan, every claim with a source and a date, whether each item applies to this box, which existing instrument would test it, what the test costs, a ranked shortlist of at most seven items, and a 'checked and nothing moved' list. Then update AGENTS.md's dated entry and the README report list, and commit those three paths and push - never git add -A. Reading only: no downloads, installs, builds, engines, inference or benchmarks, and never touch C:\Users\kevin\ai_bench, which holds measurement evidence and may have a run in flight. Search ALL of these platforms every run, broadly, on Kevin's standing instruction (2026-10-22): breadth is preferred to precision because there is time to review many items, so a plausible false positive is cheaper than a miss. Tag every item with its source class: [GH] GitHub issue or pull request, [REL] release notes, [HFR] Hugging Face model repo, [ARX] arXiv, [YT] YouTube, [RD] Reddit, [HN] Hacker News. Per platform, answer its own question and no other: (1) GitHub issues and PRs on llama.cpp, Strata, Ollama, ComfyUI and Colibri - what changed in the code, with a patch or commit; go deep and read the whole thread. (2) GitHub issues on ADJACENT projects whenever the item is about VRAM, memory, offload, kernels, quantisation or Windows drivers - do not follow other projects' roadmaps or product news, but do not drop a memory-shaped report because the repo is unfamiliar. (3) Release notes - which flags exist now, at which version. (4) Hugging Face - sweep model repos broadly: created, lastModified, revision, file count, bytes, quantisation mix, licence, context; report a revision move even when sizes are unchanged. (5) arXiv cs.CL and cs.LG - read the new listings, prioritising quantisation, Mixture-of-Experts routing, KV cache, speculative decoding and long-context, and say how many new papers the index carried. (6) YouTube - DAILY, found with web search and read from captions, because video is where practical tuning recipes live rather than announcements: fetch with "wsl -e bash -lc \"yt-dlp --skip-download --write-auto-subs --sub-langs 'en.*' --sub-format vtt URL\"", quote with timestamps, label the item second-hand with channel and upload date, and record a recipe or a symptom, never a benchmark number as fact. (7) Reddit r/LocalLLaMA - DAILY, for symptoms that carry a card, driver, engine version and quant before any issue exists. (8) Hacker News - DAILY, for the same reason. Skip Discord and X: not searchable or not verifiable. Items from [YT], [RD] and [HN] may enter the ranked shortlist only if you name the local test that would settle them, and they must never be cited as measured facts. Do not re-review something a previous NEWS file already covered - cite that file's date instead."
set "RUNVERIFY=1"
if not "%~1"=="" set "PROMPT=%~1"
if not "%~1"=="" set "RUNVERIFY=0"

echo [%DATE% %TIME%] daily news scan start >> "%LOG%"
REM Marker: the verifier accepts a suffixed same-day file, so it must know when THIS run started.
type nul > "%TEMP%\daily-news-scan.start"
"%OMP%" -p "%PROMPT%" --cwd "%REPO%" --thinking high --max-time 75m >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo [%DATE% %TIME%] daily news scan exit %RC% >> "%LOG%"
REM A start line without this exit line means the wrapper was killed (seen 2026-10-21, exit -1073741510).
REM When the real scan runs, verify it wrote today's file: a clean exit code is not evidence.
if "%RUNVERIFY%"=="1" powershell -NoProfile -ExecutionPolicy Bypass -File "%REPO%\tools\verify-scan.ps1" -Repo "%REPO%" -Marker "%TEMP%\daily-news-scan.start" >> "%LOG%" 2>&1
if errorlevel 1 set "RC=1"
endlocal & exit /b %RC%
