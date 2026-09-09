#!/usr/bin/env python3
"""tasks.py - a dependency-aware task manager (single file, Python stdlib only).

Invoke as:  python tasks.py <command> [args]

Tasks form a dependency graph.  Each task has:
    id       - integer, incrementing, never reused
    title    - str
    priority - int 1-5 (default 3, 5 = highest)
    status   - "open" or "done"
    deps     - list of task ids it depends on
    created  - ISO timestamp of when the task was created

State is persisted to tasks.json in the current directory.  A missing, empty,
or corrupt tasks.json simply starts with no tasks (never crashes).

Commands:
    add "title" [--priority N] [--dep ID]...
    list [--status open|done|all]
    dep <id> --on <other_id>
    done <id>
    rm <id> [--force]
    ready
    plan
    block <id>
    graph
    search <term>
    stats
    export <file.csv>
    import <file.csv>
    test
"""

import contextlib
import csv
import datetime
import heapq
import io
import json
import os
import shutil
import sys
import tempfile

USAGE = """usage: python tasks.py <command> [args]

commands:
  add "title" [--priority N] [--dep ID]...    add a task
  list [--status open|done|all]               list tasks (default: all)
  dep <id> --on <other_id>                    task <id> depends on <other_id>
  done <id>                                   mark a task done
  rm <id> [--force]                           delete a task
  ready                                       list actionable (ready) tasks
  plan                                        print a valid execution order of open tasks
  block <id>                                  show which open deps block a task
  graph                                       print tasks with their direct dependents
  search <term>                               case-insensitive title search
  stats                                       print task statistics
  export <file.csv>                           export all tasks to CSV
  import <file.csv>                           replace tasks from a CSV file
  test                                        run the self test (temporary data file)"""


class UsageError(Exception):
    """Raised for missing/invalid command arguments (prints usage)."""


# --------------------------------------------------------------------------
# persistence
# --------------------------------------------------------------------------

#: Name of the data file, resolved against the current directory unless the
#: self-test overrides it with an absolute path into a temporary directory.
DATA_FILE = "tasks.json"


def data_path():
    if os.path.isabs(DATA_FILE):
        return DATA_FILE
    return os.path.join(os.getcwd(), DATA_FILE)


def fresh_state():
    return {"next_id": 1, "tasks": []}


def _parse_state(data):
    """Validate a decoded JSON payload.

    Returns (tasks, next_id) on success or None when the payload is corrupt.
    """
    if not isinstance(data, dict):
        return None
    raw_tasks = data.get("tasks")
    if not isinstance(raw_tasks, list):
        return None
    tasks = []
    seen = set()
    for raw in raw_tasks:
        if not isinstance(raw, dict):
            return None
        try:
            tid = int(raw.get("id"))
            title = raw.get("title")
            priority = int(raw.get("priority"))
            status = str(raw.get("status")).strip().lower()
            raw_deps = raw.get("deps")
        except (TypeError, ValueError):
            return None
        if not isinstance(title, str):
            return None
        if not isinstance(raw_deps, list):
            return None
        try:
            deps = [int(d) for d in raw_deps]
        except (TypeError, ValueError):
            return None
        if tid <= 0 or tid in seen:
            return None
        if priority < 1 or priority > 5:
            return None
        if status not in ("open", "done"):
            return None
        deps = sorted({d for d in deps if d > 0})
        seen.add(tid)
        created = raw.get("created")
        tasks.append({
            "id": tid,
            "title": title,
            "priority": priority,
            "status": status,
            "deps": deps,
            "created": created if isinstance(created, str) else "",
        })
    tasks.sort(key=lambda t: t["id"])
    # every stored dependency must reference a task that exists
    if any(dep not in seen for task in tasks for dep in task["deps"]):
        return None
    try:
        nid = int(data.get("next_id", 0))
    except (TypeError, ValueError):
        return None
    max_id = tasks[-1]["id"] if tasks else 0
    if nid <= max_id:
        nid = max_id + 1
    if nid < 1:
        nid = 1
    return tasks, nid


