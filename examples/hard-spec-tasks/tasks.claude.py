#!/usr/bin/env python3
"""tasks - a dependency-aware task manager (Python stdlib only).

Tasks form a dependency graph and are persisted to tasks.json in the current
directory. See spec2.md for the full requirements.
"""

import sys
import os
import json
import csv
import time

DATA_FILE = "tasks.json"

VALID_STATUS = ("open", "done")


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def load(path=DATA_FILE):
    """Load tasks from the JSON file.

    A missing, empty, or corrupt file starts with no tasks and never crashes.
    Returns a dict: {"tasks": [...], "next_id": int}.
    """
    if not os.path.exists(path):
        return {"tasks": [], "next_id": 1}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
        if not content:
            return {"tasks": [], "next_id": 1}
        data = json.loads(content)
        tasks = data.get("tasks", [])
        if not isinstance(tasks, list):
            return {"tasks": [], "next_id": 1}
        # Normalize / sanitize tasks.
        clean = []
        for t in tasks:
            if not isinstance(t, dict) or "id" not in t:
                continue
            clean.append(_normalize_task(t))
        next_id = data.get("next_id")
        max_id = max((t["id"] for t in clean), default=0)
        if not isinstance(next_id, int) or next_id <= max_id:
            next_id = max_id + 1
        return {"tasks": clean, "next_id": next_id}
    except (json.JSONDecodeError, ValueError, OSError, TypeError):
        return {"tasks": [], "next_id": 1}


def _normalize_task(t):
    """Coerce a loaded task dict into the canonical shape."""
    tid = int(t["id"])
    title = str(t.get("title", ""))
    try:
        priority = int(t.get("priority", 3))
    except (ValueError, TypeError):
        priority = 3
    if priority < 1 or priority > 5:
        priority = 3
    status = t.get("status", "open")
    if status not in VALID_STATUS:
        status = "open"
    deps = t.get("deps", [])
    if not isinstance(deps, list):
        deps = []
    norm_deps = []
    for d in deps:
        try:
            norm_deps.append(int(d))
        except (ValueError, TypeError):
            continue
    created = t.get("created")
    if not isinstance(created, (int, float)):
        created = time.time()
    return {
        "id": tid,
        "title": title,
        "priority": priority,
        "status": status,
        "deps": norm_deps,
        "created": created,
    }


def save(state, path=DATA_FILE):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def find_task(state, tid):
    for t in state["tasks"]:
        if t["id"] == tid:
            return t
    return None


def task_map(state):
    return {t["id"]: t for t in state["tasks"]}


def deps_all_done(state, task, tmap=None):
    if tmap is None:
        tmap = task_map(state)
    for d in task["deps"]:
        dep = tmap.get(d)
        if dep is not None and dep["status"] != "done":
            return False
    return True


def open_blockers(state, task, tmap=None):
    """Return the ids of a task's dependencies that are still open."""
    if tmap is None:
        tmap = task_map(state)
    blockers = []
    for d in task["deps"]:
        dep = tmap.get(d)
        if dep is not None and dep["status"] != "done":
            blockers.append(d)
    return blockers


def ready_tasks(state):
    tmap = task_map(state)
    ready = [
        t for t in state["tasks"]
        if t["status"] == "open" and deps_all_done(state, t, tmap)
    ]
    ready.sort(key=lambda t: (-t["priority"], t["id"]))
    return ready


def dependents_of(state, tid):
    """Tasks that directly depend on tid (reverse edges)."""
    return [t for t in state["tasks"] if tid in t["deps"]]


def parse_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Topological ordering / cycle detection
# --------------------------------------------------------------------------- #
def topo_open(state):
    """Topological sort of open tasks respecting deps.

    Ties broken by priority (highest first) then id. Only open tasks are
    ordered; deps that are done are treated as already satisfied.

    Returns (order, cycle_ids). If a cycle exists among open tasks, order is
    None and cycle_ids is the sorted list of ids involved.
    """
    tmap = task_map(state)
    open_ids = {t["id"] for t in state["tasks"] if t["status"] == "open"}

    # Build in-degree counting only edges among open tasks.
    indeg = {tid: 0 for tid in open_ids}
    for tid in open_ids:
        for d in tmap[tid]["deps"]:
            if d in open_ids:
                indeg[tid] += 1

    # Kahn's algorithm with deterministic tie-breaking.
    available = [tid for tid in open_ids if indeg[tid] == 0]
    order = []
    while available:
        available.sort(key=lambda i: (-tmap[i]["priority"], i))
        tid = available.pop(0)
        order.append(tid)
        for other in open_ids:
            if tid in tmap[other]["deps"] and indeg[other] > 0:
                indeg[other] -= 1
                if indeg[other] == 0:
                    available.append(other)

    if len(order) != len(open_ids):
        cycle_ids = sorted(tid for tid in open_ids if indeg[tid] > 0)
        return None, cycle_ids
    return order, None


