@echo off
REM Start a FRESH OMP session for the local LLM lab, without inheriting the previous session.
REM
REM Why this exists (2026-10-19): a bare `omp` auto-resumes the most recent session for the working
REM directory. The session that produced the 2026-10-18/19 work ran to a peak prompt of 848,437 tokens,
    REM compacted once, and carried a 430k median prompt - that is the "shape" we do not want to resume.
REM `--goal` is the documented bypass for autoResume, and starting inside the repo also gives a
REM per-project session namespace instead of accumulating everything under %TEMP%.
REM
REM Usage:
REM   start-lab-session.cmd            launch fresh, default thinking level (low, from config.yml)
REM   start-lab-session.cmd high       launch fresh with --thinking high (judgment-heavy work)
REM   start-lab-session.cmd check      print the resolved command and exit - no session is started
REM
REM The goal text names the state notes rather than restating them, so a fresh session re-briefs from
REM files on disk (AGENTS.md, the newest NEWS-*.md) instead of needing the old transcript.
setlocal
set "REPO=C:\Users\kevin\local-llm-lab"
set "OMP=%USERPROFILE%\.local\bin\omp.exe"
set "GOAL=Continue the local LLM lab. Read AGENTS.md (recent entries) and the newest NEWS-*.md first, then the ranked shortlist. One inference workload at a time; check the memory gates (9 GiB free physical, 8 GiB commit headroom) before loading anything."

set "THINK="
set "MODE=run"
for %%A in (%*) do (
  if /i "%%A"=="high"  set "THINK=--thinking high"
  if /i "%%A"=="check" set "MODE=check"
)
if /i "%MODE%"=="check" goto check

if not exist "%OMP%" (
  echo ERROR: omp not found at "%OMP%"
  exit /b 1
)
if not exist "%REPO%\AGENTS.md" (
  echo ERROR: lab repo not found at "%REPO%"
  exit /b 1
)

cd /d "%REPO%"
echo Starting a FRESH goal-mode session in %CD%
if defined THINK (echo Thinking level: high) else (echo Thinking level: default ^(low^))
"%OMP%" --goal "%GOAL%" %THINK%
endlocal
exit /b %ERRORLEVEL%

:check
echo omp      : "%OMP%"
echo cwd      : "%REPO%"
echo thinking : %THINK%
echo goal     : %GOAL%
echo.
echo resolved : "%OMP%" --goal "%GOAL%" %THINK%
endlocal
exit /b 0