def load():
    """Load state from tasks.json; never crashes, never raises."""
    try:
        with open(data_path(), "r", encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError):
        return fresh_state()
    if not text.strip():
        return fresh_state()
    try:
        payload = json.loads(text)
    except ValueError:
        return fresh_state()
    parsed = _parse_state(payload)
    if parsed is None:
        return fresh_state()
    tasks, next_id = parsed
    return {"next_id": next_id, "tasks": tasks}


def save(state):
    """Persist state to tasks.json (atomically via a temp file)."""
    path = data_path()
    tasks = sorted(state["tasks"], key=lambda t: t["id"])
    payload = {"next_id": int(state["next_id"]), "tasks": tasks}
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        raise RuntimeError("cannot write %s: %s" % (path, exc)) from exc


def _commit(state):
    """Attempt to persist; on failure print an error and report failure."""
    try:
        save(state)
    except RuntimeError as exc:
        print("error: %s" % exc)
        return False
    return True


def task_index(state):
    return {t["id"]: t for t in state["tasks"]}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# output helpers
# --------------------------------------------------------------------------


def fmt_task(task):
    """Human readable line: id [status] p<priority> title [deps: ...]."""
    line = "%d [%s] p%d %s" % (task["id"], task["status"], task["priority"], task["title"])
    deps = task.get("deps") or []
    if deps:
        line += " deps: " + ", ".join(str(d) for d in deps)
    return line


def _parse_int(raw, what):
    try:
        return int(raw)
    except ValueError:
        raise UsageError("%s must be an integer, got %r" % (what, raw))


# --------------------------------------------------------------------------
# graph algorithms
# --------------------------------------------------------------------------


def _find_cycle(depmap):
    """Return a list of ids forming one directed cycle in depmap, or None.

    depmap maps a node id to its sorted dependency ids; the edges are only
    followed inside the given node set, so traversal never escapes it.
    """
    if not depmap:
        return None
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, len(depmap) * 4 + 100))
    try:
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in depmap}
        stack = []

        def visit(node):
            color[node] = GRAY
            stack.append(node)
            for nxt in depmap.get(node, ()):
                if nxt not in color:
                    continue
                if color[nxt] == GRAY:
                    return stack[stack.index(nxt):]
                if color[nxt] == WHITE:
                    result = visit(nxt)
                    if result is not None:
                        return result
            stack.pop()
            color[node] = BLACK
            return None

        for node in sorted(depmap):
            if color[node] == WHITE:
                result = visit(node)
                if result is not None:
                    return result
        return None
    finally:
        sys.setrecursionlimit(old_limit)


