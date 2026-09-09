import argparse
import contextlib
import csv
import heapq
import io
import json
import os
import sys
import tempfile
from datetime import datetime, timezone


DATA_FILE = "tasks.json"


class TaskError(Exception):
    pass


class CycleError(TaskError):
    def __init__(self, ids):
        self.ids = sorted(ids)
        super().__init__("cycle detected: " + " ".join(map(str, self.ids)))


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def valid_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_tasks(records):
    if not isinstance(records, list):
        raise TaskError("tasks must be a list")

    tasks = {}
    for record in records:
        if not isinstance(record, dict):
            raise TaskError("invalid task record")
        task_id = record.get("id")
        priority = record.get("priority", 3)
        title = record.get("title")
        status = record.get("status", "open")
        deps = record.get("deps", [])
        created = record.get("created", timestamp())

        if not valid_integer(task_id) or task_id < 1:
            raise TaskError("task ids must be positive integers")
        if task_id in tasks:
            raise TaskError("duplicate task id {}".format(task_id))
        if not isinstance(title, str):
            raise TaskError("task title must be a string")
        if not valid_integer(priority) or not 1 <= priority <= 5:
            raise TaskError("priority must be an integer from 1 to 5")
        if status not in ("open", "done"):
            raise TaskError("status must be open or done")
        if not isinstance(deps, list) or any(
            not valid_integer(dep) or dep < 1 for dep in deps
        ):
            raise TaskError("dependencies must be positive integer ids")
        if not isinstance(created, str) or not created:
            raise TaskError("invalid created timestamp")

        tasks[task_id] = {
            "id": task_id,
            "title": title,
            "priority": priority,
            "status": status,
            "deps": list(dict.fromkeys(deps)),
            "created": created,
        }

    for task in tasks.values():
        for dep in task["deps"]:
            if dep not in tasks:
                raise TaskError("dependency {} does not exist".format(dep))
    return tasks


