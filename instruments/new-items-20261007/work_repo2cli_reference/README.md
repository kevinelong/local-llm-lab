Repair a three-module frame codec.

`codec.py` implements a base-128 varint. `encode(value) -> bytes` accepts a non-negative int only.
`decode(buffer, offset=0) -> (value, next_offset)` must raise ValueError when the buffer ends inside a
varint; it must never return a value for malformed input.

`frames.py` implements `FrameLog`, a append-only log of text frames:
- `append(text)` stores `varint(len(text.encode("utf-8"))) + text.encode("utf-8")` and returns self.
  `text` must be a str.
- `read_all() -> list[str]` returns the appended frames in order.
- `to_bytes() -> bytes` returns the serialized log.
- `FrameLog.from_bytes(data)` rebuilds a log from that buffer. It must **copy** the bytes it is given:
  a source buffer mutated afterwards must not change the decoded log.
- `filter(kind)` returns the frames whose prefix before the first `:` equals `kind`.

`registry.py` implements `Registry`:
- `register(kind, handler=None)` records a kind and returns the handler used for it.
- `handlers()` returns the mapping of kind -> handler, built fresh each call.
- A `Registry` must never share state with another `Registry`: registering `"a"` on one must not appear
  on another, and a handler registered on one must not be callable through another.

Rules: fix the four defects (byte-length accounting, the shared default, the buffer reference, and the
swallowed ValueError). Do not change the public names or signatures, do not modify `test_public.py` or
`README.md`, and use only the Python standard library.