def compute_depth(tasks):
    """Length (in tasks) of the longest dependency chain in the whole graph.

    A task chain t1 -> t2 -> ... means each task depends on the next.  Empty
    graph has depth 0; a single task has depth 1.  Exact on DAGs; cycle-safe
    (a chain never loops back through a node already on the same path).
    """
    if not tasks:
        return 0
    byid = {t["id"]: t for t in tasks}
    state = {}
    memo = {}
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, len(tasks) * 4 + 100))
    try:
        def depth_of(node_id):
            st = state.get(node_id, 0)
            if st == 1:      # would extend a chain through an ancestor: cycle
                return 0
            if st == 2:
                return memo[node_id]
            state[node_id] = 1
            best = 1
            for dep in byid[node_id].get("deps", ()):
                if dep not in byid:
                    continue
                cand = 1 + depth_of(dep)
                if cand > best:
                    best = cand
            state[node_id] = 2
            memo[node_id] = best
            return best

        return max(depth_of(t["id"]) for t in tasks)
    finally:
        sys.setrecursionlimit(old_limit)


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def do_add(args):
    """add "title" [--priority N] [--dep ID]..."""
    if not args:
        raise UsageError("add requires a title")
    if args[0].startswith("--"):
        raise UsageError("add requires a title as the first argument")
    title = args[0]
    priority = 3
    dep_ids = []
    i = 1
    while i < len(args):
        tok = args[i]
        if tok == "--priority":
            if i + 1 >= len(args):
                raise UsageError("--priority requires an integer value between 1 and 5")
            raw = args[i + 1]
            i += 2
            priority = _parse_int(raw, "--priority value")
            if priority < 1 or priority > 5:
                raise UsageError("priority must be an integer between 1 and 5")
        elif tok == "--dep":
            if i + 1 >= len(args):
                raise UsageError("--dep requires a task id")
            raw = args[i + 1]
            i += 2
            dep_ids.append(_parse_int(raw, "--dep value"))
        else:
            raise UsageError("unexpected argument: %s" % tok)

    state = load()
    byid = task_index(state)
    unique_deps = sorted(set(dep_ids))
    for dep in unique_deps:
        if dep not in byid:
            print("error: dependency task %s does not exist" % dep)
            return 1

    task = {
        "id": state["next_id"],
        "title": title,
        "priority": priority,
        "status": "open",
        "deps": unique_deps,
        "created": _now(),
    }
    state["next_id"] += 1
    state["tasks"].append(task)
    if not _commit(state):
        return 1
    return 0


def do_list(args):
    """list [--status open|done|all]"""
    status_filter = "all"
    if args:
        if len(args) == 2 and args[0] == "--status":
            if args[1] not in ("open", "done", "all"):
                raise UsageError("--status must be one of: open, done, all")
            status_filter = args[1]
        else:
            raise UsageError("usage: list [--status open|done|all]")
    state = load()
    for task in sorted(state["tasks"], key=lambda t: t["id"]):
        if status_filter == "all" or task["status"] == status_filter:
            print(fmt_task(task))
    return 0


def do_dep(args):
    """dep <id> --on <other_id>"""
    if len(args) != 3 or args[1] != "--on":
        raise UsageError("usage: dep <id> --on <other_id>")
    tid = _parse_int(args[0], "id")
    other = _parse_int(args[2], "other_id")
    state = load()
    byid = task_index(state)
    if tid not in byid:
        print("error: task %s does not exist" % tid)
        return 1
    if other not in byid:
        print("error: task %s does not exist" % other)
        return 1
    if tid == other:
        print("error: task %s cannot depend on itself" % tid)
        return 1
    task = byid[tid]
    if other not in task["deps"]:
        task["deps"] = sorted(task["deps"] + [other])
        if not _commit(state):
            return 1
    return 0


def do_done(args):
    """done <id>"""
    if len(args) != 1:
        raise UsageError("usage: done <id>")
    tid = _parse_int(args[0], "id")
    state = load()
    byid = task_index(state)
    if tid not in byid:
        print("error: task %s does not exist" % tid)
        return 1
    task = byid[tid]
    for dep in task["deps"]:
        dep_task = byid.get(dep)
        if dep_task is not None and dep_task["status"] == "open":
            print("cannot complete: blocked by open dependency %s" % dep)
            return 1
    task["status"] = "done"
    if not _commit(state):
        return 1
    return 0


def do_rm(args):
    """rm <id> [--force]"""
    if len(args) not in (1, 2) or (len(args) == 2 and args[1] != "--force"):
        raise UsageError("usage: rm <id> [--force]")
    tid = _parse_int(args[0], "id")
    force = len(args) == 2 and args[1] == "--force"
    state = load()
    byid = task_index(state)
    if tid not in byid:
        print("error: task %s does not exist" % tid)
        return 1
    dependents = sorted(
        t["id"] for t in state["tasks"] if t["id"] != tid and tid in t["deps"]
    )
    if dependents and not force:
        print(
            "error: task %s cannot be removed: it is a dependency of %s (use --force)"
            % (tid, ", ".join(map(str, dependents)))
        )
        return 1
    state["tasks"] = [t for t in state["tasks"] if t["id"] != tid]
    for task in state["tasks"]:
        task["deps"] = [d for d in task["deps"] if d != tid]
    if not _commit(state):
        return 1
    return 0


