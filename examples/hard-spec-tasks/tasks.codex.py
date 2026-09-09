#!/usr/bin/env python3
"""A dependency-aware task manager using only the Python standard library.

Data lives in tasks.json in the current directory. Dependency depth counts
edges: an independent task has depth 0, and A -> B -> C has depth 2.
"""

import argparse
import csv
import heapq
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


CSV_COLUMNS = ["id", "title", "priority", "status", "deps"]


class TaskError(Exception):
    """An invalid task operation, reported without a traceback by the CLI."""


class CycleError(TaskError):
    def __init__(self, ids):
        self.ids = ids
        super().__init__("cycle detected: " + ", ".join(map(str, ids)))


def timestamp():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Task:
    id: int
    title: str
    priority: int
    status: str
    deps: list
    created: str


def validate_tasks(records):
    """Validate a complete snapshot before accepting any of its records."""
    if not isinstance(records, list):
        raise TaskError("tasks must be a list")
    tasks = {}
    for record in records:
        if not isinstance(record, dict):
            raise TaskError("invalid task record")
        task_id = record.get("id")
        if type(task_id) is not int or task_id < 1:
            raise TaskError("task ids must be positive integers")
        if task_id in tasks:
            raise TaskError(f"duplicate task id {task_id}")
        if not isinstance(record.get("title"), str):
            raise TaskError(f"invalid title for task {task_id}")
        priority = record.get("priority")
        if type(priority) is not int or not 1 <= priority <= 5:
            raise TaskError(f"invalid priority for task {task_id}")
        if record.get("status") not in ("open", "done"):
            raise TaskError(f"invalid status for task {task_id}")
        deps = record.get("deps")
        if not isinstance(deps, list) or any(
            type(dep) is not int or dep < 1 for dep in deps
        ):
            raise TaskError(f"invalid dependencies for task {task_id}")
        if not isinstance(record.get("created"), str) or not record["created"]:
            raise TaskError(f"invalid creation timestamp for task {task_id}")
        tasks[task_id] = Task(
            task_id, record["title"], priority, record["status"],
            list(dict.fromkeys(deps)), record["created"],
        )
    for task in tasks.values():
        for dep in task.deps:
            if dep not in tasks:
                raise TaskError(f"task {task.id}: dependency {dep} does not exist")
    return tasks


