@echo off
REM Daily local-LLM news scan - one non-interactive omp run.
REM Created 2026-10-16 with Kevin's standing instruction ("remember to do that daily").
REM Registered as the Windows scheduled task "omp daily lab news scan" (daily 07:30, runs when
REM available if the machine was off). Rule and baseline live in AGENTS.md.
REM
REM The scan is READING ONLY: no downloads, installs, builds, engines, inference or benchmarks, and it
REM must never touch C:\Users\kevin\ai_bench, which holds the measurement evidence. It writes one file
REM (NEWS-<date>.md), updates the README's report list and AGENTS.md's dated entry, and commits those.
REM
REM Run it by hand the same way the task runs it; the log is %TEMP%\daily-news-scan.log.
setlocal
set "REPO=C:\Users\kevin\local-llm-lab"
set "OMP=%USERPROFILE%\.local\bin\omp.exe"
set "LOG=%TEMP%\daily-news-scan.log"

echo [%DATE% %TIME%] daily news scan start >> "%LOG%"
"%OMP%" -p "Standing instruction: the daily local-LLM news scan. Read the standing-rule entry in C:\Users\kevin\local-llm-lab\AGENTS.md and the most recent NEWS-*.md, then write today's NEWS-<YYYY-MM-DD>.md: what moved since the previous scan, every claim with a source and a date, whether each item applies to this box, which existing instrument would test it, what the test costs, a ranked shortlist of at most seven items, and a 'checked and nothing moved' list. Then update AGENTS.md's dated entry and the README report list, commit and push. Reading only: no downloads, installs, builds, engines, inference or benchmarks, and never touch C:\Users\kevin\ai_bench, which holds measurement evidence and may have a run in flight." --cwd "%REPO%" --max-time 60m >> "%LOG%" 2>&1
echo [%DATE% %TIME%] daily news scan exit %ERRORLEVEL% >> "%LOG%"
endlocal