def _is_ready(task, byid):
    for dep in task["deps"]:
        dep_task = byid.get(dep)
        if dep_task is not None and dep_task["status"] != "done":
            return False
    return True


def do_ready(args):
    """ready - actionable open tasks, priority desc then id asc."""
    if args:
        raise UsageError("ready takes no arguments")
    state = load()
    byid = task_index(state)
    result = [
        t for t in state["tasks"]
        if t["status"] == "open" and _is_ready(t, byid)
    ]
    result.sort(key=lambda t: (-t["priority"], t["id"]))
    for task in result:
        print(fmt_task(task))
    return 0


def do_plan(args):
    """plan - topo order of open tasks (deps first); detects cycles."""
    if args:
        raise UsageError("plan takes no arguments")
    state = load()
    byid = task_index(state)
    open_tasks = [t for t in state["tasks"] if t["status"] == "open"]

    # depmap: open task -> sorted list of its open dependencies
    depmap = {}
    for task in open_tasks:
        deps = []
        for dep in task["deps"]:
            dep_task = byid.get(dep)
            if dep_task is not None and dep_task["status"] == "open":
                deps.append(dep)
        depmap[task["id"]] = sorted(deps)

    depend = {node: [] for node in depmap}
    for node, deps in depmap.items():
        for dep in deps:
            depend[dep].append(node)

    indeg = {node: len(deps) for node, deps in depmap.items()}
    heap = []
    for task in open_tasks:
        if indeg[task["id"]] == 0:
            heapq.heappush(heap, (-task["priority"], task["id"]))

    order = []
    while heap:
        _neg_priority, node = heapq.heappop(heap)
        order.append(node)
        for follower in depend.get(node, ()):
            indeg[follower] -= 1
            if indeg[follower] == 0:
                heapq.heappush(heap, (-byid[follower]["priority"], follower))

    if len(order) != len(depmap):
        remaining = [n for n in depmap if n not in set(order)]
        rem_set = set(remaining)
        rem_map = {n: [d for d in depmap[n] if d in rem_set] for n in remaining}
        cycle = _find_cycle(rem_map)
        if cycle is None:
            cycle = sorted(remaining)
        print("cycle detected: " + ", ".join(str(x) for x in cycle))
        return 1

    for node in order:
        print(fmt_task(byid[node]))
    return 0


def do_block(args):
    """block <id> - list the task's dependencies that are still open."""
    if len(args) != 1:
        raise UsageError("usage: block <id>")
    tid = _parse_int(args[0], "id")
    state = load()
    byid = task_index(state)
    if tid not in byid:
        print("error: task %s does not exist" % tid)
        return 1
    task = byid[tid]
    for dep in task["deps"]:
        dep_task = byid.get(dep)
        if dep_task is not None and dep_task["status"] == "open":
            print(fmt_task(dep_task))
    return 0


def do_graph(args):
    """graph - print each task with its direct dependents."""
    if args:
        raise UsageError("graph takes no arguments")
    state = load()
    dependents = {t["id"]: [] for t in state["tasks"]}
    for task in state["tasks"]:
        for dep in task["deps"]:
            if dep in dependents:
                dependents[dep].append(task["id"])
    for task in sorted(state["tasks"], key=lambda t: t["id"]):
        print(fmt_task(task))
        who = sorted(dependents.get(task["id"], []))
        if who:
            print("    depended on by: " + ", ".join(map(str, who)))
        else:
            print("    depended on by: none")
    return 0