class TaskStore:
    def __init__(self, path="tasks.json"):
        self.path = Path(path)
        self.tasks = {}
        self.next_id = 1
        self.load()

    def load(self):
        # A malformed snapshot is ignored as a whole, including dangling edges.
        self.tasks = {}
        self.next_id = 1
        try:
            with self.path.open(encoding="utf-8-sig") as source:
                data = json.load(source)
            if not isinstance(data, dict):
                return
            tasks = validate_tasks(data.get("tasks"))
            next_id = data.get("next_id")
            if type(next_id) is not int or next_id <= max(tasks, default=0):
                return
        except (OSError, UnicodeError, ValueError, RecursionError, TaskError):
            return
        self.tasks = tasks
        self.next_id = next_id

    def save(self):
        data = {
            "next_id": self.next_id,
            "tasks": [asdict(task) for task in self.ordered()],
        }
        # Replace only after the full snapshot has been written successfully.
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent,
                prefix=self.path.name + ".", suffix=".tmp", delete=False,
            ) as target:
                temp_path = Path(target.name)
                json.dump(data, target, ensure_ascii=True, indent=2)
                target.write("\n")
                target.flush()
                os.fsync(target.fileno())
            os.replace(temp_path, self.path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def get(self, task_id):
        if task_id not in self.tasks:
            raise TaskError(f"task {task_id} does not exist")
        return self.tasks[task_id]

    def ordered(self, status="all"):
        return [
            task for _, task in sorted(self.tasks.items())
            if status == "all" or task.status == status
        ]

    # 1. Add only after every requested dependency has been validated.
    def add(self, title, priority=3, deps=()):
        if not isinstance(title, str):
            raise TaskError("title must be a string")
        if type(priority) is not int or not 1 <= priority <= 5:
            raise TaskError("priority must be between 1 and 5")
        deps = list(dict.fromkeys(deps))
        for dep in deps:
            self.get(dep)
        task = Task(self.next_id, title, priority, "open", deps, timestamp())
        self.tasks[task.id] = task
        self.next_id += 1
        return task

    # 2. Listing is provided by ordered() and print_tasks().

    # 3. Cycles are allowed here and diagnosed by graph operations.
    def depend(self, task_id, other_id):
        task = self.get(task_id)
        self.get(other_id)
        if task_id == other_id:
            raise TaskError("a task cannot depend on itself")
        if other_id not in task.deps:
            task.deps.append(other_id)

    # 4. Completion requires all direct dependencies to be done.
    def complete(self, task_id):
        task = self.get(task_id)
        for dep in task.deps:
            if self.tasks[dep].status == "open":
                raise TaskError(f"cannot complete: blocked by open dependency {dep}")
        task.status = "done"

    # 5. Forced deletion removes every incoming dependency edge.
    def remove(self, task_id, force=False):
        self.get(task_id)
        dependents = [
            task for task in self.tasks.values()
            if task.id != task_id and task_id in task.deps
        ]
        if dependents and not force:
            ids = ", ".join(str(task.id) for task in sorted(dependents, key=lambda t: t.id))
            raise TaskError(f"cannot remove: task {task_id} has dependents {ids}; use --force")
        for task in dependents:
            task.deps.remove(task_id)
        del self.tasks[task_id]

    # 6. Ready tasks are open tasks whose dependencies are all done.
    def ready(self):
        return sorted(
            (task for task in self.tasks.values()
             if task.status == "open" and not self.blockers(task.id)),
            key=lambda task: (-task.priority, task.id),
        )

    # 7. A heap applies the tie breakers to the currently available tasks.
    def plan(self):
        nodes = {task.id for task in self.tasks.values() if task.status == "open"}
        return [self.tasks[task_id] for task_id in self._topological(nodes)]

    def _topological(self, nodes):
        incoming = {task_id: 0 for task_id in nodes}
        dependents = {task_id: [] for task_id in nodes}
        for task_id in nodes:
            for dep in self.tasks[task_id].deps:
                if dep in nodes:
                    incoming[task_id] += 1
                    dependents[dep].append(task_id)
        available = [
            (-self.tasks[task_id].priority, task_id)
            for task_id in nodes if incoming[task_id] == 0
        ]
        heapq.heapify(available)
        result = []
        while available:
            _, task_id = heapq.heappop(available)
            result.append(task_id)
            for dependent in dependents[task_id]:
                incoming[dependent] -= 1
                if incoming[dependent] == 0:
                    heapq.heappush(available, (-self.tasks[dependent].priority, dependent))
        if len(result) != len(nodes):
            remaining = {task_id for task_id in nodes if incoming[task_id] > 0}
            raise CycleError(self._find_cycle(remaining))
        return result

    def _find_cycle(self, nodes):
        # Iterative DFS also handles chains longer than Python's recursion limit.
        visited = set()
        for start in sorted(nodes):
            if start in visited:
                continue
            path = [start]
            positions = {start: 0}
            visited.add(start)
            stack = [iter(sorted(dep for dep in self.tasks[start].deps if dep in nodes))]
            while stack:
                dep = next(stack[-1], None)
                if dep is None:
                    stack.pop()
                    positions.pop(path.pop())
                elif dep in positions:
                    return path[positions[dep]:]
                elif dep not in visited:
                    visited.add(dep)
                    positions[dep] = len(path)
                    path.append(dep)
                    stack.append(iter(sorted(d for d in self.tasks[dep].deps if d in nodes)))
        raise AssertionError("topological sort failed without a cycle")

    # 8. Blockers are direct dependencies that are still open.
    def blockers(self, task_id):
        return [self.tasks[dep] for dep in self.get(task_id).deps
                if self.tasks[dep].status == "open"]

    # 9. Reverse edges include both open and completed dependents.
    def graph(self):
        dependents = {task_id: [] for task_id in self.tasks}
        for task in self.ordered():
            for dep in task.deps:
                dependents[dep].append(task.id)
        return dependents

    # 10. casefold also supports case-insensitive Unicode title searches.
    def search(self, term):
        term = term.casefold()
        return [task for task in self.ordered() if term in task.title.casefold()]

    # 11. Depth includes done tasks and counts dependency edges, not tasks.
    def stats(self):
        depths = {}
        for task_id in self._topological(set(self.tasks)):
            depths[task_id] = max(
                (depths[dep] + 1 for dep in self.tasks[task_id].deps), default=0,
            )
        open_count = sum(task.status == "open" for task in self.tasks.values())
        ready_count = len(self.ready())
        return {
            "total": len(self.tasks),
            "open": open_count,
            "done": len(self.tasks) - open_count,
            "ready": ready_count,
            "blocked": open_count - ready_count,
            "depth": max(depths.values(), default=0),
        }

    # 12. csv handles quoted titles, embedded newlines, and empty deps.
    def export_csv(self, path):
        with Path(path).open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for task in self.ordered():
                writer.writerow({
                    "id": task.id, "title": task.title, "priority": task.priority,
                    "status": task.status, "deps": ";".join(map(str, task.deps)),
                })

    # 13. Import is a replacement, committed only after complete validation.
    def import_csv(self, path):
        records = []
        created = timestamp()  # The specified CSV format has no created column.
        with Path(path).open(newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source, strict=True)
            if (reader.fieldnames is None or len(reader.fieldnames) != len(CSV_COLUMNS)
                    or set(reader.fieldnames) != set(CSV_COLUMNS)):
                raise TaskError("CSV must have columns: " + ",".join(CSV_COLUMNS))
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise TaskError(f"invalid CSV row at line {reader.line_num}")
                try:
                    records.append({
                        "id": int(row["id"]),
                        "title": row["title"],
                        "priority": int(row["priority"]),
                        "status": row["status"].strip(),
                        "deps": [int(dep) for dep in row["deps"].split(";")]
                        if row["deps"].strip() else [],
                        "created": created,
                    })
                except ValueError as error:
                    raise TaskError(f"invalid integer in CSV at line {reader.line_num}") from error
        tasks = validate_tasks(records)
        self.tasks = tasks
        # Import may restore older IDs, but future additions never reuse them.
        self.next_id = max(self.next_id, max(tasks, default=0) + 1)


def format_task(task):
    marker = "x" if task.status == "done" else " "
    deps = ",".join(map(str, task.deps)) or "-"
    # Keep each listing entry on one line, even after importing multiline titles.
    title = task.title.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    return f"{task.id} [{marker}] priority={task.priority} {title} (deps: {deps})"


def print_tasks(tasks):
    for task in tasks:
        print(format_task(task))


# 15. argparse normally exits 2 on bad arguments; this CLI requires exit 1.
class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, f"error: {message}\n")


