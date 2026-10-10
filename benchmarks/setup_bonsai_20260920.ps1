$ErrorActionPreference = 'Stop'
$labRoot = 'C:/Users/kevin/ai_bench/round-20260920/bonsai'
$tag = 'prism-b10709-9a9394a'
$revision = '6ed5e12bf84b7a63069882c91dd9e9218647d17b'
New-Item -ItemType Directory -Force -Path $labRoot | Out-Null
$release = Invoke-RestMethod -TimeoutSec 30 "https://api.github.com/repos/PrismML-Eng/llama.cpp/releases/tags/$tag"
$model = Invoke-RestMethod -TimeoutSec 30 "https://huggingface.co/api/models/prism-ml/Ternary-Bonsai-2-27B-gguf/revision/$revision`?blobs=true"
$release | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath "$labRoot/release.json" -Encoding utf8
$model | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath "$labRoot/model.json" -Encoding utf8
$assets = @("llama-$tag-bin-win-cuda-13.3-x64.zip", 'cudart-llama-bin-win-cuda-13.3-x64.zip')
foreach ($name in $assets) {
    $asset = $release.assets | Where-Object name -eq $name
    if (-not $asset) { throw "Missing release asset: $name" }
    $destination = "$labRoot/$name"
    if (-not (Test-Path -LiteralPath $destination) -or (Get-Item -LiteralPath $destination).Length -ne $asset.size) {
        & curl.exe --fail --location --retry 3 --connect-timeout 20 --max-time 1200 --continue-at - --output $destination $asset.browser_download_url
        if ($LASTEXITCODE -ne 0) { throw "Download failed: $name" }
    }
    if ((Get-Item -LiteralPath $destination).Length -ne $asset.size) { throw "Size mismatch: $name" }
    if ($asset.digest -and $asset.digest.StartsWith('sha256:')) {
        if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $asset.digest.Substring(7)) { throw "Hash mismatch: $name" }
    }
    Expand-Archive -LiteralPath $destination -DestinationPath "$labRoot/runtime" -Force
}
$name = 'Ternary-Bonsai-2-27B-PQ2_0.gguf'
$entry = $model.siblings | Where-Object rfilename -eq $name
if (-not $entry.lfs.sha256) { throw 'Missing model digest' }
$destination = "$labRoot/$name"
if (-not (Test-Path -LiteralPath $destination) -or (Get-Item -LiteralPath $destination).Length -ne $entry.size) {
    & curl.exe --fail --location --retry 3 --connect-timeout 20 --max-time 1800 --continue-at - --output $destination "https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/resolve/$revision/$name"
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed' }
}
$hash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne $entry.lfs.sha256) { throw 'Model checksum mismatch' }
@{ model_revision=$revision; model_sha256=$hash; model_bytes=(Get-Item -LiteralPath $destination).Length; runtime_tag=$tag; runtime_commit=$release.target_commitish } | ConvertTo-Json | Set-Content -LiteralPath "$labRoot/verified.json" -Encoding ascii
Write-Output 'Bonsai dependencies downloaded and verified.'
