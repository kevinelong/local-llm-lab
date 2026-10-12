"""Check rule distinctions that matter for legitimate retries."""
import copy
import json
from pathlib import Path
from prepare_natural import baseline
ROOT=Path(__file__).parent
def action(key='x',tool='powershell',error=True,result='same',command='python test.py'):
    return {'key':key,'tool':tool,'fullInput':{'command':command},
            'outcome':{'isError':error,'sha256':result}}
pending=action();pending.pop('outcome')
loop={'audit':[action(),action(),pending]}
assert baseline(loop)
failed=copy.deepcopy(loop);failed['audit'].insert(2,action('edit','edit'))
assert baseline(failed), 'Failed edit must not reset'
fixed=copy.deepcopy(loop);fixed['audit'].insert(2,action('edit','edit',False))
assert not baseline(fixed), 'Successful edit permits retesting'
changed=copy.deepcopy(loop);changed['audit'][1]['outcome']['sha256']='different'
assert not baseline(changed), 'Changed failure permits further investigation'
poll=copy.deepcopy(loop)
for c in poll['audit'][:-1]: c['outcome']['isError']=False
assert not baseline(poll), 'The failure-only rule must not flag successful polls'
mutated=copy.deepcopy(loop);mutated['audit'].insert(2,action('change',error=False,command='python tasks.py add New'))
assert not baseline(mutated), 'Recognized successful data mutation permits retesting'
(ROOT/'evidence/baseline-tests.json').write_text(json.dumps({'checks':6,'passed':6},indent=2))
print('6 baseline behavior checks passed')
