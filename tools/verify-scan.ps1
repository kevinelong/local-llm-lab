# verify-scan.ps1 - did today's news scan actually write its file?
# A clean exit code is not evidence: on 2026-10-21 the wrapper started, printed "Now writing today's scan",
# and was killed (-1073741510) with no file.
#
# 2026-10-22: a same-day file may be renamed (NEWS-2026-10-22a.md) so a second run cannot overwrite it. So the
# check is "a NEWS-<today>*.md written AFTER this run started", using a marker the wrapper touches just before
# invoking the scan. Existence alone would let a stale file from earlier in the day pass.
param(
    [string]$Repo,
    [string]$Marker = ''
)
$d = Get-Date -Format 'yyyy-MM-dd'
$files = @(Get-ChildItem -Path $Repo -Filter ('NEWS-' + $d + '*.md') -File -ErrorAction SilentlyContinue)
if ($Marker -and (Test-Path $Marker)) {
    $started = (Get-Item $Marker).LastWriteTime
    $fresh = @($files | Where-Object { $_.LastWriteTime -gt $started })
} else {
    $fresh = $files
}
if ($fresh.Count -gt 0) {
    $names = (($fresh | ForEach-Object { $_.Name }) -join ', ')
    Write-Output ('[' + $d + '] verify OK: ' + $names + ' present')
    exit 0
}
Write-Output ('[' + $d + '] verify FAILED: no NEWS-' + $d + '*.md written after this run started')
exit 1
