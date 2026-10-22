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
set "PROMPT=Standing instruction: the daily local-LLM news scan. Read the standing-rule entry in C:\Users\kevin\local-llm-lab\AGENTS.md and the most recent NEWS-*.md, then write today's NEWS-<YYYY-MM-DD>.md: what moved since the previous scan, every claim with a source and a date, whether each item applies to this box, which existing instrument would test it, what the test costs, a ranked shortlist of at most seven items, and a 'checked and nothing moved' list. Then update AGENTS.md's dated entry and the README report list, and commit those three paths and push - never git add -A. Reading only: no downloads, installs, builds, engines, inference or benchmarks, and never touch C:\Users\kevin\ai_bench, which holds measurement evidence and may have a run in flight. Broaden the beat for this run, on Kevin's instruction (2026-10-22): search widely across, at minimum, (a) VRAM and memory constraints on consumer cards - quantisation formats, expert and weight offload, KV cache sizing, Windows WDDM/driver behaviour, and any measured report of free-VRAM floors or allocation failures; (b) new and updated local model releases - weights, quantisations, licences, context length, and any measured quality or speed numbers; (c) engine and toolchain changes that touch either. Label each item as VRAM or MODEL or ENGINE, and prefer a measured report over an announcement."
set "RUNVERIFY=1"
if not "%~1"=="" set "PROMPT=%~1"
if not "%~1"=="" set "RUNVERIFY=0"

echo [%DATE% %TIME%] daily news scan start >> "%LOG%"
REM Marker: the verifier accepts a suffixed same-day file, so it must know when THIS run started.
type nul > "%TEMP%\daily-news-scan.start"
"%OMP%" -p "%PROMPT%" --cwd "%REPO%" --thinking high --max-time 60m >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo [%DATE% %TIME%] daily news scan exit %RC% >> "%LOG%"
REM A start line without this exit line means the wrapper was killed (seen 2026-10-21, exit -1073741510).
REM When the real scan runs, verify it wrote today's file: a clean exit code is not evidence.
if "%RUNVERIFY%"=="1" powershell -NoProfile -ExecutionPolicy Bypass -File "%REPO%\tools\verify-scan.ps1" -Repo "%REPO%" -Marker "%TEMP%\daily-news-scan.start" >> "%LOG%" 2>&1
if errorlevel 1 set "RC=1"
endlocal & exit /b %RC%
