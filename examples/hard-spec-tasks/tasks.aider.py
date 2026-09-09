import json
import sys
import os
from collections import defaultdict, deque

TASKS_FILE = "tasks.json"
TEMP_TEST_FILE = "test_tasks.json"

# Global task storage
tasks = {}
next_id = 1

def load_tasks():
    global tasks, next_id
    tasks = {}
    next_id = 1
    try:
        if os.path.exists(TASKS_FILE) and os.path.getsize(TASKS_FILE) > 0:
            with open(TASKS_FILE, 'r') as f:
                data = json.load(f)
                for task_data in data:
                    task_id = task_data['id']
                    tasks[task_id] = task_data
                    if task_id >= next_id:
                        next_id = task_id + 1
    except (json.JSONDecodeError, IOError):
        # Start with empty tasks on error
        pass

def save_tasks():
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(list(tasks.values()), f, indent=2)
    except IOError:
        pass  # Silently fail on save errors

def get_task(task_id):
    return tasks.get(task_id)

def add_task(title, priority=3, deps=None):
    global next_id
    if deps is None:
        deps = []
    
    # Validate dependencies exist
    for dep_id in deps:
        if dep_id not in tasks:
            print(f"error: dependency {dep_id} does not exist")
            sys.exit(1)
    
    task = {
        'id': next_id,
        'title': title,
        'priority': priority,
        'status': 'open',
        'deps': deps,
        'created': __import__('datetime').datetime.now().isoformat()
    }
    
    tasks[next_id] = task
    next_id += 1
    return task

def mark_done(task_id):
    task = get_task(task_id)
    if not task:
        print(f"error: no such task {task_id}")
        sys.exit(1)
    
    # Check if any dependencies are still open
    for dep_id in task['deps']:
        dep_task = get_task(dep_id)
        if dep_task and dep_task['status'] == 'open':
            print(f"cannot complete: blocked by open dependency {dep_id}")
            sys.exit(1)
    
    task['status'] = 'done'

def remove_task(task_id, force=False):
    task = get_task(task_id)
    if not task:
        print(f"error: no such task {task_id}")
        sys.exit(1)
    
    # Check if any other tasks depend on this one
    dependents = [t for t in tasks.values() if task_id in t['deps']]
    if dependents and not force:
        print(f"error: task {task_id} is depended on by others")
        sys.exit(1)
    
    # Remove from dependents' deps if force
    if force:
        for dep_task in dependents:
            dep_task['deps'].remove(task_id)
    
    del tasks[task_id]

def get_dependents(task_id):
    return [t for t in tasks.values() if task_id in t['deps']]

def get_open_deps(task_id):
    task = get_task(task_id)
    if not task:
        return []
    return [dep_id for dep_id in task['deps'] if tasks[dep_id]['status'] == 'open']

def is_ready(task_id):
    task = get_task(task_id)
    if not task or task['status'] != 'open':
        return False
    return all(tasks[dep_id]['status'] == 'done' for dep_id in task['deps'])

def get_all_deps(task_id):
    """Get all transitive dependencies"""
    visited = set()
    queue = [task_id]
    deps = set()
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        task = get_task(current)
        if not task:
            continue
            
        for dep_id in task['deps']:
            deps.add(dep_id)
            queue.append(dep_id)
    
    return list(deps)

