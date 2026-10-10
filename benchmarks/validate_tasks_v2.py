"""Validate v2 against a passing archived control and targeted fault injection."""
import json
from pathlib import Path
import shutil
import tempfile
import eval_tasks_v2 as evaluator

REPO = Path(__file__).resolve().parents[1]
OUT = Path('C:/Users/kevin/ai_bench/round-20260920/evaluation')
OUT.mkdir(parents=True,exist_ok=True)
reference = (REPO/'examples/hard-spec-tasks/tasks.astra.py').read_text(encoding='utf-8')
mutations = {
    'crash': ("raise RuntimeError('deliberately broken')\n", None),
    'always_success': ("raise SystemExit(0)\n", None),
    'selftest_overwrites': (reference.replace('    sys.exit(main())',
        "    result = main()\n    if len(sys.argv)>1 and sys.argv[1]=='test':\n        open('tasks.json','w').write('[]')\n    sys.exit(result)"), 'selftest_preserves_existing'),
    'cycle_exit_swallowed': (reference.replace('    sys.exit(main())',
        "    result = main()\n    sys.exit(0 if len(sys.argv)>1 and sys.argv[1]=='plan' else result)"), 'plan_cycle_exit'),
    'import_noop': (reference.replace('    sys.exit(main())',
        "    if len(sys.argv)>1 and sys.argv[1]=='import': sys.exit(0)\n    sys.exit(main())"), 'csv_roundtrip_state'),
    'reuse_deleted_ids': (reference.replace('self.next_id = max(next_id, max(tasks, default=0) + 1)',
        'self.next_id = max(tasks, default=0) + 1'), 'ids_never_reused'),
}
summary = {}
for path in sorted((REPO/'examples/hard-spec-tasks').glob('tasks.*.py')):
    result = evaluator.evaluate(path)
    (OUT/(path.stem+'-v2.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    summary[path.name] = {'passed':result['passed'],'total':result['total'],
                          'failures':[c['name'] for c in result['checks'] if not c['passed']]}
    print(path.name, json.dumps(summary[path.name]), flush=True)
    if path.name=='tasks.astra.py': assert result['success'], summary[path.name]

for name,(source,target) in mutations.items():
    with tempfile.TemporaryDirectory(prefix='v2_mutation_') as directory:
        path = Path(directory)/'tasks.py'
        path.write_text(source,encoding='utf-8')
        assert source != reference
        # Full controls verify no false passes; targeted mutations exercise the
        # relevant end-to-end group rather than duplicating every unaffected test.
        if target is None:
            result = evaluator.evaluate(path)
            assert result['passed']==0, (name,result['passed'])
            summary[name] = {'passed':result['passed'],'total':result['total']}
        else:
            test = next(t for t in evaluator.CHECKS if t.__name__==target)
            with tempfile.TemporaryDirectory(prefix='v2_mutation_case_') as work:
                shutil.copy2(path,Path(work)/'tasks.py')
                try: test(evaluator.Candidate(work))
                except AssertionError as exc: summary[name] = {'detected_by':target,'error':str(exc)}
                else: raise AssertionError('Mutation escaped: '+name)
        print(name, json.dumps(summary[name]), flush=True)
(OUT/'validation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('Evaluator validation passed.',flush=True)
