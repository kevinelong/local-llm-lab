"""Recheck archived programs without model inference or changes to old scores."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
env = dict(os.environ, PYTHONIOENCODING="utf-8")

def run(command, cwd):
    p = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    return {"exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

results = {}
for source in sorted((REPO / "examples/hard-spec-tasks").glob("tasks.*.py")):
    with tempfile.TemporaryDirectory(prefix="lab_review_20260920_") as directory:
        work = Path(directory)
        shutil.copy2(source, work / "tasks.py")
        entry = {}
        for label, scorer in [("historical", REPO / "examples/eval2.py"),
                              ("supplemental", REPO / "benchmarks/eval_round_20260915.py")]:
            entry[label] = run([sys.executable, str(scorer), str(work)], work)
        if source.name == "tasks.aider.py":
            entry["cycle_reproduction"] = [
                {"args": args, **run([sys.executable, "tasks.py", *args], work)}
                for args in [["add", "A"], ["add", "B"],
                             ["dep", "1", "--on", "2"], ["dep", "2", "--on", "1"], ["plan"]]
            ]
        if source.name == "tasks.claude.py":
            run([sys.executable, "tasks.py", "add", "PRESERVE_ME"], work)
            before = (work / "tasks.json").read_text(encoding="utf-8")
            outcome = run([sys.executable, "tasks.py", "test"], work)
            after = (work / "tasks.json").read_text(encoding="utf-8")
            entry["preservation_reproduction"] = {
                "before": before, "test": outcome, "after": after,
                "listing_after": run([sys.executable, "tasks.py", "list"], work),
            }
        results[source.name] = entry
        print(source.name, entry["historical"]["stdout"].strip().splitlines()[-1],
              entry["supplemental"]["stdout"].strip(), flush=True)

with tempfile.TemporaryDirectory(prefix="lab_review_broken_") as directory:
    work = Path(directory)
    (work / "tasks.py").write_text("raise RuntimeError('deliberately broken control')\n", encoding="ascii")
    results["broken_control"] = run([sys.executable, str(REPO / "examples/eval2.py"), str(work)], work)

output = Path(__file__).with_name("archived-audit.json")
output.write_text(json.dumps(results, indent=2), encoding="utf-8")
print("Evidence:", output)
