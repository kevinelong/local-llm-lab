# Spec: "tasks" - a dependency-aware task manager (single file `tasks.py`, Python stdlib only)

Implement ALL requirements. Tasks form a dependency graph; several features are interdependent, so design
the data model first. Persist to `tasks.json` in the current directory.

Data model: each task has an integer `id` (incrementing, never reused), `title` (str), `priority`
(int 1-5, default 3, 5 = highest), `status` ("open" or "done"), `deps` (list of task ids it depends on),
and a `created` timestamp.

Commands (invoked as `python tasks.py <command> ...`):

1. `add "title" [--priority N] [--dep ID]...` - add a task. Every `--dep ID` must reference an existing
   task id; if any does not exist, print an error and exit 1 (do not add the task).
2. `list [--status open|done|all]` - list tasks (default all); show id, a status marker, priority, title,
   and deps.
3. `dep <id> --on <other_id>` - add a dependency edge (id depends on other_id). Both must exist. Reject a
   direct self-dependency (id == other_id) with exit 1.
4. `done <id>` - mark a task done. If ANY of its deps are still open, print
   "cannot complete: blocked by open dependency <dep_id>" and exit 1. Otherwise mark done, exit 0.
5. `rm <id> [--force]` - delete a task. If another task depends on it, refuse with exit 1 unless `--force`
   is given, in which case delete it AND remove it from every dependent's `deps`.
6. `ready` - list tasks that are open and whose deps are all done (the actionable set), ordered by
   priority (highest first), then by id ascending.
7. `plan` - print a valid execution order of ALL open tasks that respects dependencies (a topological
   sort): every task appears after all of its deps. Break ties by priority (highest first) then id.
   If the open tasks contain a dependency cycle, print "cycle detected: <ids>" and exit 1.
8. `block <id>` - list which of the task's dependencies are still open (what is blocking it).
9. `graph` - print each task with its direct dependents (the reverse edges).
10. `search <term>` - list tasks whose title contains term, case-insensitive.
11. `stats` - print total, open, done, ready count, blocked count, and `depth` = the length of the longest
    dependency chain in the graph.
12. `export <file.csv>` - write all tasks to CSV with columns: id,title,priority,status,deps
    (deps joined by ';').
13. `import <file.csv>` - replace all current tasks with those loaded from the CSV; validate that every
    dep id referenced exists in the imported set (else exit 1).
14. Persist to `tasks.json`; load on startup; a missing, empty, or corrupt file must start with no tasks
    and never crash.
15. Unknown command or missing/invalid arguments: print a short usage message and exit 1. Success exits 0.
16. `test` - a self-test (run via `python tasks.py test`) using a TEMPORARY data file (not the real
    tasks.json), with asserts covering: dep validation on add, done-blocking by open deps, ready set,
    plan topological correctness, cycle detection, rm-with-dependents (and --force), stats depth, and
    export/import round-trip. Print "all tests passed" and exit 0 on success.
