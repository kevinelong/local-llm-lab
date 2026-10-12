from solution import merge

assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
assert merge([]) == []
assert merge([[2, 3], [1, 4]]) == [[1, 4]]
print("public checks passed")