def positive_id(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("id must be a positive integer") from None
    if number < 1:
        raise argparse.ArgumentTypeError("id must be a positive integer")
    return number


def build_parser():
    parser = ArgumentParser(
        prog="tasks.py", description=__doc__, allow_abbrev=False,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, help_text):
        return commands.add_parser(name, help=help_text, allow_abbrev=False)

    add = command("add", "add a task")
    add.add_argument("title")
    add.add_argument("--priority", type=int, choices=range(1, 6), default=3)
    add.add_argument("--dep", type=positive_id, action="append", default=[])

    listing = command("list", "list tasks")
    listing.add_argument("--status", choices=("open", "done", "all"), default="all")

    dep = command("dep", "add a dependency")
    dep.add_argument("id", type=positive_id)
    dep.add_argument("--on", type=positive_id, required=True)

    done = command("done", "complete a task if its dependencies are done")
    done.add_argument("id", type=positive_id)

    remove = command("rm", "delete a task")
    remove.add_argument("id", type=positive_id)
    remove.add_argument("--force", action="store_true")

    command("ready", "list actionable tasks in priority order")
    command("plan", "list all open tasks in dependency order")

    block = command("block", "list a task's open dependencies")
    block.add_argument("id", type=positive_id)

    command("graph", "list tasks and their direct dependents")

    search = command("search", "find tasks by title, ignoring case")
    search.add_argument("term")

    command("stats", "show counts and dependency depth (edges); cycles are errors")

    export = command("export", "export tasks as CSV")
    export.add_argument("file")

    import_command = command("import", "replace tasks from a validated CSV")
    import_command.add_argument("file")

    command("test", "run isolated self-tests using temporary files")
    return parser


# 16. Exercise the command handlers with a fresh load on every invocation.
def run_self_tests():
    import io
    from contextlib import redirect_stderr, redirect_stdout

    with tempfile.TemporaryDirectory(prefix="tasks-self-test-") as directory:
        root = Path(directory)
        data_path = root / "tasks.json"

        def cli(*args, expected=0, path=data_path):
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                try:
                    code = main(list(args), data_path=path)
                except SystemExit as error:
                    code = error.code
            assert code == expected, (args, code, output.getvalue(), errors.getvalue())
            return output.getvalue(), errors.getvalue()

        def ids(output):
            return [int(line.split()[0]) for line in output.splitlines()]

        def rejected(*args):
            before = data_path.read_bytes()
            output, errors = cli(*args, expected=1)
            assert data_path.read_bytes() == before, "failed command changed data"
            return output, errors

        # Dependency validation must not create a file, task, or ID gap.
        _, error = cli("add", "invalid", "--dep", "999", expected=1)
        assert "999" in error and not data_path.exists()
        cli("add", "Design", "--priority", "4")
        title = 'Build, "quoted"\nsecond line \u00e9'
        cli("add", title, "--priority", "5", "--dep", "1", "--dep", "1")
        cli("add", "Smoke test")
        cli("add", "Documentation")
        cli("add", "Release", "--priority", "5", "--dep", "2", "--dep", "3")
        rejected("add", "invalid", "--dep", "1", "--dep", "999")
        store = TaskStore(data_path)
        assert set(store.tasks) == {1, 2, 3, 4, 5} and store.next_id == 6
        assert store.get(2).deps == [1]
        assert store.get(3).priority == 3
        assert all(datetime.fromisoformat(task.created).tzinfo for task in store.ordered())

        # List filters, direct dependencies, blockers, graph, and search.
        output, _ = cli("list")
        assert "priority=4 Design" in output and "deps: 2,3" in output
        assert cli("list", "--status", "done")[0] == ""
        rejected("dep", "1", "--on", "1")
        rejected("dep", "1", "--on", "999")
        rejected("dep", "999", "--on", "1")
        cli("dep", "2", "--on", "1")
        assert TaskStore(data_path).get(2).deps == [1]
        assert ids(cli("block", "5")[0]) == [2, 3]
        assert ids(cli("search", "dEsIgN")[0]) == [1]
        graph, _ = cli("graph")
        assert "dependents: 2" in graph.splitlines()[0]
        assert TaskStore(data_path).graph() == {1: [2], 2: [5], 3: [5], 4: [], 5: []}

        # Priorities are applied whenever a task becomes available.
        assert ids(cli("ready")[0]) == [1, 3, 4]
        order = [task.id for task in store.plan()]
        assert order == [1, 2, 3, 5, 4]
        positions = {task_id: index for index, task_id in enumerate(order)}
        assert len(positions) == len(store.tasks)
        for task in store.ordered():
            assert all(positions[dep] < positions[task.id] for dep in task.deps)

        # Completion checks every dependency, including after partial progress.
        _, error = rejected("done", "2")
        assert "cannot complete: blocked by open dependency 1" in error
        cli("done", "1")
        assert [task.id for task in TaskStore(data_path).plan()] == [2, 3, 5, 4]
        assert ids(cli("ready")[0]) == [2, 3, 4]
        assert ids(cli("list", "--status", "done")[0]) == [1]
        assert TaskStore(data_path).stats() == {
            "total": 5, "open": 4, "done": 1, "ready": 3, "blocked": 1, "depth": 2,
        }
        assert "depth: 2" in cli("stats")[0]
        cli("done", "2")
        _, error = rejected("done", "5")
        assert "cannot complete: blocked by open dependency 3" in error
        assert ids(cli("block", "5")[0]) == [3]
        assert cli("block", "2")[0] == ""

        # Round-trip every CSV field, including quoting and multiple deps.
        csv_path = root / "export.csv"
        cli("export", str(csv_path))
        with csv_path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        assert list(rows[0]) == CSV_COLUMNS
        assert rows[1]["title"] == title and rows[4]["deps"] == "2;3"
        cli("add", "temporary")  # ID 6 must stay retired after deletion/import.
        cli("rm", "6")
        cli("add", "replace me")  # Import must remove tasks absent from CSV.
        cli("import", str(csv_path))
        assert set(TaskStore(data_path).tasks) == {1, 2, 3, 4, 5}
        second_csv = root / "roundtrip.csv"
        cli("export", str(second_csv))
        assert second_csv.read_bytes() == csv_path.read_bytes()
        assert TaskStore(data_path).next_id == 8

        # Invalid imports leave both the original data and ID counter intact.
        invalid_csv = root / "invalid.csv"
        for contents in (
            "id,title,priority,status,deps\n9,bad,3,open,999\n",
            "id,title,priority,status,deps\n9,a,3,open,\n9,b,3,open,\n",
            "id,title,priority,status,deps\n9,bad,6,open,\n",
            "id,title,priority,status,deps\n9,bad,3,unknown,\n",
            "id,title,priority,status,deps\n9,bad,3,open\n",
            "id,title,priority,status,deps\n9,bad,3,open,2;\n",
            "wrong,header\n", "",
        ):
            invalid_csv.write_text(contents, encoding="utf-8")
            rejected("import", str(invalid_csv))
        rejected("import", str(root / "missing.csv"))

        # Removal refuses even completed dependents, then cleans every edge.
        rejected("rm", "1")
        cli("rm", "1", "--force")
        assert TaskStore(data_path).get(2).deps == []
        rejected("rm", "2")
        cli("rm", "2", "--force")
        assert TaskStore(data_path).get(5).deps == [3]

        # A downstream blocked task must not be reported as part of the cycle.
        cli("dep", "3", "--on", "5")
        cli("dep", "4", "--on", "5")
        output, error = rejected("plan")
        assert output == "" and "cycle detected: 3, 5" in error
        rejected("stats")
        try:
            TaskStore(data_path).plan()
        except CycleError as error:
            assert set(error.ids) == {3, 5}
        else:
            assert False, "cycle was not detected"
        cli("rm", "5", "--force")
        store = TaskStore(data_path)
        assert store.get(3).deps == store.get(4).deps == []
        cli("add", "new task")
        assert TaskStore(data_path).get(8).title == "new task"

        # Missing/invalid arguments consistently produce usage and exit 1.
        for args in (
            (), ("unknown",), ("add",), ("add", "bad", "--priority", "6"),
            ("add", "bad", "--priority", "abc"), ("add", "bad", "--dep"),
            ("dep", "3"), ("done", "abc"), ("rm", "0"), ("block", "-1"),
            ("list", "--status", "bad"), ("ready", "extra"), ("search",),
            ("export",), ("import",),
        ):
            _, error = rejected(*args)
            assert "usage:" in error
        for args in (("done", "999"), ("rm", "999"), ("block", "999")):
            rejected(*args)

        # Startup handles absent, empty, corrupt, and malformed snapshots.
        bad_path = root / "corrupt.json"
        assert cli("list", path=bad_path)[0] == ""
        for contents in (
            b"", b"{broken", b"\xff", b"null", b"[]",
            b'{"tasks": [null], "next_id": 2}',
            b'{"tasks": [], "next_id": true}',
            b'{"tasks": [], "next_id": 0}',
        ):
            bad_path.write_bytes(contents)
            assert cli("list", path=bad_path)[0] == ""
            assert not TaskStore(bad_path).tasks
        cli("add", "recovered", path=bad_path)
        assert TaskStore(bad_path).get(1).title == "recovered"

        # Forward references work; a header-only import clears the task set.
        other_path = root / "imported.json"
        csv_path.write_text(
            "id,title,priority,status,deps\n20,child,3,open,30\n30,parent,3,done,\n",
            encoding="utf-8",
        )
        cli("import", str(csv_path), path=other_path)
        assert ids(cli("ready", path=other_path)[0]) == [20]
        csv_path.write_text(",".join(CSV_COLUMNS) + "\n", encoding="utf-8")
        cli("import", str(csv_path), path=other_path)
        assert TaskStore(other_path).stats() == {
            "total": 0, "open": 0, "done": 0, "ready": 0, "blocked": 0, "depth": 0,
        }
        assert cli("plan", path=other_path)[0] == ""
        cli("add", "after empty import", path=other_path)
        assert TaskStore(other_path).get(31).title == "after empty import"

        # Deep dependency chains do not depend on Python's recursion limit.
        deep = TaskStore(root / "deep.json")
        for number in range(1, 1201):
            deep.add(str(number), deps=[number - 1] if number > 1 else [])
        assert deep.stats()["depth"] == 1199
        assert [task.id for task in deep.plan()] == list(range(1, 1201))
        deep.depend(1, 1200)
        try:
            deep.plan()
        except CycleError as error:
            assert set(error.ids) == set(range(1, 1201))
        else:
            assert False, "long cycle was not detected"


def main(argv=None, data_path="tasks.json"):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "test":
            run_self_tests()
            print("all tests passed")
            return 0

        store = TaskStore(data_path)
        if args.command == "add":
            task = store.add(args.title, args.priority, args.dep)
            store.save()
            print(f"added task {task.id}")
        elif args.command == "list":
            print_tasks(store.ordered(args.status))
        elif args.command == "dep":
            store.depend(args.id, args.on)
            store.save()
            print(f"task {args.id} depends on {args.on}")
        elif args.command == "done":
            store.complete(args.id)
            store.save()
            print(f"completed task {args.id}")
        elif args.command == "rm":
            store.remove(args.id, args.force)
            store.save()
            print(f"removed task {args.id}")
        elif args.command == "ready":
            print_tasks(store.ready())
        elif args.command == "plan":
            print_tasks(store.plan())
        elif args.command == "block":
            print_tasks(store.blockers(args.id))
        elif args.command == "graph":
            graph = store.graph()
            for task in store.ordered():
                dependents = ",".join(map(str, graph[task.id])) or "-"
                print(f"{format_task(task)} | dependents: {dependents}")
        elif args.command == "search":
            print_tasks(store.search(args.term))
        elif args.command == "stats":
            for label, count in store.stats().items():
                print(f"{label}: {count}")
        elif args.command == "export":
            store.export_csv(args.file)
            print(f"exported {len(store.tasks)} tasks")
        elif args.command == "import":
            store.import_csv(args.file)
            store.save()
            print(f"imported {len(store.tasks)} tasks")
    except (TaskError, OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
