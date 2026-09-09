"""Rigorous black-box scorer for the hard 'tasks.py' spec.
Usage: python eval2.py <dir-containing-tasks.py>
Prints PASS/FAIL per check and a final score. Format-tolerant: uses distinctive
titles and exit codes rather than parsing exact output layouts. Assumes 1-based
sequential task ids (per the spec's 'incrementing id')."""
import sys, os, shutil, subprocess, tempfile

SRC = os.path.join(sys.argv[1], "tasks.py")
if not os.path.exists(SRC):
    print("NO tasks.py in", sys.argv[1]); print("SCORE: 0/10"); sys.exit(0)

def fresh():
    d = tempfile.mkdtemp(prefix="taskeval_")
    shutil.copy(SRC, os.path.join(d, "tasks.py"))
    return d

def run(d, *args, timeout=60):
    try:
        p = subprocess.run([sys.executable, "tasks.py", *args], cwd=d,
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)
    except Exception as e:
        return 999, "EXC:" + repr(e)

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))

# 1. self-test
d = fresh(); c, o = run(d, "test"); check("self_test", c == 0, "exit=%d" % c)

# 2. add rejects nonexistent dep
d = fresh(); run(d, "add", "QPA"); c, o = run(d, "add", "QPX", "--dep", "999")
check("add_invalid_dep_rejected", c != 0, "exit=%d" % c)

# 3. done blocked by open dep, then unblocks
d = fresh(); run(d, "add", "QPA"); run(d, "add", "QPB", "--dep", "1")
c1, _ = run(d, "done", "2"); c2, _ = run(d, "done", "1"); c3, _ = run(d, "done", "2")
check("done_blocking", c1 != 0 and c2 == 0 and c3 == 0, "blocked=%d a_done=%d b_done=%d" % (c1, c2, c3))

# 4. ready = open tasks whose deps are all done
d = fresh(); run(d, "add", "QPA", "--priority", "5"); run(d, "add", "QPB", "--dep", "1")
c, o = run(d, "ready"); check("ready_set", c == 0 and "QPA" in o and "QPB" not in o, "exit=%d" % c)

# 5. plan is a valid topological order
d = fresh(); run(d, "add", "QPA"); run(d, "add", "QPB", "--dep", "1"); run(d, "add", "QPC", "--dep", "2")
c, o = run(d, "plan")
def before(a, b, s): return a in s and b in s and s.index(a) < s.index(b)
check("plan_topological", c == 0 and before("QPA", "QPB", o) and before("QPB", "QPC", o), "exit=%d" % c)

# 6. cycle detection via dep edges
d = fresh(); run(d, "add", "QPA"); run(d, "add", "QPB")
run(d, "dep", "1", "--on", "2"); run(d, "dep", "2", "--on", "1")
c, o = run(d, "plan"); check("cycle_detected", c != 0 and "cycle" in o.lower(), "exit=%d" % c)

# 7. rm refuses when depended on, --force cleans up
d = fresh(); run(d, "add", "QPA"); run(d, "add", "QPB", "--dep", "1")
c1, _ = run(d, "rm", "1"); c2, _ = run(d, "rm", "1", "--force")
check("rm_dependents_guard", c1 != 0 and c2 == 0, "refuse=%d force=%d" % (c1, c2))

# 8. export then import round-trip
d = fresh(); run(d, "add", "QPA"); run(d, "add", "QPB", "--dep", "1")
c1, _ = run(d, "export", "out.csv"); ex = os.path.exists(os.path.join(d, "out.csv"))
c2, _ = run(d, "import", "out.csv")
check("export_import", c1 == 0 and ex and c2 == 0, "exp=%d file=%s imp=%d" % (c1, ex, c2))

# 9. persistence across invocations
d = fresh(); run(d, "add", "QPZ"); c, o = run(d, "list"); check("persistence", c == 0 and "QPZ" in o, "exit=%d" % c)

# 10. corrupt tasks.json does not crash
d = fresh()
open(os.path.join(d, "tasks.json"), "w").write("not valid json {{{")
c, o = run(d, "list"); check("corrupt_file_safe", c == 0, "exit=%d" % c)

passed = sum(1 for _, ok, _ in results if ok)
print("==== %s ====" % os.path.basename(os.path.dirname(SRC + os.sep)))
for name, ok, detail in results:
    print("  %-26s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
print("SCORE: %d/%d" % (passed, len(results)))
