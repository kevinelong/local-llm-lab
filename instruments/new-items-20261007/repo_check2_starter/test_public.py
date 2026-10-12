from varint import encode, decode
from store import Ledger

assert encode(5) == b"\x05"
assert decode(b"\x05") == (5, 1)
ledger = Ledger().append("a", 7).append("b", -3)
assert ledger.read_all() == [("a", 7), ("b", -3)]
assert Ledger.from_bytes(ledger.to_bytes()).read_all() == [("a", 7), ("b", -3)]
print("public checks passed")
