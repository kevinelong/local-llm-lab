"""Prepare an isolated, stuck-only follow-up without modifying the prior trial."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).parent
OLD=ROOT.parent/'local-decisions-20260925-v1'
(ROOT/'evidence').mkdir(exist_ok=True)
text=(OLD/'worker.py').read_text()
replacements={
    "split in ('diagnostic','development','evaluation')":"split in ('timing','natural')",
    "model_path=ROOT/'models'/model_name":"model_path=ROOT.parent/'local-decisions-20260925-v1'/'models'/model_name",
    "ROOT/'upstream/openjev'":"ROOT.parent/'local-decisions-20260925-v1'/'upstream/openjev'",
    "limit=6 if split=='diagnostic' else 20":"limit=len(json.loads((ROOT/(split+'-inputs.json')).read_text()))",
    "set(questions)!={'stuck','wrong_approach'}":"set(questions)!={'stuck'}",
}
for old,new in replacements.items():
    assert text.count(old)==1,old
    text=text.replace(old,new)
target=ROOT/'worker.py'
if target.exists():raise SystemExit('Worker already prepared; preserve it')
target.write_text(text,encoding='ascii')
(ROOT/'evidence/worker-provenance.json').write_text(json.dumps({
    'original':str(OLD/'worker.py'),'original_sha256':hashlib.sha256((OLD/'worker.py').read_bytes()).hexdigest(),
    'changes':replacements,'followup_sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2),encoding='ascii')