class TaskManager:
    def __init__(self, path=DATA_FILE):
        self.path = os.fspath(path)
        self.tasks = {}
        self.next_id = 1
        self.load()

    def load(self):
        self.tasks = {}
        self.next_id = 1
        try:
            with open(self.path, "r", encoding="utf-8") as stream:
                data = json.load(stream)
            if not isinstance(data, dict):
                return
            tasks = normalize_tasks(data["tasks"])
            next_id = data.get("next_id", max(tasks, default=0) + 1)
            if not valid_integer(next_id) or next_id < 1:
                return
            self.tasks = tasks
            self.next_id = max(next_id, max(tasks, default=0) + 1)
        except (OSError, ValueError, TypeError, KeyError, TaskError, RecursionError):
            self.tasks = {}
            self.next_id = 1

    def save(self):
        directory = os.path.dirname(os.path.abspath(self.path))
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                prefix=".tasks-",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = stream.name
                json.dump(
                    {
                        "next_id": self.next_id,
                        "tasks": self.all_tasks(),
                    },
                    stream,
                    ensure_ascii=True,
                    indent=2,
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass

    def all_tasks(self):
        return [self.tasks[task_id] for task_id in sorted(self.tasks)]

    def require(self, task_id):
        if task_id not in self.tasks:
            raise TaskError("task {} does not exist".format(task_id))
        return self.tasks[task_id]

    def add(self, title, priority=3, deps=None):
        if not isinstance(title, str):
            raise TaskError("task title must be a string")
        if not valid_integer(priority) or not 1 <= priority <= 5:
            raise TaskError("priority must be an integer from 1 to 5")
        deps = list(dict.fromkeys(deps or []))
        for dep in deps:
            self.require(dep)

        task_id = self.next_id
        self.tasks[task_id] = {
            "id": task_id,
            "title": title,
            "priority": priority,
            "status": "open",
            "deps": deps,
            "created": timestamp(),
        }
        self.next_id += 1
        self.save()
        return task_id

    def add_dependency(self, task_id, other_id):
        task = self.require(task_id)
        self.require(other_id)
        if task_id == other_id:
            raise TaskError("a task cannot depend on itself")
        if other_id not in task["deps"]:
            task["deps"].append(other_id)
            self.save()

    def blockers(self, task_id):
        task = self.require(task_id)
        return [
            self.tasks[dep]
            for dep in sorted(task["deps"])
            if self.tasks[dep]["status"] == "open"
        ]

    def complete(self, task_id):
        task = self.require(task_id)
        blockers = self.blockers(task_id)
        if blockers:
            raise TaskError(
                "cannot complete: blocked by open dependency {}".format(
                    blockers[0]["id"]
                )
            )
        task["status"] = "done"
        self.save()

    def remove(self, task_id, force=False):
        self.require(task_id)
        dependents = [
            task
            for task in self.tasks.values()
            if task["id"] != task_id and task_id in task["deps"]
        ]
        if dependents and not force:
            raise TaskError(
                "cannot remove: task {} has dependents {}".format(
                    task_id,
                    " ".join(str(task["id"]) for task in sorted(
                        dependents, key=lambda task: task["id"]
                    )),
                )
            )
        del self.tasks[task_id]
        if force:
            for task in self.tasks.values():
                task["deps"] = [dep for dep in task["deps"] if dep != task_id]
        self.save()

    def ready(self):
        return sorted(
            (
                task
                for task in self.tasks.values()
                if task["status"] == "open"
                and all(self.tasks[dep]["status"] == "done" for dep in task["deps"])
            ),
            key=lambda task: (-task["priority"], task["id"]),
        )

    def find_cycle(self, nodes):
        """Return the ids in one actual cycle, not downstream blocked tasks."""
        nodes = set(nodes)
        color = {}
        for root in sorted(nodes):
            if color.get(root, 0):
                continue
            path = [root]
            positions = {root: 0}
            color[root] = 1
            stack = [(root, iter(self.tasks[root]["deps"]))]
            while stack:
                node, edges = stack[-1]
                try:
                    dep = next(edges)
                except StopIteration:
                    stack.pop()
                    color[node] = 2
                    positions.pop(node)
                    path.pop()
                    continue
                if dep not in nodes:
                    continue
                state = color.get(dep, 0)
                if state == 1:
                    return path[positions[dep]:]
                if state == 0:
                    color[dep] = 1
                    positions[dep] = len(path)
                    path.append(dep)
                    stack.append((dep, iter(self.tasks[dep]["deps"])))
        return []

    def topological_order(self, nodes):
        nodes = set(nodes)
        indegree = {node: 0 for node in nodes}
        dependents = {node: [] for node in nodes}
        for node in nodes:
            for dep in self.tasks[node]["deps"]:
                if dep in nodes:
                    indegree[node] += 1
                    dependents[dep].append(node)

        available = [
            (-self.tasks[node]["priority"], node)
            for node in nodes
            if indegree[node] == 0
        ]
        heapq.heapify(available)
        result = []
        while available:
            _, node = heapq.heappop(available)
            result.append(node)
            for dependent in dependents[node]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    heapq.heappush(
                        available,
                        (-self.tasks[dependent]["priority"], dependent),
                    )
        if len(result) != len(nodes):
            remaining = {node for node in nodes if indegree[node] > 0}
            raise CycleError(self.find_cycle(remaining))
        return result

    def plan(self):
        return [
            self.tasks[node]
            for node in self.topological_order(
                task["id"]
                for task in self.tasks.values()
                if task["status"] == "open"
            )
        ]

    def stats(self):
        open_count = sum(task["status"] == "open" for task in self.tasks.values())
        ready_count = len(self.ready())
        # Chain length is measured in dependency edges: an isolated task has
        # depth zero. A cyclic graph has no finite dependency depth.
        try:
            order = self.topological_order(self.tasks)
        except CycleError:
            depth = "undefined (cycle)"
        else:
            depths = {}
            for node in order:
                deps = self.tasks[node]["deps"]
                depths[node] = (
                    1 + max(depths[dep] for dep in deps) if deps else 0
                )
            depth = max(depths.values(), default=0)

        return {
            "total": len(self.tasks),
            "open": open_count,
            "done": len(self.tasks) - open_count,
            "ready": ready_count,
            "blocked": open_count - ready_count,
            "depth": depth,
        }

    def export_csv(self, path):
        with open(path, "w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=["id", "title", "priority", "status", "deps"]
            )
            writer.writeheader()
            for task in self.all_tasks():
                writer.writerow({
                    "id": task["id"],
                    "title": task["title"],
                    "priority": task["priority"],
                    "status": task["status"],
                    "deps": ";".join(map(str, task["deps"])),
                })

    def import_csv(self, path):
        records = []
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, strict=True)
                required = {"id", "title", "priority", "status", "deps"}
                fields = reader.fieldnames
                if (
                    fields is None
                    or len(fields) != len(set(fields))
                    or not required.issubset(fields)
                ):
                    raise TaskError("CSV requires columns id,title,priority,status,deps")

                created = timestamp()
                for row in reader:
                    if None in row or any(row.get(key) is None for key in required):
                        raise TaskError("invalid CSV row")
                    raw_deps = row["deps"].strip()
                    records.append({
                        "id": int(row["id"]),
                        "title": row["title"],
                        "priority": int(row["priority"]),
                        "status": row["status"].strip(),
                        "deps": (
                            [int(part.strip()) for part in raw_deps.split(";")]
                            if raw_deps else []
                        ),
                        "created": created,
                    })
        except (ValueError, csv.Error) as exc:
            raise TaskError("invalid CSV: {}".format(exc)) from exc

        tasks = normalize_tasks(records)
        self.tasks = tasks
        self.next_id = max(self.next_id, max(tasks, default=0) + 1)
        self.save()