def has_cycle():
    """Detect cycles using topological sort"""
    # Build reverse dependency graph
    reverse_deps = defaultdict(list)
    for task in tasks.values():
        for dep_id in task['deps']:
            reverse_deps[dep_id].append(task['id'])
    
    # Topological sort with cycle detection
    in_degree = {task_id: len(task['deps']) for task_id, task in tasks.items()}
    queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
    visited = set()
    
    while queue:
        current = queue.pop(0)
        visited.add(current)
        
        for dependent in reverse_deps[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    # If not all tasks were visited, there's a cycle
    return len(visited) != len(tasks)

def get_execution_order():
    """Get topological order respecting priorities"""
    if has_cycle():
        cycle_tasks = [task_id for task_id in tasks.keys() if tasks[task_id]['status'] == 'open']
        print(f"cycle detected: {sorted(cycle_tasks)}")
        sys.exit(1)
    
    # Build reverse dependency graph
    reverse_deps = defaultdict(list)
    for task in tasks.values():
        for dep_id in task['deps']:
            reverse_deps[dep_id].append(task['id'])
    
    # Topological sort with priority tie-breaking
    in_degree = {task_id: len(task['deps']) for task_id, task in tasks.items()}
    queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
    
    # Sort by priority (desc) then id (asc)
    queue.sort(key=lambda x: (-tasks[x]['priority'], x))
    
    result = []
    while queue:
        current = queue.pop(0)
        result.append(current)
        
        for dependent in reverse_deps[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                # Add to queue and sort again
                queue.append(dependent)
                queue.sort(key=lambda x: (-tasks[x]['priority'], x))
    
    return result

def get_stats():
    total = len(tasks)
    open_count = sum(1 for t in tasks.values() if t['status'] == 'open')
    done_count = sum(1 for t in tasks.values() if t['status'] == 'done')
    ready_count = sum(1 for t in tasks.values() if is_ready(t['id']))
    
    # Calculate blocked count
    blocked_count = 0
    for task in tasks.values():
        if task['status'] == 'open' and get_open_deps(task['id']):
            blocked_count += 1
    
    # Calculate depth (longest dependency chain)
    def max_depth(task_id):
        task = get_task(task_id)
        if not task:
            return 0
        if not task['deps']:
            return 1
        return 1 + max(max_depth(dep_id) for dep_id in task['deps'])
    
    depth = max(max_depth(task_id) for task_id in tasks.keys()) if tasks else 0
    
    return {
        'total': total,
        'open': open_count,
        'done': done_count,
        'ready': ready_count,
        'blocked': blocked_count,
        'depth': depth
    }

def export_tasks(filename):
    with open(filename, 'w') as f:
        f.write('id,title,priority,status,deps\n')
        for task in tasks.values():
            deps_str = ';'.join(map(str, task['deps']))
            f.write(f"{task['id']},{task['title']},{task['priority']},{task['status']},{deps_str}\n")

def import_tasks(filename):
    global tasks, next_id
    tasks = {}
    next_id = 1
    
    with open(filename, 'r') as f:
        lines = f.readlines()[1:]  # Skip header
        
        # First pass: load all tasks without validating dependencies
        task_list = []
        for line in lines:
            parts = line.strip().split(',', 4)
            if len(parts) < 5:
                continue
                
            task_id, title, priority, status, deps_str = parts
            
            try:
                task_id = int(task_id)
                priority = int(priority)
                deps = [int(d) for d in deps_str.split(';') if d] if deps_str else []
                
                task_list.append({
                    'id': task_id,
                    'title': title,
                    'priority': priority,
                    'status': status,
                    'deps': deps,
                    'created': __import__('datetime').datetime.now().isoformat()
                })
                
                if task_id >= next_id:
                    next_id = task_id + 1
                    
            except ValueError:
                continue
        
        # Validate dependencies exist
        all_ids = {task['id'] for task in task_list}
        for task in task_list:
            for dep_id in task['deps']:
                if dep_id not in all_ids:
                    print(f"error: dependency {dep_id} does not exist in import")
                    sys.exit(1)
        
        # Load valid tasks
        for task in task_list:
            tasks[task['id']] = task

def test():
    global next_id  # Add this line to fix the error
    # Save current state
    original_tasks = dict(tasks)
    original_next_id = next_id
    
    try:
        # Test case 1: dep validation on add
        t1 = add_task("Task 1")
        t2 = add_task("Task 2", deps=[999])  # Should fail
        print("Test failed: should have exited on invalid dependency")
        sys.exit(1)
    except SystemExit:
        pass  # Expected
    
    try:
        # Test case 2: done-blocking by open deps
        t3 = add_task("Task 3")
        t4 = add_task("Task 4", deps=[t3['id']])
        mark_done(t4['id'])  # Should fail
        print("Test failed: should have exited on blocked task completion")
        sys.exit(1)
    except SystemExit:
        pass  # Expected
    
    try:
        # Test case 3: ready set
        mark_done(t3['id'])
        if not is_ready(t4['id']):
            print("Test failed: task should be ready after deps done")
            sys.exit(1)
    except Exception:
        print("Test failed: ready set test")
        sys.exit(1)
    
    # Test case 4: plan topological correctness
    try:
        plan = get_execution_order()
        if len(plan) != 2 or plan[0] != t3['id'] or plan[1] != t4['id']:
            print("Test failed: plan should be topologically sorted")
            sys.exit(1)
    except Exception:
        print("Test failed: plan test")
        sys.exit(1)
    
    # Test case 5: cycle detection
    try:
        add_task("Cycle Task", deps=[t4['id']])
        t4['deps'].append(t3['id'])  # Create cycle
        get_execution_order()  # Should fail
        print("Test failed: should have detected cycle")
        sys.exit(1)
    except SystemExit:
        pass  # Expected
    
    # Test case 6: rm-with-dependents (and --force)
    try:
        remove_task(t3['id'], force=True)  # Should work with force
    except Exception:
        print("Test failed: force removal should work")
        sys.exit(1)
    
    # Test case 7: stats depth
    stats = get_stats()
    if stats['depth'] != 2:
        print("Test failed: depth calculation incorrect")
        sys.exit(1)
    
    # Test case 8: export/import round-trip
    try:
        export_tasks("temp_export.csv")
        import_tasks("temp_export.csv")
        if len(tasks) != 2:
            print("Test failed: import should preserve tasks")
            sys.exit(1)
    except Exception:
        print("Test failed: export/import test")
        sys.exit(1)
    
    # Restore original state
    tasks.clear()
    tasks.update(original_tasks)
    next_id = original_next_id
    
    print("all tests passed")

def main():
    if len(sys.argv) < 2:
        print("Usage: python tasks.py <command> [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Load tasks at startup
    load_tasks()
    
    if command == "add":
        if len(sys.argv) < 3:
            print("Usage: python tasks.py add \"title\" [--priority N] [--dep ID]...")
            sys.exit(1)
        
        title = sys.argv[2]
        priority = 3
        deps = []
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--priority":
                try:
                    priority = int(sys.argv[i+1])
                    if not (1 <= priority <= 5):
                        print("Priority must be between 1 and 5")
                        sys.exit(1)
                    i += 2
                except (IndexError, ValueError):
                    print("Invalid priority value")
                    sys.exit(1)
            elif sys.argv[i] == "--dep":
                try:
                    dep_id = int(sys.argv[i+1])
                    deps.append(dep_id)
                    i += 2
                except (IndexError, ValueError):
                    print("Invalid dependency ID")
                    sys.exit(1)
            else:
                break
        
        add_task(title, priority, deps)
        save_tasks()
        
    elif command == "list":
        status_filter = None
        if len(sys.argv) > 2 and sys.argv[2] == "--status":
            if len(sys.argv) < 4:
                print("Usage: python tasks.py list [--status open|done|all]")
                sys.exit(1)
            status_filter = sys.argv[3]
        
        for task in sorted(tasks.values(), key=lambda t: (t['priority'], t['id']), reverse=True):
            if status_filter and status_filter != 'all' and task['status'] != status_filter:
                continue
                
            status_marker = "✓" if task['status'] == 'done' else "○"
            deps_str = ', '.join(map(str, task['deps'])) if task['deps'] else ''
            print(f"{task['id']} {status_marker} [{task['priority']}] {task['title']} (deps: {deps_str})")
            
    elif command == "dep":
        if len(sys.argv) < 5 or sys.argv[3] != "--on":
            print("Usage: python tasks.py dep <id> --on <other_id>")
            sys.exit(1)
        
        try:
            task_id = int(sys.argv[2])
            other_id = int(sys.argv[4])
            
            if task_id == other_id:
                print("error: self-dependency not allowed")
                sys.exit(1)
                
            if task_id not in tasks or other_id not in tasks:
                print("error: task does not exist")
                sys.exit(1)
                
            tasks[task_id]['deps'].append(other_id)
            save_tasks()
        except ValueError:
            print("Invalid task ID")
            sys.exit(1)
            
    elif command == "done":
        if len(sys.argv) < 3:
            print("Usage: python tasks.py done <id>")
            sys.exit(1)
        
        try:
            task_id = int(sys.argv[2])
            mark_done(task_id)
            save_tasks()
        except ValueError:
            print("Invalid task ID")
            sys.exit(1)
            
    elif command == "rm":
        force = False
        if len(sys.argv) > 3 and sys.argv[3] == "--force":
            force = True
            
        if len(sys.argv) < 3:
            print("Usage: python tasks.py rm <id> [--force]")
            sys.exit(1)
            
        try:
            task_id = int(sys.argv[2])
            remove_task(task_id, force)
            save_tasks()
        except ValueError:
            print("Invalid task ID")
            sys.exit(1)
            
    elif command == "ready":
        ready_tasks = [t for t in tasks.values() if is_ready(t['id'])]
        ready_tasks.sort(key=lambda t: (-t['priority'], t['id']))
        
        for task in ready_tasks:
            deps_str = ', '.join(map(str, task['deps'])) if task['deps'] else ''
            print(f"{task['id']} [ready] [{task['priority']}] {task['title']} (deps: {deps_str})")
            
    elif command == "plan":
        try:
            order = get_execution_order()
            for task_id in order:
                task = tasks[task_id]
                deps_str = ', '.join(map(str, task['deps'])) if task['deps'] else ''
                print(f"{task['id']} [{task['priority']}] {task['title']} (deps: {deps_str})")
        except SystemExit:
            pass  # Already handled in get_execution_order
            
    elif command == "block":
        if len(sys.argv) < 3:
            print("Usage: python tasks.py block <id>")
            sys.exit(1)
            
        try:
            task_id = int(sys.argv[2])
            open_deps = get_open_deps(task_id)
            if open_deps:
                print(f"task {task_id} is blocked by: {', '.join(map(str, open_deps))}")
            else:
                print(f"task {task_id} is not blocked")
        except ValueError:
            print("Invalid task ID")
            sys.exit(1)
            
    elif command == "graph":
        dependents = defaultdict(list)
        for task in tasks.values():
            for dep_id in task['deps']:
                dependents[dep_id].append(task['id'])
        
        for task_id in sorted(tasks.keys()):
            task = tasks[task_id]
            deps_str = ', '.join(map(str, dependents[task_id])) if dependents[task_id] else ''
            print(f"{task['id']} {task['title']} -> {deps_str}")
            
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python tasks.py search <term>")
            sys.exit(1)
            
        term = sys.argv[2].lower()
        found = [t for t in tasks.values() if term in t['title'].lower()]
        
        for task in sorted(found, key=lambda t: (t['priority'], t['id']), reverse=True):
            deps_str = ', '.join(map(str, task['deps'])) if task['deps'] else ''
            print(f"{task['id']} [{task['priority']}] {task['title']} (deps: {deps_str})")
            
    elif command == "stats":
        stats = get_stats()
        print(f"total: {stats['total']}")
        print(f"open: {stats['open']}")
        print(f"done: {stats['done']}")
        print(f"ready: {stats['ready']}")
        print(f"blocked: {stats['blocked']}")
        print(f"depth: {stats['depth']}")
        
    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: python tasks.py export <file.csv>")
            sys.exit(1)
            
        export_tasks(sys.argv[2])
        
    elif command == "import":
        if len(sys.argv) < 3:
            print("Usage: python tasks.py import <file.csv>")
            sys.exit(1)
            
        import_tasks(sys.argv[2])
        save_tasks()
        
    elif command == "test":
        test()
        
    else:
        print("Unknown command")
        sys.exit(1)

if __name__ == "__main__":
    main()
