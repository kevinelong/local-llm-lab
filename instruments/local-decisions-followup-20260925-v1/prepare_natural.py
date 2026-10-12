"""Freeze reviewed archival labels and a compact, deterministic state representation."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).parent
OLD = ROOT.parent / 'local-decisions-20260925-v1'

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def clip(text, limit):
    if len(text) <= limit: return text
    return text[:limit//2] + ' ... ' + text[-(limit//2-5):]

def successful_mutation(call):
    out = call.get('outcome')
    if not out or out['isError']: return False
    if call['tool'] in ('edit', 'write', 'apply_patch'): return True
    command = call['fullInput'].get('command', '')
    return bool(re.search(r'(?i)\b(Set-Content|Add-Content|Out-File|Remove-Item|Move-Item|Copy-Item|New-Item)\b|\bpython tasks\.py (add|dep|done|rm|import)\b', command))

def baseline(c):
    calls = c['audit']; key = calls[-1]['key']
    indices = [i for i,r in enumerate(calls) if r['key']==key]
    prev = [calls[i]['outcome'] for i in indices[:-1]]
    return (len(indices)>=3 and all(r['isError'] for r in prev)
            and len({r['sha256'] for r in prev})==1
            and not any(successful_mutation(r) for r in calls[indices[0]+1:-1]))

def main():
    assert not (ROOT/'natural-labels.json').exists(), 'Labels already frozen'
    candidates = json.loads((ROOT/'natural-candidates.json').read_text())
    reasons = [
        'Dependency diagnostic rerun after a successful, relevant test repair.',
        'Missing-dependency retest after fixing the deps normalization in solution.py.',
        'Edge-case test rewritten after diagnostic probes; failures change. Separate test-file policy violation is not a loop label.',
        'Three identical local scalar diagnostics, same successful output, no intervening change or polling requirement.',
        'Repeated merge probes with unchanged results and then three identical calls, no intervening edits.',
        'Malformed-input retest after changing validation and unpacking in solution.py.',
        'Three empty directory listings of harness files while implementation remains absent; no intervening change.',
        'Self-test rerun after a successful repair of the import assertion.',
        'Self-test rerun amid successful edits with a changed failure.',
        'Third identical edit after two identical no-change failures; a reread does not change the replacement.',
        'Public tests rerun after successful edits, with changing failing assertions.',
        'Public tests rerun after successful edits, with changing failing assertions.',
        'Self-test rerun after repairs; earlier failures and passed-test output differ.',
        'List requested after successful task removal and dependency mutation; outputs change.',
        'Plan requested after adding tasks; state and output change.',
        'Public tests rerun after successful solution edits.',
        'Public tests rerun after successful solution edits.',
        'Public tests rerun after successful solution edits and inspection.',
    ]
    assert len(candidates)==len(reasons)==18
    labels=[{'id':c['id'],'stuck':i in (4,5,7,10),'rationale':reasons[i-1]}
            for i,c in enumerate(candidates,1)]
    inputs=[]; rules=[]
    for c in candidates:
        keys={}; outputs={}; calls=[]
        for call in c['audit']:
            keys.setdefault(call['key'],len(keys)+1)
            row={'tool':call['tool'],'inputId':keys[call['key']],
                 'input':clip(json.dumps(call['fullInput'],sort_keys=True,ensure_ascii=False),160),
                 'successfulMutation':successful_mutation(call)}
            if 'outcome' in call:
                out=call['outcome'];outputs.setdefault(out['sha256'],len(outputs)+1)
                row['outcome']={'isError':out['isError'],'resultId':outputs[out['sha256']],
                                'chars':out['chars'],'excerpt':clip(out['excerpt'],120)}
            calls.append(row)
        inputs.append({'id':c['id'],'state':{'task':c['state']['task'][:400],
            'representation':'Same inputId means identical full tool and arguments; same resultId means identical full output. Excerpts are shortened.',
            'recentCalls':calls}})
        rules.append({'id':c['id'],'stuck':baseline(c)})
    for name,value in [('natural-labels.json',labels),('natural-inputs.json',inputs),('baseline-predictions.json',rules)]:
        (ROOT/name).write_text(json.dumps(value,indent=2),encoding='ascii')
    questions=json.loads(subprocess.check_output(['node','--input-type=module','-e',
        "import {QUESTIONS} from 'file:///C:/Users/kevin/ai_bench/jev-pi-observer-20260924-v1/core.mjs'; console.log(JSON.stringify(QUESTIONS));"],text=True))
    (ROOT/'questions.json').write_text(json.dumps(questions,indent=2),encoding='ascii')
    protocol=json.loads((ROOT/'protocol.json').read_text())
    protocol.update({'natural_inputs_sha256':digest(ROOT/'natural-inputs.json'),
        'natural_labels_sha256':digest(ROOT/'natural-labels.json'),
        'baseline_predictions_sha256':digest(ROOT/'baseline-predictions.json'),
        'prepare_source_sha256':digest(Path(__file__)),
        'natural_frozen_utc':datetime.now(timezone.utc).isoformat(),
        'natural_labels':'Single reviewer, 4 positive and 14 negative; no independent annotator; no model scores seen.',
        'natural_representation':'12 calls preserved, task first 400 chars, input head/tail 160, output head/tail 120. Full input/output equality represented with local integer IDs. Full audit retained. Successful mutation metadata shared with both judges.',
        'baseline':'Third identical tool+full arguments; both prior outputs errors and identical; no successful edit/write/apply_patch or recognized shell mutation since first occurrence. Failed edits do not reset. Shell recognition is limited and no general side-effect inference is claimed.',
        'observer_scope':'All eligible first-per-key archival windows up to 3/source; original online observer emits at most once/user turn, so this is an expanded offline screen, not exact online firing counts.'})
    (ROOT/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='ascii')
    print(json.dumps({'labels':len(labels),'positive':sum(x['stuck'] for x in labels),'baseline_positive':sum(x['stuck'] for x in rules)}))

if __name__=='__main__': main()