class ArgumentError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        raise ArgumentError(message)


def positive_id(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("id must be a positive integer")
    if value < 1:
        raise argparse.ArgumentTypeError("id must be a positive integer")
    return value


def build_parser():
    parser = Parser(prog="tasks.py", description="Dependency-aware task manager")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="add a task")
    add.add_argument("title")
    add.add_argument("--priority", type=int, choices=range(1, 6), default=3)
    add.add_argument("--dep", type=positive_id, action="append", default=[])

    listing = commands.add_parser("list", help="list tasks")
    listing.add_argument("--status", choices=["open", "done", "all"], default="all")

    dep = commands.add_parser("dep", help="add a dependency")
    dep.add_argument("id", type=positive_id)
    dep.add_argument("--on", type=positive_id, required=True)

    done = commands.add_parser("done", help="complete a task")
    done.add_argument("id", type=positive_id)

    remove = commands.add_parser("rm", help="remove a task")
    remove.add_argument("id", type=positive_id)
    remove.add_argument("--force", action="store_true")

    commands.add_parser("ready", help="list actionable tasks")
    commands.add_parser("plan", help="list a dependency-respecting execution order")

    block = commands.add_parser("block", help="list open dependencies")
    block.add_argument("id", type=positive_id)

    commands.add_parser("graph", help="list direct dependents")

    search = commands.add_parser("search", help="search task titles")
    search.add_argument("term")

    commands.add_parser("stats", help="show counts and dependency depth")
    export = commands.add_parser("export", help="export tasks to CSV")
    export.add_argument("file")
    import_command = commands.add_parser("import", help="replace tasks from CSV")
    import_command.add_argument("file")
    commands.add_parser("test", help="run isolated self-tests")
    return parser


def display_task(task):
    marker = "x" if task["status"] == "done" else " "
    title = task["title"].replace("\r", "\\r").replace("\n", "\\n")
    deps = ",".join(map(str, task["deps"]))
    print("{} [{}] priority={} {} deps=[{}]".format(
        task["id"], marker, task["priority"], title, deps
    ))


def display_tasks(tasks):
    for task in tasks:
        display_task(task)


