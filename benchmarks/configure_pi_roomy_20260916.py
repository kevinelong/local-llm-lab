"""Install the experimental OmniCoder 32k/12k local Pi profile from trial config."""
import json
from pathlib import Path

home=Path('C:/Users/kevin')
trial=home/'ai_bench/stream-diagnosis-20260916/agent-tests/runs/pi-omni-hard-32768-3/config'
target=home/'ai_bench/stream-diagnosis-20260916/pi-config-roomy'
config=json.loads((trial/'models.json').read_text())
config['providers']['lab']['baseUrl']='http://127.0.0.1:11434/v1'
assert len(config['providers']['lab']['models'])==1
model=config['providers']['lab']['models'][0]
assert model['id']=='night-20260916-omni-32768' and model['maxTokens']==12288
settings=json.loads((trial/'settings.json').read_text())
assert settings['compaction']['reserveTokens']==12288
target.mkdir(parents=True,exist_ok=True)
(target/'models.json').write_text(json.dumps(config,indent=2),encoding='ascii')
(target/'settings.json').write_text(json.dumps(settings,indent=2),encoding='ascii')
print(target)
