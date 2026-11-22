"""Re-score stored hard-suite replies after a scorer fix, by rebuilding the deterministic plan.

The BBH scorer first compared the model's answer to the target *letter* only - so "ANSWER: 12/25/1937" was marked
wrong against "(B) 12/25/1937", and logical-deduction answers like "D" were wrong against "(D)". The items are
generated deterministically and in a fixed order, so the plan can be rebuilt and each stored row re-scored against
the same item, with the reply text unchanged.

  python benchmarks/rescore-hard-2026-11-22.py results/hard-reasoning-*.json
"""

import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("hp", HERE / "hard-probe-2026-11-22.py")
hp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hp)


def plan_for(suite, limit, ctx):
    if suite == "longctx":
        return [(name, scorer, want, "") for name, _prompt, scorer, want in hp.longctx_tasks(ctx)]
    plan = [(name, (lambda a, w=want, o=option: hp.bbh_ok(a, w, o)), want, option)
            for name, _p, want, option in hp.bbh_items("date_understanding", limit)]
    plan += [(name, (lambda a, w=want, o=option: hp.bbh_ok(a, w, o)), want, option)
             for name, _p, want, option in hp.bbh_items("logical_deduction_seven_objects", limit)]
    plan += [(name, scorer, want, "") for name, _p, want, scorer in hp.gsm8k_items(limit)]
    return plan


def main(paths):
    for path in paths:
        document = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        rows = document["rows"]
        limit = max(1, len(rows) // 3) if document["suite"] == "reasoning" else 0
        plan = plan_for(document["suite"], limit, document["ctx"])
        if len(plan) != len(rows):
            print("%s: plan %d rows but %d stored, skipping" % (path, len(plan), len(rows)))
            continue
        per = {}
        for row, (name, scorer, want, want_text) in zip(rows, plan):
            ok = bool(scorer(row["content"]))
            row["ok"] = ok
            row["why"] = "match" if ok else "no match"
            row["want"] = str(want)
            row["want_text"] = want_text
            per.setdefault(name, []).append(1 if ok else 0)
        passed = sum(sum(v) for v in per.values())
        document["rows"], document["per_task"] = rows, per
        document["passed"], document["possible"] = passed, len(rows)
        document["rate"] = round(passed / len(rows), 3)
        document["scorer"] = "hard-probe-2026-11-22.py, re-scored: BBH accepts the letter or the value"
        pathlib.Path(path).write_text(json.dumps(document, indent=1), encoding="utf-8")
        print("%-40s %2d/%2d" % (document["label"] + " " + document["suite"], passed, len(rows)))
        for task, vector in per.items():
            print("   %-34s %s" % (task, vector))


if __name__ == "__main__":
    main(sys.argv[1:])