def self_test():
    with tempfile.TemporaryDirectory(prefix="tasks-test-") as directory:
        data_path = os.path.join(directory, "tasks.json")
        csv_path = os.path.join(directory, "tasks.csv")

        def invoke(*args):
            output = io.StringIO()
            errors = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                code = main(list(args), data_path=data_path)
            return code, output.getvalue() + errors.getvalue()

        def succeeds(*args):
            code, output = invoke(*args)
            assert code == 0, (args, code, output)
            return output

        def fails(*args):
            code, output = invoke(*args)
            assert code == 1, (args, code, output)
            return output

        fails("add", "invalid", "--dep", "999")
        manager = TaskManager(data_path)
        assert manager.tasks == {} and manager.next_id == 1

        succeeds("add", "root", "--priority", "2")
        succeeds("add", "middle", "--dep", "1", "--priority", "5")
        succeeds("add", "leaf", "--dep", "2")
        succeeds("add", "independent", "--priority", "4")
        assert "cannot complete: blocked by open dependency 1" in fails("done", "2")
        assert TaskManager(data_path).require(2)["status"] == "open"
        fails("dep", "1", "--on", "1")
        fails("dep", "1", "--on", "999")
        fails("dep", "999", "--on", "1")

        manager = TaskManager(data_path)
        assert [task["id"] for task in manager.ready()] == [4, 1]
        plan = [task["id"] for task in manager.plan()]
        assert plan == [4, 1, 2, 3]
        positions = {node: index for index, node in enumerate(plan)}
        for task in manager.tasks.values():
            for dep in task["deps"]:
                assert positions[dep] < positions[task["id"]]
        assert manager.stats() == {
            "total": 4, "open": 4, "done": 0, "ready": 2,
            "blocked": 2, "depth": 2,
        }

        succeeds("dep", "1", "--on", "3")
        assert "cycle detected:" in fails("plan")
        try:
            TaskManager(data_path).plan()
        except CycleError as exc:
            assert set(exc.ids) == {1, 2, 3}
        else:
            assert False, "cycle was not detected"

        fails("rm", "3")
        assert 3 in TaskManager(data_path).tasks
        succeeds("rm", "3", "--force")
        manager = TaskManager(data_path)
        assert 3 not in manager.tasks
        assert all(3 not in task["deps"] for task in manager.tasks.values())
        assert manager.stats()["depth"] == 1

        fails("rm", "1")
        succeeds("done", "1")
        assert [task["id"] for task in TaskManager(data_path).ready()] == [2, 4]
        succeeds("done", "2")
        assert TaskManager(data_path).stats()["done"] == 2

        succeeds("add", 'CSV, "quoted"\nUnicode: \u2603', "--dep", "1")
        assert 5 in TaskManager(data_path).tasks

        def csv_fields(manager):
            return [
                {key: task[key] for key in ("id", "title", "priority", "status", "deps")}
                for task in manager.all_tasks()
            ]

        before = csv_fields(TaskManager(data_path))
        succeeds("export", csv_path)
        succeeds("rm", "1", "--force")
        succeeds("import", csv_path)
        assert csv_fields(TaskManager(data_path)) == before

        bad_csv = os.path.join(directory, "bad.csv")
        with open(bad_csv, "w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["id", "title", "priority", "status", "deps"])
            writer.writerow([10, "bad dependency", 3, "open", "999"])
        fails("import", bad_csv)
        assert csv_fields(TaskManager(data_path)) == before

        succeeds("rm", "5")
        succeeds("add", "never reuse")
        assert 6 in TaskManager(data_path).tasks

        succeeds("list")
        succeeds("ready")
        succeeds("plan")
        succeeds("block", "6")
        succeeds("graph")
        assert "root" in succeeds("search", "ROOT")
        assert "depth:" in succeeds("stats")
        fails("unknown-command")
        fails("add")
        fails("add", "bad priority", "--priority", "6")

        recovery_path = os.path.join(directory, "recovery.json")
        assert TaskManager(recovery_path).tasks == {}
        for content in ("", "{broken", "null", '{"tasks":[{}]}'):
            with open(recovery_path, "w", encoding="utf-8") as stream:
                stream.write(content)
            assert TaskManager(recovery_path).tasks == {}

    print("all tests passed")


def main(argv=None, data_path=DATA_FILE):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except ArgumentError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1

    try:
        if args.command == "test":
            self_test()
            return 0

        manager = TaskManager(data_path)
        command = args.command
        if command == "add":
            task_id = manager.add(args.title, args.priority, args.dep)
            print("added {}".format(task_id))
        elif command == "list":
            display_tasks(
                task for task in manager.all_tasks()
                if args.status == "all" or task["status"] == args.status
            )
        elif command == "dep":
            manager.add_dependency(args.id, args.on)
            print("task {} depends on {}".format(args.id, args.on))
        elif command == "done":
            manager.complete(args.id)
            print("completed {}".format(args.id))
        elif command == "rm":
            manager.remove(args.id, args.force)
            print("removed {}".format(args.id))
        elif command == "ready":
            display_tasks(manager.ready())
        elif command == "plan":
            display_tasks(manager.plan())
        elif command == "block":
            display_tasks(manager.blockers(args.id))
        elif command == "graph":
            dependents = {task_id: [] for task_id in manager.tasks}
            for task in manager.all_tasks():
                for dep in task["deps"]:
                    dependents[dep].append(task["id"])
            for task in manager.all_tasks():
                title = task["title"].replace("\r", "\\r").replace("\n", "\\n")
                print("{} {} dependents=[{}]".format(
                    task["id"], title,
                    ",".join(map(str, dependents[task["id"]])),
                ))
        elif command == "search":
            term = args.term.casefold()
            display_tasks(
                task for task in manager.all_tasks()
                if term in task["title"].casefold()
            )
        elif command == "stats":
            for key, value in manager.stats().items():
                print("{}: {}".format(key, value))
        elif command == "export":
            manager.export_csv(args.file)
            print("exported {} tasks".format(len(manager.tasks)))
        elif command == "import":
            manager.import_csv(args.file)
            print("imported {} tasks".format(len(manager.tasks)))
        return 0
    except TaskError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, UnicodeError, csv.Error) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

