from codec import encode, decode
from frames import FrameLog
from registry import Registry

assert encode(5) == b"\x05"
assert decode(b"\x05") == (5, 1)
log = FrameLog().append("alpha:1").append("beta:2")
assert log.read_all() == ["alpha:1", "beta:2"]
assert FrameLog.from_bytes(log.to_bytes()).read_all() == ["alpha:1", "beta:2"]
assert log.filter("alpha") == ["alpha:1"]
first = Registry()
second = Registry()
first.register("a")
assert second.handlers() == {}
print("public checks passed")
