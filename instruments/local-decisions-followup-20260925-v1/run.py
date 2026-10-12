"""Fixed follow-up actions; reuse the verified monitor in a separate artifact root."""
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).parent
OLD=ROOT.parent/'local-decisions-20260925-v1'
spec=importlib.util.spec_from_file_location('prior_monitor',OLD/'run.py')
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)
monitor.ROOT=ROOT;monitor.EVIDENCE=ROOT/'evidence'
if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('preflight','timing','natural','report'):
        raise SystemExit('Use preflight, timing, natural, or report')
    action=sys.argv[1]
    if action=='preflight':print(json.dumps(monitor.preflight()))
    elif action in ('timing','natural'):
        protocol=json.loads((ROOT/'protocol.json').read_text())
        if monitor.digest(ROOT/(action+'-inputs.json'))!=protocol[action+'_inputs_sha256']:
            raise RuntimeError('Inputs changed after freeze')
        monitor.run('openjev',action)
    else:
        import report
        report.main()
