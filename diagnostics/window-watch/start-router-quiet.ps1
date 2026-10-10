$ErrorActionPreference = 'Stop'
$stateDir = $PSScriptRoot
$logPath = Join-Path $stateDir 'quiet-launcher.log'
function Write-LauncherLog([string]$message) {
    Add-Content -LiteralPath $logPath -Value ((Get-Date -Format o) + ' ' + $message) -Encoding ASCII
}
try {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:4202/health' -TimeoutSec 5
        if ($health.ok -eq $true -and $health.service -eq 'codex-router') {
            Write-LauncherLog 'Router already healthy; no launch needed.'
            exit 0
        }
    } catch {
        # An unavailable health endpoint falls through to the existing launcher.
    }
    Write-LauncherLog 'Health check failed; starting router without a console.'
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = Join-Path $env:SystemRoot 'System32\cmd.exe'
    $info.Arguments = '/d /c ""' + (Join-Path $stateDir 'start-codex-router.cmd') + '""'
    $info.WorkingDirectory = $stateDir
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $child = [System.Diagnostics.Process]::Start($info)
    $child.WaitForExit()
    $result = $child.ExitCode
    $child.Dispose()
    Write-LauncherLog ('Router launcher exited with code ' + $result)
    exit $result
} catch {
    Write-LauncherLog ('Launcher failed: ' + $_.Exception.Message)
    exit 1
}