def do_search(args):
    """search <term> - case-insensitive substring search on titles."""
    if not args:
        raise UsageError("search requires a term")
    term = " ".join(args).lower()
    state = load()
    for task in sorted(state["tasks"], key=lambda t: t["id"]):
        if term in task["title"].lower():
            print(fmt_task(task))
    return 0


def do_stats(args):
    """stats - total/open/done/ready/blocked counts and graph depth."""
    if args:
        raise UsageError("stats takes no arguments")
    state = load()
    tasks = state["tasks"]
    byid = task_index(state)
    total = len(tasks)
    open_count = sum(1 for t in tasks if t["status"] == "open")
    done_count = total - open_count
    ready_count = sum(
        1 for t in tasks if t["status"] == "open" and _is_ready(t, byid)
    )
    blocked_count = open_count - ready_count
    print("total: %d" % total)
    print("open: %d" % open_count)
    print("done: %d" % done_count)
    print("ready: %d" % ready_count)
    print("blocked: %d" % blocked_count)
    print("depth: %d" % compute_depth(tasks))
    return 0


def do_export(args):
    """export <file.csv> - write all tasks as CSV (id,title,priority,status,deps)."""
    if len(args) != 1:
        raise UsageError("usage: export <file.csv>")
    path = args[0]
    state = load()
    try:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "title", "priority", "status", "deps"])
            for task in sorted(state["tasks"], key=lambda t: t["id"]):
                writer.writerow([
                    task["id"],
                    task["title"],
                    task["priority"],
                    task["status"],
                    ";".join(map(str, task["deps"])),
                ])
    except OSError as exc:
        print("error: cannot export to %s: %s" % (path, exc))
        return 1
    return 0


