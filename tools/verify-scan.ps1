# verify-scan.ps1 - did today's news scan actually write its file?
# A clean exit code is not evidence: on 2026-10-21 the wrapper started, printed "Now writing today's scan",
# and was killed (-1073741510) with no file and no exit line in the log.
param([string]$Repo = 'C:\Users\kevin\local-llm-lab')
$d = Get-Date -Format 'yyyy-MM-dd'
$f = Join-Path $Repo ("NEWS-$d.md")
if (Test-Path $f) {
    Write-Output ("[" + $d + "] verify OK: NEWS-" + $d + ".md present")
    exit 0
}
Write-Output ("[" + $d + "] verify FAILED: no NEWS-" + $d + ".md - the scan is not complete")
exit 1