def longest_chain_depth(state):
    """Length of the longest dependency chain in the graph (# of tasks).

    Uses memoized DFS over dep edges. Cycles are handled gracefully (nodes in
    a cycle do not produce infinite depth).
    """
    tmap = task_map(state)
    memo = {}
    visiting = set()

    def depth(tid):
        if tid in memo:
            return memo[tid]
        if tid in visiting:
            return 0  # cycle guard
        visiting.add(tid)
        best = 0
        for d in tmap[tid]["deps"]:
            if d in tmap:
                best = max(best, depth(d))
        visiting.discard(tid)
        memo[tid] = best + 1
        return memo[tid]

    return max((depth(t["id"]) for t in state["tasks"]), default=0)


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
def format_task_line(t):
    marker = "[x]" if t["status"] == "done" else "[ ]"
    deps = ",".join(str(d) for d in t["deps"]) if t["deps"] else "-"
    return "%d %s P%d %s (deps: %s)" % (
        t["id"], marker, t["priority"], t["title"], deps
    )


# --------------------------------------------------------------------------- #
# Argument parsing (lightweight, per-command)
# --------------------------------------------------------------------------- #
def usage_error(msg=None):
    if msg:
        print("error: %s" % msg, file=sys.stderr)
    print(
        "usage: tasks.py <command> [args]\n"
        "commands: add, list, dep, done, rm, ready, plan, block, graph, "
        "search, stats, export, import, test",
        file=sys.stderr,
    )
    return 1


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_add(state, args):
    if not args:
        return usage_error("add requires a title")
    title = None
    priority = 3
    deps = []
    i = 0
    positional = []
    while i < len(args):
        a = args[i]
        if a == "--priority":
            if i + 1 >= len(args):
                return usage_error("--priority requires a value")
            p = parse_int(args[i + 1])
            if p is None or p < 1 or p > 5:
                return usage_error("--priority must be an integer 1-5")
            priority = p
            i += 2
        elif a == "--dep":
            if i + 1 >= len(args):
                return usage_error("--dep requires an id")
            d = parse_int(args[i + 1])
            if d is None:
                return usage_error("--dep must be an integer id")
            deps.append(d)
            i += 2
        else:
            positional.append(a)
            i += 1

    if len(positional) != 1:
        return usage_error("add requires exactly one title")
    title = positional[0]

    # Validate every dep references an existing task.
    existing = {t["id"] for t in state["tasks"]}
    for d in deps:
        if d not in existing:
            print("error: dependency %d does not exist" % d, file=sys.stderr)
            return 1

    # De-duplicate deps while preserving order.
    seen = set()
    uniq_deps = []
    for d in deps:
        if d not in seen:
            seen.add(d)
            uniq_deps.append(d)

    tid = state["next_id"]
    state["next_id"] += 1
    task = {
        "id": tid,
        "title": title,
        "priority": priority,
        "status": "open",
        "deps": uniq_deps,
        "created": time.time(),
    }
    state["tasks"].append(task)
    save(state)
    print("added task %d: %s" % (tid, title))
    return 0


def cmd_list(state, args):
    status = "all"
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--status":
            if i + 1 >= len(args):
                return usage_error("--status requires a value")
            status = args[i + 1]
            if status not in ("open", "done", "all"):
                return usage_error("--status must be open, done, or all")
            i += 2
        else:
            return usage_error("unknown argument: %s" % a)

    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    if status != "all":
        tasks = [t for t in tasks if t["status"] == status]

    if not tasks:
        print("(no tasks)")
        return 0
    for t in tasks:
        print(format_task_line(t))
    return 0