def do_import(args):
    """import <file.csv> - replace all tasks with those loaded from the CSV."""
    if len(args) != 1:
        raise UsageError("usage: import <file.csv>")
    path = args[0]
    try:
        with open(path, "r", newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
    except (OSError, csv.Error, UnicodeDecodeError) as exc:
        print("error: cannot read %s: %s" % (path, exc))
        return 1

    data_rows = rows
    # optional header row (id,title,priority,status,deps)
    if rows and rows[0] and str(rows[0][0]).strip().lower() == "id":
        data_rows = rows[1:]

    new_tasks = []
    seen = set()
    try:
        for row in data_rows:
            if not row or all(str(cell).strip() == "" for cell in row):
                continue
            if len(row) != 5:
                raise ValueError("expected 5 columns, got %d: %r" % (len(row), row))
            try:
                tid = int(str(row[0]).strip())
                priority = int(str(row[2]).strip())
            except ValueError:
                raise ValueError("invalid numeric field in row %r" % (row,))
            title = str(row[1])
            status = str(row[3]).strip().lower()
            deps = []
            for part in str(row[4]).split(";"):
                piece = part.strip()
                if piece:
                    try:
                        deps.append(int(piece))
                    except ValueError:
                        raise ValueError("invalid dependency %r in row %r" % (piece, row))
            if tid <= 0:
                raise ValueError("invalid task id %s in row %r" % (tid, row))
            if tid in seen:
                raise ValueError("duplicate task id %s" % tid)
            if priority < 1 or priority > 5:
                raise ValueError("priority %s out of range 1-5 in row %r" % (priority, row))
            if status not in ("open", "done"):
                raise ValueError("invalid status %r in row %r" % (status, row))
            seen.add(tid)
            new_tasks.append({
                "id": tid,
                "title": title,
                "priority": priority,
                "status": status,
                "deps": sorted(set(deps)),
                "created": _now(),
            })
        missing = []
        for task in new_tasks:
            for dep in task["deps"]:
                if dep not in seen:
                    missing.append(dep)
        if missing:
            raise ValueError(
                "dependency task %s does not exist" % sorted(set(missing))[0]
            )
    except ValueError as exc:
        print("error: import failed: %s" % exc)
        return 1

    new_tasks.sort(key=lambda t: t["id"])
    max_id = new_tasks[-1]["id"] if new_tasks else 0
    state = {"next_id": max_id + 1, "tasks": new_tasks}
    if not _commit(state):
        return 1
    return 0


# --------------------------------------------------------------------------
# self test
# --------------------------------------------------------------------------

def do_test(args):
    """test - run the self test suite against a temporary data file."""
    if args:
        raise UsageError("test takes no arguments")
    global DATA_FILE
    old_file = DATA_FILE
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix="tasks_test_")
        DATA_FILE = os.path.join(tmpdir, "tasks.json")

        def reset():
            try:
                os.remove(data_path())
            except OSError:
                pass

        def current():
            return load()

        def run(argv):
            buf = io.StringIO()
            code = 1
            try:
                with contextlib.redirect_stdout(buf):
                    code = dispatch(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
            return code, buf.getvalue()

        def ids_of(out):
            return [int(line.split(None, 1)[0]) for line in out.splitlines() if line.strip()]

        def expect(cond, msg):
            if not cond:
                raise AssertionError("TEST FAILED: %s" % msg)

        # --- unknown command / argument validation -------------------------
        code, out = run([])
        expect(code == 1 and "usage" in out.lower(), "no arguments must print usage, exit 1")
        code, out = run(["frobnicate"])
        expect(code == 1 and "usage" in out.lower(), "unknown command prints usage, exit 1")
        code, out = run(["list", "--status", "bogus"])
        expect(code == 1, "invalid --status value must exit 1")

        # --- add: dependency validation and priority checks -----------------
        reset()
        code, out = run(["add", "standalone"])
        expect(code == 0, "plain add should succeed")
        code, out = run(["add", "broken", "--dep", "999"])
        expect(code == 1, "add with a nonexistent dep must exit 1")
        expect("999" in out, "add error message names the missing dep")
        expect(len(current()["tasks"]) == 1, "failed add must not insert the task")
        code, out = run(["add", "high", "--priority", "5"])
        expect(code == 0, "priority 5 accepted")
        code, out = run(["add", "badp", "--priority", "9"])
        expect(code == 1, "out-of-range priority rejected")
        code, out = run(["add", "badp2", "--priority", "x"])
        expect(code == 1, "non-integer priority rejected")

        # --- dep command validation ----------------------------------------
        reset()
        run(["add", "a"])                       # id 1
        run(["add", "b"])                       # id 2
        code, out = run(["dep", "1", "--on", "1"])
        expect(code == 1, "self dependency rejected")
        code, out = run(["dep", "1", "--on", "99"])
        expect(code == 1, "edge to nonexistent task rejected")
        code, out = run(["dep", "99", "--on", "1"])
        expect(code == 1, "edge from nonexistent task rejected")
        code, out = run(["dep", "1", "--on", "2"])
        expect(code == 0, "valid dependency edge added")
        a = next(t for t in current()["tasks"] if t["id"] == 1)
        expect(a["deps"] == [2], "dependency stored")
        code, out = run(["dep", "1", "--on", "2"])
        expect(code == 0 and a["deps"] == [2], "duplicate edge is idempotent")

        # --- done: blocked by open dependencies -----------------------------
        reset()
        run(["add", "root"])                       # id 1
        run(["add", "leaf", "--dep", "1"])         # id 2
        code, out = run(["done", "2"])
        expect(code == 1, "done must fail while a dep is open")
        expect("cannot complete: blocked by open dependency 1" in out,
               "done prints the blocking message")
        code, out = run(["done", "1"])
        expect(code == 0, "done on root succeeds")
        code, out = run(["done", "2"])
        expect(code == 0, "done on leaf succeeds after dep done")
        expect(all(t["status"] == "done" for t in current()["tasks"]),
               "both tasks are done")
        code, out = run(["done", "42"])
        expect(code == 1, "done on a nonexistent task exits 1")

        # --- ready set, blocked count, status filter ------------------------
        reset()
        run(["add", "hi", "--priority", "5"])      # id 1 (ready)
        run(["add", "mid", "--dep", "1"])          # id 2 (blocked)
        run(["add", "lo", "--priority", "1"])      # id 3 (ready)
        code, out = run(["ready"])
        expect(ids_of(out) == [1, 3],
               "ready = open tasks with all deps done, priority desc then id asc")
        code, out = run(["stats"])
        expect("total: 3" in out, "stats total")
        expect("open: 3" in out, "stats open")
        expect("done: 0" in out, "stats done")
        expect("ready: 2" in out, "stats ready")
        expect("blocked: 1" in out, "stats blocked")
        run(["done", "1"])
        code, out = run(["ready"])
        expect(ids_of(out) == [2, 3], "task 2 becomes ready once dep 1 is done")
        code, out = run(["list", "--status", "done"])
        expect(ids_of(out) == [1], "list --status done filters")
        code, out = run(["block", "2"])
        expect(code == 0 and out.strip() == "", "block prints nothing when no open deps")

        # --- plan: topological order with priority/id tie breaks ------------
        reset()
        run(["add", "a"])                                     # id 1
        run(["add", "b", "--dep", "1"])                       # id 2
        run(["add", "c", "--dep", "2"])                       # id 3
        run(["add", "d", "--dep", "1", "--priority", "5"])    # id 4
        code, out = run(["plan"])
        expect(code == 0, "plan succeeds on a DAG")
        plan_ids = ids_of(out)
        expect(plan_ids == [1, 4, 2, 3],
               "plan respects deps and breaks ties by priority then id: %r" % (plan_ids,))
        st = current()
        pos = {tid: i for i, tid in enumerate(plan_ids)}
        for task in st["tasks"]:
            for dep in task["deps"]:
                if task["status"] == "open" and dep in pos:
                    expect(pos[dep] < pos[task["id"]],
                           "every task must appear after all of its deps")

        # --- plan: cycle detection ------------------------------------------
        reset()
        run(["add", "x"])                # id 1
        run(["add", "y"])                # id 2
        run(["dep", "1", "--on", "2"])   # 1 depends on 2
        run(["dep", "2", "--on", "1"])   # 2 depends on 1
        code, out = run(["plan"])
        expect(code == 1, "plan must exit 1 on a cycle")
        expect(out.strip() == "cycle detected: 1, 2",
               "cycle message lists the cycle ids, got %r" % (out.strip(),))

        # --- rm: dependent refusal, --force, id never reused ---------------
        reset()
        run(["add", "base"])                        # id 1
        run(["add", "child", "--dep", "1"])         # id 2
        run(["add", "other"])                       # id 3
        code, out = run(["rm", "1"])
        expect(code == 1, "rm refused while another task depends on it")
        code, out = run(["rm", "1", "--force"])
        expect(code == 0, "rm --force succeeds")
        st = current()
        expect(sorted(t["id"] for t in st["tasks"]) == [2, 3], "base task deleted")
        child = next(t for t in st["tasks"] if t["id"] == 2)
        expect(child["deps"] == [], "--force removes the id from dependents' deps")
        code, out = run(["add", "new"])
        expect(code == 0 and any(t["id"] == 4 for t in current()["tasks"]),
               "task ids are never reused")
        code, out = run(["rm", "3"])
        expect(code == 0, "plain rm deletes a task nobody depends on")
        expect(sorted(t["id"] for t in current()["tasks"]) == [2, 4],
               "plain rm removed the task")

        # --- stats depth ----------------------------------------------------
        reset()
        run(["add", "a"])                    # id 1
        run(["add", "b", "--dep", "1"])      # id 2
        run(["add", "c", "--dep", "2"])      # id 3
        code, out = run(["stats"])
        expect("depth: 3" in out, "depth of a 3-task chain is 3")
        reset()
        code, out = run(["stats"])
        expect("total: 0" in out and "depth: 0" in out, "empty graph depth is 0")

        # --- search ---------------------------------------------------------
        reset()
        run(["add", "Hello World"])
        run(["add", "Goodbye"])
        run(["add", "hello again"])
        code, out = run(["search", "hello"])
        expect(ids_of(out) == [1, 3], "search matches case-insensitively")
        code, out = run(["search", "HELLO"])
        expect(ids_of(out) == [1, 3], "search is case-insensitive both ways")

        # --- export / import round-trip -------------------------------------
        reset()
        run(["add", "alpha"])
        run(["add", 'beta, "quoted"; title', "--dep", "1", "--priority", "2"])
        run(["add", "gamma", "--dep", "1", "--dep", "2"])
        csv_path = os.path.join(tmpdir, "out.csv")
        code, out = run(["export", csv_path])
        expect(code == 0, "export succeeds")
        snapshot = current()
        reset()
        code, out = run(["import", csv_path])
        expect(code == 0, "import succeeds")

        def norm(task):
            return (task["id"], task["title"], task["priority"],
                    task["status"], tuple(task["deps"]))

        st = current()
        expect(sorted(norm(t) for t in st["tasks"]) ==
               sorted(norm(t) for t in snapshot["tasks"]),
               "export/import round trip preserves tasks")
        run(["add", "delta"])
        expect(any(t["id"] == 4 for t in current()["tasks"]),
               "ids continue past the imported max id")

        # --- import validation ----------------------------------------------
        bad_csv = os.path.join(tmpdir, "bad.csv")
        with open(bad_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "title", "priority", "status", "deps"])
            writer.writerow([1, "orphan", "3", "open", "9"])
        before = current()
        code, out = run(["import", bad_csv])
        expect(code == 1, "import with an unknown dep id exits 1")
        expect("9" in out, "import error names the missing dep")
        expect(len(current()["tasks"]) == len(before["tasks"]),
               "failed import leaves the current tasks untouched")

        # import replaces the whole task set
        single_csv = os.path.join(tmpdir, "single.csv")
        with open(single_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "title", "priority", "status", "deps"])
            writer.writerow([77, "loner", "4", "open", ""])
        code, out = run(["import", single_csv])
        expect(code == 0, "import of a valid csv succeeds")
        st = current()
        expect([t["id"] for t in st["tasks"]] == [77] and st["tasks"][0]["priority"] == 4,
               "import replaced all previous tasks")
        run(["add", "after-import"])
        expect(any(t["id"] == 78 for t in current()["tasks"]),
               "next id continues past imported max")

        # --- graph ----------------------------------------------------------
        reset()
        run(["add", "base"])                # id 1
        run(["add", "child", "--dep", "1"]) # id 2
        code, out = run(["graph"])
        expect(code == 0, "graph runs")
        expect("depended on by: 2" in out, "graph shows the direct dependents")
        expect("depended on by: none" in out, "graph shows tasks with no dependents")

        print("all tests passed")
        return 0
    finally:
        DATA_FILE = old_file
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


# --------------------------------------------------------------------------
# dispatch
# --------------------------------------------------------------------------

COMMANDS = {
    "add": do_add,
    "list": do_list,
    "dep": do_dep,
    "done": do_done,
    "rm": do_rm,
    "ready": do_ready,
    "plan": do_plan,
    "block": do_block,
    "graph": do_graph,
    "search": do_search,
    "stats": do_stats,
    "export": do_export,
    "import": do_import,
    "test": do_test,
}


def dispatch(argv):
    """Run one command; returns the process exit code."""
    if not argv:
        print(USAGE)
        return 1
    cmd = argv[0]
    handler = COMMANDS.get(cmd)
    if handler is None:
        print("unknown command: %s" % cmd)
        print(USAGE)
        return 1
    try:
        return handler(argv[1:])
    except UsageError as exc:
        print("error: %s" % exc)
        print(USAGE)
        return 1


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    return dispatch(argv)


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(main())
