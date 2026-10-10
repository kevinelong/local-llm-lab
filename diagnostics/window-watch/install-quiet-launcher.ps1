$ErrorActionPreference = 'Stop'
$stateDir = 'C:\Users\kevin\.codex\codex-router'
$backup = Join-Path $PSScriptRoot ('router-task-preinstall-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.xml')
Export-ScheduledTask -TaskName 'Codex Router' | Set-Content -LiteralPath $backup
foreach ($name in @('start-router-quiet.ps1', 'start-router-quiet.vbs')) {
    $destination = Join-Path $stateDir $name
    if (Test-Path -LiteralPath $destination) { throw "Refusing to overwrite existing file: $destination" }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $destination
}
$action = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\wscript.exe" -Argument ('//B //NoLogo "' + (Join-Path $stateDir 'start-router-quiet.vbs') + '"') -WorkingDirectory $stateDir
Set-ScheduledTask -TaskName 'Codex Router' -Action $action | Out-Null
Start-ScheduledTask -TaskName 'Codex Router'
[pscustomobject]@{AppliedAt=(Get-Date).ToString('o');Backup=$backup;Action='wscript.exe //B //NoLogo start-router-quiet.vbs'} | ConvertTo-Json