def cmd_dep(state, args):
    # dep <id> --on <other_id>
    if len(args) < 3 or args[1] != "--on":
        return usage_error("usage: dep <id> --on <other_id>")
    tid = parse_int(args[0])
    other = parse_int(args[2])
    if tid is None or other is None:
        return usage_error("dep requires integer ids")
    if tid == other:
        print("error: a task cannot depend on itself", file=sys.stderr)
        return 1
    task = find_task(state, tid)
    other_task = find_task(state, other)
    if task is None:
        print("error: task %d does not exist" % tid, file=sys.stderr)
        return 1
    if other_task is None:
        print("error: task %d does not exist" % other, file=sys.stderr)
        return 1
    if other not in task["deps"]:
        task["deps"].append(other)
        save(state)
    print("task %d now depends on %d" % (tid, other))
    return 0


def cmd_done(state, args):
    if len(args) != 1:
        return usage_error("usage: done <id>")
    tid = parse_int(args[0])
    if tid is None:
        return usage_error("done requires an integer id")
    task = find_task(state, tid)
    if task is None:
        print("error: task %d does not exist" % tid, file=sys.stderr)
        return 1
    blockers = open_blockers(state, task)
    if blockers:
        # Report the first (lowest-id) open dependency.
        print("cannot complete: blocked by open dependency %d" % min(blockers))
        return 1
    task["status"] = "done"
    save(state)
    print("task %d marked done" % tid)
    return 0


def cmd_rm(state, args):
    force = False
    positional = []
    for a in args:
        if a == "--force":
            force = True
        else:
            positional.append(a)
    if len(positional) != 1:
        return usage_error("usage: rm <id> [--force]")
    tid = parse_int(positional[0])
    if tid is None:
        return usage_error("rm requires an integer id")
    task = find_task(state, tid)
    if task is None:
        print("error: task %d does not exist" % tid, file=sys.stderr)
        return 1
    dependents = dependents_of(state, tid)
    if dependents and not force:
        dep_ids = ", ".join(str(d["id"]) for d in dependents)
        print(
            "error: task %d is depended on by %s (use --force)" % (tid, dep_ids),
            file=sys.stderr,
        )
        return 1
    # Remove the task.
    state["tasks"] = [t for t in state["tasks"] if t["id"] != tid]
    # Remove it from every dependent's deps.
    for t in state["tasks"]:
        if tid in t["deps"]:
            t["deps"] = [d for d in t["deps"] if d != tid]
    save(state)
    print("removed task %d" % tid)
    return 0


def cmd_ready(state, args):
    if args:
        return usage_error("ready takes no arguments")
    ready = ready_tasks(state)
    if not ready:
        print("(nothing ready)")
        return 0
    for t in ready:
        print(format_task_line(t))
    return 0


def cmd_plan(state, args):
    if args:
        return usage_error("plan takes no arguments")
    order, cycle = topo_open(state)
    if order is None:
        print("cycle detected: %s" % ", ".join(str(c) for c in cycle))
        return 1
    if not order:
        print("(no open tasks)")
        return 0
    tmap = task_map(state)
    for tid in order:
        print(format_task_line(tmap[tid]))
    return 0


def cmd_block(state, args):
    if len(args) != 1:
        return usage_error("usage: block <id>")
    tid = parse_int(args[0])
    if tid is None:
        return usage_error("block requires an integer id")
    task = find_task(state, tid)
    if task is None:
        print("error: task %d does not exist" % tid, file=sys.stderr)
        return 1
    blockers = open_blockers(state, task)
    if not blockers:
        print("task %d is not blocked" % tid)
        return 0
    tmap = task_map(state)
    for b in sorted(blockers):
        print(format_task_line(tmap[b]))
    return 0


def cmd_graph(state, args):
    if args:
        return usage_error("graph takes no arguments")
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    if not tasks:
        print("(no tasks)")
        return 0
    for t in tasks:
        dependents = sorted(d["id"] for d in dependents_of(state, t["id"]))
        dep_str = ", ".join(str(d) for d in dependents) if dependents else "-"
        print("%d %s -> dependents: %s" % (t["id"], t["title"], dep_str))
    return 0


def cmd_search(state, args):
    if len(args) != 1:
        return usage_error("usage: search <term>")
    term = args[0].lower()
    matches = [
        t for t in sorted(state["tasks"], key=lambda t: t["id"])
        if term in t["title"].lower()
    ]
    if not matches:
        print("(no matches)")
        return 0
    for t in matches:
        print(format_task_line(t))
    return 0


