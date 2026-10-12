"""Report frozen follow-up evidence and verify owned-process cleanup."""
import hashlib
import json
import math
from pathlib import Path
import socket
import statistics
import time
import psutil

ROOT=Path(__file__).parent
OLD=ROOT.parent/'local-decisions-20260925-v1'
def read(path):return json.loads(path.read_text())
def lines(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def latency(rows):
    v=sorted(x['ms'] for x in rows)
    return {'n':len(v),'median_ms':statistics.median(v),'p95_ms':v[math.ceil(.95*len(v))-1],
            'max_ms':v[-1],'over_3000ms':sum(x>3000 for x in v)}
def metrics(labels,pred):
    return {k:sum(bool(pred[x['id']])==p and x['stuck']==g for x in labels)
            for k,p,g in [('tp',True,True),('fp',True,False),('tn',False,False),('fn',False,True)]}

def main():
    protocol=read(ROOT/'protocol.json')
    for field,name in [('timing_inputs_sha256','timing-inputs.json'),('natural_inputs_sha256','natural-inputs.json'),
                       ('natural_labels_sha256','natural-labels.json'),('baseline_predictions_sha256','baseline-predictions.json'),
                       ('prepare_source_sha256','prepare_natural.py')]:
        assert digest(ROOT/name)==protocol[field],name+' changed'
    provenance=read(ROOT/'evidence/worker-provenance.json')
    assert digest(OLD/'worker.py')==provenance['original_sha256']
    assert digest(ROOT/'worker.py')==provenance['followup_sha256']
    old_manifest=read(OLD/'evidence/source-manifest.json')
    for row in old_manifest:
        assert digest(Path(row['path']))==row['sha256'],row['path']
    sources=read(ROOT/'evidence/natural-sources.json')
    for row in sources:
        assert digest(Path(row['path']))==row['sha256'],row['path']
    labels=read(ROOT/'natural-labels.json')
    rules={x['id']:x['stuck'] for x in read(ROOT/'baseline-predictions.json')}
    timing=lines(ROOT/'evidence/openjev-timing/predictions.jsonl')
    natural=lines(ROOT/'evidence/openjev-natural/predictions.jsonl')
    assert len(timing)==46 and len(natural)==18
    assert {x['id'] for x in natural}=={x['id'] for x in labels}
    inputs={x['id']:x['state'] for x in read(ROOT/'natural-inputs.json')}
    counts={x['id']:x['tokens'] for x in read(ROOT/'evidence/natural-token-check.json')}
    for row in natural:
        canonical=json.dumps(inputs[row['id']],sort_keys=True,separators=(',',':'),ensure_ascii=False)
        assert hashlib.sha256(canonical.encode()).hexdigest()==row['stateHash']
        assert row['tokenCounts']==counts[row['id']] and max(row['tokenCounts'])<=2048
    original={x['id']:x for split in ('diagnostic','development','evaluation')
        for x in lines(OLD/('evidence/openjev-'+split+'-monitored-v2/predictions.jsonl'))}
    exact=all(x['p']==original[x['id']]['answer']['probabilities']['stuck'] and
        x['stateHash']==original[x['id']]['candidate']['stateHash'] for x in timing)
    assert exact
    owners=set(); resource_summary={}
    for split in ('timing','natural'):
        path=ROOT/('evidence/openjev-'+split)
        status=read(path/'status.json');assert status['error'] is None and status['worker_exited']
        resources=read(path/'resources.json')
        for r in resources:
            owners.update((p['pid'],p['created']) for p in r['owned_processes'])
        resource_summary[split]={'peak_private_gib':max(x['server_private_gib'] for x in resources),
             'min_free_ram_gib':min(x['physical_available_gib'] for x in resources),
             'min_commit_headroom_gib':min(x['commit_headroom_gib'] for x in resources),
             'min_free_vram_gib':min(x['gpu_free_gib'] for x in resources),
             'resource_samples':len(resources),'error':status['error']}
    alive=[]
    for pid,created in owners:
        try:
            p=psutil.Process(pid)
            if abs(p.create_time()-created)<.01:alive.append(pid)
        except psutil.NoSuchProcess:pass
    with socket.socket() as s:
        s.settimeout(1);port_closed=s.connect_ex(('127.0.0.1',8098))!=0
    cleanup={'owned_identities_checked':len(owners),'still_alive':alive,
             'port_8098_closed':port_closed,'lock_absent':not (ROOT/'RUNNING.lock').exists()}
    assert not alive and port_closed and cleanup['lock_absent'],cleanup
    probabilities={x['id']:x['p'] for x in natural}
    summary={'timing':{'all_46_probabilities_and_states_exact':exact,'all':latency(timing),
                'warm_excluding_first':latency(timing[1:]),
                'prior_paired_median_ms':statistics.median(original[x['id']]['answer']['ms'] for x in timing),
                'gate_passed':exact and latency(timing[1:])['p95_ms']<=3000},
             'natural':{'latency':latency(natural),'openjev':metrics(labels,{k:p>=.85 for k,p in probabilities.items()}),
                'failure_rule':metrics(labels,rules),'never_flag':metrics(labels,{k:False for k in probabilities}),
                'always_flag':metrics(labels,{k:True for k in probabilities})},
             'resources':resource_summary,'cleanup':cleanup,
             'verified_prior_source_files':len(old_manifest),'verified_archival_sources':len(sources)}
    (ROOT/'evidence/summary.json').write_text(json.dumps(summary,indent=2))
    t=summary['timing'];n=summary['natural']; stats=t['warm_excluding_first']
    report=['# OpenJev single-question and real-history follow-up - September 25, 2026','',
        'Completed offline, observation-only. No global hook or automatic intervention enabled. No reboot or startup changes.', '',
        f"Single-question scoring preserved all 46 original stuck probabilities exactly. Paired median latency changed from {t['prior_paired_median_ms']/1000:.2f}s to {t['all']['median_ms']/1000:.2f}s. Warm p95 is {stats['p95_ms']/1000:.2f}s: the fixed 3-second gate {'passed' if t['gate_passed'] else 'failed'}.", '',
        '## Natural-history screen','',
        '18 windows from 34 archived coding traces, selected before scoring (first per repeated key, at most 3 per source). These are real recorded histories newly used for this judge, not fresh coding runs. Four stalls and 14 legitimate retries/progress windows were labeled by one reviewer before inference; labels and rationales are frozen. No independent annotator, no threshold tuning, and correlated windows limit confidence. Labels concern stalled progress, not overall code correctness or policy compliance.', '',
        '| Judge | Caught stalls / 4 | Missed stalls | False alarms / 14 | Correct / 18 |',
        '|---|---:|---:|---:|---:|']
    for name,key in [('OpenJev, frozen threshold 0.85','openjev'),('Failure-only repeat rule','failure_rule'),('Never flag','never_flag'),('Always flag','always_flag')]:
        m=n[key];report.append(f"| {name} | {m['tp']} | {m['fn']} | {m['fp']} | {m['tp']+m['tn']} |")
    report += ['',f"Natural-history model latency: median {n['latency']['median_ms']/1000:.2f}s, p95 {n['latency']['p95_ms']/1000:.2f}s; {n['latency']['over_3000ms']}/18 exceed three seconds.", '',
        'The deterministic rule requires two identical failed outputs before the third identical call and no intervening successful edit or recognized mutation. Failed edits do not reset it. Successful read/diagnostic loops are outside its scope. It uses exact full-input/output identity, not clipped-text equality; six regression checks cover successful edits, failed edits, changed errors, successful polling, and data changes.', '',
        'Model and rule share mutation metadata. Model states retain all 12 calls but shorten input/output excerpts to 160/120 characters and task to 400; integer equality IDs replace long hashes. Maximum formatted input is 1,888 tokens, below the unchanged 2,048-token cap. Full source and audit hashes remain available. This representation differs from the synthetic control, so natural results are not a pure dataset-only comparison.', '',
        'Offline extraction allows multiple keys per source; the existing online observer emits at most once per user turn. These are screen metrics, not predicted live intervention counts.', '',
        '| Case | Reviewed stuck | OpenJev p | Rule flag | Rationale |','|---|---|---:|---|---|']
    for x in labels:
        report.append(f"| {x['id']} | {x['stuck']} | {probabilities[x['id']]:.4f} | {rules[x['id']]} | {x['rationale']} |")
    report += ['', '## Runtime and evidence','',
        'Pinned OpenJev 0.8B v5, CPU float32, four threads, batch size one. Same model and upstream wrapper as the prior trial; only the unused second question was removed in the timing control. Warm latency excludes the first request; model load is separate. Timing was not randomized or replicated, so speedup is descriptive.', '',
        '64 model requests: 46 repeated synthetic controls plus 18 archival windows. No concurrent inference. Initial gates remained 9 GiB free RAM / 8 GiB commit / 0.5 GiB VRAM; runtime floors 3 / 2 / 0.5 GiB, sustained paging guard, 6 GiB process-tree private cap, 900-second deadline, and STOP file.', '',
        '| Run | Peak process-tree private GiB | Minimum free RAM GiB | Minimum commit GiB |','|---|---:|---:|---:|']
    for key,r in resource_summary.items():report.append(f"| {key} | {r['peak_private_gib']:.2f} | {r['min_free_ram_gib']:.2f} | {r['min_commit_headroom_gib']:.2f} |")
    report += ['',f"Both runs completed without a resource abort. All {len(owners)} owned process identities are absent, port 8098 is closed, and the lock is removed. Prior worker provenance and all frozen follow-up input/label/baseline hashes verified.", '',
        f"All {len(old_manifest)} previously recorded source-file hashes and all {len(sources)} archived source hashes match. Every natural prediction matches its frozen state hash and pre-counted token length.", '',
        'Evidence: protocol.json; natural-labels.json; natural-candidates.json; baseline-predictions.json; evidence/natural-sources.json; evidence/natural-token-check.json; evidence/baseline-tests.json; evidence/summary.json; and both evidence/openjev-* run directories.', '',
        '## Decision','',
        'Do not promote OpenJev to automatic interruption. Its fixed latency gate failed, and these natural states are slower still. Keep the failure-only rule as an observation-only candidate. Next useful step: a cheap logging hook that records unchanged failures and successful-output loops separately, followed by independent labels from new sessions before considering intervention. Do not broaden the rule on these labels and call the same cases validation.', '']
    (ROOT/'REPORT.md').write_text('\n'.join(report),encoding='ascii')
    manifest={str(p.relative_to(ROOT)):digest(p) for p in ROOT.rglob('*') if p.is_file() and p.suffix in ('.py','.mjs','.json','.jsonl','.md') and p.name!='artifact-manifest.json'}
    (ROOT/'evidence/artifact-manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
