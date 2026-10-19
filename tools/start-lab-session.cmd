@echo off
REM Lab entry point for a FRESH session. Delegates to the machine-wide launcher so there is one
REM implementation of the resume-bypass logic (bare `omp` auto-resumes the previous session - see the
REM global AGENTS.md).
REM
REM Usage:
REM   start-lab-session.cmd            fresh session in the lab, default (low) thinking
REM   start-lab-session.cmd high       fresh session with --thinking high
REM   start-lab-session.cmd check      print the resolved command, start nothing
setlocal
call "%USERPROFILE%\.local\bin\omp-fresh.cmd" "C:\Users\kevin\local-llm-lab" %*
endlocal & exit /b %ERRORLEVEL%
