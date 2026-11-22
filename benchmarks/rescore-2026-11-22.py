"""Re-apply the current scorers to replies already saved by quality-pass-2026-11-22.py.

Why this exists: two scorer bugs were found after the first runs (a correct $0.05 answer that also explains
where $0.10 would come from was marked wrong, and "no crewed landing … has occurred" was not recognised as a
decline). Re-running the models would have changed nothing but the clock; the replies are stored verbatim in
the results files, so the *same answers* are scored again with the fixed rules. The model comparison then
rests on one scorer version, which is the only thing that makes the rows comparable.

Usage: python benchmarks/rescore-2026-11-22.py results/quality-*.json
"""

import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("qp", HERE / "quality-pass-2026-11-22.py")
qp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qp)

SCORERS = {name: scorer for name, _, scorer in qp.tasks()}


def main(paths):
    for path in paths:
        document = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        per_task, rows = {}, []
        for row in document["rows"]:
            scorer = SCORERS[row["task"]]
            ok, why = scorer(row["content"], None)
            row["ok"] = ok
            row["why"] = why
            rows.append(row)
            per_task.setdefault(row["task"], []).append(1 if ok else 0)
        passed = sum(sum(v) for v in per_task.values())
        possible = len(rows)
        document["rows"] = rows
        document["per_task"] = per_task
        document["passed"] = passed
        document["possible"] = possible
        document["rate"] = round(passed / possible, 3)
        document["scorer"] = "quality-pass-2026-11-22.py, re-scored after the bat_ball/no_invention fixes"
        pathlib.Path(path).write_text(json.dumps(document, indent=1), encoding="utf-8")
        print("%-42s %2d/%2d = %5.1f%%" % (document["label"], passed, possible, 100 * document["rate"]))
        for task, vector in per_task.items():
            print("   %-20s %s" % (task, vector))


if __name__ == "__main__":
    main(sys.argv[1:])
