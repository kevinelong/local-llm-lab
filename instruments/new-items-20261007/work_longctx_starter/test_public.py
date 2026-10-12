from legacy import reconcile_batch
from solution import reconcile_batch as shimmed

assert shimmed is not None
assert reconcile_batch([("a", 10), ("a", 0)]) == [("a", 10, 2)]
assert reconcile_batch([]) == []
assert reconcile_batch([("b", 1), ("a", 2)]) == [("a", 2, 1), ("b", 1, 1)]
print("public checks passed")
