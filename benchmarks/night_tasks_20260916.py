"""Small repair fixtures and external evaluation; no model access."""
import copy
import heapq
import importlib.util
import json
from pathlib import Path
import random
import sys

TASKS = {
    'graph': {
        'spec': 'Repair solution.py: plan(tasks) returns all task IDs in dependency order. Each task has unique integer id, priority (larger first), and deps (list of IDs). At every step choose the highest-priority currently available task, then smallest ID. Raise ValueError for duplicate IDs, missing dependencies, or cycles. Empty input returns []. Never mutate the input. Python 3.11, standard library only.',
        'code': 'def plan(tasks):\n    return [t["id"] for t in sorted(tasks, key=lambda t: (-t["priority"], t["id"]))]\n',
        'public': 'from solution import plan\na=[dict(id=1,priority=1,deps=[]),dict(id=2,priority=5,deps=[1])]\nassert plan(a)==[1,2]\ntry:\n    plan([dict(id=1,priority=1,deps=[1])])\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError("cycle not rejected")\nprint("public checks passed")\n',
    },
    'intervals': {
        'spec': 'Repair solution.py: merge(intervals) accepts a list of pairs of integer endpoints for nonempty half-open intervals [start,end). Return sorted tuples merging overlapping intervals transitively; merely touching intervals must remain separate. Duplicates merge. Negative endpoints are allowed. Empty input returns []. Invalid pair length, non-integer endpoints (including bool), or start >= end raises ValueError. Do not mutate input. Python 3.11, standard library only.',
        'code': 'def merge(intervals):\n    intervals.sort()\n    out=[]\n    for a,b in intervals:\n        if out and a <= out[-1][1]:\n            out[-1]=(out[-1][0],b)\n        else:\n            out.append((a,b))\n    return out\n',
        'public': 'from solution import merge\nassert merge([(1,3),(3,5)])==[(1,3),(3,5)]\nassert merge([(1,9),(2,4)])==[(1,9)]\nprint("public checks passed")\n',
    },
}

def reference_graph(tasks):
    nodes = {t['id']: t for t in tasks}
    if len(nodes) != len(tasks): raise ValueError('duplicate')
    remaining = {i: set(t['deps']) for i,t in nodes.items()}
    if any(d not in nodes for deps in remaining.values() for d in deps): raise ValueError('missing')
    result=[]
    while remaining:
        ready=[(-nodes[i]['priority'],i) for i,deps in remaining.items() if not deps]
        if not ready: raise ValueError('cycle')
        _, chosen=min(ready)
        result.append(chosen)
        del remaining[chosen]
        for deps in remaining.values(): deps.discard(chosen)
    return result

def reference_intervals(values):
    for pair in values:
        if not isinstance(pair,(list,tuple)) or len(pair)!=2: raise ValueError('pair')
        a,b=pair
        if type(a)!=int or type(b)!=int or a>=b: raise ValueError('endpoints')
    out=[]
    for a,b in sorted(values):
        if out and a<out[-1][1]: out[-1]=(out[-1][0],max(b,out[-1][1]))
        else: out.append((a,b))
    return out

def cases(kind):
    rng=random.Random(20260916)
    if kind=='graph':
        values=[[],[dict(id=1,priority=1,deps=[1])],
                [dict(id=1,priority=1,deps=[99])],
                [dict(id=1,priority=1,deps=[]),dict(id=1,priority=2,deps=[])],
                [dict(id=1,priority=1,deps=[2]),dict(id=2,priority=1,deps=[1])]]
        for _ in range(50):
            ids=list(range(1,rng.randint(3,14)))
            rng.shuffle(ids)
            items=[dict(id=i,priority=rng.randint(1,5),deps=[j for j in ids[:k] if rng.random()<0.25]) for k,i in enumerate(ids)]
            rng.shuffle(items)
            values.append(items)
    else:
        values=[[],[(1,3),(3,5)],[(1,9),(2,4)],[(0,2),(1,4),(3,9)],[(1,1)],[(4,1)],[(True,5)],[(1.5,4)],[(1,2,3)],[(1,2),(1,2)], [(-9,-3),(-4,1)]]
        for _ in range(50):
            values.append([(a:=rng.randint(-30,30),a+rng.randint(1,15)) for _ in range(rng.randint(0,15))])
    return values

def evaluate(kind, path):
    spec=importlib.util.spec_from_file_location('candidate',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func=getattr(module,'plan' if kind=='graph' else 'merge')
    ref=reference_graph if kind=='graph' else reference_intervals
    checks=[]
    for index,value in enumerate(cases(kind)):
        original=copy.deepcopy(value)
        try: expected=ref(copy.deepcopy(value)); invalid=False
        except ValueError: expected=None; invalid=True
        try:
            actual=func(value)
            passed=not invalid and actual==expected and value==original
        except ValueError: passed=invalid and value==original
        except Exception: passed=False
        checks.append({'case':index,'pass':passed})
    return {'passed':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks}

if __name__=='__main__':
    try: print(json.dumps(evaluate(sys.argv[1],Path(sys.argv[2]))))
    except Exception as exc: print(json.dumps({'passed':0,'total':len(cases(sys.argv[1])),'error':str(exc)}))
