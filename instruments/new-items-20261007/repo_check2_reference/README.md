Repair a two-module record store.

`varint.py` implements a base-128 varint: unsigned integers, 7 bits per byte, the high bit set on
every byte except the last. `encode(value) -> bytes` must reject anything that is not a non-negative
int. `decode(buffer, offset=0) -> (value, next_offset)` must raise ValueError when the buffer ends
inside a varint, and must reject an encoding longer than 10 bytes.

`store.py` implements `Ledger` on top of it. A record is
`varint(len(account_utf_8_bytes)) + account_utf_8_bytes + varint(zigzag(cents))`, where zigzag maps
a signed integer to an unsigned one as `n >= 0 -> 2n` and `n < 0 -> -2n - 1`. `append(account, cents)`
appends and returns self; it must reject an account that is not a non-empty string, not equal to its
stripped form, or a cents that is not an int (bools are not ints). `read_all()` returns the appended
`(account, cents)` tuples in order. `to_bytes()` returns the serialized buffer.
`Ledger.from_bytes(data)` rebuilds a ledger from that buffer and must raise ValueError when the
buffer ends in the middle of a record. Everything must survive a round trip through `to_bytes()`
and `from_bytes()`, including multi-byte varints, non-ASCII account names and negative cents.

Do not change the public names or signatures, do not modify test_public.py or README.md, and use only
the Python standard library. `solution.py` re-exports the public names for the harness
(`encode`, `decode`, `Ledger`); keep that working.