def cmd_stats(state, args):
    if args:
        return usage_error("stats takes no arguments")
    total = len(state["tasks"])
    open_count = sum(1 for t in state["tasks"] if t["status"] == "open")
    done_count = sum(1 for t in state["tasks"] if t["status"] == "done")
    ready_count = len(ready_tasks(state))
    blocked_count = sum(
        1 for t in state["tasks"]
        if t["status"] == "open" and open_blockers(state, t)
    )
    depth = longest_chain_depth(state)
    print("total: %d" % total)
    print("open: %d" % open_count)
    print("done: %d" % done_count)
    print("ready: %d" % ready_count)
    print("blocked: %d" % blocked_count)
    print("depth: %d" % depth)
    return 0


def cmd_export(state, args):
    if len(args) != 1:
        return usage_error("usage: export <file.csv>")
    path = args[0]
    try:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "title", "priority", "status", "deps"])
            for t in sorted(state["tasks"], key=lambda t: t["id"]):
                deps = ";".join(str(d) for d in t["deps"])
                writer.writerow(
                    [t["id"], t["title"], t["priority"], t["status"], deps]
                )
    except OSError as e:
        print("error: could not write %s: %s" % (path, e), file=sys.stderr)
        return 1
    print("exported %d tasks to %s" % (len(state["tasks"]), path))
    return 0


