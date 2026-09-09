# bench-model.ps1 - quick, repeatable benchmark of one local Ollama model.
#   .\bench-model.ps1 -Model qwen3:14b
# Prints: generation tok/s, GPU/CPU placement, and 3 correctness probes.
param(
  [Parameter(Mandatory)][string]$Model,
  [string]$Base = "http://127.0.0.1:11434"
)
function Gen($prompt, $np, $think) {
  $b = @{ model = $Model; prompt = $prompt; stream = $false; think = $think;
          options = @{ temperature = 0; num_predict = $np } } | ConvertTo-Json
  Invoke-RestMethod -Uri "$Base/api/generate" -Method Post -Body $b -ContentType "application/json" -TimeoutSec 600
}

Write-Output "############ $Model ############"
$tp = Gen "Write a clear 150-word explanation of how a bicycle works." 200 $false
Write-Output ("gen tok/s : {0}" -f [math]::Round($tp.eval_count / ($tp.eval_duration / 1e9), 1))
Write-Output ("eval_count: {0}   load_ms: {1}" -f $tp.eval_count, [math]::Round($tp.load_duration / 1e6, 0))
Write-Output ("placement : " + (((& ollama ps) | Select-Object -Skip 1) -join " | "))
Write-Output ("vram_used : " + ((nvidia-smi --query-gpu=memory.used --format=csv,noheader) -join ""))

# reasoning trap (thinking ON - forcing it off tests the wrong thing)
$r = Gen "A bat and a ball cost `$1.10 total. The bat costs `$1.00 more than the ball. How much is the ball?" 1500 $true
$ans = ($r.response -replace "`r?`n", " ").Trim()
Write-Output ("reasoning : " + $ans.Substring(0, [Math]::Min(160, $ans.Length)))

# factual / instruction following
$p = Gen "List the eight planets in order from the Sun, comma-separated, no other text." 300 $false
Write-Output ("planets   : " + (($p.response -replace "`r?`n", " ").Trim()))
Write-Output "done."
