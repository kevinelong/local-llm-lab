#!/usr/bin/env bash
# Does Inkling get faster at a smaller context? It is served by llama-server, so each window is a fresh
# process with a different -c. Same prompt, same 400-token budget, same probe as the other models.
set -u
BIN=/d/build/llamacpp-b12611/build-cuda135/bin/llama-server.exe
MODEL='D:\models\inkling-2-mini\Inkling-2-Mini-UD-IQ2_XXS.gguf'
PROJ='D:\models\inkling-2-mini\mmproj-F16.gguf'
export PATH="/d/tools/cuda-13.5/bin/x64:/d/tools/cuda-13.5/bin:$PATH"

powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force" 2>/dev/null
sleep 3

for C in 4096 8192 16384 32768; do
  echo "=== ctx $C"
  powershell -NoProfile -Command "\$env:PATH='"$(cygpath -w /d/tools/cuda-13.5/bin/x64)";$(cygpath -w /d/tools/cuda-13.5/bin)';' + \$env:PATH; \$p = Start-Process -FilePath '$(cygpath -w $BIN)' -ArgumentList '-m','$MODEL','--mmproj','$PROJ','--host','127.0.0.1','--port','8080','-c','$C','-ub','512','-fa','on','-ngl','99','-np','1','--jinja' -PassThru -WindowStyle Hidden; 'started ' + \$p.Id" 
  for i in $(seq 1 60); do
    if curl -s --max-time 3 http://127.0.0.1:8080/health | grep -q '"ok"'; then break; fi
    sleep 2
  done
  nvidia-smi --query-gpu=memory.used --format=csv,noheader
  cd /c/Users/kevin/local-llm-lab && python benchmarks/speed-probe-2026-11-22.py --base-url http://127.0.0.1:8080 --model "inkling ctx$C" --runs 3 2>/dev/null
  powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force" 2>/dev/null
  sleep 3
done