def cmd_import(state, args):
    if len(args) != 1:
        return usage_error("usage: import <file.csv>")
    path = args[0]
    if not os.path.exists(path):
        print("error: file %s does not exist" % path, file=sys.stderr)
        return 1
    imported = []
    try:
        with open(path, "r", newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            required = {"id", "title", "priority", "status", "deps"}
            if reader.fieldnames is None or not required.issubset(
                set(reader.fieldnames)
            ):
                print("error: CSV missing required columns", file=sys.stderr)
                return 1
            for row in reader:
                tid = parse_int(row["id"])
                if tid is None:
                    print("error: invalid id in CSV", file=sys.stderr)
                    return 1
                priority = parse_int(row["priority"])
                if priority is None or priority < 1 or priority > 5:
                    priority = 3
                status = row["status"] if row["status"] in VALID_STATUS else "open"
                deps_raw = (row["deps"] or "").strip()
                deps = []
                if deps_raw:
                    for part in deps_raw.split(";"):
                        part = part.strip()
                        if not part:
                            continue
                        d = parse_int(part)
                        if d is None:
                            print("error: invalid dep id in CSV", file=sys.stderr)
                            return 1
                        deps.append(d)
                imported.append({
                    "id": tid,
                    "title": row["title"],
                    "priority": priority,
                    "status": status,
                    "deps": deps,
                    "created": time.time(),
                })
    except (OSError, csv.Error) as e:
        print("error: could not read %s: %s" % (path, e), file=sys.stderr)
        return 1

    # Validate every dep references a task that exists in the imported set.
    ids = {t["id"] for t in imported}
    for t in imported:
        for d in t["deps"]:
            if d not in ids:
                print(
                    "error: dependency %d referenced by task %d does not exist"
                    % (d, t["id"]),
                    file=sys.stderr,
                )
                return 1

    state["tasks"] = imported
    state["next_id"] = max(ids, default=0) + 1
    save(state)
    print("imported %d tasks from %s" % (len(imported), path))
    return 0


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
def cmd_test(args):
    import tempfile

    tmpdir = tempfile.mkdtemp(prefix="tasks_test_")
    data_path = os.path.join(tmpdir, "tasks_test.json")
    csv_path = os.path.join(tmpdir, "tasks_test.csv")

    def fresh():
        return {"tasks": [], "next_id": 1}

    global DATA_FILE
    original_data_file = DATA_FILE
    DATA_FILE = data_path

    try:
        # --- dep validation on add ---
        state = fresh()
        assert cmd_add(state, ["task one"]) == 0
        assert cmd_add(state, ["task two", "--dep", "1"]) == 0
        # add referencing a non-existent dep must fail and not add.
        before = len(state["tasks"])
        assert cmd_add(state, ["bad", "--dep", "999"]) == 1
        assert len(state["tasks"]) == before

        # --- done blocking by open deps ---
        state = fresh()
        cmd_add(state, ["a"])                      # id 1
        cmd_add(state, ["b", "--dep", "1"])        # id 2 depends on 1
        assert cmd_done(state, ["2"]) == 1         # blocked by open 1
        assert find_task(state, 2)["status"] == "open"
        assert cmd_done(state, ["1"]) == 0         # 1 has no deps
        assert cmd_done(state, ["2"]) == 0         # now unblocked
        assert find_task(state, 2)["status"] == "done"

        # --- ready set ---
        state = fresh()
        cmd_add(state, ["low", "--priority", "1"])         # id 1, ready
        cmd_add(state, ["high", "--priority", "5"])        # id 2, ready
        cmd_add(state, ["blocked", "--dep", "1"])          # id 3, blocked
        ready = ready_tasks(state)
        ready_ids = [t["id"] for t in ready]
        assert ready_ids == [2, 1], ready_ids       # high prio first, then id
        assert 3 not in ready_ids

        # --- plan topological correctness ---
        state = fresh()
        cmd_add(state, ["a"])                       # 1
        cmd_add(state, ["b", "--dep", "1"])         # 2
        cmd_add(state, ["c", "--dep", "2"])         # 3
        cmd_add(state, ["d", "--dep", "1"])         # 4
        order, cycle = topo_open(state)
        assert cycle is None
        pos = {tid: i for i, tid in enumerate(order)}
        tmap = task_map(state)
        for t in state["tasks"]:
            for d in t["deps"]:
                assert pos[d] < pos[t["id"]], (order, t["id"], d)

        # --- cycle detection ---
        state = fresh()
        cmd_add(state, ["a"])                       # 1
        cmd_add(state, ["b", "--dep", "1"])         # 2
        # Manually create a cycle 1 -> 2 -> 1.
        find_task(state, 1)["deps"].append(2)
        order, cycle = topo_open(state)
        assert order is None
        assert cycle == [1, 2], cycle
        assert cmd_plan(state, []) == 1

        # --- rm with dependents (and --force) ---
        state = fresh()
        cmd_add(state, ["base"])                    # 1
        cmd_add(state, ["dependent", "--dep", "1"]) # 2
        assert cmd_rm(state, ["1"]) == 1            # refused, has dependent
        assert find_task(state, 1) is not None
        assert cmd_rm(state, ["1", "--force"]) == 0
        assert find_task(state, 1) is None
        assert 1 not in find_task(state, 2)["deps"]  # edge removed

        # --- stats depth ---
        state = fresh()
        cmd_add(state, ["a"])                       # 1
        cmd_add(state, ["b", "--dep", "1"])         # 2
        cmd_add(state, ["c", "--dep", "2"])         # 3 -> longest chain 1,2,3
        cmd_add(state, ["standalone"])              # 4
        assert longest_chain_depth(state) == 3, longest_chain_depth(state)

        # --- export/import round-trip ---
        state = fresh()
        cmd_add(state, ["a", "--priority", "4"])            # 1
        cmd_add(state, ["b", "--dep", "1", "--priority", "2"])  # 2
        cmd_add(state, ["c", "--dep", "1", "--dep", "2"])  # 3
        cmd_done(state, ["1"])
        assert cmd_export(state, [csv_path]) == 0
        state2 = fresh()
        assert cmd_import(state2, [csv_path]) == 0
        assert len(state2["tasks"]) == 3
        t1 = find_task(state2, 1)
        t3 = find_task(state2, 3)
        assert t1["status"] == "done"
        assert t1["priority"] == 4
        assert t3["deps"] == [1, 2], t3["deps"]

        # --- import with dangling dep must fail ---
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "title", "priority", "status", "deps"])
            writer.writerow([1, "x", 3, "open", "42"])  # 42 doesn't exist
        state3 = fresh()
        assert cmd_import(state3, [csv_path]) == 1

        print("all tests passed")
        return 0
    finally:
        DATA_FILE = original_data_file
        try:
            if os.path.exists(data_path):
                os.remove(data_path)
            if os.path.exists(csv_path):
                os.remove(csv_path)
            os.rmdir(tmpdir)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "dep": cmd_dep,
    "done": cmd_done,
    "rm": cmd_rm,
    "ready": cmd_ready,
    "plan": cmd_plan,
    "block": cmd_block,
    "graph": cmd_graph,
    "search": cmd_search,
    "stats": cmd_stats,
    "export": cmd_export,
    "import": cmd_import,
}


def main(argv):
    if len(argv) < 1:
        return usage_error("no command given")
    command = argv[0]
    args = argv[1:]

    if command == "test":
        return cmd_test(args)

    if command not in COMMANDS:
        return usage_error("unknown command: %s" % command)

    state = load()
    return COMMANDS[command](state, args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
